"""Puerto del read path de telemetría (capa de dominio) — TQ-1 (ISS-S3-01).

`QueryRepository` abstrae la consulta app-scoped de métricas RUM agregadas
por bucket temporal y el catálogo de tipos. La implementación SQLAlchemy
agrega EN SQL (DD-9): el proceso recibe solo filas agregadas, sin
materializar el rango.

`MetricAggregate` es el shape ML C6 (base `MetricBatchInput` de S3-04 sin
`metric_id`: fila agregada): `(application_id, metric_type_id, timestamp,
value, session_count)` con `timestamp` = inicio del bucket (anclado a la
ventana del request, no a medianoche UTC).
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID

# pylint: disable=too-few-public-methods  # DTOs planos


@dataclass(frozen=True)
class MetricAggregate:
    """Fila agregada del read path — shape ML C6 (TQ-1)."""

    application_id: UUID
    metric_type_id: int
    timestamp: datetime  # inicio del bucket (anclado a la ventana)
    value: float  # AVG(value) del bucket
    session_count: int  # COUNT(DISTINCT session_id) del bucket


@dataclass(frozen=True)
class MetricTypeInfo:
    """Entrada del catálogo metric_type (/metrics/list, OAS-13)."""

    metric_type_id: int
    name: str
    description: str | None = None


class QueryRepository(Protocol):
    """Read path app-scoped: el tenant es parámetro (OAS-14), nunca query."""

    async def query_metrics(
        self,
        app_id: UUID,
        start: datetime,
        end: datetime,
        bucket_seconds: int,
        metric_type_id: int | None = None,
    ) -> list[MetricAggregate]:
        """Métricas de `app_id` agregadas por bucket temporal (TQ-1)."""
        ...

    async def list_metric_types(self) -> list[MetricTypeInfo]:
        """Catálogo metric_type completo (metric_type_id, name, description)."""
        ...
