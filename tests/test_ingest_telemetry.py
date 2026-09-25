"""TDD: ingesta RUM asíncrona — RUM-1..RUM-8, IAUTH-2/5, OAS-11/12 (ISS-S2-03).

Strict TDD: cada escenario Given/When/Then de la spec se convierte en un
test red antes de implementar. Capas: unit (política, contadores, cola),
integration (httpx ASGI + Postgres real) y contract (openapi.yaml).
"""

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from api.domain.services.ingest_policy import (
    REJECTION_CODES,
    validate_js_exception,
    validate_rum_event,
)


def _ts() -> str:
    """Timestamp ISO 8601 UTC con zona explícita (contrato)."""
    return datetime.now(timezone.utc).isoformat()


def _rum(**overrides) -> dict:
    """Evento RUM válido base; overrides por test."""
    event = {
        "schema_version": "1.0",
        "timestamp": _ts(),
        "session_id": str(uuid4()),
        "application_id": str(uuid4()),
        "metrics": [
            {
                "type": "TTFB",
                "value": 120.5,
                "unit": "ms",
            }
        ],
        "metadata": {"page_url": "https://app.example.com/", "user_agent": "ua"},
    }
    event.update(overrides)
    return event


def _js(**overrides) -> dict:
    """Evento JS_EXCEPTION válido base; overrides por test."""
    event = {
        "schema_version": "1.0",
        "error_type": "TypeError",
        "message": "Cannot read properties of undefined",
        "stack_trace": "at line 42",
        "session_id": str(uuid4()),
        "application_id": str(uuid4()),
        "timestamp": _ts(),
    }
    event.update(overrides)
    return event


# -- RUM-4: política por evento — 7 códigos, sin unknown_application ----------

def test_policy_accepts_valid_rum_event():
    """Un evento RUM bien formado DEBE validar (None = sin rechazo)."""
    assert validate_rum_event(_rum()) is None


def test_policy_accepts_valid_js_exception():
    """Una excepción JS bien formada DEBE validar (None = sin rechazo)."""
    assert validate_js_exception(_js()) is None


def test_policy_rejects_ttfb_out_of_sanity_range_but_accepts_9000():
    """TTFB 61000 DEBE rechazarse con invalid_range; 9000 ms es dato legítimo
    de cordura y DEBE aceptarse (rango de cordura, no de calidad)."""
    assert validate_rum_event(_rum(metrics=[_metric(value=61000)])) == "invalid_range"
    assert validate_rum_event(_rum(metrics=[_metric(value=9000)])) is None


def test_policy_rejects_invalid_session_uuid():
    """session_id no-UUID DEBE rechazarse con invalid_uuid (RUM-4)."""
    assert validate_rum_event(_rum(session_id="no-es-uuid")) == "invalid_uuid"
    assert validate_js_exception(_js(session_id="no-es-uuid")) == "invalid_uuid"


def test_policy_rejects_incoherent_unit():
    """JS_EXCEPTION_RATE con unit ms DEBE rechazarse con invalid_unit."""
    event = _rum(
        metrics=[
            {"type": "JS_EXCEPTION_RATE", "value": 1, "unit": "ms"}
        ]
    )
    assert validate_rum_event(event) == "invalid_unit"


def test_policy_rejects_unknown_unit():
    """unit fuera de ms/count DEBE rechazarse con invalid_unit."""
    event = _rum(metrics=[{"type": "TTFB", "value": 100, "unit": "s"}])
    assert validate_rum_event(event) == "invalid_unit"


def test_policy_rejects_oversized_exception_stack_trace():
    """stack_trace de 20001 caracteres DEBE rechazarse con oversized_event."""
    assert validate_js_exception(_js(stack_trace="x" * 20001)) == "oversized_event"


def test_policy_rejects_oversized_error_type_and_message():
    """error_type > 100 o message > 2000 DEBEN rechazarse con oversized_event."""
    assert validate_js_exception(_js(error_type="t" * 101)) == "oversized_event"
    assert validate_js_exception(_js(message="m" * 2001)) == "oversized_event"


