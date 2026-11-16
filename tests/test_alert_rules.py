"""Reglas de umbral de la v1 (ISS-B-14, #74) — AR-1..AR-7.

Unit: lógica pura (`effective_rules`, `breaches`, `build_message`) y
`AlertRuleService` con un repositorio stub. Integración: repositorio
SQLAlchemy contra Postgres real.
"""

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest

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
