"""Mapeo puro MetricAggregate (JSON del read path) -> MetricBatchInput."""
import math
from datetime import datetime
from typing import Any, List, Optional

from pydantic import ValidationError

from src.ml.schemas import MetricBatchInput

_FIELDS = ("application_id", "metric_type_id", "timestamp", "value", "session_count")


class DatasetReadError(Exception):
    """Falla tipada al leer o validar el dataset operativo."""

    def __init__(
        self, message: str, status: Optional[int] = None, code: Optional[str] = None
    ) -> None:
        super().__init__(message)
        self.status = status
        self.code = code


def _to_record(index: int, row: Any, bucket_seconds: int) -> MetricBatchInput:
    if not isinstance(row, dict):
        raise DatasetReadError(f"row {index}: not an object")
    missing = [name for name in _FIELDS if name not in row]
    if missing:
        raise DatasetReadError(f"row {index}: missing fields {missing}")
    try:
        record = MetricBatchInput(
            **{name: row[name] for name in _FIELDS}, bucket_seconds=bucket_seconds
        )
    except ValidationError as exc:
        raise DatasetReadError(f"row {index}: invalid aggregate: {exc}") from exc
    if not math.isfinite(record.value):
        raise DatasetReadError(f"row {index}: value is not finite")
    return record


def to_batch(
    rows: List[Any], bucket_seconds: int, start: datetime, end: datetime
) -> List[MetricBatchInput]:
    """Valida fail-fast cada fila y devuelve el batch (sin datos parciales)."""
    batch: List[MetricBatchInput] = []
    seen = set()
    for index, row in enumerate(rows):
        record = _to_record(index, row, bucket_seconds)
        if not start <= record.timestamp < end:
            raise DatasetReadError(f"row {index}: timestamp outside window")
        if batch and record.application_id != batch[0].application_id:
            raise DatasetReadError(f"row {index}: mixed application_id")
        key = (record.metric_type_id, record.timestamp)
        if key in seen:
            raise DatasetReadError(f"row {index}: duplicate series/bucket {key}")
        seen.add(key)
        batch.append(record)
    return batch
