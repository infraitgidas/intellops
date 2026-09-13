"""Schemas Pydantic de usuarios — design §4.5 (C1).

SEC-4: ningún schema de salida expone `password_hash`; UserRead solo lleva
los campos del contrato (USR-1/USR-2). `email` usa LabEmail de
schemas/common (ADR-12): el seed 0002 y las fixtures usan dominios reserved
(.local) que EmailStr plano rechazaría. `password` exige >= 8 chars (USR-3).
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from .common import LabEmail, NoNul


class UserCreate(BaseModel):
    """Payload de POST /users: campos requeridos + password >= 8 (USR-3)."""

    name: NoNul
    email: LabEmail
    password: NoNul = Field(min_length=8)
    role_id: int


class UserUpdate(BaseModel):
    """Payload de PUT /users/{id}: todos los campos opcionales (USR-5).

    `password` solo dispara re-hash cuando se envía explícitamente.
    """

    name: NoNul | None = None
    email: LabEmail | None = None
    password: NoNul | None = Field(default=None, min_length=8)
    is_active: bool | None = None
    role_id: int | None = None


class UserRead(BaseModel):
    """Contrato de salida de usuario — sin password_hash (SEC-4).

    `from_attributes=True` permite responder directamente con el ORM
    LabUser desde los routers (response_model de solo lectura).
    """

    model_config = ConfigDict(from_attributes=True)

    user_id: UUID
    name: str
    email: str
    role_id: int
    is_active: bool
    last_login: datetime | None
    created_at: datetime
