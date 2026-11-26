"""TDD del despachador de alertas de `intellops-comms` (ISS-B-10).

Sin Postgres: el `Dispatcher` recibe el repositorio y los proveedores por
inyección, así que la decisión (routing por severidad, backoff, transiciones
a Sent/Failed y el canal sin credenciales) se prueba con dobles. Los
proveedores reales se prueban acá mismo con un transporte falso
(`httpx.MockTransport` y un `smtplib.SMTP` falso): ningún test sale a la red.

Formatos fijados (spec ISS-B-10):

- `critical`/`high` → Telegram; `medium`/`low` → Email, configurable por env
  (OAS-B10-1, design §2).
- Un destino por canal, tomado del entorno y persistido en
  `alert.recipient` (OAS-B10-2, CD-5).
- Backoff exponencial: 4 intentos, base 1 s, factor 2 → esperas 1, 2, 4 s,
  con presupuesto total acotado (CD-3, design §4).
- Telegram 400/403 y SMTP 5xx son permanentes: van a Failed sin reintento
  (CD-4).
- Éxito → `Sent` + `sent_at`; intentos agotados → `Failed` con `sent_at`
  NULL (CD-5, design §5).
- Un canal sin destino configurado NO es un fallo: la alerta queda Pending,
  se loguea una vez con el nombre del canal y el ciclo no levanta
  (OAS-B10-2, design §6).
- Los logs nombran id de alerta, canal e intento; nunca el mensaje ni el
  destino (OAS-B10-4, design §7).
"""

import json
import logging
import smtplib
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import httpx
import pytest
from pydantic import ValidationError
import comms.providers as providers_module
from comms.config import CommsSettings
from comms.dispatcher import (
    CycleSummary,
    Dispatcher,
    PendingAlert,
    PermanentDeliveryError,
    RetryPolicy,
    TransientDeliveryError,
)
from comms.entrypoint import build_providers
from comms.providers import EmailProvider, TelegramProvider
from comms.scheduler import CommsScheduler

NOW = datetime(2026, 11, 18, 12, 0, tzinfo=timezone.utc)
APP_ID = UUID("8f14e45f-ceea-467a-9a3c-1c9b1dbb1f2a")
CHAT_ID = "424242"
MAILBOX = "guardia@example.test"
BOT_TOKEN = "123456:the-bot-token"
# Stub local de la Bot API del smoke E2E (ISS-C-01, E2E-1).
API_BASE_VAR = "INTELLOPS_COMMS_TELEGRAM_API_BASE"
STUB_API_BASE = "http://host.docker.internal:8099"
ROUTING = {
    "critical": "telegram",
    "high": "telegram",
    "medium": "email",
    "low": "email",
}


@pytest.fixture(autouse=True)
def _enable_comms_logger():
    """Reactiva el logger del worker para los tests que lo inspeccionan.

    `alembic upgrade head` (fixture de sesión, para los tests de integración)
    corre `logging.config.fileConfig`, que por defecto desactiva los loggers
    ya creados: al correr la suite completa el logger del worker quedaría con
    `disabled = True`. Es un artefacto del harness (en runtime el worker no
    corre migraciones), no del código, así que el test lo reactiva.
    """
    logger = logging.getLogger("intellops-comms")
    logger.disabled = False
    yield
    logger.disabled = False


# -- Dobles ---------------------------------------------------------------


def _alert(severity: str = "high", *, created_at: datetime | None = None) -> PendingAlert:
    """Alerta tal como la deja el motor de reglas: Pending y sin canal."""
    return PendingAlert(
        alert_id=uuid4(),
        application_id=APP_ID,
        severity=severity,
        message=f"TTFB p95 995,0 ms supera el umbral de 800,0 ms ({severity}).",
        created_at=created_at or NOW - timedelta(minutes=1),
    )


@dataclass
class FakeProvider:
    """Proveedor con una cola de resultados por intento."""

    name: str
    destination: str
    outcomes: list[str] = field(default_factory=lambda: ["ok"])
    attempts: list[PendingAlert] = field(default_factory=list)

    async def send(self, alert: PendingAlert) -> None:
        self.attempts.append(alert)
        outcome = self.outcomes.pop(0) if len(self.outcomes) > 1 else self.outcomes[0]
        if outcome == "permanent":
            raise PermanentDeliveryError("provider rejected the message permanently")
        if outcome == "transient":
            raise TransientDeliveryError("provider is temporarily unavailable")
        if outcome == "unexpected":
            raise RuntimeError("unexpected provider failure")
        return None


