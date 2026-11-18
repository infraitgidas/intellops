#!/usr/bin/env python3
"""Smoke E2E de la v1 contra la stack de `docker-compose.yml` (ISS-C-01, E2E-2).

Recorre el flujo completo, en este orden:

1. `GET /health` — espera el build y las migraciones (hasta 120 s).
2. `POST /auth/login` con el Admin del seed.
3. `POST /applications` + `POST /applications/{id}/api-key`.
4. `POST /telemetry/metrics` — un lote de TTFB sobre UNA sesión, con
   `>= min_samples` eventos aceptados y valores por encima del umbral.
5. `GET /metrics/query` — espera que el dato se pueda leer.
6. `POST /alerts/config` — regla `gt` sobre TTFB, severidad `critical`.
7. `GET /alerts` — espera que el motor de reglas cree la alerta.
8. `GET /alerts` + `GET /_messages` del stub — espera la alerta `sent` y el
   mensaje correspondiente en el stub de Telegram.

Las esperas son por etapa con polling y timeout (D4): nunca un `sleep` a
ciegas, porque los workers de reglas y de despacho avanzan por ciclo. Cada
fallo imprime la etapa, el request, el status y el cuerpo truncado, y el
proceso sale con código ≠ 0.

El stub de Telegram es un servicio del compose bajo `profiles: ["smoke"]`
(`telegram-stub`, D3): lo levanta `make smoke` con el resto de la stack y el
smoke sólo verifica su `/health` y lee `/_messages` desde el host. No depende de
que el host acepte tráfico de contenedores.

Variables de entorno (todas opcionales, D1):

| Variable | Default | Qué cambia |
|---|---|---|
| `SMOKE_API_URL` | `http://localhost:8000` | Base de la API |
| `SMOKE_STUB_URL` | `http://127.0.0.1:8099` | Stub de Telegram visto desde el host |
| `SMOKE_ADMIN_EMAIL` | `admin@intellops.local` | Admin del seed |
| `SMOKE_ADMIN_PASSWORD` | `admin-dev-password` | Password dev del seed |
| `SMOKE_TIMEOUT_HEALTH` | `120` | Segundos para `/health` |
| `SMOKE_TIMEOUT_INGEST` | `60` | Segundos para ver el dato en `/metrics/query` |
| `SMOKE_TIMEOUT_ALERT` | `60` | Segundos para ver la alerta en `/alerts` |
| `SMOKE_TIMEOUT_NOTIFICATION` | `120` | Segundos para la alerta `sent` + el mensaje |

Sólo biblioteca estándar (`urllib`, `argparse`): corre en el host con Python
3.11+, sin instalar nada y sin credenciales externas.

Uso:

    make smoke
    SMOKE_NO_BUILD=1 make smoke
    python3 scripts/smoke.py --api-url http://localhost:8000
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode
from uuid import uuid4

DEFAULT_API_URL = "http://localhost:8000"
DEFAULT_STUB_URL = "http://127.0.0.1:8099"
DEFAULT_ADMIN_EMAIL = "admin@intellops.local"
DEFAULT_ADMIN_PASSWORD = "admin-dev-password"
DEFAULT_TIMEOUT_HEALTH = "120"
DEFAULT_TIMEOUT_INGEST = "60"
DEFAULT_TIMEOUT_ALERT = "60"
DEFAULT_TIMEOUT_NOTIFICATION = "120"

# Polling: cada cuánto se reintenta y cuánto se espera al arrancar el stub.
POLL_INTERVAL = 2.0
STUB_START_TIMEOUT = 15.0
STUB_HINT = (
    "levantá el stub con `make smoke` o, con la stack arriba, "
    "`docker compose --profile smoke up -d telegram-stub`"
)
REQUEST_TIMEOUT = 15.0
# Cuerpo de respuesta que se imprime en un fallo (el resto se trunca).
MAX_BODY_CHARS = 600

# Escenario de la regla: TTFB por encima del umbral, severidad `critical`
# (rutea a Telegram), ventana de 5 min para que las muestras sigan vigentes
# cuando el motor de reglas evalúe, y `min_samples` acorde al lote.
THRESHOLD_MS = 500.0
WINDOW_MINUTES = 5
MIN_SAMPLES = 5
COOLDOWN_MINUTES = 1
# Mismo valor en todas las muestras a propósito: el p95 de una serie constante
# es exacto, así el smoke puede asertar el valor observado del mensaje sin
# depender de la interpolación de `percentile_cont`.
OBSERVED_MS = 1500.0
TTFB_VALUES = (OBSERVED_MS,) * MIN_SAMPLES

# Lo que el formateador del motor sí incluye en el mensaje (AR-5, D5):
# `_telegram_text` agrega la severidad entre corchetes y `format_message`
# nombra métrica, observado, umbral y ventana. Si el formato cambia, el smoke
# falla en la verificación del mensaje en vez de relajar la aserción.


def _comma(value: float) -> str:
    """Número con coma decimal y un decimal, como lo publica el motor."""
    return f"{value:.1f}".replace(".", ",")


EXPECTED_TEXT = (
    "[CRITICAL]",
    "TTFB",
    "p95",
    f"{_comma(OBSERVED_MS)} ms",
    f"supera el umbral de {_comma(THRESHOLD_MS)} ms",
)

LOGIN_HINT = (
    "el Admin del seed no loguea: si la base es vieja, recreá el volumen "
    "(`docker compose down -v && make up`) para que migración 0002 siembre "
    "admin@intellops.local"
)


class SmokeError(RuntimeError):
    """Fallo de una etapa, con el request, el status y el cuerpo observados."""

    def __init__(self, stage: str, response: "ApiResponse", detail: str = "") -> None:
        super().__init__(f"{stage}: {response.method} {response.url}")
        self.stage = stage
        self.response = response
        self.detail = detail


@dataclass
class ApiResponse:
    """Respuesta HTTP: método, URL, status (0 = error de red) y cuerpo."""

    method: str
    url: str
    status: int
    body: object

    @property
    def request_line(self) -> str:
        """`MÉTODO url` para los mensajes de error y el resumen."""
        return f"{self.method} {self.url}"

    def truncated_body(self) -> str:
        """Cuerpo legible y acotado (JSON si se puede, texto si no)."""
        if isinstance(self.body, (dict, list)):
            text = json.dumps(self.body, ensure_ascii=False, sort_keys=True)
        else:
            text = str(self.body)
        if len(text) > MAX_BODY_CHARS:
            return text[:MAX_BODY_CHARS] + " …(truncado)"
        return text or "(vacío)"


def _parse_body(raw: bytes) -> object:
    """JSON si el cuerpo lo es; texto si no (las respuestas 204 vienen vacías)."""
    text = raw.decode("utf-8", errors="replace")
    if not text:
        return ""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


def call(
    method: str,
    url: str,
    *,
    payload: object | None = None,
    token: str | None = None,
    api_key: str | None = None,
) -> ApiResponse:
    """Un request HTTP con `urllib`. No lanza por status ni por red.

    Un error de red se devuelve como `status = 0` con el motivo en el cuerpo,
    así el polling de `/health` puede reintentar y el fallo se reporta con el
    mismo formato que un status inesperado.
    """
    headers = {"Accept": "application/json"}
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if token is not None:
        headers["Authorization"] = f"Bearer {token}"
    if api_key is not None:
        headers["X-API-Key"] = api_key
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT) as response:
            return ApiResponse(
                method, url, response.status, _parse_body(response.read())
            )
    except urllib.error.HTTPError as exc:
        return ApiResponse(method, url, exc.code, _parse_body(exc.read()))
    except OSError as exc:  # URLError, timeout, conexión cortada
        reason = getattr(exc, "reason", exc)
        return ApiResponse(method, url, 0, f"error de red: {reason}")


def expect(stage: str, response: ApiResponse, *statuses: int, detail: str = "") -> ApiResponse:
    """Falla con `SmokeError` si el status no es uno de los esperados."""
    if response.status not in statuses:
        expected = ", ".join(str(status) for status in statuses)
        raise SmokeError(
            stage,
            response,
            detail or f"se esperaba status {expected}, llegó {response.status}",
        )
    return response


@contextmanager
def stage(name: str, timings: list[tuple[str, float]]):
    """Anuncia una etapa y registra su duración, falle o no."""
    print(f"\n==> {name}", flush=True)
    started = time.monotonic()
    try:
        yield
    finally:
        timings.append((name, time.monotonic() - started))


def _iso(moment: datetime) -> str:
    """ISO 8601 UTC con zona explícita (lo que exige la ingesta)."""
    return moment.astimezone(timezone.utc).isoformat()


def _wait_health(base_url: str, budget: float) -> ApiResponse:
    """Espera `GET /health` 200: build, migraciones y arranque de la API."""
    deadline = time.monotonic() + budget
    attempt = 0
    response = ApiResponse("GET", f"{base_url}/health", 0, "sin intentos")
    while time.monotonic() < deadline:
        attempt += 1
        response = call("GET", f"{base_url}/health")
        if response.status == 200:
            print(f"   intento {attempt}: 200 OK", flush=True)
            return response
        print(
            f"   intento {attempt}: status={response.status} "
            f"({response.truncated_body()})",
            flush=True,
        )
        time.sleep(POLL_INTERVAL)
    raise SmokeError(
        "health",
        response,
        f"la API no respondió 200 en {budget:.0f} s: revisá "
        "`docker compose logs intellops-core`",
    )


def _telemetry_batch(session_id: str, sent_at: datetime) -> dict:
    """Lote RUM de una sesión: un evento con una métrica TTFB por muestra.

    Un evento por muestra hace que `accepted` del 202 cuente exactamente las
    muestras que el motor de reglas va a ver (`rum_metric` por evento).
    """
    timestamp = _iso(sent_at)
    return {
        "schema_version": "1.0",
        "events": [
            {
                "schema_version": "1.0",
                "timestamp": timestamp,
                "session_id": session_id,
                "metrics": [
                    {
                        "type": "TTFB",
                        "value": value,
                        "unit": "ms",
                        "timestamp": timestamp,
                    }
                ],
            }
            for value in TTFB_VALUES
        ],
    }


def _wait_metrics_visible(
    base_url: str,
    api_key: str,
    metric_type_id: int,
    start: datetime,
    batch_note: str,
    budget: float,
) -> ApiResponse:
    """Espera a que `/metrics/query` devuelva el bucket de la sesión enviada.

    Si el dato no aparece, el fallo nombra el `batch_id` y los contadores de la
    ingesta (E2E-2, escenario "dato no persistido"): el smoke NO sigue con la
    regla como si nada.
    """
    query = urlencode({"metric_type": metric_type_id, "start": _iso(start)})
    url = f"{base_url}/metrics/query?{query}"
    deadline = time.monotonic() + budget
    response = ApiResponse("GET", url, 0, "sin intentos")
    while time.monotonic() < deadline:
        response = call("GET", url, api_key=api_key)
        expect("lectura", response, 200)
        rows = response.body if isinstance(response.body, list) else []
        visible = [
            row
            for row in rows
            if row.get("metric_type_id") == metric_type_id
            and row.get("session_count", 0) >= 1
        ]
        if visible:
            print(
                f"   bucket {visible[0].get('timestamp')}: "
                f"value={visible[0].get('value')} "
                f"session_count={visible[0].get('session_count')}",
                flush=True,
            )
            return response
        time.sleep(POLL_INTERVAL)
    raise SmokeError(
        "lectura",
        response,
        f"el dato aceptado no apareció en /metrics/query en {budget:.0f} s "
        f"({batch_note}): revisá `docker compose logs intellops-core` "
        "(worker de ingesta)",
    )


def _find_alert(alerts: object, alert_id: str) -> dict | None:
    """La alerta pedida dentro de la lista de `GET /alerts`, o None."""
    if not isinstance(alerts, list):
        return None
    for alert in alerts:
        if alert.get("alert_id") == alert_id:
            return alert
    return None


def _matching_messages(messages: object) -> list[dict]:
    """Mensajes del stub cuyo texto trae todo lo que el formateador incluye."""
    if not isinstance(messages, list):
        return []
    return [
        message
        for message in messages
        if isinstance(message.get("text"), str)
        and all(piece in message["text"] for piece in EXPECTED_TEXT)
    ]


def _run_flow(args: argparse.Namespace, timings: list[tuple[str, float]]) -> dict:
    """Las ocho etapas del smoke (D4), con polling y fallo accionable."""
    base_url = args.api_url.rstrip("/")

    with stage("health", timings):
        _wait_health(base_url, args.timeout_health)
        print(f"   API arriba en {base_url}", flush=True)

    with stage("login (admin del seed)", timings):
        response = call(
            "POST",
            f"{base_url}/auth/login",
            payload={"email": args.admin_email, "password": args.admin_password},
        )
        expect("login", response, 200, detail=f"login falló. {LOGIN_HINT}")
        token = response.body["access_token"]
        print(f"   {args.admin_email} autenticado", flush=True)

    with stage("aplicación y API key", timings):
        name = f"smoke-{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}"
        response = call(
            "POST", f"{base_url}/applications", payload={"name": name}, token=token
        )
        expect("aplicación", response, 201)
        app_id = response.body["app_id"]
        response = call(
            "POST", f"{base_url}/applications/{app_id}/api-key", token=token
        )
        expect("api key", response, 201)
        api_key = response.body["api_key"]
        print(f"   app_id={app_id} name={name}", flush=True)

    with stage("catálogo de métricas", timings):
        response = call("GET", f"{base_url}/metrics/list", api_key=api_key)
        expect("catálogo", response, 200)
        rows = response.body if isinstance(response.body, list) else []
        ttfb = next((row for row in rows if row.get("name") == "TTFB"), None)
        if ttfb is None:
            raise SmokeError(
                "catálogo",
                response,
                f"el catálogo no tiene TTFB: {response.truncated_body()}",
            )
        metric_type_id = int(ttfb["metric_type_id"])
        print(f"   TTFB metric_type_id={metric_type_id}", flush=True)

    session_id = str(uuid4())
    sent_at = datetime.now(timezone.utc)
    batch_id = ""
    with stage("ingesta (POST /telemetry/metrics)", timings):
        response = call(
            "POST",
            f"{base_url}/telemetry/metrics",
            payload=_telemetry_batch(session_id, sent_at),
            api_key=api_key,
        )
        expect("ingesta", response, 202)
        body = response.body if isinstance(response.body, dict) else {}
        batch_id = str(body.get("batch_id", ""))
        accepted = int(body.get("accepted", 0))
        rejected = body.get("rejected") or []
        if rejected or accepted < MIN_SAMPLES:
            raise SmokeError(
                "ingesta",
                response,
                f"batch_id={batch_id} accepted={accepted} rejected={rejected}: "
                f"se esperaban >= {MIN_SAMPLES} eventos aceptados y ninguno "
                "rechazado",
            )
        print(
            f"   session_id={session_id} batch_id={batch_id} "
            f"accepted={accepted}",
            flush=True,
        )

    batch_note = f"batch_id={batch_id} accepted={MIN_SAMPLES}"
    with stage("lectura (GET /metrics/query)", timings):
        _wait_metrics_visible(
            base_url,
            api_key,
            metric_type_id,
            sent_at - timedelta(minutes=WINDOW_MINUTES),
            batch_note,
            args.timeout_ingest,
        )
        print("   la sesión enviada se lee por /metrics/query", flush=True)

    with stage("regla de umbral (POST /alerts/config)", timings):
        response = call(
            "POST",
            f"{base_url}/alerts/config",
            payload={
                "application_id": app_id,
                "metric_type_id": metric_type_id,
                "comparison": "gt",
                "threshold": THRESHOLD_MS,
                "window_minutes": WINDOW_MINUTES,
                "min_samples": MIN_SAMPLES,
                "cooldown_minutes": COOLDOWN_MINUTES,
                "severity": "critical",
                "is_active": True,
            },
            token=token,
        )
        expect("regla", response, 201, 200)
        rule_id = response.body["rule_id"]
        print(
            f"   rule_id={rule_id} TTFB gt {THRESHOLD_MS:.0f} ms "
            f"(min_samples={MIN_SAMPLES})",
            flush=True,
        )

    with stage("alerta creada (GET /alerts)", timings):
        deadline = time.monotonic() + args.timeout_alert
        response = call("GET", f"{base_url}/alerts", api_key=api_key)
        alert_id = ""
        while time.monotonic() < deadline:
            response = call("GET", f"{base_url}/alerts", api_key=api_key)
            expect("alerta", response, 200)
            alerts = response.body if isinstance(response.body, list) else []
            own = next(
                (
                    alert
                    for alert in alerts
                    if "TTFB" in (alert.get("message") or "")
                ),
                None,
            )
            if own is not None:
                alert_id = str(own["alert_id"])
                print(
                    f"   alert_id={alert_id} status={own.get('status')} "
                    f"message={own.get('message')!r}",
                    flush=True,
                )
                break
            time.sleep(POLL_INTERVAL)
        if not alert_id:
            raise SmokeError(
                "alerta",
                response,
                f"el motor de reglas no creó la alerta en "
                f"{args.timeout_alert:.0f} s: revisá "
                "`docker compose logs intellops-ai-engine` "
                "(ciclo de reglas y ventana de la regla)",
            )

    with stage("notificación (alerta sent + stub de Telegram)", timings):
        stub_url = args.stub_url.rstrip("/")
        deadline = time.monotonic() + args.timeout_notification
        response = call("GET", f"{base_url}/alerts", api_key=api_key)
        alert: dict | None = None
        message: dict | None = None
        while time.monotonic() < deadline:
            response = call("GET", f"{base_url}/alerts", api_key=api_key)
            expect("notificación", response, 200)
            alert = _find_alert(response.body, alert_id)
            receipt = call("GET", f"{stub_url}/_messages")
            expect("notificación", receipt, 200)
            matched = _matching_messages(receipt.body)
            message = matched[0] if matched else None
            if alert is not None and alert.get("status") == "sent" and message:
                break
            time.sleep(POLL_INTERVAL)
        status = (alert or {}).get("status")
        if status != "sent" or message is None:
            receipts = call("GET", f"{stub_url}/_messages")
            raise SmokeError(
                "notificación",
                receipts,
                f"la alerta quedó en status={status!r} y el stub tiene "
                f"{len(receipts.body) if isinstance(receipts.body, list) else 0} "
                f"mensaje(s) que no incluyen {EXPECTED_TEXT}: revisá "
                "`docker compose logs intellops-comms` (credenciales y "
                "INTELLOPS_COMMS_TELEGRAM_API_BASE)",
            )
        if not message.get("chat_id"):
            raise SmokeError(
                "notificación",
                response,
                f"el mensaje llegó sin chat_id: {message}",
            )
        print(
            f"   alert_id={alert_id} status=sent "
            f"channel={alert.get('channel')}",
            flush=True,
        )
        print(
            f"   stub recibió chat_id={message['chat_id']!r} "
            f"text={message['text']!r}",
            flush=True,
        )

    return {
        "app_id": app_id,
        "session_id": session_id,
        "alert_id": alert_id,
        "metric_type_id": metric_type_id,
        "rule_id": rule_id,
        "batch_id": batch_id,
        "alert_status": str((alert or {}).get("status")),
        "channel": str((alert or {}).get("channel")),
        "message": str((message or {}).get("text")),
    }


def _wait_stub(stub_url: str) -> None:
    """Verifica el `/health` del stub antes de arrancar el flujo (D3).

    El stub es un servicio del compose bajo `profiles: ["smoke"]`: no lo
    levanta este script, así que si falta el fallo dice cómo levantarlo.
    """
    url = f"{stub_url}/health"
    deadline = time.monotonic() + STUB_START_TIMEOUT
    response = ApiResponse("GET", url, 0, "sin intentos")
    while time.monotonic() < deadline:
        response = call("GET", url)
        if response.status == 200:
            return
        time.sleep(0.2)
    raise SmokeError(
        "stub de Telegram",
        response,
        f"el stub no responde en {stub_url} ({STUB_START_TIMEOUT:.0f} s): "
        f"{STUB_HINT}",
    )


def _print_failure(error: SmokeError, timings: list[tuple[str, float]]) -> None:
    """Fallo accionable: etapa, request, status y cuerpo truncado."""
    print("\n" + "=" * 70, flush=True)
    print(f"FALLÓ la etapa: {error.stage}", flush=True)
    print(f"  request: {error.response.request_line}", flush=True)
    print(f"  status:  {error.response.status}", flush=True)
    print(f"  body:    {error.response.truncated_body()}", flush=True)
    if error.detail:
        print(f"  detalle: {error.detail}", flush=True)
    print("\nEtapas completadas antes del fallo:", flush=True)
    _print_timings(timings)
    print("=" * 70, flush=True)


def _print_timings(timings: list[tuple[str, float]]) -> None:
    """Tabla de etapas con sus segundos, en orden de ejecución."""
    for name, elapsed in timings:
        print(f"  {name:<52} {elapsed:6.1f} s", flush=True)


def _print_summary(summary: dict, timings: list[tuple[str, float]]) -> None:
    """Resumen final legible: ids, mensaje verificado y segundos por etapa."""
    total = sum(elapsed for _, elapsed in timings)
    print("\n" + "=" * 70, flush=True)
    print("SMOKE E2E EN VERDE", flush=True)
    print(f"  app_id:            {summary['app_id']}", flush=True)
    print(f"  session_id:        {summary['session_id']}", flush=True)
    print(f"  alert_id:          {summary['alert_id']}", flush=True)
    print(f"  rule_id:           {summary['rule_id']}", flush=True)
    print(f"  TTFB metric_type:  {summary['metric_type_id']}", flush=True)
    print(f"  batch_id:          {summary['batch_id']}", flush=True)
    print(
        f"  alerta:            status={summary['alert_status']} "
        f"channel={summary['channel']}",
        flush=True,
    )
    print(f"  mensaje en el stub: {summary['message']!r}", flush=True)
    print("\nSegundos por etapa:", flush=True)
    _print_timings(timings)
    print(f"  {'total':<52} {total:6.1f} s", flush=True)
    print("=" * 70, flush=True)


def _env(name: str, default: str) -> str:
    """Valor del entorno, o el default si falta o viene vacío."""
    return os.environ.get(name) or default


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Flags del smoke; cada uno tiene su variable `SMOKE_*` como default."""
    parser = argparse.ArgumentParser(
        prog="smoke.py",
        description=(
            "Smoke E2E de IntellOps contra la stack de docker-compose.yml "
            "(ISS-C-01): health, login, app + API key, ingesta, lectura, "
            "regla, alerta y notificación en un stub de Telegram."
        ),
        epilog=(
            "Levantá la stack con `make smoke` (baja los intervalos a 5 s, "
            "levanta el stub con `--profile smoke` y apunta el proveedor de "
            "Telegram a él). Los defaults se pueden cambiar con SMOKE_API_URL, "
            "SMOKE_STUB_URL, SMOKE_ADMIN_EMAIL, SMOKE_ADMIN_PASSWORD y "
            "SMOKE_TIMEOUT_*."
        ),
    )
    parser.add_argument(
        "--api-url",
        default=_env("SMOKE_API_URL", DEFAULT_API_URL),
        help="Base de la API (default: %(default)s)",
    )
    parser.add_argument(
        "--stub-url",
        default=_env("SMOKE_STUB_URL", DEFAULT_STUB_URL),
        help=(
            "Stub de Telegram visto desde el host "
            "(default: %(default)s)"
        ),
    )
    parser.add_argument(
        "--admin-email",
        default=_env("SMOKE_ADMIN_EMAIL", DEFAULT_ADMIN_EMAIL),
        help="Admin del seed (default: %(default)s)",
    )
    parser.add_argument(
        "--admin-password",
        default=_env("SMOKE_ADMIN_PASSWORD", DEFAULT_ADMIN_PASSWORD),
        help="Password dev del seed (default: %(default)s)",
    )
    parser.add_argument(
        "--timeout-health",
        type=float,
        default=_env("SMOKE_TIMEOUT_HEALTH", DEFAULT_TIMEOUT_HEALTH),
        help="Segundos para /health (default: %(default)s)",
    )
    parser.add_argument(
        "--timeout-ingest",
        type=float,
        default=_env("SMOKE_TIMEOUT_INGEST", DEFAULT_TIMEOUT_INGEST),
        help="Segundos para ver el dato en /metrics/query (default: %(default)s)",
    )
    parser.add_argument(
        "--timeout-alert",
        type=float,
        default=_env("SMOKE_TIMEOUT_ALERT", DEFAULT_TIMEOUT_ALERT),
        help="Segundos para ver la alerta en /alerts (default: %(default)s)",
    )
    parser.add_argument(
        "--timeout-notification",
        type=float,
        default=_env("SMOKE_TIMEOUT_NOTIFICATION", DEFAULT_TIMEOUT_NOTIFICATION),
        help="Segundos para la alerta sent + el mensaje (default: %(default)s)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Verifica el stub, recorre el flujo y resume; 0 en verde, 1 si falla."""
    args = parse_args(argv)
    timings: list[tuple[str, float]] = []
    try:
        print(
            "Smoke E2E ISS-C-01: "
            f"api={args.api_url} stub={args.stub_url} "
            f"admin={args.admin_email}",
            flush=True,
        )
        print(
            f"  TTFB gt {THRESHOLD_MS:.0f} ms, min_samples={MIN_SAMPLES}, "
            f"ventana={WINDOW_MINUTES} min, severidad=critical",
            flush=True,
        )
        with stage("stub de Telegram", timings):
            _wait_stub(args.stub_url.rstrip("/"))
            print(f"   stub arriba en {args.stub_url}", flush=True)
        summary = _run_flow(args, timings)
    except SmokeError as error:
        _print_failure(error, timings)
        return 1
    except KeyboardInterrupt:
        print("\nSmoke interrumpido por el operador", flush=True)
        return 130
    _print_summary(summary, timings)
    return 0


if __name__ == "__main__":
    sys.exit(main())
