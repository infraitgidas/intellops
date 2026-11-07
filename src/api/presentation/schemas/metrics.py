"""Schemas Pydantic del read path de telemetría (OAS-13, ISS-S3-01).

`MetricAggregateOut` es el shape ML C6 serializable de `GET /metrics/query`
(application_id, metric_type_id, timestamp, value, session_count);
`MetricTypeInfoOut` la entrada del catálogo de `GET /metrics/list`;
`ProbeRunOut` una ejecución de la sonda HTTP de `GET /metrics/probes` (B.13).
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class MetricAggregateOut(BaseModel):
    """Fila agregada del read path — shape ML C6 (TQ-1)."""

    application_id: UUID
    metric_type_id: int
    timestamp: datetime  # inicio del bucket (anclado a la ventana)
    value: float  # AVG(value) del bucket
    session_count: int  # COUNT(DISTINCT session_id) del bucket


class MetricTypeInfoOut(BaseModel):
    """Entrada del catálogo metric_type (/metrics/list, OAS-13)."""

    metric_type_id: int
    name: str
    description: str | None = None


class ProbeRunOut(BaseModel):
    """Una ejecución de la sonda HTTP de disponibilidad (B.13/T6, D3).

    `target`/`http_status`/`outcome`/`latency_ms` vienen de `metadata` (null
    cuando la clave falta) y `available` es `value == 1` (D1).
    """

    timestamp: datetime
    target: str | None = None
    http_status: int | None = None
    outcome: str | None = None
    latency_ms: float | None = None
    available: bool
