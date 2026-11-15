"""Schemas Pydantic de la lectura de sesiones RUM (ISS-S3-03, #42).

`SessionOut` es la respuesta de `GET /sessions` y `GET /sessions/{session_id}`.
No incluye `user_id`, `ip_address`, `os_version`, `end_timestamp` ni
`duration_ms`: existen en el DDL pero en v1 siempre son NULL (ADR-0011), y
exponerlos sugeriría una funcionalidad que no existe. Se agregan al schema
cuando haya un proceso que los rellene (agregar un campo no rompe clientes).
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class SessionOut(BaseModel):
    """Sesión RUM de la aplicación autenticada con su actividad agregada."""

    session_id: UUID
    application_id: UUID  # tenant derivado de la key (OAS-14)
    start_timestamp: datetime  # primer evento recibido de la sesión
    last_activity_at: datetime | None = None  # observación, no cierre (ADR-0011)
    user_agent: str | None = None
    metric_count: int
    exception_count: int
