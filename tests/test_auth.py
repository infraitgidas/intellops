"""Tests del PR-B (core-auth): escenarios AUTH-1..AUTH-6 (spec §1, design §7).

Cubre B1 (schemas auth), B2 (auth_service login/logout), B3 (dependencies
get_current_user/require_role, ADR-15) y B4 (router /auth + wiring main.py).
Los paths protegidos disponibles en este slice son los de /auth/logout;
users/applications los ejercitan en PR-C/PR-D con la misma dependencia.
"""

from datetime import datetime, timezone
from uuid import uuid4

import jwt as pyjwt
import pytest
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from api.config import get_settings
from api.domain.entities.lab_user import LabUser
from api.domain.entities.user_role import UserRole
from api.domain.exceptions import AuthorizationError
from api.infrastructure.security.jwt import create_access_token
from api.presentation.dependencies import require_role
from api.presentation.schemas.auth import AuthResponse, LoginRequest

SECRET = "test-secret-key-0123456789abcdef"


# -- B1: schemas auth ------------------------------------------------------

def test_login_request_rejects_invalid_email():
    """Email malformado DEBE fallar la validación del schema (422)."""
    with pytest.raises(ValidationError):
        LoginRequest(email="not-an-email", password="x")


def test_login_request_accepts_local_reserved_domain():
    """El seed 0002 usa .local (admin@intellops.local): DEBE ser aceptado."""
    req = LoginRequest(email="admin@intellops.local", password="x")
    assert req.email == "admin@intellops.local"


def test_auth_response_shape_and_literal_token_type():
    """AuthResponse DEBE fijar token_type="bearer" y expires_in entero."""
    resp = AuthResponse(access_token="tok", token_type="bearer", expires_in=1800)
    assert resp.access_token == "tok"
    assert resp.token_type == "bearer"
    assert resp.expires_in == 1800
    with pytest.raises(ValidationError):
        AuthResponse(access_token="tok", token_type="Bearer", expires_in=1800)


# -- AUTH-1: login exitoso -------------------------------------------------