def test_policy_accepts_rum_without_application_id():
    """application_id fuera de required (D2): ausente DEBE aceptarse; el
    tenant viene de la key, no del payload."""
    event = _rum()
    del event["application_id"]
    assert validate_rum_event(event) is None
    js = _js()
    del js["application_id"]
    assert validate_js_exception(js) is None


def test_policy_has_no_unknown_application_code():
    """El código unknown_application NO DEBE existir en el flujo (D2)."""
    assert "unknown_application" not in REJECTION_CODES


def test_policy_rejects_missing_required_field():
    """Falta de campo obligatorio DEBE rechazarse con missing_required_field."""
    event = _rum()
    del event["session_id"]
    assert validate_rum_event(event) == "missing_required_field"
    js = _js()
    del js["message"]
    assert validate_js_exception(js) == "missing_required_field"


def test_policy_rejects_invalid_metric_type():
    """type fuera del enum DEBE rechazarse con invalid_metric_type."""
    event = _rum(metrics=[{"type": "LCP", "value": 100, "unit": "ms"}])
    assert validate_rum_event(event) == "invalid_metric_type"


def test_policy_rejects_invalid_application_uuid_when_present():
    """application_id presente pero no-UUID DEBE rechazarse con invalid_uuid
    (matriz general del contrato: todos los UUID válidos)."""
    assert validate_rum_event(_rum(application_id="no-uuid")) == "invalid_uuid"
    assert validate_js_exception(_js(application_id="no-uuid")) == "invalid_uuid"


def test_policy_rejects_naive_timestamp():
    """timestamp sin zona horaria explícita DEBE rechazarse con
    invalid_timestamp (contrato: ISO 8601 UTC con tz)."""
    assert validate_rum_event(_rum(timestamp="2026-09-25T10:00:00")) == "invalid_timestamp"
    assert validate_js_exception(_js(timestamp="2026-09-25T10:00:00")) == "invalid_timestamp"


def test_policy_rejects_garbage_timestamp():
    """timestamp no parseable DEBE rechazarse con invalid_timestamp."""
    assert validate_rum_event(_rum(timestamp="ayer a la tarde")) == "invalid_timestamp"


def test_policy_rejects_over_50_metrics_per_event():
    """Más de 50 métricas en un evento DEBE rechazarse con oversized_event
    (límite 50 por evento, RUM-4)."""
    metrics = [_metric(value=float(i)) for i in range(51)]
    assert validate_rum_event(_rum(metrics=metrics)) == "oversized_event"


def test_policy_rejects_empty_metrics():
    """Un evento sin métricas DEBE rechazarse con missing_required_field."""
    assert validate_rum_event(_rum(metrics=[])) == "missing_required_field"


def test_policy_rejects_fcp_and_ttfb_above_sanity_bounds():
    """FCP > 120000 y TTFB > 60000 DEBEN rechazarse con invalid_range."""
    assert validate_rum_event(_rum(metrics=[_metric(type_="FCP", value=120001)])) == "invalid_range"
    assert validate_rum_event(_rum(metrics=[_metric(value=60001)])) == "invalid_range"


def test_policy_accepts_sanity_boundary_values():
    """Los límites del rango de cordura DEBEN aceptarse (TTFB 60000, FCP 120000)."""
    assert validate_rum_event(_rum(metrics=[_metric(value=60000)])) is None
    assert validate_rum_event(_rum(metrics=[_metric(type_="FCP", value=120000)])) is None


def test_policy_rejects_negative_count_metrics():
    """JS_EXCEPTION_RATE/RAGE_CLICK negativos DEBEN rechazarse con invalid_range."""
    event = _rum(metrics=[{"type": "RAGE_CLICK", "value": -1, "unit": "count"}])
    assert validate_rum_event(event) == "invalid_range"


