"""Tests de credenciales de ingesta — CRED-1..CRED-5 (spec §1, design §7).

Cubre emisión/rotación/revocación de API key por aplicación:
- Servicio (D2/ADR-10): issue/revoke/authenticate sobre Postgres real.
- Endpoints POST/DELETE /applications/{id}/api-key (solo Admin).
- Show-once (CRED-5), 409 con key activa (CRED-3), DELETE fail-closed
  idempotente (CRED-4), aislamiento A≠B y rotación en dos pasos (4.1).
El guard `require_api_key` se ejercita vía la app de prueba `/_probe`
(conftest; prod sin wiring, IAUTH-5).
"""

import hashlib
from uuid import uuid4

import pytest
from sqlalchemy import text

from api.domain.exceptions import (
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    NotFoundError,
)
from api.domain.services.application_service import ApplicationService
from api.infrastructure.db.repositories.sqlalchemy_application_repository import (
    SQLAlchemyApplicationRepository,
)
from api.infrastructure.security.api_keys import hash_api_key
from api.presentation.schemas.application import ApplicationCreate


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _api_key_header(key: str) -> dict[str, str]:
    return {"X-API-Key": key}


async def _create_app(client, token: str, name: str = "web-app") -> str:
    resp = await client.post(
        "/applications", headers=_auth(token), json={"name": name}
    )
    assert resp.status_code == 201
    return resp.json()["app_id"]


async def _stored_hash(db_session, app_id: str) -> str | None:
    row = await db_session.execute(
        text("SELECT api_token_hash FROM application WHERE app_id = :app_id"),
        {"app_id": app_id},
    )
    return row.scalar_one_or_none()


def _service(db_session) -> ApplicationService:
    return ApplicationService(db_session, SQLAlchemyApplicationRepository(db_session))


# -- CRED-1: emisión show-once (servicio, ADR-10) ----------------------------

async def test_service_issue_api_key_returns_key_and_persists_only_sha256(
    db_session, make_admin
):
    """issue_api_key DEBE devolver key ilp_ + hint y persistir SOLO el hash
    SHA-256 hex (el plaintext nunca se persiste) (CRED-1, SEC-7)."""
    _, token = await make_admin()
    created = await _service(db_session).create_application(
        ApplicationCreate(name="svc-app")
    )
    issued = await _service(db_session).issue_api_key(created.app_id)

    assert issued.api_key.startswith("ilp_")
    assert len(issued.api_key) == 47
    assert issued.hint == issued.api_key[-4:]

    stored = await _stored_hash(db_session, str(created.app_id))
    assert stored == hashlib.sha256(issued.api_key.encode("utf-8")).hexdigest()
    assert issued.api_key not in stored


async def test_service_issue_api_key_404_for_unknown_app(db_session, make_admin):
    """issue_api_key sobre aplicación inexistente DEBE lanzar 404 (CRED-2)."""
    await make_admin()
    with pytest.raises(NotFoundError):
        await _service(db_session).issue_api_key(uuid4())


async def test_service_issue_api_key_409_when_active_key_exists(
    db_session, make_admin
):
    """issue_api_key con key activa DEBE lanzar 409 y NO alterar la key
    vigente (CRED-3: rotación explícita en dos pasos)."""
    _, token = await make_admin()
    service = _service(db_session)
    created = await service.create_application(
        ApplicationCreate(name="svc-409")
    )
    first = await service.issue_api_key(created.app_id)
    before = await _stored_hash(db_session, str(created.app_id))

    with pytest.raises(ConflictError):
        await service.issue_api_key(created.app_id)

    after = await _stored_hash(db_session, str(created.app_id))
    assert before == after
    assert after == hash_api_key(first.api_key)


async def test_service_revoke_api_key_is_idempotent_and_fail_closed(
    db_session, make_admin
):
    """revoke_api_key DEBE borrar el hash y ser idempotente: revocar dos
    veces no falla (CRED-4)."""
    _, token = await make_admin()
    service = _service(db_session)
    created = await service.create_application(
        ApplicationCreate(name="svc-revoke")
    )
    await service.issue_api_key(created.app_id)
    assert await _stored_hash(db_session, str(created.app_id)) is not None

    await service.revoke_api_key(created.app_id)
    assert await _stored_hash(db_session, str(created.app_id)) is None
    await service.revoke_api_key(created.app_id)  # idempotente
    assert await _stored_hash(db_session, str(created.app_id)) is None


async def test_service_revoke_api_key_404_for_unknown_app(db_session, make_admin):
    """revoke_api_key sobre aplicación inexistente DEBE lanzar 404 (CRED-2)."""
    await make_admin()
    with pytest.raises(NotFoundError):
        await _service(db_session).revoke_api_key(uuid4())


# -- IAUTH-3/IAUTH-1: authenticate_api_key (servicio) ------------------------

