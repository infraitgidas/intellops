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
import logging
from contextlib import contextmanager
from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import UUID

import httpx
import pytest

import probe.__main__ as probe_main
import probe.scheduler as scheduler_module
from api.domain.services.ingest_policy import validate_rum_event
from probe.config import ProbeSettings
from probe.ingest import build_batch, sanitize_target_url, send_batch
from probe.runner import ProbeOutcome, ProbeResult, run_probe
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


def test_probe_latency_above_ttfb_cap_keeps_availability_record():
    """B.13/S2: un TTFB sobre el tope de cordura NO puede descartar el registro
    de disponibilidad: el evento sigue siendo válido para la política."""
    result = ProbeResult(target_url=TARGET, timestamp=datetime.now(timezone.utc),
                         available=True, status_code=200, latency_ms=70_000.0,
                         outcome=ProbeOutcome.OK)
    payload = build_batch(result, api_key=API_KEY)
    event = payload["events"][0]
    assert validate_rum_event(event) is None
    metrics = {m["type"]: m for m in event["metrics"]}
    assert metrics["AVAILABILITY"]["value"] == 1
    assert "TTFB" not in metrics          # fuera de rango: no se envía
    assert metrics["AVAILABILITY"]["metadata"]["latency_ms"] == 70_000.0


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


async def test_send_batch_logs_rejection_reasons_from_response():
    """S2/S3: un 202 no es "todo bien". Si la ingesta aceptó 0 eventos, el
    ciclo tiene que registrar la cantidad aceptada y la razón del rechazo: un
    log con solo `ingest_status=202` esconde la pérdida de datos.

    La captura usa un handler propio del logger `probe.ingest` en vez de
    `caplog`: el root logger cambia cuando otros módulos de la suite se
    importan (la app configura logging), y este test no puede depender de eso.
    """
    records: list[logging.LogRecord] = []

    class _Collector(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            records.append(record)

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            202,
            json={
                "batch_id": "b-2",
                "accepted": 0,
                "rejected": [{"index": 0, "reason": "invalid_range"}],
            },
        )

    ingest_logger = logging.getLogger("probe.ingest")
    collector = _Collector()
    # Nivel y `disabled` explícitos: otros tests de la suite reconfiguran
    # logging con `disable_existing_loggers`, que apaga este logger y hace que
    # el registro ni se cree. Sin esto el test miente.
    previous_level = ingest_logger.level
    previous_disabled = ingest_logger.disabled
    ingest_logger.setLevel(logging.INFO)
    ingest_logger.disabled = False
    ingest_logger.addHandler(collector)
    try:
        async with _client(handler) as client:
            status_code = await send_batch(
                base_url="http://api.test",
                api_key=API_KEY,
                payload={"schema_version": "1.0", "events": [{"x": 1}]},
                client=client,
            )
    finally:
        ingest_logger.removeHandler(collector)
        ingest_logger.setLevel(previous_level)
        ingest_logger.disabled = previous_disabled

    assert status_code == 202  # el contrato de retorno no cambia
    messages = [record.getMessage() for record in records]
    assert any("invalid_range" in message for message in messages)
    assert any("accepted=0" in message for message in messages)


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


def test_settings_reject_non_uuid_application_id():
    """S2: un `PROBE_APPLICATION_ID` que no es UUID hace que la política
    rechace el evento completo (`invalid_uuid`) y la corrida se pierda en
    silencio cada ciclo. Se rechaza al construir, no en la primera corrida."""
    with pytest.raises(ValueError):
        _settings(probe_application_id="piloto")

    settings = _settings(probe_application_id=APP_ID)
    assert settings.probe_application_id == APP_ID


def test_settings_require_target_and_api_key():
    """S1/D4: sin target ni API key la sonda no tiene origen ni tenant: falla
    al construir la configuración, no en la primera corrida."""
    with pytest.raises(ValueError):
        ProbeSettings(probe_api_key=API_KEY)
    with pytest.raises(ValueError):
        ProbeSettings(probe_target_url=TARGET)


