"""CORS de la API — el wildcard debe ser compatible con navegadores (D-05).

`allow_origins=["*"]` exige `allow_credentials=False`. Con credenciales
habilitadas el navegador rechaza la respuesta porque
`Access-Control-Allow-Origin: *` es inválido junto a
`Access-Control-Allow-Credentials: true`. La ingesta autentica con el header
`X-API-Key`, no con cookies, así que no necesita credenciales CORS.
"""

from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)

ORIGIN = "https://piloto.example.com"


def test_preflight_permite_origen_externo_sin_credenciales():
    """El preflight de un sitio piloto DEBE devolver `*` sin credenciales."""
    response = client.options(
        "/telemetry/metrics",
        headers={
            "Origin": ORIGIN,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "x-api-key,content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "*"
    assert "access-control-allow-credentials" not in response.headers
    assert "x-api-key" in response.headers["access-control-allow-headers"].lower()


def test_respuesta_simple_devuelve_wildcard():
    """Una respuesta simple DEBE exponer `*`, no el origen reflejado."""
    response = client.get("/openapi.json", headers={"Origin": ORIGIN})

    assert response.headers["access-control-allow-origin"] == "*"
    assert "access-control-allow-credentials" not in response.headers
