"""Decisión pura del motor de reglas de umbral (ISS-B-14, AR-1..AR-6).

Sin base de datos: `decide` compara la evaluación con la regla, aplica el
cooldown y arma el mensaje determinista. El ciclo (`RulesEngine.run_cycle`)
solo orquesta el repositorio inyectado, así la lógica se prueba con dobles.

Reglas fijadas por la spec:

- `gt` dispara con `observado >= umbral`; `lt` con `observado <= umbral`
  (AR-3, design §5). La igualdad dispara en ambos sentidos.
- Menos de `min_samples` muestras es `insufficient`, nunca alerta (AR-4,
  design §6); `samples = 0` cae en el mismo caso.
- Una alerta de la misma `rule_id` con `created_at > now - cooldown_minutes`
  es `cooled` (AR-6, design §7).
- El mensaje nombra métrica, observado, umbral y ventana en español
  (AR-5, design §8).
"""

# pylint: disable=too-many-instance-attributes,too-few-public-methods

from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
from decimal import ROUND_HALF_UP, Decimal
from enum import Enum
from typing import Protocol
from uuid import UUID

# AR-2: las métricas de latencia se agregan por percentil 95.
LATENCY_METRICS = frozenset({"TTFB", "FCP", "XHR_LATENCY", "RAGE_CLICK"})
PERCENTILE = 0.95


class Verdict(str, Enum):
    """Resultado de evaluar una regla en un ciclo."""

    FIRED = "fired"
    COOLED = "cooled"
    INSUFFICIENT = "insufficient"
    OK = "ok"


@dataclass(frozen=True)
class RuleSnapshot:
    """Regla activa + nombre de su métrica (design §2, §4)."""

    rule_id: UUID
    application_id: UUID
    metric_type_id: int
    metric_name: str
    comparison: str
    threshold: Decimal
    window_minutes: int
    min_samples: int
    cooldown_minutes: int
    severity: str


@dataclass(frozen=True)
class Evaluation:
    """Agregación de la ventana: valor observado y cantidad de muestras."""

    observed: Decimal | None
    samples: int


@dataclass(frozen=True)
class Decision:
    """Decisión del ciclo; `message` solo existe cuando la regla dispara."""

    verdict: Verdict
    rule: RuleSnapshot
    observed: Decimal | None
    samples: int
    message: str | None = None


@dataclass(frozen=True)
class CycleSummary:
    """Resumen del ciclo (design §10): una regla cuenta en un solo cubo."""

    evaluated: int = 0
    fired: int = 0
    cooled: int = 0
    insufficient: int = 0
    ok: int = 0


class RulesRepository(Protocol):
    """Puerto del motor: reglas, agregación, cooldown y alta de alerta."""

    async def active_rules(self) -> list[RuleSnapshot]:
        """Reglas con `is_active = true`, ordenadas por `created_at`."""

    async def evaluate(self, rule: RuleSnapshot, now: datetime) -> Evaluation:
        """Agrega la ventana `[now - window_minutes, now)` de la regla."""

    async def last_alert_at(
        self, rule_id: UUID, since: datetime
    ) -> datetime | None:
        """`created_at` más reciente de la regla posterior a `since`."""

    async def create_alert(self, decision: Decision) -> None:
        """Inserta la alerta Pending de una decisión `fired` (AR-5)."""


def _format_decimal(value: Decimal) -> str:
    """Formato español: coma decimal y un decimal cuando alcanza (design §8).

    La latencia se publica con un decimal (912,4 / 800,0). Un umbral de
    disponibilidad (0,99) o una tasa (0,75) no se redondean a un decimal:
    `0,99` no puede convertirse en `1,0` sin dejar de nombrar el valor.
    """
    one_decimal = value.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
    if one_decimal == value:
        return f"{one_decimal:.1f}".replace(".", ",")
    return format(value.normalize(), "f").replace(".", ",")


