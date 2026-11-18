"""TDD: configuración de reglas de umbral — OAS-B14-1/OAS-B14-2 (ISS-B-14).

Capa unit (sin Postgres): `AlertRuleService` sobre repositorios en memoria y
`FakeSession` del conftest. Fija:

- la matriz de validación semántica por campo → 422 `invalid_alert_rule` sin
  escribir ni commitear (umbral finito, ventana 1..10080, `min_samples` >= 1,
  `cooldown_minutes` >= 1, `comparison` en gt|lt y `severity` en su dominio);
- la existencia de la aplicación y del tipo de métrica → 404
  `application_not_found` / `metric_type_not_found`, antes de escribir;
- la idempotencia de OAS-B14-1: la misma clave
  (`application_id`, `metric_type_id`, `comparison`, `threshold`) actualiza la
  regla existente y devuelve created=False, sin duplicar filas;
- el listado por aplicación tal cual lo devuelve el repositorio (activas e
  inactivas), sin commit.
"""

from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from api.domain.entities.application import Application
from api.domain.exceptions import InvalidAlertRuleError, NotFoundError
from api.domain.repositories.alert_rule_repository import (
    AlertRuleRecord,
    AlertRuleRepository,
)
from api.domain.services.alert_rule_service import AlertRuleService
from api.presentation.schemas.alert_rule import AlertRule, AlertRuleInput

TTFB_ID = 1


# -- Dobles --------------------------------------------------------------------

def _app(**overrides) -> Application:
    fields = {
        "app_id": uuid4(),
        "name": "piloto",
        "description": None,
        "is_active": True,
        "api_token_hash": None,
        "created_at": datetime(2026, 11, 18, tzinfo=timezone.utc),
    }
    fields.update(overrides)
    return Application(**fields)


class _InMemoryApplications:
    """ApplicationRepository mínimo: solo el lookup por id del servicio."""

    def __init__(self, *applications: Application) -> None:
        self.items = {app.app_id: app for app in applications}

    async def get_by_id(self, app_id):
        return self.items.get(app_id)


class _InMemoryAlertRules:
    """AlertRuleRepository en memoria: registra escrituras y listados."""

    def __init__(self, *rules: AlertRuleRecord, metric_types=(TTFB_ID,)) -> None:
        self.metric_types = set(metric_types)
        self.rules: dict[tuple, AlertRuleRecord] = {_key(rule): rule for rule in rules}
        self.writes = 0
        self.listed: list = []

    async def list_rules(self, app_id):
        self.listed.append(app_id)
        return [rule for rule in self.rules.values() if rule.application_id == app_id]

    async def upsert_rule(self, rule):
        self.writes += 1
        key = _key(rule)
        existing = self.rules.get(key)
        if existing is None:
            self.rules[key] = rule
            return rule, True
        updated = replace(
            existing,
            window_minutes=rule.window_minutes,
            min_samples=rule.min_samples,
            cooldown_minutes=rule.cooldown_minutes,
            severity=rule.severity,
            is_active=rule.is_active,
        )
        self.rules[key] = updated
        return updated, False

    async def metric_type_exists(self, metric_type_id):
        return metric_type_id in self.metric_types


def _key(rule: AlertRuleRecord) -> tuple:
    return (
        rule.application_id,
        rule.metric_type_id,
        rule.comparison,
        rule.threshold,
    )


def _record(app_id, **overrides) -> AlertRuleRecord:
    fields = {
        "rule_id": uuid4(),
        "application_id": app_id,
        "metric_type_id": TTFB_ID,
        "comparison": "gt",
        "threshold": Decimal("800.0"),
        "window_minutes": 15,
        "min_samples": 5,
        "cooldown_minutes": 15,
        "severity": "high",
        "is_active": True,
        "created_at": datetime(2026, 11, 18, 12, 0, tzinfo=timezone.utc),
    }
    fields.update(overrides)
    return AlertRuleRecord(**fields)


def _payload(app_id, **overrides) -> AlertRuleInput:
    fields = {
        "application_id": app_id,
        "metric_type_id": TTFB_ID,
        "comparison": "gt",
        "threshold": 800.0,
        "window_minutes": 15,
        "min_samples": 5,
        "cooldown_minutes": 15,
        "severity": "high",
    }
    fields.update(overrides)
    return AlertRuleInput(**fields)


def _service(fake_session, rules, *applications):
    return AlertRuleService(
        fake_session, rules, _InMemoryApplications(*applications)
    )


# -- Puerto ------------------------------------------------------------------

def test_alert_rule_repository_protocol_shape():
    """El puerto DEBE exponer list_rules(app_id) y el upsert idempotente, y
    ser implementable por el repositorio SQLAlchemy."""
    from api.infrastructure.db.repositories.sqlalchemy_alert_rule_repository import (
        SQLAlchemyAlertRuleRepository,
    )

    assert AlertRuleRepository is not None
    for name in ("list_rules", "upsert_rule", "metric_type_exists"):
        assert hasattr(AlertRuleRepository, name), name
        assert hasattr(SQLAlchemyAlertRuleRepository, name), name


