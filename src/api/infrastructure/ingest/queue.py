"""Ingest queue port and in-process implementation (RUM-5, DD-1).

`IngestQueue` is the port (Protocol: enqueue/close/join) — migrable to a
durable broker without touching routers/service (Pipeline §3). `QueuedEvent`
carries the tenant ALREADY resolved from the API key (D2/IAUTH-2): the
worker never derives authority from the payload.

`AsyncioIngestQueue` wraps `asyncio.Queue(maxsize)` with N worker tasks:
enqueue = put_nowait (QueueFull or closed → 503 queue_full, backpressure),
workers drain in chunks of 500 with retry on transient DB errors and
dead-letter on permanent ones (RUM-6, DD-3/DD-4). Shutdown: close() → no
new events; join(timeout) drains with a bounded timeout, logging any
unpersisted events (RUM-7, DD-6).
"""

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Protocol
from uuid import UUID, uuid4

import sqlalchemy.exc
from sqlalchemy.ext.asyncio import AsyncSession

from api.domain.exceptions import ServiceUnavailableError
from api.domain.repositories.ingest_repository import (
    ExceptionRow,
    IngestRepository,
    MetricRow,
    PersistStats,
    SessionRow,
)
from api.infrastructure.db.session import get_session_factory
from api.infrastructure.ingest.counters import IngestCounters

logger = logging.getLogger(__name__)

# Errores transitorios de BD: se reintentan con backoff (DD-4). El resto
# (p. ej. IntegrityError por constraint) es permanente → dead-letter.
TRANSIENT_DB_ERRORS = (
    sqlalchemy.exc.OperationalError,
    sqlalchemy.exc.TimeoutError,
    asyncio.TimeoutError,
)

DEFAULT_CHUNK_SIZE = 500
DEFAULT_RETRY_DELAYS = (0.5, 1.0, 2.0)


@dataclass(frozen=True)
class QueuedEvent:
    """Evento ya validado y encolado para el worker.

    `payload` es el dict JSON del evento (RumEvent/JsExceptionEvent) tal
    como llegó, sin reinterpretación de tenant.
    """

    batch_id: UUID
    index: int
    tenant_app_id: UUID
    kind: str  # "metric" | "exception"
    payload: dict = field(default_factory=dict)


class IngestQueue(Protocol):
    """Puerto de cola de ingesta — abstrae el broker (Pipeline §3).

    `enqueue` NUNCA bloquea: cola llena o cerrada → ServiceUnavailableError
    (503 queue_full, RUM-5). `close` deja de aceptar eventos; `join` drena
    los pendientes con timeout acotado (D6, RUM-7).
    """

    async def enqueue(self, event: QueuedEvent) -> None:
        """Encola un evento; 503 queue_full si la cola está llena o cerrada."""
        ...

    async def close(self) -> None:
        """Cierra la cola: enqueue nuevo → 503 (RUM-7)."""
        ...

    async def join(self, timeout: float) -> None:
        """Espera a que se procesen los eventos pendientes (drenado)."""
        ...


