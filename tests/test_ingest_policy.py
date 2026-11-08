"""Unit: casos límite de la política de validación de ingesta (ISS-S3-06, #45).

`ingest_policy` es la autoridad única de rechazo por evento (ADR-0004). Los
caminos felices y los códigos principales ya se prueban en
`test_ingest_telemetry.py`; este módulo fija los casos límite de tipo que
quedaban sin cubrir: identificadores y timestamps que llegan como objetos
nativos o como tipos inesperados, métricas malformadas dentro del array y
`metric_id` inválido en excepciones.

Capa unit: funciones puras, sin Postgres ni FastAPI.
"""

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from api.domain.services.ingest_policy import (
    validate_js_exception,
    validate_rum_event,
)


def _rum(**overrides) -> dict:
    """RumEvent canónico válido; overrides por test."""
    event = {
        "schema_version": "1.0",
        "timestamp": "2026-11-08T12:00:00+00:00",
        "session_id": str(uuid4()),
        "metrics": [{"type": "TTFB", "value": 120.0, "unit": "ms"}],
    }
    event.update(overrides)
    return event


def _js(**overrides) -> dict:
    """JsExceptionEvent canónico válido; overrides por test."""
    event = {
        "schema_version": "1.0",
        "error_type": "TypeError",
        "message": "boom",
        "session_id": str(uuid4()),
        "timestamp": "2026-11-08T12:00:00+00:00",
    }
    event.update(overrides)
    return event


def test_base_events_are_valid():
    """Los eventos base de este módulo DEBEN ser válidos (precondición)."""
    assert validate_rum_event(_rum()) is None
    assert validate_js_exception(_js()) is None


# -- Identificadores ----------------------------------------------------------

def test_native_uuid_session_id_is_accepted():
    """Un `session_id` que ya es `uuid.UUID` (no string) DEBE aceptarse."""
    assert validate_rum_event(_rum(session_id=uuid4())) is None
    assert validate_js_exception(_js(session_id=uuid4())) is None


@pytest.mark.parametrize("bad_id", [123, 4.5, None, ["a"], {"id": "x"}, b"bytes"])
def test_non_string_session_id_is_invalid_uuid(bad_id):
    """Un `session_id` de tipo inesperado DEBE rechazarse con invalid_uuid,
    nunca lanzar."""
    assert validate_rum_event(_rum(session_id=bad_id)) == "invalid_uuid"
    assert validate_js_exception(_js(session_id=bad_id)) == "invalid_uuid"


def test_invalid_application_id_is_rejected_in_both_event_kinds():
    """`application_id` es opcional, pero si viene DEBE ser un UUID."""
    assert validate_rum_event(_rum(application_id="not-a-uuid")) == "invalid_uuid"
    assert validate_js_exception(_js(application_id="not-a-uuid")) == "invalid_uuid"


def test_invalid_metric_id_in_exception_is_invalid_uuid():
    """Un `metric_id` presente e inválido en una excepción DEBE rechazarse
    con invalid_uuid; ausente o válido se acepta."""
    assert validate_js_exception(_js(metric_id="nope")) == "invalid_uuid"
    assert validate_js_exception(_js(metric_id=str(uuid4()))) is None
    assert validate_js_exception(_js(metric_id=None)) is None


# -- Timestamps ---------------------------------------------------------------

def test_aware_datetime_timestamp_is_accepted():
    """Un `timestamp` que ya es `datetime` con zona DEBE aceptarse."""
    aware = datetime(2026, 11, 8, 12, 0, tzinfo=timezone.utc)
    assert validate_rum_event(_rum(timestamp=aware)) is None
    assert validate_js_exception(_js(timestamp=aware)) is None


def test_naive_datetime_timestamp_is_invalid():
    """Un `datetime` sin zona DEBE rechazarse con invalid_timestamp: el
    contrato exige zona explícita también para objetos nativos."""
    naive = datetime(2026, 11, 8, 12, 0)
    assert validate_rum_event(_rum(timestamp=naive)) == "invalid_timestamp"
    assert validate_js_exception(_js(timestamp=naive)) == "invalid_timestamp"


