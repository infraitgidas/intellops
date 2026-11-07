"""Una corrida de la sonda: disponibilidad, status y latencia (S2, S4).

El transporte HTTP se inyecta (`httpx.AsyncClient`), así la corrida es
determinista en tests y no abre red por su cuenta. La latencia se mide con
`time.perf_counter()`, que es monotónico y no depende del reloj de pared.

La medición es de TTFB y por streaming (D2, R3-002, R4-001): se mide al recibir
los headers y NO se lee el body. Leer el body mediría la descarga completa (no
el primer byte) y podría tardar más que el timeout en un sitio que está arriba,
además de materializar en memoria una respuesta que no se usa.

Ningún error de red escapa: un timeout o un error de conexión se registran
como indisponibilidad explícita (S4), no como una corrida perdida.
"""

import time
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum

import httpx

# Un status >= 400 significa servicio no disponible; el código se persiste en
# `rum_metric.metadata` porque promediar códigos de estado no significa nada
# (D3).
UNAVAILABLE_STATUS_THRESHOLD = 400


class ProbeOutcome(str, Enum):
    """Clasificación de la corrida, persistida como valor string (D3)."""

    OK = "ok"
    HTTP_ERROR = "http_error"
    TIMEOUT = "timeout"
    CONNECTION_ERROR = "connection_error"


@dataclass(frozen=True)
class ProbeResult:
    """Resultado de una corrida de la sonda (S2).

    `latency_ms` es None cuando no hubo respuesta (timeout, error de conexión):
    no se inventa una latencia que no se pudo medir.
    """

    target_url: str
    timestamp: datetime
    available: bool
    status_code: int | None
    latency_ms: float | None
    outcome: ProbeOutcome


def _utc_now() -> datetime:
    """Timestamp de la corrida con zona explícita (el contrato la exige)."""
    return datetime.now(tz=timezone.utc)


def _latency_ms(started: float) -> float:
    """Milisegundos transcurridos desde `started`, redondeados a microsegundo."""
    return round((time.perf_counter() - started) * 1000.0, 3)


def _without_response(target_url: str, outcome: ProbeOutcome) -> ProbeResult:
    """Corrida sin respuesta: indisponible, sin status ni latencia (S4)."""
    return ProbeResult(
        target_url=target_url,
        timestamp=_utc_now(),
        available=False,
        status_code=None,
        latency_ms=None,
        outcome=outcome,
    )


async def run_probe(
    target_url: str,
    timeout_seconds: float,
    client: httpx.AsyncClient,
) -> ProbeResult:
    """Ejecuta un `GET` contra el target y clasifica el resultado.

    `client` lo provee el llamador (un solo `AsyncClient` compartido por ciclo
    en `python -m probe`), de modo que la sonda no abre conexiones propias.

    La latencia se toma al recibir la respuesta (headers), antes de cualquier
    lectura del body: es TTFB, no tiempo total de descarga (R3-002, R4-001).
    """
    started = time.perf_counter()
    try:
        async with client.stream("GET", target_url, timeout=timeout_seconds) as response:
            latency_ms = _latency_ms(started)
            status_code = response.status_code
    except httpx.TimeoutException:
        # Antes que TransportError: TimeoutException es su subclase.
        return _without_response(target_url, ProbeOutcome.TIMEOUT)
    except httpx.TransportError:
        # DNS/TCP/rechazo de conexión: también es indisponibilidad (S4).
        return _without_response(target_url, ProbeOutcome.CONNECTION_ERROR)

    available = status_code < UNAVAILABLE_STATUS_THRESHOLD
    return ProbeResult(
        target_url=target_url,
        timestamp=_utc_now(),
        available=available,
        status_code=status_code,
        latency_ms=latency_ms,
        outcome=ProbeOutcome.OK if available else ProbeOutcome.HTTP_ERROR,
    )
