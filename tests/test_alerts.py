"""TDD: lectura de alertas — GET /alerts (ISS-B-03, #68; ADR-0012).

Capas: unit (AlertService con repos dobles: límites y filtro de estado antes
del repo; forma de AlertOut sin recipient) e integration (httpx ASGI +
Postgres real: aislamiento por key, orden por created_at, ventana, filtro por
estado, canal null hasta el despacho, alerta sin anomalía, 401/403/422).
"""

from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest
from sqlalchemy import text

from api.domain.exceptions import QueryRangeError
from api.domain.repositories.alert_repository import ALERT_SEVERITIES, ALERT_STATUSES
from api.domain.services.alert_service import AlertService

ALERT_FIELDS = {
    "alert_id",
    "application_id",
    "anomaly_id",
    "severity",
    "message",
    "status",
    "channel",
    "created_at",
    "sent_at",
}


def _ts(dt: datetime) -> str:
    """ISO 8601 UTC con zona explícita (contrato date-time)."""
    return dt.isoformat()


# -- Unit: AlertService --------------------------------------------------------

class _BoomRepo:
    """Repo que falla si se lo llama: prueba que la guarda corre antes."""

    called = False

    async def list_alerts(self, *args, **kwargs):
        self.called = True
        raise AssertionError("el repo no debe llamarse con parámetros inválidos")


class _CaptureRepo:
    """Repo que registra los argumentos con los que se lo llama."""

    def __init__(self) -> None:
        self.kwargs = None

    async def list_alerts(self, app_id, start, end, limit, status=None):
        self.kwargs = {
            "app_id": app_id,
            "start": start,
            "end": end,
            "limit": limit,
            "status": status,
        }
        return []


@pytest.mark.parametrize(
    "kwargs",
    [
        {"start": datetime(2026, 11, 1, tzinfo=timezone.utc),
         "end": datetime(2026, 11, 1, tzinfo=timezone.utc)},
        {"start": datetime(2026, 10, 1, tzinfo=timezone.utc),
         "end": datetime(2026, 11, 1, tzinfo=timezone.utc)},
        {"limit": 0},
        {"limit": 501},
        {"status": "acknowledged"},
        {"status": "Pending"},  # el filtro es en minúsculas, como lo expone la API
        {"status": ""},
    ],
)
async def test_service_rejects_invalid_params_without_calling_repo(kwargs):
    """Ventana inválida, limit fuera de rango o estado desconocido DEBEN dar
    422 invalid_query_range sin consultar el repositorio."""
    repo = _BoomRepo()
    with pytest.raises(QueryRangeError) as excinfo:
        await AlertService(repo).list_alerts(app_id=uuid4(), **kwargs)
    assert excinfo.value.code == "invalid_query_range"
    assert repo.called is False


async def test_service_status_error_names_the_rejected_value():
    """El 422 de status DEBE decir el valor rechazado y los válidos."""
    with pytest.raises(QueryRangeError) as excinfo:
        await AlertService(_BoomRepo()).list_alerts(app_id=uuid4(), status="acked")
    assert "'acked'" in excinfo.value.message
    assert "pending, sent, failed" in excinfo.value.message


@pytest.mark.parametrize("status", [None, *ALERT_STATUSES])
async def test_service_delegates_defaults_and_status(status):
    """Sin ventana ni limit, el servicio DEBE pedir 24 h y limit 50, y pasar
    el estado (o None) y el tenant tal cual."""
    repo = _CaptureRepo()
    app_id = uuid4()

    assert await AlertService(repo).list_alerts(app_id=app_id, status=status) == []

    assert repo.kwargs["app_id"] == app_id
    assert repo.kwargs["limit"] == 50
    assert repo.kwargs["status"] == status
    assert repo.kwargs["end"] - repo.kwargs["start"] == timedelta(hours=24)


def test_alert_out_has_no_recipient_and_closed_enums():
    """AlertOut NO DEBE exponer recipient (ADR-0012) y DEBE rechazar una
    severidad o un estado fuera del dominio."""
    from pydantic import ValidationError

    from api.presentation.schemas.alert import AlertOut

    assert set(AlertOut.model_fields) == ALERT_FIELDS
    assert "recipient" not in AlertOut.model_fields

    base = {
        "alert_id": uuid4(),
        "application_id": uuid4(),
        "severity": "high",
        "message": "TTFB p75 > 800 ms",
        "status": "pending",
        "created_at": datetime(2026, 11, 1, tzinfo=timezone.utc),
    }
    pending = AlertOut(**base)
    assert pending.anomaly_id is None
    assert pending.channel is None
    assert pending.sent_at is None
    for field, bad in (("severity", "urgent"), ("status", "Pending"), ("channel", "sms")):
        with pytest.raises(ValidationError):
            AlertOut(**{**base, field: bad})