def test_policy_rejects_invalid_metric_value_type():
    """value no numérico DEBE rechazarse con invalid_range."""
    event = _rum(metrics=[{"type": "TTFB", "value": "abc", "unit": "ms"}])
    assert validate_rum_event(event) == "invalid_range"


def _metric(type_: str = "TTFB", value: float = 120.5) -> dict:
    """Métrica RUM válida base."""
    return {"type": type_, "value": value, "unit": "ms"}


# -- RUM-6/DDL: entidades mirror de openspec/specs/database/ddl_v1.0.sql ------

def test_ingest_entities_mirror_ddl_0001():
    """Las entidades DEBEN reflejar las tablas del DDL 0001 (rum_metric,
    js_exception, user_session) con sus columnas clave."""
    from api.domain.entities.js_exception import JsException
    from api.domain.entities.rum_metric import RumMetric
    from api.domain.entities.user_session import UserSession

    assert UserSession.__tablename__ == "user_session"
    assert RumMetric.__tablename__ == "rum_metric"
    assert JsException.__tablename__ == "js_exception"

    assert {"session_id", "app_id", "start_timestamp"} <= set(
        UserSession.__table__.columns.keys()
    )
    assert {"metric_id", "session_id", "metric_type_id", "value", "unit", "timestamp"} <= set(
        RumMetric.__table__.columns.keys()
    )
    assert {"error_id", "session_id", "metric_id", "error_type", "message", "timestamp"} <= set(
        JsException.__table__.columns.keys()
    )


# -- RUM-5/DD-6: config de ingesta y error 503 ---------------------------------

def test_settings_ingest_defaults():
    """Los settings de ingesta DEBEN tener defaults: maxsize 10000, 2 workers,
    timeout de shutdown 10.0 s."""
    from api.config import Settings

    settings = Settings()
    assert settings.ingest_queue_maxsize == 10000
    assert settings.ingest_workers == 2
    assert settings.ingest_shutdown_timeout == 10.0


def test_settings_ingest_env_override(monkeypatch):
    """Las variables INGEST_* DEBEN poder overridear los defaults."""
    from api.config import get_settings

    monkeypatch.setenv("INGEST_QUEUE_MAXSIZE", "5")
    monkeypatch.setenv("INGEST_WORKERS", "1")
    monkeypatch.setenv("INGEST_SHUTDOWN_TIMEOUT", "2.5")
    get_settings.cache_clear()
    try:
        settings = get_settings()
        assert settings.ingest_queue_maxsize == 5
        assert settings.ingest_workers == 1
        assert settings.ingest_shutdown_timeout == 2.5
    finally:
        get_settings.cache_clear()


def test_service_unavailable_error_is_503_queue_full():
    """ServiceUnavailableError DEBE ser 503 con código default queue_full
    (RUM-5, backpressure)."""
    from api.domain.exceptions import ServiceUnavailableError

    exc = ServiceUnavailableError("ingest queue is full")
    assert exc.http_code == 503
    assert exc.code == "queue_full"
    assert exc.message == "ingest queue is full"


# -- RUM-8/D4: contadores en proceso (prefijo ingest., sufijo _total) ----------

def test_counters_snapshot_uses_ingest_prefix_and_total_suffix():
    """El snapshot DEBE exponer claves con prefijo `ingest.` y sufijo `_total`
    (o queue_depth), incluyendo dead-letter y metric_id_unknown."""
    from api.infrastructure.ingest.counters import IngestCounters

    snapshot = IngestCounters().snapshot()
    assert "ingest.received_total" in snapshot
    assert "ingest.accepted_total" in snapshot
    assert "ingest.rejected_total" in snapshot
    assert "ingest.persisted_total" in snapshot
    assert "ingest.persistence_dead_letter_total" in snapshot
    assert "ingest.metric_id_unknown_total" in snapshot
    assert "ingest.queue_depth" in snapshot


