"""TDD unitario del motor de reglas de umbral (ISS-B-14, AR-1/AR-3/AR-4/AR-5/AR-6).

Sin Postgres: la decisión (comparación inclusiva, datos insuficientes,
cooldown y mensaje) es una función pura y el ciclo se ejercita con un
repositorio doble. La agregación real se prueba en
`tests/test_rules_aggregates.py` y el contrato con `GET /alerts` en
`tests/test_rules_contract.py`.

Formatos fijados acá:

- `gt` dispara con `observado >= umbral`; `lt` con `observado <= umbral`
  (AR-3, design §5). La igualdad dispara en ambos sentidos.
- `samples < min_samples` es `insufficient`, nunca alerta (AR-4, design §6).
- Una alerta de la misma regla dentro del cooldown es `cooled` (AR-6,
  design §7).
- Mensaje determinista en español con métrica, observado, umbral y ventana
  (AR-5, design §8).
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest

import ml.rules.scheduler as scheduler_module
from ml.rules.engine import (
    CycleSummary,
    Decision,
    Evaluation,
    RuleSnapshot,
    RulesEngine,
    Verdict,
    decide,
    format_message,
)
from ml.rules.scheduler import RuleScheduler

NOW = datetime(2026, 11, 18, 12, 0, tzinfo=timezone.utc)
APP_ID = UUID("8f14e45f-ceea-467a-9a3c-1c9b1dbb1f2a")


def _rule(**overrides) -> RuleSnapshot:
    """Regla `TTFB gt 800` con ventana 15, min_samples 5 y cooldown 15."""
    values = {
        "rule_id": uuid4(),
        "application_id": APP_ID,
        "metric_type_id": 1,
        "metric_name": "TTFB",
        "comparison": "gt",
        "threshold": Decimal("800"),
        "window_minutes": 15,
        "min_samples": 5,
        "cooldown_minutes": 15,
        "severity": "high",
    }
    values.update(overrides)
    return RuleSnapshot(**values)


def _availability_rule(**overrides) -> RuleSnapshot:
    """Regla `AVAILABILITY lt 0.99` (AR-3, escenario de disponibilidad)."""
    return _rule(
        metric_type_id=6,
        metric_name="AVAILABILITY",
        comparison="lt",
        threshold=Decimal("0.99"),
        **overrides,
    )


def _decide(rule, observed, samples, *, last_alert_at=None):
    return decide(
        rule,
        Evaluation(observed=observed, samples=samples),
        last_alert_at=last_alert_at,
        now=NOW,
    )


# -- AR-3: comparación inclusiva en ambos sentidos ----------------------------


def test_gt_fires_when_observed_equals_threshold():
    """GIVEN `gt 800` y observado 800 WHEN se evalúa THEN dispara (AR-3)."""
    decision = _decide(_rule(), Decimal("800"), samples=5)

    assert decision.verdict is Verdict.FIRED
    assert decision.observed == Decimal("800")


def test_gt_does_not_fire_just_below_threshold():
    """GIVEN `gt 800` y observado 799,9 WHEN se evalúa THEN no dispara."""
    decision = _decide(_rule(), Decimal("799.9"), samples=5)

    assert decision.verdict is Verdict.OK


def test_lt_fires_when_observed_equals_threshold():
    """GIVEN `lt 0.99` y uptime 0,99 WHEN se evalúa THEN dispara (AR-3)."""
    decision = _decide(_availability_rule(), Decimal("0.99"), samples=5)

    assert decision.verdict is Verdict.FIRED


def test_lt_does_not_fire_just_above_threshold():
    """GIVEN `lt 0.99` y uptime 0,991 WHEN se evalúa THEN no dispara."""
    decision = _decide(_availability_rule(), Decimal("0.991"), samples=5)

    assert decision.verdict is Verdict.OK


# -- AR-4: datos insuficientes ------------------------------------------------


def test_one_sample_below_min_samples_is_insufficient():
    """GIVEN min_samples 2 y una sola muestra WHEN corre el ciclo THEN no
    hay alerta y la regla cuenta como `insufficient` (AR-4)."""
    decision = _decide(_rule(min_samples=2), Decimal("900"), samples=1)

    assert decision.verdict is Verdict.INSUFFICIENT
    assert decision.message is None


def test_zero_samples_is_insufficient_even_without_observed_value():
    """Una ventana vacía (samples = 0) es `insufficient`, no un error."""
    decision = _decide(_rule(), observed=None, samples=0)

    assert decision.verdict is Verdict.INSUFFICIENT


# -- AR-6: cooldown contra `alert` -------------------------------------------


def test_alert_inside_cooldown_cools_the_rule():
    """GIVEN una alerta de la regla hace 1 min y cooldown 15 WHEN vuelve a
    disparar THEN no se crea otra: `cooled` (AR-6)."""
    decision = _decide(
        _rule(), Decimal("900"), samples=5, last_alert_at=NOW - timedelta(minutes=1)
    )

    assert decision.verdict is Verdict.COOLED
    assert decision.message is None


def test_alert_outside_cooldown_allows_a_new_one():
    """GIVEN una alerta hace 16 min y cooldown 15 WHEN dispara THEN se crea
    una nueva (AR-6)."""
    decision = _decide(
        _rule(), Decimal("900"), samples=5, last_alert_at=NOW - timedelta(minutes=16)
    )

    assert decision.verdict is Verdict.FIRED


def test_alert_exactly_at_cooldown_boundary_does_not_block():
    """El cooldown es `created_at > now - cooldown`: el borde no bloquea."""
    decision = _decide(
        _rule(), Decimal("900"), samples=5, last_alert_at=NOW - timedelta(minutes=15)
    )

    assert decision.verdict is Verdict.FIRED


# -- AR-5 / design §8: mensaje determinista ----------------------------------


def test_message_for_gt_names_metric_value_threshold_and_window():
    """El mensaje DEBE nombrar TTFB, 912,4, 800 y 15 (AR-5, design §8)."""
    message = format_message(_rule(), Decimal("912.4"))

    assert message == (
        "TTFB p95 912,4 ms supera el umbral de 800,0 ms "
        "en los últimos 15 min."
    )


def test_message_for_lt_keeps_slo_precision():
    """`lt` usa "por debajo" y no redondea 0,99 a 1,0 (AR-5)."""
    message = format_message(_availability_rule(), Decimal("0.75"))

    assert message == (
        "AVAILABILITY promedio 0,75 está por debajo del umbral de 0,99 "
        "en los últimos 15 min."
    )


def test_message_for_js_exception_rate_has_no_ms_unit():
    """La tasa de excepciones no lleva unidad de latencia (AR-2/AR-5)."""
    rule = _rule(
        metric_type_id=4,
        metric_name="JS_EXCEPTION_RATE",
        threshold=Decimal("0.05"),
        severity="medium",
    )

    message = format_message(rule, Decimal("0.2"))

    assert message == (
        "JS_EXCEPTION_RATE tasa 0,2 supera el umbral de 0,05 "
        "en los últimos 15 min."
    )


# -- Ciclo con repositorio doble -------------------------------------------


class FakeRepository:
    """Repositorio en memoria: reglas, evaluaciones, cooldowns y alertas."""

    def __init__(self, rules, evaluations, last_alerts=None) -> None:
        self.rules = list(rules)
        self.evaluations = evaluations
        self.last_alerts = last_alerts or {}
        self.created: list[Decision] = []
        self.last_alert_calls: list[UUID] = []

    async def active_rules(self):
        return list(self.rules)

    async def evaluate(self, rule, now):
        return self.evaluations[rule.rule_id]

    async def last_alert_at(self, rule_id, since):
        self.last_alert_calls.append(rule_id)
        return self.last_alerts.get(rule_id)

    async def create_alert(self, decision):
        self.created.append(decision)


async def test_engine_inserts_one_alert_with_the_rule_shape():
    """Una regla que dispara DEBE crear UNA alerta con rule_id, tenant,
    severidad, umbral y observado de la evaluación (AR-5)."""
    rule = _rule()
    repo = FakeRepository(
        [rule], {rule.rule_id: Evaluation(Decimal("912.4"), samples=8)}
    )

    summary = await RulesEngine(repo, now=lambda: NOW).run_cycle()

    assert summary == CycleSummary(
        evaluated=1, fired=1, cooled=0, insufficient=0, ok=0
    )
    (alert,) = repo.created
    assert alert.verdict is Verdict.FIRED
    assert alert.rule.rule_id == rule.rule_id
    assert alert.rule.application_id == APP_ID
    assert alert.rule.severity == "high"
    assert alert.rule.threshold == Decimal("800")
    assert alert.observed == Decimal("912.4")
    assert alert.message == (
        "TTFB p95 912,4 ms supera el umbral de 800,0 ms "
        "en los últimos 15 min."
    )


async def test_engine_summary_counts_each_verdict():
    """El resumen DEBE contar evaluadas, disparadas, cooled, insufficient y ok."""
    fired = _rule()
    cooled = _rule(metric_name="FCP", metric_type_id=2)
    insufficient = _rule(metric_name="XHR_LATENCY", metric_type_id=3, min_samples=5)
    healthy = _rule(metric_name="RAGE_CLICK", metric_type_id=5)
    repo = FakeRepository(
        [fired, cooled, insufficient, healthy],
        {
            fired.rule_id: Evaluation(Decimal("900"), samples=5),
            cooled.rule_id: Evaluation(Decimal("900"), samples=5),
            insufficient.rule_id: Evaluation(Decimal("900"), samples=1),
            healthy.rule_id: Evaluation(Decimal("100"), samples=5),
        },
        {cooled.rule_id: NOW - timedelta(minutes=1)},
    )

    summary = await RulesEngine(repo, now=lambda: NOW).run_cycle()

    assert summary == CycleSummary(
        evaluated=4, fired=1, cooled=1, insufficient=1, ok=1
    )
    assert [decision.rule.rule_id for decision in repo.created] == [fired.rule_id]


async def test_engine_does_not_query_cooldown_when_rule_does_not_fire():
    """Sin disparo no hace falta consultar `alert`: menos trabajo por ciclo."""
    rule = _rule()
    repo = FakeRepository(
        [rule], {rule.rule_id: Evaluation(Decimal("100"), samples=5)}
    )

    summary = await RulesEngine(repo, now=lambda: NOW).run_cycle()

    assert summary == CycleSummary(
        evaluated=1, fired=0, cooled=0, insufficient=0, ok=1
    )
    assert repo.last_alert_calls == []
    assert repo.created == []


# -- Scheduler: misma semántica que la sonda (design §10) -------------------


class _FakeClock:
    """Reloj monotónico determinista para el scheduler (sin sleeps reales)."""

    def __init__(self) -> None:
        self.now = 0.0

    def monotonic(self) -> float:
        return self.now


def _inject_clock(monkeypatch, clock: _FakeClock, sleeps: list[float]) -> None:
    """Inyecta reloj y sleep falsos en el módulo del scheduler."""

    async def fake_sleep(seconds: float) -> None:
        sleeps.append(seconds)
        clock.now += max(0.0, seconds)

    monkeypatch.setattr(
        scheduler_module,
        "time",
        SimpleNamespace(monotonic=clock.monotonic),
        raising=False,
    )
    monkeypatch.setattr(
        scheduler_module, "asyncio", SimpleNamespace(sleep=fake_sleep)
    )


async def test_scheduler_runs_exactly_max_cycles_without_final_sleep(monkeypatch):
    """`max_cycles` finito DEBE correr esa cantidad de ciclos y no dormir al
    final: el worker no arranca un ciclo de más en los tests."""
    clock = _FakeClock()
    sleeps: list[float] = []
    cycles: list[int] = []

    async def cycle() -> None:
        cycles.append(1)

    _inject_clock(monkeypatch, clock, sleeps)

    await RuleScheduler(interval_seconds=0.05, cycle=cycle).run(max_cycles=3)

    assert len(cycles) == 3
    assert len(sleeps) == 2


async def test_scheduler_compensates_cycle_duration(monkeypatch):
    """El período real es el intervalo MENOS la duración del ciclo: sin la
    compensación, con ventanas de 60 s se pierde el ritmo (design §10)."""
    clock = _FakeClock()
    sleeps: list[float] = []

    async def cycle() -> None:
        clock.now += 0.03

    _inject_clock(monkeypatch, clock, sleeps)

    await RuleScheduler(interval_seconds=0.05, cycle=cycle).run(max_cycles=3)

    assert sleeps == pytest.approx([0.02, 0.02])


async def test_scheduler_resyncs_after_an_overrunning_cycle(monkeypatch):
    """Si un ciclo se pasa del intervalo, la espera se recorta a cero y el
    reloj se resincroniza: el atraso no se arrastra a un bucle sin pausa."""
    clock = _FakeClock()
    sleeps: list[float] = []
    durations = iter([0.07, 0.01, 0.01])

    async def cycle() -> None:
        clock.now += next(durations, 0.01)

    _inject_clock(monkeypatch, clock, sleeps)

    await RuleScheduler(interval_seconds=0.05, cycle=cycle).run(max_cycles=3)

    assert sleeps == pytest.approx([0.0, 0.04])
