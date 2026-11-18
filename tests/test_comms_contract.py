"""TDD de contrato B.14 → B.10: la alerta del motor se despacha y se lee.

CT-B14-B10 (extensión B.10): una alerta creada por `RulesEngine` —Pending,
con `application_id`, `severity` y `message` y sin canal ni destinatario— es
despachable por el `Dispatcher` sin consultar `alert_rule`. Al enviarse queda
`Sent`, con `channel_id` y `recipient` persistidos y `sent_at` del momento del
envío; `GET /alerts` la expone con el canal y `sent_at` y NO expone
`recipient` (OAS-B10-2, CD-5).

Además se fija el reclamo de CD-1 contra Postgres real: dos transacciones
concurrentes no despachan la misma fila (`FOR UPDATE SKIP LOCKED`).

El transporte es un doble en memoria: el test nunca sale a Telegram ni a un
SMTP real.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker

from comms.dispatcher import (
    Dispatcher,
    PendingAlert,
    PermanentDeliveryError,
    RetryPolicy,
)
from comms.repository import SqlAlchemyCommsRepository
from ml.rules.engine import RulesEngine
from ml.rules.repository import SqlAlchemyRulesRepository

ROUTING = {
    "critical": "telegram",
    "high": "telegram",
    "medium": "email",
    "low": "email",
}
CHAT_ID = "424242"


@dataclass
class RecordingProvider:
    """Transporte falso: registra los envíos y opcionalmente falla."""

    name: str = "telegram"
    destination: str = CHAT_ID
    permanent_failure: bool = False
    sent: list[PendingAlert] = field(default_factory=list)

    async def send(self, alert: PendingAlert) -> None:
        if self.permanent_failure:
            raise PermanentDeliveryError("telegram rejected the message")
        self.sent.append(alert)


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _make_app_with_key(client, make_admin, name: str) -> tuple[UUID, str]:
    """Crea la aplicación y su API key por HTTP (tenant del test)."""
    _, token = await make_admin(email=f"admin-{uuid4().hex[:12]}@intellops.local")
    created = await client.post(
        "/applications", headers=_auth(token), json={"name": name}
    )
    assert created.status_code == 201, created.text
    app_id = created.json()["app_id"]
    key_resp = await client.post(
        f"/applications/{app_id}/api-key", headers=_auth(token)
    )
    assert key_resp.status_code == 201, key_resp.text
    return UUID(app_id), key_resp.json()["api_key"]


async def _metric_type_id(db_session, name: str) -> int:
    result = await db_session.execute(
        text("SELECT metric_type_id FROM metric_type WHERE name = :name"),
        {"name": name},
    )
    return result.scalar_one()


async def _api_key_alert(client, api_key: str) -> dict:
    """La única alerta de la app, tal como la devuelve `GET /alerts`."""
    resp = await client.get("/alerts", headers={"X-API-Key": api_key})
    assert resp.status_code == 200, resp.text
    (alert,) = resp.json()
    return alert


async def _create_pending_alert_with_the_engine(
    db_session, app_id: UUID
) -> datetime:
    """Crea la alerta con el motor real: regla `TTFB gt 800` + p95 de 995.

    Es la forma exacta que produce B.14 (`RulesEngine` + repositorio del
    motor), así el contrato se fija contra el productor y no contra un INSERT
    escrito a mano.
    """
    metric_id = await _metric_type_id(db_session, "TTFB")
    await db_session.execute(
        text(
            "INSERT INTO alert_rule (rule_id, application_id, metric_type_id, "
            "comparison, threshold, window_minutes, min_samples, "
            "cooldown_minutes, severity, is_active) "
            "VALUES (:rule_id, :app_id, :metric_type_id, 'gt', 800, "
            "15, 1, 15, 'high', TRUE)"
        ),
        {"rule_id": uuid4(), "app_id": app_id, "metric_type_id": metric_id},
    )
    now = datetime.now(timezone.utc)
    session_id = uuid4()
    await db_session.execute(
        text(
            "INSERT INTO user_session (session_id, app_id, start_timestamp) "
            "VALUES (:session_id, :app_id, :start)"
        ),
        {
            "session_id": session_id,
            "app_id": app_id,
            "start": now - timedelta(minutes=5),
        },
    )
    for value in (900.0, 950.0, 1000.0):
        await db_session.execute(
            text(
                "INSERT INTO rum_metric (metric_id, session_id, "
                "metric_type_id, value, unit, timestamp) "
                "VALUES (:metric_id, :session_id, :metric_type_id, :value, "
                "'ms', :timestamp)"
            ),
            {
                "metric_id": uuid4(),
                "session_id": session_id,
                "metric_type_id": metric_id,
                "value": value,
                "timestamp": now - timedelta(minutes=1),
            },
        )
    await db_session.commit()

    summary = await RulesEngine(SqlAlchemyRulesRepository(db_session)).run_cycle()

    assert summary.fired == 1
    return now


async def _alert_row(db_session) -> object:
    """Fila de `alert` con los catálogos resueltos (estado y canal)."""
    return (
        await db_session.execute(
            text(
                "SELECT a.alert_id, a.application_id, a.severity, a.message, "
                "s.name AS status, c.name AS channel, a.recipient, a.sent_at, "
                "a.threshold, a.observed_value "
                "FROM alert a "
                "JOIN alert_status s ON s.status_id = a.status_id "
                "LEFT JOIN alert_channel c ON c.channel_id = a.channel_id"
            )
        )
    ).one()


async def test_engine_alert_is_dispatched_to_sent_and_visible_in_get_alerts(
    client, db_session, make_admin
):
    """GIVEN una alerta creada por el motor de reglas WHEN el dispatcher la
    envía por Telegram THEN queda Sent con canal, destinatario y `sent_at`, y
    `GET /alerts` la expone con canal y `sent_at` sin `recipient`
    (CT-B14-B10, CD-2, CD-5)."""
    app_id, api_key = await _make_app_with_key(client, make_admin, "comms-sent")
    await _create_pending_alert_with_the_engine(db_session, app_id)
    provider = RecordingProvider()

    summary = await Dispatcher(
        SqlAlchemyCommsRepository(db_session),
        {"telegram": provider},
        ROUTING,
        RetryPolicy(),
    ).run_cycle()

    assert summary.claimed == 1
    assert summary.sent == 1
    assert summary.failed == 0
    (sent,) = provider.sent
    assert sent.severity == "high"
    assert sent.application_id == app_id

    row = await _alert_row(db_session)
    assert row.status == "Sent"
    assert row.channel == "Telegram"
    assert row.recipient == CHAT_ID
    assert row.sent_at is not None
    # La alerta conserva lo que el motor puso: mensaje, umbral y observado.
    assert row.message == (
        "TTFB p95 995,0 ms supera el umbral de 800,0 ms en los últimos 15 min."
    )
    assert row.threshold == Decimal("800")
    assert row.observed_value == Decimal("995")

    alert = await _api_key_alert(client, api_key)
    assert alert["status"] == "sent"
    assert alert["channel"] == "telegram"
    assert alert["sent_at"] is not None
    assert alert["message"] == row.message
    assert "recipient" not in alert


async def test_permanent_provider_failure_shows_as_failed_without_sent_at(
    client, db_session, make_admin
):
    """GIVEN un proveedor que rechaza el mensaje de forma permanente WHEN
    corre el ciclo THEN la alerta queda Failed, `GET /alerts` la muestra sin
    canal y con `sent_at` NULL (CD-4, CD-5)."""
    app_id, api_key = await _make_app_with_key(client, make_admin, "comms-failed")
    await _create_pending_alert_with_the_engine(db_session, app_id)
    provider = RecordingProvider(permanent_failure=True)

    summary = await Dispatcher(
        SqlAlchemyCommsRepository(db_session),
        {"telegram": provider},
        ROUTING,
        RetryPolicy(),
    ).run_cycle()

    assert summary.failed == 1
    assert summary.sent == 0

    row = await _alert_row(db_session)
    assert row.status == "Failed"
    assert row.sent_at is None
    # El canal del intento se persiste; `sent_at` no, porque nunca hubo entrega.
    assert row.channel == "Telegram"
    assert row.recipient == CHAT_ID

    alert = await _api_key_alert(client, api_key)
    assert alert["status"] == "failed"
    assert alert["channel"] == "telegram"
    assert alert["sent_at"] is None
    assert "recipient" not in alert


async def test_sent_alert_is_not_dispatched_twice(db_session):
    """GIVEN una alerta ya enviada WHEN corre otro ciclo THEN no se reclama
    (CD-1: solo Pending)."""
    app_id = uuid4()
    await db_session.execute(
        text("INSERT INTO application (app_id, name) VALUES (:app_id, :name)"),
        {"app_id": app_id, "name": "comms-idempotent"},
    )
    await db_session.commit()
    await _create_pending_alert_with_the_engine(db_session, app_id)
    provider = RecordingProvider()
    repository = SqlAlchemyCommsRepository(db_session)

    first = await Dispatcher(repository, {"telegram": provider}, ROUTING).run_cycle()
    second = await Dispatcher(repository, {"telegram": provider}, ROUTING).run_cycle()

    assert first.sent == 1
    assert second.claimed == 0
    assert len(provider.sent) == 1


async def test_claim_holds_the_row_lock_until_the_batch_commits(
    db_session, test_engine, make_admin
):
    """GIVEN una alerta Pending reclamada por un dispatcher WHEN otro
    dispatcher reclama a la vez THEN la fila no se reparte (`FOR UPDATE SKIP
    LOCKED`, CD-1, design §3)."""
    app_id = uuid4()
    await db_session.execute(
        text("INSERT INTO application (app_id, name) VALUES (:app_id, :name)"),
        {"app_id": app_id, "name": "comms-lock"},
    )
    pending_id = (
        await db_session.execute(
            text("SELECT status_id FROM alert_status WHERE name = 'Pending'")
        )
    ).scalar_one()
    alert_id = uuid4()
    await db_session.execute(
        text(
            "INSERT INTO alert (alert_id, application_id, severity, message, "
            "status_id) VALUES (:alert_id, :app_id, 'high', 'x', :status_id)"
        ),
        {"alert_id": alert_id, "app_id": app_id, "status_id": pending_id},
    )
    await db_session.commit()

    sessions = async_sessionmaker(test_engine, expire_on_commit=False)
    severities = list(ROUTING)
    async with sessions() as holder, sessions() as other:
        claimed = await SqlAlchemyCommsRepository(holder).claim_pending(
            severities, 10
        )
        blocked = await SqlAlchemyCommsRepository(other).claim_pending(
            severities, 10
        )

        assert [alert.alert_id for alert in claimed] == [alert_id]
        assert blocked == []

        await holder.rollback()

    async with sessions() as after:
        released = await SqlAlchemyCommsRepository(after).claim_pending(
            severities, 10
        )
        assert [alert.alert_id for alert in released] == [alert_id]
        await after.rollback()
