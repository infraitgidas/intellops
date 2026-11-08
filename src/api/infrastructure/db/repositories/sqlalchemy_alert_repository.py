"""Alert repository SQLAlchemy async — lectura app-scoped (ISS-B-03, #68).

UNA sentencia: filtro por tenant (`application_id`), ventana sobre
`created_at` en `[start, end)`, filtro opcional por estado,
`ORDER BY created_at DESC, alert_id DESC` (desempate determinista) y `LIMIT`,
todo EN SQL. El plan usa `idx_alert_app_created` (migración 0007).

`status` y `channel` salen de los catálogos `alert_status` (JOIN) y
`alert_channel` (LEFT JOIN: `channel_id` es NULL hasta que B.10 despacha la
alerta), en minúsculas. `recipient` no se lee (ADR-0012).
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import Column, SmallInteger, Text, func, select, table
from sqlalchemy.ext.asyncio import AsyncSession

from api.domain.entities.alert import Alert
from api.domain.repositories.alert_repository import AlertRecord, AlertRepository

# pylint: disable=too-few-public-methods  # repositorio con un solo método público

# Catálogos sin entidad ORM: TableClause liviano para los JOIN por id.
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


class SQLAlchemyAlertRepository(AlertRepository):
    """AlertRepository sobre AsyncSession (PostgreSQL, asyncpg)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_alerts(
        self,
        app_id: UUID,
        start: datetime,
        end: datetime,
        limit: int,
        status: str | None = None,
    ) -> list[AlertRecord]:
        """Alertas de `app_id` creadas en `[start, end)`, la más nueva
        primero; filtro, orden y `LIMIT` se resuelven EN SQL."""
        status_name = func.lower(_ALERT_STATUS.c.name)
        stmt = (
            select(
                Alert.alert_id,
                Alert.application_id,
                Alert.anomaly_id,
                Alert.severity,
                Alert.message,
                status_name.label("status"),
                func.lower(_ALERT_CHANNEL.c.name).label("channel"),
                Alert.created_at,
                Alert.sent_at,
            )
            .join(_ALERT_STATUS, _ALERT_STATUS.c.status_id == Alert.status_id)
            .outerjoin(_ALERT_CHANNEL, _ALERT_CHANNEL.c.channel_id == Alert.channel_id)
            .where(
                Alert.application_id == app_id,
                Alert.created_at >= start,
                Alert.created_at < end,
            )
            .order_by(Alert.created_at.desc(), Alert.alert_id.desc())
            .limit(limit)
        )
        if status is not None:
            stmt = stmt.where(status_name == status)
        result = await self._session.execute(stmt)
        return [
            AlertRecord(
                alert_id=row.alert_id,
                application_id=row.application_id,
                anomaly_id=row.anomaly_id,
                severity=row.severity,
                message=row.message,
                status=row.status,
                channel=row.channel,
                created_at=row.created_at,
                sent_at=row.sent_at,
            )
            for row in result
        ]