def test_counters_received_accepted_rejected_by_reason():
    """Batch de 3 con 1 rechazado DEBE reflejar received +3, accepted +2 y
    rejected_total{reason} +1 (RUM-8, escenario Contadores en proceso)."""
    from api.infrastructure.ingest.counters import IngestCounters

    counters = IngestCounters()
    counters.received(3)
    counters.accepted(2)
    counters.rejected("invalid_range")
    counters.set_queue_depth(2)

    snapshot = counters.snapshot()
    assert snapshot["ingest.received_total"] == 3
    assert snapshot["ingest.accepted_total"] == 2
    assert snapshot["ingest.rejected_total"] == {"invalid_range": 1}
    assert snapshot["ingest.queue_depth"] == 2


def test_counters_track_persistence_and_dead_letter():
    """persisted/dead_letter/metric_id_unknown DEBEN contarse por separado."""
    from api.infrastructure.ingest.counters import IngestCounters

    counters = IngestCounters()
    counters.persisted(500)
    counters.dead_letter(1)
    counters.metric_id_unknown(2)

    snapshot = counters.snapshot()
    assert snapshot["ingest.persisted_total"] == 500
    assert snapshot["ingest.persistence_dead_letter_total"] == 1
    assert snapshot["ingest.metric_id_unknown_total"] == 2


def test_counters_rejected_accumulates_by_reason():
    """Rechazos de distintas razones DEBEN acumularse por código."""
    from api.infrastructure.ingest.counters import IngestCounters

    counters = IngestCounters()
    counters.rejected("invalid_range")
    counters.rejected("invalid_range")
    counters.rejected("invalid_uuid")
    assert counters.snapshot()["ingest.rejected_total"] == {
        "invalid_range": 2,
        "invalid_uuid": 1,
    }


# -- RUM-2/OAS-12: schemas de ingesta — envelope estricto, evento laxo --------

def test_envelope_schema_rejects_unknown_schema_version():
    """schema_version ≠ 1.0 DEBE fallar la validación del envelope (RUM-2):
    el batch completo se rechaza antes de validar por evento."""
    from pydantic import ValidationError

    from api.presentation.schemas.ingest import RumEventBatch

    with pytest.raises(ValidationError):
        RumEventBatch(schema_version="2.0", events=[_rum_event_model()])


def test_envelope_schema_rejects_501_events():
    """Un envelope con 501 eventos DEBE fallar la validación (RUM-2)."""
    from pydantic import ValidationError

    from api.presentation.schemas.ingest import RumEventBatch

    with pytest.raises(ValidationError):
        RumEventBatch(
            schema_version="1.0",
            events=[_rum_event_model() for _ in range(501)],
        )


def test_envelope_schema_rejects_empty_events():
    """Un envelope sin eventos DEBE fallar la validación (RUM-2)."""
    from pydantic import ValidationError

    from api.presentation.schemas.ingest import RumEventBatch

    with pytest.raises(ValidationError):
        RumEventBatch(schema_version="1.0", events=[])


def test_rum_event_schema_application_id_optional():
    """application_id DEBE estar fuera de required en RumEvent (OAS-12, D2)."""
    from api.presentation.schemas.ingest import RumEvent

    event = RumEvent(
        schema_version="1.0",
        timestamp=_ts(),
        session_id=str(uuid4()),
        metrics=[{"type": "TTFB", "value": 100, "unit": "ms"}],
    )
    assert event.application_id is None
    assert "application_id" not in event.model_fields_set


def test_js_exception_schema_application_id_optional():
    """application_id DEBE estar fuera de required en JsExceptionEvent
    (OAS-12, D2)."""
    from api.presentation.schemas.ingest import JsExceptionEvent

    event = JsExceptionEvent(
        schema_version="1.0",
        error_type="TypeError",
        message="boom",
        session_id=str(uuid4()),
        timestamp=_ts(),
    )
    assert event.application_id is None


def test_rum_event_schema_accepts_over_50_metrics():
    """El schema del EVENTO NO DEBE fijar maxItems en metrics: el límite de 50
    lo aplica la política por evento (202 parcial con oversized_event, RUM-4)."""
    from api.presentation.schemas.ingest import RumEvent

    metrics = [{"type": "TTFB", "value": float(i), "unit": "ms"} for i in range(51)]
    event = RumEvent(
        schema_version="1.0",
        timestamp=_ts(),
        session_id=str(uuid4()),
        metrics=metrics,
    )
    assert len(event.metrics) == 51


