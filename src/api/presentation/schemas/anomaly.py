"""Schema Pydantic de la lectura de anomalías (ISS-B-03, #68).

`AnomalyOut` es la respuesta de `GET /anomalies` y `GET /anomalies/{id}`.
Expone las columnas reales de `anomaly` (ancla a la serie y al bucket,
ADR-0008) y no los campos del borrador inicial del contrato (`detector`,
`description`, `metrics_snapshot`, `severity` como enum) que la tabla no
guarda. Los scores se exponen tal como los escribe el detector, sin mapearlos
a una severidad (ADR-0012).
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class AnomalyOut(BaseModel):
    """Anomalía de la aplicación autenticada."""

    anomaly_id: UUID
    application_id: UUID  # tenant derivado de la key (OAS-14)
    metric_type_id: int
    metric_name: str  # nombre del catálogo metric_type
    model_id: UUID
    bucket_start: datetime  # inicio del bucket de la serie (ADR-0008)
    bucket_seconds: int
    expected_value: float
    actual_value: float
    severity_score: float
    confidence_score: float
    detected_at: datetime  # instante de detección
