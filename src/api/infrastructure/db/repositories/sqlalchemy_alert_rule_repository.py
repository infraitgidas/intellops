"""Implementación SQLAlchemy async del AlertRuleRepository (sin commit, ADR-10).

`upsert_rule` hace UNA escritura `INSERT ... ON CONFLICT (uq_alert_rule_key)
DO UPDATE ... RETURNING`: la clave es exacta porque `threshold` es `NUMERIC`
(ADR-0013 §2) y dos POST concurrentes de la misma regla no pueden duplicar
la fila. El SELECT previo solo decide si la respuesta es 201 o 200, así que
no condiciona la escritura.

`list_rules` resuelve el filtro por tenant y el orden `created_at` ASC (con
desempate por `rule_id`) EN SQL, sobre `idx_alert_rule_app_active`.
`metric_type_exists` consulta el catálogo `metric_type`, que no tiene
entidad ORM (TableClause liviano, igual que los catálogos de `alert`).
"""

from uuid import UUID

from sqlalchemy import Column, SmallInteger, func, select, table
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from api.domain.entities.alert_rule import AlertRule
from api.domain.repositories.alert_rule_repository import (
    AlertRuleRecord,
    AlertRuleRepository,
)

# pylint: disable=too-few-public-methods  # repositorio con tres métodos

_METRIC_TYPE = table("metric_type", Column("metric_type_id", SmallInteger))

# Clave de idempotencia = índice único `uq_alert_rule_key` (migración 0008).
_KEY_COLUMNS = ("application_id", "metric_type_id", "comparison", "threshold")

# Columnas que la regla expone (mismo orden que AlertRuleRecord).
_RETURNING = (
    AlertRule.__table__.c.rule_id,
    AlertRule.__table__.c.application_id,
    AlertRule.__table__.c.metric_type_id,
    AlertRule.__table__.c.comparison,
    AlertRule.__table__.c.threshold,
    AlertRule.__table__.c.window_minutes,
    AlertRule.__table__.c.min_samples,
    AlertRule.__table__.c.cooldown_minutes,
    AlertRule.__table__.c.severity,
    AlertRule.__table__.c.is_active,
    AlertRule.__table__.c.created_at,
)


def _record(row) -> AlertRuleRecord:
    """Fila (ORM o RETURNING) → DTO de dominio."""
    return AlertRuleRecord(
        rule_id=row.rule_id,
        application_id=row.application_id,
        metric_type_id=row.metric_type_id,
        comparison=row.comparison,
        threshold=row.threshold,
        window_minutes=row.window_minutes,
        min_samples=row.min_samples,
        cooldown_minutes=row.cooldown_minutes,
        severity=row.severity,
        is_active=row.is_active,
        created_at=row.created_at,
    )


class SQLAlchemyAlertRuleRepository(AlertRuleRepository):
    """AlertRuleRepository sobre AsyncSession (PostgreSQL, asyncpg)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_rules(self, app_id: UUID) -> list[AlertRuleRecord]:
        """Reglas de `app_id` (activas e inactivas) por `created_at` ASC."""
        result = await self._session.execute(
            select(*_RETURNING)
            .where(AlertRule.application_id == app_id)
            .order_by(AlertRule.created_at, AlertRule.rule_id)
        )
        return [_record(row) for row in result]

    async def upsert_rule(
        self, rule: AlertRuleRecord
    ) -> tuple[AlertRuleRecord, bool]:
        """Crea o actualiza por `uq_alert_rule_key`; el `created_at` de una
        regla existente NO se toca (una actualización no la rejuvenece)."""
        existed = await self._exists(rule)
        statement = (
            pg_insert(AlertRule.__table__)
            .values(
                rule_id=rule.rule_id,
                application_id=rule.application_id,
                metric_type_id=rule.metric_type_id,
                comparison=rule.comparison,
                threshold=rule.threshold,
                window_minutes=rule.window_minutes,
                min_samples=rule.min_samples,
                cooldown_minutes=rule.cooldown_minutes,
                severity=rule.severity,
                is_active=rule.is_active,
            )
            .on_conflict_do_update(
                index_elements=list(_KEY_COLUMNS),
                set_={
                    "window_minutes": rule.window_minutes,
                    "min_samples": rule.min_samples,
                    "cooldown_minutes": rule.cooldown_minutes,
                    "severity": rule.severity,
                    "is_active": rule.is_active,
                },
            )
            .returning(*_RETURNING)
        )
        row = (await self._session.execute(statement)).one()
        return _record(row), not existed

    async def metric_type_exists(self, metric_type_id: int) -> bool:
        """`True` si el id está en el catálogo `metric_type`."""
        result = await self._session.execute(
            select(func.count())
            .select_from(_METRIC_TYPE)
            .where(_METRIC_TYPE.c.metric_type_id == metric_type_id)
        )
        return bool(result.scalar_one())

    async def _exists(self, rule: AlertRuleRecord) -> bool:
        """¿Ya hay una regla con la misma clave? (solo decide 201 vs 200)."""
        result = await self._session.execute(
            select(AlertRule.rule_id).where(
                AlertRule.application_id == rule.application_id,
                AlertRule.metric_type_id == rule.metric_type_id,
                AlertRule.comparison == rule.comparison,
                AlertRule.threshold == rule.threshold,
            )
        )
        return result.first() is not None
