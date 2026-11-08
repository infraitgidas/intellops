"""Per-event ingest policy — pure, no I/O (RUM-4, DD-2).

Applies the ContratoIngestaRUM.md matrices + PipelineIngestaRUM.md §2.3:
8 rejection codes, no `unknown_application` (D2), `application_id` optional
(never a tenant authority, IAUTH-2). Ratings good/poor are reference only
and are NOT rejection criteria — the ranges here are sanity bounds.

Validation order is deterministic so a single event maps to exactly one
reason: required fields → schema_version → uuids → metric type → unit →
value range → timestamp → size limits. El validador de excepciones aplica
los límites de tamaño antes de los UUID y valida `sample_rate` (0..1, finito)
antes del timestamp.
"""

from datetime import datetime
from math import isfinite
from uuid import UUID

# pylint: disable=too-many-return-statements  # cadena determinista de validación

REJECTION_CODES = frozenset(
    {
        "missing_required_field",
        "invalid_uuid",
        "invalid_metric_type",
        "invalid_unit",
        "invalid_range",
        "invalid_timestamp",
        "invalid_schema_version",
        "oversized_event",
    }
)

METRIC_TYPES = frozenset(
    {"TTFB", "FCP", "XHR_LATENCY", "JS_EXCEPTION_RATE", "RAGE_CLICK"}
)
VALID_UNITS = frozenset({"ms", "count"})
UNIT_BY_TYPE = {
    "TTFB": "ms",
    "FCP": "ms",
    "XHR_LATENCY": "ms",
    "JS_EXCEPTION_RATE": "count",
    "RAGE_CLICK": "count",
}

# -- Registros compartidos con el normalizador (ISS-S3-02, R7) ----------------
# Fuente única de verdad: `ingest_normalizer.py` los importa para evitar
# derivas entre la conversión (normalización) y las reglas de validación.

# Unidad DECLARADA -> (unidad canónica, factor). La conversión es escalar y
# preserva la magnitud; indexada por la unidad de entrada (idempotente).
UNIT_CONVERSIONS: dict[str, tuple[str, float]] = {
    "ms": ("ms", 1.0),
    "msec": ("ms", 1.0),
    "millis": ("ms", 1.0),
    "s": ("ms", 1000.0),
    "sec": ("ms", 1000.0),
    "secs": ("ms", 1000.0),
    "count": ("count", 1.0),
    "counts": ("count", 1.0),
}

# Alias de nombre de métrica (case-fold) -> canónico UPPER_SNAKE.
METRIC_TYPE_ALIASES: dict[str, str] = {
    "ttfb": "TTFB",
    "time_to_first_byte": "TTFB",
    "fcp": "FCP",
    "first_contentful_paint": "FCP",
    "xhr_latency": "XHR_LATENCY",
    "xhrlatency": "XHR_LATENCY",
    "js_exception_rate": "JS_EXCEPTION_RATE",
    "jsexceptionrate": "JS_EXCEPTION_RATE",
    "rage_click": "RAGE_CLICK",
    "rageclick": "RAGE_CLICK",
}

# Catálogo de `error_type` canónico: built-ins de ECMAScript + ejemplos del
# contrato + bucket de fallback `Other`. Sin DDL/migración (ADR-0006).
ERROR_TYPE_CATALOG = frozenset(
    {
        "Error",
        "EvalError",
        "RangeError",
        "ReferenceError",
        "SyntaxError",
        "TypeError",
        "URIError",
        "AggregateError",
        "InternalError",
        "UnhandledRejection",
        "Other",
    }
)
# Alias explícitos (case-fold) -> canónico, para sinónimos fuera del catálogo.
ERROR_TYPE_ALIASES: dict[str, str] = {
    "unhandled_rejection": "UnhandledRejection",
    "unhandledrejectionerror": "UnhandledRejection",
    "promise_rejection": "UnhandledRejection",
    "unhandled promise rejection": "UnhandledRejection",
}

# Tipos de métrica cuyos valores DEBEN ser enteros (sin redondeo; NORM-6/f).
COUNT_TYPES = frozenset({"JS_EXCEPTION_RATE", "RAGE_CLICK"})
# (min, max|None) sanity bounds per metric type.
RANGE_BY_TYPE = {
    "TTFB": (0, 60_000),
    "FCP": (0, 120_000),
    "XHR_LATENCY": (0, 60_000),
    "JS_EXCEPTION_RATE": (0, None),
    "RAGE_CLICK": (0, None),
}

MAX_BATCH_EVENTS = 500
MAX_METRICS_PER_EVENT = 50
MAX_ERROR_TYPE_LEN = 100
MAX_MESSAGE_LEN = 2000
MAX_STACK_TRACE_LEN = 20_000

_REQUIRED_RUM_FIELDS = ("schema_version", "timestamp", "session_id", "metrics")
_REQUIRED_JS_FIELDS = ("schema_version", "error_type", "message", "session_id", "timestamp")

# v0.1 acepta exclusivamente esta versión por evento (OD-04/D-02). Comparación
# exacta sobre str: no se aceptan números ni valores equivalentes.
SUPPORTED_SCHEMA_VERSION = "1.0"

# Rango declarado en OpenAPI para `sample_rate` (OD-03): el valor se persiste,
# así que fuera de rango o no finito se rechaza como cualquier otra magnitud.
SAMPLE_RATE_RANGE = (0.0, 1.0)


