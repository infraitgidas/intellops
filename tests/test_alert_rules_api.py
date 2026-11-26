"""TDD integration: POST/GET /alerts/config — OAS-B14-1/OAS-B14-2 (ISS-B-14).

httpx ASGI + Postgres real. Fija:

- POST con Admin crea la regla (201) y la repite como actualización (200) sin
  duplicar filas (clave `application_id`+`metric_type_id`+`comparison`+
  `threshold`);
- GET con Admin o Researcher lista SOLO las reglas de la aplicación pedida,
  activas e inactivas, por `created_at` ascendente;
- 404 `application_not_found` (aplicación inexistente) y 404
  `metric_type_not_found` (métrica fuera del catálogo), antes de escribir;
- 422 `invalid_alert_rule` con el contrato ErrorResponse para cada violación
  semántica, sin tocar `alert_rule` (ni crear ni modificar la existente);
- 401 sin bearer y 403 para Researcher en POST.
"""

import json
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest
from sqlalchemy import text


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


# -- Helpers -------------------------------------------------------------------

async def _make_app(client, make_admin, name: str) -> tuple[UUID, str]:
    """Crea una aplicación vía HTTP; devuelve (app_id, token del Admin)."""
    _, token = await make_admin(email=f"admin-{uuid4().hex[:12]}@intellops.local")
    created = await client.post(
        "/applications", headers=_auth(token), json={"name": name}
    )
    assert created.status_code == 201, created.text
    return UUID(created.json()["app_id"]), token


async def _metric_type_id(db_session, name: str = "TTFB") -> int:
    """Id del catálogo `metric_type` (sembrado por las migraciones)."""
    result = await db_session.execute(
        text("SELECT metric_type_id FROM metric_type WHERE name = :name"),
        {"name": name},
    )
    return result.scalar_one()


def _payload(app_id: UUID, metric_type_id: int, **overrides) -> dict:
    payload = {
        "application_id": str(app_id),
        "metric_type_id": metric_type_id,
        "comparison": "gt",
        "threshold": 800.0,
        "window_minutes": 15,
        "min_samples": 5,
        "cooldown_minutes": 15,
        "severity": "high",
    }
    payload.update(overrides)
    return payload


async def _rule_rows(db_session) -> list[dict]:
    """Filas de alert_rule ordenadas por created_at (para contar y comparar)."""
    result = await db_session.execute(
        text(
            "SELECT rule_id, application_id, comparison, threshold, "
            "window_minutes, min_samples, cooldown_minutes, severity, "
            "is_active, created_at FROM alert_rule ORDER BY created_at, rule_id"
        )
    )
    return [dict(row._mapping) for row in result]


async def _seed_rule(
    db_session,
    app_id: UUID,
    metric_type_id: int,
    *,
    created_at: datetime,
    comparison: str = "gt",
    threshold: str = "100",
    is_active: bool = True,
) -> UUID:
    """Seed SQL directo de una regla con `created_at` explícito (0008)."""
    rule_id = uuid4()
    await db_session.execute(
        text(
            "INSERT INTO alert_rule (rule_id, application_id, metric_type_id, "
            "comparison, threshold, window_minutes, min_samples, "
            "cooldown_minutes, severity, is_active, created_at) "
            "VALUES (:rule_id, :app_id, :metric_type_id, :comparison, "
            ":threshold, 15, 5, 15, 'high', :is_active, :created_at)"
        ),
        {
            "rule_id": rule_id,
            "app_id": app_id,
            "metric_type_id": metric_type_id,
            "comparison": comparison,
            "threshold": threshold,
            "is_active": is_active,
            "created_at": created_at,
        },
    )
    await db_session.commit()
    return rule_id


async def _post_rule(client, token: str, payload: dict):
    """POST con `json.dumps` explícito.

    httpx rechaza `json=` con valores no finitos (allow_nan=False); el
    parser de Starlette sí acepta `NaN`/`Infinity`, que es el camino real
    para ejercitar la validación de umbral finito del servicio.
    """
    return await client.post(
        "/alerts/config",
        headers={**_auth(token), "Content-Type": "application/json"},
        content=json.dumps(payload),
    )


def _assert_error(resp, status: int, code: str) -> None:
    """Contrato ErrorResponse {error: {code, message}} con el status pedido."""
    assert resp.status_code == status, resp.text
    body = resp.json()
    assert set(body) == {"error"}
    assert set(body["error"]) == {"code", "message"}
    assert body["error"]["code"] == code
    assert body["error"]["message"]


# -- POST /alerts/config: alta (201) ------------------------------------------

async def test_create_rule_201_with_full_row(client, db_session, make_admin):
    """POST con Admin DEBE crear la regla y devolver 201 con la fila
    completa (OAS-B14-1)."""
    app_id, token = await _make_app(client, make_admin, "rule-create")
    metric_id = await _metric_type_id(db_session)

    resp = await client.post(
        "/alerts/config", headers=_auth(token), json=_payload(app_id, metric_id)
    )

    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert set(body) == {
        "rule_id",
        "application_id",
        "metric_type_id",
        "comparison",
        "threshold",
        "window_minutes",
        "min_samples",
        "cooldown_minutes",
        "severity",
        "is_active",
        "created_at",
    }
    assert body["application_id"] == str(app_id)
    assert body["metric_type_id"] == metric_id
    assert body["comparison"] == "gt"
    assert body["threshold"] == 800.0
    assert body["window_minutes"] == 15
    assert body["min_samples"] == 5
    assert body["cooldown_minutes"] == 15
    assert body["severity"] == "high"
    assert body["is_active"] is True

    (row,) = await _rule_rows(db_session)
    assert str(row["rule_id"]) == body["rule_id"]


