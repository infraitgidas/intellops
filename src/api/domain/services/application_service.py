"""Caso de uso de aplicaciones: list/get/create/update/delete (design §4.4, D2).

ADR-10 (el servicio commitea y hace rollback ante DomainError), ADR-07
(delete físico; FK RESTRICT de user_session.app_id → ConflictError 409 con
rollback), APP-1..APP-4 (404 en get/update/delete de inexistente;
api_token_hash queda None en create — columna dormida, ADR-16) y CRED-1..5
(emisión/revocación/autenticación de API key de ingesta, S2-02).
"""

import hmac
from typing import NamedTuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from api.config import get_settings
from api.domain.entities.application import Application
from api.domain.exceptions import (
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    DomainError,
    NotFoundError,
)
from api.domain.repositories.application_repository import ApplicationRepository
from api.infrastructure.security.api_keys import (
    DEFAULT_KEY_PREFIX,
    generate_api_key,
    hash_api_key,
)
from api.presentation.schemas.application import ApplicationCreate, ApplicationUpdate


class IssuedApiKey(NamedTuple):
    """Key emitida + hint show-once (CRED-1; el hint no se persiste)."""

    api_key: str
    hint: str


class ApplicationService:
    """Operaciones de aplicaciones sobre el ApplicationRepository (sin estado)."""

    def __init__(
        self, session: AsyncSession, application_repository: ApplicationRepository
    ) -> None:
        self._session = session
        self._applications = application_repository

    async def list_applications(self) -> list[Application]:
        """Lista todas las aplicaciones (APP-1)."""
        return await self._applications.list()

    async def get_application(self, app_id: UUID) -> Application:
        """Devuelve una aplicación por id; 404 si no existe (APP-1)."""
        application = await self._applications.get_by_id(app_id)
        if application is None:
            raise NotFoundError("application not found")
        return application

    async def create_application(self, data: ApplicationCreate) -> Application:
        """Crea una aplicación con api_token_hash None (APP-2, ADR-16)."""
        application = Application(name=data.name, description=data.description)
        created = await self._applications.create(application)
        await self._session.commit()
        await self._session.refresh(created)
        return created

    async def update_application(
        self, app_id: UUID, data: ApplicationUpdate
    ) -> Application:
        """Actualiza name/description/is_active; 404 si no existe (APP-3/APP-7)."""
        application = await self.get_application(app_id)
        if data.name is not None:
            application.name = data.name
        if data.description is not None:
            application.description = data.description
        if data.is_active is not None:
            application.is_active = data.is_active
        await self._applications.update(application)
        await self._session.commit()
        await self._session.refresh(application)
        return application

    async def delete_application(self, app_id: UUID) -> None:
        """Elimina físicamente la aplicación (APP-4).

        404 si no existe; FK RESTRICT de user_session.app_id → ConflictError
        409 con rollback (ADR-07, ADR-10). El router responde 204 en OK.
        """
        await self.get_application(app_id)
        try:
            await self._applications.delete(app_id)
            await self._session.commit()
        except DomainError:
            # ADR-10: la sesión queda limpia para el próximo request.
            await self._session.rollback()
            raise

    # -- Credenciales de ingesta (CRED-1..CRED-5, design §4) ----------------

    async def issue_api_key(self, app_id: UUID) -> IssuedApiKey:
        """Emite una API key nueva y persiste SOLO su hash SHA-256 (CRED-1).

        404 si la aplicación no existe; 409 si ya hay una key activa
        (CRED-3: la rotación es un flujo explícito de dos pasos). El
        plaintext se devuelve una sola vez (show-once).
        """
        application = await self.get_application(app_id)
        if application.api_token_hash is not None:
            raise ConflictError(
                "application already has an active api key",
                code="key_exists",
            )
        api_key = generate_api_key(prefix=get_settings().api_key_prefix)
        application.api_token_hash = hash_api_key(api_key)
        await self._applications.update(application)
        await self._session.commit()
        await self._session.refresh(application)
        return IssuedApiKey(api_key=api_key, hint=api_key[-4:])

    async def revoke_api_key(self, app_id: UUID) -> None:
        """Revoca la key de forma inmediata y fail-closed (CRED-4).

        404 si la aplicación no existe; idempotente: sin key activa no hay
        nada que hacer (204 igual).
        """
        application = await self.get_application(app_id)
        if application.api_token_hash is None:
            return
        application.api_token_hash = None
        await self._applications.update(application)
        await self._session.commit()

    async def authenticate_api_key(self, raw_key: str) -> Application:
        """Autentica un header X-API-Key → Application (IAUTH-1..3, ADR-19).

        Timing-safe: gate de prefijo `ilp_` → lookup indexado por hash
        SHA-256 → `hmac.compare_digest`. Hash/formato inválido → 401
        indistinguible (fail-closed, incluye key revocada); key válida de
        aplicación inactiva → 403 app_inactive (APP-8).
        """
        if not raw_key.startswith(DEFAULT_KEY_PREFIX):
            raise AuthenticationError("invalid api key", code="invalid_api_key")
        digest = hash_api_key(raw_key)
        application = await self._applications.get_by_api_token_hash(digest)
        if application is None:
            raise AuthenticationError("invalid api key", code="invalid_api_key")
        if not hmac.compare_digest(digest, application.api_token_hash or ""):
            raise AuthenticationError("invalid api key", code="invalid_api_key")
        if not application.is_active:
            raise AuthorizationError(
                "application is inactive", code="app_inactive"
            )
        return application
