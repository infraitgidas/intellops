"""Schemas Pydantic de autenticación — design §4.5 (B1)."""

from typing import Literal

from pydantic import BaseModel

from .common import LabEmail


class LoginRequest(BaseModel):
    """Payload de POST /auth/login (email validado, AUTH-1)."""

    email: LabEmail
    password: str


class AuthResponse(BaseModel):
    """Contrato de login exitoso: token HS256 + metadata (AUTH-1)."""

    access_token: str
    token_type: Literal["bearer"]
    expires_in: int
