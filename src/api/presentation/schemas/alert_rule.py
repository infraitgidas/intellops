"""Schemas Pydantic de configuración de reglas de umbral — OAS-B14-1/2 (ISS-B-14).

`AlertRuleInput` es el cuerpo de `POST /alerts/config` y `AlertRule` la
respuesta (201 al crear, 200 al actualizar) y el item de
`GET /alerts/config`.

Las validaciones semánticas NO se declaran como restricciones Pydantic
(`ge`/`le`, `Literal`): la especificación exige 422 `invalid_alert_rule` con
el contrato ErrorResponse para cada una, y eso lo decide el servicio de
dominio (mismo criterio que el filtro `status` de `/alerts`). Por eso
`comparison` y `severity` son `str` en la entrada y cerrados en la salida:
la base los garantiza con `ck_alert_rule_comparison` y
`ck_alert_rule_severity` (migración 0008).

`threshold` viaja como número JSON y es `NUMERIC` en la base: la conversión
del `Decimal` del repositorio ocurre acá, en la capa de presentación
(ADR-0013, Consecuencias).
"""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AlertRuleInput(BaseModel):
    """Umbral por aplicación y por métrica (OAS-B14-1).

    `is_active` es opcional con default true: el POST reactiva la regla
    equivalente salvo que se pida desactivarla (OAS-B14-1: la actualización
    incluye `is_active`).
    """

    application_id: UUID
    metric_type_id: int
    comparison: str  # gt|lt → lo valida el servicio (422 invalid_alert_rule)
    threshold: float  # finito → lo valida el servicio (422 invalid_alert_rule)
    window_minutes: int
    min_samples: int
    cooldown_minutes: int
    severity: str  # low|medium|high|critical → lo valida el servicio
    is_active: bool = True


class AlertRule(BaseModel):
    """Regla persistida: respuesta del POST e item del GET (OAS-B14-2).

    `from_attributes=True` permite responder directamente con el
    `AlertRuleRecord` del repositorio.
    """

    model_config = ConfigDict(from_attributes=True)

    rule_id: UUID
    application_id: UUID
    metric_type_id: int
    comparison: Literal["gt", "lt"]
    threshold: float
    window_minutes: int
    min_samples: int
    cooldown_minutes: int
    severity: Literal["low", "medium", "high", "critical"]
    is_active: bool
    created_at: datetime
