"""Agregación de la ventana en PostgreSQL (ISS-B-14, AR-1/AR-2, design §4).

La agregación se deriva del `metric_type` y corre EN SQL: traer las muestras
al worker para calcular el percentil duplicaría lógica y consumo. Cada
consulta queda acotada al tenant de la regla y a la ventana
`[now - window_minutes, now)` (AR-1).

Tablas locales al contenedor: ADR-0010 prohíbe cross-imports con `api`, así
que este módulo declara solo las columnas que lee.

La sonda HTTP (B.13) ingesta filas sintéticas `TTFB` y `AVAILABILITY` marcadas
con `metadata ? 'probe_target'`. Esas filas se EXCLUYEN del percentil de
latencia (un TTFB sintético no es latencia de usuario real y distorsiona el
p95 de las reglas), pero se CONSERVAN en el promedio de `AVAILABILITY`: la
disponibilidad proviene únicamente de la sonda.
"""

# pylint: disable=not-callable  # percentile_cont/within_group son funciones SQL

from datetime import datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from uuid import UUID

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    SmallInteger,
    false,
    func,
    not_,
    select,
    table,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement

from ml.rules.engine import LATENCY_METRICS, PERCENTILE, Evaluation

_RUM_METRIC = table(
    "rum_metric",
    Column("session_id", PGUUID(as_uuid=True)),
    Column("metric_type_id", SmallInteger),
    Column("value", Float),
    Column("metadata", JSONB),
    Column("timestamp", DateTime(timezone=True)),
)
_USER_SESSION = table(
    "user_session",
    Column("session_id", PGUUID(as_uuid=True)),
    Column("app_id", PGUUID(as_uuid=True)),
    Column("start_timestamp", DateTime(timezone=True)),
)
_JS_EXCEPTION = table(
    "js_exception",
    Column("error_id", PGUUID(as_uuid=True)),
    Column("session_id", PGUUID(as_uuid=True)),
    Column("timestamp", DateTime(timezone=True)),
)


# `rum_metric.value` es DOUBLE PRECISION: `percentile_cont` interpola en
# float8 y devuelve, por ejemplo, 954.9999999999999 para un p95 exacto de 955.
# Sin cuantizar, la comparación inclusiva (AR-3) fallaría justo en el umbral por
# un artefacto binario. Se guarda con 6 decimales, muy por encima de la
# precisión que publica el mensaje (1 decimal).
_OBSERVED_QUANTUM = Decimal("0.000001")


def _round_observed(value: Decimal) -> Decimal:
    """Cuantiza el observado a una precisión estable para comparar y guardar."""
    return value.quantize(_OBSERVED_QUANTUM, rounding=ROUND_HALF_UP)


def _to_decimal(value: float | int | Decimal | None) -> Decimal | None:
    """Convierte el resultado SQL a NUMERIC exacto para comparar y guardar.

    `str(value)` y no `Decimal(float)`: 912.4 debe quedar en 912,4 y no en la
    expansión binaria completa, porque el valor se guarda en `alert` y se
    publica en el mensaje.
    """
    if value is None:
        return None
    if isinstance(value, Decimal):
        return _round_observed(value)
    return _round_observed(Decimal(str(value)))


def _window(now: datetime, window_minutes: int) -> tuple[datetime, datetime]:
    """Ventana `[now - window_minutes, now)` de AR-1."""
    return now - timedelta(minutes=window_minutes), now


def _not_probe() -> ColumnElement[bool]:
    """Predicado: la fila `rum_metric` NO es de la sonda HTTP.

    `coalesce(..., false)` hace que un `metadata` NULL cuente como RUM real:
    `NOT NULL` sería NULL y descartaría las filas del agente.
    """
    return not_(
        func.coalesce(_RUM_METRIC.c.metadata.has_key("probe_target"), false())
    )


