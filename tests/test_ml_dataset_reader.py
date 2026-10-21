"""Tests unitarios del reader HTTP del dataset operativo para ML (ISS-S3-04).

Sin Postgres ni red: el read path se simula con `httpx.MockTransport`.
"""
import ast
import logging
import pathlib
from datetime import datetime, timedelta, timezone

import httpx
import pytest
from pydantic import ValidationError

from src.ml.config import MLDatasetSettings
from src.ml.pipeline.api_reader import align_window, read_dataset
from src.ml.pipeline.mapper import DatasetReadError, to_batch

pytestmark = pytest.mark.unit

UTC = timezone.utc
APP = "f47ac10b-58cc-4372-a567-0e02b2c3d479"
OTHER_APP = "a1b2c3d4-58cc-4372-a567-0e02b2c3d480"
API_KEY = "ik_super_secret_key_123"
START = datetime(2026, 8, 28, 21, 0, tzinfo=UTC)
END = datetime(2026, 8, 28, 22, 0, tzinfo=UTC)
NOW = datetime(2026, 8, 28, 22, 0, 37, tzinfo=UTC)


def _row(**changes):
    row = {
        "application_id": APP,
        "metric_type_id": 1,
        "timestamp": "2026-08-28T21:15:00Z",
        "value": 120.5,
        "session_count": 4,
    }
    row.update(changes)
    return row


def _settings(monkeypatch, **env):
    base = {
        "INTELLOPS_API_BASE_URL": "http://core:8000",
        "INTELLOPS_ML_API_KEY": API_KEY,
    }
    base.update(env)
    for name in (
        "INTELLOPS_API_BASE_URL",
        "INTELLOPS_ML_API_KEY",
        "INTELLOPS_ML_BUCKET_SECONDS",
        "INTELLOPS_ML_WINDOW_MINUTES",
        "INTELLOPS_ML_HTTP_TIMEOUT_SECONDS",
        "INTELLOPS_ML_HTTP_RETRIES",
    ):
        monkeypatch.delenv(name, raising=False)
    for name, value in base.items():
        if value is not None:
            monkeypatch.setenv(name, value)
    return MLDatasetSettings(_env_file=None)


# -- align_window (MLD-4, MLD-6) ---------------------------------------------

@pytest.mark.parametrize("bucket", [60, 300, 900, 3600])
@pytest.mark.parametrize("offset", [0, 1, 37, 59, 61, 299, 1234, 86399])
def test_align_window_properties(bucket, offset):
    now = datetime(2026, 8, 28, 0, 0, tzinfo=UTC) + timedelta(seconds=offset)
    start, end = align_window(now - timedelta(hours=2), now, bucket)
    assert int(start.timestamp()) % bucket == 0
    assert int(end.timestamp()) % bucket == 0
    assert end <= now
    assert start < end


def test_align_window_start_not_aligned():
    start = datetime(2026, 8, 28, 10, 0, 37, tzinfo=UTC)
    end = datetime(2026, 8, 28, 11, 0, 59, tzinfo=UTC)
    s, e = align_window(start, end, 60)
    assert s == datetime(2026, 8, 28, 10, 0, 0, tzinfo=UTC)
    assert e == datetime(2026, 8, 28, 11, 0, 0, tzinfo=UTC)


def test_align_window_300_seconds():
    start = datetime(2026, 8, 28, 10, 7, 12, tzinfo=UTC)
    end = datetime(2026, 8, 28, 11, 0, 0, tzinfo=UTC)
    s, _ = align_window(start, end, 300)
    assert s == datetime(2026, 8, 28, 10, 5, 0, tzinfo=UTC)


def test_align_window_overlapping_pulls_share_bucket_keys():
    t0 = datetime(2026, 8, 28, 10, 0, 37, tzinfo=UTC)
    s1, _ = align_window(t0, t0 + timedelta(hours=1), 60)
    s2, _ = align_window(t0 + timedelta(seconds=20), t0 + timedelta(hours=1), 60)
    assert s1 == s2


def test_align_window_rejects_naive_datetimes():
    with pytest.raises(DatasetReadError):
        align_window(datetime(2026, 8, 28, 10, 0), END, 60)


def test_align_window_rejects_empty_window():
    with pytest.raises(DatasetReadError):
        align_window(END, END, 60)
    with pytest.raises(DatasetReadError):  # colapsa tras alinear
        align_window(END, END + timedelta(seconds=30), 60)


def test_align_window_accepts_exactly_seven_days():
    end = datetime(2026, 8, 28, 0, 0, tzinfo=UTC)
    s, e = align_window(end - timedelta(days=7), end, 60)
    assert e - s == timedelta(days=7)


