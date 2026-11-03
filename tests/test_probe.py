"""Tests de la sonda HTTP de disponibilidad (ISS-B-13, B.13).

Cubren las cinco specs del issue #73:
- S1: corrida programada a intervalo configurable desde un solo origen.
- S2: registro de disponibilidad, código de estado y latencia por ejecución.
- S3: los datos salen por el mismo camino de ingesta RUM (`RumEventBatch`
  validado por la política real, no por un mock del contrato).
- S4: timeout y error de conexión se registran como indisponibilidad explícita.
- S5: la evidencia de ejecución real se toma fuera de la suite (ver feature
  doc); acá se fija el comportamiento determinista.

El transporte HTTP se inyecta (`httpx.MockTransport`): la sonda no abre red en
los tests y los casos de error son reproducibles.
"""

import json
from datetime import datetime
from uuid import UUID

import httpx
import pytest

from api.domain.services.ingest_policy import validate_rum_event
from probe.config import ProbeSettings
from probe.ingest import build_batch, send_batch
from probe.runner import ProbeOutcome, run_probe
from probe.scheduler import ProbeScheduler

TARGET = "https://piloto.example.com/health"
API_KEY = "ilp_test_probe_key"
APP_ID = "8f14e45f-ceea-467a-9a3c-1c9b1dbb1f2a"
SESSION_ID = "1f0d5c1e-3c1a-4d3a-9d4e-6a2b8c7d5e01"


def _settings(**overrides) -> ProbeSettings:
    """Settings de la sonda con target y API key inyectados por test."""
    base = {
        "probe_target_url": TARGET,
        "probe_api_key": API_KEY,
        "ingest_base_url": "http://api.test",
    }
    base.update(overrides)
    return ProbeSettings(**base)


def _client(handler) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


# -- S2/S4: la corrida clasifica disponibilidad, status y latencia -----------


async def test_run_probe_records_availability_status_and_latency():
    """S2: una respuesta 200 registra disponible=True, el status code y una
    latencia medible."""
    async with _client(lambda request: httpx.Response(200, text="ok")) as client:
        result = await run_probe(TARGET, timeout_seconds=5.0, client=client)

    assert request_was_single_origin(result, TARGET)
    assert result.available is True
    assert result.status_code == 200
    assert result.outcome is ProbeOutcome.OK
    assert result.latency_ms is not None and result.latency_ms >= 0
    assert isinstance(result.timestamp, datetime)


def request_was_single_origin(result, target) -> bool:
    """S1: la corrida registra el origen único contra el que midió."""
    return result.target_url == target


async def test_run_probe_marks_http_error_response_as_unavailable():
    """S2/S4: un 5xx es servicio no disponible, con su status code registrado."""
    async with _client(lambda request: httpx.Response(503)) as client:
        result = await run_probe(TARGET, timeout_seconds=5.0, client=client)

    assert result.available is False
    assert result.status_code == 503
    assert result.outcome is ProbeOutcome.HTTP_ERROR
    assert result.latency_ms is not None


async def test_run_probe_marks_timeout_as_unavailable():
    """S4: el timeout es indisponibilidad explícita, no una excepción que
    escape ni una corrida perdida."""

    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("timeout", request=request)

    async with _client(handler) as client:
        result = await run_probe(TARGET, timeout_seconds=0.5, client=client)

    assert result.available is False
    assert result.status_code is None
    assert result.latency_ms is None
    assert result.outcome is ProbeOutcome.TIMEOUT


async def test_run_probe_marks_connection_error_as_unavailable():
    """S4: un error de conexión (DNS/TCP/rechazo) también es indisponibilidad."""

    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    async with _client(handler) as client:
        result = await run_probe(TARGET, timeout_seconds=1.0, client=client)

    assert result.available is False
    assert result.status_code is None
    assert result.outcome is ProbeOutcome.CONNECTION_ERROR


# -- S2/S3: el payload sale por el camino de ingesta y lo acepta el contrato --


async def test_build_batch_emits_availability_metric_accepted_by_policy():
    """S2/S3: el batch de la sonda es un `RumEventBatch` que la política real
    de ingesta acepta, con AVAILABILITY (1, count) y el status en metadata."""
    async with _client(lambda request: httpx.Response(200)) as client:
        result = await run_probe(TARGET, timeout_seconds=5.0, client=client)

    payload = build_batch(result, api_key=API_KEY, session_id=SESSION_ID, application_id=APP_ID)

    assert payload["schema_version"] == "1.0"
    event = payload["events"][0]
    assert validate_rum_event(event) is None

    metrics = {metric["type"]: metric for metric in event["metrics"]}
    assert metrics["AVAILABILITY"]["value"] == 1
    assert metrics["AVAILABILITY"]["unit"] == "count"
    metadata = metrics["AVAILABILITY"]["metadata"]
    assert metadata["http_status"] == 200
    assert metadata["probe_target"] == TARGET
    assert metadata["outcome"] == "ok"
    assert metadata["latency_ms"] is not None
    # La latencia de la sonda es un TTFB: mismo tipo y unidad que el RUM.
    assert metrics["TTFB"]["unit"] == "ms"


async def test_build_batch_omits_ttfb_when_unavailable_without_response():
    """S4: sin respuesta no hay latencia que inventar: se registra solo
    AVAILABILITY=0, y el evento sigue siendo válido para la política."""

    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("timeout", request=request)

    async with _client(handler) as client:
        result = await run_probe(TARGET, timeout_seconds=0.5, client=client)

    payload = build_batch(result, api_key=API_KEY, session_id=SESSION_ID, application_id=None)
    event = payload["events"][0]

    assert validate_rum_event(event) is None
    assert [metric["type"] for metric in event["metrics"]] == ["AVAILABILITY"]
    assert event["metrics"][0]["value"] == 0
    assert event["metrics"][0]["metadata"]["http_status"] is None
    assert event["metrics"][0]["metadata"]["outcome"] == "timeout"


