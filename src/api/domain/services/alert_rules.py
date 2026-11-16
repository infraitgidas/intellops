"""Reglas de umbral de la v1 — lógica pura (ISS-B-14, #74).

Tres reglas por aplicación (`latency`, `error_rate`, `availability`) con
defaults en código; una fila de `alert_rule` reemplaza al default completo
(DT-4). La dirección de la comparación es fija por regla (DT-3) y SIEMPRE
estricta: un valor exactamente igual al umbral no dispara (AR-5). Sin I/O.
"""

from collections.abc import Iterable
from dataclasses import dataclass

# pylint: disable=too-many-instance-attributes  # DTO plano de la regla

# Reglas que disparan cuando el valor es MENOR que el umbral; el resto, cuando
# es MAYOR.
_LOWER_IS_WORSE = frozenset({"availability"})


@dataclass(frozen=True)
class AlertRule:
    """Regla efectiva de una aplicación: default de código o fila de BD."""

    rule_id: str
    threshold: float
    severity: str
    window_seconds: int
    min_samples: int
    cooldown_seconds: int
    enabled: bool = True


# Orden estable de evaluación; ventana 5 min, mínimo 3 muestras, cooldown 30 min.
DEFAULT_RULES: dict[str, AlertRule] = {
    "latency": AlertRule("latency", 2000.0, "medium", 300, 3, 1800),
    "error_rate": AlertRule("error_rate", 0.5, "high", 300, 3, 1800),
    "availability": AlertRule("availability", 0.9, "critical", 300, 3, 1800),
}


def effective_rules(overrides: Iterable[AlertRule]) -> list[AlertRule]:
    """Reglas habilitadas de una aplicación: la fila reemplaza al default.

    Las deshabilitadas (`enabled = False`) no se devuelven: no se evalúan.
    """
    by_id = dict(DEFAULT_RULES)
    for override in overrides:
        if override.rule_id in by_id:
            by_id[override.rule_id] = override
    return [rule for rule in by_id.values() if rule.enabled]


def breaches(rule: AlertRule, value: float | None, samples: int) -> bool:
    """True si `value` cruza el umbral con comparación estricta.

    Sin valor, o con menos muestras que `rule.min_samples`, no dispara.
    """
    if value is None or samples < rule.min_samples:
        return False
    if rule.rule_id in _LOWER_IS_WORSE:
        return value < rule.threshold
    return value > rule.threshold


def _number(value: float, decimals: int) -> str:
    """Número con coma decimal y sin ceros finales (`0,5`, `2000`)."""
    text = f"{value:.{decimals}f}"
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text.replace(".", ",")


def _window_label(window_seconds: int) -> str:
    if window_seconds % 60 == 0:
        return f"{window_seconds // 60} min"
    return f"{window_seconds} s"


def build_message(rule: AlertRule, value: float) -> str:
    """Mensaje en español con el valor observado, el umbral y la ventana."""
    window = _window_label(rule.window_seconds)
    if rule.rule_id == "latency":
        return (
            f"TTFB promedio {_number(value, 0)} ms supera el umbral de "
            f"{_number(rule.threshold, 2)} ms (últimos {window})"
        )
    if rule.rule_id == "error_rate":
        return (
            f"{_number(value, 2)} excepciones JS por sesión superan el umbral de "
            f"{_number(rule.threshold, 2)} (últimos {window})"
        )
    return (
        f"Disponibilidad {_number(value * 100, 0)} % por debajo del umbral de "
        f"{_number(rule.threshold * 100, 1)} % (últimos {window})"
    )
