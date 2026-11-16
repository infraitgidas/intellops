"""AlertEvaluator, settings y lifespan del evaluador (ISS-B-14, #74).

Unit: factories falsas, sin Postgres (AR-8, DT-10). Integración: `evaluate_once`
con reloj inyectado contra Postgres (AR-1.3, AR-8.1).
"""

import asyncio
from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError
from sqlalchemy import text

from api import main as api_main
from api.config import Settings
from api.domain.repositories.alert_rule_repository import Observation
from api.infrastructure.alerting import evaluator as evaluator_module
from api.infrastructure.alerting.evaluator import AlertEvaluator
from api.infrastructure.db.repositories.sqlalchemy_alert_rule_repository import (
    SQLAlchemyAlertRuleRepository,
)
from test_alert_rules import (
    INSIDE,
    _seed_alert,
    _seed_app,
    _seed_metric,
    _seed_session,
)

NOW = datetime(2026, 11, 15, 12, 0, tzinfo=timezone.utc)


# -- Falsos ------------------------------------------------------------------


class FakeSession:
    """Sesión falsa: registra commit y rollback; sirve de context manager."""

    def __init__(self, log: list[str]) -> None:
        self.log = log

    async def __aenter__(self) -> "FakeSession":
        return self

    async def __aexit__(self, *_exc) -> None:
        return None

    async def commit(self) -> None:
        self.log.append("commit")

    async def rollback(self) -> None:
        self.log.append("rollback")


class FakeRepository:
    """Repositorio falso: una app falla al leer sus reglas, otra dispara."""

    def __init__(self, session: FakeSession, apps, failing) -> None:
        self.session = session
        self.apps = apps
        self.failing = failing
        self.created: list = []

    async def list_active_application_ids(self):
        return list(self.apps)

    async def list_rule_overrides(self, app_id):
        self.session.log.append(f"rules:{app_id}")
        if app_id in self.failing:
            raise RuntimeError("boom")
        return []

    async def observe(self, app_id, rule_id, start, end):
        if rule_id == "latency":
            return Observation(3000.0, 5)
        return Observation(None, 0)

    async def has_recent_alert(self, app_id, rule_id, since):
        return False

    async def create_alert(self, alert):
        self.session.log.append(f"alert:{alert.application_id}")


def _build(apps, failing=(), interval=0.01):
    log: list[str] = []
    evaluator = AlertEvaluator(
        session_factory=lambda: FakeSession(log),
        repository_factory=lambda session: FakeRepository(session, apps, set(failing)),
        interval_seconds=interval,
    )
    return evaluator, log


# -- evaluate_once -------------------------------------------------------------


async def test_evaluate_once_commits_once_per_application():
    """AR-8.1: sesión y commit propios por aplicación."""
    app_a, app_b = uuid4(), uuid4()
    evaluator, log = _build([app_a, app_b])

    await evaluator.evaluate_once(NOW)

    assert log.count("commit") == 2
    assert "rollback" not in log
    assert f"alert:{app_a}" in log and f"alert:{app_b}" in log


async def test_evaluate_once_rolls_back_logs_and_continues(caplog, monkeypatch):
    """AR-8.1: la app que falla hace rollback + log; la siguiente se evalúa."""
    monkeypatch.setattr(evaluator_module.logger, "disabled", False)
    bad, good = uuid4(), uuid4()
    evaluator, log = _build([bad, good], failing=[bad])

    with caplog.at_level("ERROR"):
        await evaluator.evaluate_once(NOW)

    assert log.count("rollback") == 1
    assert log.count("commit") == 1
    assert f"alert:{good}" in log and f"alert:{bad}" not in log
    assert str(bad) in caplog.text


async def test_evaluate_once_with_no_applications_does_nothing():
    evaluator, log = _build([])

    await evaluator.evaluate_once(NOW)

    assert log == []


# -- loop ------------------------------------------------------------------------


async def test_loop_sleeps_before_the_first_evaluation():
    """DT-10: no evalúa antes de `interval`."""
    evaluator, log = _build([uuid4()], interval=3600)

    evaluator.start()
    await asyncio.sleep(0.05)
    await evaluator.stop()

    assert log == []


async def test_loop_evaluates_periodically_and_stop_cancels_it():
    evaluator, log = _build([uuid4()], interval=0.01)

    evaluator.start()
    await asyncio.sleep(0.1)
    await evaluator.stop()
    seen = len(log)

    assert seen > 0
    await asyncio.sleep(0.05)
    assert len(log) == seen  # detenido: sin más ciclos


async def test_stop_without_start_is_safe():
    evaluator, _ = _build([])

    await evaluator.stop()


async def test_a_failing_cycle_does_not_kill_the_loop(caplog, monkeypatch):
    """AR-8.2: el loop sobrevive a un ciclo que revienta entero."""
    monkeypatch.setattr(evaluator_module.logger, "disabled", False)
    evaluator, _ = _build([])
    calls: list[int] = []

    async def flaky(_now):
        calls.append(1)
        if len(calls) == 1:
            raise RuntimeError("cycle boom")

    monkeypatch.setattr(evaluator, "evaluate_once", flaky)

    with caplog.at_level("ERROR"):
        evaluator.start()
        await asyncio.sleep(0.1)
        await evaluator.stop()

    assert len(calls) >= 2
    assert "cycle boom" in caplog.text


# -- Settings y lifespan ---------------------------------------------------------


def test_settings_defaults_for_the_alert_evaluator(monkeypatch):
    monkeypatch.delenv("ALERT_RULES_ENABLED", raising=False)
    monkeypatch.delenv("ALERT_RULES_INTERVAL_SECONDS", raising=False)
    settings = Settings(_env_file=None)

    assert settings.alert_rules_enabled is True
    assert settings.alert_rules_interval_seconds == 60.0


