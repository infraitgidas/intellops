"""Cliente de ingesta de la sonda (S3, D1-D4).

Arma un `RumEventBatch` con las métricas de la corrida y lo envía por el mismo
camino que el RUM: `POST /telemetry/metrics` con la API key del tenant. Así la
disponibilidad queda agregable por `GET /metrics/query` sin read path nuevo.

- D1: `AVAILABILITY`, unidad `count`, valor 1/0 (razón de uptime por bucket).
- D2: la latencia va como `TTFB` (la sonda mide tiempo hasta el primer byte).
- D3: el status HTTP va en `metadata`, no como métrica.
- D4: sin `session_id` explícito se usa un UUID v5 estable derivado del target.

Un evento que la política rechaza se pierde COMPLETO, no por métrica: por eso
`build_batch` no emite `TTFB` cuando la latencia medida queda fuera del rango de
cordura del contrato (S2). Un sitio lento produce una latencia mayor al tope y
mandarla haría que la ingesta descarte también la disponibilidad.
"""

import logging
from hashlib import sha256
from typing import Any
from uuid import NAMESPACE_URL, uuid5

import httpx

from api.domain.services.ingest_policy import RANGE_BY_TYPE
from probe.runner import ProbeResult

logger = logging.getLogger(__name__)

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
    """Métrica `TTFB` en ms, solo si hubo respuesta que medir (D2, S4).

    La métrica se emite ÚNICAMENTE si la latencia cae dentro del rango de
    cordura que la política declara para `TTFB` (S2): el rango se importa de
    `ingest_policy.RANGE_BY_TYPE`, no se copia, para que la sonda siga al
    contrato sin deriva. Una corrida contra un sitio lento puede superar el
    tope; enviarla haría que la ingesta rechace el evento ENTERO con
    `invalid_range` y se perdería también la disponibilidad. El valor medido no
    se pierde: queda en `metadata.latency_ms` del registro de disponibilidad.
    """
    if result.latency_ms is None:
        return None
    _, max_latency_ms = RANGE_BY_TYPE[LATENCY_METRIC]
    if max_latency_ms is not None and result.latency_ms > max_latency_ms:
        return None
    return {
        "type": LATENCY_METRIC,
        "value": result.latency_ms,
        "unit": LATENCY_UNIT,
        "metadata": _metric_metadata(result),
    }


def _parse_ingest_body(response: httpx.Response) -> tuple[int | None, list[str]]:
    """Extrae `accepted` y las razones de rechazo de la respuesta (S2, S3).

    El cuerpo de la ingesta es `IngestResponse` (`batch_id`, `accepted`,
    `rejected[{index, reason}]`). Si no es JSON o no trae `accepted`, se
    devuelve `None` para no inventar un resultado: el status es toda la
    evidencia disponible.
    """
    try:
        body = response.json()
    except ValueError:
        return None, []
    if not isinstance(body, dict):
        return None, []
    accepted = body.get("accepted")
    if not isinstance(accepted, int) or isinstance(accepted, bool):
        accepted = None
    rejected = body.get("rejected")
    reasons = [
        f"{item.get('index')}:{item.get('reason')}"
        for item in (rejected if isinstance(rejected, list) else [])
        if isinstance(item, dict)
    ]
    return accepted, reasons


def _log_ingest_outcome(response: httpx.Response, payload: dict[str, Any]) -> None:
    """Registra QUÉ aceptó la ingesta, no solo el status (S2, S3).

    `202` solo significa "recibido": si la política rechazó eventos, el batch
    se pierde igual y un log con `ingest_status=202` a secas esconde la pérdida.
    Por eso se registran `accepted`, la cantidad enviada y las razones del
    rechazo, con nivel WARNING cuando no se aceptó todo.
    """
    sent = len(payload.get("events") or [])
    accepted, reasons = _parse_ingest_body(response)
    if accepted is None:
        logger.info(
            "probe ingest status=%s sent=%s accepted=unknown",
            response.status_code,
            sent,
        )
        return
    log = logger.info if accepted >= sent else logger.warning
    log(
        "probe ingest status=%s sent=%s accepted=%s rejected=%s reasons=%s",
        response.status_code,
        sent,
        accepted,
        len(reasons),
        ",".join(reasons) or "-",
    )


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
    key o el payload no son válidos); el llamador solo lo registra. El cuerpo de
    la respuesta sí se registra acá: es el único lugar donde `accepted` y las
    razones de rechazo están disponibles (S2).
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
    _log_ingest_outcome(response, payload)
    return response.status_code
