"""Contrato del repositorio de aplicaciones (capa de dominio)."""
# pylint: disable=unnecessary-ellipsis

from typing import Protocol
from uuid import UUID

from api.domain.entities.application import Application


class ApplicationRepository(Protocol):
    """Operaciones de persistencia de aplicaciones.

    Las implementaciones reciben una AsyncSession; las mutaciones NO
    commitean (ADR-10): el servicio coordina commit/rollback.
    """

    async def get_by_id(self, app_id: UUID) -> Application | None:
        """Devuelve la aplicación por id, o None si no existe."""
        ...

    async def list(self) -> list[Application]:
        """Lista todas las aplicaciones."""
        ...

    async def create(self, application: Application) -> Application:
        """Persiste una aplicación nueva."""
        ...

    async def update(self, application: Application) -> None:
        """Persiste cambios de una aplicación existente."""
        ...

    async def delete(self, app_id: UUID) -> None:
        """Elimina físicamente una aplicación.

        FK RESTRICT de user_session.app_id → IntegrityError → ConflictError.
        """
        ...

    async def get_by_api_token_hash(self, api_token_hash: str) -> Application | None:
        """Busca por hash de API key (CRED-1, IAUTH-3).

        Lookup indexado por el índice único parcial de 0002; devuelve la
        aplicación cuya key coincide, o None. El servicio compara con
        `hmac.compare_digest` y valida `is_active` (ADR-19).
        """
        ...
