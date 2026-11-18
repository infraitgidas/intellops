"""Proveedores de notificación de `intellops-comms` (ISS-B-10, CD-2/CD-4).

Dos canales en la v1, ambos con UN destino por canal (D3):

- Telegram por la Bot API con `httpx` (ya es dependencia: D9), sin SDK nuevo.
- Email por `smtplib` + `email.message` de la stdlib (D9), ejecutado en un
  hilo con `asyncio.to_thread` porque `smtplib` es bloqueante: bloquear el
  event loop congelaría el ciclo que despacha el resto del lote.

La clasificación de fallos es la de CD-4: Telegram 400/403 y SMTP 5xx son
permanentes (`PermanentDeliveryError`, van a Failed sin reintento); el resto
—429, 5xx HTTP, 4xx SMTP, conexión caída, timeout— es transitorio y se
reintenta con backoff. Los mensajes de error nunca incluyen el token del bot,
la contraseña SMTP ni el cuerpo de la respuesta del proveedor, para que un log
no pueda filtrar un secreto (OAS-B10-4).
"""

import asyncio
import smtplib
from email.message import EmailMessage

import httpx

from comms.dispatcher import (
    PendingAlert,
    PermanentDeliveryError,
    TransientDeliveryError,
)
from comms.config import EMAIL, TELEGRAM

# Base de la Bot API: constante, no se configura por entorno (no hay motivo
# para apuntar a otro host en la v1 y una URL configurable es una fuga más).
TELEGRAM_API_BASE = "https://api.telegram.org"
# 400 (chat inválido / mensaje rechazado) y 403 (bot bloqueado) no mejoran
# reintentando: son la lista explícita de CD-4.
TELEGRAM_PERMANENT_STATUSES = frozenset({400, 403})
# Rango de códigos SMTP permanentes (5.x.x): credenciales, destinatario,
# política del servidor.
SMTP_PERMANENT_MIN = 500
SMTP_PERMANENT_MAX = 599


def _telegram_text(alert: PendingAlert) -> str:
    """Texto plano del mensaje: severidad + mensaje del motor (AR-5)."""
    return f"[{alert.severity.upper()}] {alert.message}"


class TelegramProvider:
    """Canal Telegram: `sendMessage` a un chat fijo (D3)."""

    name = TELEGRAM

    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def __init__(
        self,
        *,
        token: str,
        destination: str,
        client: httpx.AsyncClient,
        timeout: float = 10.0,
        api_base: str = TELEGRAM_API_BASE,
    ) -> None:
        self._token = token
        self.destination = destination
        self._client = client
        self._timeout = timeout
        self._api_base = api_base

    async def send(self, alert: PendingAlert) -> None:
        """POST a la Bot API; clasifica la respuesta según CD-4.

        El error de transporte no propaga el mensaje original de httpx porque
        incluye la URL, y la URL lleva el token del bot.
        """
        url = f"{self._api_base}/bot{self._token}/sendMessage"
        payload = {"chat_id": self.destination, "text": _telegram_text(alert)}
        try:
            response = await self._client.post(url, json=payload, timeout=self._timeout)
        except httpx.HTTPError as exc:
            raise TransientDeliveryError(
                f"telegram request failed: {type(exc).__name__}"
            ) from exc
        if response.status_code == httpx.codes.OK:
            return
        if response.status_code in TELEGRAM_PERMANENT_STATUSES:
            raise PermanentDeliveryError(
                f"telegram rejected the message: {response.status_code}"
            )
        raise TransientDeliveryError(
            f"telegram is unavailable: {response.status_code}"
        )


class EmailProvider:
    """Canal Email: un mail por alerta a un destinatario fijo (D3, D9)."""

    name = EMAIL

    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def __init__(
        self,
        *,
        host: str,
        port: int,
        destination: str,
        sender: str,
        username: str | None = None,
        password: str | None = None,
        starttls: bool = True,
        timeout: float = 10.0,
    ) -> None:
        self._host = host
        self._port = port
        self.destination = destination
        self._sender = sender
        self._username = username
        self._password = password
        self._starttls = starttls
        self._timeout = timeout

    async def send(self, alert: PendingAlert) -> None:
        """Arma el mail y lo entrega en un hilo (smtplib es bloqueante)."""
        message = self._build(alert)
        await asyncio.to_thread(self._send_sync, message)

    def _build(self, alert: PendingAlert) -> EmailMessage:
        """Mail determinista: severidad en el asunto y mensaje del motor."""
        message = EmailMessage()
        message["Subject"] = f"[IntellOps] Alerta {alert.severity}"
        message["From"] = self._sender
        message["To"] = self.destination
        message.set_content(
            f"{alert.message}\n\n"
            f"Alerta: {alert.alert_id}\n"
            f"Aplicación: {alert.application_id}\n"
            f"Severidad: {alert.severity}\n"
        )
        return message

    def _send_sync(self, message: EmailMessage) -> None:
        """Entrega SMTP y traduce la excepción a la clasificación de CD-4."""
        try:
            with smtplib.SMTP(self._host, self._port, timeout=self._timeout) as smtp:
                if self._starttls:
                    smtp.starttls()
                if self._username:
                    smtp.login(self._username, self._password or "")
                smtp.send_message(message)
        except smtplib.SMTPResponseException as exc:
            if SMTP_PERMANENT_MIN <= exc.smtp_code <= SMTP_PERMANENT_MAX:
                raise PermanentDeliveryError(
                    f"smtp rejected the message: {exc.smtp_code}"
                ) from exc
            raise TransientDeliveryError(
                f"smtp is unavailable: {exc.smtp_code}"
            ) from exc
        except smtplib.SMTPRecipientsRefused as exc:
            # El servidor rechazó el destinatario: reintentar no lo arregla.
            raise PermanentDeliveryError("smtp refused the recipients") from exc
        except smtplib.SMTPException as exc:
            raise TransientDeliveryError(
                f"smtp delivery failed: {type(exc).__name__}"
            ) from exc
        except OSError as exc:
            raise TransientDeliveryError(
                f"smtp connection failed: {type(exc).__name__}"
            ) from exc
