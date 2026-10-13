"""TDD: normalizador puro de ingesta RUM — NORM-1..7 (ISS-S3-02).

Capa unit (sin Postgres): el normalizador es puro, sin E/S y nunca lanza.
Cada escenario Given/When/Then de `specs/ingest-normalization/spec.md` se
convierte en un test RED antes de implementar `ingest_normalizer.py`.

Contrato fijado (design):
- `_canonical_ts` devuelve ISO-8601 UTC tz-aware o `None` (nunca inventa un
  timestamp).
- La conversión de unidad se indexa por la unidad DECLARADA y es idempotente.
- Solo representación: nunca se recortan magnitudes (9000 ms intacto).
"""

from datetime import datetime, timezone

import pytest

from api.domain.services.ingest_normalizer import (
    _canonical_ts,
    normalize_js_exception,
    normalize_rum_event,
)

# Aliases declarados -> (unidad canónica, factor) — espejo de UNIT_CONVERSIONS.
_UNIT_ALIASES = {
    "s": ("ms", 1000.0),
    "sec": ("ms", 1000.0),
    "secs": ("ms", 1000.0),
    "msec": ("ms", 1.0),
    "millis": ("ms", 1.0),
    "ms": ("ms", 1.0),
    "counts": ("count", 1.0),
    "count": ("count", 1.0),
}


def _rum(**overrides) -> dict:
    """Evento RUM base (dict, sin Pydantic) para el normalizador puro."""
    event = {
        "schema_version": "1.0",
        "timestamp": "2026-10-13T12:00:00+00:00",
        "session_id": "9f8c5a2e-1b2c-4d5e-8f9a-0b1c2d3e4f5a",
        "metrics": [
            {"type": "TTFB", "value": 120, "unit": "ms"},
        ],
    }
    event.update(overrides)
    return event


def _metric(**overrides) -> dict:
    metric = {"type": "TTFB", "value": 120, "unit": "ms"}
    metric.update(overrides)
    return metric


def _js(**overrides) -> dict:
    event = {
        "schema_version": "1.0",
        "error_type": "TypeError",
        "message": "boom",
        "session_id": "9f8c5a2e-1b2c-4d5e-8f9a-0b1c2d3e4f5a",
        "timestamp": "2026-10-13T12:00:00+00:00",
    }
    event.update(overrides)
    return event


# -- NORM-2: contrato `_canonical_ts` -----------------------------------------

def test_canonical_ts_returns_utc_iso_for_offset():
    """Un timestamp con offset DEBE canonicalizarse a UTC tz-aware (NORM-2)."""
    assert _canonical_ts("2026-10-13T12:00:00-03:00") == "2026-10-13T15:00:00+00:00"


def test_canonical_ts_returns_utc_iso_for_zulu():
    """`Z` DEBE parsearse como UTC y devolver offset explícito (NORM-2)."""
    assert _canonical_ts("2026-10-13T12:00:00Z") == "2026-10-13T12:00:00+00:00"


def test_canonical_ts_accepts_datetime_with_tz():
    """Un datetime con tz DEBE serializarse como ISO UTC (NORM-2)."""
    value = datetime(2026, 10, 13, 12, 0, tzinfo=timezone.utc)
    assert _canonical_ts(value) == "2026-10-13T12:00:00+00:00"


@pytest.mark.parametrize("value", [None, "", "ayer a la tarde", 42, "2026-10-13T12:00:00"])
def test_canonical_ts_returns_none_for_missing_naive_or_garbage(value):
    """Ausente, naïve o no parseable DEBE devolver None — el normalizador NUNCA
    inventa un timestamp (NORM-2)."""
    assert _canonical_ts(value) is None


def test_normalize_rum_event_never_invents_missing_timestamp():
    """Un timestamp naïve DEBE quedar intacto (no reemplazado por now()); la
    validación lo rechazará (NORM-2)."""
    event = _rum(timestamp="2026-10-13T12:00:00")
    normalized = normalize_rum_event(event)
    assert normalized["timestamp"] == "2026-10-13T12:00:00"


