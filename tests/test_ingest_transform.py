"""Unit: transformación de eventos encolados a filas de persistencia
(ISS-S3-06, #45).

`_build_rows` es la frontera entre el payload canónico que valida el
servicio y las filas que escribe el repositorio: decide a qué sesión y a qué
tenant va cada métrica y excepción. `_parse_ts` convierte los timestamps.
Ambos son puros, así que se prueban sin Postgres ni workers. Al final se
fija el registro de contadores de `_persist_chunk` con un repositorio y una
sesión falsos.
"""

from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest

from api.domain.repositories.ingest_repository import PersistStats
from api.infrastructure.ingest import queue as queue_module
from api.infrastructure.ingest.counters import IngestCounters
from api.infrastructure.ingest.queue import (
    AsyncioIngestQueue,
    QueuedEvent,
    _build_rows,
    _parse_ts,
)

TS = "2026-11-08T12:00:00+00:00"
TS_DT = datetime(2026, 11, 8, 12, 0, tzinfo=timezone.utc)


def _metric_event(session_id, tenant, **payload_overrides) -> QueuedEvent:
    payload = {
        "schema_version": "1.0",
        "timestamp": TS,
        "session_id": str(session_id),
        "metrics": [{"type": "TTFB", "value": 120.0, "unit": "ms", "timestamp": TS}],
    }
    payload.update(payload_overrides)
    return QueuedEvent(
        batch_id=uuid4(), index=0, tenant_app_id=tenant, kind="metric", payload=payload
    )


def _exception_event(session_id, tenant, **payload_overrides) -> QueuedEvent:
    payload = {
        "schema_version": "1.0",
        "error_type": "TypeError",
        "message": "boom",
        "session_id": str(session_id),
        "timestamp": TS,
    }
    payload.update(payload_overrides)
    return QueuedEvent(
        batch_id=uuid4(), index=0, tenant_app_id=tenant, kind="exception", payload=payload
    )


# -- _parse_ts ----------------------------------------------------------------

def test_parse_ts_accepts_offset_zulu_and_datetime():
    """ISO con offset, con `Z` y un `datetime` ya construido → datetime aware."""
    assert _parse_ts(TS) == TS_DT
    assert _parse_ts("2026-11-08T12:00:00Z") == TS_DT
    assert _parse_ts(TS_DT) is TS_DT


@pytest.mark.parametrize("raw", ["2026-11-08T12:00:00", "basura", "", 1731067200, None, []])
def test_parse_ts_returns_none_instead_of_inventing(raw):
    """Naive, no parseable o de otro tipo → None: nunca se inventa un instante
    (la columna NOT NULL lo rechaza después, ISS-S3-02)."""
    assert _parse_ts(raw) is None


# -- _build_rows: sesiones y tenant -------------------------------------------

def test_build_rows_creates_one_session_per_session_id_with_tenant_from_key():
    """Varios eventos de la misma sesión en un chunk → UNA SessionRow, con el
    tenant del evento encolado (la key), no el `application_id` del payload."""
    session_id, tenant = uuid4(), uuid4()
    chunk = [
        _metric_event(session_id, tenant, application_id=str(uuid4())),
        _exception_event(session_id, tenant),
    ]

    sessions, metrics, exceptions = _build_rows(chunk)

    (session_row,) = sessions
    assert session_row.session_id == session_id
    assert session_row.app_id == tenant
    assert session_row.start_timestamp == TS_DT
    assert len(metrics) == 1 and len(exceptions) == 1


def test_build_rows_takes_user_agent_from_metadata_when_present():
    """`user_agent` sale de `metadata.user_agent`; sin metadata, sin la clave
    o en una excepción (que no tiene metadata) queda None. El schema Pydantic
    garantiza que `metadata` llega como objeto o None."""
    tenant = uuid4()
    chunk = [
        _metric_event(uuid4(), tenant, metadata={"user_agent": "Mozilla/5.0"}),
        _metric_event(uuid4(), tenant, metadata={"page_url": "https://sitio/"}),
        _metric_event(uuid4(), tenant, metadata=None),
        _exception_event(uuid4(), tenant),
    ]

    sessions, _, _ = _build_rows(chunk)

    assert [row.user_agent for row in sessions] == ["Mozilla/5.0", None, None, None]


def test_build_rows_never_copies_identity_fields_into_the_session():
    """`user_id`, `ip_address` y `os_version` del payload NO DEBEN llegar a
    la sesión: SessionRow ni siquiera los modela (ADR-0011)."""
    event = _metric_event(
        uuid4(),
        uuid4(),
        metadata={"user_id": str(uuid4()), "ip_address": "203.0.113.7", "os_version": "14"},
    )

    (session_row,), _, _ = _build_rows([event])

    assert not {"user_id", "ip_address", "os_version"} & set(vars(session_row))


# -- _build_rows: métricas ----------------------------------------------------

