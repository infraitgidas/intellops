"""Anomaly repository SQLAlchemy async — lectura app-scoped (ISS-B-03, #68).

Cada consulta es UNA sentencia: filtro por tenant (`application_id`), ventana
sobre el instante de detección (`timestamp` en `[start, end)`), filtro
opcional por tipo de métrica, `ORDER BY timestamp DESC, anomaly_id DESC`
(desempate determinista) y `LIMIT`, todo EN SQL. El JOIN al catálogo
`metric_type` aporta el nombre de la métrica. El plan usa
`idx_anomaly_app_timestamp` (migración 0007).

El detalle filtra por `anomaly_id` AND `application_id` (ADR-0003): una
anomalía de otro tenant se comporta como inexistente.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import Column, Select, SmallInteger, Text, select, table
from sqlalchemy.ext.asyncio import AsyncSession

from api.domain.entities.anomaly import Anomaly
from api.domain.repositories.anomaly_repository import (
    AnomalyRecord,
    AnomalyRepository,
)

# `metric_type` no tiene entidad ORM (catálogo): TableClause liviano para el
# JOIN por id, igual que en `sqlalchemy_query_repository`.
_METRIC_TYPE = table(
    "metric_type",
    Column("metric_type_id", SmallInteger),
    Column("name", Text),
)


def _anomaly_columns() -> Select:
    """Columnas que la lectura expone, con el nombre de la métrica."""
    return select(
        Anomaly.anomaly_id,
        Anomaly.application_id,
        Anomaly.metric_type_id,
        _METRIC_TYPE.c.name.label("metric_name"),
        Anomaly.model_id,
        Anomaly.bucket_start,
        Anomaly.bucket_seconds,
        Anomaly.expected_value,
        Anomaly.actual_value,
        Anomaly.severity_score,
        Anomaly.confidence_score,
        Anomaly.timestamp.label("detected_at"),
    ).join(_METRIC_TYPE, _METRIC_TYPE.c.metric_type_id == Anomaly.metric_type_id)


class SQLAlchemyAnomalyRepository(AnomalyRepository):
    """AnomalyRepository sobre AsyncSession (PostgreSQL, asyncpg)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_anomalies(
        self,
        app_id: UUID,
        start: datetime,
        end: datetime,
        limit: int,
        metric_type_id: int | None = None,
    ) -> list[AnomalyRecord]:
        """Anomalías de `app_id` detectadas en `[start, end)`, la más nueva
        primero; filtro, orden y `LIMIT` se resuelven EN SQL."""
        stmt = (
            _anomaly_columns()
            .where(
                Anomaly.application_id == app_id,
                Anomaly.timestamp >= start,
                Anomaly.timestamp < end,
            )
            .order_by(Anomaly.timestamp.desc(), Anomaly.anomaly_id.desc())
            .limit(limit)
        )
        if metric_type_id is not None:
            stmt = stmt.where(Anomaly.metric_type_id == metric_type_id)
        result = await self._session.execute(stmt)
        return [_to_record(row) for row in result]

    async def get_anomaly(
        self, app_id: UUID, anomaly_id: UUID
    ) -> AnomalyRecord | None:
        """La anomalía solo si `anomaly_id` AND `application_id` coinciden."""
        stmt = _anomaly_columns().where(
            Anomaly.anomaly_id == anomaly_id,
            Anomaly.application_id == app_id,
        )
        row = (await self._session.execute(stmt)).one_or_none()
        return None if row is None else _to_record(row)


def _to_record(row) -> AnomalyRecord:
    """Fila SQL → DTO de dominio."""
    return AnomalyRecord(
        anomaly_id=row.anomaly_id,
        application_id=row.application_id,
        metric_type_id=row.metric_type_id,
        metric_name=row.metric_name,
        model_id=row.model_id,
        bucket_start=row.bucket_start,
        bucket_seconds=row.bucket_seconds,
        expected_value=row.expected_value,
        actual_value=row.actual_value,
        severity_score=row.severity_score,
        confidence_score=row.confidence_score,
        detected_at=row.detected_at,
    )
