"""Rutas de aplicaciones — design §4.5 (D3).

GET /applications y GET /applications/{id} (Admin+Researcher, APP-1),
POST /applications (Admin, 201, APP-2), PUT /applications/{id} (Admin,
APP-3), DELETE /applications/{id} (Admin; 204 | 404 | 409, APP-4),
POST/DELETE /applications/{id}/api-key (Admin; CRED-1..CRED-4).
`require_role` aplica ADR-04: Admin muta, Researcher solo lee.
`response_model` de solo lectura garantiza ADR-16 (sin api_token_hash).
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.domain.entities.application import Application
from api.domain.entities.lab_user import LabUser
from api.domain.services.application_service import (
    ApplicationService,
    IssuedApiKey,
)
from api.infrastructure.db.repositories.sqlalchemy_application_repository import (
    SQLAlchemyApplicationRepository,
)
from api.infrastructure.db.session import get_session
from api.presentation.dependencies import require_role
from api.presentation.schemas.application import (
    ApiKeyResponse,
    ApplicationCreate,
    ApplicationRead,
    ApplicationUpdate,
)

router = APIRouter(prefix="/applications", tags=["Applications"])


@router.get(
    "", response_model=list[ApplicationRead], status_code=status.HTTP_200_OK
)
async def list_applications(
    _current_user: Annotated[
        LabUser, Depends(require_role("Admin", "Researcher"))
    ],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[Application]:
    """Lista aplicaciones (APP-1)."""
    service = ApplicationService(session, SQLAlchemyApplicationRepository(session))
    return await service.list_applications()


@router.post(
    "", response_model=ApplicationRead, status_code=status.HTTP_201_CREATED
)
async def create_application(
    payload: ApplicationCreate,
    _current_user: Annotated[LabUser, Depends(require_role("Admin"))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> Application:
    """Crea una aplicación (solo Admin, APP-2); 422 si name vacío (APP-6)."""
    service = ApplicationService(session, SQLAlchemyApplicationRepository(session))
    return await service.create_application(payload)


@router.get(
    "/{application_id}",
    response_model=ApplicationRead,
    status_code=status.HTTP_200_OK,
)
async def get_application(
    application_id: UUID,
    _current_user: Annotated[
        LabUser, Depends(require_role("Admin", "Researcher"))
    ],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> Application:
    """Devuelve el detalle de una aplicación (APP-1); 404 si no existe."""
    service = ApplicationService(session, SQLAlchemyApplicationRepository(session))
    return await service.get_application(application_id)


@router.put(
    "/{application_id}",
    response_model=ApplicationRead,
    status_code=status.HTTP_200_OK,
)
async def update_application(
    application_id: UUID,
    payload: ApplicationUpdate,
    _current_user: Annotated[LabUser, Depends(require_role("Admin"))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> Application:
    """Actualiza una aplicación (solo Admin, APP-3); 404 si no existe."""
    service = ApplicationService(session, SQLAlchemyApplicationRepository(session))
    return await service.update_application(application_id, payload)


@router.delete(
    "/{application_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_application(
    application_id: UUID,
    _current_user: Annotated[LabUser, Depends(require_role("Admin"))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    """Elimina una aplicación (solo Admin, APP-4): 204 | 404 | 409."""
    service = ApplicationService(session, SQLAlchemyApplicationRepository(session))
    await service.delete_application(application_id)
    return None


@router.post(
    "/{application_id}/api-key",
    response_model=ApiKeyResponse,
    status_code=status.HTTP_201_CREATED,
)
async def issue_api_key(
    application_id: UUID,
    _current_user: Annotated[LabUser, Depends(require_role("Admin"))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> IssuedApiKey:
    """Emite una API key show-once (solo Admin): 201 | 404 | 409 (CRED-1..3)."""
    service = ApplicationService(session, SQLAlchemyApplicationRepository(session))
    return await service.issue_api_key(application_id)


@router.delete(
    "/{application_id}/api-key", status_code=status.HTTP_204_NO_CONTENT
)
async def revoke_api_key(
    application_id: UUID,
    _current_user: Annotated[LabUser, Depends(require_role("Admin"))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    """Revoca la key de forma inmediata y fail-closed (solo Admin, CRED-4):
    204 idempotente | 404."""
    service = ApplicationService(session, SQLAlchemyApplicationRepository(session))
    await service.revoke_api_key(application_id)
    return None
