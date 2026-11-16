"""Reglas de umbral de la v1 (ISS-B-14, #74) — AR-1..AR-7.

Unit: lógica pura (`effective_rules`, `breaches`, `build_message`) y
`AlertRuleService` con un repositorio stub. Integración: repositorio
SQLAlchemy contra Postgres real.
"""

from contextlib import asynccontextmanager
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from api.domain.repositories.alert_rule_repository import NewAlert, Observation
from api.domain.services import alert_rule_service
from api.domain.services.alert_rule_service import AlertRuleService
from api.domain.services.alert_rules import (
    DEFAULT_RULES,
    AlertRule,
    breaches,
    build_message,
    effective_rules,
)
from api.infrastructure.db.repositories.sqlalchemy_alert_rule_repository import (
    SQLAlchemyAlertRuleRepository,
)

# -- Lógica pura: reglas efectivas (AR-1) -----------------------------------


def _rule(rule_id: str, **overrides) -> AlertRule:
    return replace(DEFAULT_RULES[rule_id], **overrides)


def test_defaults_match_the_spec_summary():
    """AR-1.1: defaults sin fila."""
    latency = DEFAULT_RULES["latency"]
    assert (latency.threshold, latency.severity) == (2000.0, "medium")
    assert (latency.window_seconds, latency.min_samples) == (300, 3)
    assert latency.cooldown_seconds == 1800
    assert latency.enabled is True
    error_rate = DEFAULT_RULES["error_rate"]
    assert (error_rate.threshold, error_rate.severity) == (0.5, "high")
    availability = DEFAULT_RULES["availability"]
    assert (availability.threshold, availability.severity) == (0.9, "critical")
    for rule in DEFAULT_RULES.values():
        assert (rule.window_seconds, rule.min_samples, rule.cooldown_seconds) == (
            300,
            3,
            1800,
        )


def test_effective_rules_without_overrides_returns_the_three_defaults():
    rules = effective_rules([])
    assert [rule.rule_id for rule in rules] == ["latency", "error_rate", "availability"]
    assert rules == list(DEFAULT_RULES.values())


def test_effective_rules_override_replaces_the_default_completely():
    """AR-1.2 / DT-4: la fila reemplaza al default entero."""
    override = AlertRule(
        rule_id="latency",
        threshold=1000.0,
        severity="low",
        window_seconds=120,
        min_samples=1,
        cooldown_seconds=0,
    )
    rules = {rule.rule_id: rule for rule in effective_rules([override])}
    assert rules["latency"] == override
    assert rules["error_rate"] == DEFAULT_RULES["error_rate"]
    assert rules["availability"] == DEFAULT_RULES["availability"]


def test_effective_rules_skips_disabled_rules():
    """AR-1.3: una regla deshabilitada no se evalúa; las demás sí."""
    disabled = _rule("error_rate", enabled=False)
    rules = effective_rules([disabled])
    assert [rule.rule_id for rule in rules] == ["latency", "availability"]


# -- Lógica pura: comparación (AR-5) ----------------------------------------


@pytest.mark.parametrize(
    ("rule_id", "value", "expected"),
    [
        ("latency", 2450.0, True),
        ("latency", 2000.0, False),  # igualdad no dispara
        ("latency", 500.0, False),
        ("error_rate", 0.75, True),
        ("error_rate", 0.5, False),
        ("error_rate", 0.1, False),
        ("availability", 0.2, True),
        ("availability", 0.9, False),
        ("availability", 1.0, False),
    ],
)
def test_breaches_is_strict_and_direction_depends_on_the_rule(rule_id, value, expected):
    assert breaches(DEFAULT_RULES[rule_id], value, samples=5) is expected


@pytest.mark.parametrize("rule_id", ["latency", "error_rate", "availability"])
def test_breaches_without_value_never_fires(rule_id):
    """AR-5.2: sin datos no dispara."""
    assert breaches(DEFAULT_RULES[rule_id], None, samples=0) is False


def test_breaches_below_min_samples_never_fires():
    """AR-5.3: con menos muestras que el mínimo no se evalúa."""
    assert breaches(DEFAULT_RULES["latency"], 9000.0, samples=2) is False
    assert breaches(DEFAULT_RULES["latency"], 9000.0, samples=3) is True