async def _percentile(
    session: AsyncSession,
    application_id: UUID,
    metric_type_id: int,
    start: datetime,
    end: datetime,
) -> Evaluation:
    """p95 de `rum_metric.value` (TTFB, FCP, XHR_LATENCY, RAGE_CLICK).

    Excluye las filas de la sonda: su `TTFB` sintético no es latencia de
    usuario real y no debe disparar (ni enmascarar) reglas de latencia.
    """
    p95 = func.percentile_cont(PERCENTILE).within_group(
        _RUM_METRIC.c.value.asc()
    )
    stmt = (
        select(p95.label("observed"), func.count().label("samples"))
        .select_from(
            _RUM_METRIC.join(
                _USER_SESSION,
                _USER_SESSION.c.session_id == _RUM_METRIC.c.session_id,
            )
        )
        .where(
            _USER_SESSION.c.app_id == application_id,
            _RUM_METRIC.c.metric_type_id == metric_type_id,
            _RUM_METRIC.c.timestamp >= start,
            _RUM_METRIC.c.timestamp < end,
            _not_probe(),
        )
    )
    row = (await session.execute(stmt)).one()
    return Evaluation(
        observed=_to_decimal(row.observed), samples=int(row.samples or 0)
    )


async def _average(
    session: AsyncSession,
    application_id: UUID,
    metric_type_id: int,
    start: datetime,
    end: datetime,
) -> Evaluation:
    """`AVG(rum_metric.value)`: uptime de AVAILABILITY (0/1).

    NO excluye la sonda: la disponibilidad proviene únicamente de sus filas.
    """
    stmt = (
        select(
            func.avg(_RUM_METRIC.c.value).label("observed"),
            func.count().label("samples"),
        )
        .select_from(
            _RUM_METRIC.join(
                _USER_SESSION,
                _USER_SESSION.c.session_id == _RUM_METRIC.c.session_id,
            )
        )
        .where(
            _USER_SESSION.c.app_id == application_id,
            _RUM_METRIC.c.metric_type_id == metric_type_id,
            _RUM_METRIC.c.timestamp >= start,
            _RUM_METRIC.c.timestamp < end,
        )
    )
    row = (await session.execute(stmt)).one()
    return Evaluation(
        observed=_to_decimal(row.observed), samples=int(row.samples or 0)
    )


async def _js_exception_rate(
    session: AsyncSession,
    application_id: UUID,
    start: datetime,
    end: datetime,
) -> Evaluation:
    """`count(js_exception) / count(user_session)` en la ventana.

    El denominador son las sesiones INICIADAS en la ventana (design §4); el
    numerador, las excepciones registradas en la ventana. Ambas cuentas están
    scoped al tenant por `user_session.app_id`.
    """
    sessions = (
        select(func.count())
        .select_from(_USER_SESSION)
        .where(
            _USER_SESSION.c.app_id == application_id,
            _USER_SESSION.c.start_timestamp >= start,
            _USER_SESSION.c.start_timestamp < end,
        )
        .scalar_subquery()
    )
    exceptions = (
        select(func.count())
        .select_from(
            _JS_EXCEPTION.join(
                _USER_SESSION,
                _USER_SESSION.c.session_id == _JS_EXCEPTION.c.session_id,
            )
        )
        .where(
            _USER_SESSION.c.app_id == application_id,
            _JS_EXCEPTION.c.timestamp >= start,
            _JS_EXCEPTION.c.timestamp < end,
        )
        .scalar_subquery()
    )
    row = (
        await session.execute(
            select(
                exceptions.label("exceptions"),
                sessions.label("samples"),
            )
        )
    ).one()
    samples = int(row.samples or 0)
    if samples == 0:
        return Evaluation(observed=None, samples=0)
    observed = Decimal(int(row.exceptions or 0)) / Decimal(samples)
    return Evaluation(observed=_round_observed(observed), samples=samples)


async def aggregate_metric(
    session: AsyncSession,
    *,
    application_id: UUID,
    metric_type_id: int,
    metric_name: str,
    window_minutes: int,
    now: datetime,
) -> Evaluation:
    """Agrega la ventana de una regla según el tipo de métrica (AR-2).

    `observed` es NULL cuando la ventana no tiene muestras; el motor lo trata
    como `insufficient` (AR-4).
    """
    start, end = _window(now, window_minutes)
    if metric_name in LATENCY_METRICS:
        return await _percentile(
            session, application_id, metric_type_id, start, end
        )
    if metric_name == "AVAILABILITY":
        return await _average(
            session, application_id, metric_type_id, start, end
        )
    if metric_name == "JS_EXCEPTION_RATE":
        return await _js_exception_rate(session, application_id, start, end)
    raise ValueError(f"unsupported metric type: {metric_name!r}")
