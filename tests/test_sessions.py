"""TDD: lectura de sesiones RUM — GET /sessions y GET /sessions/{session_id}
(ISS-S3-03, #42; ADR-0011).

Capas: unit (límites de SessionService sin tocar el repo, forma de
SessionOut) e integration (httpx ASGI + Postgres real: aislamiento por key,
conteos y última actividad, ventana, limit, 401/403/404/422, sesión creada
por la ingesta con user_id/ip_address/os_version en NULL).
"""

from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest
from sqlalchemy import text

# Campos que la respuesta expone. user_id, ip_address, os_version,
# end_timestamp y duration_ms existen en el DDL pero siempre son NULL en v1:
# NO deben aparecer (ADR-0011).
SESSION_FIELDS = {
    "session_id",
    "application_id",
    "start_timestamp",
    "last_activity_at",
    "user_agent",
    "metric_count",
    "exception_count",
}
DEAD_FIELDS = {"user_id", "ip_address", "os_version", "end_timestamp", "duration_ms"}


def _ts(dt: datetime) -> str:
    """ISO 8601 UTC con zona explícita (contrato date-time)."""
    return dt.isoformat()


async def _make_app_with_key(client, make_admin, name: str):
    """Crea una aplicación + API key vía HTTP; devuelve (app_id, key, token).

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
    return app_id, key_resp.json()["api_key"], token


async def _seed_session(db_session, app_id, *, start, session_id=None, user_agent=None):
    """Seed SQL directo de una fila user_session con start controlado."""
    session_id = session_id or uuid4()
    await db_session.execute(
        text(
            "INSERT INTO user_session (session_id, app_id, start_timestamp, "
            "user_agent) VALUES (:s, :a, :ts, :ua)"
        ),
        {"s": str(session_id), "a": str(app_id), "ts": start, "ua": user_agent},
    )
    await db_session.commit()
    return session_id


async def _seed_metric(db_session, session_id, *, ts, metric_type="TTFB"):
    """Seed SQL directo de una fila rum_metric de la sesión."""
    type_id = (
        await db_session.execute(
            text("SELECT metric_type_id FROM metric_type WHERE name = :n"),
            {"n": metric_type},
        )
    ).scalar_one()
    await db_session.execute(
        text(
            "INSERT INTO rum_metric (metric_id, session_id, metric_type_id, "
            "value, unit, timestamp) VALUES (:m, :s, :tid, 120.0, 'ms', :ts)"
        ),
        {"m": str(uuid4()), "s": str(session_id), "tid": type_id, "ts": ts},
    )
    await db_session.commit()


async def _seed_exception(db_session, session_id, *, ts):
    """Seed SQL directo de una fila js_exception de la sesión."""
    await db_session.execute(
        text(
            "INSERT INTO js_exception (error_id, session_id, error_type, "
            "message, timestamp) VALUES (:e, :s, 'TypeError', 'boom', :ts)"
        ),
        {"e": str(uuid4()), "s": str(session_id), "ts": ts},
    )
    await db_session.commit()


# -- Unit: SessionService — límites y defaults sin tocar el repo --------------

class _BoomRepo:
    """Repo que falla si se lo llama: prueba que la guarda corre antes."""

    def __init__(self) -> None:
        self.called = False

    async def list_sessions(self, *args, **kwargs):
        self.called = True
        raise AssertionError("el repo no debe llamarse con parámetros inválidos")

    async def get_session(self, *args, **kwargs):
        self.called = True
        raise AssertionError("no aplica")


class _CaptureRepo:
    """Repo que registra los argumentos con los que se lo llama."""

    def __init__(self, result=None) -> None:
        self.kwargs = None
        self.result = result

    async def list_sessions(self, app_id, start, end, limit):
        self.kwargs = {"app_id": app_id, "start": start, "end": end, "limit": limit}
        return []

    async def get_session(self, app_id, session_id):
        self.kwargs = {"app_id": app_id, "session_id": session_id}
        return self.result


async def test_service_rejects_invalid_window_and_limit_without_calling_repo():
    """start >= end, ventana > 7 días y limit fuera de 1..500 DEBEN
    rechazarse con 422 invalid_query_range SIN consultar el repositorio."""
    from api.domain.exceptions import QueryRangeError
    from api.domain.services.session_service import SessionService

    repo = _BoomRepo()
    service = SessionService(repo)
    now = datetime.now(timezone.utc)
    cases = [
        {"start": now, "end": now},  # start >= end
        {"start": now - timedelta(days=8), "end": now},  # ventana > 7 días
        {"limit": 0},
        {"limit": 501},
    ]
    for kwargs in cases:
        with pytest.raises(QueryRangeError) as excinfo:
            await service.list_sessions(app_id=uuid4(), **kwargs)
        assert excinfo.value.http_code == 422
        assert excinfo.value.code == "invalid_query_range"
    assert repo.called is False


async def test_service_limit_error_names_the_rejected_value():
    """El 422 de limit DEBE decir el valor rechazado, no solo el rango."""
    from api.domain.exceptions import QueryRangeError
    from api.domain.services.session_service import SessionService

    with pytest.raises(QueryRangeError) as excinfo:
        await SessionService(_BoomRepo()).list_sessions(app_id=uuid4(), limit=501)
    assert "501" in excinfo.value.message


async def test_service_applies_default_window_and_limit():
    """Sin start/end/limit, el servicio DEBE pedir 24 h hasta ahora, en UTC
    aware, y limit 50."""
    from api.domain.services.session_service import SessionService

    repo = _CaptureRepo()
    app_id = uuid4()
    await SessionService(repo).list_sessions(app_id=app_id)

    assert repo.kwargs["app_id"] == app_id
    assert repo.kwargs["limit"] == 50
    assert repo.kwargs["end"] - repo.kwargs["start"] == timedelta(hours=24)
    assert repo.kwargs["end"].tzinfo is not None


async def test_service_normalizes_naive_datetimes_to_utc():
    """Un datetime naive DEBE asumirse UTC antes de delegar."""
    from api.domain.services.session_service import SessionService

    repo = _CaptureRepo()
    naive_end = datetime(2026, 11, 1, 12, 0, 0)
    await SessionService(repo).list_sessions(
        app_id=uuid4(), start=naive_end - timedelta(hours=1), end=naive_end
    )

    assert repo.kwargs["end"] == naive_end.replace(tzinfo=timezone.utc)
    assert repo.kwargs["start"].tzinfo is not None


async def test_service_get_session_missing_raises_404_session_not_found():
    """Si el repo no encuentra la sesión del tenant, el servicio DEBE
    responder 404 session_not_found (inexistente y ajena son lo mismo)."""
    from api.domain.exceptions import NotFoundError
    from api.domain.services.session_service import SessionService

    repo = _CaptureRepo(result=None)
    app_id, session_id = uuid4(), uuid4()
    with pytest.raises(NotFoundError) as excinfo:
        await SessionService(repo).get_session(app_id=app_id, session_id=session_id)

    assert excinfo.value.http_code == 404
    assert excinfo.value.code == "session_not_found"
    assert repo.kwargs == {"app_id": app_id, "session_id": session_id}


def test_session_out_exposes_no_dead_fields():
    """SessionOut NO DEBE declarar campos que en v1 siempre son NULL
    (ADR-0011): sugerirían una funcionalidad que no existe."""
    from api.presentation.schemas.session import SessionOut

    assert set(SessionOut.model_fields) == SESSION_FIELDS
    assert not DEAD_FIELDS & set(SessionOut.model_fields)


# -- Integration: GET /sessions -----------------------------------------------

async def test_list_sessions_is_app_scoped_with_counts_and_last_activity(
    client, make_admin, db_session
):
    """GET /sessions con la key de A DEBE devolver solo las sesiones de A,
    la más nueva primero, con conteos y última actividad correctos."""
    app_a, key_a, _ = await _make_app_with_key(client, make_admin, "app-a")
    app_b, _, _ = await _make_app_with_key(client, make_admin, "app-b")
    ref = datetime.now(timezone.utc).replace(microsecond=0) - timedelta(hours=1)

    older = await _seed_session(db_session, app_a, start=ref, user_agent="ua-a")
    await _seed_metric(db_session, older, ts=ref + timedelta(seconds=5))
    await _seed_metric(db_session, older, ts=ref + timedelta(seconds=10), metric_type="FCP")
    await _seed_exception(db_session, older, ts=ref + timedelta(seconds=40))
    newer = await _seed_session(db_session, app_a, start=ref + timedelta(minutes=5))
    await _seed_metric(db_session, newer, ts=ref + timedelta(minutes=5, seconds=3))
    foreign = await _seed_session(db_session, app_b, start=ref + timedelta(minutes=1))
    await _seed_metric(db_session, foreign, ts=ref + timedelta(minutes=1))

    resp = await client.get("/sessions", headers={"X-API-Key": key_a})

    assert resp.status_code == 200, resp.text
    rows = resp.json()
    assert [row["session_id"] for row in rows] == [str(newer), str(older)]
    for row in rows:
        assert set(row) == SESSION_FIELDS
        assert row["application_id"] == app_a

    newer_row, older_row = rows
    assert older_row["metric_count"] == 2
    assert older_row["exception_count"] == 1
    assert older_row["user_agent"] == "ua-a"
    # La excepción es lo más reciente de la sesión: GREATEST entre tablas.
    assert datetime.fromisoformat(older_row["last_activity_at"]) == ref + timedelta(
        seconds=40
    )
    assert datetime.fromisoformat(older_row["start_timestamp"]) == ref
    assert newer_row["metric_count"] == 1
    assert newer_row["exception_count"] == 0
    assert datetime.fromisoformat(newer_row["last_activity_at"]) == ref + timedelta(
        minutes=5, seconds=3
    )


async def test_list_sessions_without_activity_reports_zero_and_null(
    client, make_admin, db_session
):
    """Una sesión sin métricas ni excepciones DEBE listarse con conteos en 0
    y last_activity_at null (no se inventa actividad)."""
    app_id, key, _ = await _make_app_with_key(client, make_admin, "empty-app")
    start = datetime.now(timezone.utc).replace(microsecond=0) - timedelta(minutes=10)
    session_id = await _seed_session(db_session, app_id, start=start)

    resp = await client.get("/sessions", headers={"X-API-Key": key})

    assert resp.status_code == 200
    (row,) = resp.json()
    assert row["session_id"] == str(session_id)
    assert row["metric_count"] == 0
    assert row["exception_count"] == 0
    assert row["last_activity_at"] is None
    assert row["user_agent"] is None


async def test_list_sessions_filters_by_start_window(client, make_admin, db_session):
    """La ventana filtra por start_timestamp en [start, end): el default
    (24 h) deja afuera una sesión de hace 2 días y una ventana explícita
    deja afuera la que empieza justo en `end`."""
    app_id, key, _ = await _make_app_with_key(client, make_admin, "window-app")
    now = datetime.now(timezone.utc).replace(microsecond=0)
    old = await _seed_session(db_session, app_id, start=now - timedelta(days=2))
    recent = await _seed_session(db_session, app_id, start=now - timedelta(hours=1))

    default = await client.get("/sessions", headers={"X-API-Key": key})
    assert [row["session_id"] for row in default.json()] == [str(recent)]

    explicit = await client.get(
        "/sessions",
        headers={"X-API-Key": key},
        params={
            "start": _ts(now - timedelta(days=3)),
            "end": _ts(now - timedelta(hours=1)),  # exclusivo: deja afuera `recent`
        },
    )
    assert explicit.status_code == 200
    assert [row["session_id"] for row in explicit.json()] == [str(old)]


async def test_list_sessions_limit_bounds_and_newest_first(client, make_admin, db_session):
    """limit fuera de 1..500 DEBE responder 422 invalid_query_range con el
    contrato ErrorResponse (sin clamp) y limit=1 DEBE devolver solo la sesión
    más nueva."""
    app_id, key, _ = await _make_app_with_key(client, make_admin, "limit-app")
    ref = datetime.now(timezone.utc).replace(microsecond=0) - timedelta(hours=2)
    for offset in (0, 10, 20):
        newest = await _seed_session(
            db_session, app_id, start=ref + timedelta(minutes=offset)
        )

    for bad_limit in (0, -1, 501):
        rejected = await client.get(
            "/sessions", headers={"X-API-Key": key}, params={"limit": bad_limit}
        )
        assert rejected.status_code == 422, f"limit={bad_limit} DEBE dar 422"
        # Contrato ErrorResponse del servicio, no el {"detail": [...]} de la
        # validación de FastAPI (review de la PR de ISS-S3-03).
        error = rejected.json()["error"]
        assert error["code"] == "invalid_query_range"
        assert str(bad_limit) in error["message"]

    one = await client.get("/sessions", headers={"X-API-Key": key}, params={"limit": 1})
    assert one.status_code == 200
    assert [row["session_id"] for row in one.json()] == [str(newest)]


async def test_list_sessions_422_invalid_window(client, make_admin):
    """start >= end y ventana > 7 días DEBEN responder 422
    invalid_query_range con el contrato ErrorResponse."""
    _, key, _ = await _make_app_with_key(client, make_admin, "range-app")
    now = datetime.now(timezone.utc)
    for params in (
        {"start": _ts(now), "end": _ts(now)},
        {"start": _ts(now - timedelta(days=8)), "end": _ts(now)},
    ):
        resp = await client.get("/sessions", headers={"X-API-Key": key}, params=params)
        assert resp.status_code == 422
        assert resp.json()["error"]["code"] == "invalid_query_range"


# -- Integration: GET /sessions/{session_id} ----------------------------------

async def test_get_session_returns_own_session(client, make_admin, db_session):
    """GET /sessions/{id} de una sesión propia DEBE devolver 200 con la
    misma forma que el listado."""
    app_id, key, _ = await _make_app_with_key(client, make_admin, "detail-app")
    start = datetime.now(timezone.utc).replace(microsecond=0) - timedelta(minutes=30)
    session_id = await _seed_session(db_session, app_id, start=start, user_agent="ua")
    await _seed_metric(db_session, session_id, ts=start + timedelta(seconds=2))

    resp = await client.get(f"/sessions/{session_id}", headers={"X-API-Key": key})

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert set(body) == SESSION_FIELDS
    assert body["session_id"] == str(session_id)
    assert body["application_id"] == app_id
    assert body["metric_count"] == 1
    assert body["exception_count"] == 0


async def test_get_session_of_other_tenant_is_404_not_403(client, make_admin, db_session):
    """Una sesión de otra aplicación DEBE responder 404 session_not_found,
    igual que una inexistente: no se revela que existe (ADR-0003)."""
    app_a, _, _ = await _make_app_with_key(client, make_admin, "owner-app")
    _, key_b, _ = await _make_app_with_key(client, make_admin, "other-app")
    start = datetime.now(timezone.utc) - timedelta(minutes=5)
    foreign = await _seed_session(db_session, app_a, start=start)

    cross = await client.get(f"/sessions/{foreign}", headers={"X-API-Key": key_b})
    missing = await client.get(f"/sessions/{uuid4()}", headers={"X-API-Key": key_b})

    for resp in (cross, missing):
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "session_not_found"
    assert cross.json() == missing.json()  # indistinguibles


async def test_get_session_invalid_uuid_is_422(client, make_admin):
    """Un session_id que no es UUID DEBE rechazarse con 422 sin consultar."""
    _, key, _ = await _make_app_with_key(client, make_admin, "uuid-app")
    resp = await client.get("/sessions/not-a-uuid", headers={"X-API-Key": key})
    assert resp.status_code == 422


# -- Integration: autenticación (mismo guard que /metrics/*) ------------------

async def test_sessions_401_without_key(client):
    """Sin X-API-Key ambos paths DEBEN responder 401 invalid_api_key con
    WWW-Authenticate."""
    for path in ("/sessions", f"/sessions/{uuid4()}"):
        resp = await client.get(path)
        assert resp.status_code == 401
        assert resp.json()["error"]["code"] == "invalid_api_key"
        assert resp.headers.get("www-authenticate") == "ApiKey"


async def test_sessions_403_app_inactive(client, make_admin):
    """Key válida de una aplicación inactiva DEBE responder 403 app_inactive."""
    app_id, key, token = await _make_app_with_key(client, make_admin, "inactive-app")
    deactivated = await client.put(
        f"/applications/{app_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"is_active": False},
    )
    assert deactivated.status_code == 200

    resp = await client.get("/sessions", headers={"X-API-Key": key})
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "app_inactive"


# -- Integration: la sesión la crea la ingesta (sin POST, ADR-0011) -----------

async def test_session_created_by_ingest_is_listed_with_dead_columns_null(
    client, make_admin, db_session
):
    """Una sesión creada por el worker de ingesta DEBE aparecer en
    GET /sessions, y user_id, ip_address, os_version, end_timestamp y
    duration_ms DEBEN quedar NULL aunque el payload traiga esas claves en
    metadata: nunca se toman del payload (ADR-0011)."""
    from api.domain.services.ingest_normalizer import normalize_rum_event
    from api.infrastructure.db.repositories.sqlalchemy_ingest_repository import (
        SQLAlchemyIngestRepository,
    )
    from api.infrastructure.ingest.counters import IngestCounters
    from api.infrastructure.ingest.queue import AsyncioIngestQueue, QueuedEvent

    app_id, key, _ = await _make_app_with_key(client, make_admin, "ingest-app")
    session_id = str(uuid4())
    event_ts = datetime.now(timezone.utc).replace(microsecond=0) - timedelta(minutes=1)
    payload = normalize_rum_event(
        {
            "schema_version": "1.0",
            "timestamp": event_ts.isoformat(),
            "session_id": session_id,
            "metrics": [{"type": "TTFB", "value": 210.0, "unit": "ms"}],
            "metadata": {
                "user_agent": "Mozilla/5.0",
                "user_id": str(uuid4()),
                "ip_address": "203.0.113.7",
                "os_version": "Android 14",
            },
        }
    )

    queue = AsyncioIngestQueue(
        maxsize=10,
        worker_count=1,
        repository_factory=SQLAlchemyIngestRepository,
        counters=IngestCounters(),
    )
    await queue.start()
    await queue.enqueue(
        QueuedEvent(
            batch_id=uuid4(),
            index=0,
            tenant_app_id=UUID(app_id),
            kind="metric",
            payload=payload,
        )
    )
    await queue.close()
    await queue.join(timeout=5.0)

    resp = await client.get("/sessions", headers={"X-API-Key": key})
    assert resp.status_code == 200, resp.text
    (row,) = resp.json()
    assert row["session_id"] == session_id
    assert row["user_agent"] == "Mozilla/5.0"
    assert row["metric_count"] == 1
    assert datetime.fromisoformat(row["start_timestamp"]) == event_ts

    stored = (
        await db_session.execute(
            text(
                "SELECT user_id, ip_address, os_version, end_timestamp, "
                "duration_ms FROM user_session WHERE session_id = :s"
            ),
            {"s": session_id},
        )
    ).one()
    assert tuple(stored) == (None, None, None, None, None)