def test_alert_rule_record_is_a_plain_frozen_dto():
    """`AlertRuleRecord` DEBE ser un DTO plano con el umbral en Decimal (la
    frontera del SLO no se evalúa en punto flotante, ADR-0013 §5)."""
    record = _record(uuid4())
    assert record.threshold == Decimal("800.0")
    with pytest.raises(AttributeError):
        record.severity = "low"  # type: ignore[misc]


# -- Validación semántica por campo → 422 invalid_alert_rule ------------------

@pytest.mark.parametrize(
    ("field", "value", "expected_in_message"),
    [
        ("threshold", float("nan"), "nan"),
        ("threshold", float("inf"), "inf"),
        ("threshold", float("-inf"), "-inf"),
        ("window_minutes", 0, "0"),
        ("window_minutes", 10081, "10081"),
        ("window_minutes", -1, "-1"),
        ("min_samples", 0, "0"),
        ("min_samples", -5, "-5"),
        ("cooldown_minutes", 0, "0"),
        ("cooldown_minutes", -1, "-1"),
        ("comparison", "ge", "ge"),
        ("comparison", "GT", "GT"),
        ("comparison", "", ""),
        ("severity", "urgent", "urgent"),
        ("severity", "HIGH", "HIGH"),
        ("severity", "", ""),
    ],
)
async def test_invalid_field_is_422_without_writing(
    fake_session, field, value, expected_in_message
):
    """Cada campo inválido DEBE dar 422 `invalid_alert_rule` con un mensaje
    que lo nombre y muestre el valor rechazado, sin escribir ni commitear."""
    app = _app()
    rules = _InMemoryAlertRules()
    service = _service(fake_session, rules, app)

    with pytest.raises(InvalidAlertRuleError) as excinfo:
        await service.upsert_rule(_payload(app.app_id, **{field: value}))

    assert excinfo.value.http_code == 422
    assert excinfo.value.code == "invalid_alert_rule"
    assert field in excinfo.value.message
    assert expected_in_message in excinfo.value.message
    assert rules.writes == 0
    assert rules.rules == {}
    assert fake_session.calls == []


@pytest.mark.parametrize(
    "overrides",
    [
        {"window_minutes": 1},
        {"window_minutes": 10080},
        {"min_samples": 1},
        {"cooldown_minutes": 1},
        {"comparison": "lt", "threshold": 0.99, "severity": "critical"},
        {"severity": "low"},
        {"severity": "medium"},
    ],
)
async def test_boundary_values_are_accepted(fake_session, overrides):
    """Los límites del dominio (1, 10080, >=1) y los valores válidos de
    `comparison`/`severity` DEBEN aceptarse y persistirse."""
    app = _app()
    rules = _InMemoryAlertRules()
    service = _service(fake_session, rules, app)

    record, created = await service.upsert_rule(_payload(app.app_id, **overrides))

    assert created is True
    assert rules.writes == 1
    assert record.window_minutes == overrides.get("window_minutes", 15)
    assert fake_session.calls == ["commit"]


async def test_semantic_validation_runs_before_any_lookup(fake_session):
    """Una violación semántica DEBE rechazarse antes de mirar si la
    aplicación o la métrica existen (no se consulta persistencia)."""
    app = _app()
    rules = _InMemoryAlertRules(metric_types=())
    lookups: list = []

    class _RecordingApplications(_InMemoryApplications):
        async def get_by_id(self, app_id):
            lookups.append(app_id)
            return await super().get_by_id(app_id)

    service = AlertRuleService(fake_session, rules, _RecordingApplications(app))

    with pytest.raises(InvalidAlertRuleError):
        await service.upsert_rule(_payload(uuid4(), severity="urgent"))

    assert lookups == []
    assert rules.writes == 0


# -- Existencia de aplicación y de tipo de métrica → 404 ---------------------

async def test_unknown_application_is_404_without_writing(fake_session):
    """Una aplicación inexistente DEBE responder 404 `application_not_found`
    antes de escribir."""
    app = _app()
    rules = _InMemoryAlertRules()
    service = _service(fake_session, rules, app)

    with pytest.raises(NotFoundError) as excinfo:
        await service.upsert_rule(_payload(uuid4()))

    assert excinfo.value.http_code == 404
    assert excinfo.value.code == "application_not_found"
    assert rules.writes == 0
    assert fake_session.calls == []


async def test_unknown_metric_type_is_404_without_writing(fake_session):
    """`metric_type_id` fuera del catálogo DEBE responder 404
    `metric_type_not_found` antes de escribir (OAS-B14-1)."""
    app = _app()
    rules = _InMemoryAlertRules(metric_types=(TTFB_ID,))
    service = _service(fake_session, rules, app)

    with pytest.raises(NotFoundError) as excinfo:
        await service.upsert_rule(_payload(app.app_id, metric_type_id=9999))

    assert excinfo.value.http_code == 404
    assert excinfo.value.code == "metric_type_not_found"
    assert "9999" in excinfo.value.message
    assert rules.writes == 0
    assert fake_session.calls == []


# -- Idempotencia (OAS-B14-1) -------------------------------------------------

