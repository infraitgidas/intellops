"""Módulo encargado de la lectura y validación de datos simulados (mocks)."""
import json
import os
from typing import List

from src.ml.schemas import MetricBatchInput


def load_mock_data() -> List[MetricBatchInput]:
    """Lee y valida los datos mock respetando el contrato del dataset."""
    file_path = os.path.join(os.path.dirname(__file__), '..', 'mock_data.json')

    with open(file_path, 'r', encoding='utf-8') as file:
        raw_data = json.load(file)

    validated_batch = [MetricBatchInput(**item) for item in raw_data]
    return validated_batch
