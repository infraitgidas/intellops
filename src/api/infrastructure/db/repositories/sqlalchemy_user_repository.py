"""Implementación SQLAlchemy async del UserRepository (sin commit, ADR-10)."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.domain.entities.lab_user import LabUser
from api.domain.entities.user_role import UserRole
from api.domain.exceptions import ConflictError
from api.domain.repositories.user_repository import UserRepository


class SQLAlchemyUserRepository(UserRepository):
    """Repositorio de usuarios sobre AsyncSession (PostgreSQL, asyncpg)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: UUID) -> LabUser | None:
        """Devuelve el usuario con su rol eager-load (B3: require_role)."""
        result = await self._session.execute(
            select(LabUser)
            .options(selectinload(LabUser.role))
            .where(LabUser.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> LabUser | None:
        """Devuelve el usuario con su rol eager-load (B2: role denormalizado)."""
        result = await self._session.execute(
            select(LabUser)
            .options(selectinload(LabUser.role))
            .where(LabUser.email == email)
        )
        return result.scalar_one_or_none()

    async def list(self) -> list[LabUser]:
        result = await self._session.execute(select(LabUser).order_by(LabUser.created_at))
        return list(result.scalars())

    async def create(self, user: LabUser) -> LabUser:
        self._session.add(user)
        try:
            await self._session.flush()
        except IntegrityError as exc:
            raise ConflictError("email already registered") from exc
        return user

    async def update(self, user: LabUser) -> None:
        try:
            await self._session.flush()
        except IntegrityError as exc:
            raise ConflictError("email already registered") from exc

    async def get_role_by_id(self, role_id: int) -> UserRole | None:
        return await self._session.get(UserRole, role_id)
