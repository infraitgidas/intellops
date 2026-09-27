"""
Synthetic RUM dataset generator for ISS-S3-05 EDA.

Generates a realistic time-series dataset respecting the MetricBatchInput contract:
  - application_id: UUID4
  - metric_id:      UUID4
  - metric_type_id: int (1-5, mapped to TTFB/FCP/XHR_LATENCY/JS_EXCEPTION_RATE/RAGE_CLICK)
  - timestamp:      datetime (ISO-8601, UTC)
  - value:          float   (metric-specific units and distribution)
  - session_count:  int

Metric type catalog mirrors migration seed in 0001_initial_schema.py:
  1 = TTFB              (ms)
  2 = FCP               (ms)
  3 = XHR_LATENCY       (ms)
  4 = JS_EXCEPTION_RATE (rate 0..1)
  5 = RAGE_CLICK        (count)

Usage:
    python ml/data/generate_mock_dataset.py
    python ml/data/generate_mock_dataset.py --rows 2000 --out ml/data/rum_mock.json
"""
import argparse
import json
import uuid
from datetime import datetime, timedelta, timezone

import numpy as np

METRIC_TYPES = {
    1: {"name": "TTFB",              "mean": 300,  "std": 120,  "anomaly_factor": 5,  "floor": 0.0,  "ceil": None},
    2: {"name": "FCP",               "mean": 1800, "std": 400,  "anomaly_factor": 3,  "floor": 0.0,  "ceil": None},
    3: {"name": "XHR_LATENCY",       "mean": 250,  "std": 80,   "anomaly_factor": 6,  "floor": 0.0,  "ceil": None},
    4: {"name": "JS_EXCEPTION_RATE", "mean": 0.02, "std": 0.01, "anomaly_factor": 10, "floor": 0.0,  "ceil": 1.0},
    5: {"name": "RAGE_CLICK",        "mean": 0.5,  "std": 0.3,  "anomaly_factor": 8,  "floor": 0.0,  "ceil": None},
}

APP_IDS = [
    "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "a1b2c3d4-58cc-4372-a567-0e02b2c3d480",
    "b2c3d4e5-58cc-4372-a567-0e02b2c3d481",
]


def _apply_tod_pattern(value, hour):
    if 9 <= hour <= 11 or 14 <= hour <= 17:
        value *= 1.20
    elif hour >= 22 or hour <= 5:
        value *= 0.75
    return value


def _generate_value(cfg, rng, is_anomaly):
    if is_anomaly:
        spike = rng.uniform(cfg["anomaly_factor"] * cfg["std"], cfg["anomaly_factor"] * cfg["std"] * 1.5)
        value = cfg["mean"] + spike
    else:
        value = float(rng.normal(cfg["mean"], cfg["std"]))
    value = max(cfg["floor"], value)
    if cfg["ceil"] is not None:
        value = min(cfg["ceil"], value)
    return round(value, 4)


def generate_dataset(n_rows=1500, start=None, anomaly_rate=0.05, seed=42):
    rng = np.random.default_rng(seed)
    if start is None:
        start = datetime(2026, 8, 1, 0, 0, 0, tzinfo=timezone.utc)
    records = []
    n_apps = len(APP_IDS)
    n_types = len(METRIC_TYPES)
    for i in range(n_rows):
        app_id = APP_IDS[i % n_apps]
        metric_type_id = (i % n_types) + 1
        cfg = METRIC_TYPES[metric_type_id]
        ts = start + timedelta(minutes=5 * (i // (n_apps * n_types)))
        hour = ts.hour
        is_anomaly = bool(rng.random() < anomaly_rate)
        value = _generate_value(cfg, rng, is_anomaly)
        if not is_anomaly:
            value = round(_apply_tod_pattern(value, hour), 4)
            value = max(cfg["floor"], value)
            if cfg["ceil"] is not None:
                value = min(cfg["ceil"], value)
        session_count = max(1, int(rng.normal(30, 15)))
        records.append({
            "application_id": app_id,
            "metric_id": str(uuid.uuid4()),
            "metric_type_id": metric_type_id,
            "timestamp": ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "value": value,
            "session_count": session_count,
        })
    return records


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic RUM mock dataset for EDA")
    parser.add_argument("--rows", type=int, default=1500)
    parser.add_argument("--out", type=str, default="ml/data/rum_mock.json")
    parser.add_argument("--anomaly-rate", type=float, default=0.05)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    dataset = generate_dataset(n_rows=args.rows, anomaly_rate=args.anomaly_rate, seed=args.seed)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)
    print(f"Generated {len(dataset)} records -> {args.out}")


if __name__ == "__main__":
    main()