@pytest.mark.parametrize("bucket", [500, 7000])
@pytest.mark.parametrize("offset", [0, 1, 37, 499, 501, 3499, 6999, 86399, 123457])
def test_align_window_seven_days_with_non_dividing_bucket(bucket, offset):
    now = datetime(2026, 8, 28, 0, 0, tzinfo=UTC) + timedelta(seconds=offset)
    start, end = align_window(now - timedelta(minutes=10080), now, bucket)
    assert end - start <= timedelta(days=7)
    assert int(start.timestamp()) % bucket == 0
    assert int(end.timestamp()) % bucket == 0
    assert start < end


def test_align_window_rejects_more_than_seven_days_after_aligning():
    end = datetime(2026, 8, 28, 0, 0, tzinfo=UTC)
    start = end - timedelta(days=7, seconds=1)  # el floor suma 1 bucket
    with pytest.raises(DatasetReadError):
        align_window(start, end, 60)


# -- to_batch (MLD-2, MLD-7.2, MLD-8) ----------------------------------------

def test_to_batch_maps_rows_and_propagates_bucket_seconds():
    rows = [_row(), _row(metric_type_id=5, value=3.0, session_count=1)]
    batch = to_batch(rows, 60, START, END)
    assert [b.metric_type_id for b in batch] == [1, 5]
    assert all(b.bucket_seconds == 60 for b in batch)
    assert batch[0].value == 120.5
    assert str(batch[0].application_id) == APP


def test_to_batch_empty_list():
    assert to_batch([], 60, START, END) == []


def test_to_batch_ignores_extra_response_fields():
    batch = to_batch([_row(extra="x")], 60, START, END)
    assert len(batch) == 1


@pytest.mark.parametrize(
    "bad",
    [
        {k: v for k, v in _row().items() if k != "value"},
        _row(value=None),
        _row(value=float("nan")),
        _row(session_count=-1),
        _row(timestamp="2026-08-28T21:15:00"),  # naive
        _row(timestamp="2026-08-28T21:15:05Z"),  # no alineado
    ],
)
def test_to_batch_fail_fast_on_malformed_row(bad):
    with pytest.raises(DatasetReadError, match="row 1"):
        to_batch([_row(), bad, _row(metric_type_id=2)], 60, START, END)


def test_to_batch_rejects_mixed_applications():
    with pytest.raises(DatasetReadError):
        to_batch([_row(), _row(application_id=OTHER_APP, metric_type_id=2)], 60, START, END)


def test_to_batch_rejects_duplicate_series_bucket():
    with pytest.raises(DatasetReadError, match="duplicate"):
        to_batch([_row(), _row()], 60, START, END)


@pytest.mark.parametrize(
    "ts", ["2026-08-28T20:59:00Z", "2026-08-28T22:00:00Z"]
)
def test_to_batch_rejects_timestamp_outside_window(ts):
    with pytest.raises(DatasetReadError, match="window"):
        to_batch([_row(timestamp=ts)], 60, START, END)


def test_to_batch_rejects_non_dict_row():
    with pytest.raises(DatasetReadError):
        to_batch(["nope"], 60, START, END)


# -- config (MLD-5, MLD-10) --------------------------------------------------

def test_settings_defaults(monkeypatch):
    s = _settings(monkeypatch)
    assert s.bucket_seconds == 60
    assert s.window_minutes == 60
    assert s.http_timeout_seconds == 10
    assert s.http_retries == 2
    assert s.api_base_url == "http://core:8000"


def test_settings_bucket_seconds_below_60_fails(monkeypatch):
    with pytest.raises(ValidationError):
        _settings(monkeypatch, INTELLOPS_ML_BUCKET_SECONDS="30")


@pytest.mark.parametrize("name", ["INTELLOPS_ML_API_KEY", "INTELLOPS_API_BASE_URL"])
def test_settings_missing_required_names_variable(monkeypatch, name):
    with pytest.raises(ValidationError, match=name):
        _settings(monkeypatch, **{name: None})


@pytest.mark.parametrize("minutes", ["0", "10081"])
def test_settings_window_out_of_range_fails(monkeypatch, minutes):
    with pytest.raises(ValidationError):
        _settings(monkeypatch, INTELLOPS_ML_WINDOW_MINUTES=minutes)


def test_settings_window_must_cover_one_bucket(monkeypatch):
    with pytest.raises(ValidationError):
        _settings(
            monkeypatch,
            INTELLOPS_ML_BUCKET_SECONDS="3600",
            INTELLOPS_ML_WINDOW_MINUTES="30",
        )


