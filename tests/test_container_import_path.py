"""Tests del path de import del contenedor (CRITICAL-1).

El runtime real carga la app con `uvicorn api.main:app` (PYTHONPATH=/app/src).
La dualidad `src.api.*` vs `api.*` registraba el handler de DomainError para
una clase distinta a la que levantan dependencies/routers, y todos los errores
de dominio (401/403/404/409) se convertían en 500. Estos tests anclan el path
canónico `api.main` y verifican el contrato de error de extremo a extremo.
"""

from pathlib import Path
from uuid import uuid4

from sqlalchemy import select

from api.domain.entities.user_role import UserRole
from api.domain.exceptions import (
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    DomainError,
    NotFoundError,
)
from api.main import app


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _researcher_role_id(db_session) -> int:
    """role_id del catálogo Researcher (seed 0001, mapeo por nombre)."""
    return (
        await db_session.execute(
            select(UserRole.role_id).where(UserRole.name == "Researcher")
        )
    ).scalar_one()


# -- Identidad de clases y handler ------------------------------------------

def test_container_import_path_registers_domain_error_handler():
    """Importar la app como `api.main` DEBE registrar el handler de DomainError.

    El handler debe estar registrado para la MISMA clase `DomainError` que
    levantan dependencies/routers (import absoluto `api.domain.exceptions`),
    de modo que 401/403/404/409 se traduzcan y no caigan en un 500 genérico.
    """
    assert app.exception_handlers.get(DomainError) is not None
    assert issubclass(AuthenticationError, DomainError)
    assert issubclass(AuthorizationError, DomainError)
    assert issubclass(NotFoundError, DomainError)
    assert issubclass(ConflictError, DomainError)


# -- Contrato HTTP de errores de dominio -------------------------------------

async def test_get_users_without_token_returns_401(client):
    """GET /users sin bearer DEBE responder 401 con body ErrorResponse, no 500."""
    resp = await client.get("/users")
    assert resp.status_code == 401
    body = resp.json()
    assert body["error"]["code"] == "invalid_token"
    assert body["error"]["message"]


async def test_get_unknown_user_returns_404(client, make_admin):
    """GET /users/{uuid inexistente} con Admin DEBE responder 404, no 500."""
    _, token = await make_admin()
    resp = await client.get(f"/users/{uuid4()}", headers=_auth(token))
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "not_found"


async def test_create_duplicate_email_returns_409(client, db_session, make_admin):
    """POST /users con email ya existente DEBE responder 409, no 500."""
    _, token = await make_admin()
    role_id = await _researcher_role_id(db_session)
    payload = {
        "name": "Dup Path",
        "email": "dup-path@intellops.local",
        "password": "password-123",
        "role_id": role_id,
    }
    first = await client.post("/users", headers=_auth(token), json=payload)
    assert first.status_code == 201
    second = await client.post("/users", headers=_auth(token), json=payload)
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "conflict"


async def test_researcher_create_user_returns_403(client, db_session, make_researcher):
    """POST /users con token de Researcher DEBE responder 403, no 500."""
    _, token = await make_researcher()
    role_id = await _researcher_role_id(db_session)
    resp = await client.post(
        "/users",
        headers=_auth(token),
        json={
            "name": "X",
            "email": "x-path@intellops.local",
            "password": "password-123",
            "role_id": role_id,
        },
    )
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "forbidden"


# -- Anclaje estático del path de import del contenedor ----------------------

def test_dockerfile_cmd_uses_canonical_api_main():
    """El CMD del Dockerfile DEBE servir `uvicorn api.main:app`, no `src.api.main:app`."""
    dockerfile = Path(__file__).resolve().parents[1] / "Dockerfile"
    content = dockerfile.read_text(encoding="utf-8")
    cmd_lines = [line for line in content.splitlines() if line.strip().startswith("CMD")]
    assert cmd_lines, "El Dockerfile DEBE declarar un CMD"
    cmd = "\n".join(cmd_lines)
    assert "uvicorn api.main:app" in cmd
    assert "src.api.main:app" not in content