def test_breaches_uses_the_rule_min_samples():
    rule = _rule("latency", min_samples=1)
    assert breaches(rule, 9000.0, samples=1) is True


# -- Lógica pura: mensajes en español (AR-6) --------------------------------


def test_build_message_latency():
    assert build_message(DEFAULT_RULES["latency"], 2450.0) == (
        "TTFB promedio 2450 ms supera el umbral de 2000 ms (últimos 5 min)"
    )


def test_build_message_error_rate_uses_decimal_comma():
    assert build_message(DEFAULT_RULES["error_rate"], 0.75) == (
        "0,75 excepciones JS por sesión superan el umbral de 0,5 (últimos 5 min)"
    )


def test_build_message_availability_as_percentage():
    assert build_message(DEFAULT_RULES["availability"], 0.67) == (
        "Disponibilidad 67 % por debajo del umbral de 90 % (últimos 5 min)"
    )


def test_build_message_reflects_the_rule_window():
    rule = _rule("latency", window_seconds=900)
    assert build_message(rule, 2450.0).endswith("(últimos 15 min)")
    rule = _rule("latency", window_seconds=90)
    assert build_message(rule, 2450.0).endswith("(últimos 90 s)")


# -- AlertRuleService con repositorio stub (AR-6, AR-7, AR-8) ---------------

NOW = datetime(2026, 11, 15, 12, 0, tzinfo=timezone.utc)
APP_ID = UUID("11111111-2222-3333-4444-555555555555")


class StubRepository:
    """Repositorio en memoria: observaciones por regla y alertas previas."""

    def __init__(self, observations=None, overrides=None, recent=None, fail_on=None):
        self.observations = observations or {}
        self.overrides = overrides or []
        self.recent = recent or {}  # rule_id -> created_at de la última alerta
        self.fail_on = fail_on or set()  # rule_id cuya observación lanza
        self.observe_calls: list[tuple[str, datetime, datetime]] = []
        self.created: list[NewAlert] = []
        self.transactions: list[tuple[str, bool]] = []  # (evento, con error)

    @asynccontextmanager
    async def rule_transaction(self):
        self.transactions.append(("enter", False))
        try:
            yield
        except BaseException:
            self.transactions.append(("exit", True))
            raise
        self.transactions.append(("exit", False))

    async def list_rule_overrides(self, app_id):
        return list(self.overrides)

    async def observe(self, app_id, rule_id, start, end):
        self.observe_calls.append((rule_id, start, end))
        if rule_id in self.fail_on:
            raise RuntimeError(f"boom {rule_id}")
        return self.observations.get(rule_id, Observation(None, 0))

    async def has_recent_alert(self, app_id, rule_id, since):
        created_at = self.recent.get(rule_id)
        return created_at is not None and created_at > since

    async def create_alert(self, alert):
        self.created.append(alert)


async def test_service_creates_a_new_alert_with_the_rule_data():
    """AR-6.1: severidad, umbral, valor, mensaje y created_at = now."""
    repo = StubRepository({"latency": Observation(2450.0, 5)})

    created = await AlertRuleService(repo).evaluate_application(APP_ID, NOW)

    assert repo.created == created
    assert created == [
        NewAlert(
            application_id=APP_ID,
            rule_id="latency",
            severity="medium",
            threshold=2000.0,
            observed_value=2450.0,
            message="TTFB promedio 2450 ms supera el umbral de 2000 ms (últimos 5 min)",
            created_at=NOW,
        )
    ]


async def test_service_does_not_create_without_breach_or_samples():
    repo = StubRepository(
        {
            "latency": Observation(2000.0, 5),  # igualdad
            "error_rate": Observation(9.0, 2),  # muestra insuficiente
            "availability": Observation(None, 0),  # sin datos
        }
    )

    assert await AlertRuleService(repo).evaluate_application(APP_ID, NOW) == []
    assert repo.created == []


async def test_service_skips_alert_inside_the_cooldown():
    """AR-7.1: alerta de hace 10 min con cooldown de 30."""
    repo = StubRepository(
        {"latency": Observation(2450.0, 5)},
        recent={"latency": NOW - timedelta(minutes=10)},
    )

    assert await AlertRuleService(repo).evaluate_application(APP_ID, NOW) == []


