"""Creación y validación de JWT HS256 access-only (ADR-01, AUTH-1).

Claims: sub=user_id, role (denormalizado), iat, exp (iat + N min),
iss="intellops-api". Sin refresh tokens (S4).
"""

from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt as pyjwt

DEFAULT_ISSUER = "intellops-api"


def create_access_token(
    user_id: UUID,
    role: str,
    *,
    secret: str,
    algorithm: str = "HS256",
    expire_minutes: int = 30,
    issuer: str = DEFAULT_ISSUER,
) -> str:
    """Genera un JWT firmado HS256 con los claims del contrato AUTH-1."""
    # pylint: disable=too-many-arguments  # firma explícita del design §4.1
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "role": role,
        "iat": now,
        "exp": now + timedelta(minutes=expire_minutes),
        "iss": issuer,
    }
    return pyjwt.encode(payload, secret, algorithm=algorithm)


def decode_token(
    token: str,
    secret: str,
    *,
    algorithms: list[str] | None = None,
    issuer: str = DEFAULT_ISSUER,
) -> dict:
    """Decodifica y valida firma/exp/iss; propaga jwt.InvalidTokenError.

    El caller traduce a 401 (AUTH-5); la excepción cubre expirado,
    firma inválida y claims ausentes/alterados.
    """
    return pyjwt.decode(token, secret, algorithms=algorithms or ["HS256"], issuer=issuer)
