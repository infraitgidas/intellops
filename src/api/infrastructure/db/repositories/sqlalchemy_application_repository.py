"""Implementación SQLAlchemy async del ApplicationRepository (sin commit, ADR-10)."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from api.domain.entities.application import Application
from api.domain.exceptions import ConflictError
from api.domain.repositories.application_repository import ApplicationRepository


class SQLAlchemyApplicationRepository(ApplicationRepository):
    """Repositorio de aplicaciones sobre AsyncSession (PostgreSQL, asyncpg)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, app_id: UUID) -> Application | None:
        return await self._session.get(Application, app_id)

    async def list(self) -> list[Application]:
        result = await self._session.execute(
            select(Application).order_by(Application.created_at)
        )
        return list(result.scalars())

    async def create(self, application: Application) -> Application:
        self._session.add(application)
        await self._session.flush()
        return application

    async def update(self, application: Application) -> None:
        await self._session.flush()

    async def delete(self, app_id: UUID) -> None:
        application = await self._session.get(Application, app_id)
        if application is None:
            return
        try:
            await self._session.delete(application)
            await self._session.flush()
        except IntegrityError as exc:
            # FK RESTRICT de user_session.app_id (APP-4, SEC-3).
            raise ConflictError(
                "application has associated sessions and cannot be deleted"
            ) from exc

    async def get_by_api_token_hash(self, api_token_hash: str) -> Application | None:
        result = await self._session.execute(
            select(Application).where(Application.api_token_hash == api_token_hash)
        )
        return result.scalar_one_or_none()