# -- RUM-2/3: IngestService.process_batch — 202 parcial al encolar -------------

async def test_service_process_batch_returns_202_with_batch_id_and_totals():
    """Un batch válido DEBE devolver IngestResponse con batch_id UUID,
    accepted + len(rejected) == total y 202 al encolar, no al persistir
    (RUM-3, semántica §3.4)."""
    from api.domain.services.ingest_service import IngestService
    from api.infrastructure.ingest.counters import IngestCounters
    from api.presentation.schemas.ingest import IngestResponse, RumEventBatch

    fake_queue = _FakeQueue()
    service = IngestService(queue=fake_queue, counters=IngestCounters())
    batch = RumEventBatch(
        schema_version="1.0", events=[_rum_event_model(), _rum_event_model()]
    )

    result = await service.process_batch(batch, tenant_app_id=uuid4())

    assert isinstance(result, IngestResponse)
    assert result.accepted == 2
    assert result.rejected == []
    assert len(fake_queue.enqueued) == 2
    # batch_id es UUID generado por el servidor (correlación; no se persiste).
    from uuid import UUID as _UUID

    assert _UUID(result.batch_id)


async def test_service_process_batch_partial_rejection_with_index_and_reason():
    """Batch mixto de 3 con 1 inválido en la posición 1 DEBE devolver 202 con
    rejected [{index: 1, reason}] y encolar solo 2 (RUM-3, escenario Batch
    mixto)."""
    from api.domain.services.ingest_service import IngestService
    from api.infrastructure.ingest.counters import IngestCounters
    from api.presentation.schemas.ingest import RumEventBatch

    fake_queue = _FakeQueue()
    service = IngestService(queue=fake_queue, counters=IngestCounters())
    valid = _rum_event_model()
    invalid = _rum_event_model(session_id="no-es-uuid")
    batch = RumEventBatch(
        schema_version="1.0", events=[valid, invalid, _rum_event_model()]
    )

    result = await service.process_batch(batch, tenant_app_id=uuid4())

    assert result.accepted == 2
    assert len(result.rejected) == 1
    assert result.rejected[0].index == 1
    assert result.rejected[0].reason == "invalid_uuid"
    assert result.accepted + len(result.rejected) == 3
    assert len(fake_queue.enqueued) == 2


async def test_service_process_batch_all_invalid_returns_accepted_zero():
    """Batch bien formado con todos los eventos inválidos DEBE devolver 202 con
    accepted 0 y los N índices rechazados (el nivel evento no rechaza el
    batch, RUM-3, escenario Batch íntegramente inválido)."""
    from api.domain.services.ingest_service import IngestService
    from api.infrastructure.ingest.counters import IngestCounters
    from api.presentation.schemas.ingest import RumEventBatch

    fake_queue = _FakeQueue()
    service = IngestService(queue=fake_queue, counters=IngestCounters())
    batch = RumEventBatch(
        schema_version="1.0",
        events=[
            _rum_event_model(session_id="no-es-uuid"),
            _rum_event_model(session_id="tampoco"),
        ],
    )

    result = await service.process_batch(batch, tenant_app_id=uuid4())

    assert result.accepted == 0
    assert [r.index for r in result.rejected] == [0, 1]
    assert fake_queue.enqueued == []