async def test_login_seed_admin_with_dev_password(client, seed_admin):
    """Seed Admin (admin@intellops.local) loguea con password dev (DATA-3)."""
    settings = get_settings()
    resp = await client.post(
        "/auth/login",
        json={
            "email": "admin@intellops.local",
            "password": settings.admin_bootstrap_password,
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert body["expires_in"] == 1800
    assert body["access_token"]


async def test_login_success_returns_token_claims_and_updates_last_login(
    client, db_session, make_admin
):
    """Login OK → 200 con token + claims + last_login actualizado (AUTH-1)."""
    user, _ = await make_admin(
        email="login-ok@intellops.local", password="correct-password-123"
    )
    resp = await client.post(
        "/auth/login",
        json={"email": "login-ok@intellops.local", "password": "correct-password-123"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert body["expires_in"] == 1800
    assert body["access_token"]

    payload = pyjwt.decode(body["access_token"], get_settings().jwt_secret, algorithms=["HS256"])
    assert payload["sub"] == str(user.user_id)
    assert payload["role"] == "Admin"
    assert payload["iss"] == "intellops-api"
    assert payload["exp"] - payload["iat"] == 1800

    await db_session.refresh(user)
    assert user.last_login is not None
    assert (datetime.now(timezone.utc) - user.last_login).total_seconds() < 30


# -- AUTH-2 / SEC-1: 401 indistinguible ------------------------------------

async def test_login_401_identical_for_unknown_email_and_wrong_password(client, make_admin):
    """Email desconocido y password incorrecta DEBEN dar 401 idéntico (AUTH-2)."""
    await make_admin(email="known@intellops.local", password="right-password-123")
    unknown = await client.post(
        "/auth/login", json={"email": "ghost@intellops.local", "password": "whatever-123"}
    )
    wrong_pw = await client.post(
        "/auth/login", json={"email": "known@intellops.local", "password": "wrong-password-123"}
    )
    assert unknown.status_code == 401
    assert wrong_pw.status_code == 401
    assert unknown.json() == wrong_pw.json()
    assert unknown.json()["error"]["code"] == "invalid_credentials"
    assert unknown.json()["error"]["message"]


async def test_login_user_without_password_hash_returns_401_identical(client, db_session):
    """password_hash NULL (pre-0002) DEBE dar 401 idéntico a credenciales inválidas."""
    role_id = (
        await db_session.execute(select(UserRole.role_id).where(UserRole.name == "Admin"))
    ).scalar_one()
    db_session.add(
        LabUser(
            user_id=uuid4(),
            name="No Hash",
            email="no-hash@intellops.local",
            role_id=role_id,
            is_active=True,
            password_hash=None,
        )
    )
    await db_session.commit()

    resp = await client.post(
        "/auth/login", json={"email": "no-hash@intellops.local", "password": "any-password"}
    )
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "invalid_credentials"

    unknown = await client.post(
        "/auth/login", json={"email": "ghost@intellops.local", "password": "any-password"}
    )
    assert resp.json() == unknown.json()


# -- AUTH-3 / SEC-2: usuario inactivo --------------------------------------

async def test_login_inactive_user_403_and_last_login_unchanged(client, db_session, make_admin):
    """is_active=false → 403 y last_login NO cambia (AUTH-3)."""
    user, _ = await make_admin(
        email="inactive@intellops.local", password="right-password-123"
    )
    frozen = datetime(2024, 1, 1, tzinfo=timezone.utc)
    user.is_active = False
    user.last_login = frozen
    await db_session.commit()

    resp = await client.post(
        "/auth/login", json={"email": "inactive@intellops.local", "password": "right-password-123"}
    )
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "user_inactive"
    assert resp.json()["error"]["message"]

    await db_session.refresh(user)
    assert user.last_login == frozen


# -- AUTH-4: logout stateless ----------------------------------------------

async def test_logout_returns_204_stateless(client, make_admin):
    """Logout con bearer válido → 204 sin cuerpo y sin estado (AUTH-4)."""
    _, token = await make_admin()
    headers = {"Authorization": f"Bearer {token}"}
    resp = await client.post("/auth/logout", headers=headers)
    assert resp.status_code == 204
    assert resp.content == b""
    # Stateless: el mismo token sigue siendo aceptado por otro request.
    again = await client.post("/auth/logout", headers=headers)
    assert again.status_code == 204


# -- AUTH-5 / B3: token inválido, expirado, ausente, usuario borrado --------

async def test_logout_requires_bearer(client):
    """Bearer ausente en path protegido → 401 invalid_token (AUTH-5)."""
    resp = await client.post("/auth/logout")
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "invalid_token"


async def test_logout_rejects_invalid_signature_token(client):
    """Firma inválida → 401 invalid_token (AUTH-5)."""
    token = create_access_token(uuid4(), "Admin", secret="y" * 32)
    resp = await client.post("/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "invalid_token"


async def test_logout_rejects_expired_token(client):
    """Token expirado → 401 invalid_token (AUTH-5)."""
    token = create_access_token(
        uuid4(), "Admin", secret=get_settings().jwt_secret, expire_minutes=-1
    )
    resp = await client.post("/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "invalid_token"


async def test_logout_rejects_malformed_bearer(client):
    """Bearer malformado (no JWT) → 401 invalid_token (AUTH-5)."""
    resp = await client.post("/auth/logout", headers={"Authorization": "Bearer not-a-jwt"})
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "invalid_token"


async def test_protected_path_rejects_token_of_deleted_user(client, db_session, make_admin):
    """get_by_id inexistente → 401 invalid_token (B3)."""
    user, token = await make_admin(email="delete-me@intellops.local")
    await db_session.delete(user)
    await db_session.commit()
    resp = await client.post("/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "invalid_token"


async def test_protected_path_returns_403_for_inactive_user(client, db_session, make_admin):
    """is_active=false con token válido → 403 user_inactive (ADR-15)."""
    user, token = await make_admin(email="inactive-token@intellops.local")
    user.is_active = False
    await db_session.commit()
    resp = await client.post("/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "user_inactive"


# -- B3: require_role (factory; primer consumidor real en PR-C) -------------

async def test_require_role_grants_matching_role_and_forbids_others(db_session, make_admin):
    """require_role DEBE permitir el rol esperado y prohibir el resto (403 forbidden)."""
    user, _ = await make_admin()
    admin = (
        await db_session.execute(
            select(LabUser)
            .options(selectinload(LabUser.role))
            .where(LabUser.user_id == user.user_id)
        )
    ).scalar_one()

    checker = require_role("Admin")
    assert await checker(admin) is admin

    forbidden = require_role("Researcher")
    with pytest.raises(AuthorizationError) as exc_info:
        await forbidden(admin)
    assert exc_info.value.code == "forbidden"
