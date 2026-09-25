"""Per-event ingest policy — pure, no I/O (RUM-4, DD-2).

Applies the ContratoIngestaRUM.md matrices + PipelineIngestaRUM.md §2.3:
7 rejection codes, no `unknown_application` (D2), `application_id` optional
(never a tenant authority, IAUTH-2). Ratings good/poor are reference only
and are NOT rejection criteria — the ranges here are sanity bounds.

Validation order is deterministic so a single event maps to exactly one
reason: required fields → uuids → metric type → unit → value range →
timestamp → size limits.
"""

from datetime import datetime
from uuid import UUID

REJECTION_CODES = frozenset(
    {
        "missing_required_field",
        "invalid_uuid",
        "invalid_metric_type",
        "invalid_unit",
        "invalid_range",
        "invalid_timestamp",
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
_REQUIRED_JS_FIELDS = ("error_type", "message", "session_id", "timestamp")


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
    if not _is_number(value):
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
    metric_ts = metric.get("timestamp")
    if metric_ts is not None and not _is_timestamp(metric_ts):
        return "invalid_timestamp"
    return None


def validate_rum_event(event: dict) -> str | None:
    """Valida un RumEvent; devuelve el código de rechazo o None (aceptado)."""
    for field in _REQUIRED_RUM_FIELDS:
        if field not in event:
            return "missing_required_field"
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
    if not _is_timestamp(event["timestamp"]):
        return "invalid_timestamp"
    return None