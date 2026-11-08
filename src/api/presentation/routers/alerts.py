"""Lectura de alertas — GET /alerts (ISS-B-03, #68).

Aplica `Depends(require_api_key)` igual que `/metrics/*` (OAS-14, ADR-0003):
el tenant se deriva EXCLUSIVAMENTE de la key; no existe parámetro de
aplicación en el request. Solo lectura: las alertas las crea el motor de
reglas (B.14) y las despacha B.10. `/alerts/config` y `/alerts/{id}/ack`
quedan fuera de este cambio.
"""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from api.domain.entities.application import Application
from api.domain.repositories.alert_repository import ALERT_STATUSES
from api.domain.services.alert_service import AlertService
from api.domain.services.read_window import (
    DEFAULT_READ_LIMIT,
    MAX_READ_LIMIT,
    MIN_READ_LIMIT,
)
from api.infrastructure.db.repositories.sqlalchemy_alert_repository import (
    SQLAlchemyAlertRepository,
)
from api.infrastructure.db.session import get_session
from api.presentation.dependencies import require_api_key
from api.presentation.schemas.alert import AlertOut

# Los endpoints reciben un argumento por parámetro de query (FastAPI).
# pylint: disable=too-many-arguments,too-many-positional-arguments

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get(
    "",
    response_model=list[AlertOut],
    operation_id="listAlerts",
)
async def list_alerts(
    application: Annotated[Application, Depends(require_api_key)],
    session: Annotated[AsyncSession, Depends(get_session)],
    start: datetime | None = Query(
        default=None,
        description=(
            "Inicio de la ventana sobre created_at (ISO 8601 UTC). "
            "Default: end - 24 h."
        ),
    ),
    end: datetime | None = Query(
        default=None,
        description=(
            "Fin de la ventana, exclusivo (ISO 8601 UTC). Default: ahora. "
            "Máximo 7 días desde start."
        ),
    ),
    # Sin ge/le ni enum a propósito: limit y status los valida el servicio
    # para responder 422 `invalid_query_range` con el contrato ErrorResponse.
    limit: int = Query(
        default=DEFAULT_READ_LIMIT,
        description=(
            f"Máximo de alertas a devolver ({MIN_READ_LIMIT}.."
            f"{MAX_READ_LIMIT}, default {DEFAULT_READ_LIMIT}). Fuera de "
            "rango → 422 invalid_query_range (sin clamp silencioso)."
        ),
    ),
    status: str | None = Query(
        default=None,
        description=(
            f"Filtro opcional por estado ({', '.join(ALERT_STATUSES)}). "
            "Otro valor → 422 invalid_query_range."
        ),
    ),
) -> list[AlertOut]:
    """Alertas de la app autenticada creadas en la ventana, la más nueva
    primero (ISS-B-03)."""
    service = AlertService(SQLAlchemyAlertRepository(session))
    records = await service.list_alerts(
        app_id=application.app_id,
        start=start,
        end=end,
        limit=limit,
        status=status,
    )
    return [
        AlertOut(
            alert_id=record.alert_id,
            application_id=record.application_id,
            anomaly_id=record.anomaly_id,
            severity=record.severity,
            message=record.message,
            status=record.status,
            channel=record.channel,
            created_at=record.created_at,
            sent_at=record.sent_at,
        )
        for record in records
    ]
