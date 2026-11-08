"""Límites compartidos de los listados del read path (ISS-B-03, #68).

Los listados de eventos (`GET /anomalies`, `GET /alerts`) se acotan con la
misma disciplina que `QueryService` (TQ-2), ANTES de tocar el repositorio:
`start < end`, ventana máxima de 7 días y `limit` 1..500 sin clamp
silencioso. Cualquier violación → `QueryRangeError` (422
`invalid_query_range`, ADR-09) sin ejecutar la consulta.

La ventana default es de 24 h: los eventos son escasos comparados con las
métricas, y 15 min (el default de `/metrics/query`) dejaría casi siempre la
respuesta vacía.
"""

from datetime import datetime, timedelta, timezone

from api.domain.exceptions import QueryRangeError
from api.domain.services.query_service import MAX_WINDOW_DAYS

DEFAULT_READ_WINDOW_HOURS = 24

MIN_READ_LIMIT = 1
MAX_READ_LIMIT = 500
DEFAULT_READ_LIMIT = 50


def as_utc(value: datetime) -> datetime:
    """Normaliza a UTC aware (los naive se asumen UTC)."""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def bounded_window(
    start: datetime | None, end: datetime | None
) -> tuple[datetime, datetime]:
    """Ventana `[start, end)` en UTC con defaults; fuera de límite → 422."""
    end = as_utc(end or datetime.now(timezone.utc))
    start = as_utc(start or (end - timedelta(hours=DEFAULT_READ_WINDOW_HOURS)))
    if start >= end:
        raise QueryRangeError("start must be before end")
    if end - start > timedelta(days=MAX_WINDOW_DAYS):
        raise QueryRangeError(f"window exceeds {MAX_WINDOW_DAYS} days")
    return start, end


def bounded_limit(limit: int | None) -> int:
    """`limit` efectivo (default 50); fuera de 1..500 → 422 con el valor."""
    effective = DEFAULT_READ_LIMIT if limit is None else limit
    if not MIN_READ_LIMIT <= effective <= MAX_READ_LIMIT:
        raise QueryRangeError(
            f"limit must be between {MIN_READ_LIMIT} and {MAX_READ_LIMIT}, "
            f"got {effective}"
        )
    return effective
