"""Dependencias de autenticación y autorización — design §4.5 (B3).

`get_current_user`: HTTPBearer(auto_error=False) → decode inválido/expirado
→ 401 invalid_token; usuario inexistente → 401 invalid_token; is_active=false
→ 403 user_inactive (ADR-15). `require_role(*roles)`: factory que valida el
rol denormalizado del token contra los roles permitidos → 403 forbidden
(ADR-04). `require_api_key`: guard reutilizable de ingesta (IAUTH-1..5,
ADR-19/ADR-22): X-API-Key ausente/inválida → 401 invalid_api_key con
WWW-Authenticate; key válida de app inactiva → 403 app_inactive; inyecta la
Application autenticada (binding 1:1, el app_id del payload nunca se confía).
Reutiliza `get_session` de infrastructure/db/session.py.
"""

from typing import Annotated
from uuid import UUID

import jwt as pyjwt
from fastapi import Depends
from fastapi.security import (
    APIKeyHeader,
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from sqlalchemy.ext.asyncio import AsyncSession

from api.config import get_settings
from api.domain.entities.application import Application
from api.domain.entities.lab_user import LabUser
from api.domain.exceptions import AuthenticationError, AuthorizationError
from api.domain.services.application_service import ApplicationService
from api.infrastructure.db.repositories.sqlalchemy_application_repository import (
    SQLAlchemyApplicationRepository,
)
from api.infrastructure.db.repositories.sqlalchemy_user_repository import (
    SQLAlchemyUserRepository,
)
from api.infrastructure.db.session import get_session
from api.infrastructure.security.jwt import decode_token

_bearer = HTTPBearer(auto_error=False)

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> LabUser:
    """Resuelve el LabUser autenticado a partir del bearer JWT (AUTH-5)."""
    if credentials is None:
        raise AuthenticationError("missing bearer token", code="invalid_token")

    settings = get_settings()
    try:
        payload = decode_token(credentials.credentials, settings.jwt_secret)
        user_id = UUID(payload["sub"])
    except (pyjwt.InvalidTokenError, KeyError, TypeError, ValueError) as exc:
        raise AuthenticationError(
            "invalid or expired token", code="invalid_token"
        ) from exc

    user = await SQLAlchemyUserRepository(session).get_by_id(user_id)
    if user is None:
        raise AuthenticationError("user not found", code="invalid_token")
    if not user.is_active:
        raise AuthorizationError("user is inactive", code="user_inactive")
    return user


def require_role(*roles: str):
    """Factory de dependencia: permite SOLO los roles indicados (ADR-04)."""

    async def _checker(
        current_user: Annotated[LabUser, Depends(get_current_user)],
    ) -> LabUser:
        if current_user.role.name not in roles:
            raise AuthorizationError("insufficient permissions", code="forbidden")
        return current_user

    return _checker


async def require_api_key(
    api_key: Annotated[str | None, Depends(_api_key_header)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> Application:
    """Guard reutilizable de ingesta: X-API-Key → Application (IAUTH-1..5).

    Ausente/inválida → 401 invalid_api_key con `WWW-Authenticate: ApiKey`
    (ADR-22: 401 + scheme, distinguible); key válida de app inactiva → 403
    app_inactive; key revocada → 401 (fail-closed). Inyecta la Application
    autenticada; el app_id del payload nunca se confía (IAUTH-2). No está
    cableado a ningún path en este cambio (IAUTH-5, wiring en #37).
    """
    if api_key is None:
        raise AuthenticationError(
            "missing api key",
            code="invalid_api_key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    service = ApplicationService(session, SQLAlchemyApplicationRepository(session))
    try:
        return await service.authenticate_api_key(api_key)
    except AuthenticationError as exc:
        # IAUTH-1/IAUTH-3: 401 indistinguible del caso ausente — mismo código
        # y mismo mensaje (sin información de causa), fail-closed.
        raise AuthenticationError(
            "missing api key",
            code="invalid_api_key",
            headers={"WWW-Authenticate": "ApiKey"},
        ) from exc
