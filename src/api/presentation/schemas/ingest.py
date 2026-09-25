"""Pydantic schemas de ingesta — espejo del contrato (OAS-11/12, D2).

El ENVELOPE (RumEventBatch/JsExceptionBatch) valida estrictamente:
schema_version == "1.0", 1..500 events. El EVENTO es laxo a propósito: los
UUID, timestamps, unidades, rangos y límites de forma (error_type ≤ 100,
message ≤ 2000, stack_trace ≤ 20000, ≤ 50 metrics) los aplica la POLÍTICA
por evento → 202 parcial con su código, no un 422 que rechace el batch
completo (RUM-3/RUM-4). `application_id` está fuera de required (OAS-12):
nunca es autoridad de tenant (IAUTH-2).
"""

from pydantic import BaseModel, Field


class RumMetric(BaseModel):
    """Métrica RUM — campos laxos; la política valida tipo/unidad/rango."""

    type: str
    value: float
    unit: str
    timestamp: str | None = None
    page_url: str | None = None
    metadata: dict | None = None


class RumEvent(BaseModel):
    """Evento RUM — laxo; application_id opcional (OAS-12, D2)."""

    schema_version: str
    timestamp: str
    session_id: str
    application_id: str | None = None
    metrics: list[RumMetric]
    metadata: dict | None = None


class RumEventBatch(BaseModel):
    """Envelope de métricas RUM — estricto (RUM-2)."""

    schema_version: str = Field(pattern="^1\\.0$")
    events: list[RumEvent] = Field(min_length=1, max_length=500)


class JsExceptionEvent(BaseModel):
    """Excepción JS — laxa; application_id opcional (OAS-12, D2)."""

    schema_version: str
    error_type: str
    message: str
    stack_trace: str | None = None
    session_id: str
    application_id: str | None = None
    metric_id: str | None = None
    timestamp: str


class JsExceptionBatch(BaseModel):
    """Envelope de excepciones JS — estricto (RUM-2)."""

    schema_version: str = Field(pattern="^1\\.0$")
    events: list[JsExceptionEvent] = Field(min_length=1, max_length=500)


class RejectedEvent(BaseModel):
    """Evento rechazado: posición original en events + código de razón."""

    index: int
    reason: str


class IngestResponse(BaseModel):
    """Respuesta 202: batch_id generado por el servidor (no se persiste)."""

    batch_id: str
    accepted: int
    rejected: list[RejectedEvent]
