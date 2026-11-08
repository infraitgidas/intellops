"""Query repository SQLAlchemy async — read path app-scoped (DD-9, TQ-1).

`query_metrics` agrega EN SQL (una sola sentencia, sin materializar filas en
el proceso): JOIN `user_session`→`rum_metric` con `app_id = tenant`, GROUP BY
`metric_type_id` + bucket temporal (epoch anclado a `:start`), `AVG(value)` y
`COUNT(DISTINCT session_id)` → shape ML C6 `MetricAggregate`. Los índices
existentes (`idx_user_session_app_id`, `idx_rum_metric_*`) acotan el plan;
la ventana default (15 min) escanea miles de filas → < 2 s, CPU-only (TQ-2).

`list_metric_types` devuelve el catálogo `metric_type` (id, name, description)
para `GET /metrics/list` (OAS-13). Sin DDL nuevo.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Float, bindparam, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from api.domain.entities.rum_metric import RumMetric
from api.domain.entities.user_session import UserSession
from api.domain.repositories.query_repository import (
    MetricAggregate,
    MetricTypeInfo,
    QueryRepository,
)


class SQLAlchemyQueryRepository(QueryRepository):
    """QueryRepository sobre AsyncSession (PostgreSQL, asyncpg)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def query_metrics(
        self,
        app_id: UUID,
        start: datetime,
        end: datetime,
        bucket_seconds: int,
        metric_type_id: int | None = None,
    ) -> list[MetricAggregate]:
        """Métricas de `app_id` agregadas por bucket temporal (DD-9/TQ-1).

        El bucket se ancla al inicio de la ventana (`:start`): determinista y
        alineado al request, no a medianoche UTC.
        """
        ts_type = DateTime(timezone=True)
        start_p = bindparam("start", type_=ts_type)
        end_p = bindparam("end", type_=ts_type)
        bucket_p = bindparam("bucket_s")
        epoch_start = func.extract("epoch", start_p)
        epoch_ts = func.extract("epoch", RumMetric.timestamp)
        bucket_expr = func.to_timestamp(
            epoch_start
            + func.floor((epoch_ts - epoch_start) / bucket_p) * bucket_p
        )

        stmt = (
            select(
                UserSession.app_id.label("application_id"),
                RumMetric.metric_type_id.label("metric_type_id"),
                bucket_expr.label("timestamp"),
                func.avg(RumMetric.value).cast(Float).label("value"),
                func.count(func.distinct(RumMetric.session_id)).label(
                    "session_count"
                ),
            )
            .join(UserSession, UserSession.session_id == RumMetric.session_id)
            .where(
                UserSession.app_id == bindparam("app_id"),
                RumMetric.timestamp >= start_p,
                RumMetric.timestamp < end_p,
            )
            .group_by(UserSession.app_id, RumMetric.metric_type_id, bucket_expr)
            .order_by(bucket_expr, RumMetric.metric_type_id)
        )
        if metric_type_id is not None:
            stmt = stmt.where(RumMetric.metric_type_id == metric_type_id)

        result = await self._session.execute(
            stmt,
            {
                "app_id": app_id,
                "start": start,
                "end": end,
                "bucket_s": bucket_seconds,
            },
        )
        return [
            MetricAggregate(
                application_id=row.application_id,
                metric_type_id=row.metric_type_id,
                timestamp=row.timestamp,
                value=row.value,
                session_count=row.session_count,
            )
            for row in result
        ]

    async def list_metric_types(self) -> list[MetricTypeInfo]:
        """Catálogo metric_type completo (OAS-13: /metrics/list)."""
        result = await self._session.execute(
            text(
                "SELECT metric_type_id, name, description "
                "FROM metric_type ORDER BY metric_type_id"
            )
        )
        return [
            MetricTypeInfo(
                metric_type_id=row.metric_type_id,
                name=row.name,
                description=row.description,
            )
            for row in result
        ]