def test_alert_severities_match_migration_check():
    """El dominio de severidad DEBE ser el de ck_alert_severity (0007)."""
    assert ALERT_SEVERITIES == ("low", "medium", "high", "critical")


# -- Integration: helpers ------------------------------------------------------

async def _make_app_with_key(client, make_admin, name: str):
    """Crea una aplicación + API key vía HTTP; devuelve (app_id, key, token)."""
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


async def _seed_alert(
    db_session,
    app_id,
    *,
    created_at,
    status="Pending",
    severity="high",
    channel=None,
    recipient=None,
    sent_at=None,
    anomaly_id=None,
) -> UUID:
    """Seed SQL directo de una alerta (forma de la migración 0007)."""
    alert_id = uuid4()
    await db_session.execute(
        text(
            "INSERT INTO alert (alert_id, application_id, anomaly_id, severity, "
            "recipient, channel_id, message, status_id, created_at, sent_at) "
            "VALUES (:id, :app, :anomaly, :severity, :recipient, "
            "(SELECT channel_id FROM alert_channel WHERE name = :channel), "
            "'TTFB p75 > 800 ms', "
            "(SELECT status_id FROM alert_status WHERE name = :status), "
            ":created_at, :sent_at)"
        ),
        {
            "id": str(alert_id),
            "app": str(app_id),
            "anomaly": None if anomaly_id is None else str(anomaly_id),
            "severity": severity,
            "recipient": recipient,
            "channel": channel,
            "status": status,
            "created_at": created_at,
            "sent_at": sent_at,
        },
    )
    await db_session.commit()
    return alert_id


# -- Integration: GET /alerts --------------------------------------------------

async def test_list_alerts_is_app_scoped_newest_first(client, make_admin, db_session):
    """GET /alerts con la key de A DEBE devolver solo las alertas de A, la
    más nueva primero, con estado y canal en minúsculas y sin recipient."""
    app_a, key_a, _ = await _make_app_with_key(client, make_admin, "alert-a")
    app_b, _, _ = await _make_app_with_key(client, make_admin, "alert-b")
    now = datetime.now(timezone.utc).replace(microsecond=0)

    pending = await _seed_alert(db_session, app_a, created_at=now - timedelta(hours=1))
    sent = await _seed_alert(
        db_session,
        app_a,
        created_at=now - timedelta(hours=3),
        status="Sent",
        severity="critical",
        channel="Telegram",
        recipient="chat-123",
        sent_at=now - timedelta(hours=3) + timedelta(seconds=4),
    )
    await _seed_alert(db_session, app_b, created_at=now - timedelta(hours=2))

    resp = await client.get("/alerts", headers={"X-API-Key": key_a})

    assert resp.status_code == 200, resp.text
    rows = resp.json()
    assert [row["alert_id"] for row in rows] == [str(pending), str(sent)]
    for row in rows:
        assert set(row) == ALERT_FIELDS
        assert row["application_id"] == app_a
        assert row["anomaly_id"] is None  # alerta de umbral, sin anomalía
        assert row["message"] == "TTFB p75 > 800 ms"

    pending_row, sent_row = rows
    assert pending_row["status"] == "pending"
    assert pending_row["severity"] == "high"
    assert pending_row["channel"] is None
    assert pending_row["sent_at"] is None
    assert sent_row["status"] == "sent"
    assert sent_row["severity"] == "critical"
    assert sent_row["channel"] == "telegram"
    assert datetime.fromisoformat(sent_row["sent_at"]) == (
        now - timedelta(hours=3) + timedelta(seconds=4)
    )
    assert "chat-123" not in resp.text


