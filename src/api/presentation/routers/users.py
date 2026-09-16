"""Rutas de usuarios — design §4.5 (C3).

GET /users (Admin+Researcher, USR-1), POST /users (Admin, 201, USR-3),
GET /users/{user_id} (Admin+Researcher, USR-2), PUT /users/{user_id}
(Admin, 200, USR-5). `require_role` aplica ADR-04: Admin muta, Researcher
solo lee. `response_model` de solo lectura garantiza SEC-4 (sin
password_hash en respuestas).
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.domain.entities.lab_user import LabUser
from api.domain.services.user_service import UserService
from api.infrastructure.db.repositories.sqlalchemy_user_repository import (
    SQLAlchemyUserRepository,
)
from api.infrastructure.db.session import get_session
from api.presentation.dependencies import require_role
from api.presentation.schemas.user import UserCreate, UserRead, UserUpdate

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=list[UserRead], status_code=status.HTTP_200_OK)
async def list_users(
    _current_user: Annotated[LabUser, Depends(require_role("Admin", "Researcher"))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[LabUser]:
    """Lista usuarios sin exponer password_hash (USR-1)."""
    service = UserService(session, SQLAlchemyUserRepository(session))
    return await service.list_users()


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate,
    _current_user: Annotated[LabUser, Depends(require_role("Admin"))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> LabUser:
    """Crea un usuario (solo Admin, USR-3); 409 en email duplicado/rol inválido."""
    service = UserService(session, SQLAlchemyUserRepository(session))
    return await service.create_user(payload)


@router.get("/{user_id}", response_model=UserRead, status_code=status.HTTP_200_OK)
async def get_user(
    user_id: UUID,
    _current_user: Annotated[LabUser, Depends(require_role("Admin", "Researcher"))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> LabUser:
    """Devuelve el detalle de un usuario (USR-2); 404 si no existe."""
    service = UserService(session, SQLAlchemyUserRepository(session))
    return await service.get_user(user_id)


@router.put("/{user_id}", response_model=UserRead, status_code=status.HTTP_200_OK)
async def update_user(
    user_id: UUID,
    payload: UserUpdate,
    _current_user: Annotated[LabUser, Depends(require_role("Admin"))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> LabUser:
    """Actualiza un usuario (solo Admin, USR-5); re-hash solo si envía password."""
    service = UserService(session, SQLAlchemyUserRepository(session))
    return await service.update_user(user_id, payload)