async def test_service_authenticate_api_key_valid_returns_application(
    db_session, make_admin
):
    """authenticate_api_key DEBE devolver la Application de la key (IAUTH-1)."""
    _, token = await make_admin()
    service = _service(db_session)
    created = await service.create_application(
        ApplicationCreate(name="svc-auth")
    )
    issued = await service.issue_api_key(created.app_id)

    app = await service.authenticate_api_key(issued.api_key)
    assert app.app_id == created.app_id


async def test_service_authenticate_api_key_rejects_no_prefix_format(
    db_session, make_admin
):
    """Formato sin prefijo ilp_ DEBE ser 401 indistinguible (IAUTH-3)."""
    _, token = await make_admin()
    service = _service(db_session)
    created = await service.create_application(
        ApplicationCreate(name="svc-format")
    )
    await service.issue_api_key(created.app_id)

    with pytest.raises(AuthenticationError) as exc:
        await service.authenticate_api_key(
            "random-without-prefix-"
            "123456789012345678901234567890123456789012345"
        )
    assert exc.value.code == "invalid_api_key"


async def test_service_authenticate_api_key_rejects_revoked_key(
    db_session, make_admin
):
    """Key revocada DEBE autenticarse como 401 (fail-closed, IAUTH-1)."""
    _, token = await make_admin()
    service = _service(db_session)
    created = await service.create_application(
        ApplicationCreate(name="svc-revoked")
    )
    issued = await service.issue_api_key(created.app_id)
    await service.revoke_api_key(created.app_id)

    with pytest.raises(AuthenticationError) as exc:
        await service.authenticate_api_key(issued.api_key)
    assert exc.value.code == "invalid_api_key"


async def test_service_authenticate_api_key_inactive_app_403(
    db_session, make_admin
):
    """Key válida de aplicación inactiva DEBE ser 403 app_inactive (APP-8)."""
    _, token = await make_admin()
    service = _service(db_session)
    created = await service.create_application(
        ApplicationCreate(name="svc-inactive")
    )
    issued = await service.issue_api_key(created.app_id)
    created.is_active = False
    await db_session.commit()

    with pytest.raises(AuthorizationError) as exc:
        await service.authenticate_api_key(issued.api_key)
    assert exc.value.code == "app_inactive"


# -- CRED-1: POST /applications/{id}/api-key (endpoint, solo Admin) ---------

async def test_post_api_key_201_show_once(client, db_session, make_admin):
    """POST api-key → 201 {api_key, hint}; el hash SHA-256 se persiste y el
    detalle de la app NO expone key ni hash (CRED-1/CRED-5)."""
    _, token = await make_admin()
    app_id = await _create_app(client, token)

    resp = await client.post(f"/applications/{app_id}/api-key", headers=_auth(token))
    assert resp.status_code == 201
    body = resp.json()
    assert body["api_key"].startswith("ilp_")
    assert len(body["api_key"]) == 47
    assert body["hint"] == body["api_key"][-4:]

    stored = await _stored_hash(db_session, app_id)
    assert stored == hashlib.sha256(body["api_key"].encode("utf-8")).hexdigest()

    detail = await client.get(f"/applications/{app_id}", headers=_auth(token))
    assert detail.status_code == 200
    assert "api_key" not in detail.json()
    assert "api_token_hash" not in detail.json()


async def test_post_api_key_404_unknown_app(client, make_admin):
    """POST api-key sobre aplicación inexistente → 404 ErrorResponse (CRED-2)."""
    _, token = await make_admin()
    resp = await client.post(
        f"/applications/{uuid4()}/api-key", headers=_auth(token)
    )
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "not_found"


async def test_post_api_key_409_with_active_key_previous_key_still_valid(
    client, db_session, make_admin, probe_client
):
    """POST con key activa → 409; la key previa SIGUE validando (CRED-3)."""
    _, token = await make_admin()
    app_id = await _create_app(client, token)
    first = await client.post(
        f"/applications/{app_id}/api-key", headers=_auth(token)
    )
    assert first.status_code == 201
    first_key = first.json()["api_key"]

    again = await client.post(
        f"/applications/{app_id}/api-key", headers=_auth(token)
    )
    assert again.status_code == 409
    assert again.json()["error"]["code"] == "key_exists"

    stored = await _stored_hash(db_session, app_id)
    assert stored == hash_api_key(first_key)

    probe = await probe_client.get("/_probe", headers=_api_key_header(first_key))
    assert probe.status_code == 200
    assert probe.json()["app_id"] == app_id


