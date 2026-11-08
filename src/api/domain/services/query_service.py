"""QueryService — límites del read path de telemetría (TQ-2, ISS-S3-01).

Acota la consulta ANTES de tocar el repositorio: ventana default 15 minutos,
máximo 7 días, bucket mínimo 60 s y `start < end`; cualquier violación →
`QueryRangeError` (422 `invalid_query_range`, ADR-09) sin ejecutar la
agregación. El tenant proviene EXCLUSIVAMENTE del caller (OAS-14): el
servicio nunca deriva autoridad de parámetros de request.

`list_probe_runs` (B.13/T6) aplica la misma disciplina al `limit` de
`GET /metrics/probes`: 1..500, default 50, sin clamp silencioso.
"""

from datetime import datetime, timedelta, timezone
from uuid import UUID

from api.domain.exceptions import QueryRangeError
from api.domain.repositories.query_repository import (
    MetricAggregate,
    MetricTypeInfo,
    ProbeRun,
    QueryRepository,
)

DEFAULT_WINDOW_MINUTES = 15
MAX_WINDOW_DAYS = 7
MIN_BUCKET_SECONDS = 60
DEFAULT_BUCKET_SECONDS = 60

# B.13/T6: corridas de la sonda por página — 1..500, default 50.
MIN_PROBE_LIMIT = 1
MAX_PROBE_LIMIT = 500
DEFAULT_PROBE_LIMIT = 50


class QueryService:
    """Aplica los límites TQ-2 y delega la agregación en el repositorio."""

    def __init__(self, repository: QueryRepository) -> None:
        self._repository = repository

    async def query(
        self,
        app_id: UUID,
        start: datetime | None,
        end: datetime | None,
        bucket_seconds: int | None,
        metric_type_id: int | None = None,
    ) -> list[MetricAggregate]:
        """Consulta app-scoped con la ventana acotada (TQ-2)."""
        end = self._as_utc(end or datetime.now(timezone.utc))
        start = self._as_utc(
            start or (end - timedelta(minutes=DEFAULT_WINDOW_MINUTES))
        )
        bucket = bucket_seconds or DEFAULT_BUCKET_SECONDS

        if start >= end:
            raise QueryRangeError("start must be before end")
        if end - start > timedelta(days=MAX_WINDOW_DAYS):
            raise QueryRangeError("window exceeds 7 days")
        if bucket < MIN_BUCKET_SECONDS:
            raise QueryRangeError("bucket_seconds must be at least 60")

        return await self._repository.query_metrics(
            app_id=app_id,
            start=start,
            end=end,
            bucket_seconds=bucket,
            metric_type_id=metric_type_id,
        )

    async def list_metric_types(self) -> list[MetricTypeInfo]:
        """Catálogo metric_type (delegado al repositorio, OAS-13)."""
        return await self._repository.list_metric_types()

    async def list_probe_runs(
        self, app_id: UUID, limit: int | None = None
    ) -> list[ProbeRun]:
        """Corridas de la sonda HTTP del tenant, de la más nueva a la más vieja.

        `limit` fuera de 1..500 → `QueryRangeError` (422) SIN consultar el
        repositorio: el endpoint no aplica un clamp silencioso (B.13/T6).
        """
        effective_limit = DEFAULT_PROBE_LIMIT if limit is None else limit
        if not MIN_PROBE_LIMIT <= effective_limit <= MAX_PROBE_LIMIT:
            raise QueryRangeError(
                f"limit must be between {MIN_PROBE_LIMIT} and "
                f"{MAX_PROBE_LIMIT}, got {effective_limit}"
            )
        return await self._repository.list_probe_runs(
            app_id=app_id, limit=effective_limit
        )

    @staticmethod
    def _as_utc(value: datetime) -> datetime:
        """Normaliza a UTC aware (los naive se asumen UTC; sin tzinfo el
        contrato date-time de FastAPI es inválido pero defensivo aquí)."""
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
