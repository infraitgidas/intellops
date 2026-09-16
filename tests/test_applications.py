"""Tests del PR-D (core-applications): escenarios APP-1..APP-6 (spec §3, design §7).

Cubre D1 (schemas application: Create/Update/Read con api_token_hash null, ADR-16),
D2 (application_service: list/get/create/update/delete con 404 y 409+rollback por
FK RESTRICT de user_session) y D3 (router /applications + wiring en main.py).
ADR-16: `api_token_hash` está presente en las respuestas y SIEMPRE es null en S2-01.
"""

from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError
from sqlalchemy import text

from api.presentation.schemas.application import (
    ApplicationCreate,
    ApplicationRead,
    ApplicationUpdate,
)


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


# -- D1: schemas application ------------------------------------------------

def test_application_create_rejects_empty_name():
    """name vacío en POST DEBE fallar la validación del schema (APP-6)."""
    with pytest.raises(ValidationError):
        ApplicationCreate(name="")


def test_application_update_rejects_empty_name():
    """name vacío en PUT DEBE fallar la validación del schema (APP-6)."""
    with pytest.raises(ValidationError):
        ApplicationUpdate(name="")


def test_application_create_description_optional():
    """description es opcional en el payload de creación (APP-2)."""
    app = ApplicationCreate(name="web-app")
    assert app.name == "web-app"
    assert app.description is None


def test_application_read_exposes_api_token_hash_null():
    """ApplicationRead DEBE incluir api_token_hash con valor null (ADR-16)."""
    read = ApplicationRead(
        app_id=uuid4(),
        name="web-app",
        description=None,
        api_token_hash=None,
        created_at=datetime.now(timezone.utc),
    )
    dumped = read.model_dump()
    assert "api_token_hash" in dumped
    assert dumped["api_token_hash"] is None


# -- APP-2: crear aplicación como Admin -------------------------------------

async def test_create_application_201_api_token_hash_null(client, make_admin):
    """POST /applications con Admin → 201 y api_token_hash null (APP-2, ADR-16)."""
    _, token = await make_admin()
    resp = await client.post(
        "/applications", headers=_auth(token), json={"name": "web-app"}
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "web-app"
    assert body["description"] is None
    assert body["api_token_hash"] is None
    assert body["app_id"]
    assert body["created_at"]


# -- APP-1: listar y detallar aplicaciones ----------------------------------

async def test_list_applications_200(client, make_admin):
    """GET /applications con Admin → 200 con la aplicación creada (APP-1)."""
    _, token = await make_admin()
    created = await client.post(
        "/applications", headers=_auth(token), json={"name": "web-app"}
    )
    assert created.status_code == 201

    resp = await client.get("/applications", headers=_auth(token))
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) == 1
    assert items[0]["name"] == "web-app"
    assert items[0]["api_token_hash"] is None


async def test_researcher_can_list_applications(client, make_admin, make_researcher):
    """GET /applications con Researcher también → 200 (APP-1: Admin y Researcher)."""
    _, admin_token = await make_admin()
    created = await client.post(
        "/applications", headers=_auth(admin_token), json={"name": "web-app"}
    )
    assert created.status_code == 201
    _, token = await make_researcher()

    resp = await client.get("/applications", headers=_auth(token))
    assert resp.status_code == 200
    assert len(resp.json()) == 1


