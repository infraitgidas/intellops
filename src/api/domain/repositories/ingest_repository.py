"""Contrato del repositorio de ingesta (capa de dominio).

Sin commit (ADR-10): el worker coordina commit/rollback por chunk. Los DTOs
son planos para no acoplar domain a la infraestructura de cola. `metric_type`
viaja como nombre (TTFB, ...); la implementación lo resuelve contra el
catálogo cacheado. `metric_id` de correlación blanda: si la métrica no
existe, la impl persiste NULL y lo reporta en `metric_id_unknown`.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID


@dataclass(frozen=True)
class SessionRow:
    """Fila user_session — app_id es el TENANT ya resuelto desde la key."""

    session_id: UUID
    app_id: UUID
    start_timestamp: datetime
    user_agent: str | None = None


@dataclass(frozen=True)
class MetricRow:
    """Fila rum_metric — metric_type es el nombre del catálogo."""

    metric_id: UUID
    session_id: UUID
    metric_type: str
    value: float
    unit: str
    timestamp: datetime
    page_url: str | None = None
    metadata: dict | None = None


@dataclass(frozen=True)
class ExceptionRow:
    """Fila js_exception — metric_id opcional (correlación blanda)."""

    error_id: UUID
    session_id: UUID
    error_type: str
    message: str
    timestamp: datetime
    metric_id: UUID | None = None
    stack_trace: str | None = None


@dataclass(frozen=True)
class PersistStats:
    """Resultado de persistir un chunk."""

    rows: int
    metric_id_unknown: int


class IngestRepository(Protocol):
    """Persistencia del worker — mutaciones sin commit (ADR-10)."""

    async def persist_chunk(
        self,
        sessions: list[SessionRow],
        metrics: list[MetricRow],
        exceptions: list[ExceptionRow],
    ) -> PersistStats:
        """Persiste un chunk en una transacción (el worker commitea)."""
        ...