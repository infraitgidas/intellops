"""Tests del endpoint de health check."""

import pytest
from fastapi.testclient import TestClient

from api.main import app

# /health consulta Postgres con el engine global (sin fixtures de DB): se
# declara integración explícitamente para que no corra en `pytest -m unit`.
pytestmark = pytest.mark.integration

client = TestClient(app)


def test_health_endpoint():
    """GET /health debe retornar status ok y confirmar conexión a la DB."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == "0.1.0"
    assert data["service"] == "intellops-api"
    assert data["database"] == "connected"


def test_readiness_endpoint():
    """GET /ready debe retornar ready."""
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}
