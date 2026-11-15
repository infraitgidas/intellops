"""Lectura de sesiones RUM — GET /sessions y GET /sessions/{session_id}
(ISS-S3-03, #42).

Ambos aplican `Depends(require_api_key)` igual que `/metrics/*` (OAS-14,
ADR-0003): el tenant se deriva EXCLUSIVAMENTE de la key; no existe parámetro
de aplicación en el request. No hay POST: la sesión la crea la ingesta en el
primer evento (ADR-0002) y el agente no reporta su fin (ADR-0011).

`GET /sessions/{session_id}` filtra por `session_id` AND `app_id`: una sesión
de otra aplicación responde 404 `session_not_found`, igual que una
inexistente, para no revelar que existe bajo otro tenant.
"""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from api.domain.entities.application import Application
from api.domain.repositories.session_repository import SessionSummary
from api.domain.services.session_service import (
    DEFAULT_SESSION_LIMIT,
    MAX_SESSION_LIMIT,
    MIN_SESSION_LIMIT,
    SessionService,
)
from api.infrastructure.db.repositories.sqlalchemy_session_repository import (
    SQLAlchemySessionRepository,
)
from api.infrastructure.db.session import get_session
from api.presentation.dependencies import require_api_key
from api.presentation.schemas.session import SessionOut

router = APIRouter(prefix="/sessions", tags=["Sessions"])


def _to_out(summary: SessionSummary) -> SessionOut:
    return SessionOut(
        session_id=summary.session_id,
        application_id=summary.application_id,
        start_timestamp=summary.start_timestamp,
        last_activity_at=summary.last_activity_at,
        user_agent=summary.user_agent,
        metric_count=summary.metric_count,
        exception_count=summary.exception_count,
    )


@router.get(
    "",
    response_model=list[SessionOut],
    operation_id="listSessions",
)
async def list_sessions(
    application: Annotated[Application, Depends(require_api_key)],
    session: Annotated[AsyncSession, Depends(get_session)],
    start: datetime | None = Query(
        default=None,
        description=(
            "Inicio de la ventana sobre start_timestamp (ISO 8601 UTC). "
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
    # Sin ge/le a propósito: el rango lo valida SessionService para responder
    # 422 `invalid_query_range` con el contrato ErrorResponse, igual que
    # `bucket_seconds` en /metrics/query (review de la PR de ISS-S3-03).
    limit: int = Query(
        default=DEFAULT_SESSION_LIMIT,
        description=(
            f"Máximo de sesiones a devolver ({MIN_SESSION_LIMIT}.."
            f"{MAX_SESSION_LIMIT}, default {DEFAULT_SESSION_LIMIT}). Fuera de "
            "rango → 422 invalid_query_range (sin clamp silencioso)."
        ),
    ),
) -> list[SessionOut]:
    """Sesiones de la app autenticada iniciadas en la ventana, la más nueva
    primero (ISS-S3-03)."""
    service = SessionService(SQLAlchemySessionRepository(session))
    summaries = await service.list_sessions(
        app_id=application.app_id, start=start, end=end, limit=limit
    )
    return [_to_out(summary) for summary in summaries]


@router.get(
    "/{session_id}",
    response_model=SessionOut,
    operation_id="getSession",
)
async def get_session_detail(
    session_id: UUID,
    application: Annotated[Application, Depends(require_api_key)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> SessionOut:
    """Detalle de una sesión de la app autenticada; de otra app → 404."""
    service = SessionService(SQLAlchemySessionRepository(session))
    summary = await service.get_session(
        app_id=application.app_id, session_id=session_id
    )
    return _to_out(summary)
