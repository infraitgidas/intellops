"""Caso de uso de reglas de umbral — OAS-B14-1/OAS-B14-2 (ISS-B-14, design §9).

Orden de la validación, toda ANTES de escribir:

1. semántica del payload (umbral finito, ventana 1..10080, `min_samples`
   >= 1, `cooldown_minutes` >= 1, `comparison` en gt|lt y `severity` en su
   dominio) → 422 `invalid_alert_rule`;
2. existencia de la aplicación → 404 `application_not_found`;
3. existencia del tipo de métrica en el catálogo → 404 `metric_type_not_found`.

La semántica va primero porque es pura: un payload mal formado se rechaza
sin consultar persistencia. Las tres violaciones comparten la garantía que
pide OAS-B14-1: `alert_rule` no gana ni modifica filas.

`upsert_rule` es idempotente por la clave (`application_id`,
`metric_type_id`, `comparison`, `threshold`): el repositorio actualiza la
regla existente y el router responde 200 en vez de 201 (ADR-0013 §2).

Los 422 semánticos usan `InvalidAlertRuleError`: fija el 422 y el código
`invalid_alert_rule` en el contrato ErrorResponse (OAS-B14-1), en vez de
reutilizar el 422 del read path de métricas.
"""

import math
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from api.domain.exceptions import InvalidAlertRuleError, NotFoundError
from api.domain.repositories.alert_rule_repository import (
    ALERT_RULE_COMPARISONS,
    ALERT_RULE_MAX_WINDOW_MINUTES,
    ALERT_RULE_MIN_WINDOW_MINUTES,
    ALERT_RULE_SEVERITIES,
    AlertRuleRecord,
    AlertRuleRepository,
)
from api.domain.repositories.application_repository import ApplicationRepository
from api.presentation.schemas.alert_rule import AlertRuleInput

# pylint: disable=too-few-public-methods  # caso de uso con dos métodos públicos


def _invalid(message: str) -> InvalidAlertRuleError:
    """422 `invalid_alert_rule` (contrato ErrorResponse, OAS-B14-1)."""
    return InvalidAlertRuleError(message)


def _validate_semantics(data: AlertRuleInput) -> None:
    """Valida los dominios de la regla sin tocar persistencia (OAS-B14-1)."""
    if not math.isfinite(data.threshold):
        raise _invalid(f"threshold must be finite, got {data.threshold}")
    if not (
        ALERT_RULE_MIN_WINDOW_MINUTES
        <= data.window_minutes
        <= ALERT_RULE_MAX_WINDOW_MINUTES
    ):
        raise _invalid(
            "window_minutes must be between "
            f"{ALERT_RULE_MIN_WINDOW_MINUTES} and "
            f"{ALERT_RULE_MAX_WINDOW_MINUTES}, got {data.window_minutes}"
        )
    if data.min_samples < 1:
        raise _invalid(f"min_samples must be >= 1, got {data.min_samples}")
    if data.cooldown_minutes < 1:
        raise _invalid(
            f"cooldown_minutes must be >= 1, got {data.cooldown_minutes}"
        )
    if data.comparison not in ALERT_RULE_COMPARISONS:
        raise _invalid(
            "comparison must be one of "
            f"{', '.join(ALERT_RULE_COMPARISONS)}, got {data.comparison!r}"
        )
    if data.severity not in ALERT_RULE_SEVERITIES:
        raise _invalid(
            "severity must be one of "
            f"{', '.join(ALERT_RULE_SEVERITIES)}, got {data.severity!r}"
        )


class AlertRuleService:
    """Valida y persiste reglas idempotentes por (app, métrica, comparación,
    umbral); lista las reglas de una aplicación (sin estado)."""

    def __init__(
        self,
        session: AsyncSession,
        rule_repository: AlertRuleRepository,
        application_repository: ApplicationRepository,
    ) -> None:
        self._session = session
        self._rules = rule_repository
        self._applications = application_repository

    async def upsert_rule(
        self, data: AlertRuleInput
    ) -> tuple[AlertRuleRecord, bool]:
        """Crea la regla o actualiza la equivalente; devuelve (regla, alta).

        422 `invalid_alert_rule` si el payload viola un dominio (sin
        escribir); 404 `application_not_found` / `metric_type_not_found` si
        la aplicación o la métrica no existen (sin escribir).
        """
        _validate_semantics(data)
        await self._ensure_application(data.application_id)
        if not await self._rules.metric_type_exists(data.metric_type_id):
            raise NotFoundError(
                f"metric type {data.metric_type_id} not found",
                code="metric_type_not_found",
            )
        record = AlertRuleRecord(
            rule_id=uuid4(),
            application_id=data.application_id,
            metric_type_id=data.metric_type_id,
            comparison=data.comparison,
            # str() evita el artefacto binario del float en el umbral.
            threshold=Decimal(str(data.threshold)),
            window_minutes=data.window_minutes,
            min_samples=data.min_samples,
            cooldown_minutes=data.cooldown_minutes,
            severity=data.severity,
            is_active=data.is_active,
        )
        stored, created = await self._rules.upsert_rule(record)
        await self._session.commit()
        return stored, created

    async def list_rules(self, app_id: UUID) -> list[AlertRuleRecord]:
        """Reglas de `app_id`, activas e inactivas, por `created_at`
        ascendente (OAS-B14-2); 404 si la aplicación no existe."""
        await self._ensure_application(app_id)
        return await self._rules.list_rules(app_id)

    async def _ensure_application(self, app_id: UUID) -> None:
        """404 `application_not_found` si la aplicación no existe."""
        application = await self._applications.get_by_id(app_id)
        if application is None:
            raise NotFoundError(
                f"application {app_id} not found",
                code="application_not_found",
            )