def _is_uuid(value: object) -> bool:
    """True si value parsea como UUID (str o UUID nativo)."""
    if isinstance(value, UUID):
        return True
    if isinstance(value, str):
        try:
            UUID(value)
            return True
        except (ValueError, AttributeError, TypeError):
            return False
    return False


def _is_timestamp(value: object) -> bool:
    """True si value es datetime con tz explícito o ISO 8601 UTC con zona.

    El contrato exige zona horaria explícita; un datetime naive (sin tz)
    se considera invalid_timestamp.
    """
    if isinstance(value, datetime):
        return value.tzinfo is not None
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return False
        return parsed.tzinfo is not None
    return False


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _in_range(type_: str, value: object) -> bool:
    if not _is_number(value) or not isfinite(value):
        # NaN/Infinity no son comparables: sin el guard, NaN pasaría todas las
        # comparaciones (NORM-6) y Infinity pasaría las cotas sin máximo.
        return False
    low, high = RANGE_BY_TYPE[type_]
    if value < low:
        return False
    if high is not None and value > high:
        return False
    return True


def _validate_optional_uuid(value: object) -> str | None:
    """Valida un UUID opcional presente: None si ausente o válido."""
    if value is None:
        return None
    if not _is_uuid(value):
        return "invalid_uuid"
    return None


def _schema_version_is_supported(value: object) -> bool:
    """True solo si value es el string exacto "1.0" (OD-04/D-02)."""
    return isinstance(value, str) and value == SUPPORTED_SCHEMA_VERSION


def _sample_rate_is_valid(value: object) -> bool:
    """True si value es un número finito dentro del rango de OpenAPI (OD-03).

    `sample_rate` se persiste en `js_exception`, así que se valida antes de
    encolar: NaN/Infinity no son ponderables y `1 / sample_rate` se usa en el
    análisis (§5 del contrato del agente).
    """
    if not _is_number(value) or not isfinite(value):
        return False
    low, high = SAMPLE_RATE_RANGE
    return low <= value <= high


def _validate_metric(metric: object) -> str | None:
    """Valida una métrica RUM individual (RUM-4, matriz ContratoIngestaRUM)."""
    if not isinstance(metric, dict):
        return "missing_required_field"
    for field in ("type", "value", "unit"):
        if field not in metric:
            return "missing_required_field"
    type_ = metric["type"]
    if type_ not in METRIC_TYPES:
        return "invalid_metric_type"
    unit = metric["unit"]
    if unit not in VALID_UNITS or UNIT_BY_TYPE[type_] != unit:
        return "invalid_unit"
    if not _in_range(type_, metric["value"]):
        return "invalid_range"
    if type_ in COUNT_TYPES and not float(metric["value"]).is_integer():
        # Conteos no enteros: sin redondeo (redondear cambia la magnitud,
        # NORM-6/decisión f).
        return "invalid_range"
    metric_ts = metric.get("timestamp")
    if metric_ts is not None and not _is_timestamp(metric_ts):
        return "invalid_timestamp"
    return None


def validate_rum_event(event: dict) -> str | None:
    """Valida un RumEvent; devuelve el código de rechazo o None (aceptado)."""
    for field in _REQUIRED_RUM_FIELDS:
        if field not in event:
            return "missing_required_field"
    if not _schema_version_is_supported(event["schema_version"]):
        return "invalid_schema_version"
    session_id = event["session_id"]
    if not _is_uuid(session_id):
        return "invalid_uuid"
    app_reason = _validate_optional_uuid(event.get("application_id"))
    if app_reason is not None:
        return app_reason
    if not _is_timestamp(event["timestamp"]):
        return "invalid_timestamp"
    metrics = event["metrics"]
    if not isinstance(metrics, list) or not metrics:
        return "missing_required_field"
    if len(metrics) > MAX_METRICS_PER_EVENT:
        return "oversized_event"
    for metric in metrics:
        reason = _validate_metric(metric)
        if reason is not None:
            return reason
    return None


def validate_js_exception(event: dict) -> str | None:
    """Valida un JsExceptionEvent; devuelve el código de rechazo o None."""
    for field in _REQUIRED_JS_FIELDS:
        if field not in event:
            return "missing_required_field"
    if not _schema_version_is_supported(event["schema_version"]):
        return "invalid_schema_version"
    error_type = event["error_type"]
    if not isinstance(error_type, str) or len(error_type) > MAX_ERROR_TYPE_LEN:
        return "oversized_event"
    message = event["message"]
    if not isinstance(message, str) or len(message) > MAX_MESSAGE_LEN:
        return "oversized_event"
    stack_trace = event.get("stack_trace")
    if stack_trace is not None and (
        not isinstance(stack_trace, str) or len(stack_trace) > MAX_STACK_TRACE_LEN
    ):
        return "oversized_event"
    if not _is_uuid(event["session_id"]):
        return "invalid_uuid"
    app_reason = _validate_optional_uuid(event.get("application_id"))
    if app_reason is not None:
        return app_reason
    metric_reason = _validate_optional_uuid(event.get("metric_id"))
    if metric_reason is not None:
        return metric_reason
    sample_rate = event.get("sample_rate")
    if sample_rate is not None and not _sample_rate_is_valid(sample_rate):
        return "invalid_range"
    if not _is_timestamp(event["timestamp"]):
        return "invalid_timestamp"
    return None
