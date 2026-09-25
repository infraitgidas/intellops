"""Implementación SQLAlchemy async del IngestRepository (DD-3, ADR-10).

Insert Core por chunk: user_session ON CONFLICT DO NOTHING, bulk rum_metric
con `metric_type` resuelto contra el catálogo cacheado, bulk js_exception con
`metric_id` de correlación blanda (inexistente → NULL + contador). NO
commitea (ADR-10): el worker coordina commit/rollback por chunk y aplica
retry transitorio / dead-letter (DD-4).
"""

# pylint: disable=too-few-public-methods  # repositorio con un solo método público

from sqlalchemy import insert, select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from api.domain.entities.js_exception import JsException
from api.domain.entities.rum_metric import RumMetric
from api.domain.entities.user_session import UserSession
from api.domain.repositories.ingest_repository import (
    ExceptionRow,
    IngestRepository,
    MetricRow,
    PersistStats,
    SessionRow,
)


class SQLAlchemyIngestRepository(IngestRepository):
    """Repositorio de ingesta sobre AsyncSession (PostgreSQL, asyncpg)."""

    def __init__(
        self,
        session: AsyncSession,
        metric_type_cache: dict[str, int] | None = None,
    ) -> None:
        self._session = session
        # Cache compartido entre chunks: el worker inyecta el mismo dict para
        # no re-consultar el catálogo en cada chunk.
        self.metric_type_cache = (
            metric_type_cache if metric_type_cache is not None else {}
        )

    async def persist_chunk(
        self,
        sessions: list[SessionRow],
        metrics: list[MetricRow],
        exceptions: list[ExceptionRow],
    ) -> PersistStats:
        if sessions:
            await self._upsert_sessions(sessions)
        if metrics:
            await self._bulk_metrics(metrics)
        metric_id_unknown = 0
        if exceptions:
            metric_id_unknown = await self._bulk_exceptions(exceptions)
        return PersistStats(
            rows=len(metrics) + len(exceptions),
            metric_id_unknown=metric_id_unknown,
        )

    async def _upsert_sessions(self, sessions: list[SessionRow]) -> None:
        """user_session ON CONFLICT (session_id) DO NOTHING — app_id es el
        tenant autenticado (RUM-6, IAUTH-2)."""
        await self._session.execute(
            pg_insert(UserSession.__table__)
            .values(
                [
                    {
                        "session_id": row.session_id,
                        "app_id": row.app_id,
                        "user_agent": row.user_agent,
                        "start_timestamp": row.start_timestamp,
                    }
                    for row in sessions
                ]
            )
            .on_conflict_do_nothing(index_elements=["session_id"])
        )

    async def _bulk_metrics(self, metrics: list[MetricRow]) -> None:
        """Bulk insert rum_metric con type → metric_type_id del catálogo."""
        await self._session.execute(
            insert(RumMetric.__table__)
            .values(
                [
                    {
                        "metric_id": row.metric_id,
                        "session_id": row.session_id,
                        "metric_type_id": await self._metric_type_id(
                            row.metric_type
                        ),
                        "value": row.value,
                        "unit": row.unit,
                        "page_url": row.page_url,
                        "metadata": row.metadata,
                        "timestamp": row.timestamp,
                    }
                    for row in metrics
                ]
            )
        )

    async def _bulk_exceptions(self, exceptions: list[ExceptionRow]) -> int:
        """Bulk insert js_exception; metric_id inexistente → NULL + contador."""
        claimed = {row.metric_id for row in exceptions if row.metric_id is not None}
        existing: set = set()
        if claimed:
            result = await self._session.execute(
                select(RumMetric.metric_id).where(RumMetric.metric_id.in_(claimed))
            )
            existing = set(result.scalars())
        unknown = 0
        rows = []
        for row in exceptions:
            metric_id = row.metric_id
            if metric_id is not None and metric_id not in existing:
                unknown += 1
                metric_id = None
            rows.append(
                {
                    "error_id": row.error_id,
                    "session_id": row.session_id,
                    "metric_id": metric_id,
                    "error_type": row.error_type,
                    "message": row.message,
                    "stack_trace": row.stack_trace,
                    "timestamp": row.timestamp,
                }
            )
        if rows:
            await self._session.execute(insert(JsException.__table__).values(rows))
        return unknown

    async def _metric_type_id(self, name: str) -> int:
        """Resuelve el id del catálogo metric_type, cacheado por nombre."""
        cached = self.metric_type_cache.get(name)
        if cached is not None:
            return cached
        result = await self._session.execute(
            text("SELECT metric_type_id FROM metric_type WHERE name = :name"),
            {"name": name},
        )
        type_id = result.scalar_one()
        self.metric_type_cache[name] = type_id
        return type_id