class AsyncioIngestQueue:
    """Cola en proceso sobre asyncio.Queue(maxsize) + N workers (DD-1)."""

    def __init__(
        self,
        *,
        maxsize: int,
        worker_count: int,
        repository_factory: Callable[[AsyncSession], IngestRepository],
        counters: IngestCounters,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        retry_delays: tuple[float, ...] = DEFAULT_RETRY_DELAYS,
    ) -> None:
        self._queue: asyncio.Queue[QueuedEvent] = asyncio.Queue(maxsize=maxsize)
        self._closed = False
        self._worker_count = worker_count
        self._repository_factory = repository_factory
        self._counters = counters
        self._chunk_size = chunk_size
        self._retry_delays = retry_delays
        self._workers: list[asyncio.Task] = []
        self._in_flight = 0
        self._metric_type_cache: dict[str, int] = {}

    def qsize(self) -> int:
        """Ocupación actual de la cola (gauge ingest.queue_depth)."""
        return self._queue.qsize()

    async def start(self) -> None:
        """Lanza los worker tasks (lifespan startup, DD-1)."""
        for _ in range(self._worker_count):
            task = asyncio.create_task(self._worker_loop(), name="ingest-worker")
            self._workers.append(task)

    async def enqueue(self, event: QueuedEvent) -> None:
        """put_nowait: cola llena o cerrada → 503 queue_full, sin bloquear."""
        if self._closed:
            raise ServiceUnavailableError(
                "ingest queue is closed", code="queue_full"
            )
        try:
            self._queue.put_nowait(event)
        except asyncio.QueueFull as exc:
            raise ServiceUnavailableError(
                "ingest queue is full", code="queue_full"
            ) from exc

    async def close(self) -> None:
        """Deja de aceptar eventos nuevos; el drenado ocurre en join() (D6)."""
        self._closed = True

    async def join(self, timeout: float) -> None:
        """Drena lo pendiente con timeout acotado; lo no persistido se loguea
        explícitamente (RUM-7, escenario Timeout de drenado)."""
        try:
            await asyncio.wait_for(self._queue.join(), timeout=timeout)
        except asyncio.TimeoutError:
            remaining = self._queue.qsize() + self._in_flight
            logger.warning(
                "ingest shutdown timeout: %d events not persisted", remaining
            )
        finally:
            for worker in self._workers:
                worker.cancel()
            await asyncio.gather(*self._workers, return_exceptions=True)
            self._workers = []

    async def _worker_loop(self) -> None:
        """Consume la cola agrupando en chunks de `chunk_size` filas.

        El chunk parcial se persiste cuando la cola queda vacía (drenado
        eficiente sin wait_for). task_done() se llama SOLO tras persistir:
        así join() espera la persistencia real, no el get().
        """
        chunk: list[QueuedEvent] = []
        while True:
            try:
                event = self._queue.get_nowait()
            except asyncio.QueueEmpty:
                if chunk:
                    await self._persist_chunk(chunk)
                    for _ in chunk:
                        self._queue.task_done()
                    chunk = []
                try:
                    event = await self._queue.get()
                except asyncio.CancelledError:
                    return
            self._in_flight += 1
            chunk.append(event)
            if len(chunk) >= self._chunk_size:
                await self._persist_chunk(chunk)
                for _ in chunk:
                    self._queue.task_done()
                self._in_flight -= len(chunk)
                chunk = []

    async def _persist_chunk(self, chunk: list[QueuedEvent]) -> None:
        """Persiste el chunk con retry transitorio y dead-letter (RUM-6, DD-4)."""
        sessions, metrics, exceptions = _build_rows(chunk)
        if not metrics and not exceptions:
            return
        stats: PersistStats | None = None
        for attempt, delay in enumerate(self._retry_delays, 1):
            try:
                async with get_session_factory()() as session:
                    repo = self._repository_factory(session)
                    if hasattr(repo, "metric_type_cache"):
                        repo.metric_type_cache = self._metric_type_cache
                    stats = await repo.persist_chunk(sessions, metrics, exceptions)
                    await session.commit()
                break
            except TRANSIENT_DB_ERRORS:
                if attempt == len(self._retry_delays):
                    logger.exception(
                        "ingest chunk transient failures exhausted: %d events "
                        "dead-lettered", len(chunk)
                    )
                    self._dead_letter(chunk)
                    return
                await asyncio.sleep(delay)
            except Exception:  # pylint: disable=broad-exception-caught
                logger.exception(
                    "ingest chunk persistence failed: %d events dead-lettered",
                    len(chunk),
                )
                self._dead_letter(chunk)
                return
        assert stats is not None
        self._counters.persisted(stats.rows)
        if stats.metric_id_unknown:
            self._counters.metric_id_unknown(stats.metric_id_unknown)

    def _dead_letter(self, chunk: list[QueuedEvent]) -> None:
        """Dead-letter: log + contador, nunca pérdida silenciosa (RUM-6)."""
        self._counters.dead_letter(1)
        logger.error(
            "ingest chunk dead-lettered: %d events not persisted",
            len(chunk),
            extra={"batch_ids": sorted({str(e.batch_id) for e in chunk})},
        )


def _build_rows(
    chunk: list[QueuedEvent],
) -> tuple[list[SessionRow], list[MetricRow], list[ExceptionRow]]:
    """Mapea eventos encolados a filas del repositorio (tenant ya resuelto)."""
    sessions: dict[UUID, SessionRow] = {}
    metrics: list[MetricRow] = []
    exceptions: list[ExceptionRow] = []
    for event in chunk:
        payload = event.payload
        session_id = UUID(payload["session_id"])
        ts = _parse_ts(payload.get("timestamp"))
        if session_id not in sessions:
            user_agent = None
            metadata = payload.get("metadata")
            if isinstance(metadata, dict):
                user_agent = metadata.get("user_agent")
            sessions[session_id] = SessionRow(
                session_id=session_id,
                app_id=event.tenant_app_id,
                start_timestamp=ts or datetime.now(timezone.utc),
                user_agent=user_agent,
            )
        if event.kind == "metric":
            event_metadata = payload.get("metadata") or {}
            for metric in payload.get("metrics", []):
                metric_ts = metric.get("timestamp") or payload.get("timestamp")
                metrics.append(
                    MetricRow(
                        metric_id=uuid4(),
                        session_id=session_id,
                        metric_type=metric["type"],
                        value=float(metric["value"]),
                        unit=metric["unit"],
                        timestamp=_parse_ts(metric_ts) or datetime.now(timezone.utc),
                        page_url=metric.get("page_url")
                        or event_metadata.get("page_url"),
                        metadata=metric.get("metadata"),
                    )
                )
        elif event.kind == "exception":
            metric_id = payload.get("metric_id")
            exceptions.append(
                ExceptionRow(
                    error_id=uuid4(),
                    session_id=session_id,
                    error_type=payload["error_type"],
                    message=payload["message"],
                    timestamp=ts or datetime.now(timezone.utc),
                    metric_id=UUID(metric_id) if metric_id else None,
                    stack_trace=payload.get("stack_trace"),
                )
            )
    return list(sessions.values()), metrics, exceptions


def _parse_ts(value: object) -> datetime | None:
    """Parsea un timestamp ISO 8601 del payload a datetime aware."""
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
        if parsed.tzinfo is None:
            return None
        return parsed
    return None