async def test_list_alerts_window_and_status_filter(client, make_admin, db_session):
    """La ventana filtra por created_at en [start, end) (default 24 h) y
    status deja solo ese estado."""
    app_id, key, _ = await _make_app_with_key(client, make_admin, "alert-window")
    now = datetime.now(timezone.utc).replace(microsecond=0)
    old = await _seed_alert(db_session, app_id, created_at=now - timedelta(days=2))
    failed = await _seed_alert(
        db_session,
        app_id,
        created_at=now - timedelta(hours=2),
        status="Failed",
        channel="Email",
        recipient="ops@example.org",
    )
    pending = await _seed_alert(db_session, app_id, created_at=now - timedelta(hours=1))

    default = await client.get("/alerts", headers={"X-API-Key": key})
    assert [row["alert_id"] for row in default.json()] == [str(pending), str(failed)]

    explicit = await client.get(
        "/alerts",
        headers={"X-API-Key": key},
        params={
            "start": _ts(now - timedelta(days=3)),
            "end": _ts(now - timedelta(hours=2)),  # exclusivo: deja afuera `failed`
        },
    )
    assert [row["alert_id"] for row in explicit.json()] == [str(old)]

    only_failed = await client.get(
        "/alerts", headers={"X-API-Key": key}, params={"status": "failed"}
    )
    (row,) = only_failed.json()
    assert row["alert_id"] == str(failed)
    assert row["channel"] == "email"


async def test_list_alerts_links_anomaly_when_present(client, make_admin, db_session):
    """Una alerta disparada por una anomalía (M3) DEBE exponer su anomaly_id."""
    app_id, key, _ = await _make_app_with_key(client, make_admin, "alert-ml")
    now = datetime.now(timezone.utc).replace(microsecond=0)
    model_id, anomaly_id = uuid4(), uuid4()
    await db_session.execute(
        text(
            "INSERT INTO ml_model (model_id, name, target_metric_id, version, "
            "status_id) VALUES (:id, 'iforest', 1, 'v1', 1)"
        ),
        {"id": str(model_id)},
    )
    await db_session.execute(
        text(
            "INSERT INTO anomaly (anomaly_id, application_id, metric_type_id, "
            "bucket_start, bucket_seconds, model_id, expected_value, "
            "actual_value, severity_score, confidence_score, timestamp) "
            "VALUES (:id, :app, 1, :bucket, 60, :model, 1, 2, 0.9, 0.8, :ts)"
        ),
        {
            "id": str(anomaly_id),
            "app": app_id,
            "bucket": now.replace(second=0) - timedelta(minutes=5),
            "model": str(model_id),
            "ts": now - timedelta(minutes=4),
        },
    )
    await db_session.commit()
    await _seed_alert(
        db_session, app_id, created_at=now - timedelta(minutes=3), anomaly_id=anomaly_id
    )

    (row,) = (await client.get("/alerts", headers={"X-API-Key": key})).json()
    assert row["anomaly_id"] == str(anomaly_id)


async def test_list_alerts_limit_and_422_contract(client, make_admin, db_session):
    """limit=1 DEBE devolver solo la más nueva; limit, ventana o status
    inválidos DEBEN responder 422 invalid_query_range con ErrorResponse."""
    app_id, key, _ = await _make_app_with_key(client, make_admin, "alert-limit")
    now = datetime.now(timezone.utc).replace(microsecond=0)
    for hours in (3, 2, 1):
        newest = await _seed_alert(db_session, app_id, created_at=now - timedelta(hours=hours))

    one = await client.get("/alerts", headers={"X-API-Key": key}, params={"limit": 1})
    assert [row["alert_id"] for row in one.json()] == [str(newest)]

    for params in (
        {"limit": 0},
        {"limit": 501},
        {"status": "acked"},
        {"start": _ts(now), "end": _ts(now)},
        {"start": _ts(now - timedelta(days=8)), "end": _ts(now)},
    ):
        resp = await client.get("/alerts", headers={"X-API-Key": key}, params=params)
        assert resp.status_code == 422, params
        assert resp.json()["error"]["code"] == "invalid_query_range"


# -- Integration: autenticación ------------------------------------------------

async def test_alerts_401_without_key(client):
    """Sin X-API-Key DEBE responder 401 invalid_api_key con WWW-Authenticate."""
    resp = await client.get("/alerts")
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "invalid_api_key"
    assert resp.headers.get("www-authenticate") == "ApiKey"


async def test_alerts_403_app_inactive(client, make_admin):
    """Key válida de una aplicación inactiva DEBE responder 403 app_inactive."""
    app_id, key, token = await _make_app_with_key(client, make_admin, "alert-inactive")
    deactivated = await client.put(
        f"/applications/{app_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"is_active": False},
    )
    assert deactivated.status_code == 200

    resp = await client.get("/alerts", headers={"X-API-Key": key})
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "app_inactive"
