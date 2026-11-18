"""TDD de integración de la agregación por métrica (ISS-B-14, AR-1/AR-2).

Postgres real: la agregación corre EN SQL (design §4), así que el test usa
`aggregate_metric` contra la base migrada y fija:

- `TTFB`, `FCP`, `XHR_LATENCY` y `RAGE_CLICK` por `percentile_cont(0.95)`
  de `rum_metric.value` (AR-2);
- `AVAILABILITY` por `AVG(rum_metric.value)`: 1,1,1,0 → 0,75 (AR-2);
- `JS_EXCEPTION_RATE` por `count(js_exception)/count(user_session)` en la
  ventana (AR-2);
- aislamiento por tenant y ventana `[now - window_minutes, now)` (AR-1);
- ventana vacía: observado NULL y `samples = 0` (AR-1/AR-4).

Las filas se insertan con SQL directo: la agregación no depende de la API de
configuración ni del motor.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import text

from ml.rules.aggregates import aggregate_metric

NOW = datetime(2026, 11, 18, 12, 0, tzinfo=timezone.utc)
WINDOW_MINUTES = 15


async def _application(db_session, name: str) -> UUID:
    app_id = uuid4()
    await db_session.execute(
        text("INSERT INTO application (app_id, name) VALUES (:app_id, :name)"),
        {"app_id": app_id, "name": name},
    )
    await db_session.commit()
    return app_id


async def _metric_type_id(db_session, name: str) -> int:
    result = await db_session.execute(
        text("SELECT metric_type_id FROM metric_type WHERE name = :name"),
        {"name": name},
    )
    return result.scalar_one()


async def _session(db_session, app_id: UUID, *, start: datetime) -> UUID:
    session_id = uuid4()
    await db_session.execute(
        text(
            "INSERT INTO user_session (session_id, app_id, start_timestamp) "
            "VALUES (:session_id, :app_id, :start)"
        ),
        {"session_id": session_id, "app_id": app_id, "start": start},
    )
    await db_session.commit()
    return session_id


async def _metric(
    db_session,
    session_id: UUID,
    metric_type_id: int,
    value: float,
    *,
    timestamp: datetime,
) -> None:
    await db_session.execute(
        text(
            "INSERT INTO rum_metric (metric_id, session_id, metric_type_id, "
            "value, unit, timestamp) "
            "VALUES (:metric_id, :session_id, :metric_type_id, :value, 'ms', "
            ":timestamp)"
        ),
        {
            "metric_id": uuid4(),
            "session_id": session_id,
            "metric_type_id": metric_type_id,
            "value": value,
            "timestamp": timestamp,
        },
    )
    await db_session.commit()


async def _js_exception(
    db_session, session_id: UUID, *, timestamp: datetime
) -> None:
    await db_session.execute(
        text(
            "INSERT INTO js_exception (error_id, session_id, error_type, "
            "message, timestamp) "
            "VALUES (:error_id, :session_id, 'TypeError', 'boom', :timestamp)"
        ),
        {
            "error_id": uuid4(),
            "session_id": session_id,
            "timestamp": timestamp,
        },
    )
    await db_session.commit()


async def _aggregate(
    db_session,
    app_id: UUID,
    metric_type_id: int,
    metric_name: str,
    *,
    window_minutes: int = WINDOW_MINUTES,
    now: datetime = NOW,
):
    return await aggregate_metric(
        db_session,
        application_id=app_id,
        metric_type_id=metric_type_id,
        metric_name=metric_name,
        window_minutes=window_minutes,
        now=now,
    )


# -- AR-2: percentiles de latencia -------------------------------------------


async def test_latency_metrics_use_percentile_cont_p95(db_session):
    """GIVEN diez muestras 100..1000 en la ventana WHEN se agrega TTFB THEN
    el observado es el p95 (955) y samples cuenta las filas de la ventana
    (AR-2)."""
    app_id = await _application(db_session, "agg-p95")
    metric_id = await _metric_type_id(db_session, "TTFB")
    session_id = await _session(db_session, app_id, start=NOW - timedelta(minutes=10))
    for value in (100, 200, 300, 400, 500, 600, 700, 800, 900, 1000):
        await _metric(
            db_session,
            session_id,
            metric_id,
            value,
            timestamp=NOW - timedelta(minutes=5),
        )
    # Filas fuera de [now - 15 min, now): no entran ni al p95 ni al conteo.
    await _metric(
        db_session,
        session_id,
        metric_id,
        99999,
        timestamp=NOW - timedelta(minutes=30),
    )
    await _metric(db_session, session_id, metric_id, 99999, timestamp=NOW)

    evaluation = await _aggregate(db_session, app_id, metric_id, "TTFB")

    assert evaluation.observed == Decimal("955")
    assert evaluation.samples == 10


async def test_all_latency_metrics_use_p95(db_session):
    """AR-2: TTFB, FCP, XHR_LATENCY y RAGE_CLICK se agregan por p95."""
    app_id = await _application(db_session, "agg-latency-types")
    session_id = await _session(db_session, app_id, start=NOW - timedelta(minutes=10))

    for name in ("TTFB", "FCP", "XHR_LATENCY", "RAGE_CLICK"):
        metric_id = await _metric_type_id(db_session, name)
        for value in (100, 200, 300, 400, 500, 600, 700, 800, 900, 1000):
            await _metric(
                db_session,
                session_id,
                metric_id,
                value,
                timestamp=NOW - timedelta(minutes=5),
            )
        evaluation = await _aggregate(db_session, app_id, metric_id, name)
        assert evaluation.observed == Decimal("955"), name
        assert evaluation.samples == 10, name


# -- AR-2: disponibilidad ----------------------------------------------------


async def test_availability_is_the_average_of_the_probe_runs(db_session):
    """GIVEN 4 corridas 1,1,1,0 WHEN se agrega AVAILABILITY THEN el observado
    es 0,75 (AR-2, escenario de disponibilidad)."""
    app_id = await _application(db_session, "agg-availability")
    metric_id = await _metric_type_id(db_session, "AVAILABILITY")
    session_id = await _session(db_session, app_id, start=NOW - timedelta(minutes=10))
    for value in (1.0, 1.0, 1.0, 0.0):
        await _metric(
            db_session,
            session_id,
            metric_id,
            value,
            timestamp=NOW - timedelta(minutes=4),
        )

    evaluation = await _aggregate(db_session, app_id, metric_id, "AVAILABILITY")

    assert evaluation.observed == Decimal("0.75")
    assert evaluation.samples == 4


# -- AR-2: tasa de excepciones JS -------------------------------------------


async def test_js_exception_rate_counts_exceptions_over_sessions(db_session):
    """GIVEN 5 sesiones y 2 excepciones en la ventana WHEN se agrega
    JS_EXCEPTION_RATE THEN la tasa es 0,4 y samples son las sesiones (AR-2)."""
    app_id = await _application(db_session, "agg-js-rate")
    metric_id = await _metric_type_id(db_session, "JS_EXCEPTION_RATE")
    sessions = [
        await _session(db_session, app_id, start=NOW - timedelta(minutes=5))
        for _ in range(5)
    ]
    # Una sesión que arrancó antes de la ventana no entra a la denominación.
    old_session = await _session(
        db_session, app_id, start=NOW - timedelta(minutes=40)
    )
    await _js_exception(db_session, sessions[0], timestamp=NOW - timedelta(minutes=3))
    await _js_exception(db_session, sessions[1], timestamp=NOW - timedelta(minutes=2))
    # Excepción fuera de la ventana: no entra al numerador.
    await _js_exception(
        db_session, old_session, timestamp=NOW - timedelta(minutes=30)
    )

    evaluation = await _aggregate(
        db_session, app_id, metric_id, "JS_EXCEPTION_RATE"
    )

    assert evaluation.observed == Decimal("0.4")
    assert evaluation.samples == 5


# -- AR-1/AR-2: aislamiento por tenant --------------------------------------


async def test_aggregation_is_tenant_scoped(db_session):
    """GIVEN métricas de A y B en la ventana WHEN se evalúa una regla de A
    THEN el observado solo usa las filas de A (AR-2)."""
    app_a = await _application(db_session, "agg-tenant-a")
    app_b = await _application(db_session, "agg-tenant-b")
    metric_id = await _metric_type_id(db_session, "TTFB")
    session_a = await _session(db_session, app_a, start=NOW - timedelta(minutes=10))
    session_b = await _session(db_session, app_b, start=NOW - timedelta(minutes=10))
    for value in (900, 910, 920):
        await _metric(
            db_session,
            session_a,
            metric_id,
            value,
            timestamp=NOW - timedelta(minutes=5),
        )
    for value in (1, 2, 3):
        await _metric(
            db_session,
            session_b,
            metric_id,
            value,
            timestamp=NOW - timedelta(minutes=5),
        )

    evaluation_a = await _aggregate(db_session, app_a, metric_id, "TTFB")
    evaluation_b = await _aggregate(db_session, app_b, metric_id, "TTFB")

    assert evaluation_a.observed == Decimal("919")
    assert evaluation_a.samples == 3
    assert evaluation_b.observed == Decimal("2.9")
    assert evaluation_b.samples == 3


# -- AR-1/AR-4: ventana vacía ------------------------------------------------


async def test_empty_window_has_no_value_and_zero_samples(db_session):
    """GIVEN una aplicación sin métricas en la ventana WHEN se agrega THEN
    observed es NULL y samples = 0 (AR-1/AR-4)."""
    app_id = await _application(db_session, "agg-empty")
    metric_id = await _metric_type_id(db_session, "TTFB")

    evaluation = await _aggregate(db_session, app_id, metric_id, "TTFB")

    assert evaluation.observed is None
    assert evaluation.samples == 0