async def test_get_application_detail_200(client, make_admin):
    """GET /applications/{id} → 200 con detalle completo (APP-1)."""
    _, token = await make_admin()
    created = await client.post(
        "/applications",
        headers=_auth(token),
        json={"name": "api-gw", "description": "API Gateway"},
    )
    app_id = created.json()["app_id"]

    resp = await client.get(f"/applications/{app_id}", headers=_auth(token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["app_id"] == app_id
    assert body["name"] == "api-gw"
    assert body["description"] == "API Gateway"
    assert body["api_token_hash"] is None


async def test_get_application_not_found_404(client, make_admin):
    """GET /applications/{id} con UUID inexistente → 404 (APP-1)."""
    _, token = await make_admin()
    resp = await client.get(f"/applications/{uuid4()}", headers=_auth(token))
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "not_found"


# -- APP-5: Researcher NO muta ----------------------------------------------

async def test_researcher_cannot_create_application_403(client, make_researcher):
    """POST /applications con bearer de Researcher → 403 (APP-5)."""
    _, token = await make_researcher()
    resp = await client.post(
        "/applications", headers=_auth(token), json={"name": "x"}
    )
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "forbidden"


async def test_researcher_cannot_update_application_403(
    client, make_admin, make_researcher
):
    """PUT /applications/{id} con bearer de Researcher → 403 (APP-5)."""
    _, admin_token = await make_admin()
    created = await client.post(
        "/applications", headers=_auth(admin_token), json={"name": "web-app"}
    )
    app_id = created.json()["app_id"]
    _, token = await make_researcher()

    resp = await client.put(
        f"/applications/{app_id}", headers=_auth(token), json={"name": "hack"}
    )
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "forbidden"


async def test_researcher_cannot_delete_application_403(
    client, make_admin, make_researcher
):
    """DELETE /applications/{id} con bearer de Researcher → 403 (APP-5)."""
    _, admin_token = await make_admin()
    created = await client.post(
        "/applications", headers=_auth(admin_token), json={"name": "web-app"}
    )
    app_id = created.json()["app_id"]
    _, token = await make_researcher()

    resp = await client.delete(f"/applications/{app_id}", headers=_auth(token))
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "forbidden"


# -- APP-4: DELETE /applications/{id} ---------------------------------------

async def test_delete_application_without_sessions_204_then_404(
    client, make_admin
):
    """DELETE sin user_session → 204; la app ya no existe (GET → 404) (APP-4)."""
    _, token = await make_admin()
    created = await client.post(
        "/applications", headers=_auth(token), json={"name": "temp"}
    )
    app_id = created.json()["app_id"]

    resp = await client.delete(f"/applications/{app_id}", headers=_auth(token))
    assert resp.status_code == 204
    assert resp.content == b""

    get_resp = await client.get(f"/applications/{app_id}", headers=_auth(token))
    assert get_resp.status_code == 404


async def test_delete_application_with_sessions_409_then_200(
    client, db_session, make_admin
):
    """DELETE con user_session (FK RESTRICT) → 409; la app permanece (APP-4)."""
    _, token = await make_admin()
    created = await client.post(
        "/applications", headers=_auth(token), json={"name": "in-use"}
    )
    app_id = created.json()["app_id"]
    await db_session.execute(
        text(
            "INSERT INTO user_session (session_id, app_id, user_id, start_timestamp) "
            "VALUES (:session_id, :app_id, NULL, now())"
        ),
        {"session_id": uuid4(), "app_id": UUID(app_id)},
    )
    await db_session.commit()

    resp = await client.delete(f"/applications/{app_id}", headers=_auth(token))
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "conflict"

    get_resp = await client.get(f"/applications/{app_id}", headers=_auth(token))
    assert get_resp.status_code == 200


async def test_delete_application_not_found_404(client, make_admin):
    """DELETE /applications/{id} con UUID inexistente → 404 (APP-4)."""
    _, token = await make_admin()
    resp = await client.delete(f"/applications/{uuid4()}", headers=_auth(token))
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "not_found"


# -- APP-3: PUT /applications/{id} ------------------------------------------

async def test_update_application_200(client, make_admin):
    """PUT actualiza name/description y conserva api_token_hash null (APP-3)."""
    _, token = await make_admin()
    created = await client.post(
        "/applications", headers=_auth(token), json={"name": "before"}
    )
    app_id = created.json()["app_id"]

    resp = await client.put(
        f"/applications/{app_id}",
        headers=_auth(token),
        json={"name": "after", "description": "desc"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["name"] == "after"
    assert body["description"] == "desc"
    assert body["api_token_hash"] is None


async def test_update_application_not_found_404(client, make_admin):
    """PUT /applications/{id} con UUID inexistente → 404 (APP-3)."""
    _, token = await make_admin()
    resp = await client.put(
        f"/applications/{uuid4()}", headers=_auth(token), json={"name": "x"}
    )
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "not_found"


# -- APP-6: validaciones de forma → 422 -------------------------------------

async def test_create_application_422_empty_name(client, make_admin):
    """POST con name vacío → 422 (APP-6)."""
    _, token = await make_admin()
    resp = await client.post(
        "/applications", headers=_auth(token), json={"name": ""}
    )
    assert resp.status_code == 422


async def test_create_application_422_nul_byte_in_name(client, make_admin):
    """POST con NUL (\\x00) en name → 422, no 500 (Postgres rechaza 0x00)."""
    _, token = await make_admin()
    resp = await client.post(
        "/applications", headers=_auth(token), json={"name": "bad\x00name"}
    )
    assert resp.status_code == 422


async def test_update_application_422_nul_byte_in_description(
    client, make_admin
):
    """PUT con NUL (\\x00) en description → 422, no 500 (Postgres rechaza 0x00)."""
    _, token = await make_admin()
    created = await client.post(
        "/applications", headers=_auth(token), json={"name": "ok"}
    )
    app_id = created.json()["app_id"]

    resp = await client.put(
        f"/applications/{app_id}",
        headers=_auth(token),
        json={"description": "bad\x00desc"},
    )
    assert resp.status_code == 422


async def test_update_application_422_empty_name(client, make_admin):
    """PUT con name vacío → 422 (APP-6)."""
    _, token = await make_admin()
    created = await client.post(
        "/applications", headers=_auth(token), json={"name": "ok"}
    )
    app_id = created.json()["app_id"]

    resp = await client.put(
        f"/applications/{app_id}", headers=_auth(token), json={"name": ""}
    )
    assert resp.status_code == 422


# -- AUTH-5 reutilizado sobre /applications (D3: wiring de require_role) ----

async def test_applications_path_requires_bearer(client):
    """GET /applications sin bearer → 401 invalid_token (AUTH-5 sobre /applications)."""
    resp = await client.get("/applications")
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "invalid_token"
