"""TDD: ingesta RUM asíncrona — RUM-1..RUM-8, IAUTH-2/5, OAS-11/12 (ISS-S2-03).

Strict TDD: cada escenario Given/When/Then de la spec se convierte en un
test red antes de implementar. Capas: unit (política, contadores, cola),
integration (httpx ASGI + Postgres real) y contract (openapi.yaml).
"""

from datetime import datetime, timezone
from uuid import uuid4

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