async def test_service_creates_again_after_the_cooldown():
    """AR-7.2: hace 31 min con cooldown de 30."""
    repo = StubRepository(
        {"latency": Observation(2450.0, 5)},
        recent={"latency": NOW - timedelta(minutes=31)},
    )

    assert len(await AlertRuleService(repo).evaluate_application(APP_ID, NOW)) == 1


async def test_service_cooldown_boundary_creates_the_alert():
    """DT-2: `created_at == now - cooldown` ya salió del cooldown (`>` estricto)."""
    repo = StubRepository(
        {"latency": Observation(2450.0, 5)},
        recent={"latency": NOW - timedelta(seconds=1800)},
    )

    assert len(await AlertRuleService(repo).evaluate_application(APP_ID, NOW)) == 1


async def test_service_cooldown_is_independent_per_rule():
    """AR-7.3: la alerta reciente de latencia no frena la de errores."""
    repo = StubRepository(
        {"latency": Observation(2450.0, 5), "error_rate": Observation(0.75, 4)},
        recent={"latency": NOW - timedelta(minutes=1)},
    )

    created = await AlertRuleService(repo).evaluate_application(APP_ID, NOW)

    assert [alert.rule_id for alert in created] == ["error_rate"]


async def test_service_passes_the_window_to_the_repository():
    """La ventana evaluada es `[now - window, now)`."""
    repo = StubRepository(
        overrides=[_rule("latency", window_seconds=120)],
    )

    await AlertRuleService(repo).evaluate_application(APP_ID, NOW)

    calls = {rule_id: (start, end) for rule_id, start, end in repo.observe_calls}
    assert calls["latency"] == (NOW - timedelta(seconds=120), NOW)
    assert calls["error_rate"] == (NOW - timedelta(seconds=300), NOW)
    assert calls["availability"] == (NOW - timedelta(seconds=300), NOW)


async def test_service_uses_the_override_threshold_and_skips_disabled_rules():
    """AR-1.2 / AR-1.3."""
    repo = StubRepository(
        {
            "latency": Observation(1500.0, 3),
            "error_rate": Observation(0.9, 5),
        },
        overrides=[
            _rule("latency", threshold=1000.0),
            _rule("error_rate", enabled=False),
        ],
    )

    created = await AlertRuleService(repo).evaluate_application(APP_ID, NOW)

    assert [(a.rule_id, a.threshold) for a in created] == [("latency", 1000.0)]
    assert "error_rate" not in {call[0] for call in repo.observe_calls}


async def test_service_a_failing_rule_does_not_stop_the_others(caplog, monkeypatch):
    """AR-8: el error de una regla se registra y las demás se evalúan."""
    # `alembic.fileConfig` (migraciones de la sesión) deshabilita los loggers
    # ya creados: se reactiva para que caplog lo capture en la suite completa.
    monkeypatch.setattr(alert_rule_service.logger, "disabled", False)
    repo = StubRepository(
        {"availability": Observation(0.2, 10)}, fail_on={"latency", "error_rate"}
    )

    with caplog.at_level("ERROR"):
        created = await AlertRuleService(repo).evaluate_application(uuid4(), NOW)

    assert [alert.rule_id for alert in created] == ["availability"]
    assert "latency" in caplog.text and "error_rate" in caplog.text


async def test_service_isolates_each_rule_in_its_own_transaction():
    """AR-8: cada regla corre en un `rule_transaction`; el error lo hace fallar."""
    repo = StubRepository(
        {"availability": Observation(0.2, 10)}, fail_on={"latency"}
    )

    await AlertRuleService(repo).evaluate_application(uuid4(), NOW)

    assert repo.transactions.count(("enter", False)) == 3
    assert repo.transactions.count(("exit", True)) == 1
    assert repo.transactions.count(("exit", False)) == 2


# -- Integración: SQLAlchemyAlertRuleRepository (AR-2..AR-4, AR-6, AR-7) -----

START = datetime(2026, 11, 15, 11, 55, tzinfo=timezone.utc)
END = datetime(2026, 11, 15, 12, 0, tzinfo=timezone.utc)
INSIDE = datetime(2026, 11, 15, 11, 57, tzinfo=timezone.utc)
BEFORE = datetime(2026, 11, 15, 11, 54, 59, tzinfo=timezone.utc)


async def _seed_app(db: AsyncSession, active: bool = True) -> UUID:
    app_id = uuid4()
    await db.execute(
        text(
            "INSERT INTO application (app_id, name, description, is_active) "
            "VALUES (:id, :name, 'alert rules', :active)"
        ),
        {"id": app_id, "name": f"app-{app_id}", "active": active},
    )
    await db.commit()
    return app_id


