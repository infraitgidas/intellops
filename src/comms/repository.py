"""Repositorio del despachador sobre PostgreSQL (ISS-B-10, CD-1/CD-5).

Implementa el puerto `CommsRepository` del dispatcher sobre `AsyncSession`:

- **Reclamo** (CD-1, design §3): una sola sentencia
  `SELECT ... WHERE status_id = Pending AND severity IN (...) ORDER BY
  created_at FOR UPDATE SKIP LOCKED LIMIT :batch`. La fila queda bloqueada
  mientras se despacha, así un segundo despachador no la repite; el filtro
  por severidad deja fuera las alertas cuyo canal no tiene credenciales, que
  siguen Pending sin que nadie las toque (OAS-B10-2).
- **Sent** (CD-5): `status_id = Sent`, `sent_at` del momento del envío,
  `channel_id` del catálogo y `recipient` con el destino real.
- **Failed** (CD-5): solo `status_id = Failed`. `sent_at` queda NULL porque la
  columna es el momento de entrega y una alerta fallida nunca se entregó;
  `channel_id` y `recipient` también quedan NULL porque no hubo entrega (el
  canal del intento está en el log, no en la fila).

Esquemas locales al contenedor: ADR-0010 prohíbe cross-imports con `api`.
"""

from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    SmallInteger,
    Text,
    select,
    table,
    update,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.asyncio import AsyncSession

from comms.dispatcher import PendingAlert

# Catálogo `alert_status` (DDL 0001) y `alert_channel` (DDL 0001): los nombres
# son los de la migración, en title case.
PENDING_STATUS = "Pending"
SENT_STATUS = "Sent"
FAILED_STATUS = "Failed"
CHANNEL_CATALOG_NAMES = {"telegram": "Telegram", "email": "Email"}

_ALERT = table(
    "alert",
    Column("alert_id", PGUUID(as_uuid=True)),
    Column("application_id", PGUUID(as_uuid=True)),
    Column("severity", Text),
    Column("recipient", Text),
    Column("channel_id", SmallInteger),
    Column("message", Text),
    Column("status_id", SmallInteger),
    Column("created_at", DateTime(timezone=True)),
    Column("sent_at", DateTime(timezone=True)),
)
_ALERT_STATUS = table(
    "alert_status",
    Column("status_id", SmallInteger),
    Column("name", Text),
)
_ALERT_CHANNEL = table(
    "alert_channel",
    Column("channel_id", SmallInteger),
    Column("name", Text),
)


class SqlAlchemyCommsRepository:
    """`CommsRepository` sobre PostgreSQL (asyncpg)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def claim_pending(
        self, severities: Sequence[str], batch: int
    ) -> list[PendingAlert]:
        """Reclama hasta `batch` alertas Pending con `FOR UPDATE SKIP LOCKED`.

        El `SELECT` no commitea: el lock vive en la transacción abierta de la
        sesión y se libera con la transición de la alerta (design §3).
        """
        if batch < 1 or not severities:
            return []
        pending_id = await self._status_id(PENDING_STATUS)
        stmt = (
            select(
                _ALERT.c.alert_id,
                _ALERT.c.application_id,
                _ALERT.c.severity,
                _ALERT.c.message,
                _ALERT.c.created_at,
            )
            .where(
                _ALERT.c.status_id == pending_id,
                _ALERT.c.severity.in_(list(severities)),
            )
            .order_by(_ALERT.c.created_at, _ALERT.c.alert_id)
            .limit(batch)
            .with_for_update(skip_locked=True)
        )
        rows = (await self._session.execute(stmt)).all()
        return [
            PendingAlert(
                alert_id=row.alert_id,
                application_id=row.application_id,
                severity=row.severity,
                message=row.message,
                created_at=row.created_at,
            )
            for row in rows
        ]

    async def mark_sent(
        self,
        alert: PendingAlert,
        *,
        channel: str,
        recipient: str,
        sent_at: datetime,
    ) -> None:
        """Transición a `Sent` con canal, destinatario y `sent_at` (CD-5)."""
        status_id = await self._status_id(SENT_STATUS)
        channel_id = await self._channel_id(channel)
        await self._session.execute(
            update(_ALERT)
            .where(_ALERT.c.alert_id == alert.alert_id)
            .values(
                status_id=status_id,
                channel_id=channel_id,
                recipient=recipient,
                sent_at=sent_at,
            )
        )
        await self._session.commit()

    async def mark_failed(
        self, alert: PendingAlert, *, channel: str, recipient: str
    ) -> None:
        """Transición a `Failed`; `sent_at` queda NULL a propósito (CD-5).

        `sent_at` es el momento de entrega: una alerta que nunca se entregó no
        tiene uno. El canal y el destinatario SÍ se persisten: son el destino
        del intento, y sin ellos una alerta fallida no se puede diagnosticar
        (qué canal falló) ni distinguir de una que nadie intentó despachar.
        """
        status_id = await self._status_id(FAILED_STATUS)
        channel_id = await self._channel_id(channel)
        await self._session.execute(
            update(_ALERT)
            .where(_ALERT.c.alert_id == alert.alert_id)
            .values(
                status_id=status_id,
                channel_id=channel_id,
                recipient=recipient,
            )
        )
        await self._session.commit()

    async def _status_id(self, name: str) -> int:
        """`alert_status.status_id` por nombre; el catálogo existe por 0001."""
        status_id = await self._session.scalar(
            select(_ALERT_STATUS.c.status_id).where(_ALERT_STATUS.c.name == name)
        )
        if status_id is None:
            raise RuntimeError(f"alert_status catalog has no {name!r} row")
        return status_id

    async def _channel_id(self, channel: str) -> int:
        """`alert_channel.channel_id` por nombre de la configuración."""
        catalog_name = CHANNEL_CATALOG_NAMES.get(channel)
        if catalog_name is None:
            raise ValueError(f"unknown alert channel: {channel!r}")
        channel_id = await self._session.scalar(
            select(_ALERT_CHANNEL.c.channel_id).where(
                _ALERT_CHANNEL.c.name == catalog_name
            )
        )
        if channel_id is None:
            raise RuntimeError(
                f"alert_channel catalog has no {catalog_name!r} row"
            )
        return channel_id