@pytest.mark.parametrize("interval", [0, -1])
def test_settings_reject_a_non_positive_interval(interval):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, alert_rules_interval_seconds=interval)


class _FakeQueue:
    async def start(self):
        return None

    async def close(self):
        return None

    async def join(self, timeout):
        return None


def _patch_lifespan(monkeypatch, enabled: bool):
    settings = Settings(
        _env_file=None, alert_rules_enabled=enabled, alert_rules_interval_seconds=3600
    )
    monkeypatch.setattr(api_main, "get_settings", lambda: settings)
    monkeypatch.setattr(api_main, "AsyncioIngestQueue", lambda **_kw: _FakeQueue())

    async def _dispose():
        return None

    monkeypatch.setattr(api_main, "dispose_engine", _dispose)


async def test_lifespan_starts_and_stops_the_evaluator(monkeypatch):
    """DT-10: habilitado crea `app.state.alert_evaluator` y lo detiene al salir."""
    _patch_lifespan(monkeypatch, enabled=True)

    async with api_main.lifespan(api_main.app):
        evaluator = api_main.app.state.alert_evaluator
        task = evaluator._task  # pylint: disable=protected-access
        assert task is not None and not task.done()

    assert task.done()
    assert task.cancelled()


async def test_lifespan_does_not_create_the_evaluator_when_disabled(monkeypatch):
    _patch_lifespan(monkeypatch, enabled=False)
    if hasattr(api_main.app.state, "alert_evaluator"):
        del api_main.app.state.alert_evaluator

    async with api_main.lifespan(api_main.app):
        assert not hasattr(api_main.app.state, "alert_evaluator")


def test_conftest_disables_the_evaluator_for_the_suite():
    import os

    assert os.environ["ALERT_RULES_ENABLED"].lower() == "false"


# -- Integración: evaluate_once con Postgres -----------------------------------


@pytest.fixture
def real_evaluator(test_engine):
    from sqlalchemy.ext.asyncio import async_sessionmaker

    factory = async_sessionmaker(test_engine, expire_on_commit=False)
    return AlertEvaluator(
        session_factory=factory,
        repository_factory=SQLAlchemyAlertRuleRepository,
        interval_seconds=60,
    )


async def _count_alerts(db, app_id: UUID, rule_id: str | None = None) -> int:
    query = "SELECT count(*) FROM alert WHERE application_id = :aid"
    params: dict = {"aid": app_id}
    if rule_id:
        query += " AND rule_id = :rule"
        params["rule"] = rule_id
    return (await db.execute(text(query), params)).scalar_one()


async def _seed_slow_app(db) -> UUID:
    app_id = await _seed_app(db)
    session_id = await _seed_session(db, app_id)
    for value in (2400.0, 2500.0, 2450.0):
        await _seed_metric(db, session_id, "TTFB", value)
    return app_id


async def test_evaluate_once_creates_the_alert(db_session, real_evaluator):
    """AR-1.3."""
    app_id = await _seed_slow_app(db_session)

    await real_evaluator.evaluate_once(NOW)

    assert await _count_alerts(db_session, app_id, "latency") == 1


async def test_evaluate_once_respects_the_cooldown(db_session, real_evaluator):
    app_id = await _seed_slow_app(db_session)

    await real_evaluator.evaluate_once(NOW)
    await real_evaluator.evaluate_once(NOW)

    assert await _count_alerts(db_session, app_id, "latency") == 1


async def test_evaluate_once_skips_when_a_recent_alert_exists(
    db_session, real_evaluator
):
    app_id = await _seed_slow_app(db_session)
    await _seed_alert(db_session, app_id, "latency", INSIDE)

    await real_evaluator.evaluate_once(NOW)

    assert await _count_alerts(db_session, app_id, "latency") == 1


async def test_evaluate_once_skips_a_disabled_rule(db_session, real_evaluator):
    app_id = await _seed_slow_app(db_session)
    await db_session.execute(
        text(
            "INSERT INTO alert_rule (application_id, rule_id, threshold, severity, "
            "window_seconds, min_samples, cooldown_seconds, enabled) "
            "VALUES (:aid, 'latency', 2000, 'medium', 300, 3, 900, FALSE)"
        ),
        {"aid": app_id},
    )
    await db_session.commit()

    await real_evaluator.evaluate_once(NOW)

    assert await _count_alerts(db_session, app_id) == 0


async def test_evaluate_once_failure_in_one_app_does_not_affect_others(
    db_session, test_engine, monkeypatch
):
    """AR-8.1: un error SQL en una app (transacción abortada) no frena a las demás."""
    monkeypatch.setattr(evaluator_module.logger, "disabled", False)
    from sqlalchemy.ext.asyncio import async_sessionmaker

    bad = await _seed_slow_app(db_session)
    good = await _seed_slow_app(db_session)

    class FlakyRepository(SQLAlchemyAlertRuleRepository):
        async def observe(self, app_id, rule_id, start, end):
            if app_id == bad:
                # Error SQL real: deja la transacción abortada.
                await self._session.execute(text("SELECT * FROM missing_table"))
            return await super().observe(app_id, rule_id, start, end)

    evaluator = AlertEvaluator(
        session_factory=async_sessionmaker(test_engine, expire_on_commit=False),
        repository_factory=FlakyRepository,
        interval_seconds=60,
    )

    await evaluator.evaluate_once(NOW)

    assert await _count_alerts(db_session, bad) == 0
    assert await _count_alerts(db_session, good, "latency") == 1