@dataclass
class FakeCommsRepository:
    """Repositorio en memoria con la misma semántica que el SQL (CD-1)."""

    alerts: list[PendingAlert] = field(default_factory=list)
    claim_calls: list[tuple[list[str], int]] = field(default_factory=list)
    sent: list[tuple[PendingAlert, str, str, datetime]] = field(
        default_factory=list
    )
    failed: list[PendingAlert] = field(default_factory=list)
    failed_deliveries: list[tuple[PendingAlert, str, str]] = field(
        default_factory=list
    )
    status: dict[UUID, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for alert in self.alerts:
            self.status.setdefault(alert.alert_id, "Pending")

    async def claim_pending(
        self, severities: list[str], batch: int
    ) -> list[PendingAlert]:
        """Pending de las severidades pedidas, la más vieja primero (CD-1)."""
        self.claim_calls.append((list(severities), batch))
        pending = [
            alert
            for alert in sorted(self.alerts, key=lambda item: item.created_at)
            if self.status[alert.alert_id] == "Pending"
            and alert.severity in severities
        ]
        return pending[:batch]

    async def mark_sent(
        self,
        alert: PendingAlert,
        *,
        channel: str,
        recipient: str,
        sent_at: datetime,
    ) -> None:
        self.status[alert.alert_id] = "Sent"
        self.sent.append((alert, channel, recipient, sent_at))

    async def mark_failed(
        self, alert: PendingAlert, *, channel: str, recipient: str
    ) -> None:
        self.status[alert.alert_id] = "Failed"
        self.failed.append(alert)
        self.failed_deliveries.append((alert, channel, recipient))


class FakeClock:
    """Reloj manual: `sleep` avanza el monotónico como el tiempo real."""

    def __init__(self, start: datetime = NOW) -> None:
        self.current = start
        self.elapsed = 0.0
        self.delays: list[float] = []

    def now(self) -> datetime:
        return self.current

    def monotonic(self) -> float:
        return self.elapsed

    async def sleep(self, delay: float) -> None:
        self.delays.append(delay)
        self.elapsed += delay
        self.current += timedelta(seconds=delay)


def _dispatcher(
    repository: FakeCommsRepository,
    providers: dict[str, FakeProvider],
    *,
    policy: RetryPolicy | None = None,
    routing: dict[str, str] | None = None,
    batch_size: int = 20,
    clock: FakeClock | None = None,
    notified_channels: set[str] | None = None,
) -> Dispatcher:
    clock = clock or FakeClock()
    return Dispatcher(
        repository,
        providers,
        routing or ROUTING,
        policy or RetryPolicy(),
        batch_size=batch_size,
        now=clock.now,
        monotonic=clock.monotonic,
        sleep=clock.sleep,
        notified_channels=notified_channels,
    )


# -- CD-2: routing por severidad ------------------------------------------


async def test_routing_sends_each_severity_to_its_default_channel():
    """GIVEN una alerta de cada severidad WHEN corre el ciclo THEN critical y
    high salen por Telegram, medium y low por Email (OAS-B10-1, CD-2)."""
    repository = FakeCommsRepository(
        alerts=[_alert(severity) for severity in ("critical", "high", "medium", "low")]
    )
    telegram = FakeProvider(name="telegram", destination=CHAT_ID)
    email = FakeProvider(name="email", destination=MAILBOX)

    summary = await _dispatcher(
        repository, {"telegram": telegram, "email": email}
    ).run_cycle()

    assert summary == CycleSummary(claimed=4, sent=4, failed=0)
    assert {alert.severity for alert in telegram.attempts} == {"critical", "high"}
    assert {alert.severity for alert in email.attempts} == {"medium", "low"}
    by_channel = {
        channel: recipient for _, channel, recipient, _ in repository.sent
    }
    assert by_channel == {"telegram": CHAT_ID, "email": MAILBOX}


async def test_routing_is_configurable_per_severity():
    """GIVEN un routing que manda critical a Email WHEN corre el ciclo THEN
    esa severidad sale por Email (OAS-B10-1: configurable por env)."""
    repository = FakeCommsRepository(alerts=[_alert("critical")])
    telegram = FakeProvider(name="telegram", destination=CHAT_ID)
    email = FakeProvider(name="email", destination=MAILBOX)
    routing = dict(ROUTING, critical="email")

    await _dispatcher(
        repository, {"telegram": telegram, "email": email}, routing=routing
    ).run_cycle()

    assert [alert.severity for alert in email.attempts] == ["critical"]
    assert telegram.attempts == []


# -- CD-3/CD-4: retry, backoff y fallos permanentes ------------------------


def test_backoff_sequence_is_exponential_from_the_base():
    """4 intentos, base 1 s y factor 2 → esperas 1, 2, 4 s (CD-3)."""
    assert RetryPolicy().schedule() == (1.0, 2.0, 4.0)
    assert RetryPolicy(attempts=5).schedule() == (1.0, 2.0, 4.0, 8.0)
    assert RetryPolicy(attempts=1).schedule() == ()
    assert RetryPolicy(attempts=3, base_seconds=0.5, factor=3.0).schedule() == (
        0.5,
        1.5,
    )


async def test_transient_failure_is_retried_then_succeeds():
    """GIVEN un envío que falla una vez y luego funciona WHEN corre el ciclo
    THEN hay dos intentos, una espera de 1 s y la alerta queda Sent (CD-3)."""
    alert = _alert("critical")
    repository = FakeCommsRepository(alerts=[alert])
    telegram = FakeProvider(
        name="telegram", destination=CHAT_ID, outcomes=["transient", "ok"]
    )
    clock = FakeClock()

    summary = await _dispatcher(
        repository, {"telegram": telegram}, clock=clock
    ).run_cycle()

    assert summary == CycleSummary(claimed=1, sent=1, failed=0)
    assert len(telegram.attempts) == 2
    assert clock.delays == [1.0]
    assert repository.status[alert.alert_id] == "Sent"


async def test_permanent_failure_goes_to_failed_without_retry():
    """GIVEN un 4xx que el proveedor marca permanente WHEN corre el ciclo
    THEN hay UN intento, sin esperas, y la alerta queda Failed (CD-4)."""
    alert = _alert("critical")
    repository = FakeCommsRepository(alerts=[alert])
    telegram = FakeProvider(
        name="telegram", destination=CHAT_ID, outcomes=["permanent"]
    )
    clock = FakeClock()

    summary = await _dispatcher(
        repository, {"telegram": telegram}, clock=clock
    ).run_cycle()

    assert summary == CycleSummary(claimed=1, sent=0, failed=1)
    assert len(telegram.attempts) == 1
    assert clock.delays == []
    assert repository.status[alert.alert_id] == "Failed"


async def test_exhausted_attempts_mark_failed_and_leave_sent_at_null():
    """GIVEN un proveedor que siempre falla de forma transitoria WHEN corre el
    ciclo THEN son 4 intentos con esperas 1, 2, 4 s y la alerta queda Failed
    con `sent_at` NULL (CD-3, CD-5)."""
    alert = _alert("critical")
    repository = FakeCommsRepository(alerts=[alert])
    telegram = FakeProvider(
        name="telegram", destination=CHAT_ID, outcomes=["transient"]
    )
    clock = FakeClock()

    summary = await _dispatcher(
        repository, {"telegram": telegram}, clock=clock
    ).run_cycle()

    assert summary == CycleSummary(claimed=1, sent=0, failed=1)
    assert len(telegram.attempts) == 4
    assert clock.delays == [1.0, 2.0, 4.0]
    assert repository.status[alert.alert_id] == "Failed"
    assert repository.sent == []
    assert repository.failed == [alert]
    # El canal y el destinatario del intento se persisten: sin ellos una
    # alerta fallida no se puede diagnosticar (CD-5).
    assert repository.failed_deliveries == [(alert, "telegram", CHAT_ID)]


async def test_unexpected_provider_error_is_retried_like_transient():
    """Un error no clasificado no se propaga: se reintenta y termina Failed."""
    alert = _alert("critical")
    repository = FakeCommsRepository(alerts=[alert])
    telegram = FakeProvider(
        name="telegram", destination=CHAT_ID, outcomes=["unexpected"]
    )
    clock = FakeClock()

    summary = await _dispatcher(
        repository, {"telegram": telegram}, clock=clock
    ).run_cycle()

    assert summary.failed == 1
    assert len(telegram.attempts) == 4
    assert clock.delays == [1.0, 2.0, 4.0]


async def test_retry_budget_bounds_the_total_wait():
    """GIVEN un presupuesto de 4 s y esperas 1, 2, 4 s WHEN falla siempre
    THEN no se duerme más allá del presupuesto y la alerta va a Failed (CD-3)."""
    alert = _alert("critical")
    repository = FakeCommsRepository(alerts=[alert])
    telegram = FakeProvider(
        name="telegram", destination=CHAT_ID, outcomes=["transient"]
    )
    clock = FakeClock()
    policy = RetryPolicy(attempts=5, base_seconds=1.0, factor=2.0, budget_seconds=4.0)

    await _dispatcher(
        repository, {"telegram": telegram}, policy=policy, clock=clock
    ).run_cycle()

    assert clock.delays == [1.0, 2.0]
    assert len(telegram.attempts) == 3
    assert repository.status[alert.alert_id] == "Failed"


# -- CD-5: transiciones ----------------------------------------------------


async def test_success_persists_channel_recipient_and_sent_at():
    """WHEN el envío funciona THEN se persisten canal, destino real y
    `sent_at` del reloj del ciclo (CD-5, OAS-B10-2)."""
    alert = _alert("medium")
    repository = FakeCommsRepository(alerts=[alert])
    email = FakeProvider(name="email", destination=MAILBOX)
    clock = FakeClock()

    await _dispatcher(repository, {"email": email}, clock=clock).run_cycle()

    (record,) = repository.sent
    assert record[0] is alert
    assert record[1] == "email"
    assert record[2] == MAILBOX
    assert record[3] == NOW


# -- CD-1: lote acotado ----------------------------------------------------


async def test_cycle_claims_at_most_the_configured_batch():
    """GIVEN 5 alertas Pending y batch 2 WHEN corre el ciclo THEN se despachan
    2 y quedan 3 Pending para el ciclo siguiente (CD-1)."""
    repository = FakeCommsRepository(alerts=[_alert("high") for _ in range(5)])
    telegram = FakeProvider(name="telegram", destination=CHAT_ID)

    first = await _dispatcher(
        repository, {"telegram": telegram}, batch_size=2
    ).run_cycle()
    second = await _dispatcher(
        repository, {"telegram": telegram}, batch_size=2
    ).run_cycle()

    assert first == CycleSummary(claimed=2, sent=2, failed=0)
    assert second == CycleSummary(claimed=2, sent=2, failed=0)
    assert sum(1 for status in repository.status.values() if status == "Pending") == 1
    assert repository.claim_calls[-1][1] == 2


# -- OAS-B10-2: canal sin credenciales ------------------------------------


async def test_channel_without_destination_keeps_the_alert_pending(caplog):
    """GIVEN un canal sin destino configurado WHEN corre el ciclo dos veces
    THEN la alerta queda Pending, no se levanta y el canal se loguea UNA vez
    (OAS-B10-2, design §6)."""
    email_alert = _alert("medium")
    telegram_alert = _alert("critical")
    repository = FakeCommsRepository(alerts=[email_alert, telegram_alert])
    telegram = FakeProvider(name="telegram", destination=CHAT_ID)
    dispatcher = _dispatcher(repository, {"telegram": telegram})

    with caplog.at_level(logging.WARNING, logger="intellops-comms"):
        first = await dispatcher.run_cycle()
        second = await dispatcher.run_cycle()

    assert first == CycleSummary(claimed=1, sent=1, failed=0)
    assert second == CycleSummary(claimed=0, sent=0, failed=0)
    assert repository.status[email_alert.alert_id] == "Pending"
    assert repository.status[telegram_alert.alert_id] == "Sent"
    assert repository.failed == []
    unavailable = [
        record for record in caplog.records if "channel=email" in record.getMessage()
    ]
    assert len(unavailable) == 1


async def test_unavailable_channel_is_logged_once_across_cycles(caplog):
    """GIVEN un proceso de varios ciclos WHEN el canal sigue sin credenciales
    THEN el aviso sale UNA sola vez, no una por ciclo (design §6)."""
    shared: set[str] = set()
    repository = FakeCommsRepository(alerts=[_alert("medium")])

    with caplog.at_level(logging.WARNING, logger="intellops-comms"):
        for _ in range(3):
            await _dispatcher(
                repository, {}, notified_channels=shared
            ).run_cycle()

    unavailable = [
        record for record in caplog.records if "channel=email" in record.getMessage()
    ]
    assert len(unavailable) == 1
    assert shared == {"telegram", "email"}


async def test_no_configured_channel_does_not_query_the_database(caplog):
    """GIVEN ningún canal configurado WHEN corre el ciclo THEN no se reclama
    nada y no se levanta: el stack arranca sin secretos (OAS-B10-2)."""
    repository = FakeCommsRepository(alerts=[_alert("critical")])

    with caplog.at_level(logging.WARNING, logger="intellops-comms"):
        summary = await _dispatcher(repository, {}).run_cycle()

    assert summary == CycleSummary(claimed=0, sent=0, failed=0)
    assert repository.claim_calls == []


# -- OAS-B10-4: higiene de logs -------------------------------------------


async def test_logs_name_alert_channel_and_attempt_but_no_secrets(caplog):
    """WHEN el envío falla THEN el log trae id de alerta, canal e intento y
    nunca el mensaje ni el destino (OAS-B10-4, design §7)."""
    alert = _alert("critical")
    repository = FakeCommsRepository(alerts=[alert])
    telegram = FakeProvider(
        name="telegram", destination=CHAT_ID, outcomes=["permanent"]
    )

    with caplog.at_level(logging.WARNING, logger="intellops-comms"):
        await _dispatcher(repository, {"telegram": telegram}).run_cycle()

    text = caplog.text
    assert str(alert.alert_id) in text
    assert "channel=telegram" in text
    assert "attempt=1" in text
    assert alert.message not in text
    assert CHAT_ID not in text


# -- Proveedores reales con transporte falso ------------------------------


def _telegram(
    handler, *, destination: str = CHAT_ID
) -> tuple[TelegramProvider, httpx.AsyncClient]:
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    provider = TelegramProvider(
        token=BOT_TOKEN, destination=destination, client=client, timeout=5.0
    )
    return provider, client


async def test_telegram_provider_sends_chat_id_and_message():
    """WHEN el proveedor envía THEN postea `chat_id` y el texto de la alerta a
    la Bot API (D9: httpx, ya en las dependencias)."""
    seen: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append({"url": str(request.url), "json": json.loads(request.content)})
        return httpx.Response(200, json={"ok": True})

    provider, client = _telegram(handler)
    alert = _alert("critical")
    async with client:
        await provider.send(alert)

    assert len(seen) == 1
    assert seen[0]["json"]["chat_id"] == CHAT_ID
    assert alert.message in seen[0]["json"]["text"]
    assert BOT_TOKEN in seen[0]["url"]
    assert provider.destination == CHAT_ID


@pytest.mark.parametrize("status_code", [400, 403])
async def test_telegram_provider_marks_4xx_as_permanent(status_code: int):
    """Telegram 400/403 es permanente: no se reintenta (CD-4)."""

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code, json={"ok": False})

    provider, client = _telegram(handler)
    async with client:
        with pytest.raises(PermanentDeliveryError):
            await provider.send(_alert("critical"))


