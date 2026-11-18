#!/usr/bin/env python3
"""Stub local de la Bot API de Telegram para el smoke E2E (ISS-C-01, E2E-3).

Escucha en `0.0.0.0:${SMOKE_STUB_PORT:-8099}` y expone sólo lo que el
despachador de `intellops-comms` necesita para que la notificación sea
verificable sin credenciales reales:

- `POST /bot<token>/sendMessage` → 200 `{"ok": true}`; el `chat_id`, el texto y
  el momento de llegada quedan en memoria.
- `GET /_messages` → lista JSON de los mensajes recibidos, en orden de llegada.
- `GET /health` → 200 `{"ok": true}` para que el smoke espere a que escuche.
- Cualquier otra ruta → 404 con cuerpo JSON (no HTML), para que un error de
  configuración se lea como tal.

Sólo biblioteca estándar (`http.server`): no requiere dependencias, ni cuenta de
bot, ni red. El token no se valida a propósito —el smoke usa uno inventado— y
los mensajes viven en memoria: al cortar el proceso se pierden.

Uso:

    python3 scripts/telegram_stub.py            # 0.0.0.0:8099
    SMOKE_STUB_PORT=9100 python3 scripts/telegram_stub.py
"""

import json
import os
import signal
import sys
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8099

# Mensajes recibidos, en orden de llegada. Cada uno: chat_id, text y
# received_at (ISO 8601 UTC). Es estado del proceso, sin persistencia.
MESSAGES: list[dict] = []


def _utc_now_iso() -> str:
    """Instante actual en ISO 8601 UTC, con zona explícita."""
    return datetime.now(timezone.utc).isoformat()


def _log(message: str) -> None:
    """Log del stub por stderr: no se mezcla con el resumen del smoke."""
    print(f"[stub] {message}", file=sys.stderr, flush=True)


class StubHandler(BaseHTTPRequestHandler):
    """Atiende las cuatro rutas del contrato del stub (E2E-3)."""

    server_version = "IntellOpsTelegramStub/1.0"

    def _respond(self, status: int, payload: object) -> None:
        """Responde JSON con el status pedido y cierra el cuerpo."""
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> object:
        """Lee el cuerpo JSON del request; `{}` si viene vacío."""
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b""
        if not raw:
            return {}
        return json.loads(raw.decode("utf-8"))

    @staticmethod
    def _is_send_message(path: str) -> bool:
        """True sólo para `POST /bot<token>/sendMessage`."""
        return (
            path.startswith("/bot")
            and path.endswith("/sendMessage")
            and len(path) > len("/bot/sendMessage")
        )

    def do_POST(self) -> None:  # noqa: N802 (nombre que exige http.server)
        """`sendMessage` acumula el mensaje y responde 200 `{"ok": true}`."""
        if not self._is_send_message(self.path):
            self._respond(
                404, {"ok": False, "error": "not_found", "path": self.path}
            )
            return
        try:
            payload = self._read_json()
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            self._respond(
                400, {"ok": False, "error": f"invalid json body: {exc}"}
            )
            return
        if not isinstance(payload, dict):
            self._respond(
                400, {"ok": False, "error": "body must be a json object"}
            )
            return
        message = {
            "chat_id": payload.get("chat_id"),
            "text": payload.get("text"),
            "received_at": _utc_now_iso(),
        }
        MESSAGES.append(message)
        _log(f"sendMessage chat_id={message['chat_id']!r} recibido")
        self._respond(200, {"ok": True, "result": {"message_id": len(MESSAGES)}})

    def do_GET(self) -> None:  # noqa: N802 (nombre que exige http.server)
        """`/_messages` y `/health`; el resto, 404 JSON."""
        if self.path == "/_messages":
            self._respond(200, MESSAGES)
            return
        if self.path == "/health":
            self._respond(200, {"ok": True, "messages": len(MESSAGES)})
            return
        self._respond(404, {"ok": False, "error": "not_found", "path": self.path})

    def log_message(self, _format: str, *args: object) -> None:
        """Log de request sólo para 4xx/5xx (el resto es ruido en el smoke)."""
        status = args[1] if len(args) > 1 else None
        if isinstance(status, int) and status >= 400:
            _log(f"{args[0]} -> {status}")


def _stop(_signum: int, _frame: object) -> None:
    """SIGTERM/SIGINT → corta `serve_forever` de forma ordenada."""
    raise KeyboardInterrupt


def _port() -> int:
    """Puerto de escucha: `SMOKE_STUB_PORT` o 8099."""
    raw = os.environ.get("SMOKE_STUB_PORT") or str(DEFAULT_PORT)
    try:
        return int(raw)
    except ValueError:
        _log(f"SMOKE_STUB_PORT inválido ({raw!r}): uso {DEFAULT_PORT}")
        return DEFAULT_PORT


def main() -> int:
    """Levanta el stub hasta que lo corten (SIGTERM/SIGINT)."""
    port = _port()
    server = ThreadingHTTPServer((DEFAULT_HOST, port), StubHandler)
    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT, _stop)
    _log(
        f"escuchando en http://{DEFAULT_HOST}:{port} "
        "(POST /bot<token>/sendMessage, GET /_messages, GET /health)"
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    _log(f"detenido; {len(MESSAGES)} mensaje(s) recibido(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
