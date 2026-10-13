"""Normalizador puro de ingesta RUM — NORM-1..7 (ISS-S3-02).

Etapa de canonicalización de SOLO REPRESENTACIÓN que corre por evento ANTES
de la validación por evento (`ingest_policy`). Nunca decide la aceptación,
nunca lanza y no realiza E/S: la validación sigue siendo la autoridad única
de rechazo (ARCH-5, ADR-0004). Nunca recorta magnitudes — el TTFB de 9000ms
es la señal de anomalía y se preserva (NORM-6, ADR-0005).

Contrato:
- `_canonical_ts`: ISO-8601 UTC tz-aware o `None`; NUNCA inventa un timestamp.
- `timestamp` de métrica ausente → hereda el del envelope (NORM-2).
- alias de unidad → canónica (idempotente, indexada por la unidad declarada).
- nombres de métrica/`error_type` → canónicos (métrica desconocida pasa;
  `error_type` desconocido agrupa en `Other`).
- coerción de cadenas numéricas FINITAS; nunca repara magnitudes.

Recursos (NORM-7): transformaciones puras en memoria, CPU-only, sin
dependencias ni procesos nuevos.
"""

import math
from datetime import datetime, timezone

from api.domain.services.ingest_policy import (
    ERROR_TYPE_ALIASES,
    ERROR_TYPE_CATALOG,
    METRIC_TYPE_ALIASES,
    UNIT_CONVERSIONS,
)

_OTHER_ERROR_TYPE = "Other"
# Lookup determinista (case-fold) del catálogo, evita iterar un frozenset.
_ERROR_TYPE_BY_FOLD = {name.lower(): name for name in ERROR_TYPE_CATALOG}


def _canonical_ts(value: object) -> str | None:
    """ISO-8601 UTC con zona explícita, o None si ausente/naïve/no parseable.

    El normalizador NUNCA inventa un timestamp: un valor no canonicalizable se
    devuelve como None y el llamador debe dejarlo pasar para que la validación
    lo rechace (NORM-2, NORM-5).
    """
    parsed = _as_datetime(value)
    if parsed is None or parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc).isoformat()


def _as_datetime(value: object) -> datetime | None:
    """Parsea value a datetime, sin exigir zona horaria (None si no aplica)."""
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


def _is_finite_number(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def _coerce_finite_number(value: object) -> object:
    """Cadena numérica finita → float; cualquier otra cosa pasa sin cambios.

    `Infinity`/`NaN`/no numéricos NO se coaccionan (la validación los rechaza
    con invalid_range, NORM-6).
    """
    if isinstance(value, str):
        try:
            coerced = float(value.strip())
        except ValueError:
            return value
        if math.isfinite(coerced):
            return coerced
        return value
    return value


def _canonical_metric_type(value: object) -> object:
    """trim/case + mapa de alias; los desconocidos pasan (invalid_metric_type)."""
    if not isinstance(value, str):
        return value
    return METRIC_TYPE_ALIASES.get(value.strip().lower(), value)


def _canonical_error_type(value: object) -> object:
    """trim/case + catálogo/alias; los desconocidos se agrupan en `Other`."""
    if not isinstance(value, str):
        return value
    key = value.strip().lower()
    if key in ERROR_TYPE_ALIASES:
        return ERROR_TYPE_ALIASES[key]
    return _ERROR_TYPE_BY_FOLD.get(key, _OTHER_ERROR_TYPE)


def _convert_unit(metric: dict) -> None:
    """Convierte la unidad declarada a la canónica preservando la magnitud.

    Indexada por la unidad declarada: tras una pasada la unidad es canónica y
    la segunda pasada es un no-op (idempotente, NORM-3). Si el valor no es un
    número finito la conversión se omite y la validación rechaza el evento.
    """
    unit = metric["unit"]
    declared = unit.strip() if isinstance(unit, str) else unit
    conversion = UNIT_CONVERSIONS.get(declared)
    if conversion is None:
        if isinstance(unit, str):
            metric["unit"] = declared
        return
    canonical_unit, factor = conversion
    if not _is_finite_number(metric.get("value")):
        return
    metric["unit"] = canonical_unit
    if factor != 1.0:
        metric["value"] = metric["value"] * factor


def _inherit_timestamp(metric: dict, envelope_ts: str | None) -> None:
    """Canonicaliza el timestamp de la métrica o hereda el del envelope.

    Un timestamp naïve/no parseable se deja intacto para que la validación lo
    rechace; el normalizador no lo reescribe (NORM-2).
    """
    metric_ts = metric.get("timestamp")
    if metric_ts is None:
        if envelope_ts is not None:
            metric["timestamp"] = envelope_ts
        return
    canonical_ts = _canonical_ts(metric_ts)
    if canonical_ts is not None:
        metric["timestamp"] = canonical_ts


def _normalize_metric(metric: object, envelope_ts: str | None) -> object:
    if not isinstance(metric, dict):
        return metric
    normalized = dict(metric)
    if "type" in normalized:
        normalized["type"] = _canonical_metric_type(normalized["type"])
    if "value" in normalized:
        normalized["value"] = _coerce_finite_number(normalized["value"])
    if "unit" in normalized:
        _convert_unit(normalized)
    _inherit_timestamp(normalized, envelope_ts)
    return normalized


def normalize_rum_event(event: dict) -> dict:
    """Devuelve una copia canónica de un RumEvent (puro, sin E/S, sin lanzar)."""
    normalized = dict(event)
    envelope_ts = _canonical_ts(event.get("timestamp"))
    if envelope_ts is not None:
        normalized["timestamp"] = envelope_ts
    metrics = event.get("metrics")
    if isinstance(metrics, list):
        normalized["metrics"] = [
            _normalize_metric(metric, envelope_ts) for metric in metrics
        ]
    return normalized


def normalize_js_exception(event: dict) -> dict:
    """Devuelve una copia canónica de un JsExceptionEvent (puro, sin lanzar)."""
    normalized = dict(event)
    envelope_ts = _canonical_ts(event.get("timestamp"))
    if envelope_ts is not None:
        normalized["timestamp"] = envelope_ts
    if "error_type" in normalized:
        normalized["error_type"] = _canonical_error_type(normalized["error_type"])
    return normalized