@pytest.mark.parametrize("status_code", [429, 500, 502])
async def test_telegram_provider_marks_other_failures_as_transient(status_code: int):
    """429 y 5xx son transitorios: el dispatcher reintenta (CD-3)."""

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code)

    provider, client = _telegram(handler)
    async with client:
        with pytest.raises(TransientDeliveryError):
            await provider.send(_alert("critical"))


async def test_telegram_provider_never_leaks_the_token_in_the_error():
    """Un error de transporte no puede arrastrar la URL con el token (D8)."""

    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("boom", request=request)

    provider, client = _telegram(handler)
    async with client:
        with pytest.raises(TransientDeliveryError) as excinfo:
            await provider.send(_alert("critical"))

    assert BOT_TOKEN not in str(excinfo.value)


async def test_telegram_provider_uses_the_configured_api_base(monkeypatch):
    """GIVEN `INTELLOPS_COMMS_TELEGRAM_API_BASE` WHEN el worker arma el
    proveedor y envía THEN la URL es `{base}/bot{token}/sendMessage` sobre el
    stub configurado (E2E-1, D2)."""
    monkeypatch.setenv(API_BASE_VAR, STUB_API_BASE)
    monkeypatch.setenv("INTELLOPS_COMMS_TELEGRAM_BOT_TOKEN", BOT_TOKEN)
    monkeypatch.setenv("INTELLOPS_COMMS_TELEGRAM_CHAT_ID", CHAT_ID)
    seen: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(str(request.url))
        return httpx.Response(200, json={"ok": True})

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler)
    ) as client:
        providers = build_providers(CommsSettings(), client)
        await providers["telegram"].send(_alert("critical"))

    assert seen == [f"{STUB_API_BASE}/bot{BOT_TOKEN}/sendMessage"]


