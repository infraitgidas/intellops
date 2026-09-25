"""In-process ingest counters (RUM-8, D4) — no prometheus-client.

Naming contract: `ingest.` prefix, `_total` suffix (or `queue_depth`).
`rejected_total` is nested by reason: {"invalid_range": 2, ...}. Snapshot
is a plain dict — a future Prometheus adapter can map it directly (D4:
this change only maintains the counters, no /metrics endpoint).
"""

from collections import defaultdict


class IngestCounters:
    """Counters en proceso para el pipeline de ingesta (RUM-8)."""

    def __init__(self) -> None:
        self._received = 0
        self._accepted = 0
        self._rejected_by_reason: dict[str, int] = defaultdict(int)
        self._persisted = 0
        self._dead_letter = 0
        self._metric_id_unknown = 0
        self._queue_depth = 0

    def received(self, n: int = 1) -> None:
        """Eventos recibidos en el batch (antes de validación por evento)."""
        self._received += n

    def accepted(self, n: int = 1) -> None:
        """Eventos aceptados y encolados."""
        self._accepted += n

    def rejected(self, reason: str, n: int = 1) -> None:
        """Eventos rechazados por la política, agrupados por código."""
        self._rejected_by_reason[reason] += n

    def persisted(self, n: int = 1) -> None:
        """Filas insertadas por el worker."""
        self._persisted += n

    def dead_letter(self, n: int = 1) -> None:
        """Chunks que agotaron los retries (dead-letter logueada, RUM-6)."""
        self._dead_letter += n

    def metric_id_unknown(self, n: int = 1) -> None:
        """metric_id de correlación blanda inexistente → NULL (RUM-6)."""
        self._metric_id_unknown += n

    def set_queue_depth(self, n: int) -> None:
        """Ocupación actual de la cola (gauge)."""
        self._queue_depth = n

    def snapshot(self) -> dict:
        """Snapshot plano del estado de todos los contadores."""
        return {
            "ingest.received_total": self._received,
            "ingest.accepted_total": self._accepted,
            "ingest.rejected_total": dict(self._rejected_by_reason),
            "ingest.persisted_total": self._persisted,
            "ingest.persistence_dead_letter_total": self._dead_letter,
            "ingest.metric_id_unknown_total": self._metric_id_unknown,
            "ingest.queue_depth": self._queue_depth,
        }