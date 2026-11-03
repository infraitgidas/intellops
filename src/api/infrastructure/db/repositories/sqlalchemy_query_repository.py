"""Query repository SQLAlchemy async — read path app-scoped (DD-9, TQ-1).

`query_metrics` agrega EN SQL (una sola sentencia, sin materializar filas en
el proceso): JOIN `user_session`→`rum_metric` con `app_id = tenant`, GROUP BY
`metric_type_id` + bucket temporal (epoch anclado a `:start`), `AVG(value)` y
`COUNT(DISTINCT session_id)` → shape ML C6 `MetricAggregate`. Los índices
existentes (`idx_user_session_app_id`, `idx_rum_metric_*`) acotan el plan;
la ventana default (15 min) escanea miles de filas → < 2 s, CPU-only (TQ-2).

`list_metric_types` devuelve el catálogo `metric_type` (id, name, description)
para `GET /metrics/list` (OAS-13). Sin DDL nuevo.

`list_probe_runs` (B.13/T6, S2/S3) devuelve las corridas de la sonda HTTP: una
fila `rum_metric` del tipo `AVAILABILITY` por ejecución, con los campos por
ejecución en `metadata` JSONB leídos con semántica `->>` (clave ausente →
NULL). El filtro por tipo (`JOIN metric_type ... name = 'AVAILABILITY'`), el
tenant (`JOIN user_session`), el orden (`timestamp DESC`) y el `LIMIT` se
resuelven EN SQL: el proceso nunca filtra una lista larga en memoria.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    SmallInteger,
    Text,
    bindparam,
    func,
    select,
    table,
    text,
)
from sqlalchemy.ext.asyncio import AsyncSession

from api.domain.entities.rum_metric import RumMetric
from api.domain.entities.user_session import UserSession
from api.domain.repositories.query_repository import (
    MetricAggregate,
    MetricTypeInfo,
    ProbeRun,
    QueryRepository,
)

# B.13/D1: nombre del tipo de métrica que registra cada corrida de la sonda.
PROBE_METRIC_TYPE_NAME = "AVAILABILITY"

# `metric_type` no tiene entidad ORM (es un catálogo sin DDL propio de la capa
# de dominio): se referencia como TableClause liviano para el JOIN por nombre.
_METRIC_TYPE = table(
    "metric_type",
    Column("metric_type_id", SmallInteger),
    Column("name", Text),
)


def _as_int(raw: Any) -> int | None:
    """Convierte el texto de `metadata ->> 'key'` a int (None si no se puede).

    Un `metadata` malformado no DEBE romper el endpoint (B.13/T6): el valor
    no interpretable se expone como null, igual que la clave ausente.
    """
    if raw is None:
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def _as_float(raw: Any) -> float | None:
    """Convierte el texto de `metadata ->> 'key'` a float (None si no se puede)."""
    if raw is None:
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


class SQLAlchemyQueryRepository(QueryRepository):
    """QueryRepository sobre AsyncSession (PostgreSQL, asyncpg)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def query_metrics(
        self,
        app_id: UUID,
        start: datetime,
        end: datetime,
        bucket_seconds: int,
        metric_type_id: int | None = None,
    ) -> list[MetricAggregate]:
        """Métricas de `app_id` agregadas por bucket temporal (DD-9/TQ-1).

        El bucket se ancla al inicio de la ventana (`:start`): determinista y
        alineado al request, no a medianoche UTC.
        """
        ts_type = DateTime(timezone=True)
        start_p = bindparam("start", type_=ts_type)
        end_p = bindparam("end", type_=ts_type)
        bucket_p = bindparam("bucket_s")
        epoch_start = func.extract("epoch", start_p)
        epoch_ts = func.extract("epoch", RumMetric.timestamp)
        bucket_expr = func.to_timestamp(
            epoch_start
            + func.floor((epoch_ts - epoch_start) / bucket_p) * bucket_p
        )

        stmt = (
            select(
                UserSession.app_id.label("application_id"),
                RumMetric.metric_type_id.label("metric_type_id"),
                bucket_expr.label("timestamp"),
                func.avg(RumMetric.value).cast(Float).label("value"),
                func.count(func.distinct(RumMetric.session_id)).label(
                    "session_count"
                ),
            )
            .join(UserSession, UserSession.session_id == RumMetric.session_id)
            .where(
                UserSession.app_id == bindparam("app_id"),
                RumMetric.timestamp >= start_p,
                RumMetric.timestamp < end_p,
            )
            .group_by(UserSession.app_id, RumMetric.metric_type_id, bucket_expr)
            .order_by(bucket_expr, RumMetric.metric_type_id)
        )
        if metric_type_id is not None:
            stmt = stmt.where(RumMetric.metric_type_id == metric_type_id)

        result = await self._session.execute(
            stmt,
            {
                "app_id": app_id,
                "start": start,
                "end": end,
                "bucket_s": bucket_seconds,
            },
        )
        return [
            MetricAggregate(
                application_id=row.application_id,
                metric_type_id=row.metric_type_id,
                timestamp=row.timestamp,
                value=row.value,
                session_count=row.session_count,
            )
            for row in result
        ]

    async def list_metric_types(self) -> list[MetricTypeInfo]:
        """Catálogo metric_type completo (OAS-13: /metrics/list)."""
        result = await self._session.execute(
            text(
                "SELECT metric_type_id, name, description "
                "FROM metric_type ORDER BY metric_type_id"
            )
        )
        return [
            MetricTypeInfo(
                metric_type_id=row.metric_type_id,
                name=row.name,
                description=row.description,
            )
            for row in result
        ]

    async def list_probe_runs(self, app_id: UUID, limit: int) -> list[ProbeRun]:
        """Corridas de la sonda HTTP de `app_id` (B.13/T6, S2/S3).

        Una sola sentencia: JOIN al catálogo por `name = 'AVAILABILITY'`
        (D1) y a `user_session` por el tenant (OAS-14), `metadata ->> 'key'`
        para los campos por ejecución (D3), `ORDER BY timestamp DESC` y
        `LIMIT` aplicados en SQL. `available` se deriva de `value == 1`.
        """
        metadata = RumMetric.metadata_json  # columna física "metadata" (JSONB)
        stmt = (
            select(
                RumMetric.timestamp.label("timestamp"),
                metadata["probe_target"].astext.label("target"),
                metadata["http_status"].astext.label("http_status_raw"),
                metadata["outcome"].astext.label("outcome"),
                metadata["latency_ms"].astext.label("latency_ms_raw"),
                RumMetric.value.label("value"),
            )
            .join(
                _METRIC_TYPE,
                _METRIC_TYPE.c.metric_type_id == RumMetric.metric_type_id,
            )
            .join(UserSession, UserSession.session_id == RumMetric.session_id)
            .where(
                UserSession.app_id == bindparam("app_id"),
                _METRIC_TYPE.c.name == PROBE_METRIC_TYPE_NAME,
            )
            .order_by(RumMetric.timestamp.desc())
            .limit(bindparam("limit"))
        )
        result = await self._session.execute(stmt, {"app_id": app_id, "limit": limit})
        return [
            ProbeRun(
                timestamp=row.timestamp,
                target=row.target,
                http_status=_as_int(row.http_status_raw),
                outcome=row.outcome,
                latency_ms=_as_float(row.latency_ms_raw),
                available=row.value == 1,
            )
            for row in result
        ]
