"""Contrato del repositorio de usuarios (capa de dominio)."""
# pylint: disable=unnecessary-ellipsis

from typing import Protocol
from uuid import UUID

from api.domain.entities.lab_user import LabUser
from api.domain.entities.user_role import UserRole


class UserRepository(Protocol):
    """Operaciones de persistencia de usuarios y roles.

    Las implementaciones reciben una AsyncSession; las mutaciones NO
    commitean (ADR-10): el servicio coordina commit/rollback.
    """

    async def get_by_id(self, user_id: UUID) -> LabUser | None:
        """Devuelve el usuario por id, o None si no existe."""
        ...

    async def get_by_email(self, email: str) -> LabUser | None:
        """Devuelve el usuario por email (único vía idx_lab_user_email)."""
        ...

    async def list(self) -> list[LabUser]:
        """Lista todos los usuarios."""
        ...

    async def create(self, user: LabUser) -> LabUser:
        """Persiste un usuario nuevo; IntegrityError → ConflictError."""
        ...

    async def update(self, user: LabUser) -> None:
        """Persiste cambios de un usuario existente."""
        ...

    async def get_role_by_id(self, role_id: int) -> UserRole | None:
        """Devuelve el rol por id (ADR-14), o None si no existe."""
        ...