# -- POST /alerts/config: idempotencia (200) ----------------------------------

async def test_upsert_same_key_returns_200_without_duplicating(
    client, db_session, make_admin
):
    """Repetir el POST con la misma clave DEBE actualizar la regla y
    responder 200: UNA sola fila, mismo rule_id (OAS-B14-1, escenario
    Idempotencia de la configuración)."""
    app_id, token = await _make_app(client, make_admin, "rule-upsert")
    metric_id = await _metric_type_id(db_session)

    created = await client.post(
        "/alerts/config", headers=_auth(token), json=_payload(app_id, metric_id)
    )
    assert created.status_code == 201, created.text

    updated = await client.post(
        "/alerts/config",
        headers=_auth(token),
        json=_payload(
            app_id,
            metric_id,
            cooldown_minutes=45,
            min_samples=9,
            severity="critical",
            is_active=False,
        ),
    )

    assert updated.status_code == 200, updated.text
    body = updated.json()
    assert body["rule_id"] == created.json()["rule_id"]
    assert body["cooldown_minutes"] == 45
    assert body["min_samples"] == 9
    assert body["severity"] == "critical"
    assert body["is_active"] is False

    (row,) = await _rule_rows(db_session)
    assert row["cooldown_minutes"] == 45
    assert row["severity"] == "critical"
    assert row["is_active"] is False


async def test_different_threshold_creates_a_second_rule(
    client, db_session, make_admin
):
    """Un umbral distinto NO es la misma regla: 201 y dos filas (la clave
    incluye `threshold`, OAS-B14-1)."""
    app_id, token = await _make_app(client, make_admin, "rule-threshold")
    metric_id = await _metric_type_id(db_session)

    await client.post(
        "/alerts/config", headers=_auth(token), json=_payload(app_id, metric_id)
    )
    other = await client.post(
        "/alerts/config",
        headers=_auth(token),
        json=_payload(app_id, metric_id, threshold=900.0),
    )

    assert other.status_code == 201, other.text
    assert len(await _rule_rows(db_session)) == 2


# -- GET /alerts/config -------------------------------------------------------

async def test_get_rules_isolates_applications_and_orders_oldest_first(
    client, db_session, make_admin
):
    """GET con `application_id` DEBE devolver solo las reglas de esa
    aplicación, activas e inactivas, por `created_at` ascendente
    (OAS-B14-2, escenario Reglas de otra aplicación no se mezclan)."""
    app_a, token = await _make_app(client, make_admin, "rule-a")
    app_b, _ = await _make_app(client, make_admin, "rule-b")
    metric_id = await _metric_type_id(db_session)
    now = datetime.now(timezone.utc).replace(microsecond=0)

    oldest = await _seed_rule(
        db_session, app_a, metric_id,
        created_at=now - timedelta(hours=3), comparison="lt", threshold="0.99",
    )
    inactive = await _seed_rule(
        db_session, app_a, metric_id,
        created_at=now - timedelta(hours=2), threshold="900", is_active=False,
    )
    newest = await _seed_rule(
        db_session, app_a, metric_id,
        created_at=now - timedelta(hours=1), threshold="1000",
    )
    await _seed_rule(
        db_session, app_b, metric_id,
        created_at=now - timedelta(minutes=30), threshold="1100",
    )

    resp = await client.get(
        "/alerts/config",
        headers=_auth(token),
        params={"application_id": str(app_a)},
    )

    assert resp.status_code == 200, resp.text
    rows = resp.json()
    assert [row["rule_id"] for row in rows] == [
        str(oldest), str(inactive), str(newest)
    ]
    assert {row["application_id"] for row in rows} == {str(app_a)}
    assert [row["is_active"] for row in rows] == [True, False, True]


async def test_get_rules_requires_application_id(client, make_admin):
    """Sin `application_id` el query no valida: 422 (parámetro requerido)."""
    _, token = await make_admin()
    resp = await client.get("/alerts/config", headers=_auth(token))
    assert resp.status_code == 422


async def test_get_unknown_application_is_404(client, make_admin):
    """Una aplicación inexistente en GET DEBE responder 404
    `application_not_found` (OAS-B14-2)."""
    _, token = await make_admin()
    resp = await client.get(
        "/alerts/config",
        headers=_auth(token),
        params={"application_id": str(uuid4())},
    )
    _assert_error(resp, 404, "application_not_found")


# -- 404 de POST --------------------------------------------------------------

