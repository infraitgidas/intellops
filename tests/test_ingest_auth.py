"""Tests del guard de ingesta — IAUTH-1..IAUTH-5 (spec §2, design §7).

Ejercita `require_api_key` contra la app de prueba `/_probe` definida en
tests/conftest.py (IAUTH-5: el guard es reutilizable y NO está cableado a
ningún path de producción en este cambio; el wiring a /telemetry/* vive en
#37). Cubre 401 indistinguibles con WWW-Authenticate, 403 app_inactive,
binding 1:1 (payload app_id nunca confiable) y APP-8 (reactivación).
"""

from uuid import uuid4


def _api_key_header(key: str) -> dict[str, str]:
    return {"X-API-Key": key}


def _extract_key(body: dict) -> str:
    assert body["api_key"].startswith("ilp_")
    return body["api_key"]


async def _issue_key(client, token: str, app_id: str) -> str:
    resp = await client.post(
        f"/applications/{app_id}/api-key", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 201
    return _extract_key(resp.json())


# -- IAUTH-1: key ausente ----------------------------------------------------

async def test_probe_401_missing_key_with_www_authenticate(probe_client):
    """Request sin X-API-Key → 401 con ErrorResponse y WWW-Authenticate
    indicando el esquema (IAUTH-1)."""
    resp = await probe_client.get("/_probe")
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "invalid_api_key"
    assert resp.headers.get("www-authenticate") == "ApiKey"


# -- IAUTH-1/IAUTH-3: key inválida indistinguible ----------------------------

async def test_probe_401_identical_for_missing_and_invalid_keys(probe_client):
    """Key sin prefijo ilp_ y hash que no coincide DEBEN dar 401 idéntico al
    caso de key ausente (sin información de causa, IAUTH-1/IAUTH-3)."""
    missing = await probe_client.get("/_probe")
    no_prefix = await probe_client.get(
        "/_probe",
        headers=_api_key_header(
            "random-key-without-prefix-"
            "123456789012345678901234567890123456789012345678"
        ),
    )
    wrong_hash = await probe_client.get(
        "/_probe", headers=_api_key_header("ilp_" + "A" * 43)
    )

    for resp in (no_prefix, wrong_hash):
        assert resp.status_code == 401
        assert resp.json() == missing.json()
        assert resp.json()["error"]["code"] == "invalid_api_key"


async def test_probe_401_revoked_key_indistinguishable(
    client, make_admin, probe_client
):
    """Key revocada vía DELETE → 401 fail-closed, idéntico a key inexistente
    (IAUTH-1, CRED-4)."""
    _, token = await make_admin()
    created = await client.post(
        "/applications", headers={"Authorization": f"Bearer {token}"}, json={"name": "revoked"}
    )
    app_id = created.json()["app_id"]
    key = await _issue_key(client, token, app_id)
    await client.delete(
        f"/applications/{app_id}/api-key",
        headers={"Authorization": f"Bearer {token}"},
    )

    missing = await probe_client.get("/_probe")
    revoked = await probe_client.get("/_probe", headers=_api_key_header(key))
    assert revoked.status_code == 401
    assert revoked.json() == missing.json()


# -- IAUTH-1/APP-8: aplicación inactiva → 403 app_inactive --------------------

async def test_probe_403_app_inactive_then_reactivate(
    client, make_admin, probe_client
):
    """App con is_active=false y key válida → 403 app_inactive; reactivar la
    app restaura la validez de la key vigente (APP-8, IAUTH-1)."""
    _, token = await make_admin()
    created = await client.post(
        "/applications", headers={"Authorization": f"Bearer {token}"}, json={"name": "flappy"}
    )
    app_id = created.json()["app_id"]
    key = await _issue_key(client, token, app_id)

    deactivated = await client.put(
        f"/applications/{app_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"is_active": False},
    )
    assert deactivated.status_code == 200
    assert deactivated.json()["is_active"] is False

    denied = await probe_client.get("/_probe", headers=_api_key_header(key))
    assert denied.status_code == 403
    assert denied.json()["error"]["code"] == "app_inactive"

    reactivated = await client.put(
        f"/applications/{app_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"is_active": True},
    )
    assert reactivated.status_code == 200

    allowed = await probe_client.get("/_probe", headers=_api_key_header(key))
    assert allowed.status_code == 200
    assert allowed.json()["app_id"] == app_id


# -- IAUTH-2: binding 1:1 — payload app_id nunca confiable --------------------

async def test_probe_binding_1_1_ignores_claimed_app_id_in_payload(
    client, make_admin, probe_client
):
    """La aplicación autenticada DEBE derivarse EXCLUSIVAMENTE de la key: un
    payload/query que reclama otro app_id se ignora (IAUTH-2, mitigación
    BOLA/API1)."""
    _, token = await make_admin()
    created = await client.post(
        "/applications", headers={"Authorization": f"Bearer {token}"}, json={"name": "holder"}
    )
    app_id = created.json()["app_id"]
    key = await _issue_key(client, token, app_id)

    resp = await probe_client.get(
        "/_probe",
        headers=_api_key_header(key),
        params={"claimed_app_id": str(uuid4())},
    )
    assert resp.status_code == 200
    assert resp.json()["app_id"] == app_id
    assert resp.json()["claimed_app_id"] != app_id


# -- IAUTH-5: guard cableado a producción en /telemetry/* ----------------------

def _walk_apiroutes(routes):
    """Aplana los routes de la app: FastAPI reciente envuelve los routers
    incluidos en `_IncludedRouter` (sin `.path`); los desenvuelve vía
    `original_router.routes` para inspeccionar APIRoute."""
    for route in routes:
        if type(route).__name__ == "_IncludedRouter":
            yield from _walk_apiroutes(route.original_router.routes)
        elif hasattr(route, "path") and hasattr(route, "dependant"):
            yield route


def test_prod_app_wires_api_key_guard_to_telemetry_paths():
    """IAUTH-5: el guard require_api_key DEBE estar cableado a los paths de
    producción /telemetry/metrics y /telemetry/exceptions (ISS-S2-03)."""
    from api.main import app
    from api.presentation.dependencies import require_api_key

    covered = set()
    for route in _walk_apiroutes(app.routes):
        if not route.path.startswith("/telemetry/"):
            continue
        dependency_calls = [d.call for d in route.dependant.dependencies]
        assert require_api_key in dependency_calls, (
            f"{route.path} DEBE aplicar Depends(require_api_key)"
        )
        covered.add(route.path)
    assert covered == {"/telemetry/metrics", "/telemetry/exceptions"}


async def test_probe_injects_authenticated_application(
    client, make_admin, probe_client
):
    """Key válida DEBE inyectar la Application autenticada en el handler
    (IAUTH-1): el probe la devuelve completa (id + name)."""
    _, token = await make_admin()
    created = await client.post(
        "/applications", headers={"Authorization": f"Bearer {token}"}, json={"name": "injected"}
    )
    app_id = created.json()["app_id"]
    key = await _issue_key(client, token, app_id)

    resp = await probe_client.get("/_probe", headers=_api_key_header(key))
    assert resp.status_code == 200
    assert resp.json()["app_id"] == app_id
    assert resp.json()["name"] == "injected"
