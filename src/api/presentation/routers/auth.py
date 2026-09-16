"""Rutas de autenticación — design §4.5 (B4).

POST /auth/login: público (AUTH-1). POST /auth/logout: requiere bearer,
204 stateless (AUTH-4). Los paths protegidos de users/applications llegan
en PR-C/PR-D con la misma dependencia get_current_user.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.domain.entities.lab_user import LabUser
from api.domain.services.auth_service import AuthService
from api.infrastructure.db.repositories.sqlalchemy_user_repository import (
    SQLAlchemyUserRepository,
)
from api.infrastructure.db.session import get_session
from api.presentation.dependencies import get_current_user
from api.presentation.schemas.auth import AuthResponse, LoginRequest

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/login",
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK,
)
async def login(
    payload: LoginRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AuthResponse:
    """Autentica email+password y emite el JWT (público, AUTH-1)."""
    service = AuthService(session, SQLAlchemyUserRepository(session))
    return await service.login(payload.email, payload.password)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    _current_user: Annotated[LabUser, Depends(get_current_user)],
) -> None:
    """Cierra la sesión del cliente; el servidor no persiste estado (AUTH-4)."""
    return None