def test_normalize_metric_inherits_envelope_timestamp():
    """Un timestamp de métrica ausente DEBE heredar el del envelope (NORM-2)."""
    event = _rum(timestamp="2026-10-13T12:00:00-03:00", metrics=[_metric()])
    normalized = normalize_rum_event(event)
    assert normalized["metrics"][0]["timestamp"] == "2026-10-13T15:00:00+00:00"


def test_normalize_metric_explicit_timestamp_is_canonicalized():
    """Un timestamp de métrica explícito DEBE canonicalizarse a UTC (NORM-2)."""
    event = _rum(
        metrics=[_metric(timestamp="2026-10-13T09:00:00-03:00")],
    )
    normalized = normalize_rum_event(event)
    assert normalized["metrics"][0]["timestamp"] == "2026-10-13T12:00:00+00:00"


# -- NORM-3: conversión de alias de unidad (idempotente) ----------------------

@pytest.mark.parametrize(
    ("declared", "expected_unit", "expected_value"),
    [
        ("s", "ms", 2000.0),
        ("sec", "ms", 2000.0),
        ("secs", "ms", 2000.0),
        ("msec", "ms", 2.0),
        ("millis", "ms", 2.0),
        ("ms", "ms", 2.0),
    ],
)
def test_normalize_converts_duration_aliases_to_ms(declared, expected_unit, expected_value):
    """Los alias de duración DEBEN convertirse a `ms` preservando la magnitud
    (NORM-3)."""
    event = _rum(metrics=[_metric(value=2, unit=declared)])
    metric = normalize_rum_event(event)["metrics"][0]
    assert metric["unit"] == expected_unit
    assert metric["value"] == expected_value


@pytest.mark.parametrize(("declared", "expected"), [("counts", "count"), ("count", "count")])
def test_normalize_converts_count_aliases(declared, expected):
    """`counts` DEBE resolver a `count`; `count` es identidad (NORM-3)."""
    event = _rum(metrics=[_metric(type="JS_EXCEPTION_RATE", value=3, unit=declared)])
    metric = normalize_rum_event(event)["metrics"][0]
    assert metric["unit"] == expected
    assert metric["value"] == 3


@pytest.mark.parametrize("declared", list(_UNIT_ALIASES))
def test_normalize_unit_conversion_is_idempotent(declared):
    """`normalize(normalize(e)) == normalize(e)` para cada alias y ×1000 se
    aplica UNA sola vez (NORM-3, R4)."""
    event = _rum(metrics=[_metric(value=2, unit=declared)])
    once = normalize_rum_event(event)
    twice = normalize_rum_event(once)
    assert twice == once


def test_normalize_never_applies_factor_twice():
    """`2 s` DEBE convertirse a 2000 ms, no a 2_000_000 (doble aplicación)."""
    event = _rum(metrics=[_metric(value=2, unit="s")])
    once = normalize_rum_event(event)
    assert once["metrics"][0]["value"] == 2000.0
    twice = normalize_rum_event(once)
    assert twice["metrics"][0]["value"] == 2000.0


def test_normalize_passes_unknown_unit_through_for_validation():
    """Una unidad desconocida DEBE pasar sin cambios (la validación la rechaza
    con invalid_unit) (NORM-3)."""
    event = _rum(metrics=[_metric(value=1, unit="furlongs")])
    assert normalize_rum_event(event)["metrics"][0]["unit"] == "furlongs"


# -- NORM-4: nombres de métrica y `error_type` --------------------------------

@pytest.mark.parametrize(
    ("declared", "expected"),
    [
        ("ttfb", "TTFB"),
        (" TTFB ", "TTFB"),
        ("XHR_LATENCY", "XHR_LATENCY"),
        ("xhr_latency", "XHR_LATENCY"),
        ("fcp", "FCP"),
        ("js_exception_rate", "JS_EXCEPTION_RATE"),
        ("rage_click", "RAGE_CLICK"),
    ],
)
def test_normalize_casefolds_metric_type(declared, expected):
    """El nombre de tipo de métrica DEBE canonicalizarse por trim/case (NORM-4)."""
    event = _rum(metrics=[_metric(type=declared)])
    assert normalize_rum_event(event)["metrics"][0]["type"] == expected


