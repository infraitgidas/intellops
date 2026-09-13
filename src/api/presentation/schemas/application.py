"""Schemas Pydantic de aplicaciones — design §4.5 (D1).

APP-2: `name` requerido no vacío (`min_length=1` → 422 en POST/PUT, APP-6),
`description` opcional. ADR-16: `api_token_hash` está presente en ApplicationRead
y SIEMPRE es null en S2-01 (columna dormida; S2-02 lo retira de las respuestas
al activar hashes reales). SEC-4: ningún hash real se expone.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from .common import NoNul


class ApplicationCreate(BaseModel):
    """Payload de POST /applications: name requerido no vacío (APP-2/APP-6)."""

    name: NoNul = Field(min_length=1)
    description: NoNul | None = None


class ApplicationUpdate(BaseModel):
    """Payload de PUT /applications/{id}: todos los campos opcionales (APP-3).

    `name` sigue exigiendo min_length=1 cuando se envía (APP-6).
    """

    name: NoNul | None = Field(default=None, min_length=1)
    description: NoNul | None = None


class ApplicationRead(BaseModel):
    """Contrato de salida de aplicación — api_token_hash siempre null (ADR-16).

    `from_attributes=True` permite responder directamente con el ORM
    Application desde los routers (response_model de solo lectura).
    """

    model_config = ConfigDict(from_attributes=True)

    app_id: UUID
    name: str
    description: str | None
    api_token_hash: None
    created_at: datetime