@pytest.mark.parametrize("bad_ts", [1731067200, 1731067200.5, None, ["2026"], {}])
def test_non_string_timestamp_is_invalid(bad_ts):
    """Un `timestamp` de tipo inesperado (epoch numérico incluido) DEBE
    rechazarse con invalid_timestamp."""
    assert validate_rum_event(_rum(timestamp=bad_ts)) == "invalid_timestamp"
    assert validate_js_exception(_js(timestamp=bad_ts)) == "invalid_timestamp"


@pytest.mark.parametrize("bad_ts", ["garbage", "2026-11-08T12:00:00"])
def test_invalid_metric_level_timestamp_is_rejected(bad_ts):
    """El `timestamp` propio de una métrica DEBE validarse igual que el del
    envelope: no parseable o sin zona → invalid_timestamp."""
    metric = {"type": "TTFB", "value": 120.0, "unit": "ms", "timestamp": bad_ts}
    assert validate_rum_event(_rum(metrics=[metric])) == "invalid_timestamp"


# -- Métricas malformadas -----------------------------------------------------

@pytest.mark.parametrize("bad_metric", ["TTFB", 120, None, ["TTFB", 120, "ms"]])
def test_non_dict_metric_is_missing_required_field(bad_metric):
    """Un elemento de `metrics` que no es un objeto DEBE rechazarse con
    missing_required_field, nunca lanzar."""
    assert validate_rum_event(_rum(metrics=[bad_metric])) == "missing_required_field"


@pytest.mark.parametrize("missing", ["type", "value", "unit"])
def test_metric_missing_field_is_missing_required_field(missing):
    """A una métrica le falta `type`, `value` o `unit` → missing_required_field."""
    metric = {"type": "TTFB", "value": 120.0, "unit": "ms"}
    del metric[missing]
    assert validate_rum_event(_rum(metrics=[metric])) == "missing_required_field"


def test_one_bad_metric_rejects_the_whole_event():
    """La validación es por evento: una métrica inválida entre válidas
    rechaza el evento completo con el código de la primera inválida."""
    good = {"type": "TTFB", "value": 120.0, "unit": "ms"}
    bad = {"type": "FCP", "value": -1.0, "unit": "ms"}
    assert validate_rum_event(_rum(metrics=[good, bad])) == "invalid_range"


@pytest.mark.parametrize("metrics", [[], "TTFB", None, {"type": "TTFB"}])
def test_empty_or_non_list_metrics_is_missing_required_field(metrics):
    """`metrics` vacío o que no es lista → missing_required_field."""
    assert validate_rum_event(_rum(metrics=metrics)) == "missing_required_field"


def test_boolean_value_is_not_a_number():
    """`True`/`False` son `int` en Python pero NO DEBEN aceptarse como valor
    de métrica: se rechazan con invalid_range."""
    metric = {"type": "RAGE_CLICK", "value": True, "unit": "count"}
    assert validate_rum_event(_rum(metrics=[metric])) == "invalid_range"


def test_count_metric_upper_bound_is_open():
    """Los conteos sin máximo (RAGE_CLICK) aceptan valores enteros grandes."""
    metric = {"type": "RAGE_CLICK", "value": 1_000_000, "unit": "count"}
    assert validate_rum_event(_rum(metrics=[metric])) is None


# -- Excepciones: tipos de campos de texto ------------------------------------

@pytest.mark.parametrize("field", ["error_type", "message"])
def test_non_string_text_fields_are_oversized_event(field):
    """`error_type` o `message` que no son string DEBEN rechazarse con
    oversized_event (mismo código que el exceso de longitud)."""
    assert validate_js_exception(_js(**{field: 42})) == "oversized_event"


def test_non_string_stack_trace_is_oversized_event():
    """Un `stack_trace` presente que no es string → oversized_event; ausente
    se acepta."""
    assert validate_js_exception(_js(stack_trace=["at line 1"])) == "oversized_event"
    assert validate_js_exception(_js(stack_trace=None)) is None
