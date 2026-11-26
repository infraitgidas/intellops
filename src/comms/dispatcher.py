"""Despachador de alertas de `intellops-comms` (ISS-B-10, ADR-0010).

El contenedor hace polling de las `ALERT` en estado `Pending`, elige canal por
severidad, envía con retry y backoff exponencial y actualiza la alerta a
`Sent` o `Failed`. Sin puertos: es un worker con ciclo propio.

Este módulo concentra la decisión y no toca la base ni la red: el repositorio
y los proveedores se inyectan, así el ciclo se prueba con dobles (CD-1..CD-6).

Reglas fijadas por la spec:

- Routing por severidad: `critical`/`high` → Telegram; `medium`/`low` →
  Email, configurable por entorno (OAS-B10-1, design §2).
- Retry exponencial: 4 intentos, base 1 s, factor 2 → esperas 1, 2, 4 s, con
  presupuesto total acotado (CD-3, design §4).
- Telegram 400/403 y SMTP 5xx son permanentes: van a Failed sin reintento
  (CD-4).
- Éxito → `Sent` + `sent_at` + canal + destinatario; intentos agotados →
  `Failed` con `sent_at` NULL, porque la columna es el momento de entrega y
  una alerta fallida nunca se entregó (CD-5, design §5).
- Un canal sin destino configurado no es un fallo: la alerta queda Pending y
  el canal se loguea una sola vez (OAS-B10-2, design §6).
- Los logs nombran id de alerta, canal e intento; nunca el mensaje, el
  destinatario ni un secreto (OAS-B10-4, design §7).
"""

import asyncio
import logging
from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from typing import Protocol
from uuid import UUID

logger = logging.getLogger("intellops-comms")


class DeliveryError(Exception):
    """Fallo al entregar una alerta por un proveedor."""


class TransientDeliveryError(DeliveryError):
    """Fallo recuperable: el dispatcher reintenta con backoff (CD-3)."""


class PermanentDeliveryError(DeliveryError):
    """Fallo que reintentar no arregla: va directo a Failed (CD-4)."""


@dataclass(frozen=True)
class PendingAlert:
    """Alerta reclamada: lo mínimo para decidir canal y texto (CT-B14-B10)."""

    alert_id: UUID
    application_id: UUID
    severity: str
    message: str
    created_at: datetime


@dataclass(frozen=True)
class RetryPolicy:
    """Política de reintentos del despacho (CD-3, design §4).

    `attempts` cuenta el PRIMER intento: con 4 hay tres esperas (1, 2, 4 s).
    `budget_seconds` acota el total: si la próxima espera lo excedería, el
    despacho corta y la alerta va a Failed en vez de dormir el proceso.
    """

    attempts: int = 4
    base_seconds: float = 1.0
    factor: float = 2.0
    budget_seconds: float = 60.0

    def delay(self, attempt: int) -> float:
        """Espera antes del intento `attempt + 1` (1 → base, 2 → base·factor)."""
        return self.base_seconds * self.factor ** (attempt - 1)

    def schedule(self) -> tuple[float, ...]:
        """Las esperas entre intentos, en orden (defaults: 1, 2 y 4 s)."""
        return tuple(self.delay(attempt) for attempt in range(1, self.attempts))


class AlertProvider(Protocol):
    """Canal de notificación con UN destino por canal en la v1 (D3)."""

    name: str
    destination: str

    async def send(self, alert: PendingAlert) -> None:
        """Entrega la alerta o levanta `Transient`/`PermanentDeliveryError`."""


class CommsRepository(Protocol):
    """Puerto del dispatcher: reclamo y transiciones de estado (CD-1, CD-5)."""

    async def claim_pending(
        self, severities: Sequence[str], batch: int
    ) -> list[PendingAlert]:
        """Reclama hasta `batch` alertas Pending de esas severidades."""

    async def mark_sent(
        self,
        alert: PendingAlert,
        *,
        channel: str,
        recipient: str,
        sent_at: datetime,
    ) -> None:
        """Transición a `Sent` con canal, destinatario y `sent_at`."""

    async def mark_failed(
        self, alert: PendingAlert, *, channel: str, recipient: str
    ) -> None:
        """Transición a `Failed` con canal y destinatario del intento.

        `sent_at` queda NULL (CD-5).
        """


@dataclass(frozen=True)
class CycleSummary:
    """Resumen de un ciclo: cada alerta reclamada cuenta en un solo cubo."""

    claimed: int = 0
    sent: int = 0
    failed: int = 0


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _monotonic() -> float:
    return asyncio.get_running_loop().time()