async def test_post_unknown_application_is_404_without_rows(
    client, db_session, make_admin
):
    """POST con aplicación inexistente → 404 `application_not_found` y sin
    filas nuevas (OAS-B14-1)."""
    _, token = await make_admin()
    metric_id = await _metric_type_id(db_session)

    resp = await client.post(
        "/alerts/config",
        headers=_auth(token),
        json=_payload(uuid4(), metric_id),
    )

    _assert_error(resp, 404, "application_not_found")
    assert await _rule_rows(db_session) == []


async def test_post_unknown_metric_type_is_404_without_rows(
    client, db_session, make_admin
):
    """POST con `metric_type_id` fuera del catálogo → 404
    `metric_type_not_found` y sin filas nuevas (OAS-B14-1)."""
    app_id, token = await _make_app(client, make_admin, "rule-metric")

    resp = await client.post(
        "/alerts/config",
        headers=_auth(token),
        json=_payload(app_id, 9999),
    )

    _assert_error(resp, 404, "metric_type_not_found")
    assert await _rule_rows(db_session) == []


# -- 422 invalid_alert_rule ---------------------------------------------------

@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("severity", "urgent"),
        ("comparison", "ge"),
        ("window_minutes", 0),
        ("window_minutes", 10081),
        ("min_samples", 0),
        ("cooldown_minutes", 0),
        ("threshold", float("nan")),
        ("threshold", float("inf")),
    ],
)
async def test_invalid_semantics_is_422_without_rows(
    client, db_session, make_admin, field, value
):
    """Cada violación semántica DEBE responder 422 `invalid_alert_rule` con
    ErrorResponse y NO agregar filas a `alert_rule` (OAS-B14-1)."""
    app_id, token = await _make_app(client, make_admin, f"rule-bad-{uuid4().hex[:6]}")
    metric_id = await _metric_type_id(db_session)

    resp = await _post_rule(
        client, token, _payload(app_id, metric_id, **{field: value})
    )

    _assert_error(resp, 422, "invalid_alert_rule")
    assert field in resp.json()["error"]["message"]
    assert await _rule_rows(db_session) == []


async def test_rejected_post_does_not_touch_the_existing_rule(
    client, db_session, make_admin
):
    """Un POST rechazado con la misma clave DEBE dejar la regla intacta
    (OAS-B14-1: sin escritura, ni alta ni actualización)."""
    app_id, token = await _make_app(client, make_admin, "rule-reject")
    metric_id = await _metric_type_id(db_session)
    created = await client.post(
        "/alerts/config", headers=_auth(token), json=_payload(app_id, metric_id)
    )
    assert created.status_code == 201, created.text

    rejected = await client.post(
        "/alerts/config",
        headers=_auth(token),
        json=_payload(
            app_id, metric_id, cooldown_minutes=99, severity="urgent"
        ),
    )

    _assert_error(rejected, 422, "invalid_alert_rule")
    (row,) = await _rule_rows(db_session)
    assert row["cooldown_minutes"] == 15
    assert row["severity"] == "high"


# -- PRESERVE: la lectura de alertas existente sigue montada -------------------

async def test_preserve_get_alerts_is_still_served_by_the_read_router(
    client, make_admin
):
    """PRESERVE: `GET /alerts` (ISS-B-03) sigue resolviendo en su propio
    router y el path nuevo `/alerts/config` no lo tapa (mismo prefijo)."""
    app_id, token = await _make_app(client, make_admin, "rule-preserve")
    key_resp = await client.post(
        f"/applications/{app_id}/api-key", headers=_auth(token)
    )
    assert key_resp.status_code == 201, key_resp.text

    resp = await client.get(
        "/alerts", headers={"X-API-Key": key_resp.json()["api_key"]}
    )

    assert resp.status_code == 200, resp.text
    assert resp.json() == []


# -- Auth: 401/403 ------------------------------------------------------------

@pytest.mark.parametrize("method", ["post", "get"])
async def test_alerts_config_requires_bearer(client, method):
    """Sin bearer DEBE responder 401 `invalid_token` en ambos métodos."""
    if method == "post":
        resp = await client.post(
            "/alerts/config", json=_payload(uuid4(), 1)
        )
    else:
        resp = await client.get(
            "/alerts/config", params={"application_id": str(uuid4())}
        )
    _assert_error(resp, 401, "invalid_token")


async def test_researcher_cannot_create_but_can_list(
    client, db_session, make_admin, make_researcher
):
    """POST con Researcher → 403 `forbidden`; GET con Researcher → 200
    (OAS-B14-1 solo Admin, OAS-B14-2 Admin o Researcher)."""
    app_id, _ = await _make_app(client, make_admin, "rule-roles")
    metric_id = await _metric_type_id(db_session)
    _, researcher = await make_researcher(
        email=f"researcher-{uuid4().hex[:12]}@intellops.local"
    )

    forbidden = await client.post(
        "/alerts/config",
        headers=_auth(researcher),
        json=_payload(app_id, metric_id),
    )
    _assert_error(forbidden, 403, "forbidden")
    assert await _rule_rows(db_session) == []

    listed = await client.get(
        "/alerts/config",
        headers=_auth(researcher),
        params={"application_id": str(app_id)},
    )
    assert listed.status_code == 200, listed.text
    assert listed.json() == []