async def test_service_process_batch_queued_event_carries_tenant_from_key():
    """Los eventos encolados DEBEN llevar tenant_app_id fijado desde la key
    (D2/IAUTH-2) y el índice original, no el application_id del payload."""
    from api.domain.services.ingest_service import IngestService
    from api.infrastructure.ingest.counters import IngestCounters
    from api.presentation.schemas.ingest import RumEventBatch

    tenant = uuid4()
    fake_queue = _FakeQueue()
    service = IngestService(queue=fake_queue, counters=IngestCounters())
    payload_claims_other_app = _rum_event_model(application_id=str(uuid4()))
    batch = RumEventBatch(schema_version="1.0", events=[payload_claims_other_app])

    result = await service.process_batch(batch, tenant_app_id=tenant)

    assert result.accepted == 1
    queued = fake_queue.enqueued[0]
    assert queued.tenant_app_id == tenant
    assert queued.index == 0
    assert queued.kind == "metric"


async def test_service_process_batch_uses_correct_kind_for_exceptions():
    """JsExceptionBatch DEBE encolar eventos kind=exception."""
    from api.domain.services.ingest_service import IngestService
    from api.infrastructure.ingest.counters import IngestCounters
    from api.presentation.schemas.ingest import JsExceptionBatch

    fake_queue = _FakeQueue()
    service = IngestService(queue=fake_queue, counters=IngestCounters())
    batch = JsExceptionBatch(
        schema_version="1.0",
        events=[
            {
                "schema_version": "1.0",
                "error_type": "TypeError",
                "message": "boom",
                "session_id": str(uuid4()),
                "timestamp": _ts(),
            }
        ],
    )

    result = await service.process_batch(batch, tenant_app_id=uuid4())

    assert result.accepted == 1
    assert fake_queue.enqueued[0].kind == "exception"


async def test_service_process_batch_updates_counters():
    """Un batch de 3 con 1 rechazado DEBE actualizar received +3, accepted +2
    y rejected_total{reason} +1 (RUM-8)."""
    from api.domain.services.ingest_service import IngestService
    from api.infrastructure.ingest.counters import IngestCounters
    from api.presentation.schemas.ingest import RumEventBatch

    fake_queue = _FakeQueue()
    counters = IngestCounters()
    service = IngestService(queue=fake_queue, counters=counters)
    batch = RumEventBatch(
        schema_version="1.0",
        events=[
            _rum_event_model(),
            _rum_event_model(session_id="no-es-uuid"),
            _rum_event_model(),
        ],
    )

    await service.process_batch(batch, tenant_app_id=uuid4())

    snapshot = counters.snapshot()
    assert snapshot["ingest.received_total"] == 3
    assert snapshot["ingest.accepted_total"] == 2
    assert snapshot["ingest.rejected_total"] == {"invalid_uuid": 1}


class _FakeQueue:
    """Fake del puerto IngestQueue para unit tests del service (sin workers)."""

    def __init__(self) -> None:
        self.enqueued = []

    async def enqueue(self, event) -> None:
        self.enqueued.append(event)

    async def close(self) -> None:
        pass

    async def join(self, timeout: float) -> None:
        pass


def _queued_event(**overrides):
    """QueuedEvent válido base para tests de cola."""
    from api.infrastructure.ingest.queue import QueuedEvent

    base = {
        "batch_id": uuid4(),
        "index": 0,
        "tenant_app_id": uuid4(),
        "kind": "metric",
        "payload": _rum(),
    }
    base.update(overrides)
    return QueuedEvent(**base)


# -- RUM-5: AsyncioIngestQueue — backpressure 503, close, qsize ---------------

async def test_queue_enqueue_when_full_raises_503_queue_full():
    """Cola llena (maxsize 1, sin workers) DEBE responder 503 queue_full sin
    bloquear el request (RUM-5, escenario Backpressure)."""
    from api.domain.exceptions import ServiceUnavailableError
    from api.infrastructure.ingest.counters import IngestCounters
    from api.infrastructure.ingest.queue import AsyncioIngestQueue

    queue = AsyncioIngestQueue(
        maxsize=1,
        worker_count=0,
        repository_factory=_noop_repo_factory,
        counters=IngestCounters(),
    )
    await queue.enqueue(_queued_event())

    with pytest.raises(ServiceUnavailableError) as excinfo:
        await queue.enqueue(_queued_event())

    assert excinfo.value.http_code == 503
    assert excinfo.value.code == "queue_full"


