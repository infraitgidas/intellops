"""Cliente de ingesta de la sonda (S3, D1-D4).

Arma un `RumEventBatch` con las métricas de la corrida y lo envía por el mismo
camino que el RUM: `POST /telemetry/metrics` con la API key del tenant. Así la
disponibilidad queda agregable por `GET /metrics/query` sin read path nuevo.

- D1: `AVAILABILITY`, unidad `count`, valor 1/0 (razón de uptime por bucket).
- D2: la latencia va como `TTFB` (la sonda mide tiempo hasta el primer byte).
- D3: el status HTTP va en `metadata`, no como métrica.
- D4: sin `session_id` explícito se usa un UUID v5 estable derivado del target.
"""

from typing import Any
from uuid import NAMESPACE_URL, uuid5

import httpx

from probe.runner import ProbeResult

SCHEMA_VERSION = "1.0"
AVAILABILITY_METRIC = "AVAILABILITY"
AVAILABILITY_UNIT = "count"
LATENCY_METRIC = "TTFB"
LATENCY_UNIT = "ms"

# Único endpoint de ingesta RUM: la sonda no tiene camino privilegiado (S3).
TELEMETRY_PATH = "/telemetry/metrics"
API_KEY_HEADER = "X-API-Key"


def synthetic_session_id(target_url: str) -> str:
    """UUID v5 estable por target (D4): una sesión sintética, no una por corrida.

    `uuid5` sobre `NAMESPACE_URL` es determinista entre procesos, así que el
    mismo target conserva su sesión y no se inventa cardinalidad.
    """
    return str(uuid5(NAMESPACE_URL, target_url))


def _metric_metadata(result: ProbeResult) -> dict[str, Any]:
    """Metadata de la corrida: status, target, resultado y latencia (D3)."""
    return {
        "http_status": result.status_code,
        "probe_target": result.target_url,
        "outcome": result.outcome.value,
        "latency_ms": result.latency_ms,
    }


def _availability_metric(result: ProbeResult) -> dict[str, Any]:
    """Métrica `AVAILABILITY` 1/0 — el AVG del bucket es el uptime (D1)."""
    return {
        "type": AVAILABILITY_METRIC,
        "value": 1 if result.available else 0,
        "unit": AVAILABILITY_UNIT,
        "metadata": _metric_metadata(result),
    }


def _latency_metric(result: ProbeResult) -> dict[str, Any] | None:
    """Métrica `TTFB` en ms, solo si hubo respuesta que medir (D2, S4)."""
    if result.latency_ms is None:
        return None
    return {
        "type": LATENCY_METRIC,
        "value": result.latency_ms,
        "unit": LATENCY_UNIT,
        "metadata": _metric_metadata(result),
    }


def build_batch(
    result: ProbeResult,
    session_id: str | None = None,
    application_id: str | None = None,
) -> dict[str, Any]:
    """Arma el `RumEventBatch` de una corrida (payload JSON de ingesta).

    El evento cumple `api.domain.services.ingest_policy.validate_rum_event`: es
    la política real, no una copia, para que la sonda no derive del contrato.
    """
    metrics = [_availability_metric(result)]
    latency_metric = _latency_metric(result)
    if latency_metric is not None:
        metrics.append(latency_metric)

    event: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "timestamp": result.timestamp.isoformat(),
        "session_id": session_id or synthetic_session_id(result.target_url),
        "metrics": metrics,
    }
    if application_id is not None:
        event["application_id"] = application_id

    return {"schema_version": SCHEMA_VERSION, "events": [event]}


async def send_batch(
    base_url: str,
    api_key: str,
    payload: dict[str, Any],
    client: httpx.AsyncClient,
    timeout_seconds: float | None = None,
) -> int:
    """Envía el batch por `POST /telemetry/metrics` y devuelve el status.

    El status lo decide la ingesta (202 en el camino feliz, 401/422 si la API
    key o el payload no son válidos); el llamador solo lo registra.
    """
    url = f"{base_url.rstrip('/')}{TELEMETRY_PATH}"
    response = await client.post(
        url,
        json=payload,
        headers={API_KEY_HEADER: api_key},
        timeout=timeout_seconds,
    )
    return response.status_code
