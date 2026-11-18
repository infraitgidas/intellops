"""Repositorio SQLAlchemy del motor de reglas (ISS-B-14, design §2/§3/§7).

Implementa el puerto `RulesRepository` sobre `AsyncSession`:

- lee las reglas activas con el nombre de su métrica;
- delega la agregación en PostgreSQL (`aggregates.py`);
- consulta el cooldown contra `alert` (no contra estado en memoria, design
  §7);
- inserta la alerta `Pending` con `rule_id`, `threshold` y `observed_value`
  (AR-5), dejando `recipient`, `channel_id`, `sent_at` y `anomaly_id` NULL.

Esquemas locales al contenedor: ADR-0010 prohíbe cross-imports con `api`.
"""

# pylint: disable=too-few-public-methods

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    Numeric,
    SmallInteger,
    Text,
    func,
    insert,
    select,
    table,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.asyncio import AsyncSession

from ml.rules.aggregates import aggregate_metric
from ml.rules.engine import Decision, Evaluation, RuleSnapshot

# Estado de la alerta creada por el motor (catálogo `alert_status`, DDL 0001).
PENDING_STATUS = "Pending"

_ALERT_RULE = table(
    "alert_rule",
    Column("rule_id", PGUUID(as_uuid=True)),
    Column("application_id", PGUUID(as_uuid=True)),
    Column("metric_type_id", SmallInteger),
    Column("comparison", Text),
    Column("threshold", Numeric),
    Column("window_minutes", Integer),
    Column("min_samples", Integer),
    Column("cooldown_minutes", Integer),
    Column("severity", Text),
    Column("is_active", Boolean),
    Column("created_at", DateTime(timezone=True)),
)
_METRIC_TYPE = table(
    "metric_type",
    Column("metric_type_id", SmallInteger),
    Column("name", Text),
)
_ALERT = table(
    "alert",
    Column("alert_id", PGUUID(as_uuid=True)),
    Column("application_id", PGUUID(as_uuid=True)),
    Column("anomaly_id", PGUUID(as_uuid=True)),
    Column("severity", Text),
    Column("recipient", Text),
    Column("channel_id", SmallInteger),
    Column("message", Text),
    Column("status_id", SmallInteger),
    Column("created_at", DateTime(timezone=True)),
    Column("sent_at", DateTime(timezone=True)),
    Column("rule_id", PGUUID(as_uuid=True)),
    Column("threshold", Numeric),
    Column("observed_value", Numeric),
)
_ALERT_STATUS = table(
    "alert_status",
    Column("status_id", SmallInteger),
    Column("name", Text),
)


class SqlAlchemyRulesRepository:
    """`RulesRepository` sobre PostgreSQL (asyncpg)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def active_rules(self) -> list[RuleSnapshot]:
        """Reglas con `is_active = true`, con el nombre del catálogo."""
        stmt = (
            select(
                _ALERT_RULE.c.rule_id,
                _ALERT_RULE.c.application_id,
                _ALERT_RULE.c.metric_type_id,
                _METRIC_TYPE.c.name.label("metric_name"),
                _ALERT_RULE.c.comparison,
                _ALERT_RULE.c.threshold,
                _ALERT_RULE.c.window_minutes,
                _ALERT_RULE.c.min_samples,
                _ALERT_RULE.c.cooldown_minutes,
                _ALERT_RULE.c.severity,
            )
            .join(
                _METRIC_TYPE,
                _METRIC_TYPE.c.metric_type_id == _ALERT_RULE.c.metric_type_id,
            )
            .where(_ALERT_RULE.c.is_active.is_(True))
            .order_by(_ALERT_RULE.c.created_at, _ALERT_RULE.c.rule_id)
        )
        rows = (await self._session.execute(stmt)).all()
        return [
            RuleSnapshot(
                rule_id=row.rule_id,
                application_id=row.application_id,
                metric_type_id=row.metric_type_id,
                metric_name=row.metric_name,
                comparison=row.comparison,
                threshold=row.threshold,
                window_minutes=row.window_minutes,
                min_samples=row.min_samples,
                cooldown_minutes=row.cooldown_minutes,
                severity=row.severity,
            )
            for row in rows
        ]

    async def evaluate(self, rule: RuleSnapshot, now: datetime) -> Evaluation:
        """Agrega la ventana de la regla en PostgreSQL (AR-1/AR-2)."""
        return await aggregate_metric(
            self._session,
            application_id=rule.application_id,
            metric_type_id=rule.metric_type_id,
            metric_name=rule.metric_name,
            window_minutes=rule.window_minutes,
            now=now,
        )

    async def last_alert_at(
        self, rule_id: UUID, since: datetime
    ) -> datetime | None:
        """`created_at` más reciente de la regla posterior a `since` (AR-6)."""
        stmt = select(func.max(_ALERT.c.created_at)).where(
            _ALERT.c.rule_id == rule_id,
            _ALERT.c.created_at > since,
        )
        return await self._session.scalar(stmt)

    async def create_alert(self, decision: Decision) -> None:
        """Inserta la alerta Pending de una decisión `fired` (AR-5)."""
        if decision.message is None or decision.observed is None:
            raise ValueError("only fired decisions create alerts")
        status_id = await self._session.scalar(
            select(_ALERT_STATUS.c.status_id).where(
                _ALERT_STATUS.c.name == PENDING_STATUS
            )
        )
        if status_id is None:
            raise RuntimeError(
                f"alert_status catalog has no {PENDING_STATUS!r} row"
            )
        await self._session.execute(
            insert(_ALERT).values(
                alert_id=uuid4(),
                application_id=decision.rule.application_id,
                anomaly_id=None,
                severity=decision.rule.severity,
                recipient=None,
                channel_id=None,
                message=decision.message,
                status_id=status_id,
                sent_at=None,
                rule_id=decision.rule.rule_id,
                threshold=decision.rule.threshold,
                observed_value=decision.observed,
            )
        )
        await self._session.commit()
