"""TDD de contrato B.14 ↔ B.10: la alerta del motor es despachable (CT-B14-B10).

Una alerta creada por `RulesEngine` DEBE ser suficiente para el dispatcher sin
consultar `alert_rule`: `application_id`, `severity`, `message` y estado
`pending`. Y DEBE ser visible por `GET /alerts` con la API key del tenant, con
`anomaly_id`, `channel` y `sent_at` en NULL (ISS-B-14, spec §3).

La regla y las métricas se insertan con SQL directo: el test no depende de la
API de configuración.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import text

from ml.rules.engine import RulesEngine
from ml.rules.repository import SqlAlchemyRulesRepository

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


async def _seed_rule(
    db_session,
    app_id: UUID,
    metric_type_id: int,
    *,
    threshold: str = "800",
) -> UUID:
    """Seed SQL directo de la regla `TTFB gt 800`, ventana 15 (0008)."""
    rule_id = uuid4()
    await db_session.execute(
        text(
            "INSERT INTO alert_rule (rule_id, application_id, metric_type_id, "
            "comparison, threshold, window_minutes, min_samples, "
            "cooldown_minutes, severity, is_active) "
            "VALUES (:rule_id, :app_id, :metric_type_id, 'gt', :threshold, "
            "15, 1, 15, 'high', TRUE)"
        ),
        {
            "rule_id": rule_id,
            "app_id": app_id,
            "metric_type_id": metric_type_id,
            "threshold": threshold,
        },
    )
    await db_session.commit()
    return rule_id


async def _seed_metrics(
    db_session,
    app_id: UUID,
    metric_type_id: int,
    values: list[float],
    *,
    timestamp: datetime,
) -> None:
    session_id = uuid4()
    await db_session.execute(
        text(
            "INSERT INTO user_session (session_id, app_id, start_timestamp) "
            "VALUES (:session_id, :app_id, :start)"
        ),
        {
            "session_id": session_id,
            "app_id": app_id,
            "start": timestamp - timedelta(minutes=5),
        },
    )
    for value in values:
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
                "metric_type_id": metric_type_id,
                "value": value,
                "timestamp": timestamp,
            },
        )
    await db_session.commit()


async def test_engine_cycle_does_not_duplicate_inside_the_cooldown(
    client, db_session, make_admin
):
    """GIVEN una alerta de la regla creada por el primer ciclo WHEN corre un
    segundo ciclo dentro del cooldown THEN no se crea otra y la regla cuenta
    como `cooled` (AR-6 contra `alert`, design §7)."""
    app_id, _ = await _make_app_with_key(client, make_admin, "rules-cooldown")
    metric_id = await _metric_type_id(db_session, "TTFB")
    await _seed_rule(db_session, app_id, metric_id)
    now = datetime.now(timezone.utc)
    await _seed_metrics(
        db_session,
        app_id,
        metric_id,
        [900.0, 950.0, 1000.0],
        timestamp=now - timedelta(minutes=1),
    )
    repository = SqlAlchemyRulesRepository(db_session)

    first = await RulesEngine(repository).run_cycle()
    second = await RulesEngine(repository).run_cycle()

    assert first.fired == 1
    assert second.evaluated == 1
    assert second.fired == 0
    assert second.cooled == 1
    count = await db_session.scalar(text("SELECT count(*) FROM alert"))
    assert count == 1


async def test_inactive_rule_is_not_evaluated(db_session):
    """Una regla con `is_active = false` no se evalúa ni alerta (AR-1)."""
    app_id = uuid4()
    await db_session.execute(
        text("INSERT INTO application (app_id, name) VALUES (:app_id, :name)"),
        {"app_id": app_id, "name": "rules-inactive"},
    )
    metric_id = await _metric_type_id(db_session, "TTFB")
    await db_session.execute(
        text(
            "INSERT INTO alert_rule (rule_id, application_id, metric_type_id, "
            "comparison, threshold, window_minutes, min_samples, "
            "cooldown_minutes, severity, is_active) "
            "VALUES (:rule_id, :app_id, :metric_type_id, 'gt', 800, "
            "15, 1, 15, 'high', FALSE)"
        ),
        {
            "rule_id": uuid4(),
            "app_id": app_id,
            "metric_type_id": metric_id,
        },
    )
    await db_session.commit()
    await _seed_metrics(
        db_session,
        app_id,
        metric_id,
        [900.0, 950.0, 1000.0],
        timestamp=datetime.now(timezone.utc) - timedelta(minutes=1),
    )

    summary = await RulesEngine(SqlAlchemyRulesRepository(db_session)).run_cycle()

    assert summary.evaluated == 0
    assert summary.fired == 0
    count = await db_session.scalar(text("SELECT count(*) FROM alert"))
    assert count == 0


async def test_engine_alert_is_pending_and_visible_through_get_alerts(
    client, db_session, make_admin
):
    """GIVEN una regla `TTFB gt 800` y un p95 de 995 WHEN corre el ciclo THEN
    GET /alerts la expone como `pending`, con la severidad y el mensaje del
    motor, y sin canal, destinatario, `sent_at` ni `anomaly_id`
    (CT-B14-B10)."""
    app_id, api_key = await _make_app_with_key(client, make_admin, "rules-contract")
    metric_id = await _metric_type_id(db_session, "TTFB")
    rule_id = await _seed_rule(db_session, app_id, metric_id)
    now = datetime.now(timezone.utc)
    await _seed_metrics(
        db_session,
        app_id,
        metric_id,
        [900.0, 950.0, 1000.0],
        timestamp=now - timedelta(minutes=1),
    )

    summary = await RulesEngine(SqlAlchemyRulesRepository(db_session)).run_cycle()

    assert summary.evaluated == 1
    assert summary.fired == 1

    (row,) = (
        await db_session.execute(
            text(
                "SELECT a.alert_id, a.application_id, a.anomaly_id, "
                "a.severity, a.message, s.name AS status, a.recipient, "
                "a.channel_id, a.sent_at, a.rule_id, a.threshold, "
                "a.observed_value "
                "FROM alert a "
                "JOIN alert_status s ON s.status_id = a.status_id"
            )
        )
    ).all()
    assert row.application_id == app_id
    assert row.anomaly_id is None
    assert row.severity == "high"
    assert row.status == "Pending"
    assert row.recipient is None
    assert row.channel_id is None
    assert row.sent_at is None
    assert row.rule_id == rule_id
    assert row.threshold == Decimal("800")
    assert row.observed_value == Decimal("995")
    assert row.message == (
        "TTFB p95 995,0 ms supera el umbral de 800,0 ms "
        "en los últimos 15 min."
    )

    resp = await client.get("/alerts", headers={"X-API-Key": api_key})

    assert resp.status_code == 200, resp.text
    (alert,) = resp.json()
    assert set(alert) == ALERT_FIELDS
    assert alert["alert_id"] == str(row.alert_id)
    assert alert["application_id"] == str(app_id)
    assert alert["status"] == "pending"
    assert alert["severity"] == "high"
    assert alert["message"] == row.message
    assert alert["anomaly_id"] is None
    assert alert["channel"] is None
    assert alert["sent_at"] is None