async def test_queue_enqueue_after_close_raises_503_queue_full():
    """Cola cerrada DEBE rechazar enqueue nuevos con 503 (RUM-7: shutdown deja
    de aceptar eventos)."""
    from api.domain.exceptions import ServiceUnavailableError
    from api.infrastructure.ingest.counters import IngestCounters
    from api.infrastructure.ingest.queue import AsyncioIngestQueue

    queue = AsyncioIngestQueue(
        maxsize=10,
        worker_count=0,
        repository_factory=_noop_repo_factory,
        counters=IngestCounters(),
    )
    await queue.close()

    with pytest.raises(ServiceUnavailableError) as excinfo:
        await queue.enqueue(_queued_event())

    assert excinfo.value.code == "queue_full"


async def test_queue_qsize_reflects_enqueued_events():
    """qsize DEBE reflejar los eventos encolados (contador queue_depth, RUM-8)."""
    from api.infrastructure.ingest.counters import IngestCounters
    from api.infrastructure.ingest.queue import AsyncioIngestQueue

    queue = AsyncioIngestQueue(
        maxsize=10,
        worker_count=0,
        repository_factory=_noop_repo_factory,
        counters=IngestCounters(),
    )
    await queue.enqueue(_queued_event())
    await queue.enqueue(_queued_event())

    assert queue.qsize() == 2


async def test_queue_accepts_events_with_capacity():
    """Con capacidad disponible, enqueue DEBE aceptar sin excepción (RUM-5,
    escenario Encolado con capacidad)."""
    from api.infrastructure.ingest.counters import IngestCounters
    from api.infrastructure.ingest.queue import AsyncioIngestQueue

    queue = AsyncioIngestQueue(
        maxsize=10,
        worker_count=0,
        repository_factory=_noop_repo_factory,
        counters=IngestCounters(),
    )
    await queue.enqueue(_queued_event())
    assert queue.qsize() == 1


def _noop_repo_factory(session):
    """Factory de repositorio que no persiste (tests de cola sin workers)."""
    return None


# -- RUM-6: persistencia del worker (Postgres real, D1) ------------------------

async def test_worker_persists_batch_to_postgres(db_session):
    """Un batch encolado con 2 métricas y 1 excepción de una sesión nueva DEBE
    persistir filas en rum_metric/js_exception y crear user_session con el
    app_id de la app autenticada (RUM-6, escenario Persistencia verificada)."""
    from sqlalchemy import text

    from api.domain.entities.application import Application
    from api.infrastructure.db.repositories.sqlalchemy_ingest_repository import (
        SQLAlchemyIngestRepository,
    )
    from api.infrastructure.ingest.counters import IngestCounters
    from api.infrastructure.ingest.queue import AsyncioIngestQueue, QueuedEvent

    # El tenant debe existir como aplicación (FK user_session.app_id).
    tenant = uuid4()
    db_session.add(Application(app_id=tenant, name="ingest-app"))
    await db_session.commit()

    counters = IngestCounters()
    queue = AsyncioIngestQueue(
        maxsize=100,
        worker_count=1,
        repository_factory=SQLAlchemyIngestRepository,
        counters=counters,
    )
    await queue.start()
    session_id = str(uuid4())
    batch_id = uuid4()
    await queue.enqueue(
        QueuedEvent(
            batch_id=batch_id,
            index=0,
            tenant_app_id=tenant,
            kind="metric",
            payload=_rum(session_id=session_id),
        )
    )
    await queue.enqueue(
        QueuedEvent(
            batch_id=batch_id,
            index=1,
            tenant_app_id=tenant,
            kind="metric",
            payload=_rum(
                session_id=session_id,
                metrics=[{"type": "FCP", "value": 900.0, "unit": "ms"}],
            ),
        )
    )
    await queue.enqueue(
        QueuedEvent(
            batch_id=batch_id,
            index=2,
            tenant_app_id=tenant,
            kind="exception",
            payload=_js(session_id=session_id),
        )
    )
    await queue.close()
    await queue.join(timeout=5.0)

    metric_rows = (
        await db_session.execute(text("SELECT COUNT(*) FROM rum_metric"))
    ).scalar_one()
    exception_rows = (
        await db_session.execute(text("SELECT COUNT(*) FROM js_exception"))
    ).scalar_one()
    session_row = (
        await db_session.execute(
            text(
                "SELECT app_id, user_agent FROM user_session "
                "WHERE session_id = :session_id"
            ),
            {"session_id": session_id},
        )
    ).one()

    assert metric_rows == 2
    assert exception_rows == 1
    assert session_row.app_id == tenant
    assert session_row.user_agent == "ua"
    assert counters.snapshot()["ingest.persisted_total"] == 3


