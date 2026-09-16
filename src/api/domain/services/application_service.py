"""Caso de uso de aplicaciones: list/get/create/update/delete (design §4.4, D2).

ADR-10 (el servicio commitea y hace rollback ante DomainError), ADR-07
(delete físico; FK RESTRICT de user_session.app_id → ConflictError 409 con
rollback) y APP-1..APP-4 (404 en get/update/delete de inexistente;
api_token_hash queda None en create — columna dormida, ADR-16).
"""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from api.domain.entities.application import Application
from api.domain.exceptions import DomainError, NotFoundError
from api.domain.repositories.application_repository import ApplicationRepository
from api.presentation.schemas.application import ApplicationCreate, ApplicationUpdate


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
        """Actualiza name/description; 404 si no existe (APP-3)."""
        application = await self.get_application(app_id)
        if data.name is not None:
            application.name = data.name
        if data.description is not None:
            application.description = data.description
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