def format_message(rule: RuleSnapshot, observed: Decimal) -> str:
    """Mensaje determinista con métrica, observado, umbral y ventana (AR-5)."""
    unit = " ms" if rule.metric_name in LATENCY_METRICS else ""
    if rule.metric_name in LATENCY_METRICS:
        label = "p95"
    elif rule.metric_name == "AVAILABILITY":
        label = "promedio"
    else:
        label = "tasa"
    amount = _format_decimal(observed)
    threshold = _format_decimal(rule.threshold)
    if rule.comparison == "gt":
        comparison = f"supera el umbral de {threshold}{unit}"
    else:
        comparison = f"está por debajo del umbral de {threshold}{unit}"
    return (
        f"{rule.metric_name} {label} {amount}{unit} {comparison} "
        f"en los últimos {rule.window_minutes} min."
    )


def _fires(comparison: str, observed: Decimal, threshold: Decimal) -> bool:
    """Comparación inclusiva de AR-3: la igualdad dispara en ambos sentidos."""
    if comparison == "gt":
        return observed >= threshold
    if comparison == "lt":
        return observed <= threshold
    raise ValueError(f"unknown alert rule comparison: {comparison!r}")


def decide(
    rule: RuleSnapshot,
    evaluation: Evaluation,
    *,
    last_alert_at: datetime | None = None,
    now: datetime,
) -> Decision:
    """Decide el resultado de una regla en el ciclo, sin tocar la base.

    Orden: datos insuficientes (AR-4) → comparación (AR-3) → cooldown (AR-6).
    `last_alert_at` es la alerta más reciente de la regla; el llamador puede
    pasarla solo cuando la regla dispara, porque el cooldown solo aplica ahí.
    """
    decision = Decision(
        verdict=Verdict.INSUFFICIENT,
        rule=rule,
        observed=evaluation.observed,
        samples=evaluation.samples,
    )
    if evaluation.samples < rule.min_samples or evaluation.observed is None:
        return decision
    if not _fires(rule.comparison, evaluation.observed, rule.threshold):
        return replace(decision, verdict=Verdict.OK)
    if last_alert_at is not None:
        cooldown_start = now - timedelta(minutes=rule.cooldown_minutes)
        if last_alert_at > cooldown_start:
            return replace(decision, verdict=Verdict.COOLED)
    return replace(
        decision,
        verdict=Verdict.FIRED,
        message=format_message(rule, evaluation.observed),
    )


def _tally(summary: CycleSummary, verdict: Verdict) -> CycleSummary:
    """Suma la decisión al cubo que le corresponde (design §10)."""
    if verdict is Verdict.FIRED:
        return replace(summary, fired=summary.fired + 1)
    if verdict is Verdict.COOLED:
        return replace(summary, cooled=summary.cooled + 1)
    if verdict is Verdict.INSUFFICIENT:
        return replace(summary, insufficient=summary.insufficient + 1)
    return replace(summary, ok=summary.ok + 1)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class RulesEngine:
    """Un ciclo completo: reglas activas → agregar → decidir → alertar."""

    def __init__(
        self,
        repository: RulesRepository,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self._repository = repository
        self._now = now or _utc_now

    async def run_cycle(self) -> CycleSummary:
        """Evalúa cada regla activa y devuelve el resumen del ciclo.

        El cooldown solo se consulta cuando la regla dispararía: una regla
        sana o sin datos no paga una consulta a `alert` por ciclo.
        """
        now = self._now()
        rules = await self._repository.active_rules()
        summary = CycleSummary(evaluated=len(rules))
        for rule in rules:
            evaluation = await self._repository.evaluate(rule, now)
            decision = decide(rule, evaluation, now=now)
            if decision.verdict is Verdict.FIRED:
                since = now - timedelta(minutes=rule.cooldown_minutes)
                last_alert_at = await self._repository.last_alert_at(
                    rule.rule_id, since
                )
                decision = decide(
                    rule,
                    evaluation,
                    last_alert_at=last_alert_at,
                    now=now,
                )
            if decision.verdict is Verdict.FIRED:
                await self._repository.create_alert(decision)
            summary = _tally(summary, decision.verdict)
        return summary
