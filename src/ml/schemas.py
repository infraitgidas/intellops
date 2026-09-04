"""Módulo de esquemas y contratos de datos para el módulo IA."""
from datetime import datetime
from pydantic import BaseModel, UUID4


class MetricBatchInput(BaseModel):
    """Esquema de validación para el lote de métricas de entrada."""
    application_id: UUID4
    metric_id: UUID4
    metric_type_id: int
    timestamp: datetime
    value: float
    session_count: int
