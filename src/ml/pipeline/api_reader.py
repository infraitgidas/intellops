"""Reader HTTP del dataset operativo: pull de `GET /metrics/query` (ISS-S3-04)."""
import math
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple

import httpx

from src.ml.config import MLDatasetSettings
from src.ml.pipeline.mapper import DatasetReadError, to_batch
from src.ml.schemas import MetricBatchInput

_MAX_WINDOW = timedelta(days=7)
_TS_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


def align_window(
    start: datetime, end: datetime, bucket_seconds: int
) -> Tuple[datetime, datetime]:
    """Alinea [start, end) a múltiplos de bucket_seconds desde el epoch UTC."""
    if start.tzinfo is None or end.tzinfo is None:
        raise DatasetReadError("window datetimes must be timezone-aware")
    aligned_start = math.floor(start.timestamp() / bucket_seconds) * bucket_seconds
    aligned_end = math.floor(end.timestamp() / bucket_seconds) * bucket_seconds
    if aligned_start >= aligned_end:
        raise DatasetReadError("window is empty after aligning to buckets")
    if aligned_end - aligned_start > _MAX_WINDOW.total_seconds():
        raise DatasetReadError("window exceeds the 7 day read path limit")
    return (
        datetime.fromtimestamp(aligned_start, tz=timezone.utc),
        datetime.fromtimestamp(aligned_end, tz=timezone.utc),
    )


def _error_code(response: httpx.Response) -> Optional[str]:
    try:
        return response.json()["error"]["code"]
    except (ValueError, KeyError, TypeError):
        return None


def _fetch(client: httpx.Client, settings: MLDatasetSettings, params: dict):
    url = f"{settings.api_base_url.rstrip('/')}/metrics/query"
    headers = {"X-API-Key": settings.api_key.get_secret_value()}
    try:
        response = client.get(url, params=params, headers=headers)
    except httpx.HTTPError as exc:
        raise DatasetReadError(
            f"read path unavailable: {type(exc).__name__}"
        ) from exc
    status = response.status_code
    if status in (401, 403):
        raise DatasetReadError(
            f"read path rejected the API key or the app is inactive ({status})",
            status=status,
            code=_error_code(response),
        )
    if status == 422:
        code = _error_code(response)
        raise DatasetReadError(
            f"read path rejected the window (422 {code}): alignment bug",
            status=status,
            code=code,
        )
    if status != 200:
        raise DatasetReadError(
            f"read path unavailable (status {status})", status=status
        )
    try:
        rows = response.json()
    except ValueError as exc:
        raise DatasetReadError("response body is not JSON (contract)") from exc
    if not isinstance(rows, list):
        raise DatasetReadError("response body is not a list (contract)")
    return rows


def read_dataset(
    settings: MLDatasetSettings,
    client: Optional[httpx.Client] = None,
    now: Optional[datetime] = None,
) -> List[MetricBatchInput]:
    """Pull de la ventana configurada; devuelve el batch validado o falla."""
    now = now or datetime.now(timezone.utc)
    start, end = align_window(
        now - timedelta(minutes=settings.window_minutes), now, settings.bucket_seconds
    )
    params = {
        "start": start.strftime(_TS_FORMAT),
        "end": end.strftime(_TS_FORMAT),
        "bucket_seconds": settings.bucket_seconds,
    }
    if client is not None:
        rows = _fetch(client, settings, params)
    else:
        with httpx.Client(
            transport=httpx.HTTPTransport(retries=settings.http_retries),
            timeout=settings.http_timeout_seconds,
        ) as owned:
            rows = _fetch(owned, settings, params)
    return to_batch(rows, settings.bucket_seconds, start, end)
