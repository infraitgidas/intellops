"""AlertService — lectura de alertas del tenant (ISS-B-03, #68).

Acota la consulta con `read_window` (ventana default 24 h sobre `created_at`,
máximo 7 días, `limit` 1..500) y valida el filtro `status` contra el catálogo
(`pending`, `sent`, `failed`) antes de delegar en el repositorio. Un estado
desconocido → `QueryRangeError` (422 `invalid_query_range`, contrato
ErrorResponse) sin ejecutar la consulta. El tenant proviene EXCLUSIVAMENTE
del caller (OAS-14).
"""

from datetime import datetime
from uuid import UUID

from api.domain.exceptions import QueryRangeError
from api.domain.repositories.alert_repository import (
    ALERT_STATUSES,
    AlertRecord,
    AlertRepository,
)
from api.domain.services.read_window import bounded_limit, bounded_window

# pylint: disable=too-few-public-methods  # caso de uso con un solo método público


class AlertService:
    """Aplica los límites de la consulta y delega en el repositorio."""

    def __init__(self, repository: AlertRepository) -> None:
        self._repository = repository

    async def list_alerts(
        self,
        app_id: UUID,
        start: datetime | None = None,
        end: datetime | None = None,
        limit: int | None = None,
        status: str | None = None,
    ) -> list[AlertRecord]:
        """Alertas del tenant creadas en la ventana, la más nueva primero."""
        start, end = bounded_window(start, end)
        effective_limit = bounded_limit(limit)
        if status is not None and status not in ALERT_STATUSES:
            raise QueryRangeError(
                f"status must be one of {', '.join(ALERT_STATUSES)}, got {status!r}"
            )
        return await self._repository.list_alerts(
            app_id=app_id,
            start=start,
            end=end,
            limit=effective_limit,
            status=status,
        )
