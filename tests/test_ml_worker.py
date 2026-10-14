"""Pruebas unitarias para el worker de IA y sus contratos."""
import json
import os
import sys

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from src.ml.schemas import MetricBatchInput
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


# --- Contrato M4 (ISS-S3-04): sin metric_id, con bucket_seconds ---
pytestmark = pytest.mark.unit

_VALID = {
    "application_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "metric_type_id": 1,
    "timestamp": "2026-08-28T21:15:00Z",
    "bucket_seconds": 60,
    "value": 1850.5,
    "session_count": 25,
}


def _with(**changes):
    data = dict(_VALID)
    data.update(changes)
    return data


def test_valid_record_without_metric_id():
    record = MetricBatchInput(**_VALID)
    assert record.bucket_seconds == 60
    assert not hasattr(record, "metric_id")


def test_missing_bucket_seconds_fails():
    data = dict(_VALID)
    del data["bucket_seconds"]
    with pytest.raises(ValidationError):
        MetricBatchInput(**data)


def test_metric_id_is_forbidden():
    with pytest.raises(ValidationError):
        MetricBatchInput(**_with(metric_id="8bb38d38-9cb5-4521-8207-6cb5622a450a"))


def test_naive_timestamp_fails():
    with pytest.raises(ValidationError):
        MetricBatchInput(**_with(timestamp="2026-08-28T21:15:00"))


def test_unaligned_timestamp_fails():
    with pytest.raises(ValidationError):
        MetricBatchInput(**_with(timestamp="2026-08-28T21:15:05Z"))


def test_bucket_seconds_below_minimum_fails():
    with pytest.raises(ValidationError):
        MetricBatchInput(**_with(bucket_seconds=30))


def test_mock_data_json_has_no_metric_id():
    path = os.path.join(os.path.dirname(__file__), "..", "src", "ml", "mock_data.json")
    with open(path, encoding="utf-8") as fh:
        raw = json.load(fh)
    assert all("metric_id" not in row for row in raw)
    assert all(row["bucket_seconds"] == 60 for row in raw)


def test_generator_output_validates_without_metric_id():
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ml", "data"))
    try:
        from generate_mock_dataset import generate_dataset
    finally:
        sys.path.pop(0)
    rows = generate_dataset(n_rows=30)
    assert all("metric_id" not in row for row in rows)
    assert [MetricBatchInput(**row) for row in rows]
