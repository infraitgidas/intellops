"""Schema Pydantic de la lectura de alertas (ISS-B-03, #68).

`AlertOut` es la respuesta de `GET /alerts`. No incluye `recipient` (mail o
chat id del dispatcher, ADR-0012). `anomaly_id` es null en las alertas de
reglas de umbral (v1) y `channel`/`sent_at` son null hasta que B.10 despacha
la alerta.

`severity` es un Literal cerrado porque la base lo garantiza con
`ck_alert_severity` (0007). `status` y `channel` son `str`: salen de los
catálogos `alert_status` y `alert_channel`, que no tienen CHECK. Si se
agrega un canal (p. ej. Slack) con un INSERT, un Literal cerrado haría
fallar la validación de la respuesta y `GET /alerts` respondería 500.
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
    status: str  # nombre de alert_status en minúsculas
    channel: str | None = None  # nombre de alert_channel en minúsculas
    created_at: datetime
    sent_at: datetime | None = None
