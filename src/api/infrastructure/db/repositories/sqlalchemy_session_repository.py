"""Session repository SQLAlchemy async — lectura app-scoped (ISS-S3-03, #42).

Cada consulta es UNA sentencia: primero se acota el conjunto de sesiones del
tenant (`app_id = :tenant`, ventana y `LIMIT`, o `session_id` AND `app_id`
para el detalle) y recién después se calcula su actividad con dos
subconsultas `LATERAL` (una contra `rum_metric`, otra contra `js_exception`):
`COUNT(*)` y `MAX(timestamp)`. Un agregado sin `GROUP BY` siempre devuelve
una fila (0 y NULL si la sesión no tiene filas), así que el JOIN `ON true` no
pierde sesiones.

Acotar antes de agregar evita contar actividad de sesiones que el `LIMIT`
después descarta. Los conteos usan los índices existentes
`idx_rum_metric_session_timestamp` e `idx_js_exception_session_timestamp`;
el filtro de tenant usa `idx_user_session_app_id`. Sin DDL nuevo.

`last_activity_at` = `GREATEST(max métrica, max excepción)`: PostgreSQL
ignora los NULL en `GREATEST`, así que alcanza con que haya filas de un solo
tipo. Es una observación, no un cierre de sesión (ADR-0011).
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Select, Subquery, func, select, true
from sqlalchemy.ext.asyncio import AsyncSession

from api.domain.entities.js_exception import JsException
from api.domain.entities.rum_metric import RumMetric
from api.domain.entities.user_session import UserSession
from api.domain.repositories.session_repository import (
    SessionRepository,
    SessionSummary,
)


def _with_activity(sessions: Subquery) -> Select:
    """Agrega conteos y última actividad a un conjunto ya acotado de sesiones."""
    metrics = (
        select(
            func.count().label("total"),
            func.max(RumMetric.timestamp).label("last_ts"),
        )
        .where(RumMetric.session_id == sessions.c.session_id)
        .lateral("session_metrics")
    )
    exceptions = (
        select(
            func.count().label("total"),
            func.max(JsException.timestamp).label("last_ts"),
        )
        .where(JsException.session_id == sessions.c.session_id)
        .lateral("session_exceptions")
    )
    return (
        select(
            sessions.c.session_id,
            sessions.c.app_id,
            sessions.c.start_timestamp,
            sessions.c.user_agent,
            metrics.c.total.label("metric_count"),
            exceptions.c.total.label("exception_count"),
            func.greatest(
                metrics.c.last_ts,
                exceptions.c.last_ts,
                type_=DateTime(timezone=True),
            ).label("last_activity_at"),
        )
        .select_from(sessions)
        .join(metrics, true())
        .join(exceptions, true())
    )


def _session_columns() -> Select:
    """Columnas de `user_session` que la lectura expone (ADR-0011)."""
    return select(
        UserSession.session_id,
        UserSession.app_id,
        UserSession.start_timestamp,
        UserSession.user_agent,
    )


class SQLAlchemySessionRepository(SessionRepository):
    """SessionRepository sobre AsyncSession (PostgreSQL, asyncpg)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_sessions(
        self,
        app_id: UUID,
        start: datetime,
        end: datetime,
        limit: int,
    ) -> list[SessionSummary]:
        """Sesiones de `app_id` iniciadas en `[start, end)`, la más nueva
        primero; el orden y el `LIMIT` se resuelven EN SQL."""
        sessions = (
            _session_columns()
            .where(
                UserSession.app_id == app_id,
                UserSession.start_timestamp >= start,
                UserSession.start_timestamp < end,
            )
            .order_by(
                UserSession.start_timestamp.desc(), UserSession.session_id.desc()
            )
            .limit(limit)
            .subquery("tenant_sessions")
        )
        stmt = _with_activity(sessions).order_by(
            sessions.c.start_timestamp.desc(), sessions.c.session_id.desc()
        )
        result = await self._session.execute(stmt)
        return [_to_summary(row) for row in result]

    async def get_session(
        self, app_id: UUID, session_id: UUID
    ) -> SessionSummary | None:
        """La sesión solo si `session_id` AND `app_id` coinciden (ADR-0003):
        un `session_id` de otro tenant se comporta como inexistente."""
        sessions = (
            _session_columns()
            .where(
                UserSession.session_id == session_id,
                UserSession.app_id == app_id,
            )
            .subquery("tenant_session")
        )
        row = (await self._session.execute(_with_activity(sessions))).one_or_none()
        return None if row is None else _to_summary(row)


def _to_summary(row) -> SessionSummary:
    """Fila SQL → DTO de dominio."""
    return SessionSummary(
        session_id=row.session_id,
        application_id=row.app_id,
        start_timestamp=row.start_timestamp,
        metric_count=row.metric_count,
        exception_count=row.exception_count,
        last_activity_at=row.last_activity_at,
        user_agent=row.user_agent,
    )
