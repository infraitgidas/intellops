"""Tests del PR-C (core-users): escenarios USR-1..USR-7 (spec §2, design §7).

Cubre C1 (schemas user: UserCreate/UserUpdate/UserRead), C2 (user_service:
list/get/create/update con argon2, 404 y ConflictError) y C3 (router /users
+ wiring en main.py). SEC-4: `password_hash` nunca aparece en respuestas.
"""

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError
from sqlalchemy import select

from api.domain.entities.lab_user import LabUser
from api.domain.entities.user_role import UserRole
from api.infrastructure.security.password import PasswordHasher
from api.presentation.schemas.user import UserCreate, UserRead, UserUpdate


async def _researcher_role_id(db_session) -> int:
    """role_id del catálogo Researcher (seed 0001, mapeo por nombre)."""
    return (
        await db_session.execute(
            select(UserRole.role_id).where(UserRole.name == "Researcher")
        )
    ).scalar_one()


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


# -- C1: schemas user -------------------------------------------------------

def test_user_create_rejects_short_password():
    """password < 8 DEBE fallar la validación del schema (USR-7)."""
    with pytest.raises(ValidationError):
        UserCreate(name="X", email="x@intellops.local", password="short", role_id=1)


def test_user_create_rejects_invalid_email():
    """Email malformado DEBE fallar la validación del schema (USR-7)."""
    with pytest.raises(ValidationError):
        UserCreate(
            name="X", email="not-an-email", password="password-123", role_id=1
        )


def test_user_create_accepts_local_reserved_domain():
    """LabEmail acepta dominios .local (seed 0002 y fixtures dev)."""
    user = UserCreate(
        name="X", email="admin@intellops.local", password="password-123", role_id=1
    )
    assert user.email == "admin@intellops.local"


def test_user_update_all_fields_optional():
    """UserUpdate DEBE permitir payload vacío (PUT parcial, USR-5)."""
    assert UserUpdate().model_dump(exclude_unset=True) == {}


def test_user_read_excludes_password_hash():
    """UserRead DEBE serializar sin password_hash (SEC-4)."""
    read = UserRead(
        user_id=uuid4(),
        name="X",
        email="x@intellops.local",
        role_id=1,
        is_active=True,
        last_login=None,
        created_at=datetime.now(timezone.utc),
    )
    assert "password_hash" not in read.model_dump()


# -- USR-1: listar usuarios sin exponer hashes ------------------------------

async def test_list_users_never_exposes_password_hash(client, db_session, make_admin):
    """GET /users con Admin → 200; ningún item expone password_hash (USR-1)."""
    _, token = await make_admin(email="list-admin@intellops.local")
    role_id = await _researcher_role_id(db_session)
    # segundo usuario persistido: la lista no puede quedar vacía
    db_session.add(
        LabUser(
            user_id=uuid4(),
            name="Second",
            email="second-list@intellops.local",
            role_id=role_id,
            is_active=True,
            password_hash=PasswordHasher().hash_password("password-123"),
        )
    )
    await db_session.commit()

    resp = await client.get("/users", headers=_auth(token))
    assert resp.status_code == 200
    items = resp.json()
    assert isinstance(items, list)
    assert len(items) >= 2
    for item in items:
        assert "password_hash" not in item
        assert item["name"]
        assert item["email"]


async def test_researcher_can_list_users(client, make_researcher):
    """Researcher también DEBE listar (USR-1: Admin y Researcher)."""
    _, token = await make_researcher()
    resp = await client.get("/users", headers=_auth(token))
    assert resp.status_code == 200
    items = resp.json()
    assert isinstance(items, list)
    assert len(items) == 1
    assert items[0]["role_id"] >= 1


# -- USR-2: detalle de usuario ----------------------------------------------

