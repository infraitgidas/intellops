"""AlertRule repository SQLAlchemy async — observaciones y alertas (ISS-B-14, #74).

Cada agregado es UNA sentencia acotada por tenant y por la ventana `[start, end)`
(índices `idx_rum_metric_type_timestamp`, `idx_rum_metric_session_timestamp`,
`idx_js_exception_session_timestamp`, `idx_user_session_app_id`):

- `latency`: promedio y conteo de `TTFB` RUM. Las filas de la sonda (con
  `metadata ? 'probe_target'`) no cuentan ni en el promedio ni en la muestra
  (DT-6).
- `availability`: promedio y conteo de `AVAILABILITY` (la sonda es la fuente).
- `error_rate`: excepciones / sesiones activas de la ventana. Una sesión es
  activa si tiene alguna métrica no-sonda o alguna excepción en la ventana
  (DT-7): no depende de `user_session.start_timestamp` (solo el primer evento)
  y deja afuera a la sesión sintética de la sonda sin conocer su id. Sin
  ponderar por `js_exception.sample_rate`.

El repositorio NO hace commit: la transacción es del evaluador (DT-5).
"""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import exists, false, func, insert, not_, select, union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ColumnElement

from api.domain.entities.alert import Alert
from api.domain.entities.alert_rule import AlertRule as AlertRuleRow
from api.domain.entities.application import Application
from api.domain.entities.js_exception import JsException
from api.domain.entities.rum_metric import RumMetric
from api.domain.entities.user_session import UserSession
from api.domain.repositories.alert_rule_repository import (
    AlertRuleRepository,
    NewAlert,
    Observation,
)
from api.domain.services.alert_rules import AlertRule
from api.infrastructure.db.catalogs import ALERT_STATUS, METRIC_TYPE

# Marca de la sonda en `rum_metric.metadata` (src/probe/ingest.py).
PROBE_METADATA_KEY = "probe_target"
PENDING_STATUS_NAME = "Pending"


def _is_probe_row() -> ColumnElement[bool]:
    """`metadata ? 'probe_target'`; NULL (sin metadata) cuenta como RUM."""
    return func.coalesce(RumMetric.metadata_json.has_key(PROBE_METADATA_KEY), false())


