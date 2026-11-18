"""AnomalyService — lectura de anomalías del tenant (ISS-B-03, #68).

Acota la consulta con `read_window` (ventana default 24 h, máximo 7 días,
`limit` 1..500) antes de delegar en el repositorio. El tenant proviene
EXCLUSIVAMENTE del caller (OAS-14).

Una anomalía inexistente o de otra aplicación → `NotFoundError` (404
`anomaly_not_found`): el servicio no distingue ambos casos para no revelar
que la anomalía existe bajo otro tenant (ADR-0003).
"""

from datetime import datetime
from uuid import UUID

from api.domain.exceptions import NotFoundError
from api.domain.repositories.anomaly_repository import (
    AnomalyRecord,
    AnomalyRepository,
)
from api.domain.services.read_window import bounded_limit, bounded_window


class AnomalyService:
    """Aplica los límites de la consulta y delega en el repositorio."""

    def __init__(self, repository: AnomalyRepository) -> None:
        self._repository = repository

    async def list_anomalies(
        self,
        app_id: UUID,
        start: datetime | None = None,
        end: datetime | None = None,
        limit: int | None = None,
        metric_type_id: int | None = None,
    ) -> list[AnomalyRecord]:
        """Anomalías del tenant detectadas en la ventana, la más nueva primero."""
        start, end = bounded_window(start, end)
        effective_limit = bounded_limit(limit)
        return await self._repository.list_anomalies(
            app_id=app_id,
            start=start,
            end=end,
            limit=effective_limit,
            metric_type_id=metric_type_id,
        )

    async def get_anomaly(self, app_id: UUID, anomaly_id: UUID) -> AnomalyRecord:
        """La anomalía del tenant; inexistente o de otra app → 404 (ADR-0003)."""
        record = await self._repository.get_anomaly(
            app_id=app_id, anomaly_id=anomaly_id
        )
        if record is None:
            raise NotFoundError("anomaly not found", code="anomaly_not_found")
        return record