async def test_delete_api_key_204_fail_closed_idempotent(
    client, db_session, make_admin, probe_client
):
    """DELETE api-key → 204; la key deja de validar al instante; repetir
    DELETE → 204 (idempotente, CRED-4)."""
    _, token = await make_admin()
    app_id = await _create_app(client, token)
    issued = await client.post(
        f"/applications/{app_id}/api-key", headers=_auth(token)
    )
    key = issued.json()["api_key"]

    revoked = await client.delete(
        f"/applications/{app_id}/api-key", headers=_auth(token)
    )
    assert revoked.status_code == 204
    assert revoked.content == b""
    assert await _stored_hash(db_session, app_id) is None

    probe = await probe_client.get("/_probe", headers=_api_key_header(key))
    assert probe.status_code == 401  # fail-closed: indistinguible de inválida

    again = await client.delete(
        f"/applications/{app_id}/api-key", headers=_auth(token)
    )
    assert again.status_code == 204


async def test_delete_api_key_404_unknown_app(client, make_admin):
    """DELETE api-key sobre aplicación inexistente → 404 ErrorResponse (CRED-2)."""
    _, token = await make_admin()
    resp = await client.delete(
        f"/applications/{uuid4()}/api-key", headers=_auth(token)
    )
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "not_found"


async def test_api_key_endpoints_require_admin(client, make_researcher):
    """POST/DELETE api-key con Researcher → 403 forbidden (solo Admin)."""
    _, token = await make_researcher()
    post = await client.post(
        f"/applications/{uuid4()}/api-key", headers=_auth(token)
    )
    assert post.status_code == 403
    assert post.json()["error"]["code"] == "forbidden"

    delete = await client.delete(
        f"/applications/{uuid4()}/api-key", headers=_auth(token)
    )
    assert delete.status_code == 403


# -- CRED-5: show-once — ni key ni hash en listado ni update ---------------

async def test_api_key_never_exposed_in_list_or_update(client, make_admin):
    """GET /applications y PUT /applications/{id} NUNCA exponen key ni hash
    (CRED-5; el hash es dato interno, ADR-16)."""
    _, token = await make_admin()
    app_id = await _create_app(client, token)
    await client.post(f"/applications/{app_id}/api-key", headers=_auth(token))

    listed = await client.get("/applications", headers=_auth(token))
    assert listed.status_code == 200
    for item in listed.json():
        assert "api_key" not in item
        assert "api_token_hash" not in item

    updated = await client.put(
        f"/applications/{app_id}",
        headers=_auth(token),
        json={"description": "after issue"},
    )
    assert updated.status_code == 200
    assert "api_key" not in updated.json()
    assert "api_token_hash" not in updated.json()


# -- Task 4.1: aislamiento A≠B y rotación en dos pasos -----------------------

async def test_isolation_key_of_app_a_authenticates_as_a_never_b(
    client, make_admin, probe_client
):
    """La key de A enviada a un request DEBE autenticar como A, nunca como B
    (binding 1:1 credencial→app; aislamiento entre aplicaciones)."""
    _, token = await make_admin()
    app_a = await _create_app(client, token, name="app-a")
    app_b = await _create_app(client, token, name="app-b")
    key_a = (
        await client.post(f"/applications/{app_a}/api-key", headers=_auth(token))
    ).json()["api_key"]
    key_b = (
        await client.post(f"/applications/{app_b}/api-key", headers=_auth(token))
    ).json()["api_key"]

    with_key_a = await probe_client.get("/_probe", headers=_api_key_header(key_a))
    assert with_key_a.status_code == 200
    assert with_key_a.json()["app_id"] == app_a

    with_key_b = await probe_client.get("/_probe", headers=_api_key_header(key_b))
    assert with_key_b.status_code == 200
    assert with_key_b.json()["app_id"] == app_b


async def test_two_step_rotation_old_key_invalid_new_key_valid(
    client, db_session, make_admin, probe_client
):
    """Rotación explícita en dos pasos: 409 → DELETE 204 → POST 201 con key
    nueva; la key revocada deja de validar de inmediato (CRED-3/CRED-4)."""
    _, token = await make_admin()
    app_id = await _create_app(client, token)
    old_key = (
        await client.post(f"/applications/{app_id}/api-key", headers=_auth(token))
    ).json()["api_key"]

    # La rotación NO es automática: regenerar sobre key activa → 409.
    blocked = await client.post(
        f"/applications/{app_id}/api-key", headers=_auth(token)
    )
    assert blocked.status_code == 409

    await client.delete(f"/applications/{app_id}/api-key", headers=_auth(token))
    new = await client.post(
        f"/applications/{app_id}/api-key", headers=_auth(token)
    )
    assert new.status_code == 201
    new_key = new.json()["api_key"]
    assert new_key != old_key

    old_probe = await probe_client.get("/_probe", headers=_api_key_header(old_key))
    assert old_probe.status_code == 401  # revocada: fail-closed

    new_probe = await probe_client.get("/_probe", headers=_api_key_header(new_key))
    assert new_probe.status_code == 200
    assert new_probe.json()["app_id"] == app_id