class SQLAlchemyAlertRuleRepository(AlertRuleRepository):
    """AlertRuleRepository sobre AsyncSession (PostgreSQL, asyncpg)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_active_application_ids(self) -> list[UUID]:
        """Aplicaciones con `is_active = TRUE`."""
        result = await self._session.execute(
            select(Application.app_id)
            .where(Application.is_active.is_(True))
            .order_by(Application.app_id)
        )
        return list(result.scalars())

    async def list_rule_overrides(self, app_id: UUID) -> list[AlertRule]:
        """Filas de `alert_rule` de `app_id` (incluidas las deshabilitadas)."""
        result = await self._session.execute(
            select(
                AlertRuleRow.rule_id,
                AlertRuleRow.threshold,
                AlertRuleRow.severity,
                AlertRuleRow.window_seconds,
                AlertRuleRow.min_samples,
                AlertRuleRow.cooldown_seconds,
                AlertRuleRow.enabled,
            ).where(AlertRuleRow.application_id == app_id)
        )
        return [
            AlertRule(
                rule_id=row.rule_id,
                threshold=row.threshold,
                severity=row.severity,
                window_seconds=row.window_seconds,
                min_samples=row.min_samples,
                cooldown_seconds=row.cooldown_seconds,
                enabled=row.enabled,
            )
            for row in result
        ]

    async def observe(
        self, app_id: UUID, rule_id: str, start: datetime, end: datetime
    ) -> Observation:
        """Valor y muestras de la regla en `[start, end)`; sin filas, value None."""
        if rule_id == "latency":
            return await self._average(app_id, "TTFB", start, end, exclude_probe=True)
        if rule_id == "availability":
            return await self._average(
                app_id, "AVAILABILITY", start, end, exclude_probe=False
            )
        if rule_id == "error_rate":
            return await self._error_rate(app_id, start, end)
        raise ValueError(f"unknown rule_id: {rule_id!r}")

    async def has_recent_alert(self, app_id: UUID, rule_id: str, since: datetime) -> bool:
        """True si hay una alerta de la regla con `created_at > since`,
        sin importar su estado (`idx_alert_app_created`)."""
        stmt = select(
            exists().where(
                Alert.application_id == app_id,
                Alert.rule_id == rule_id,
                Alert.created_at > since,
            )
        )
        return bool(await self._session.scalar(stmt))

    async def create_alert(self, alert: NewAlert) -> None:
        """Inserta la alerta Pending (estado resuelto por nombre en el catálogo);
        `recipient`, `channel_id`, `sent_at` y `anomaly_id` quedan NULL."""
        pending = (
            select(ALERT_STATUS.c.status_id)
            .where(ALERT_STATUS.c.name == PENDING_STATUS_NAME)
            .scalar_subquery()
        )
        await self._session.execute(
            insert(Alert).values(
                alert_id=uuid4(),
                application_id=alert.application_id,
                rule_id=alert.rule_id,
                severity=alert.severity,
                threshold=alert.threshold,
                observed_value=alert.observed_value,
                message=alert.message,
                status_id=pending,
                created_at=alert.created_at,
            )
        )

    async def _average(
        self,
        app_id: UUID,
        metric_name: str,
        start: datetime,
        end: datetime,
        exclude_probe: bool,
    ) -> Observation:
        """Promedio y conteo de `rum_metric` de un tipo, filtrado por tenant."""
        stmt = (
            select(func.avg(RumMetric.value).label("value"), func.count().label("samples"))
            .select_from(RumMetric)
            .join(METRIC_TYPE, METRIC_TYPE.c.metric_type_id == RumMetric.metric_type_id)
            .join(UserSession, UserSession.session_id == RumMetric.session_id)
            .where(
                UserSession.app_id == app_id,
                METRIC_TYPE.c.name == metric_name,
                RumMetric.timestamp >= start,
                RumMetric.timestamp < end,
            )
        )
        if exclude_probe:
            stmt = stmt.where(not_(_is_probe_row()))
        row = (await self._session.execute(stmt)).one()
        return Observation(
            value=None if row.value is None else float(row.value), samples=row.samples
        )

    async def _error_rate(self, app_id: UUID, start: datetime, end: datetime) -> Observation:
        """Excepciones por sesión activa de la ventana (sin la sesión de la sonda)."""
        metric_sessions = (
            select(RumMetric.session_id)
            .join(UserSession, UserSession.session_id == RumMetric.session_id)
            .where(
                UserSession.app_id == app_id,
                RumMetric.timestamp >= start,
                RumMetric.timestamp < end,
                not_(_is_probe_row()),
            )
        )
        exception_sessions = (
            select(JsException.session_id)
            .join(UserSession, UserSession.session_id == JsException.session_id)
            .where(
                UserSession.app_id == app_id,
                JsException.timestamp >= start,
                JsException.timestamp < end,
            )
        )
        active = union(metric_sessions, exception_sessions).subquery("active")
        exceptions = (
            select(func.count())
            .select_from(JsException)
            .join(UserSession, UserSession.session_id == JsException.session_id)
            .where(
                UserSession.app_id == app_id,
                JsException.timestamp >= start,
                JsException.timestamp < end,
            )
            .scalar_subquery()
        )
        samples = select(func.count()).select_from(active).scalar_subquery()
        row = (
            await self._session.execute(
                select(exceptions.label("exceptions"), samples.label("samples"))
            )
        ).one()
        if row.samples == 0:
            return Observation(value=None, samples=0)
        return Observation(value=row.exceptions / row.samples, samples=row.samples)