async def test_telegram_provider_without_the_variable_keeps_the_current_url(
    monkeypatch,
):
    """Sin la variable la URL es exactamente la de hoy: comportamiento
    actual preservado (E2E-1, escenario "default sin la variable")."""
    monkeypatch.delenv(API_BASE_VAR, raising=False)
    monkeypatch.setenv("INTELLOPS_COMMS_TELEGRAM_BOT_TOKEN", BOT_TOKEN)
    monkeypatch.setenv("INTELLOPS_COMMS_TELEGRAM_CHAT_ID", CHAT_ID)
    settings = CommsSettings()
    seen: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(str(request.url))
        return httpx.Response(200, json={"ok": True})

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler)
    ) as client:
        providers = build_providers(settings, client)
        await providers["telegram"].send(_alert("critical"))

    assert settings.telegram_api_base == providers_module.TELEGRAM_API_BASE
    assert seen == [f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"]


class FakeSMTP:
    """`smtplib.SMTP` falso: registra el mensaje y puede fallar a pedido."""

    instances: list["FakeSMTP"] = []
    error: Exception | None = None

    def __init__(self, host: str, port: int, timeout: float | None = None) -> None:
        self.host = host
        self.port = port
        self.timeout = timeout
        self.calls: list[object] = []
        self.messages: list[object] = []
        FakeSMTP.instances.append(self)

    def __enter__(self) -> "FakeSMTP":
        return self

    def __exit__(self, *_exc: object) -> bool:
        return False

    def starttls(self) -> None:
        self.calls.append("starttls")

    def login(self, username: str, password: str) -> None:
        self.calls.append(("login", username, password))

    def send_message(self, message) -> None:
        if FakeSMTP.error is not None:
            raise FakeSMTP.error
        self.messages.append(message)


@pytest.fixture
def fake_smtp(monkeypatch):
    """Reemplaza `smtplib.SMTP` en el módulo de proveedores por el doble."""
    FakeSMTP.instances = []
    FakeSMTP.error = None
    monkeypatch.setattr(providers_module.smtplib, "SMTP", FakeSMTP)
    return FakeSMTP


def _email(**overrides) -> EmailProvider:
    values = {
        "host": "smtp.example.test",
        "port": 587,
        "destination": MAILBOX,
        "sender": "intellops@example.test",
        "username": "intellops",
        "password": "smtp-secret",
        "starttls": True,
        "timeout": 5.0,
    }
    values.update(overrides)
    return EmailProvider(**values)


async def test_email_provider_sends_with_starttls_and_login(fake_smtp):
    """WHEN envía un mail THEN usa SMTP con STARTTLS, login y `To` del
    destino configurado (D9: stdlib `smtplib` + `email.message`)."""
    provider = _email()
    alert = _alert("medium")

    await provider.send(alert)

    (smtp,) = fake_smtp.instances
    assert (smtp.host, smtp.port) == ("smtp.example.test", 587)
    assert smtp.calls == ["starttls", ("login", "intellops", "smtp-secret")]
    (message,) = smtp.messages
    assert message["To"] == MAILBOX
    assert message["From"] == "intellops@example.test"
    assert "medium" in message["Subject"]
    assert alert.message in message.get_content()


async def test_email_provider_marks_5xx_as_permanent(fake_smtp):
    """Un 5xx del SMTP (credenciales, destinatario) es permanente (CD-4)."""
    provider = _email()
    fake_smtp.error = smtplib.SMTPResponseException(535, b"auth failed")

    with pytest.raises(PermanentDeliveryError):
        await provider.send(_alert("medium"))


async def test_email_provider_marks_4xx_and_connection_errors_as_transient(
    fake_smtp,
):
    """Un 4xx del SMTP o una caída de conexión son transitorios (CD-3)."""
    provider = _email()
    fake_smtp.error = smtplib.SMTPResponseException(451, b"try later")
    with pytest.raises(TransientDeliveryError):
        await provider.send(_alert("medium"))

    fake_smtp.error = smtplib.SMTPServerDisconnected("gone")
    with pytest.raises(TransientDeliveryError):
        await provider.send(_alert("medium"))


async def test_email_provider_does_not_leak_the_password_in_the_error(fake_smtp):
    """El error de un 5xx no arrastra la contraseña SMTP (D8)."""
    provider = _email()
    fake_smtp.error = smtplib.SMTPAuthenticationError(535, b"smtp-secret rejected")

    with pytest.raises(PermanentDeliveryError) as excinfo:
        await provider.send(_alert("medium"))

    assert "smtp-secret" not in str(excinfo.value)


# -- OAS-B10-1: configuración por entorno ---------------------------------


def test_settings_defaults_route_by_severity(monkeypatch):
    """Sin variables propias, el routing por defecto es el de la spec."""
    for name in (
        "INTELLOPS_COMMS_CHANNEL_CRITICAL",
        "INTELLOPS_COMMS_CHANNEL_HIGH",
        "INTELLOPS_COMMS_CHANNEL_MEDIUM",
        "INTELLOPS_COMMS_CHANNEL_LOW",
    ):
        monkeypatch.delenv(name, raising=False)

    settings = CommsSettings()

    assert settings.routing == {
        "critical": "telegram",
        "high": "telegram",
        "medium": "email",
        "low": "email",
    }
    assert settings.batch_size == 20


def test_settings_reads_the_channel_routing_from_the_environment(monkeypatch):
    """El routing es configurable por env, normalizado a minúsculas."""
    monkeypatch.setenv("INTELLOPS_COMMS_CHANNEL_CRITICAL", "Email")
    monkeypatch.setenv("INTELLOPS_COMMS_CHANNEL_LOW", "telegram")

    settings = CommsSettings()

    assert settings.routing["critical"] == "email"
    assert settings.routing["low"] == "telegram"
    assert settings.routing["high"] == "telegram"


def test_settings_ignore_empty_values_from_the_compose(monkeypatch):
    """GIVEN el compose pasa las variables con default vacío (`${VAR:-}`)
    WHEN se construye la configuración THEN se usan los defaults del código y
    ningún canal queda configurado: es lo que hace que `docker compose up`
    levante sin secretos (OAS-B10-2)."""
    for name in (
        "INTELLOPS_COMMS_INTERVAL_SECONDS",
        "INTELLOPS_COMMS_BATCH_SIZE",
        "INTELLOPS_COMMS_CHANNEL_CRITICAL",
        "INTELLOPS_COMMS_CHANNEL_HIGH",
        "INTELLOPS_COMMS_CHANNEL_MEDIUM",
        "INTELLOPS_COMMS_CHANNEL_LOW",
        "INTELLOPS_COMMS_RETRY_ATTEMPTS",
        "INTELLOPS_COMMS_RETRY_BASE_SECONDS",
        "INTELLOPS_COMMS_RETRY_FACTOR",
        "INTELLOPS_COMMS_RETRY_BUDGET_SECONDS",
        "INTELLOPS_COMMS_DELIVERY_TIMEOUT_SECONDS",
        "INTELLOPS_COMMS_TELEGRAM_BOT_TOKEN",
        "INTELLOPS_COMMS_TELEGRAM_CHAT_ID",
        "INTELLOPS_COMMS_TELEGRAM_API_BASE",
        "INTELLOPS_COMMS_SMTP_HOST",
        "INTELLOPS_COMMS_SMTP_PORT",
        "INTELLOPS_COMMS_SMTP_USER",
        "INTELLOPS_COMMS_SMTP_PASSWORD",
        "INTELLOPS_COMMS_SMTP_FROM",
        "INTELLOPS_COMMS_SMTP_TO",
        "INTELLOPS_COMMS_SMTP_STARTTLS",
    ):
        monkeypatch.setenv(name, "")

    settings = CommsSettings()

    assert settings.interval_seconds == 30.0
    assert settings.batch_size == 20
    assert settings.routing == ROUTING
    assert settings.retry_policy == RetryPolicy()
    assert settings.configured_channels == []
    assert settings.smtp_port == 587
    assert settings.smtp_starttls is True
    assert settings.smtp_to is None
    # Un valor vacío significa "usá el default": la base de Telegram vuelve a
    # la constante de siempre y el comportamiento no cambia (E2E-1, D3).
    assert settings.telegram_api_base == providers_module.TELEGRAM_API_BASE


def test_settings_reject_a_channel_outside_the_v1_catalog(monkeypatch):
    """Un canal fuera del catálogo v1 (p. ej. WhatsApp) es configuración
    inválida: falla al construir, no en el primer despacho (OAS-B10-1)."""
    monkeypatch.setenv("INTELLOPS_COMMS_CHANNEL_HIGH", "whatsapp")

    with pytest.raises(ValidationError):
        CommsSettings()


def test_settings_detect_missing_credentials(monkeypatch):
    """Sin destinos configurados ningún canal está listo (OAS-B10-2)."""
    for name in (
        "INTELLOPS_COMMS_TELEGRAM_BOT_TOKEN",
        "INTELLOPS_COMMS_TELEGRAM_CHAT_ID",
        "INTELLOPS_COMMS_SMTP_HOST",
        "INTELLOPS_COMMS_SMTP_TO",
    ):
        monkeypatch.delenv(name, raising=False)
    assert CommsSettings().telegram_configured is False
    assert CommsSettings().email_configured is False

    monkeypatch.setenv("INTELLOPS_COMMS_TELEGRAM_BOT_TOKEN", BOT_TOKEN)
    monkeypatch.setenv("INTELLOPS_COMMS_TELEGRAM_CHAT_ID", CHAT_ID)
    monkeypatch.setenv("INTELLOPS_COMMS_SMTP_HOST", "smtp.example.test")
    monkeypatch.setenv("INTELLOPS_COMMS_SMTP_TO", MAILBOX)
    assert CommsSettings().telegram_configured is True
    assert CommsSettings().email_configured is True


def test_settings_retry_defaults_match_the_spec(monkeypatch):
    """4 intentos, base 1 s, factor 2 y presupuesto acotado (CD-3)."""
    for name in (
        "INTELLOPS_COMMS_RETRY_ATTEMPTS",
        "INTELLOPS_COMMS_RETRY_BASE_SECONDS",
        "INTELLOPS_COMMS_RETRY_FACTOR",
        "INTELLOPS_COMMS_RETRY_BUDGET_SECONDS",
    ):
        monkeypatch.delenv(name, raising=False)

    policy = CommsSettings().retry_policy

    assert policy == RetryPolicy(attempts=4, base_seconds=1.0, factor=2.0, budget_seconds=60.0)
    assert policy.schedule() == (1.0, 2.0, 4.0)


def test_settings_normalize_the_database_url_for_asyncpg():
    """`DATABASE_URL` llega con `postgresql://` desde el compose (design §1)."""
    settings = CommsSettings(
        database_url="postgresql://user:pass@db:5432/intellops"
    )

    assert settings.async_database_url == (
        "postgresql+asyncpg://user:pass@db:5432/intellops"
    )


# -- Ciclo periódico -------------------------------------------------------


async def test_scheduler_runs_exactly_the_requested_cycles():
    """El scheduler no duerme después del último ciclo (design §8)."""
    calls: list[int] = []

    async def cycle() -> None:
        calls.append(len(calls))

    await CommsScheduler(interval_seconds=0.0, cycle=cycle).run(max_cycles=3)

    assert calls == [0, 1, 2]


def test_alert_protocol_is_structural():
    """El contrato del proveedor es estructural: un doble es un proveedor."""
    fake = FakeProvider(name="telegram", destination=CHAT_ID)

    assert fake.destination == CHAT_ID