async def _seed_session(
    db: AsyncSession, app_id: UUID, started: datetime = INSIDE
) -> UUID:
    session_id = uuid4()
    await db.execute(
        text(
            "INSERT INTO user_session (session_id, app_id, start_timestamp) "
            "VALUES (:sid, :aid, :ts)"
        ),
        {"sid": session_id, "aid": app_id, "ts": started},
    )
    await db.commit()
    return session_id


async def _seed_metric(
    db: AsyncSession,
    session_id: UUID,
    type_name: str,
    value: float,
    ts: datetime = INSIDE,
    probe: bool = False,
) -> None:
    metadata = '{"probe_target": "https://example.org"}' if probe else None
    await db.execute(
        text(
            "INSERT INTO rum_metric (metric_id, session_id, metric_type_id, value, "
            "unit, timestamp, metadata) VALUES (:mid, :sid, "
            "(SELECT metric_type_id FROM metric_type WHERE name = :type), :value, "
            "'ms', :ts, CAST(:meta AS jsonb))"
        ),
        {
            "mid": uuid4(),
            "sid": session_id,
            "type": type_name,
            "value": value,
            "ts": ts,
            "meta": metadata,
        },
    )
    await db.commit()


async def _seed_exception(
    db: AsyncSession, session_id: UUID, ts: datetime = INSIDE
) -> None:
    await db.execute(
        text(
            "INSERT INTO js_exception (error_id, session_id, error_type, message, "
            "timestamp) VALUES (:eid, :sid, 'TypeError', 'boom', :ts)"
        ),
        {"eid": uuid4(), "sid": session_id, "ts": ts},
    )
    await db.commit()


async def _seed_alert(
    db: AsyncSession, app_id: UUID, rule_id: str, created_at: datetime
) -> None:
    await db.execute(
        text(
            "INSERT INTO alert (alert_id, application_id, severity, message, "
            "status_id, created_at, rule_id) VALUES (:id, :aid, 'medium', 'x', "
            "(SELECT status_id FROM alert_status WHERE name = 'Sent'), :ts, :rule)"
        ),
        {"id": uuid4(), "aid": app_id, "ts": created_at, "rule": rule_id},
    )
    await db.commit()


async def test_repo_latency_averages_rum_ttfb(db_session):
    """AR-2.1."""
    app_id = await _seed_app(db_session)
    session_id = await _seed_session(db_session, app_id)
    for value in (2400.0, 2500.0, 2450.0):
        await _seed_metric(db_session, session_id, "TTFB", value)

    repo = SQLAlchemyAlertRuleRepository(db_session)

    assert await repo.observe(app_id, "latency", START, END) == Observation(2450.0, 3)


async def test_repo_latency_excludes_probe_rows(db_session):
    """AR-2.2: ni el promedio ni la muestra cuentan filas con probe_target."""
    app_id = await _seed_app(db_session)
    session_id = await _seed_session(db_session, app_id)
    for _ in range(3):
        await _seed_metric(db_session, session_id, "TTFB", 500.0)
    probe_session = await _seed_session(db_session, app_id)
    for _ in range(5):
        await _seed_metric(db_session, probe_session, "TTFB", 9000.0, probe=True)

    repo = SQLAlchemyAlertRuleRepository(db_session)

    assert await repo.observe(app_id, "latency", START, END) == Observation(500.0, 3)


async def test_repo_latency_ignores_other_metric_types(db_session):
    app_id = await _seed_app(db_session)
    session_id = await _seed_session(db_session, app_id)
    await _seed_metric(db_session, session_id, "FCP", 9000.0)

    repo = SQLAlchemyAlertRuleRepository(db_session)

    assert await repo.observe(app_id, "latency", START, END) == Observation(None, 0)


async def test_repo_availability_averages_probe_rows(db_session):
    """AR-4.1: 10 filas AVAILABILITY, 8 caídas -> uptime 0,2 (incluye la sonda)."""
    app_id = await _seed_app(db_session)
    session_id = await _seed_session(db_session, app_id)
    for value in (1.0, 1.0) + (0.0,) * 8:
        await _seed_metric(db_session, session_id, "AVAILABILITY", value, probe=True)

    repo = SQLAlchemyAlertRuleRepository(db_session)

    observation = await repo.observe(app_id, "availability", START, END)
    assert observation.samples == 10
    assert observation.value == pytest.approx(0.2)