def test_normalize_passes_unknown_metric_type_through():
    """Un tipo de métrica desconocido DEBE pasar sin cambios para que la
    validación lo rechace (invalid_metric_type) (NORM-4)."""
    event = _rum(metrics=[_metric(type="LCP")])
    assert normalize_rum_event(event)["metrics"][0]["type"] == "LCP"


@pytest.mark.parametrize(
    ("declared", "expected"),
    [
        ("TypeError", "TypeError"),
        ("typeerror", "TypeError"),
        ("  referenceerror ", "ReferenceError"),
        ("RangeError", "RangeError"),
        ("UnhandledRejection", "UnhandledRejection"),
        ("unhandled_rejection", "UnhandledRejection"),
        ("WeirdError", "Other"),
        ("totally-unknown", "Other"),
    ],
)
def test_normalize_canonicalizes_error_type(declared, expected):
    """`error_type` DEBE canonicalizarse por trim/case y los desconocidos
    agruparse en `Other`, sin cambio de esquema (NORM-4)."""
    assert normalize_js_exception(_js(error_type=declared))["error_type"] == expected


# -- NORM-5: valores ausentes (sin defaults inventados) -----------------------

def test_normalize_does_not_fabricate_missing_required_field():
    """Un campo requerido ausente NO DEBE ser inventado por el normalizador
    (la validación lo rechaza) (NORM-5)."""
    event = _rum()
    del event["session_id"]
    assert "session_id" not in normalize_rum_event(event)


def test_normalize_does_not_fabricate_missing_optional_field():
    """Un opcional ausente NO DEBE recibir un valor fabricado (NORM-5)."""
    assert "stack_trace" not in normalize_js_exception(_js())


# -- NORM-6: solo representación (coerción, nunca recorte) --------------------

def test_normalize_coerces_finite_numeric_string():
    """Una cadena numérica finita DEBE coaccionarse a número (NORM-6)."""
    event = _rum(metrics=[_metric(value="120.5")])
    assert normalize_rum_event(event)["metrics"][0]["value"] == 120.5


@pytest.mark.parametrize("raw", ["Infinity", "-Infinity", "NaN", "abc"])
def test_normalize_does_not_coerce_non_finite_or_garbage(raw):
    """`Infinity`/`NaN`/no numéricos NO DEBEN convertirse (la validación los
    rechaza con invalid_range) (NORM-6)."""
    event = _rum(metrics=[_metric(value=raw)])
    assert normalize_rum_event(event)["metrics"][0]["value"] == raw


def test_normalize_preserves_magnitude_without_clamping():
    """Un TTFB de 9000 ms (dentro del rango de cordura) DEBE preservarse sin
    cambios — nunca se recorta a las cotas de sanity (NORM-6, D4)."""
    event = _rum(metrics=[_metric(value=9000, unit="ms")])
    assert normalize_rum_event(event)["metrics"][0]["value"] == 9000


def test_normalize_keeps_fractional_count_intact():
    """Un conteo fraccionario NO DEBE redondearse; la validación lo rechaza
    (invalid_range) (NORM-6, decisión f)."""
    event = _rum(metrics=[_metric(type="JS_EXCEPTION_RATE", value=1.5, unit="count")])
    assert normalize_rum_event(event)["metrics"][0]["value"] == 1.5


def test_normalize_does_not_mutate_input():
    """El normalizador DEBE devolver un dict NUEVO y no mutar la entrada
    (NORM-7: puro, sin efectos)."""
    event = _rum(metrics=[_metric(value=2, unit="s")])
    normalized = normalize_rum_event(event)
    assert normalized is not event
    assert event["metrics"][0]["unit"] == "s"  # la entrada queda intacta
    assert event["metrics"][0]["value"] == 2


def test_normalize_is_deterministic():
    """Dos pasadas sobre la misma entrada DEBEN dar el mismo resultado
    (NORM-7: puro, CPU-only, sin estado)."""
    event = _rum(metrics=[_metric(value=2, unit="sec")])
    assert normalize_rum_event(event) == normalize_rum_event(event)
