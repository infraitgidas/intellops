"""Puerto de lectura de anomalías (capa de dominio) — ISS-B-03 (#68).

`AnomalyRepository` abstrae la consulta app-scoped de `anomaly`: el tenant es
SIEMPRE parámetro del caller (ADR-0003/OAS-14), nunca un dato del request.
Es de solo lectura: las anomalías las escribe el detector (M3, D1).

`AnomalyRecord` expone las columnas reales de la tabla (ancla a la serie y
al bucket, ADR-0008) más el nombre del tipo de métrica del catálogo.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID

# pylint: disable=too-many-instance-attributes,too-few-public-methods  # DTO plano


@dataclass(frozen=True)
class AnomalyRecord:
    """Anomalía de la aplicación autenticada (ADR-0008, ADR-0012)."""

    anomaly_id: UUID
    application_id: UUID
    metric_type_id: int
    metric_name: str
    model_id: UUID
    bucket_start: datetime
    bucket_seconds: int
    expected_value: float
    actual_value: float
    severity_score: float
    confidence_score: float
    detected_at: datetime


class AnomalyRepository(Protocol):
    """Lectura app-scoped de anomalías: el tenant es parámetro (OAS-14)."""

    async def list_anomalies(
        self,
        app_id: UUID,
        start: datetime,
        end: datetime,
        limit: int,
        metric_type_id: int | None = None,
    ) -> list[AnomalyRecord]:
        """Anomalías de `app_id` detectadas en `[start, end)`, la más nueva
        primero, como máximo `limit`; opcionalmente de un solo tipo."""
        ...

    async def get_anomaly(
        self, app_id: UUID, anomaly_id: UUID
    ) -> AnomalyRecord | None:
        """La anomalía SOLO si pertenece a `app_id` (filtro por `anomaly_id`
        AND `application_id`, ADR-0003); si no, None."""
        ...