class Dispatcher:
    """Un ciclo de despacho: reclamar → enviar con retry → transicionar."""

    def __init__(
        self,
        repository: CommsRepository,
        providers: Mapping[str, AlertProvider],
        routing: Mapping[str, str],
        policy: RetryPolicy | None = None,
        *,
        batch_size: int = 20,
        now: Callable[[], datetime] | None = None,
        monotonic: Callable[[], float] | None = None,
        sleep: Callable[[float], Awaitable[None]] | None = None,
        notified_channels: set[str] | None = None,
    ) -> None:
        self._repository = repository
        self._providers = dict(providers)
        self._routing = dict(routing)
        self._policy = policy or RetryPolicy()
        self._batch_size = batch_size
        self._now = now or _utc_now
        self._monotonic = monotonic or _monotonic
        self._sleep = sleep or asyncio.sleep
        # Canales sin credenciales ya avisados: el log de "sin destino" sale
        # una vez por proceso, no una vez por ciclo ni por alerta (design §6).
        # El worker comparte el set entre ciclos para que un reinicio del
        # dispatcher por ciclo no lo vuelva a loguear.
        self._logged_unavailable = (
            notified_channels if notified_channels is not None else set()
        )

    def routable_severities(self) -> list[str]:
        """Severidades cuyo canal está configurado, en orden de la config.

        Un canal sin destino no es un fallo (OAS-B10-2): se avisa una vez con
        el nombre del canal y sus alertas quedan Pending para cuando haya
        credenciales.
        """
        routable: list[str] = []
        for severity, channel in self._routing.items():
            if channel in self._providers:
                routable.append(severity)
            elif channel not in self._logged_unavailable:
                self._logged_unavailable.add(channel)
                logger.warning(
                    "comms channel unavailable channel=%s reason=missing_credentials",
                    channel,
                )
        return routable

    async def run_cycle(self) -> CycleSummary:
        """Despacha un lote acotado y devuelve el resumen (CD-1)."""
        severities = self.routable_severities()
        if not severities:
            return CycleSummary()
        alerts = await self._repository.claim_pending(severities, self._batch_size)
        summary = CycleSummary(claimed=len(alerts))
        for alert in alerts:
            provider = self._providers[self._routing[alert.severity]]
            if await self._deliver(alert, provider):
                await self._repository.mark_sent(
                    alert,
                    channel=provider.name,
                    recipient=provider.destination,
                    sent_at=self._now(),
                )
                summary = replace(summary, sent=summary.sent + 1)
            else:
                await self._repository.mark_failed(
                    alert,
                    channel=provider.name,
                    recipient=provider.destination,
                )
                summary = replace(summary, failed=summary.failed + 1)
        return summary

    async def _deliver(self, alert: PendingAlert, provider: AlertProvider) -> bool:
        """Intenta entregar con backoff acotado; `False` ⇒ la alerta falló.

        Un `PermanentDeliveryError` corta en el primer intento (CD-4). El
        resto de los fallos se reintentan hasta agotar intentos o el
        presupuesto de tiempo (CD-3). Se loguean solo id de alerta, canal e
        intento: nunca el mensaje, el destino ni un secreto (OAS-B10-4).
        """
        started = self._monotonic()
        for attempt in range(1, self._policy.attempts + 1):
            try:
                await provider.send(alert)
            except PermanentDeliveryError:
                logger.warning(
                    "comms delivery failed permanently alert_id=%s channel=%s attempt=%d",
                    alert.alert_id,
                    provider.name,
                    attempt,
                )
                return False
            except Exception:  # pylint: disable=broad-exception-caught
                # Cualquier otro fallo del proveedor es recuperable: el
                # próximo intento ES el reintento. CancelledError no entra
                # acá (deriva de BaseException): el apagado sí corta.
                logger.warning(
                    "comms delivery attempt failed alert_id=%s channel=%s attempt=%d",
                    alert.alert_id,
                    provider.name,
                    attempt,
                )
                if attempt == self._policy.attempts:
                    return False
                delay = self._policy.delay(attempt)
                if self._monotonic() - started + delay > self._policy.budget_seconds:
                    logger.warning(
                        "comms retry budget exhausted alert_id=%s channel=%s attempt=%d",
                        alert.alert_id,
                        provider.name,
                        attempt,
                    )
                    return False
                await self._sleep(delay)
            else:
                logger.info(
                    "comms alert delivered alert_id=%s channel=%s attempt=%d",
                    alert.alert_id,
                    provider.name,
                    attempt,
                )
                return True
        return False