# -- Correcciones de review de la PR #88 (comentario de RomeKai) -------------


@contextmanager
def _captured_logs(logger_name: str):
    """Registros de un logger propio, inmune a la reconfiguración global de
    logging que hacen otros módulos de la suite (mismo criterio que el test de
    razones de rechazo: nivel y `disabled` explícitos)."""
    records: list[logging.LogRecord] = []

    class _Collector(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            records.append(record)

    target = logging.getLogger(logger_name)
    collector = _Collector()
    previous_level = target.level
    previous_disabled = target.disabled
    target.setLevel(logging.INFO)
    target.disabled = False
    target.addHandler(collector)
    try:
        yield records
    finally:
        target.removeHandler(collector)
        target.setLevel(previous_level)
        target.disabled = previous_disabled


async def test_send_batch_logs_warning_when_ingest_status_is_not_2xx():
    """Review 3: un 401 (API key mala) o un 422 NO pueden loguearse como INFO
    con `accepted=unknown`: una sonda mal configurada parecería sana mientras
    no manda nada. Todo status no-2xx se registra como WARNING; un 2xx sin
    cuerpo parseable sigue siendo INFO."""
    payload = {"schema_version": "1.0", "events": [{"x": 1}]}

    with _captured_logs("probe.ingest") as records:
        async with _client(
            lambda request: httpx.Response(401, json={"detail": "invalid api key"})
        ) as client:
            await send_batch(
                base_url="http://api.test", api_key=API_KEY, payload=payload, client=client
            )
    warnings = [r for r in records if r.levelno == logging.WARNING]
    assert any("accepted=unknown" in r.getMessage() for r in warnings)

    with _captured_logs("probe.ingest") as records:
        async with _client(
            lambda request: httpx.Response(200, text="no es json")
        ) as client:
            await send_batch(
                base_url="http://api.test", api_key=API_KEY, payload=payload, client=client
            )
    assert [r for r in records if r.levelno >= logging.WARNING] == []


async def test_serve_survives_unexpected_cycle_error(monkeypatch):
    """Review 4: `cycle()` no puede atrapar solo `httpx.HTTPError`. Cualquier
    otra excepción (por ejemplo, de `build_batch`) mataba el proceso y no hay
    política de reinicio: el error se registra y el próximo ciclo reintenta."""
    attempts: list[int] = []

    async def flaky_run_cycle(settings, client):
        attempts.append(1)
        if len(attempts) == 1:
            raise ValueError("build_batch explotó")

    class _TwoCycles:
        """Scheduler acotado: dos ciclos y termina, para no correr infinito."""

        def __init__(self, interval_seconds, cycle):
            self._cycle = cycle

        async def run(self):
            await self._cycle()
            await self._cycle()

    monkeypatch.setattr(probe_main, "run_cycle", flaky_run_cycle)
    monkeypatch.setattr(probe_main, "ProbeScheduler", _TwoCycles)

    await probe_main._serve(_settings())

    assert len(attempts) == 2  # la excepción no mató el proceso


class _FakeClock:
    """Reloj monotónico determinista para el scheduler (sin sleeps reales)."""

    def __init__(self) -> None:
        self.now = 0.0

    def monotonic(self) -> float:
        return self.now


async def test_scheduler_compensates_cycle_duration(monkeypatch):
    """Review 5: el período real es `interval_seconds`, NO intervalo +
    duración del ciclo. Con buckets de 60 s, la deriva dejaba buckets con 0
    muestras y otros con 2. La espera es el intervalo menos lo que duró el
    ciclo, anclada al reloj monotónico."""
    clock = _FakeClock()
    sleeps: list[float] = []

    async def fake_sleep(seconds: float) -> None:
        sleeps.append(seconds)
        clock.now += max(0.0, seconds)

    async def cycle() -> None:
        clock.now += 0.03  # el ciclo dura 30 ms

    # `raising=False`: el reloj se inyecta aunque el scheduler viejo no lo use.
    monkeypatch.setattr(
        scheduler_module, "time", SimpleNamespace(monotonic=clock.monotonic), raising=False
    )
    monkeypatch.setattr(scheduler_module, "asyncio", SimpleNamespace(sleep=fake_sleep))

    await ProbeScheduler(interval_seconds=0.05, cycle=cycle).run(max_cycles=3)

    assert sleeps == pytest.approx([0.02, 0.02])  # 50 ms - 30 ms, sin deriva


async def test_scheduler_never_sleeps_negative_when_cycle_overruns(monkeypatch):
    """Review 5: si un ciclo dura más que el intervalo, la espera se recorta a
    cero (nunca negativa) y el próximo ciclo arranca de inmediato."""
    clock = _FakeClock()
    sleeps: list[float] = []

    async def fake_sleep(seconds: float) -> None:
        sleeps.append(seconds)
        clock.now += max(0.0, seconds)

    async def cycle() -> None:
        clock.now += 0.07  # el ciclo dura más que el intervalo de 50 ms

    monkeypatch.setattr(
        scheduler_module, "time", SimpleNamespace(monotonic=clock.monotonic), raising=False
    )
    monkeypatch.setattr(scheduler_module, "asyncio", SimpleNamespace(sleep=fake_sleep))

    await ProbeScheduler(interval_seconds=0.05, cycle=cycle).run(max_cycles=3)

    assert sleeps == [0.0, 0.0]


def test_build_batch_strips_secrets_from_probe_target_metadata():
    """Review 6: `probe_target` se persiste y se expone por el read path. La
    URL cruda puede traer un token en el query string (o credenciales en el
    userinfo): se guarda saneada, sin query, fragmento ni userinfo."""
    result = ProbeResult(
        target_url="https://user:pass@piloto.example.com/health?token=secreto&x=1#frag",
        timestamp=datetime.now(timezone.utc),
        available=True,
        status_code=200,
        latency_ms=10.0,
        outcome=ProbeOutcome.OK,
    )
    payload = build_batch(result, api_key=API_KEY)

    metadata = payload["events"][0]["metrics"][0]["metadata"]
    assert metadata["probe_target"] == "https://piloto.example.com/health"
    serialized = json.dumps(payload)
    assert "secreto" not in serialized
    assert "user:pass" not in serialized


def test_build_batch_sanitizes_even_unparseable_target():
    """Review 6: aunque la URL no se pueda parsear, el query string no se
    persiste (fallback defensivo, nunca la URL cruda)."""
    result = ProbeResult(
        target_url="https://piloto.example.com:bad/health?token=secreto",
        timestamp=datetime.now(timezone.utc),
        available=True,
        status_code=200,
        latency_ms=10.0,
        outcome=ProbeOutcome.OK,
    )
    payload = build_batch(result, api_key=API_KEY)

    metadata = payload["events"][0]["metrics"][0]["metadata"]
    assert "secreto" not in json.dumps(payload)
    assert metadata["probe_target"].endswith("/health")


def test_cycle_log_does_not_leak_url_secrets():
    """Review 6: el log del ciclo también persiste el target en cada corrida;
    usa el mismo saneo que la metadata para no filtrar el token por otro
    camino."""
    result = ProbeResult(
        target_url="https://piloto.example.com/health?token=secreto",
        timestamp=datetime.now(timezone.utc),
        available=True,
        status_code=200,
        latency_ms=10.0,
        outcome=ProbeOutcome.OK,
    )
    with _captured_logs("probe.__main__") as records:
        probe_main._log_result(result, 202)

    assert records, "el ciclo tiene que registrar su resultado"
    assert "secreto" not in records[0].getMessage()


# -- Hallazgos informativos de la review nativa (R1-R4) ----------------------


def test_sanitize_target_url_strips_userinfo_when_unparseable():
    """R1-002/R2-003/R3-002/R4-002: el fallback del saneo (URL que `urlsplit`
    no entiende) NO puede ser más débil que el camino principal. `https://
    user:pass@host:bad/path?token=x` entra por el fallback y antes conservaba
    `user:pass@`: las credenciales quedaban persistidas, que es exactamente lo
    que la función existe para impedir."""
    sanitized = sanitize_target_url(
        "https://user:pass@piloto.example.com:bad/health?token=secreto#frag"
    )

    assert "secreto" not in sanitized
    assert "user:pass" not in sanitized
    assert sanitized.endswith("/health")


def test_sanitize_target_url_strips_userinfo_in_the_main_path():
    """R1-002: el camino principal quita el userinfo, y el resultado no tiene
    query, fragmento ni credenciales."""
    sanitized = sanitize_target_url(
        "https://user:pass@piloto.example.com/health?token=secreto#frag"
    )

    assert sanitized == "https://piloto.example.com/health"


def test_sanitize_target_url_strips_userinfo_before_query_in_fallback():
    """R1-002: en el fallback el userinfo se quita PRIMERO. Recortar el query
    antes parte el userinfo: `user:pa?ss@host/p` quedaba como `https://user:pa`,
    o sea un pedazo de la contraseña persistido."""
    for raw in (
        "https://user:pa?ss@piloto.example.com:bad/health",
        "https://user:pa#ss@piloto.example.com:bad/health",
    ):
        sanitized = sanitize_target_url(raw)
        assert "pa" not in sanitized, sanitized
        assert sanitized == "https://piloto.example.com:bad/health"


def test_sanitize_target_url_keeps_ipv6_brackets():
    """R1-002: `hostname` viene sin corchetes y `urlunsplit` no los repone: un
    target IPv6 se persistía como `https://::1:8080/p`, que no es una URL."""
    assert (
        sanitize_target_url("https://[::1]:8080/health?token=secreto")
        == "https://[::1]:8080/health"
    )


def test_settings_reject_url_without_host():
    """R4-001/R3-003: validar solo el prefijo deja pasar `http://`, que no es
    una URL medible: la sonda arranca y pierde cada corrida con
    `connection_error` en vez de fallar al construir, que es donde se puede
    corregir."""
    for value in ("http://", "https://", "http:///health", "https:// "):
        with pytest.raises(ValueError):
            _settings(probe_target_url=value)
        with pytest.raises(ValueError):
            _settings(ingest_base_url=value)

    # Un host válido (con o sin puerto, con o sin path) sigue aceptándose.
    for value in ("http://localhost:8000", "https://piloto.example.com/health"):
        assert _settings(probe_target_url=value).probe_target_url == value


def test_startup_log_does_not_leak_ingest_credentials():
    """R1-003: el log de arranque saneaba el target pero no `ingest_base_url`,
    que también es una URL configurable y puede traer credenciales en el
    userinfo o un token en el query string."""
    settings = _settings(
        ingest_base_url="https://user:pass@api.example.com/?token=secreto"
    )
    with _captured_logs("probe.__main__") as records:
        probe_main._log_startup(settings)

    assert records, "el arranque tiene que registrar su configuración"
    message = records[0].getMessage()
    assert "secreto" not in message
    assert "user:pass" not in message


async def test_cycle_logs_the_measurement_even_when_ingest_send_fails(monkeypatch):
    """R4-003: si el envío a la ingesta falla, la corrida YA se midió. Antes
    `send_batch` lanzaba antes de `_log_result` y la medición no quedaba
    registrada en ningún lado: el ciclo sobrevivía, pero la evidencia se
    perdía."""

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/telemetry/metrics":
            raise httpx.ConnectError("ingesta caída", request=request)
        return httpx.Response(200)

    with _captured_logs("probe.__main__") as records:
        async with _client(handler) as client:
            with pytest.raises(httpx.ConnectError):
                await probe_main.run_cycle(_settings(), client)

    messages = [r.getMessage() for r in records]
    assert any(
        "outcome=ok" in m and "ingest_status=" in m for m in messages
    ), f"la medición se perdió: {messages}"


# -- Hallazgos de la segunda review nativa (review-e7da28ac) ------------------


async def test_scheduler_resyncs_after_an_overrunning_cycle(monkeypatch):
    """R3-001/R4-001: si un ciclo se pasa del intervalo, el reloj se
    resincroniza. Sin eso `next_tick` queda atrás y la espera se vuelve 0 para
    siempre: un bucle sin pausa en vez de recuperar el ritmo."""
    clock = _FakeClock()
    sleeps: list[float] = []
    durations = iter([0.07, 0.01, 0.01])  # el primero dura MÁS que el intervalo

    async def fake_sleep(seconds: float) -> None:
        sleeps.append(seconds)
        clock.now += max(0.0, seconds)

    async def cycle() -> None:
        clock.now += next(durations, 0.01)

    monkeypatch.setattr(
        scheduler_module, "time", SimpleNamespace(monotonic=clock.monotonic), raising=False
    )
    monkeypatch.setattr(scheduler_module, "asyncio", SimpleNamespace(sleep=fake_sleep))

    await ProbeScheduler(interval_seconds=0.05, cycle=cycle).run(max_cycles=3)

    # Tras el desborde la espera es 0 (arranca ya) y después un intervalo
    # COMPLETO: el atraso no se arrastra.
    assert sleeps == pytest.approx([0.0, 0.04])


def test_sanitize_target_url_keeps_at_sign_that_is_not_userinfo():
    """R2-001/R3-004: sin `esquema://` no hay authority, así que un `@` es parte
    del path y recortarlo lo mutila (`host.com/user@example.com/p` quedaba como
    `example.com/p`). Scheme-relative SÍ tiene authority: ahí se quita."""
    assert (
        sanitize_target_url("host.com/user@example.com/p?t=1")
        == "host.com/user@example.com/p"
    )
    assert sanitize_target_url("//user:pass@host.com/p?t=1") == "//host.com/p"


def test_settings_reject_unknown_keys(monkeypatch):
    """R4-003: `extra="ignore"` se tragaba los typos de configuración:
    `PROBE_INTERVAL_SECOND` (sin la S final) dejaba la sonda corriendo con el
    intervalo por defecto, sin ningún aviso."""
    monkeypatch.setenv("PROBE_INTERVAL_SECOND", "30")
    with pytest.raises(ValueError):
        ProbeSettings(probe_target_url=TARGET, probe_api_key=API_KEY)

    # Un kwarg desconocido explícito tampoco puede pasar en silencio.
    with pytest.raises(ValueError):
        _settings(prob_interval_seconds=30)


async def test_send_batch_builds_the_url_from_the_base_path_only():
    """R3-002: `base_url.rstrip('/')` pegaba el path de ingesta detrás del query
    del base: `http://api.test/?x=1` producía
    `http://api.test/?x=1/telemetry/metrics`, una URL que no existe."""
    seen: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        return httpx.Response(202, json={"accepted": 1})

    async with _client(handler) as client:
        await send_batch(
            base_url="http://api.test/v1/?token=x",
            api_key=API_KEY,
            payload={"schema_version": "1.0", "events": []},
            client=client,
        )

    # El path base se conserva; el query y el fragmento no contaminan.
    assert seen["url"] == "http://api.test/v1/telemetry/metrics"


def test_main_reads_settings_through_the_cached_accessor(monkeypatch):
    """R2-003: `get_probe_settings` decía ser el singleton del proceso y
    `main()` lo saltaba construyendo otro `ProbeSettings` aparte."""
    used: list[int] = []

    def fake_settings() -> ProbeSettings:
        used.append(1)
        return _settings()

    async def noop_serve(settings: ProbeSettings) -> None:
        return None

    monkeypatch.setattr(probe_main, "_serve", noop_serve)
    monkeypatch.setattr(probe_main, "get_probe_settings", fake_settings, raising=False)

    probe_main.main()

    assert used == [1]
