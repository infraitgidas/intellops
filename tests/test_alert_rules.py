"""Reglas de umbral de la v1 (ISS-B-14, #74) — AR-1..AR-7.

Unit: lógica pura (`effective_rules`, `breaches`, `build_message`) y
`AlertRuleService` con un repositorio stub. Integración: repositorio
SQLAlchemy contra Postgres real.
"""

from dataclasses import replace

import pytest

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