async def test_first_upsert_creates_and_commits(fake_session):
    """El primer POST DEBE crear la regla con un rule_id nuevo y commitear."""
    app = _app()
    rules = _InMemoryAlertRules()
    service = _service(fake_session, rules, app)

    record, created = await service.upsert_rule(_payload(app.app_id))

    assert created is True
    assert record.rule_id is not None
    assert record.application_id == app.app_id
    assert record.threshold == Decimal("800.0")
    assert fake_session.calls == ["commit"]


async def test_same_key_updates_instead_of_duplicating(fake_session):
    """Repetir el POST con la misma (app, métrica, comparación, umbral) DEBE
    actualizar la regla existente, devolver created=False y dejar UNA fila."""
    app = _app()
    rules = _InMemoryAlertRules()
    service = _service(fake_session, rules, app)

    first, created_first = await service.upsert_rule(_payload(app.app_id))
    second, created_second = await service.upsert_rule(
        _payload(app.app_id, cooldown_minutes=45, severity="critical", is_active=False)
    )

    assert (created_first, created_second) == (True, False)
    assert len(rules.rules) == 1
    assert second.rule_id == first.rule_id
    assert second.cooldown_minutes == 45
    assert second.severity == "critical"
    assert second.is_active is False
    assert fake_session.calls == ["commit", "commit"]


async def test_different_threshold_is_a_different_rule(fake_session):
    """Un umbral distinto DEBE crear otra regla: la clave del upsert incluye
    `threshold` (OAS-B14-1)."""
    app = _app()
    rules = _InMemoryAlertRules()
    service = _service(fake_session, rules, app)

    await service.upsert_rule(_payload(app.app_id, threshold=800.0))
    _, created = await service.upsert_rule(_payload(app.app_id, threshold=900.0))

    assert created is True
    assert len(rules.rules) == 2


async def test_threshold_comparison_uses_exact_decimal(fake_session):
    """800.0 y 800 son la MISMA clave (NUMERIC, no punto flotante): el upsert
    DEBE actualizar en vez de duplicar."""
    app = _app()
    rules = _InMemoryAlertRules()
    service = _service(fake_session, rules, app)

    await service.upsert_rule(_payload(app.app_id, threshold=800.0))
    _, created = await service.upsert_rule(_payload(app.app_id, threshold=800))

    assert created is False
    assert len(rules.rules) == 1


# -- Listado (OAS-B14-2) ------------------------------------------------------

async def test_list_rules_returns_app_rules_without_commit(fake_session):
    """El listado DEBE delegar en el repositorio con el tenant pedido y
    devolver activas e inactivas, sin commitear."""
    app = _app()
    other = _app()
    active = _record(app.app_id)
    inactive = _record(
        app.app_id,
        rule_id=uuid4(),
        comparison="lt",
        threshold=Decimal("0.99"),
        is_active=False,
    )
    rules = _InMemoryAlertRules(active, inactive, _record(other.app_id))
    service = _service(fake_session, rules, app, other)

    listed = await service.list_rules(app.app_id)

    assert [rule.rule_id for rule in listed] == [active.rule_id, inactive.rule_id]
    assert rules.listed == [app.app_id]
    assert fake_session.calls == []


async def test_list_unknown_application_is_404_without_listing(fake_session):
    """Pedir las reglas de una aplicación inexistente DEBE dar 404
    `application_not_found` sin consultar las reglas."""
    rules = _InMemoryAlertRules()
    service = _service(fake_session, rules, _app())

    with pytest.raises(NotFoundError) as excinfo:
        await service.list_rules(uuid4())

    assert excinfo.value.code == "application_not_found"
    assert rules.listed == []


# -- Schemas de presentación -------------------------------------------------

def test_alert_rule_output_schema_exposes_the_row_with_numeric_threshold():
    """`AlertRule` DEBE exponer la fila completa con `threshold` numérico
    (Decimal → número JSON, ADR-0013) y comparación/severidad cerradas."""
    record = _record(uuid4(), threshold=Decimal("912.4"))
    out = AlertRule.model_validate(record)

    payload = out.model_dump(mode="json")
    assert set(payload) == {
        "rule_id",
        "application_id",
        "metric_type_id",
        "comparison",
        "threshold",
        "window_minutes",
        "min_samples",
        "cooldown_minutes",
        "severity",
        "is_active",
        "created_at",
    }
    assert payload["threshold"] == 912.4
    assert isinstance(payload["threshold"], float)
    with pytest.raises(ValidationError):
        AlertRule.model_validate(replace(record, severity="urgent"))


def test_alert_rule_input_allows_service_level_validation():
    """`AlertRuleInput` NO DEBE cerrar el dominio en Pydantic: una severidad
    fuera del dominio tiene que llegar al servicio para responder 422
    `invalid_alert_rule` con el contrato ErrorResponse (OAS-B14-1)."""
    payload = _payload(uuid4(), severity="urgent", comparison="ge")
    assert payload.severity == "urgent"
    assert payload.comparison == "ge"
    assert payload.is_active is True

    with pytest.raises(ValidationError):
        AlertRuleInput(application_id=uuid4())  # faltan campos requeridos
