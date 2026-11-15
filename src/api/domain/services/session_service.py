"""SessionService — límites de la lectura de sesiones RUM (ISS-S3-03, #42).

Acota la consulta ANTES de tocar el repositorio, con la misma disciplina que
`QueryService` (TQ-2): `start < end`, ventana máxima de 7 días y `limit`
1..500 sin clamp silencioso; cualquier violación → `QueryRangeError` (422
`invalid_query_range`, ADR-09) sin ejecutar la consulta.

La ventana default es de 24 h (no los 15 min de `/metrics/query`): una
sesión vive hasta 24 h del lado del agente (ContratoAgenteRUM §2.1), así que
una ventana de 15 min dejaría afuera casi todas las sesiones en curso.

El tenant proviene EXCLUSIVAMENTE del caller (OAS-14). Una sesión
inexistente o de otra aplicación → `NotFoundError` (404 `session_not_found`):
el servicio no distingue ambos casos para no revelar que la sesión existe
bajo otro tenant (ADR-0003).
"""

from datetime import datetime, timedelta, timezone
from uuid import UUID

from api.domain.exceptions import NotFoundError, QueryRangeError
from api.domain.repositories.session_repository import (
    SessionRepository,
    SessionSummary,
)
from api.domain.services.query_service import MAX_WINDOW_DAYS

DEFAULT_SESSION_WINDOW_HOURS = 24

MIN_SESSION_LIMIT = 1
MAX_SESSION_LIMIT = 500
DEFAULT_SESSION_LIMIT = 50


def _as_utc(value: datetime) -> datetime:
    """Normaliza a UTC aware (los naive se asumen UTC)."""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


class SessionService:
    """Aplica los límites de la consulta y delega en el repositorio."""

    def __init__(self, repository: SessionRepository) -> None:
        self._repository = repository

    async def list_sessions(
        self,
        app_id: UUID,
        start: datetime | None = None,
        end: datetime | None = None,
        limit: int | None = None,
    ) -> list[SessionSummary]:
        """Sesiones del tenant iniciadas en la ventana, la más nueva primero."""
        end = _as_utc(end or datetime.now(timezone.utc))
        start = _as_utc(
            start or (end - timedelta(hours=DEFAULT_SESSION_WINDOW_HOURS))
        )
        effective_limit = DEFAULT_SESSION_LIMIT if limit is None else limit

        if start >= end:
            raise QueryRangeError("start must be before end")
        if end - start > timedelta(days=MAX_WINDOW_DAYS):
            raise QueryRangeError(f"window exceeds {MAX_WINDOW_DAYS} days")
        if not MIN_SESSION_LIMIT <= effective_limit <= MAX_SESSION_LIMIT:
            raise QueryRangeError(
                f"limit must be between {MIN_SESSION_LIMIT} and "
                f"{MAX_SESSION_LIMIT}, got {effective_limit}"
            )

        return await self._repository.list_sessions(
            app_id=app_id, start=start, end=end, limit=effective_limit
        )

    async def get_session(self, app_id: UUID, session_id: UUID) -> SessionSummary:
        """La sesión del tenant; inexistente o de otra app → 404 (ADR-0003)."""
        summary = await self._repository.get_session(
            app_id=app_id, session_id=session_id
        )
        if summary is None:
            raise NotFoundError("session not found", code="session_not_found")
        return summary
