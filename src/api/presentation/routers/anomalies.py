"""Lectura de anomalías — GET /anomalies y GET /anomalies/{anomaly_id}
(ISS-B-03, #68).

Ambos aplican `Depends(require_api_key)` igual que `/metrics/*` (OAS-14,
ADR-0003): el tenant se deriva EXCLUSIVAMENTE de la key; no existe parámetro
de aplicación en el request. Solo lectura: las anomalías las escribe el
detector (M3, D1), así que en la v1 el listado suele estar vacío.

`GET /anomalies/{anomaly_id}` filtra por `anomaly_id` AND `application_id`:
una anomalía de otra aplicación responde 404 `anomaly_not_found`, igual que
una inexistente, para no revelar que existe bajo otro tenant.
"""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from api.domain.entities.application import Application
from api.domain.repositories.anomaly_repository import AnomalyRecord
from api.domain.services.anomaly_service import AnomalyService
from api.domain.services.read_window import (
    DEFAULT_READ_LIMIT,
    MAX_READ_LIMIT,
    MIN_READ_LIMIT,
)
from api.infrastructure.db.repositories.sqlalchemy_anomaly_repository import (
    SQLAlchemyAnomalyRepository,
)
from api.infrastructure.db.session import get_session
from api.presentation.dependencies import require_api_key
from api.presentation.schemas.anomaly import AnomalyOut

# Los endpoints reciben un argumento por parámetro de query (FastAPI).
# pylint: disable=too-many-arguments,too-many-positional-arguments

router = APIRouter(prefix="/anomalies", tags=["Anomalies"])


def _to_out(record: AnomalyRecord) -> AnomalyOut:
    return AnomalyOut(
        anomaly_id=record.anomaly_id,
        application_id=record.application_id,
        metric_type_id=record.metric_type_id,
        metric_name=record.metric_name,
        model_id=record.model_id,
        bucket_start=record.bucket_start,
        bucket_seconds=record.bucket_seconds,
        expected_value=record.expected_value,
        actual_value=record.actual_value,
        severity_score=record.severity_score,
        confidence_score=record.confidence_score,
        detected_at=record.detected_at,
    )


@router.get(
    "",
    response_model=list[AnomalyOut],
    operation_id="listAnomalies",
)
async def list_anomalies(
    application: Annotated[Application, Depends(require_api_key)],
    session: Annotated[AsyncSession, Depends(get_session)],
    start: datetime | None = Query(
        default=None,
        description=(
            "Inicio de la ventana sobre detected_at (ISO 8601 UTC). "
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
    # Sin ge/le a propósito: el rango lo valida el servicio para responder
    # 422 `invalid_query_range` con el contrato ErrorResponse.
    limit: int = Query(
        default=DEFAULT_READ_LIMIT,
        description=(
            f"Máximo de anomalías a devolver ({MIN_READ_LIMIT}.."
            f"{MAX_READ_LIMIT}, default {DEFAULT_READ_LIMIT}). Fuera de "
            "rango → 422 invalid_query_range (sin clamp silencioso)."
        ),
    ),
    metric_type: int | None = Query(
        default=None, description="Filtro opcional por metric_type_id del catálogo."
    ),
) -> list[AnomalyOut]:
    """Anomalías de la app autenticada detectadas en la ventana, la más nueva
    primero (ISS-B-03)."""
    service = AnomalyService(SQLAlchemyAnomalyRepository(session))
    records = await service.list_anomalies(
        app_id=application.app_id,
        start=start,
        end=end,
        limit=limit,
        metric_type_id=metric_type,
    )
    return [_to_out(record) for record in records]


@router.get(
    "/{anomaly_id}",
    response_model=AnomalyOut,
    operation_id="getAnomaly",
)
async def get_anomaly(
    anomaly_id: UUID,
    application: Annotated[Application, Depends(require_api_key)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AnomalyOut:
    """Detalle de una anomalía de la app autenticada; de otra app → 404."""
    service = AnomalyService(SQLAlchemyAnomalyRepository(session))
    record = await service.get_anomaly(
        app_id=application.app_id, anomaly_id=anomaly_id
    )
    return _to_out(record)
