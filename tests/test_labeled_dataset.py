"""Tests del generador sintético etiquetado (A.4, spec synthetic-dataset).

Rápidos y sin Postgres: usan parámetros chicos (3 días, 2 apps). La corrida
por defecto (14 días, 3 apps) es manual y queda documentada en el README.
"""
import ast
import csv
import hashlib
import importlib.util
import json
import pathlib
from collections import defaultdict
from datetime import datetime

import numpy as np
import pytest

from src.ml.schemas import MetricBatchInput

pytestmark = pytest.mark.unit

MODULE_PATH = (
    pathlib.Path(__file__).resolve().parents[1] / "ml" / "data" / "generate_labeled_dataset.py"
)
SMALL = {"seed": 7, "days": 3, "bucket_seconds": 60, "apps": 2}
CONTRACT = (
    "application_id", "metric_type_id", "timestamp", "bucket_seconds", "value", "session_count",
)


def _load_module():
    spec = importlib.util.spec_from_file_location("generate_labeled_dataset", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_module()


@pytest.fixture(scope="module", name="small")
def _small():
    return gen.generate(**SMALL)


@pytest.fixture(scope="module", name="exported")
def _exported(small, tmp_path_factory):
    return gen.write_dataset(small, tmp_path_factory.mktemp("small"))


def _series(rows):
    grouped = defaultdict(list)
    for row in rows:
        grouped[(row["application_id"], row["metric_type_id"])].append(row)
    return grouped


def _epoch(ts):
    return int(datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp())


# --- SYN-1 reproducibilidad ------------------------------------------------

def test_same_seed_is_byte_identical(small, exported, tmp_path):
    csv_a, manifest_a = exported
    csv_b, manifest_b = gen.write_dataset(gen.generate(**SMALL), tmp_path)
    assert csv_a.read_bytes() == csv_b.read_bytes()
    assert manifest_a.read_bytes() == manifest_b.read_bytes()
    assert small.rows


def test_different_seed_differs(exported, tmp_path):
    other = gen.write_dataset(gen.generate(**{**SMALL, "seed": 8}), tmp_path)[0]
    assert exported[0].read_bytes() != other.read_bytes()


# --- SYN-2 contrato M4 -----------------------------------------------------

def test_every_row_validates_against_m4(small):
    for row in small.rows:
        MetricBatchInput(**{key: row[key] for key in CONTRACT})


def test_timestamps_aligned_utc_and_unique_per_series(small):
    for rows in _series(small.rows).values():
        stamps = [row["timestamp"] for row in rows]
        assert all(ts.endswith("Z") for ts in stamps)
        assert all(_epoch(ts) % SMALL["bucket_seconds"] == 0 for ts in stamps)
        assert len(stamps) == len(set(stamps))


def test_zero_session_buckets_are_omitted(small):
    n_buckets = SMALL["days"] * 86400 // SMALL["bucket_seconds"]
    assert all(row["session_count"] >= 1 for row in small.rows)
    low_traffic = gen.APP_PROFILES[1]["app_id"]
    sizes = [len(rows) for (app, _), rows in _series(small.rows).items() if app == low_traffic]
    assert sizes and all(size < n_buckets for size in sizes)


def test_value_ranges(small):
    assert all(row["value"] >= 0 for row in small.rows)
    assert all(row["value"] <= 1 for row in small.rows if row["metric_type_id"] == 4)


def test_bucket_seconds_parameter_is_honoured():
    # Duraciones y gaps se miden en buckets: con 5 min hace falta una ventana más larga.
    dataset = gen.generate(seed=1, days=14, bucket_seconds=300, apps=1)
    assert {row["bucket_seconds"] for row in dataset.rows} == {300}
    assert all(_epoch(row["timestamp"]) % 300 == 0 for row in dataset.rows)


def test_infeasible_window_fails_explicitly():
    with pytest.raises(RuntimeError, match="increase --days"):
        gen.generate(seed=1, days=3, bucket_seconds=3600, apps=1)


def test_rejects_bucket_below_sixty():
    with pytest.raises(ValueError):
        gen.generate(seed=1, days=3, bucket_seconds=30, apps=1)


# --- SYN-3 realismo --------------------------------------------------------

def _hour(ts):
    return int(ts[11:13])


def test_daily_seasonality_in_sessions(small):
    checkout = gen.APP_PROFILES[0]["app_id"]
    rows = [r for r in small.rows if r["application_id"] == checkout and r["metric_type_id"] == 1]
    peak = [r["session_count"] for r in rows if 10 <= _hour(r["timestamp"]) < 17]
    night = [r["session_count"] for r in rows if 1 <= _hour(r["timestamp"]) < 5]
    assert np.mean(peak) > 2 * np.mean(night)


def test_latency_is_right_skewed(small):
    for metric_id in (1, 2, 3):
        values = [r["value"] for r in small.rows if r["metric_type_id"] == metric_id]
        assert np.mean(values) > np.median(values)


def test_latency_metrics_share_noise_within_app(small):
    checkout = gen.APP_PROFILES[0]["app_id"]
    by_metric = {
        m: {r["timestamp"]: r["value"] for r in small.rows
            if r["application_id"] == checkout and r["metric_type_id"] == m
            and not r["is_anomaly"]}
        for m in (1, 3)
    }
    common = sorted(set(by_metric[1]) & set(by_metric[3]))
    # Promedios de 15 buckets: atenúan el ruido de muestreo y aíslan el factor compartido.
    blocks = len(common) // 15
    ttfb, xhr = (
        np.log([by_metric[m][t] for t in common[:blocks * 15]]).reshape(blocks, 15).mean(axis=1)
        for m in (1, 3)
    )
    assert np.corrcoef(np.diff(ttfb), np.diff(xhr))[0, 1] > 0.2


# --- SYN-4 catálogo y etiquetas --------------------------------------------

def _anomalies(dataset):
    return [e for e in dataset.events if e["kind"] == "anomaly"]


def test_every_type_and_severity_in_both_splits(small):
    seen = {(r["anomaly_type"], r["severity"], r["split"]) for r in small.rows if r["is_anomaly"]}
    for split in ("train", "validation"):
        for anomaly_type in gen.ANOMALY_TYPES:
            for severity in gen.SEVERITIES:
                assert (anomaly_type, severity, split) in seen


def test_labels_are_consistent(small):
    for row in small.rows:
        if row["is_anomaly"]:
            assert row["anomaly_type"] in gen.ANOMALY_TYPES
            assert row["severity"] in gen.SEVERITIES
            assert row["event_id"].startswith("A-")
            assert row["hard_negative"] == 0
        elif not row["hard_negative"]:
            assert (row["anomaly_type"], row["severity"], row["event_id"]) == ("none", "none", "")


def test_correlated_incident_spans_metrics_of_one_app(small):
    by_event = defaultdict(set)
    for row in small.rows:
        if row["anomaly_type"] == "correlated_incident":
            by_event[row["event_id"]].add((row["application_id"], row["metric_type_id"]))
    assert by_event
    for series in by_event.values():
        assert len({app for app, _ in series}) == 1
        assert len({metric for _, metric in series}) >= 2


def _key(row):
    return row["application_id"], row["metric_type_id"], row["timestamp"]


def test_labels_match_real_changes_against_clean_run(small, monkeypatch):
    # Misma seed sin inyección: las series base no dependen de la agenda de anomalías.
    monkeypatch.setattr(gen, "_inject", lambda *args: None)
    clean = {_key(r): (r["value"], r["session_count"]) for r in gen.generate(**SMALL).rows}
    assert {_key(r) for r in small.rows} == set(clean)  # la inyección no crea ni borra filas
    for row in small.rows:
        unchanged = clean[_key(row)] == (row["value"], row["session_count"])
        assert unchanged != bool(row["is_anomaly"]), row


def test_severity_magnitude_within_band(small):
    for event in _anomalies(small):
        bands = gen.DROPOUT_BANDS if event["type"] == "dropout" else gen.SEVERITY_BANDS
        low, high = bands[event["severity"]]
        assert event["magnitude"]
        assert all(low <= k < high for k in event["magnitude"].values())


# --- SYN-5 agenda ----------------------------------------------------------

def test_events_do_not_overlap_and_keep_min_gap(small):
    windows = defaultdict(list)
    for event in small.events:
        for metric_id in event["metric_type_ids"]:
            windows[(event["app_id"], metric_id)].append(
                (event["start_index"], event["start_index"] + event["length"]))
    for spans in windows.values():
        spans.sort()
        for (_, end), (start, _) in zip(spans, spans[1:]):
            assert start - end >= gen.MIN_GAP_BUCKETS


def test_events_never_cross_the_split_boundary(small):
    splits = defaultdict(set)
    for row in small.rows:
        if row["event_id"]:
            splits[row["event_id"]].add(row["split"])
    assert splits and all(len(found) == 1 for found in splits.values())
    boundary = small.params["boundary_index"]
    for event in small.events:
        end = event["start_index"] + event["length"]
        assert end <= boundary or event["start_index"] >= boundary


def test_some_anomalies_are_placed_at_peak_hours(small):
    assert any(event["at_peak"] for event in _anomalies(small))


def test_contamination_within_target_for_default_size():
    dataset = gen.generate(seed=gen.DEFAULT_SEED, days=gen.DEFAULT_DAYS, apps=gen.DEFAULT_APPS)
    anomalous = sum(row["is_anomaly"] for row in dataset.rows)
    assert 0.01 <= anomalous / len(dataset.rows) <= 0.03


# --- SYN-6 hard negatives --------------------------------------------------

def test_hard_negatives_are_benign_and_in_both_splits(small):
    benign = [row for row in small.rows if row["hard_negative"]]
    assert all(row["is_anomaly"] == 0 for row in benign)
    assert all(row["event_id"].startswith("H-") for row in benign)
    assert all(row["severity"] == "none" for row in benign)
    assert {row["anomaly_type"] for row in benign} == set(gen.HARD_NEGATIVE_TYPES)
    assert {row["split"] for row in benign} == {"train", "validation"}


def test_traffic_surge_raises_session_count(small):
    surges = [e for e in small.events if e["type"] == "benign_traffic_surge"]
    assert surges
    for event in surges:
        rows = sorted(
            (r for r in small.rows if r["application_id"] == event["app_id"]
             and r["metric_type_id"] == 1), key=lambda r: r["timestamp"])
        inside = [r["session_count"] for r in rows if r["event_id"] == event["event_id"]]
        before = [r["session_count"] for r in rows if r["timestamp"] < event["start"]][-60:]
        assert np.mean(inside) > 1.3 * np.mean(before)


# --- SYN-7 split temporal --------------------------------------------------

def test_split_is_temporal_with_global_boundary(small):
    boundary = small.params["boundary"]
    for rows in _series(small.rows).values():
        train = [r["timestamp"] for r in rows if r["split"] == "train"]
        validation = [r["timestamp"] for r in rows if r["split"] == "validation"]
        assert train and validation
        assert max(train) < boundary <= min(validation)


# --- SYN-8 export y manifest -----------------------------------------------

def _read_csv(path):
    with open(path, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def test_csv_has_exact_columns(exported):
    with open(exported[0], encoding="utf-8", newline="") as fh:
        header = next(csv.reader(fh))
    assert tuple(header) == CONTRACT + (
        "is_anomaly", "anomaly_type", "severity", "event_id", "hard_negative", "split")


def test_manifest_matches_csv(small, exported):
    csv_path, manifest_path = exported
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    rows = _read_csv(csv_path)
    assert manifest["csv_sha256"] == hashlib.sha256(csv_path.read_bytes()).hexdigest()
    assert manifest["params"]["seed"] == SMALL["seed"]
    assert manifest["numpy_version"] == np.__version__
    assert [col["name"] for col in manifest["schema"]] == list(gen.COLUMNS)
    counts = manifest["row_counts"]
    assert counts["total"] == len(rows) == len(small.rows)
    for split in ("train", "validation"):
        assert counts["by_split"][split] == sum(r["split"] == split for r in rows)
        assert counts["anomalous_by_split"][split] == sum(
            r["split"] == split and r["is_anomaly"] == "1" for r in rows)
    assert sum(counts["by_anomaly_type"].values()) == len(rows)
    assert counts["by_severity"]["high"] == sum(r["severity"] == "high" for r in rows)
    ttfb = [float(r["value"]) for r in rows if r["metric_type_id"] == "1"]
    assert manifest["value_ranges"]["1"]["min"] == min(ttfb)
    assert manifest["value_ranges"]["1"]["max"] == max(ttfb)
    assert len(manifest["events"]) == len(small.events)


def test_cli_writes_the_same_files(exported, tmp_path):
    gen.main(["--seed", "7", "--days", "3", "--apps", "2", "--out-dir", str(tmp_path)])
    assert (tmp_path / gen.CSV_NAME).read_bytes() == exported[0].read_bytes()
    assert (tmp_path / gen.MANIFEST_NAME).read_bytes() == exported[1].read_bytes()


# --- SYN-9 consumo por B.6 -------------------------------------------------

def test_loader_returns_validated_rows_and_labels(small, exported):
    data = gen.load_labeled_dataset(exported[0])
    assert set(data) == {"train", "validation"}
    total = 0
    for split, part in data.items():
        assert len(part.rows) == len(part.labels) > 0
        assert all(isinstance(row, MetricBatchInput) for row in part.rows)
        assert all(isinstance(label.is_anomaly, bool) for label in part.labels)
        total += len(part.rows)
        expected = sum(r["is_anomaly"] for r in small.rows if r["split"] == split)
        assert sum(label.is_anomaly for label in part.labels) == expected
    assert total == len(small.rows)


def test_loader_rejects_tampered_csv(exported, tmp_path):
    csv_path = tmp_path / gen.CSV_NAME
    csv_path.write_bytes(exported[0].read_bytes().replace(b",train", b",validation", 1))
    (tmp_path / gen.MANIFEST_NAME).write_bytes(exported[1].read_bytes())
    with pytest.raises(ValueError, match="sha256"):
        gen.load_labeled_dataset(csv_path)


def test_module_is_decoupled_from_ingest():
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.add(node.module or "")
    forbidden = ("src.api", "api", "sqlalchemy", "asyncpg", "psycopg", "httpx", "requests",
                 "urllib", "http", "socket")
    assert not [name for name in imported if name.split(".")[0] in forbidden
                or name.startswith("src.api")]