async def test_worker_retries_transient_db_error_then_persists():
    """Una falla transitoria de BD DEBE reintentarse con backoff y el chunk
    DEBE persistir en el intento ≤ 3 sin pérdida (RUM-6, escenario Retry
    transitorio)."""
    import sqlalchemy.exc

    from api.domain.repositories.ingest_repository import PersistStats
    from api.infrastructure.ingest.counters import IngestCounters
    from api.infrastructure.ingest.queue import AsyncioIngestQueue

    class _FlakyRepo:
        def __init__(self) -> None:
            self.calls = 0
            self.metric_type_cache = {}

        async def persist_chunk(self, sessions, metrics, exceptions):
            self.calls += 1
            if self.calls <= 2:
                raise sqlalchemy.exc.OperationalError(
                    "statement", {}, Exception("connection lost")
                )
            return PersistStats(
                rows=len(metrics) + len(exceptions), metric_id_unknown=0
            )

    flaky = _FlakyRepo()
    counters = IngestCounters()
    queue = AsyncioIngestQueue(
        maxsize=10,
        worker_count=1,
        repository_factory=lambda session: flaky,
        counters=counters,
        retry_delays=(0.0, 0.0, 0.0),
    )
    await queue.start()
    await queue.enqueue(_queued_event())
    await queue.close()
    await queue.join(timeout=5.0)

    assert flaky.calls == 3  # 2 fallos transitorios + 1 éxito
    snapshot = counters.snapshot()
    assert snapshot["ingest.persisted_total"] == 1
    assert snapshot["ingest.persistence_dead_letter_total"] == 0


async def test_worker_sends_permanent_error_to_dead_letter(caplog):
    """Un error permanente de BD (constraint violation) DEBE ir a dead-letter
    (log + contador) sin excepción silenciosa (RUM-6, escenario Dead-letter)."""
    import sqlalchemy.exc

    from api.infrastructure.ingest.counters import IngestCounters
    from api.infrastructure.ingest.queue import AsyncioIngestQueue

    class _BrokenRepo:
        def __init__(self) -> None:
            self.calls = 0
            self.metric_type_cache = {}

        async def persist_chunk(self, sessions, metrics, exceptions):
            self.calls += 1
            raise sqlalchemy.exc.IntegrityError(
                "INSERT INTO rum_metric", {}, Exception("duplicate key")
            )

    broken = _BrokenRepo()
    counters = IngestCounters()
    queue = AsyncioIngestQueue(
        maxsize=10,
        worker_count=1,
        repository_factory=lambda session: broken,
        counters=counters,
    )
    await queue.start()
    await queue.enqueue(_queued_event())
    await queue.close()
    await queue.join(timeout=5.0)

    # Permanente: sin retry (1 llamada) y dead-letter contado y logueado.
    assert broken.calls == 1
    assert counters.snapshot()["ingest.persistence_dead_letter_total"] == 1
    assert any("dead-lettered" in record.message for record in caplog.records)


def _rum_event_model(**overrides):
    """RumEvent Pydantic válido base; overrides por test."""
    from api.presentation.schemas.ingest import RumEvent

    payload = _rum()
    payload.update(overrides)
    return RumEvent.model_validate(payload)