async def test_repo_error_rate_counts_exceptions_per_session(db_session):
    """AR-3.1: 3 excepciones / 4 sesiones = 0,75."""
    app_id = await _seed_app(db_session)
    sessions = [await _seed_session(db_session, app_id) for _ in range(4)]
    for session_id in sessions:
        await _seed_metric(db_session, session_id, "TTFB", 100.0)
    for session_id in sessions[:3]:
        await _seed_exception(db_session, session_id)

    repo = SQLAlchemyAlertRuleRepository(db_session)

    assert await repo.observe(app_id, "error_rate", START, END) == Observation(0.75, 4)


async def test_repo_error_rate_excludes_the_probe_session(db_session):
    """AR-3.2: 3 sesiones reales + 1 de la sonda + 2 excepciones -> 2/3."""
    app_id = await _seed_app(db_session)
    sessions = [await _seed_session(db_session, app_id) for _ in range(3)]
    for session_id in sessions:
        await _seed_metric(db_session, session_id, "TTFB", 100.0)
    probe_session = await _seed_session(db_session, app_id)
    await _seed_metric(db_session, probe_session, "AVAILABILITY", 1.0, probe=True)
    await _seed_metric(db_session, probe_session, "TTFB", 100.0, probe=True)
    for session_id in sessions[:2]:
        await _seed_exception(db_session, session_id)

    repo = SQLAlchemyAlertRuleRepository(db_session)

    observation = await repo.observe(app_id, "error_rate", START, END)
    assert observation.samples == 3
    assert observation.value == pytest.approx(2 / 3)


async def test_repo_error_rate_counts_a_long_session_started_before_the_window(
    db_session,
):
    """DT-7: `start_timestamp` previo a la ventana no la deja afuera."""
    app_id = await _seed_app(db_session)
    session_id = await _seed_session(
        db_session, app_id, started=START - timedelta(hours=2)
    )
    await _seed_metric(db_session, session_id, "TTFB", 100.0)
    await _seed_exception(db_session, session_id)

    repo = SQLAlchemyAlertRuleRepository(db_session)

    assert await repo.observe(app_id, "error_rate", START, END) == Observation(1.0, 1)


async def test_repo_error_rate_counts_a_session_with_only_an_exception(db_session):
    app_id = await _seed_app(db_session)
    session_id = await _seed_session(db_session, app_id)
    await _seed_exception(db_session, session_id)

    repo = SQLAlchemyAlertRuleRepository(db_session)

    assert await repo.observe(app_id, "error_rate", START, END) == Observation(1.0, 1)


@pytest.mark.parametrize("rule_id", ["latency", "error_rate", "availability"])
async def test_repo_without_data_returns_no_value(db_session, rule_id):
    """AR-5.2."""
    app_id = await _seed_app(db_session)

    repo = SQLAlchemyAlertRuleRepository(db_session)

    assert await repo.observe(app_id, rule_id, START, END) == Observation(None, 0)


async def test_repo_window_is_closed_open(db_session):
    """Borde `[start, end)`: `start` entra, `end` y lo anterior no."""
    app_id = await _seed_app(db_session)
    session_id = await _seed_session(db_session, app_id)
    await _seed_metric(db_session, session_id, "TTFB", 1000.0, ts=START)
    await _seed_metric(db_session, session_id, "TTFB", 5000.0, ts=END)
    await _seed_metric(db_session, session_id, "TTFB", 7000.0, ts=BEFORE)

    repo = SQLAlchemyAlertRuleRepository(db_session)

    assert await repo.observe(app_id, "latency", START, END) == Observation(1000.0, 1)


async def test_repo_observations_are_scoped_by_tenant(db_session):
    app_a = await _seed_app(db_session)
    app_b = await _seed_app(db_session)
    session_a = await _seed_session(db_session, app_a)
    session_b = await _seed_session(db_session, app_b)
    await _seed_metric(db_session, session_a, "TTFB", 100.0)
    await _seed_metric(db_session, session_b, "TTFB", 9000.0)
    await _seed_exception(db_session, session_b)

    repo = SQLAlchemyAlertRuleRepository(db_session)

    assert await repo.observe(app_a, "latency", START, END) == Observation(100.0, 1)
    assert await repo.observe(app_a, "error_rate", START, END) == Observation(0.0, 1)


