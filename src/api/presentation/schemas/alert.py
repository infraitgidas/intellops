"""Schema Pydantic de la lectura de alertas (ISS-B-03, #68).

`AlertOut` es la respuesta de `GET /alerts`. No incluye `recipient` (mail o
chat id del dispatcher, ADR-0012). `anomaly_id` es null en las alertas de
reglas de umbral (v1) y `channel`/`sent_at` son null hasta que B.10 despacha
la alerta.
"""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class AlertOut(BaseModel):
    """Alerta de la aplicación autenticada."""

    alert_id: UUID
    application_id: UUID  # tenant derivado de la key (OAS-14)
    anomaly_id: UUID | None = None
    severity: Literal["low", "medium", "high", "critical"]
    message: str
    status: Literal["pending", "sent", "failed"]
    channel: Literal["telegram", "email"] | None = None
    created_at: datetime
    sent_at: datetime | None = None