async def test_get_user_detail_without_password_hash(client, make_admin):
    """GET /users/{id} → 200 con detalle y sin password_hash (USR-2)."""
    user, token = await make_admin(email="detail@intellops.local")
    resp = await client.get(f"/users/{user.user_id}", headers=_auth(token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["user_id"] == str(user.user_id)
    assert body["name"] == user.name
    assert body["email"] == "detail@intellops.local"
    assert "password_hash" not in body


async def test_get_user_not_found_404(client, make_admin):
    """GET /users/{id} con UUID inexistente → 404 (USR-2)."""
    _, token = await make_admin()
    resp = await client.get(f"/users/{uuid4()}", headers=_auth(token))
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "not_found"


# -- USR-3: crear usuario como Admin ----------------------------------------

async def test_create_user_201_argon2_verified_and_no_hash(
    client, db_session, make_admin
):
    """POST /users Admin → 201 is_active=true; hash argon2 verifica (USR-3)."""
    _, token = await make_admin()
    role_id = await _researcher_role_id(db_session)
    resp = await client.post(
        "/users",
        headers=_auth(token),
        json={
            "name": "Nuevo Usuario",
            "email": "nuevo@intellops.local",
            "password": "password-123",
            "role_id": role_id,
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Nuevo Usuario"
    assert body["email"] == "nuevo@intellops.local"
    assert body["role_id"] == role_id
    assert body["is_active"] is True
    assert "password_hash" not in body

    user = (
        await db_session.execute(
            select(LabUser).where(LabUser.email == "nuevo@intellops.local")
        )
    ).scalar_one()
    assert PasswordHasher().verify_password("password-123", user.password_hash)


# -- USR-4: email duplicado y role_id inexistente → 409 ---------------------

async def test_create_user_duplicate_email_409(client, db_session, make_admin):
    """POST /users con email ya registrado → 409 (USR-4)."""
    _, token = await make_admin()
    role_id = await _researcher_role_id(db_session)
    payload = {
        "name": "Dup",
        "email": "dup@intellops.local",
        "password": "password-123",
        "role_id": role_id,
    }
    first = await client.post("/users", headers=_auth(token), json=payload)
    assert first.status_code == 201
    second = await client.post("/users", headers=_auth(token), json=payload)
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "conflict"


async def test_create_user_nonexistent_role_409(client, make_admin):
    """POST /users con role_id sin fila → 409 (USR-4, ADR-14)."""
    _, token = await make_admin()
    resp = await client.post(
        "/users",
        headers=_auth(token),
        json={
            "name": "Ghost Role",
            "email": "role-ghost@intellops.local",
            "password": "password-123",
            "role_id": 42,  # dentro de SMALLINT, sin fila en user_role
        },
    )
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "conflict"


# -- USR-6: Researcher NO muta ----------------------------------------------

async def test_researcher_cannot_create_user_403(client, db_session, make_researcher):
    """POST /users con bearer de Researcher → 403 (USR-6)."""
    _, token = await make_researcher()
    role_id = await _researcher_role_id(db_session)
    resp = await client.post(
        "/users",
        headers=_auth(token),
        json={
            "name": "X",
            "email": "x@intellops.local",
            "password": "password-123",
            "role_id": role_id,
        },
    )
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "forbidden"


async def test_researcher_cannot_update_user_403(client, make_admin, make_researcher):
    """PUT /users/{id} con bearer de Researcher → 403 (USR-6)."""
    target, _ = await make_admin(email="target@intellops.local")
    _, token = await make_researcher()
    resp = await client.put(
        f"/users/{target.user_id}", headers=_auth(token), json={"name": "Hack"}
    )
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "forbidden"


# -- USR-5: PUT /users/{id} -------------------------------------------------

async def test_update_user_without_password_keeps_hash(client, db_session, make_admin):
    """PUT sin password → 200 y el hash previo permanece intacto (USR-5)."""
    user, token = await make_admin(
        email="keep@intellops.local", password="original-password-123"
    )
    await db_session.refresh(user)
    original_hash = user.password_hash
    role_id = await _researcher_role_id(db_session)

    resp = await client.put(
        f"/users/{user.user_id}",
        headers=_auth(token),
        json={"name": "Renombrado", "role_id": role_id},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["name"] == "Renombrado"
    assert body["role_id"] == role_id

    await db_session.refresh(user)
    assert user.password_hash == original_hash
    assert PasswordHasher().verify_password(
        "original-password-123", user.password_hash
    )


async def test_update_user_with_password_rehashes(client, db_session, make_admin):
    """PUT con password → 200 y el hash nuevo reemplaza al previo (USR-5)."""
    user, token = await make_admin(
        email="rehash@intellops.local", password="old-password-123"
    )
    await db_session.refresh(user)
    old_hash = user.password_hash

    resp = await client.put(
        f"/users/{user.user_id}",
        headers=_auth(token),
        json={"password": "new-password-456"},
    )
    assert resp.status_code == 200
    assert "password_hash" not in resp.json()

    await db_session.refresh(user)
    assert user.password_hash != old_hash
    assert PasswordHasher().verify_password("new-password-456", user.password_hash)
    assert not PasswordHasher().verify_password("old-password-123", user.password_hash)


async def test_update_user_not_found_404(client, make_admin):
    """PUT /users/{id} con UUID inexistente → 404 (USR-5)."""
    _, token = await make_admin()
    resp = await client.put(
        f"/users/{uuid4()}", headers=_auth(token), json={"name": "X"}
    )
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "not_found"


async def test_update_user_duplicate_email_409(client, db_session, make_admin):
    """PUT con email de otro usuario → 409 (USR-4)."""
    user, token = await make_admin(email="first@intellops.local")
    await make_admin(email="second@intellops.local")
    resp = await client.put(
        f"/users/{user.user_id}",
        headers=_auth(token),
        json={"email": "second@intellops.local"},
    )
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "conflict"


async def test_update_user_nonexistent_role_409(client, db_session, make_admin):
    """PUT con role_id inexistente → 409 (USR-4, ADR-14)."""
    user, token = await make_admin(email="role-upd@intellops.local")
    resp = await client.put(
        f"/users/{user.user_id}",
        headers=_auth(token),
        json={"role_id": 42},  # dentro de SMALLINT, sin fila en user_role
    )
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "conflict"


# -- USR-7: validaciones de forma → 422 -------------------------------------

async def test_create_user_422_invalid_email(client, make_admin):
    """Email malformado en POST → 422 (USR-7)."""
    _, token = await make_admin()
    resp = await client.post(
        "/users",
        headers=_auth(token),
        json={
            "name": "X",
            "email": "not-an-email",
            "password": "password-123",
            "role_id": 1,
        },
    )
    assert resp.status_code == 422


async def test_create_user_422_short_password(client, make_admin):
    """password < 8 en POST → 422 (USR-7)."""
    _, token = await make_admin()
    resp = await client.post(
        "/users",
        headers=_auth(token),
        json={
            "name": "X",
            "email": "short@intellops.local",
            "password": "abc",
            "role_id": 1,
        },
    )
    assert resp.status_code == 422


async def test_create_user_422_missing_required_fields(client, make_admin):
    """Campos requeridos ausentes en POST → 422 (USR-7)."""
    _, token = await make_admin()
    resp = await client.post(
        "/users", headers=_auth(token), json={"email": "x@intellops.local"}
    )
    assert resp.status_code == 422


async def test_update_user_422_short_password(client, db_session, make_admin):
    """password < 8 en PUT → 422 (USR-7)."""
    user, token = await make_admin(email="upd-short@intellops.local")
    resp = await client.put(
        f"/users/{user.user_id}", headers=_auth(token), json={"password": "abc"}
    )
    assert resp.status_code == 422


# -- AUTH-5 reutilizado sobre /users (C3: wiring de require_role) -----------

async def test_users_path_requires_bearer(client):
    """GET /users sin bearer → 401 invalid_token (AUTH-5 sobre /users)."""
    resp = await client.get("/users")
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "invalid_token"
