"""Rutas de configuración de reglas de umbral — OAS-B14-1/OAS-B14-2 (ISS-B-14).

`POST /alerts/config` (solo Admin) crea la regla y responde 201, o
actualiza la equivalente por (`application_id`, `metric_type_id`,
`comparison`, `threshold`) y responde 200 (idempotencia de OAS-B14-1).
`GET /alerts/config?application_id=...` (Admin o Researcher) lista las
reglas de esa aplicación, activas e inactivas, por `created_at` ascendente
(OAS-B14-2).

La autenticación es por rol (bearer JWT), no por API key de tenant: el
tenant viaja explícito en el cuerpo (POST) y en el query (GET), como en
`/applications/{application_id}/api-key` (design §9). Los errores usan el
contrato ErrorResponse: 404 `application_not_found` /
`metric_type_not_found` y 422 `invalid_alert_rule`.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.domain.entities.lab_user import LabUser
from api.domain.repositories.alert_rule_repository import AlertRuleRecord
from api.domain.services.alert_rule_service import AlertRuleService
from api.infrastructure.db.repositories.sqlalchemy_alert_rule_repository import (
    SQLAlchemyAlertRuleRepository,
)
from api.infrastructure.db.repositories.sqlalchemy_application_repository import (
    SQLAlchemyApplicationRepository,
)
from api.infrastructure.db.session import get_session
from api.presentation.dependencies import require_role
from api.presentation.schemas.alert_rule import AlertRule, AlertRuleInput

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.post(
    "/config",
    response_model=AlertRule,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_200_OK: {
            "model": AlertRule,
            "description": "Regla equivalente actualizada (idempotente)",
        },
    },
)
async def upsert_alert_rule(
    payload: AlertRuleInput,
    response: Response,
    _current_user: Annotated[LabUser, Depends(require_role("Admin"))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AlertRuleRecord:
    """Crea la regla (201) o actualiza la equivalente (200) (OAS-B14-1)."""
    service = AlertRuleService(
        session,
        SQLAlchemyAlertRuleRepository(session),
        SQLAlchemyApplicationRepository(session),
    )
    record, created = await service.upsert_rule(payload)
    if not created:
        response.status_code = status.HTTP_200_OK
    return record


@router.get(
    "/config",
    response_model=list[AlertRule],
    status_code=status.HTTP_200_OK,
)
async def list_alert_rules(
    application_id: Annotated[
        UUID, Query(description="Aplicación cuyas reglas se listan")
    ],
    _current_user: Annotated[
        LabUser, Depends(require_role("Admin", "Researcher"))
    ],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[AlertRuleRecord]:
    """Reglas de la aplicación, activas e inactivas (OAS-B14-2)."""
    service = AlertRuleService(
        session,
        SQLAlchemyAlertRuleRepository(session),
        SQLAlchemyApplicationRepository(session),
    )
    return await service.list_rules(application_id)