async def test_repo_lists_only_active_applications(db_session):
    active = await _seed_app(db_session)
    await _seed_app(db_session, active=False)

    repo = SQLAlchemyAlertRuleRepository(db_session)

    assert await repo.list_active_application_ids() == [active]


async def test_repo_lists_rule_overrides_including_disabled(db_session):
    app_id = await _seed_app(db_session)
    other = await _seed_app(db_session)
    insert = text(
        "INSERT INTO alert_rule (application_id, rule_id, threshold, severity, "
        "window_seconds, min_samples, cooldown_seconds, enabled) "
        "VALUES (:aid, :rule, :threshold, 'low', 120, 1, 0, :enabled)"
    )
    await db_session.execute(
        insert, {"aid": app_id, "rule": "latency", "threshold": 1000, "enabled": True}
    )
    await db_session.execute(
        insert,
        {"aid": app_id, "rule": "error_rate", "threshold": 0.2, "enabled": False},
    )
    await db_session.execute(
        insert, {"aid": other, "rule": "latency", "threshold": 5, "enabled": True}
    )
    await db_session.commit()

    repo = SQLAlchemyAlertRuleRepository(db_session)
    rules = {rule.rule_id: rule for rule in await repo.list_rule_overrides(app_id)}

    assert set(rules) == {"latency", "error_rate"}
    assert rules["latency"] == AlertRule("latency", 1000.0, "low", 120, 1, 0, True)
    assert rules["error_rate"].enabled is False


async def test_repo_has_recent_alert_by_application_and_rule(db_session):
    """AR-7: por (aplicación, regla), cualquier estado, `created_at > since`."""
    app_a = await _seed_app(db_session)
    app_b = await _seed_app(db_session)
    since = END - timedelta(minutes=30)
    await _seed_alert(db_session, app_a, "latency", END - timedelta(minutes=10))
    await _seed_alert(db_session, app_b, "error_rate", END - timedelta(minutes=10))

    repo = SQLAlchemyAlertRuleRepository(db_session)

    assert await repo.has_recent_alert(app_a, "latency", since) is True
    assert await repo.has_recent_alert(app_a, "error_rate", since) is False
    assert await repo.has_recent_alert(app_b, "latency", since) is False


async def test_repo_has_recent_alert_boundary_is_strict(db_session):
    app_id = await _seed_app(db_session)
    since = END - timedelta(minutes=30)
    await _seed_alert(db_session, app_id, "latency", since)

    repo = SQLAlchemyAlertRuleRepository(db_session)

    assert await repo.has_recent_alert(app_id, "latency", since) is False
    assert (
        await repo.has_recent_alert(app_id, "latency", since - timedelta(seconds=1))
        is True
    )


async def test_repo_create_alert_inserts_a_pending_row(db_session):
    """AR-6.1: Pending por nombre; destino y anomalía en NULL."""
    app_id = await _seed_app(db_session)
    repo = SQLAlchemyAlertRuleRepository(db_session)

    await repo.create_alert(
        NewAlert(
            application_id=app_id,
            rule_id="latency",
            severity="medium",
            threshold=2000.0,
            observed_value=2450.0,
            message="TTFB promedio 2450 ms supera el umbral de 2000 ms (últimos 5 min)",
            created_at=END,
        )
    )
    await db_session.commit()

    row = (
        await db_session.execute(
            text(
                "SELECT a.severity, a.message, a.rule_id, a.threshold, "
                "a.observed_value, a.created_at, a.anomaly_id, a.recipient, "
                "a.channel_id, a.sent_at, s.name AS status "
                "FROM alert a JOIN alert_status s ON s.status_id = a.status_id "
                "WHERE a.application_id = :aid"
            ),
            {"aid": app_id},
        )
    ).one()
    assert row.status == "Pending"
    assert (row.severity, row.rule_id) == ("medium", "latency")
    assert (row.threshold, row.observed_value) == (2000.0, 2450.0)
    assert row.created_at == END
    assert "2450" in row.message and "2000" in row.message
    assert (row.anomaly_id, row.recipient, row.channel_id, row.sent_at) == (
        None,
        None,
        None,
        None,
    )
