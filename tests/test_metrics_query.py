"""TDD: read path de telemetría — TQ-1/TQ-2, OAS-13/OAS-14 (ISS-S3-01).

Strict TDD: escenarios Given/When/Then de la spec → tests red antes de
implementar. Capas: unit (límites de QueryService sin tocar el repo) e
integration (httpx ASGI + Postgres real: shape ML, buckets, app-scoped,
422/401, /metrics/list).
"""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest


def _ts(dt: datetime) -> str:
    """ISO 8601 UTC con zona explícita (contrato date-time)."""
    return dt.isoformat()


async def _make_app_with_key(client, make_admin, name: str):
    """Crea una aplicación + API key vía HTTP (mismo flujo que ingesta).

    Email único por llamada: make_admin usa el mismo default y la constraint
    unique idx_lab_user_email fallaría al crear el segundo admin del test.
    """
    _, token = await make_admin(email=f"admin-{uuid4().hex[:12]}@intellops.local")
    created = await client.post(
        "/applications",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": name},
    )
    assert created.status_code == 201, created.text
    app_id = created.json()["app_id"]
    key_resp = await client.post(
        f"/applications/{app_id}/api-key",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert key_resp.status_code == 201, key_resp.text
    return app_id, key_resp.json()["api_key"]


async def _seed_metric(db_session, app_id, session_id, *, value, ts, metric_type="TTFB"):
    """Seed SQL directo: user_session (si no existe) + rum_metric con
    timestamp controlado (para aserciones de bucket deterministas)."""
    from sqlalchemy import text

    type_id = (
        await db_session.execute(
            text("SELECT metric_type_id FROM metric_type WHERE name = :n"),
            {"n": metric_type},
        )
    ).scalar_one()
    await db_session.execute(
        text(
            "INSERT INTO user_session (session_id, app_id, start_timestamp) "
            "VALUES (:s, :a, :ts) ON CONFLICT (session_id) DO NOTHING"
        ),
        {"s": str(session_id), "a": str(app_id), "ts": ts},
    )
    await db_session.execute(
        text(
            "INSERT INTO rum_metric (metric_id, session_id, metric_type_id, "
            "value, unit, timestamp) VALUES (:m, :s, :tid, :v, 'ms', :ts)"
        ),
        {"m": str(uuid4()), "s": str(session_id), "tid": type_id, "v": value, "ts": ts},
    )
    await db_session.commit()


# -- TQ-2: QueryService — límites y defaults sin tocar el repo -----------------

async def test_service_rejects_out_of_bounds_without_calling_repo():
    """Ventana > 7 días, bucket < 60 s o start >= end DEBEN rechazarse con 422
    invalid_query_range SIN ejecutar la agregación (TQ-2, escenario Rango
    fuera de límite)."""
    from api.domain.exceptions import QueryRangeError
    from api.domain.services.query_service import QueryService

    class _BoomRepo:
        def __init__(self) -> None:
            self.called = False

        async def query_metrics(self, *args, **kwargs):
            self.called = True
            raise AssertionError("el repo no debe llamarse con rango inválido")

        async def list_metric_types(self):
            return []

    repo = _BoomRepo()
    service = QueryService(repo)
    now = datetime.now(timezone.utc)
    for start, end, bucket in [
        (now - timedelta(days=8), now, 300),  # ventana > 7 días
        (now - timedelta(minutes=10), now, 30),  # bucket < 60 s
        (now, now, 60),  # start >= end
    ]:
        with pytest.raises(QueryRangeError) as excinfo:
            await service.query(
                app_id=uuid4(), start=start, end=end, bucket_seconds=bucket
            )
        assert excinfo.value.http_code == 422
        assert excinfo.value.code == "invalid_query_range"
    assert repo.called is False  # la agregación nunca se ejecutó


async def test_service_applies_default_window_and_bucket():
    """Sin start/end/bucket, el servicio DEBE aplicar la ventana default de
    15 minutos y bucket de 60 s antes de delegar (TQ-2)."""
    from api.domain.services.query_service import QueryService

    class _CaptureRepo:
        def __init__(self) -> None:
            self.kwargs = None

        async def query_metrics(self, app_id, start, end, bucket_seconds, metric_type_id=None):
            self.kwargs = {
                "app_id": app_id,
                "start": start,
                "end": end,
                "bucket_seconds": bucket_seconds,
                "metric_type_id": metric_type_id,
            }
            return []

        async def list_metric_types(self):
            return []

    repo = _CaptureRepo()
    service = QueryService(repo)
    app_id = uuid4()

    await service.query(app_id=app_id, start=None, end=None, bucket_seconds=None)

    assert repo.kwargs["app_id"] == app_id
    assert repo.kwargs["bucket_seconds"] == 60
    assert repo.kwargs["end"] - repo.kwargs["start"] == timedelta(minutes=15)
    assert repo.kwargs["end"].tzinfo is not None  # ventana UTC aware


# -- TQ-1: shape ML exacto + app-scoped (OAS-14, aislamiento por key) ----------

async def test_metrics_query_shape_ml_exact_and_app_scoped(
    client, make_admin, db_session
):
    """GET /metrics/query con la key de A y datos de A y B en rango DEBE
    devolver 200 con filas de SOLO A y exactamente los 5 campos del shape ML
    (TQ-1, escenario Shape ML exacto; OAS-14, escenario Aislamiento por key)."""
    app_a, key_a = await _make_app_with_key(client, make_admin, "app-a")
    app_b, _ = await _make_app_with_key(client, make_admin, "app-b")
    ref = datetime.now(timezone.utc).replace(microsecond=0)
    session_a = uuid4()
    await _seed_metric(db_session, app_a, session_a, value=100.0, ts=ref)
    await _seed_metric(db_session, app_b, uuid4(), value=999.0, ts=ref)

    resp = await client.get(
        "/metrics/query",
        headers={"X-API-Key": key_a},
        params={
            "start": _ts(ref - timedelta(minutes=5)),
            "end": _ts(ref + timedelta(minutes=5)),
            "bucket_seconds": 300,
        },
    )

    assert resp.status_code == 200
    rows = resp.json()
    assert len(rows) == 1  # solo la métrica de A (la de B es invisible)
    row = rows[0]
    assert set(row.keys()) == {
        "application_id",
        "metric_type_id",
        "timestamp",
        "value",
        "session_count",
    }
    assert row["application_id"] == app_a
    assert row["value"] == 100.0
    assert row["session_count"] == 1
    assert isinstance(row["metric_type_id"], int)
    assert datetime.fromisoformat(row["timestamp"]).tzinfo is not None


async def test_metrics_query_one_row_per_bucket_with_avg_and_distinct_count(
    client, make_admin, db_session
):
    """Métricas de un tipo en 2 buckets DEBEN devolver una fila por bucket con
    AVG(value) y COUNT(DISTINCT session_id) agregados (TQ-1, escenario
    Agregación por bucket)."""
    app_id, key = await _make_app_with_key(client, make_admin, "bucket-app")
    ref = datetime.now(timezone.utc).replace(microsecond=0)
    # Bucket 1 [ref, ref+60): sesión S1 con 2 métricas (100, 200) + sesión S3
    # con 1 (400) → AVG 700/3, COUNT(DISTINCT session) = 2.
    s1, s3 = uuid4(), uuid4()
    await _seed_metric(db_session, app_id, s1, value=100.0, ts=ref + timedelta(seconds=10))
    await _seed_metric(db_session, app_id, s1, value=200.0, ts=ref + timedelta(seconds=10))
    await _seed_metric(db_session, app_id, s3, value=400.0, ts=ref + timedelta(seconds=20))
    # Bucket 2 [ref+60, ref+120): sesión S2 con 1 métrica (300).
    await _seed_metric(db_session, app_id, uuid4(), value=300.0, ts=ref + timedelta(seconds=70))

    resp = await client.get(
        "/metrics/query",
        headers={"X-API-Key": key},
        params={
            "start": _ts(ref),
            "end": _ts(ref + timedelta(seconds=120)),
            "bucket_seconds": 60,
        },
    )

    assert resp.status_code == 200
    rows = resp.json()
    assert len(rows) == 2  # 1 fila por bucket
    bucket_1, bucket_2 = rows
    assert datetime.fromisoformat(bucket_1["timestamp"]) == ref
    assert bucket_1["value"] == pytest.approx(700.0 / 3.0)
    assert bucket_1["session_count"] == 2  # COUNT(DISTINCT session_id)
    assert datetime.fromisoformat(bucket_2["timestamp"]) == ref + timedelta(seconds=60)
    assert bucket_2["value"] == 300.0
    assert bucket_2["session_count"] == 1


# -- TQ-2/OAS-14: 422 y 401 vía HTTP -------------------------------------------

async def test_metrics_query_422_invalid_range(client, make_admin):
    """Ventana > 7 días, bucket < 60 s y start >= end DEBEN responder 422
    invalid_query_range (TQ-2, escenario Rango fuera de límite)."""
    app_id, key = await _make_app_with_key(client, make_admin, "limit-app")
    now = datetime.now(timezone.utc)

    cases = [
        {  # ventana > 7 días
            "start": _ts(now - timedelta(days=8)),
            "end": _ts(now),
            "bucket_seconds": 300,
        },
        {  # bucket < 60 s
            "start": _ts(now - timedelta(minutes=10)),
            "end": _ts(now),
            "bucket_seconds": 30,
        },
        {  # start >= end
            "start": _ts(now),
            "end": _ts(now),
            "bucket_seconds": 60,
        },
    ]
    for params in cases:
        resp = await client.get(
            "/metrics/query",
            headers={"X-API-Key": key},
            params=params,
        )
        assert resp.status_code == 422
        assert resp.json()["error"]["code"] == "invalid_query_range"


async def test_metrics_query_and_list_401_without_key(client):
    """GET /metrics/query y /metrics/list sin X-API-Key DEBEN responder 401
    invalid_api_key con WWW-Authenticate y sin ejecutar consulta (OAS-14,
    escenario Sin key)."""
    for path in ("/metrics/query", "/metrics/list"):
        resp = await client.get(path)
        assert resp.status_code == 401
        assert resp.json()["error"]["code"] == "invalid_api_key"
        assert resp.headers.get("www-authenticate") == "ApiKey"


# -- OAS-13: /metrics/list — catálogo metric_type ------------------------------

async def test_metrics_list_returns_catalog(client, make_admin):
    """GET /metrics/list con apiKey DEBE devolver 200 con el catálogo
    metric_type completo (metric_type_id, name, description) (OAS-13)."""
    app_id, key = await _make_app_with_key(client, make_admin, "list-app")

    resp = await client.get("/metrics/list", headers={"X-API-Key": key})

    assert resp.status_code == 200
    rows = resp.json()
    assert len(rows) == 5  # catálogo seed de la migración 0001
    assert {r["name"] for r in rows} == {
        "TTFB",
        "FCP",
        "XHR_LATENCY",
        "JS_EXCEPTION_RATE",
        "RAGE_CLICK",
    }
    for row in rows:
        assert set(row.keys()) == {"metric_type_id", "name", "description"}
        assert isinstance(row["metric_type_id"], int)
