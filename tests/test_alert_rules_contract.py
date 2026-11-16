"""Contrato de las alertas de umbral con B.10 y con GET /alerts (ISS-B-14, AR-9).

B.10 (dispatcher) toma alertas con `status = Pending`; el evaluador las deja con
destino, canal, anomalía y envío en NULL, y con los datos de la regla en columnas
propias que NO se exponen por la API (el contrato de B.3 no cambia).
"""

from datetime import timedelta

from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker
from test_alert_rules import _seed_metric, _seed_session
from test_alert_evaluator import NOW
from test_alerts import ALERT_FIELDS, _make_app_with_key

from api.infrastructure.alerting.evaluator import AlertEvaluator
from api.infrastructure.db.repositories.sqlalchemy_alert_rule_repository import (
    SQLAlchemyAlertRuleRepository,
)
from api.main import app
from api.presentation.schemas.alert import AlertOut

RULE_COLUMNS = {"rule_id", "threshold", "observed_value"}


async def test_created_alert_is_a_pending_row_visible_through_the_api(
    client, make_admin, db_session, test_engine
):
    """AR-9.1: forma de la fila para B.10 y visibilidad en GET /alerts."""
    app_id, key, _ = await _make_app_with_key(client, make_admin, "rules-contract")
    session_id = await _seed_session(db_session, app_id)
    for value in (2400.0, 2500.0, 2450.0):
        await _seed_metric(db_session, session_id, "TTFB", value)
    evaluator = AlertEvaluator(
        session_factory=async_sessionmaker(test_engine, expire_on_commit=False),
        repository_factory=SQLAlchemyAlertRuleRepository,
        interval_seconds=60,
    )

    await evaluator.evaluate_once(NOW)

    row = (
        await db_session.execute(
            text(
                "SELECT a.alert_id, a.severity, a.message, a.rule_id, a.threshold, "
                "a.observed_value, a.anomaly_id, a.recipient, a.channel_id, "
                "a.sent_at, s.name AS status "
                "FROM alert a JOIN alert_status s ON s.status_id = a.status_id "
                "WHERE a.application_id = :aid"
            ),
            {"aid": app_id},
        )
    ).one()
    assert row.status == "Pending"
    assert (row.anomaly_id, row.recipient, row.channel_id, row.sent_at) == (
        None,
        None,
        None,
        None,
    )
    assert row.message.strip()
    assert row.severity in {"low", "medium", "high", "critical"}
    assert (row.rule_id, row.threshold) == ("latency", 2000.0)
    assert row.observed_value is not None

    resp = await client.get(
        "/alerts",
        headers={"X-API-Key": key},
        params={
            "status": "pending",
            "start": (NOW - timedelta(hours=1)).isoformat(),
            "end": (NOW + timedelta(hours=1)).isoformat(),
        },
    )
    assert resp.status_code == 200, resp.text
    (body,) = resp.json()
    assert body["alert_id"] == str(row.alert_id)
    assert body["status"] == "pending"
    assert set(body) == ALERT_FIELDS
    assert body["channel"] is None and body["sent_at"] is None
    assert RULE_COLUMNS.isdisjoint(body)


def test_alert_response_schema_does_not_expose_rule_columns():
    """AR-9.2: ni el esquema ni el OpenAPI generado incluyen los datos de regla."""
    assert RULE_COLUMNS.isdisjoint(AlertOut.model_fields)
    assert "recipient" not in AlertOut.model_fields

    schema = app.openapi()["components"]["schemas"]["AlertOut"]
    assert set(schema["properties"]) == ALERT_FIELDS
