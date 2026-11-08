"""TDD: límites compartidos de los listados del read path (ISS-B-03, #68).

Capa unit: `read_window` acota la ventana y el `limit` de `GET /anomalies` y
`GET /alerts` antes de tocar el repositorio, con 422 `invalid_query_range`.
"""

from datetime import datetime, timedelta, timezone

import pytest

from api.domain.exceptions import QueryRangeError
from api.domain.services.read_window import (
    DEFAULT_READ_LIMIT,
    as_utc,
    bounded_limit,
    bounded_window,
)


def test_bounded_window_defaults_to_last_24_hours_in_utc():
    """Sin start ni end, la ventana DEBE ser las últimas 24 h, UTC aware."""
    before = datetime.now(timezone.utc)
    start, end = bounded_window(None, None)

    assert end - start == timedelta(hours=24)
    assert end.tzinfo is not None
    assert end >= before


def test_bounded_window_default_start_is_relative_to_given_end():
    """Con solo end, start DEBE ser end - 24 h."""
    end = datetime(2026, 11, 1, 12, 0, tzinfo=timezone.utc)
    start, effective_end = bounded_window(None, end)

    assert effective_end == end
    assert start == end - timedelta(hours=24)


def test_bounded_window_assumes_naive_datetimes_are_utc():
    """Un datetime naive DEBE asumirse UTC; uno con otra zona se convierte."""
    naive = datetime(2026, 11, 1, 12, 0)
    start, end = bounded_window(naive - timedelta(hours=1), naive)
    assert end == naive.replace(tzinfo=timezone.utc)
    assert start.tzinfo is not None

    minus_three = timezone(timedelta(hours=-3))
    assert as_utc(datetime(2026, 11, 1, 9, 0, tzinfo=minus_three)) == datetime(
        2026, 11, 1, 12, 0, tzinfo=timezone.utc
    )


@pytest.mark.parametrize(
    ("start_offset", "message"),
    [
        (timedelta(0), "start must be before end"),
        (timedelta(hours=-1), "start must be before end"),
        (timedelta(days=7, seconds=1), "window exceeds 7 days"),
    ],
)
def test_bounded_window_rejects_invalid_ranges(start_offset, message):
    """start >= end y ventana > 7 días DEBEN dar 422 invalid_query_range."""
    end = datetime(2026, 11, 1, 12, 0, tzinfo=timezone.utc)
    with pytest.raises(QueryRangeError) as excinfo:
        bounded_window(end - start_offset, end)
    assert excinfo.value.http_code == 422
    assert excinfo.value.code == "invalid_query_range"
    assert excinfo.value.message == message


def test_bounded_window_accepts_exactly_seven_days():
    """Una ventana de exactamente 7 días es el máximo permitido."""
    end = datetime(2026, 11, 8, tzinfo=timezone.utc)
    assert bounded_window(end - timedelta(days=7), end) == (
        end - timedelta(days=7),
        end,
    )


@pytest.mark.parametrize("limit", [1, 50, 500])
def test_bounded_limit_accepts_range_edges(limit):
    """1 y 500 son los bordes válidos del limit."""
    assert bounded_limit(limit) == limit


def test_bounded_limit_defaults_to_50():
    """Sin limit, el efectivo DEBE ser 50."""
    assert bounded_limit(None) == DEFAULT_READ_LIMIT == 50


@pytest.mark.parametrize("limit", [0, -1, 501])
def test_bounded_limit_rejects_out_of_range_naming_the_value(limit):
    """limit fuera de 1..500 DEBE dar 422 y nombrar el valor rechazado
    (sin clamp silencioso)."""
    with pytest.raises(QueryRangeError) as excinfo:
        bounded_limit(limit)
    assert excinfo.value.code == "invalid_query_range"
    assert f"got {limit}" in excinfo.value.message