def test_settings_api_key_not_in_repr(monkeypatch):
    s = _settings(monkeypatch)
    assert API_KEY not in repr(s)
    assert API_KEY not in str(s)
    assert s.api_key.get_secret_value() == API_KEY


# -- reader con MockTransport (MLD-3, MLD-6.3, MLD-9) ------------------------

def _client(handler):
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_reader_sends_authenticated_aligned_request(monkeypatch):
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = request.url
        seen["key"] = request.headers.get("X-API-Key")
        return httpx.Response(200, json=[_row()])

    s = _settings(monkeypatch)
    batch = read_dataset(s, client=_client(handler), now=NOW)

    assert len(batch) == 1
    assert seen["key"] == API_KEY
    assert seen["url"].path == "/metrics/query"
    assert str(seen["url"]).startswith("http://core:8000/metrics/query")
    params = dict(seen["url"].params)
    assert params["bucket_seconds"] == "60"
    assert params["end"] == "2026-08-28T22:00:00Z"
    assert params["start"] == "2026-08-28T21:00:00Z"
    assert "application_id" not in params


def test_reader_returns_empty_list(monkeypatch):
    s = _settings(monkeypatch)
    out = read_dataset(s, client=_client(lambda r: httpx.Response(200, json=[])), now=NOW)
    assert out == []


@pytest.mark.parametrize("status", [401, 403])
def test_reader_auth_errors(monkeypatch, status):
    body = {"error": {"code": "invalid_api_key", "message": "x"}}
    s = _settings(monkeypatch)
    with pytest.raises(DatasetReadError, match=str(status)):
        read_dataset(s, client=_client(lambda r: httpx.Response(status, json=body)), now=NOW)


def test_reader_422_includes_status_and_code(monkeypatch):
    body = {"error": {"code": "invalid_query_range", "message": "bad"}}
    s = _settings(monkeypatch)
    with pytest.raises(DatasetReadError) as exc:
        read_dataset(s, client=_client(lambda r: httpx.Response(422, json=body)), now=NOW)
    assert exc.value.status == 422
    assert exc.value.code == "invalid_query_range"


@pytest.mark.parametrize("status", [500, 503])
def test_reader_5xx_is_unavailable(monkeypatch, status):
    s = _settings(monkeypatch)
    with pytest.raises(DatasetReadError, match="unavailable"):
        read_dataset(s, client=_client(lambda r: httpx.Response(status)), now=NOW)


def test_reader_timeout_is_unavailable(monkeypatch):
    def handler(request):
        raise httpx.ReadTimeout("slow", request=request)

    s = _settings(monkeypatch)
    with pytest.raises(DatasetReadError, match="unavailable"):
        read_dataset(s, client=_client(handler), now=NOW)


@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(200, json={"data": []}),
        httpx.Response(200, content=b"<html>not json</html>"),
    ],
)
def test_reader_body_out_of_contract(monkeypatch, response):
    s = _settings(monkeypatch)
    with pytest.raises(DatasetReadError, match="contract"):
        read_dataset(s, client=_client(lambda r: response), now=NOW)


def test_reader_malformed_row_returns_no_partial_data(monkeypatch):
    s = _settings(monkeypatch)
    rows = [_row(), _row(metric_type_id=2, value=None)]
    with pytest.raises(DatasetReadError):
        read_dataset(s, client=_client(lambda r: httpx.Response(200, json=rows)), now=NOW)


def test_reader_does_not_fall_back_to_mock_and_does_not_log_key(monkeypatch, caplog):
    s = _settings(monkeypatch)
    with caplog.at_level(logging.DEBUG):
        with pytest.raises(DatasetReadError):
            read_dataset(s, client=_client(lambda r: httpx.Response(503)), now=NOW)
    assert API_KEY not in caplog.text


def test_reader_creates_default_client_when_not_injected(monkeypatch):
    created = {}

    class FakeClient(httpx.Client):
        def __init__(self, *args, **kwargs):
            created["kwargs"] = kwargs
            super().__init__(transport=httpx.MockTransport(
                lambda r: httpx.Response(200, json=[])))

    monkeypatch.setattr("src.ml.pipeline.api_reader.httpx.Client", FakeClient)
    s = _settings(monkeypatch)
    assert read_dataset(s, now=NOW) == []
    assert created["kwargs"]["timeout"] == 10


# -- aislamiento (MLD-3.2, ARCH-AI-3.2) --------------------------------------

def test_src_ml_does_not_import_src_api():
    root = pathlib.Path(__file__).resolve().parent.parent / "src" / "ml"
    offenders = []
    for path in root.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8-sig"))
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            for name in names:
                if name == "api" or name.startswith(("api.", "src.api")):
                    offenders.append(f"{path.name}: {name}")
    assert offenders == []