async def test_build_batch_uses_stable_synthetic_session_id():
    """D4: sin `session_id` explícito la sonda deriva uno estable del target,
    para no inventar cardinalidad de sesiones en cada corrida."""
    async with _client(lambda request: httpx.Response(200)) as client:
        result = await run_probe(TARGET, timeout_seconds=5.0, client=client)

    first = build_batch(result, api_key=API_KEY, session_id=None, application_id=None)
    second = build_batch(result, api_key=API_KEY, session_id=None, application_id=None)

    session_id = first["events"][0]["session_id"]
    assert session_id == second["events"][0]["session_id"]
    assert UUID(session_id)  # es UUID válido para la política


async def test_synthetic_session_id_is_scoped_by_tenant():
    """R1-001/R3-001/R4-005: dos tenants que miden el MISMO target NO pueden
    compartir sesión. `session_id` es la PK de `user_session` y la dueña es la
    aplicación: compartirla atribuiría (o descartaría) las métricas del otro
    tenant."""
    async with _client(lambda request: httpx.Response(200)) as client:
        result = await run_probe(TARGET, timeout_seconds=5.0, client=client)

    tenant_a = build_batch(result, api_key="ilp_tenant_a", session_id=None)
    tenant_b = build_batch(result, api_key="ilp_tenant_b", session_id=None)

    assert (
        tenant_a["events"][0]["session_id"]
        != tenant_b["events"][0]["session_id"]
    )
    # El mismo tenant conserva la sesión: es estable, no aleatoria.
    again = build_batch(result, api_key="ilp_tenant_a", session_id=None)
    assert again["events"][0]["session_id"] == tenant_a["events"][0]["session_id"]
    # La API key no queda codificada en el identificador persistido.
    assert "ilp_tenant_a" not in tenant_a["events"][0]["session_id"]


async def test_send_batch_posts_through_telemetry_endpoint():
    """S3: el envío usa `POST /telemetry/metrics` con la API key del tenant y
    devuelve el status de la ingesta (202 en el camino feliz)."""
    seen: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["api_key"] = request.headers.get("X-API-Key")
        seen["body"] = json.loads(request.content)
        return httpx.Response(202, json={"batch_id": "b-1", "accepted": 1, "rejected": []})

    async with _client(lambda request: httpx.Response(200)) as probe_client:
        result = await run_probe(TARGET, timeout_seconds=5.0, client=probe_client)
    payload = build_batch(result, api_key=API_KEY, session_id=SESSION_ID, application_id=APP_ID)

    async with _client(handler) as client:
        status_code = await send_batch(
            base_url="http://api.test",
            api_key=API_KEY,
            payload=payload,
            client=client,
        )

    assert status_code == 202
    assert seen["url"] == "http://api.test/telemetry/metrics"
    assert seen["api_key"] == API_KEY
    assert seen["body"] == payload


# -- S1: intervalo configurable ---------------------------------------------


async def test_run_probe_measures_ttfb_without_reading_the_body():
    """R3-002/R4-001: la latencia es TTFB. Leer el body mediría la descarga
    completa —y podría declarar `timeout` a un sitio que está arriba— además de
    materializar en memoria una respuesta que la sonda no usa."""
    reads: list[int] = []

    class _TrackingBody(httpx.AsyncByteStream):
        async def __aiter__(self):
            reads.append(1)
            yield b"cuerpo que la sonda no debe leer"

    async with _client(
        lambda request: httpx.Response(200, stream=_TrackingBody())
    ) as client:
        result = await run_probe(TARGET, timeout_seconds=5.0, client=client)

    assert result.available is True
    assert result.status_code == 200
    assert result.latency_ms is not None
    assert reads == []  # el body nunca se iteró


async def test_send_batch_always_applies_a_finite_timeout():
    """R3-003: el envío a la ingesta NUNCA sale sin timeout. Sin él, una
    ingesta que no responde cuelga el ciclo y el intervalo deja de correr."""
    seen: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["timeout"] = request.extensions.get("timeout")
        return httpx.Response(202, json={"batch_id": "b-1", "accepted": 1})

    async with _client(handler) as client:
        await send_batch(
            base_url="http://api.test",
            api_key=API_KEY,
            payload={"schema_version": "1.0", "events": []},
            client=client,
        )

    timeout = seen["timeout"]
    assert timeout is not None
    assert any(value and value > 0 for value in timeout.values())


async def test_scheduler_uses_configured_interval():
    """S1: el intervalo es configurable y la corrida es periódica: con un
    intervalo corto se ejecutan varias corridas, y el intervalo configurado es
    el que se usa entre corridas."""
    runs: list[int] = []

    async def fake_cycle() -> None:
        runs.append(1)

    scheduler = ProbeScheduler(interval_seconds=0.01, cycle=fake_cycle)
    await scheduler.run(max_cycles=3)

    assert len(runs) == 3
    assert scheduler.interval_seconds == 0.01


def test_settings_reject_non_positive_interval():
    """S1: un intervalo no positivo es configuración inválida, no un bucle
    infinito sin pausa."""
    with pytest.raises(ValueError):
        _settings(probe_interval_seconds=0)
    with pytest.raises(ValueError):
        _settings(probe_interval_seconds=-5)


def test_settings_require_target_and_api_key():
    """S1/D4: sin target ni API key la sonda no tiene origen ni tenant: falla
    al construir la configuración, no en la primera corrida."""
    with pytest.raises(ValueError):
        ProbeSettings(probe_api_key=API_KEY)
    with pytest.raises(ValueError):
        ProbeSettings(probe_target_url=TARGET)
