"""Rutas de ingesta RUM — POST /telemetry/metrics y /telemetry/exceptions.

Ambas aplican `Depends(require_api_key)` (IAUTH-5, RUM-1): 401/403 del guard
antes de tocar el body. La cola y los contadores se leen de `app.state`
(inyectados por el lifespan en producción; por los tests en suite). El 202
se responde al ENCOLAR (semántica §3.4): el worker persiste después.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Request, status

from api.domain.entities.application import Application
from api.domain.services.ingest_service import IngestService
from api.presentation.dependencies import require_api_key
from api.presentation.schemas.ingest import (
    IngestResponse,
    JsExceptionBatch,
    RumEventBatch,
)

router = APIRouter(prefix="/telemetry", tags=["Telemetry"])


@router.post(
    "/metrics",
    response_model=IngestResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def ingest_metrics(
    payload: RumEventBatch,
    application: Annotated[Application, Depends(require_api_key)],
    request: Request,
) -> IngestResponse:
    """Ingesta de métricas RUM (batch ≤ 500; 202 parcial, 503 backpressure)."""
    service = IngestService(
        queue=request.app.state.ingest_queue,
        counters=request.app.state.ingest_counters,
    )
    return await service.process_batch(payload, tenant_app_id=application.app_id)


@router.post(
    "/exceptions",
    response_model=IngestResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def ingest_exceptions(
    payload: JsExceptionBatch,
    application: Annotated[Application, Depends(require_api_key)],
    request: Request,
) -> IngestResponse:
    """Ingesta de excepciones JavaScript (batch ≤ 500; 202 parcial)."""
    service = IngestService(
        queue=request.app.state.ingest_queue,
        counters=request.app.state.ingest_counters,
    )
    return await service.process_batch(payload, tenant_app_id=application.app_id)
