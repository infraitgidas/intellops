"""Caso de uso de usuarios: list/get/create/update (design §4.4, C2).

ADR-10 (el servicio commitea y hace rollback ante DomainError), ADR-14
(validación de rol vía `get_role_by_id` → 409 si no existe), USR-1..USR-5
(404 en get/update de inexistente, argon2 en create y solo en update si se
envía password, IntegrityError de email → 409) y SEC-4 (password_hash jamás
sale del servicio: los schemas de salida no llevan el campo).
"""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from api.domain.entities.lab_user import LabUser
from api.domain.exceptions import ConflictError, DomainError, NotFoundError
from api.domain.repositories.user_repository import UserRepository
from api.infrastructure.security.password import PasswordHasher
from api.presentation.schemas.user import UserCreate, UserUpdate


class UserService:
    """Operaciones de usuarios sobre el UserRepository (sin estado propio)."""

    def __init__(self, session: AsyncSession, user_repository: UserRepository) -> None:
        self._session = session
        self._users = user_repository
        self._hasher = PasswordHasher()

    async def list_users(self) -> list[LabUser]:
        """Lista todos los usuarios (USR-1)."""
        return await self._users.list()

    async def get_user(self, user_id: UUID) -> LabUser:
        """Devuelve un usuario por id; 404 si no existe (USR-2)."""
        user = await self._users.get_by_id(user_id)
        if user is None:
            raise NotFoundError("user not found")
        return user

    async def create_user(self, data: UserCreate) -> LabUser:
        """Crea un usuario: rol existente (409 si no), argon2, commit (USR-3/4)."""
        try:
            role = await self._users.get_role_by_id(data.role_id)
            if role is None:
                raise ConflictError("role does not exist")
            user = LabUser(
                name=data.name,
                email=data.email,
                role_id=role.role_id,
                password_hash=self._hasher.hash_password(data.password),
            )
            created = await self._users.create(user)
            await self._session.commit()
            await self._session.refresh(created)
            return created
        except DomainError:
            # ADR-10: la sesión queda limpia para el próximo request.
            await self._session.rollback()
            raise

    async def update_user(self, user_id: UUID, data: UserUpdate) -> LabUser:
        """Actualiza un usuario; 404 si no existe; re-hash solo si password (USR-5).

        El email duplicado (UNIQUE idx_lab_user_email) y el role_id inexistente
        se traducen a ConflictError 409 (USR-4).
        """
        try:
            user = await self.get_user(user_id)
            if data.role_id is not None:
                role = await self._users.get_role_by_id(data.role_id)
                if role is None:
                    raise ConflictError("role does not exist")
                user.role_id = role.role_id
            if data.name is not None:
                user.name = data.name
            if data.email is not None:
                user.email = data.email
            if data.is_active is not None:
                user.is_active = data.is_active
            if data.password is not None:
                user.password_hash = self._hasher.hash_password(data.password)
            await self._users.update(user)
            await self._session.commit()
            await self._session.refresh(user)
            return user
        except DomainError:
            await self._session.rollback()
            raise
