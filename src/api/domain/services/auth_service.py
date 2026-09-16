"""Caso de uso de autenticación: login (anti-enumeración) y logout stateless.

Design §4.4 — ADR-01 (access-only HS256), ADR-10 (el servicio commitea y
hace rollback ante DomainError), ADR-13 (dummy verify para igualar timing),
SEC-1 (401 indistinguible) y SEC-2 (403 si is_active=false).
El seed Admin NO vive aquí: es SQL de la migración 0002 (DATA-3).
"""

from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from api.config import get_settings
from api.domain.exceptions import AuthenticationError, AuthorizationError, DomainError
from api.domain.repositories.user_repository import UserRepository
from api.infrastructure.security.jwt import create_access_token
from api.infrastructure.security.password import DUMMY_HASH, PasswordHasher
from api.presentation.schemas.auth import AuthResponse


class AuthService:
    """Operaciones de autenticación sobre el UserRepository (sin estado propio)."""

    def __init__(self, session: AsyncSession, user_repository: UserRepository) -> None:
        self._session = session
        self._users = user_repository
        self._hasher = PasswordHasher()

    async def login(self, email: str, password: str) -> AuthResponse:
        """Autentica email+password y emite el JWT con role denormalizado.

        - usuario null o password_hash null → verify contra DUMMY_HASH (ADR-13)
        - password incorrecta → 401 idéntico (SEC-1)
        - is_active=false → 403 sin tocar last_login (SEC-2)
        - OK → last_login=now + commit + token (AUTH-1)
        """
        try:
            user = await self._users.get_by_email(email)
            if user is None or user.password_hash is None:
                self._hasher.verify_password(password, DUMMY_HASH)
                raise AuthenticationError("invalid email or password")
            if not self._hasher.verify_password(password, user.password_hash):
                raise AuthenticationError("invalid email or password")
            if not user.is_active:
                raise AuthorizationError("user is inactive", code="user_inactive")

            user.last_login = datetime.now(timezone.utc)
            await self._session.commit()

            settings = get_settings()
            token = create_access_token(
                user.user_id,
                user.role.name,
                secret=settings.jwt_secret,
                algorithm=settings.jwt_algorithm,
                expire_minutes=settings.jwt_access_token_expire_minutes,
            )
            return AuthResponse(
                access_token=token,
                token_type="bearer",
                expires_in=settings.jwt_access_token_expire_minutes * 60,
            )
        except DomainError:
            # ADR-10: ante error de dominio, la sesión queda limpia para el
            # próximo request (no hay mutaciones pendientes en estos paths).
            await self._session.rollback()
            raise

    async def logout(self) -> None:
        """Contrato stateless (AUTH-4): el servidor no persiste ningún estado."""
        return None
