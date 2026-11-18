"""TDD: read path de telemetría — TQ-1/TQ-2, OAS-13/OAS-14 (ISS-S3-01).

Strict TDD: escenarios Given/When/Then de la spec → tests red antes de
implementar. Capas: unit (límites de QueryService sin tocar el repo) e
integration (httpx ASGI + Postgres real: shape ML, buckets, app-scoped,
422/401, /metrics/list).
"""

import json
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from api.infrastructure.db.repositories.sqlalchemy_query_repository import (
    _as_float,
    _as_int,
)


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


async def _seed_probe_run(
    db_session,
    app_id,
    *,
    ts,
    value=1.0,
    metadata=None,
    session_id=None,
    metric_type="AVAILABILITY",
):
    """Seed SQL directo de una corrida de la sonda HTTP (B.13, D3).

    Una corrida es UNA fila `rum_metric` del tipo `AVAILABILITY` con unidad
    `count`, valor 1/0 y los campos por ejecución en `metadata` JSONB. La
    sesión sintética (D4) la aporta el caller o se genera aquí; el tenant
    sale de `user_session.app_id`.
    """
    from sqlalchemy import text

    type_id = (
        await db_session.execute(
            text("SELECT metric_type_id FROM metric_type WHERE name = :n"),
            {"n": metric_type},
        )
    ).scalar_one()
    synthetic_session = session_id or uuid4()  # sesión estable por target (D4)
    await db_session.execute(
        text(
            "INSERT INTO user_session (session_id, app_id, start_timestamp) "
            "VALUES (:s, :a, :ts) ON CONFLICT (session_id) DO NOTHING"
        ),
        {"s": str(synthetic_session), "a": str(app_id), "ts": ts},
    )
    await db_session.execute(
        text(
            "INSERT INTO rum_metric (metric_id, session_id, metric_type_id, "
            'value, unit, "metadata", timestamp) VALUES '
            "(:m, :s, :tid, :v, 'count', CAST(:md AS jsonb), :ts)"
        ),
        {
            "m": str(uuid4()),
            "s": str(synthetic_session),
            "tid": type_id,
            "v": value,
            "md": None if metadata is None else json.dumps(metadata),
            "ts": ts,
        },
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
    metric_type completo (metric_type_id, name, description): los cinco tipos
    de la migración 0001 más `AVAILABILITY` de la 0006 (D1), sin regresión
    del read path (OAS-13, B.13/S2)."""
    app_id, key = await _make_app_with_key(client, make_admin, "list-app")

    resp = await client.get("/metrics/list", headers={"X-API-Key": key})

    assert resp.status_code == 200
    rows = resp.json()
    assert len(rows) == 6  # 0001 (cinco tipos) + AVAILABILITY (0006, D1)
    assert {r["name"] for r in rows} == {
        "TTFB",
        "FCP",
        "XHR_LATENCY",
        "JS_EXCEPTION_RATE",
        "RAGE_CLICK",
        "AVAILABILITY",
    }
    for row in rows:
        assert set(row.keys()) == {"metric_type_id", "name", "description"}
        assert isinstance(row["metric_type_id"], int)


# -- T6/B.13 (S2, S3): GET /metrics/probes — corridas de la sonda -------------

async def test_metrics_probes_returns_runs_newest_first_with_metadata(
    client, make_admin, db_session
):
    """GET /metrics/probes DEBE devolver UNA fila por ejecución de la sonda,
    de la más nueva a la más vieja, con target/http_status/outcome/latency_ms
    tomados de `metadata` y `available` derivado de `value == 1` (S2, S3, D3).

    Una métrica de otro tipo del mismo tenant NO es una corrida y no aparece.
    """
    app_id, key = await _make_app_with_key(client, make_admin, "probe-app")
    ref = datetime.now(timezone.utc).replace(microsecond=0)
    # Más vieja: disponible, 200.
    await _seed_probe_run(
        db_session,
        app_id,
        ts=ref + timedelta(seconds=10),
        value=1.0,
        metadata={
            "probe_target": "https://piloto.example/",
            "http_status": 200,
            "outcome": "ok",
            "latency_ms": 123.5,
        },
    )
    # Del medio: indisponible (5xx), latencia alta.
    await _seed_probe_run(
        db_session,
        app_id,
        ts=ref + timedelta(seconds=70),
        value=0.0,
        metadata={
            "probe_target": "https://piloto.example/",
            "http_status": 503,
            "outcome": "http_error",
            "latency_ms": 900,
        },
    )
    # Más nueva: timeout sin respuesta HTTP.
    await _seed_probe_run(
        db_session,
        app_id,
        ts=ref + timedelta(seconds=130),
        value=0.0,
        metadata={
            "probe_target": "https://piloto.example/",
            "http_status": None,
            "outcome": "timeout",
            "latency_ms": 30000.0,
        },
    )
    # Métrica RUM de otro tipo: no es una corrida de la sonda.
    await _seed_metric(
        db_session, app_id, uuid4(), value=100.0, ts=ref + timedelta(seconds=140)
    )

    resp = await client.get("/metrics/probes", headers={"X-API-Key": key})

    assert resp.status_code == 200
    rows = resp.json()
    assert len(rows) == 3  # solo las 3 corridas AVAILABILITY, sin la TTFB
    for row in rows:
        assert set(row.keys()) == {
            "timestamp",
            "target",
            "http_status",
            "outcome",
            "latency_ms",
            "available",
        }
    # Orden: timestamp DESC (más nueva primero).
    timestamps = [datetime.fromisoformat(row["timestamp"]) for row in rows]
    assert timestamps == [
        ref + timedelta(seconds=130),
        ref + timedelta(seconds=70),
        ref + timedelta(seconds=10),
    ]
    newest, middle, oldest = rows
    assert newest["outcome"] == "timeout"
    assert newest["http_status"] is None
    assert newest["latency_ms"] == 30000.0
    assert newest["available"] is False
    assert middle["http_status"] == 503
    assert middle["outcome"] == "http_error"
    assert middle["latency_ms"] == 900.0  # valor entero en metadata → float
    assert middle["available"] is False
    assert oldest["target"] == "https://piloto.example/"
    assert oldest["http_status"] == 200
    assert oldest["outcome"] == "ok"
    assert oldest["latency_ms"] == 123.5
    assert oldest["available"] is True


async def test_metrics_probes_excludes_other_tenant(client, make_admin, db_session):
    """Las corridas de OTRO tenant NO DEBEN aparecer: el tenant se deriva
    EXCLUSIVAMENTE de la API key, nunca de un parámetro del request (S3,
    OAS-14)."""
    app_a, key_a = await _make_app_with_key(client, make_admin, "probe-a")
    app_b, _ = await _make_app_with_key(client, make_admin, "probe-b")
    ref = datetime.now(timezone.utc).replace(microsecond=0)
    await _seed_probe_run(
        db_session,
        app_a,
        ts=ref,
        metadata={"probe_target": "https://a.example/", "outcome": "ok"},
    )
    await _seed_probe_run(
        db_session,
        app_b,
        ts=ref + timedelta(seconds=5),
        metadata={"probe_target": "https://b.example/", "outcome": "ok"},
    )

    resp = await client.get("/metrics/probes", headers={"X-API-Key": key_a})

    assert resp.status_code == 200
    rows = resp.json()
    assert len(rows) == 1  # la corrida de B es invisible para la key de A
    assert rows[0]["target"] == "https://a.example/"


async def test_metrics_probes_tolerates_absent_and_malformed_metadata(
    client, make_admin, db_session
):
    """Una corrida sin `metadata` (o con claves ausentes o no numéricas) DEBE
    devolver nulls en esos campos en vez de romper el endpoint (S3; semántica
    `metadata ->> 'key'`)."""
    app_id, key = await _make_app_with_key(client, make_admin, "probe-null")
    ref = datetime.now(timezone.utc).replace(microsecond=0)
    await _seed_probe_run(db_session, app_id, ts=ref, value=1.0, metadata=None)
    await _seed_probe_run(
        db_session,
        app_id,
        ts=ref + timedelta(seconds=60),
        value=0.0,
        metadata={
            "outcome": "connection_error",
            "http_status": "no-numerico",
            "latency_ms": "n/d",
        },
    )

    resp = await client.get("/metrics/probes", headers={"X-API-Key": key})

    assert resp.status_code == 200
    rows = resp.json()
    assert len(rows) == 2
    partial, without_metadata = rows  # orden: más nueva primero
    assert without_metadata["target"] is None
    assert without_metadata["http_status"] is None
    assert without_metadata["outcome"] is None
    assert without_metadata["latency_ms"] is None
    assert without_metadata["available"] is True  # value 1.0 sin metadata
    assert partial["target"] is None
    assert partial["http_status"] is None  # valor no numérico → null
    assert partial["latency_ms"] is None  # valor no numérico → null
    assert partial["outcome"] == "connection_error"
    assert partial["available"] is False  # value 0.0


def test_as_float_rejects_non_finite_values():
    """R1-001/R3-001: `float("nan")` e `float("inf")` no lanzan, así que un
    `metadata.latency_ms` corrupto se colaba como NaN/Infinity en la respuesta.
    `json.dumps` acepta `NaN` pero emite JSON inválido (RFC 8259): el contrato
    del endpoint es `null` para un valor no interpretable."""
    assert _as_float("nan") is None
    assert _as_float("inf") is None
    assert _as_float("-inf") is None
    assert _as_float("NaN") is None
    assert _as_float("  inf  ") is None
    # Los valores finitos siguen convirtiéndose.
    assert _as_float("279.69") == 279.69
    assert _as_float("0") == 0.0
    assert _as_float(None) is None
    assert _as_float("n/d") is None


async def test_metrics_probes_returns_null_for_non_finite_latency(
    client, make_admin, db_session
):
    """R1-001: una latencia `NaN` persistida en `metadata` NO puede salir en el
    cuerpo: el cliente recibiría JSON inválido. Se expone `null`."""
    app_id, key = await _make_app_with_key(client, make_admin, "probe-nan")
    ref = datetime.now(timezone.utc).replace(microsecond=0)
    await _seed_probe_run(
        db_session,
        app_id,
        ts=ref,
        value=1.0,
        metadata={"outcome": "ok", "http_status": 200, "latency_ms": "NaN"},
    )

    resp = await client.get("/metrics/probes", headers={"X-API-Key": key})

    assert resp.status_code == 200
    assert "NaN" not in resp.text
    assert resp.json()[0]["latency_ms"] is None


async def test_metrics_probes_limit_bounds(client, make_admin, db_session):
    """`limit` fuera de 1..500 DEBE responder 422 (no un clamp silencioso) y
    `limit=1` DEBE devolver exactamente la corrida más nueva (T6)."""
    app_id, key = await _make_app_with_key(client, make_admin, "probe-limit")
    ref = datetime.now(timezone.utc).replace(microsecond=0)
    for offset in (0, 60, 120):
        await _seed_probe_run(
            db_session,
            app_id,
            ts=ref + timedelta(seconds=offset),
            metadata={"probe_target": "https://piloto.example/"},
        )

    for bad_limit in (501, 0, -1):
        rejected = await client.get(
            "/metrics/probes",
            headers={"X-API-Key": key},
            params={"limit": bad_limit},
        )
        assert rejected.status_code == 422, (
            f"limit={bad_limit} DEBE rechazarse con 422 (sin clamp silencioso)"
        )

    one = await client.get(
        "/metrics/probes", headers={"X-API-Key": key}, params={"limit": 1}
    )
    assert one.status_code == 200
    rows = one.json()
    assert len(rows) == 1  # limit aplicado EN SQL
    assert datetime.fromisoformat(rows[0]["timestamp"]) == ref + timedelta(seconds=120)


async def test_service_rejects_out_of_bounds_probe_limit_without_calling_repo():
    """El servicio DEBE rechazar `limit` fuera de 1..500 sin consultar el
    repositorio (misma guarda que TQ-2 para /metrics/query, T6)."""
    from api.domain.exceptions import QueryRangeError
    from api.domain.services.query_service import QueryService

    class _BoomRepo:
        def __init__(self) -> None:
            self.called = False

        async def query_metrics(self, *args, **kwargs):
            raise AssertionError("no aplica")

        async def list_metric_types(self):
            return []

        async def list_probe_runs(self, *args, **kwargs):
            self.called = True
            raise AssertionError("el repo no debe llamarse con limit inválido")

    repo = _BoomRepo()
    service = QueryService(repo)
    for bad_limit in (0, -1, 501):
        with pytest.raises(QueryRangeError) as excinfo:
            await service.list_probe_runs(app_id=uuid4(), limit=bad_limit)
        assert excinfo.value.http_code == 422
        assert excinfo.value.code == "invalid_query_range"
        # R2-002: el 422 tiene que decir el valor rechazado, no solo el rango:
        # si no, el cliente no sabe si mandó 0 o 501.
        assert str(bad_limit) in excinfo.value.message
    assert repo.called is False


# -- ISS-S3-06: casos unitarios faltantes de QueryService ----------------------

class _RecordingQueryRepo:
    """Repo de consulta en memoria que registra con qué se lo llama."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, dict]] = []

    async def query_metrics(self, **kwargs):
        self.calls.append(("query_metrics", kwargs))
        return []

    async def list_metric_types(self):
        self.calls.append(("list_metric_types", {}))
        return ["catalogo"]

    async def list_probe_runs(self, **kwargs):
        self.calls.append(("list_probe_runs", kwargs))
        return ["corrida"]


async def test_service_list_metric_types_delegates_to_repo():
    """`list_metric_types` DEBE delegar en el repo y devolver su resultado tal
    cual (sin filtrar ni reordenar el catálogo)."""
    from api.domain.services.query_service import QueryService

    repo = _RecordingQueryRepo()
    assert await QueryService(repo).list_metric_types() == ["catalogo"]
    assert repo.calls == [("list_metric_types", {})]


async def test_service_list_probe_runs_applies_default_and_forwards_valid_limit():
    """Sin `limit` el servicio DEBE pedir 50; con un `limit` válido (incluidos
    los bordes 1 y 500) DEBE pasarlo intacto junto con el tenant."""
    from api.domain.services.query_service import QueryService

    repo = _RecordingQueryRepo()
    service = QueryService(repo)
    app_id = uuid4()

    assert await service.list_probe_runs(app_id=app_id) == ["corrida"]
    for limit in (1, 500):
        await service.list_probe_runs(app_id=app_id, limit=limit)

    assert [kwargs["limit"] for _, kwargs in repo.calls] == [50, 1, 500]
    assert all(kwargs["app_id"] == app_id for _, kwargs in repo.calls)


async def test_service_query_normalizes_naive_and_offset_datetimes_to_utc():
    """Un `start`/`end` naive DEBE asumirse UTC y uno con otro offset DEBE
    convertirse a UTC antes de delegar (ventana comparable con la BD)."""
    from datetime import timedelta as _td

    from api.domain.services.query_service import QueryService

    repo = _RecordingQueryRepo()
    naive_start = datetime(2026, 11, 8, 12, 0)
    offset_end = datetime(2026, 11, 8, 10, 0, tzinfo=timezone(_td(hours=-3)))

    await QueryService(repo).query(
        app_id=uuid4(), start=naive_start, end=offset_end, bucket_seconds=60
    )

    (_, kwargs), = repo.calls
    assert kwargs["start"] == naive_start.replace(tzinfo=timezone.utc)
    assert kwargs["end"] == datetime(2026, 11, 8, 13, 0, tzinfo=timezone.utc)
    assert kwargs["end"].utcoffset() == _td(0)


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("200", 200),
        ("-1", -1),
        (503, 503),
        (None, None),
        ("", None),
        ("abc", None),
        ("2.5", None),
        ([], None),
    ],
)
def test_as_int_parses_metadata_text_or_returns_none(raw, expected):
    """`_as_int` convierte el texto de `metadata ->> 'key'` a int y devuelve
    None si no es interpretable: un `http_status` corrupto no DEBE romper
    `/metrics/probes` (B.13/T6, ISS-S3-06)."""
    assert _as_int(raw) == expected