def test_build_rows_maps_each_metric_with_its_own_fields():
    """Cada métrica del array es una fila con tipo, valor, unidad, timestamp
    parseado y metadata propia; el `metric_id` lo genera el servidor."""
    session_id = uuid4()
    event = _metric_event(
        session_id,
        uuid4(),
        metrics=[
            {"type": "TTFB", "value": 120.0, "unit": "ms", "timestamp": TS,
             "metadata": {"agent_version": "1.0.0"}},
            {"type": "FCP", "value": 900.0, "unit": "ms", "timestamp": TS},
        ],
    )

    _, metrics, _ = _build_rows([event])

    assert [(m.metric_type, m.value, m.unit) for m in metrics] == [
        ("TTFB", 120.0, "ms"),
        ("FCP", 900.0, "ms"),
    ]
    assert all(m.session_id == session_id and m.timestamp == TS_DT for m in metrics)
    assert metrics[0].metadata == {"agent_version": "1.0.0"}
    assert metrics[1].metadata is None
    assert isinstance(metrics[0].metric_id, UUID)
    assert metrics[0].metric_id != metrics[1].metric_id


def test_build_rows_page_url_prefers_metric_then_event_metadata():
    """`page_url` de la métrica gana; si falta, se usa `metadata.page_url`
    del evento; si no hay ninguno, None."""
    tenant = uuid4()
    own = {"type": "TTFB", "value": 1.0, "unit": "ms", "timestamp": TS,
           "page_url": "https://sitio/propia"}
    inherited = {"type": "FCP", "value": 2.0, "unit": "ms", "timestamp": TS}
    with_fallback = _metric_event(
        uuid4(), tenant, metrics=[own, inherited],
        metadata={"page_url": "https://sitio/evento"},
    )
    without = _metric_event(uuid4(), tenant, metrics=[dict(inherited)], metadata=None)

    _, metrics, _ = _build_rows([with_fallback, without])

    assert [m.page_url for m in metrics] == [
        "https://sitio/propia",
        "https://sitio/evento",
        None,
    ]


# -- _build_rows: excepciones -------------------------------------------------

def test_build_rows_maps_exception_fields_and_optional_metric_id():
    """La excepción conserva sus campos; `metric_id` se parsea a UUID si viene
    y queda None si no (correlación blanda, D-06)."""
    tenant, session_id, metric_id = uuid4(), uuid4(), uuid4()
    correlated = _exception_event(
        session_id, tenant, metric_id=str(metric_id), stack_trace="at x", sample_rate=0.5
    )
    loose = _exception_event(session_id, tenant)

    _, metrics, exceptions = _build_rows([correlated, loose])

    assert metrics == []
    first, second = exceptions
    assert (first.error_type, first.message, first.stack_trace) == ("TypeError", "boom", "at x")
    assert first.metric_id == metric_id
    assert first.sample_rate == 0.5
    assert first.timestamp == TS_DT
    assert second.metric_id is None
    assert second.stack_trace is None
    assert second.sample_rate is None


# -- _persist_chunk: contadores desde PersistStats ----------------------------

class _FakeDbSession:
    """Sesión async mínima usada como context manager por el worker."""

    def __init__(self) -> None:
        self.committed = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc_info):
        return False

    async def commit(self):
        self.committed = True


def _queue_with_stats(monkeypatch, stats: PersistStats, counters: IngestCounters):
    """Cola cuyo repositorio devuelve `stats` y cuya BD es un fake."""
    created: list[_FakeDbSession] = []

    def _factory():
        db_session = _FakeDbSession()
        created.append(db_session)
        return db_session

    monkeypatch.setattr(queue_module, "get_session_factory", lambda: _factory)

    class _Repo:
        def __init__(self, _session) -> None:
            pass

        async def persist_chunk(self, sessions, metrics, exceptions):
            return stats

    queue = AsyncioIngestQueue(
        maxsize=10, worker_count=0, repository_factory=_Repo, counters=counters
    )
    return queue, created


async def test_persist_chunk_records_ownership_and_correlation_counters(monkeypatch):
    """Lo que informa el repositorio en PersistStats DEBE llegar a los
    contadores `ingest.*` (RUM-8, DD-10), y el chunk se commitea."""
    counters = IngestCounters()
    stats = PersistStats(rows=3, metric_id_unknown=1, session_foreign=2, metric_id_foreign=1)
    queue, created = _queue_with_stats(monkeypatch, stats, counters)

    chunk = [_metric_event(uuid4(), uuid4())]
    await queue._persist_chunk(chunk)  # pylint: disable=protected-access

    snapshot = counters.snapshot()
    assert snapshot["ingest.persisted_total"] == 3
    assert snapshot["ingest.metric_id_unknown_total"] == 1
    assert snapshot["ingest.session_foreign_total"] == 2
    assert snapshot["ingest.metric_id_foreign_total"] == 1
    assert created[0].committed is True


async def test_persist_chunk_without_rows_skips_the_database(monkeypatch):
    """Un evento métrico con `metrics` vacío no produce filas: el worker NO
    DEBE abrir sesión ni tocar contadores."""
    counters = IngestCounters()
    queue, created = _queue_with_stats(
        monkeypatch, PersistStats(rows=0, metric_id_unknown=0), counters
    )

    chunk = [_metric_event(uuid4(), uuid4(), metrics=[])]
    await queue._persist_chunk(chunk)  # pylint: disable=protected-access

    assert created == []
    assert counters.snapshot()["ingest.persisted_total"] == 0
