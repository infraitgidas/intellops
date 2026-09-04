"""Pruebas unitarias para el worker de IA y sus contratos."""
from fastapi.testclient import TestClient
from src.ml.main import app
from src.ml.pipeline.mock_reader import load_mock_data


def test_mock_reader_validates_contract():
    """Verifica la lectura del JSON validada por Pydantic."""
    data = load_mock_data()
    assert isinstance(data, list)
    assert len(data) > 0
    # Verifica la instanciación de campos clave
    assert hasattr(data[0], "application_id")
    assert hasattr(data[0], "value")


def test_ml_status_endpoint_and_startup():
    """Verifica el evento de arranque y endpoint."""
    # TestClient en un bloque 'with' dispara el startup
    with TestClient(app) as client:
        response = client.get("/ml/status")
        assert response.status_code == 200

        payload = response.json()
        assert payload["status"] == "online"
        assert payload["module"] == "intellops-ai-engine"
        assert payload["mock_contract_valid"] is True
