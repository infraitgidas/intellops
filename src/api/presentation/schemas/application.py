"""Schemas Pydantic de aplicaciones — design §4.5 (D1).

APP-2: `name` requerido no vacío (`min_length=1` → 422 en POST/PUT, APP-6),
`description` opcional. APP-7: `is_active` default true en Create, mutable
en Update y presente en Read (migración 0003). ADR-16: `api_token_hash`
está retirado de `ApplicationRead` (el hash es dato interno); el plaintext
de la API key solo aparece una vez en `ApiKeyResponse` (show-once, CRED-1).
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from .common import NoNul


class ApplicationCreate(BaseModel):
    """Payload de POST /applications: name requerido no vacío (APP-2/APP-6)."""

    name: NoNul = Field(min_length=1)
    description: NoNul | None = None
    is_active: bool = True


class ApplicationUpdate(BaseModel):
    """Payload de PUT /applications/{id}: todos los campos opcionales (APP-3).

    `name` sigue exigiendo min_length=1 cuando se envía (APP-6);
    `is_active` es mutable (APP-7): None = no se actualiza.
    """

    name: NoNul | None = Field(default=None, min_length=1)
    description: NoNul | None = None
    is_active: bool | None = None


class ApplicationRead(BaseModel):
    """Contrato de salida de aplicación — sin api_token_hash (ADR-16, APP-9).

    `from_attributes=True` permite responder directamente con el ORM
    Application desde los routers (response_model de solo lectura).
    """

    model_config = ConfigDict(from_attributes=True)

    app_id: UUID
    name: str
    description: str | None
    is_active: bool
    created_at: datetime


class ApiKeyResponse(BaseModel):
    """Respuesta show-once de emisión de API key (CRED-1, design §4).

    `api_key` es el plaintext (solo en el 201, nunca se persiste);
    `hint` son los últimos 4 caracteres, no persistidos.
    """

    model_config = ConfigDict(from_attributes=True)

    api_key: str
    hint: str
