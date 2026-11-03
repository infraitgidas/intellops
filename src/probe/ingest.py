"""Cliente de ingesta de la sonda (S3, D1-D4).

Arma un `RumEventBatch` con las métricas de la corrida y lo envía por el mismo
camino que el RUM: `POST /telemetry/metrics` con la API key del tenant. Así la
disponibilidad queda agregable por `GET /metrics/query` sin read path nuevo.

- D1: `AVAILABILITY`, unidad `count`, valor 1/0 (razón de uptime por bucket).
- D2: la latencia va como `TTFB` (la sonda mide tiempo hasta el primer byte).
- D3: el status HTTP va en `metadata`, no como métrica.
- D4: sin `session_id` explícito se usa un UUID v5 estable derivado del target.
"""

from hashlib import sha256
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

# Timeout del envío: el ciclo nunca queda colgado esperando una ingesta muda
# (R3-003). Se override con el timeout de la corrida en `python -m probe`.
DEFAULT_INGEST_TIMEOUT_SECONDS = 10.0


def synthetic_session_id(api_key: str, target_url: str) -> str:
    """UUID v5 estable por TENANT y target (D4, R1-001/R3-001/R4-005).

    El tenant entra en la derivación porque `session_id` es la PK de
    `user_session` y la dueña de la sesión es la aplicación: sin él, dos
    tenants que miden el mismo target colisionarían en la misma sesión y sus
    métricas se atribuirían (o se descartarían) al otro tenant.

    La API key se hashea antes de entrar al UUID: la sesión depende del tenant
    sin codificar el secreto en el identificador persistido.
    """
    tenant = sha256(api_key.encode("utf-8")).hexdigest()
    return str(uuid5(NAMESPACE_URL, f"{tenant}:{target_url}"))


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
    api_key: str,
    session_id: str | None = None,
    application_id: str | None = None,
) -> dict[str, Any]:
    """Arma el `RumEventBatch` de una corrida (payload JSON de ingesta).

    `api_key` identifica al tenant: sin `session_id` explícito, la sesión
    sintética se deriva de (tenant, target) para no mezclar tenants que miden
    el mismo sitio (D4, R1-001).

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
        "session_id": session_id or synthetic_session_id(api_key, result.target_url),
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

    El envío SIEMPRE lleva timeout (R3-003): uno explícito o el default acotado.
    Sin él, una ingesta que no responde bloquea el ciclo y el intervalo de la
    sonda deja de correr.

    El status lo decide la ingesta (202 en el camino feliz, 401/422 si la API
    key o el payload no son válidos); el llamador solo lo registra.
    """
    url = f"{base_url.rstrip('/')}{TELEMETRY_PATH}"
    response = await client.post(
        url,
        json=payload,
        headers={API_KEY_HEADER: api_key},
        timeout=(
            DEFAULT_INGEST_TIMEOUT_SECONDS
            if timeout_seconds is None
            else timeout_seconds
        ),
    )
    return response.status_code
