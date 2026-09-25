"""Ingest service — two-level validation + enqueue in the request (RUM-2..4).

The envelope is validated by Pydantic at the router boundary (422 → 400 via
the scoped handler, DD-5); the service receives a batch whose envelope is
already guaranteed. Per-event policy runs here (pure, DD-2) and accepted
events are enqueued with the tenant resolved from the API key (D2/IAUTH-2).
The 202 is produced on ENQUEUE, never on persist (semantics §3.4).
"""

import logging
from uuid import UUID, uuid4

from api.domain.services.ingest_policy import (
    validate_js_exception,
    validate_rum_event,
)
from api.infrastructure.ingest.counters import IngestCounters
from api.infrastructure.ingest.queue import IngestQueue, QueuedEvent
from api.presentation.schemas.ingest import (
    IngestResponse,
    JsExceptionBatch,
    RejectedEvent,
    RumEventBatch,
)

logger = logging.getLogger(__name__)


class IngestService:
    """Valida por evento, encola los aceptados y responde el 202 (sin estado)."""

    def __init__(self, queue: IngestQueue, counters: IngestCounters) -> None:
        self._queue = queue
        self._counters = counters

    async def process_batch(
        self, batch: RumEventBatch | JsExceptionBatch, tenant_app_id: UUID
    ) -> IngestResponse:
        """Procesa un batch validado por el envelope → IngestResponse 202.

        Rechaza por evento con la política (7 códigos, sin unknown_application)
        y encola SOLO los aceptados; el tenant se fija desde la key.
        """
        if isinstance(batch, RumEventBatch):
            kind = "metric"
            validator = validate_rum_event
        else:
            kind = "exception"
            validator = validate_js_exception

        batch_id = uuid4()
        total = len(batch.events)
        self._counters.received(total)

        accepted = 0
        rejected: list[RejectedEvent] = []
        for index, event in enumerate(batch.events):
            payload = event.model_dump(mode="json")
            reason = validator(payload)
            if reason is not None:
                rejected.append(RejectedEvent(index=index, reason=reason))
                self._counters.rejected(reason)
                # ADR-23: log con batch_id/index/reason; NUNCA la X-API-Key.
                logger.warning(
                    "ingest event rejected",
                    extra={
                        "batch_id": str(batch_id),
                        "index": index,
                        "reason": reason,
                    },
                )
                continue
            await self._queue.enqueue(
                QueuedEvent(
                    batch_id=batch_id,
                    index=index,
                    tenant_app_id=tenant_app_id,
                    kind=kind,
                    payload=payload,
                )
            )
            accepted += 1

        self._counters.accepted(accepted)
        self._counters.set_queue_depth(self._queue_depth())
        return IngestResponse(
            batch_id=str(batch_id), accepted=accepted, rejected=rejected
        )

    def _queue_depth(self) -> int:
        """Profundidad de la cola para el gauge; 0 si el puerto no la expone."""
        depth = getattr(self._queue, "qsize", None)
        if callable(depth):
            try:
                return depth()
            except Exception:  # pylint: disable=broad-exception-caught
                return 0
        return 0