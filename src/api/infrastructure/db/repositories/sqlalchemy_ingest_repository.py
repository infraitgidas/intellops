"""Implementación SQLAlchemy async del IngestRepository (DD-3, ADR-10).

Insert Core por chunk: user_session ON CONFLICT DO NOTHING, bulk rum_metric
con `metric_type` resuelto contra el catálogo cacheado, bulk js_exception con
`metric_id` de correlación scoped por ownership (RUM-10). NO commitea
(ADR-10): el worker coordina commit/rollback por chunk y aplica retry
transitorio / dead-letter (DD-4).

Ownership (DD-8/RUM-9): `_upsert_sessions` resuelve ANTES del insert qué
session_id del chunk ya existen bajo OTRA aplicación → sesiones extranjeras;
`persist_chunk` descarta (y cuenta en `session_foreign`) las métricas y
excepciones que las referencian. La correlación `metric_id` solo se
reivindica si la métrica existe Y pertenece a una sesión del mismo tenant
del lote; si no → NULL + contador (foreign o unknown).
"""

# pylint: disable=too-few-public-methods  # repositorio con un solo método público

from uuid import UUID

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
        session_foreign = 0
        if sessions:
            foreign = await self._upsert_sessions(sessions)
            if foreign:
                # DD-8/RUM-9: las filas que referencian una sesión extranjera
                # se descartan del chunk y se cuentan (C5: replay cross-tenant).
                kept_metrics = [m for m in metrics if m.session_id not in foreign]
                kept_exceptions = [
                    e for e in exceptions if e.session_id not in foreign
                ]
                session_foreign = (len(metrics) - len(kept_metrics)) + (
                    len(exceptions) - len(kept_exceptions)
                )
                metrics, exceptions = kept_metrics, kept_exceptions
        if metrics:
            await self._bulk_metrics(metrics)
        metric_id_unknown = 0
        metric_id_foreign = 0
        if exceptions:
            session_tenants = {row.session_id: row.app_id for row in sessions}
            metric_id_unknown, metric_id_foreign = await self._bulk_exceptions(
                exceptions, session_tenants
            )
        return PersistStats(
            rows=len(metrics) + len(exceptions),
            metric_id_unknown=metric_id_unknown,
            session_foreign=session_foreign,
            metric_id_foreign=metric_id_foreign,
        )

    async def _upsert_sessions(self, sessions: list[SessionRow]) -> set[UUID]:
        """user_session ON CONFLICT (session_id) DO NOTHING — app_id es el
        tenant autenticado (RUM-6, IAUTH-2).

        Resuelve ownership ANTES del insert (DD-8): un session_id que ya
        existe bajo OTRA aplicación es extranjero y se devuelve para que
        `persist_chunk` descarte las filas que lo referencian (el ON
        CONFLICT DO NOTHING lo deja no-op; los datos del dueño quedan
        intactos, C5). Un session_id del mismo tenant → no-op sin descarte.
        """
        result = await self._session.execute(
            select(UserSession.session_id, UserSession.app_id).where(
                UserSession.session_id.in_([row.session_id for row in sessions])
            )
        )
        owned = {row.session_id: row.app_id for row in result}
        foreign = {
            row.session_id
            for row in sessions
            if row.session_id in owned and owned[row.session_id] != row.app_id
        }
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
        return foreign

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

    async def _bulk_exceptions(
        self,
        exceptions: list[ExceptionRow],
        session_tenants: dict[UUID, UUID],
    ) -> tuple[int, int]:
        """Bulk insert js_exception con correlación metric_id scoped (RUM-10).

        Un metric_id solo se reivindica si la métrica existe Y pertenece a
        una sesión del MISMO tenant del lote (DD-8): inexistente → NULL +
        `metric_id_unknown`; existente pero de otro tenant → NULL +
        `metric_id_foreign`. Devuelve (unknown, foreign).
        """
        claimed = {row.metric_id for row in exceptions if row.metric_id is not None}
        metric_session: dict[UUID, UUID] = {}
        session_tenant: dict[UUID, UUID] = {}
        if claimed:
            result = await self._session.execute(
                select(RumMetric.metric_id, RumMetric.session_id).where(
                    RumMetric.metric_id.in_(claimed)
                )
            )
            metric_session = {row.metric_id: row.session_id for row in result}
            if metric_session:
                result = await self._session.execute(
                    select(UserSession.session_id, UserSession.app_id).where(
                        UserSession.session_id.in_(list(metric_session.values()))
                    )
                )
                session_tenant = {row.session_id: row.app_id for row in result}
        unknown = 0
        foreign = 0
        rows = []
        for row in exceptions:
            metric_id = row.metric_id
            if metric_id is not None:
                metric_session_id = metric_session.get(metric_id)
                if metric_session_id is None:
                    unknown += 1  # la métrica no existe (RUM-6)
                    metric_id = None
                elif (
                    session_tenant.get(metric_session_id)
                    != session_tenants.get(row.session_id)
                ):
                    foreign += 1  # existe pero es de otro tenant (RUM-10)
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
        return unknown, foreign

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
