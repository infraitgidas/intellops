"""Read path de telemetría — GET /metrics/query y GET /metrics/list (ISS-S3-01).

Ambos aplican `Depends(require_api_key)` (OAS-14): el tenant se deriva
EXCLUSIVAMENTE de la key; no existe parámetro de aplicación en el request.
`QueryService` acota la ventana (default 15 min, ≤ 7 d, bucket ≥ 60 s,
start < end → 422 `invalid_query_range`, TQ-2) antes de delegar en
`SQLAlchemyQueryRepository` (agregación EN SQL, DD-9).
"""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from api.domain.entities.application import Application
from api.domain.services.query_service import QueryService
from api.infrastructure.db.repositories.sqlalchemy_query_repository import (
    SQLAlchemyQueryRepository,
)
from api.infrastructure.db.session import get_session
from api.presentation.dependencies import require_api_key
from api.presentation.schemas.metrics import MetricAggregateOut, MetricTypeInfoOut

router = APIRouter(prefix="/metrics", tags=["Metrics"])


@router.get(
    "/query",
    response_model=list[MetricAggregateOut],
    operation_id="queryMetrics",
)
async def query_metrics(
    application: Annotated[Application, Depends(require_api_key)],
    session: Annotated[AsyncSession, Depends(get_session)],
    start: datetime | None = Query(
        default=None,
        description="Inicio de la ventana (ISO 8601 UTC). Default: ahora - 15 min (TQ-2).",
    ),
    end: datetime | None = Query(
        default=None,
        description=(
            "Fin de la ventana (ISO 8601 UTC). Default: ahora. "
            "Máximo 7 días desde start (TQ-2)."
        ),
    ),
    bucket_seconds: int | None = Query(
        default=None,
        description=(
            "Tamaño del bucket temporal en segundos (mínimo 60, TQ-2). "
            "Default: 60."
        ),
    ),
    metric_type: int | None = Query(
        default=None, description="Filtro opcional por metric_type_id del catálogo."
    ),
) -> list[MetricAggregateOut]:
    """Métricas RUM de la app autenticada agregadas por bucket (OAS-13/14)."""
    service = QueryService(SQLAlchemyQueryRepository(session))
    aggregates = await service.query(
        app_id=application.app_id,
        start=start,
        end=end,
        bucket_seconds=bucket_seconds,
        metric_type_id=metric_type,
    )
    return [
        MetricAggregateOut(
            application_id=row.application_id,
            metric_type_id=row.metric_type_id,
            timestamp=row.timestamp,
            value=row.value,
            session_count=row.session_count,
        )
        for row in aggregates
    ]


@router.get(
    "/list",
    response_model=list[MetricTypeInfoOut],
    operation_id="listMetrics",
)
async def list_metrics(
    application: Annotated[Application, Depends(require_api_key)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[MetricTypeInfoOut]:
    """Catálogo metric_type de la plataforma (OAS-13)."""
    service = QueryService(SQLAlchemyQueryRepository(session))
    types = await service.list_metric_types()
    return [
        MetricTypeInfoOut(
            metric_type_id=row.metric_type_id,
            name=row.name,
            description=row.description,
        )
        for row in types
    ]
