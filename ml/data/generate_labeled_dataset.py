"""Generador sintético de series RUM con anomalías inyectadas y etiquetadas (A.4).

Produce un dataset reproducible (seed fija) con el contrato M4 de
`src/ml/schemas.py::MetricBatchInput` más columnas de etiqueta, un split
temporal train/validation y un `manifest.json`. Pensado para B.6 (baseline
estadístico vs Isolation Forest). Es SINTÉTICO: ver `ml/data/README.md`.

Solo numpy + stdlib. No importa `src.api`, no usa DB ni HTTP.

Uso:
    python ml/data/generate_labeled_dataset.py
    python ml/data/generate_labeled_dataset.py --seed 7 --days 8 --apps 2
"""
import argparse
import csv
import hashlib
import json
import math
import pathlib
import platform
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import NamedTuple

import numpy as np

GENERATOR_VERSION = "1.0.0"
DEFAULT_SEED = 66
DEFAULT_DAYS = 28  # validation (20 %) con 3 eventos por celda y contaminación ~2 %
DEFAULT_BUCKET_SECONDS = 60
DEFAULT_APPS = 3
DEFAULT_OUT_DIR = "ml/data/synthetic"
CSV_NAME = "labeled_dataset.csv"
MANIFEST_NAME = "manifest.json"
MIN_BUCKET_SECONDS = 60
START = datetime(2026, 8, 3, tzinfo=timezone.utc)  # lunes
TRAIN_FRACTION = 0.8
# Menos días no alcanzan para ubicar MIN_PER_COMBO eventos de cada combinación en
# ambos splits (medido: seeds 0-19 x apps 1-3 x buckets 60/300/900/3600/7000 s).
MIN_DAYS = 8

CONTRACT_COLUMNS = (
    "application_id", "metric_type_id", "timestamp", "bucket_seconds", "value", "session_count",
)
LABEL_COLUMNS = ("is_anomaly", "anomaly_type", "severity", "event_id", "hard_negative", "split")
COLUMNS = CONTRACT_COLUMNS + LABEL_COLUMNS
NONE = "none"
SCHEMA = (
    ("application_id", "uuid4", "app (perfil de tráfico)"),
    ("metric_type_id", "int", "1 TTFB, 2 FCP, 3 XHR_LATENCY, 4 JS_EXCEPTION_RATE, 5 RAGE_CLICK"),
    ("timestamp", "iso8601", "inicio del bucket, UTC con sufijo Z, alineado a bucket_seconds"),
    ("bucket_seconds", "int", ">= 60"),
    ("value", "float", "4 decimales; >= 0; tasa <= 1"),
    ("session_count", "int", ">= 1 (los buckets sin sesiones se omiten)"),
    ("is_anomaly", "0|1", "1 = fila que una anomalía inyectada modificó"),
    ("anomaly_type", "str", "tipo de anomalía, patrón benigno o none"),
    ("severity", "str", "low | medium | high | none"),
    ("event_id", "str", "A-NNNN (anomalía), H-NNNN (hard negative) o vacío"),
    ("hard_negative", "0|1", "1 = evento benigno que parece anómalo"),
    ("split", "str", "train | validation (corte temporal global)"),
)
UNITS = {1: "ms", 2: "ms", 3: "ms", 4: "ratio", 5: "clicks/session"}

APP_PROFILES = (
    {"app_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479", "name": "checkout", "peak": 90.0,
     "night_floor": 0.15, "weekend": (0.85, 0.80),
     "level": {1: 280.0, 2: 1600.0, 3: 220.0, 4: 0.012, 5: 0.35}},
    {"app_id": "a1b2c3d4-58cc-4372-a567-0e02b2c3d480", "name": "backoffice", "peak": 25.0,
     "night_floor": 0.05, "weekend": (0.25, 0.15),
     "level": {1: 450.0, 2: 2200.0, 3: 380.0, 4: 0.025, 5: 0.60}},
    {"app_id": "b2c3d4e5-58cc-4372-a567-0e02b2c3d481", "name": "portal", "peak": 6.0,
     "night_floor": 0.10, "weekend": (0.60, 0.55),
     "level": {1: 350.0, 2: 2600.0, 3: 300.0, 4: 0.020, 5: 0.30}},
)

# kind: latency (ms, lognormal), rate (proporción binomial), count (clics por sesión).
METRICS = {
    1: {"name": "TTFB", "kind": "latency", "sigma": 0.12, "sample": 0.6, "alpha": 0.15,
        "rho": 0.6, "coverage": 1.00, "trend": 0.03},
    2: {"name": "FCP", "kind": "latency", "sigma": 0.10, "sample": 0.5, "alpha": 0.10,
        "rho": 0.6, "coverage": 0.95, "trend": 0.02},
    3: {"name": "XHR_LATENCY", "kind": "latency", "sigma": 0.15, "sample": 0.8, "alpha": 0.25,
        "rho": 0.6, "coverage": 0.70, "trend": 0.04},
    4: {"name": "JS_EXCEPTION_RATE", "kind": "rate", "sigma": 0.20, "sample": 0.0,
        "alpha": 0.10, "rho": 0.2, "coverage": 1.00, "trend": 0.0},
    5: {"name": "RAGE_CLICK", "kind": "count", "sigma": 0.20, "sample": 0.0, "alpha": 0.10,
        "rho": 0.2, "coverage": 1.00, "trend": 0.0},
}

TRAFFIC_TREND = 0.05
DAY_FACTOR_SIGMA = 0.08
TRAFFIC_NOISE = 0.10
PHI_TRAFFIC, PHI_COMMON, PHI_OWN = 0.95, 0.9, 0.8
STREAMS_PER_APP = 2 + len(METRICS)  # traffic, common, una por métrica
LATENCY_IDS = (1, 2, 3)
LATENCY_FLOOR = 0.05  # piso de latencia como fracción de la base (nunca 0 ms)

# --- Catálogo de anomalías (design §3) -------------------------------------
ANOMALY_TYPES = (
    "spike", "level_shift", "drift", "variance_burst", "dropout", "correlated_incident",
)
SEVERITIES = ("low", "medium", "high")
SEVERITY_BANDS = {"low": (3.0, 4.0), "medium": (4.0, 6.0), "high": (6.0, 9.0)}  # sigmas
DROPOUT_BANDS = {"low": (0.4, 0.6), "medium": (0.6, 0.8), "high": (0.8, 0.95)}  # fracción
DURATIONS = {  # minutos de reloj (min, max); se convierten a buckets con _buckets()
    "spike": (1, 3), "level_shift": (20, 60), "drift": (30, 90),
    "variance_burst": (15, 45), "dropout": (5, 20), "correlated_incident": (10, 40),
}
PLACEMENT_ORDER = (  # más largas primero: empaquetan mejor
    "correlated_incident", "drift", "level_shift", "variance_burst", "dropout", "spike",
)
CORRELATED_EXTRA_METRIC = 4  # JS_EXCEPTION_RATE se suma con prob. 0.5
CONTAMINATION_TARGET = 0.02
MIN_PER_COMBO = 3  # eventos mínimos por (tipo, severidad) y split
MIN_GAP_MINUTES = 30
NEIGHBORHOOD = 60  # buckets: ventana estadística del desvío local, no una duración
MIN_EXPECTED_SESSIONS = 3.0
MIN_DROPOUT_SESSIONS = 20.0
PEAK_EVERY = 3
PEAK_HOURS = (10.0, 17.0)
SPLITS = ("train", "validation")

# --- Hard negatives (design §4) --------------------------------------------
HARD_NEGATIVE_TYPES = ("benign_traffic_surge", "benign_maintenance")
SURGE_DURATION = (30, 90)  # minutos
SURGE_MULTIPLIER = (1.8, 2.6)
SURGE_DAYS_PER_EVENT = 3  # ~1 surge por app cada 3 días de cada split
MAINTENANCE_START = (19 * 3600, 23 * 3600 + 45 * 60)  # inicio sorteado por app y día (UTC)
MAINTENANCE_SECONDS = 15 * 60
MAINTENANCE_TRAFFIC = 0.6
# Efecto en `value` (sigmas locales, banda low/medium) sobre estas métricas.
BENIGN_SIGMAS = (3.0, 6.0)
BENIGN_METRICS = {"benign_traffic_surge": LATENCY_IDS, "benign_maintenance": (1, 3)}


class Dataset(NamedTuple):
    """Dataset generado en memoria: filas, eventos y parámetros."""
    rows: list
    events: list
    params: dict


class Timeline(NamedTuple):
    """Eje temporal de buckets."""
    n: int
    stamps: list
    hours: np.ndarray
    dow: np.ndarray
    day: np.ndarray
    frac: np.ndarray
    boundary: int


def _timeline(days, bucket_seconds):
    start = int(START.timestamp()) // bucket_seconds * bucket_seconds
    n = days * 86400 // bucket_seconds
    epochs = start + np.arange(n, dtype=np.int64) * bucket_seconds
    origin = datetime.fromtimestamp(start, tz=timezone.utc)
    stamps = [(origin + timedelta(seconds=i * bucket_seconds)).strftime("%Y-%m-%dT%H:%M:%SZ")
              for i in range(n)]
    day = (epochs - start) // 86400
    return Timeline(
        n=n, stamps=stamps, hours=(epochs % 86400) / 3600.0,
        dow=(day + origin.weekday()) % 7, day=day, frac=np.arange(n) / max(n - 1, 1),
        boundary=int(math.floor(TRAIN_FRACTION * n)),
    )


def _buckets(minutes, bucket_seconds):
    """Minutos de reloj -> buckets (mínimo 1): la duración no depende del bucket."""
    return max(1, round(minutes * 60 / bucket_seconds))


def _ar1(rng, n, phi):
    """AR(1) estacionario de varianza unitaria."""
    eps = rng.standard_normal(n).tolist()
    scale = math.sqrt(1.0 - phi * phi)
    out = [0.0] * n
    prev = 0.0
    for i, shock in enumerate(eps):
        prev = shock if i == 0 else phi * prev + scale * shock
        out[i] = prev
    return np.asarray(out)


def _expected_traffic(profile, tl):
    """Sesiones/min esperadas (sin ruido): estacionalidad diaria, semanal y tendencia."""
    diurnal = 0.5 - 0.5 * np.cos(2 * np.pi * (tl.hours - 4.0) / 24.0)
    weekend = tl.dow >= 5
    business = np.exp(-(((tl.hours - 13.0) / 3.5) ** 2)) * np.where(weekend, 0.3, 1.0)
    floor = profile["night_floor"]
    daily = floor + (1.0 - floor) * (0.55 * diurnal + 0.45 * business)
    sat, sun = profile["weekend"]
    weekly = np.select([tl.dow == 5, tl.dow == 6], [sat, sun], 1.0)
    return profile["peak"] * daily * weekly * (1.0 + TRAFFIC_TREND * tl.frac)


def _app_trace(profile, streams, tl, bucket_seconds, traffic_mult):
    traffic_rng = np.random.default_rng(streams[0])
    expected = _expected_traffic(profile, tl)
    day_factor = traffic_rng.lognormal(0.0, DAY_FACTOR_SIGMA, size=int(tl.day.max()) + 1)
    noise = np.exp(TRAFFIC_NOISE * _ar1(traffic_rng, tl.n, PHI_TRAFFIC))
    lam = expected * day_factor[tl.day] * noise * traffic_mult
    sessions = traffic_rng.poisson(lam * bucket_seconds / 60.0)
    load = lam / profile["peak"]
    common = _ar1(np.random.default_rng(streams[1]), tl.n, PHI_COMMON)
    series = {}
    for metric_id, cfg in METRICS.items():
        rng = np.random.default_rng(streams[1 + metric_id])
        series[metric_id] = _metric_trace(cfg, profile["level"][metric_id], rng, sessions, load,
                                          common, tl)
    return {"expected": expected, "series": series}


def _metric_trace(cfg, level, rng, sessions, load, common, tl):
    rho = cfg["rho"]
    noise = rho * common + math.sqrt(1.0 - rho * rho) * _ar1(rng, tl.n, PHI_OWN)
    z = rng.standard_normal(tl.n)
    n = rng.binomial(sessions, cfg["coverage"])
    base = level * (1.0 + cfg["alpha"] * (load - 0.5)) * (1.0 + cfg["trend"] * tl.frac)
    sigma = cfg["sigma"]
    level_t = base * np.exp(sigma * noise - sigma * sigma / 2.0)
    safe_n = np.maximum(n, 1)
    if cfg["kind"] == "latency":
        value = level_t * np.exp(cfg["sample"] * z / np.sqrt(safe_n))
    elif cfg["kind"] == "rate":
        level_t = np.clip(level_t, 0.0, 1.0)
        value = rng.binomial(n, level_t) / safe_n
    else:
        value = rng.poisson(n * level_t) / safe_n
    return {"n": n, "value": value, "base": base, "level": level_t, "z": z,
            "clean": value.copy(), "n_clean": n.copy()}


# --- Agenda estratificada (design §5) --------------------------------------

class _Scheduler:
    """Ubica eventos sin solapes, con gap mínimo y sin cruzar el corte."""

    def __init__(self, rng, expected, tl, bucket_seconds):
        self.rng = rng
        self.tl = tl
        self.bucket_seconds = bucket_seconds
        self.gap = round(MIN_GAP_MINUTES * 60 / bucket_seconds)  # puede ser 0
        self.exp_n = {
            (app, metric_id): expected[app] * cfg["coverage"] * bucket_seconds / 60.0
            for app in range(len(expected)) for metric_id, cfg in METRICS.items()
        }
        self.busy = {key: np.zeros(tl.n, dtype=bool) for key in self.exp_n}
        self.peak = (tl.dow < 5) & (tl.hours >= PEAK_HOURS[0]) & (tl.hours < PEAK_HOURS[1])
        self.ranges = {"train": (0, tl.boundary), "validation": (tl.boundary, tl.n)}

    def events_per_combo(self, split):
        """Eventos por (tipo, severidad) para ~CONTAMINATION_TARGET de filas anómalas."""
        lo, hi = self.ranges[split]
        rows = sum(float(np.sum(1.0 - np.exp(-n[lo:hi]))) for n in self.exp_n.values())
        set_rows = sum(sum(self.duration_range(DURATIONS[t])) / 2.0
                       * (3.5 if t == "correlated_incident" else 1.0) for t in ANOMALY_TYPES)
        return max(MIN_PER_COMBO, round(CONTAMINATION_TARGET * rows / (3 * set_rows)))

    def duration_range(self, minutes):
        """Rango (min, max) de una duración en minutos, convertido a buckets."""
        return tuple(_buckets(m, self.bucket_seconds) for m in minutes)

    def draw_length(self, minutes):
        """Largo en buckets sorteado uniforme dentro del rango."""
        low, high = self.duration_range(minutes)
        return int(self.rng.integers(low, high + 1))

    def place(self, targets, length, split, threshold, want_peak, gap=True):
        """Reserva una ventana (con gap si `gap`); devuelve (app, metrics, start)."""
        lo, hi = self.ranges[split]
        for peak_only in ((True, False) if want_peak else (False,)):
            for index in self.rng.permutation(len(targets)).tolist():
                app, metrics = targets[index]
                starts = self._valid_starts(app, metrics, length, lo, hi, threshold)
                if peak_only:
                    starts = starts[self.peak[starts]]
                if starts.size:
                    start = int(self.rng.choice(starts))
                    self.reserve(app, metrics, start, length, self.gap if gap else 0)
                    return app, metrics, start
        raise RuntimeError(
            f"cannot place a {length}-bucket event in {split}: increase --days"
            f" (validated minimum {MIN_DAYS})")

    def _valid_starts(self, app, metrics, length, lo, hi, threshold):
        ok = np.ones(self.tl.n, dtype=bool)
        for metric_id in metrics:
            ok &= ~self.busy[(app, metric_id)] & (self.exp_n[(app, metric_id)] >= threshold)
        bad = np.concatenate(([0], np.cumsum(~ok)))
        starts = np.arange(lo, hi - length + 1)
        return starts[(bad[starts + length] - bad[starts]) == 0]

    def reserve(self, app, metrics, start, length, gap):
        """Marca la ventana (± gap) como ocupada en las series dadas."""
        for metric_id in metrics:
            self.busy[(app, metric_id)][max(0, start - gap):start + length + gap] = True


def _hard_negative(kind, app, start, length, split, effect):
    return {"kind": "hard_negative", "type": kind, "severity": NONE, "app_index": app,
            "metric_type_ids": list(METRICS), "start_index": start, "length": length,
            "split": split, "at_peak": False, "effect": effect}


def _benign_effect(rng, kind, traffic):
    sigmas = {str(m): round(float(rng.uniform(*BENIGN_SIGMAS)), 4) for m in BENIGN_METRICS[kind]}
    return {"traffic": traffic, "value_sigmas": sigmas}


def _schedule_hard_negatives(scheduler, n_apps, bucket_seconds):
    """Mantenimiento diario (hora sorteada) y surges.

    Se reservan sin gap: una anomalía puede caer justo al lado de un benigno.
    """
    tl, rng = scheduler.tl, scheduler.rng
    events = []
    length = max(1, math.ceil(MAINTENANCE_SECONDS / bucket_seconds))
    for day in range(int(tl.day.max()) + 1):
        for app in range(n_apps):
            offset = int(rng.integers(MAINTENANCE_START[0], MAINTENANCE_START[1] + 1))
            start = (day * 86400 + offset) // bucket_seconds
            if start + length > tl.n or start < tl.boundary < start + length:
                continue
            split = "train" if start < tl.boundary else "validation"
            scheduler.reserve(app, METRICS, start, length, 0)
            events.append(_hard_negative("benign_maintenance", app, start, length, split,
                                         _benign_effect(rng, "benign_maintenance",
                                                        MAINTENANCE_TRAFFIC)))
    for split in SPLITS:
        lo, hi = scheduler.ranges[split]
        split_days = (hi - lo) * bucket_seconds / 86400.0
        for _ in range(max(1, round(n_apps * split_days / SURGE_DAYS_PER_EVENT))):
            length = scheduler.draw_length(SURGE_DURATION)
            targets = [(app, tuple(METRICS)) for app in range(n_apps)]
            app, _, start = scheduler.place(targets, length, split, MIN_EXPECTED_SESSIONS, True,
                                            gap=False)
            multiplier = round(float(rng.uniform(*SURGE_MULTIPLIER)), 4)
            events.append(_hard_negative("benign_traffic_surge", app, start, length, split,
                                         _benign_effect(rng, "benign_traffic_surge",
                                                        multiplier)))
    return events


def _benign_shape(event):
    """Surge: campana; mantenimiento: escalón."""
    if event["type"] == "benign_traffic_surge":
        return np.sin(np.pi * (np.arange(event["length"]) + 0.5) / event["length"])
    return np.ones(event["length"])


def _traffic_multiplier(events, tl):
    """Multiplicador de tráfico (sesiones) que producen los hard negatives de una app."""
    traffic = np.ones(tl.n)
    for event in events:
        if event["kind"] == "hard_negative":
            window = slice(event["start_index"], event["start_index"] + event["length"])
            traffic[window] *= 1.0 + (event["effect"]["traffic"] - 1.0) * _benign_shape(event)
    return traffic


def _magnitude(rng, anomaly_type, severity):
    low, high = (DROPOUT_BANDS if anomaly_type == "dropout" else SEVERITY_BANDS)[severity]
    return min(round(float(rng.uniform(low, high)), 4), round(high - 1e-4, 4))


def _schedule_anomalies(scheduler, n_apps):
    """Estratifica: `count` eventos por (tipo, severidad) en cada split."""
    events = []
    for split in ("validation", "train"):  # validation primero: es la más chica
        count = scheduler.events_per_combo(split)
        for anomaly_type in PLACEMENT_ORDER:
            for severity in SEVERITIES:
                for _ in range(count):
                    want_peak = len(events) % PEAK_EVERY == 0
                    events.append(_place_anomaly(scheduler, n_apps, anomaly_type, severity,
                                                 split, want_peak))
    return events


def _place_anomaly(scheduler, n_apps, anomaly_type, severity, split, want_peak):
    rng = scheduler.rng
    if anomaly_type == "correlated_incident":
        extra = (CORRELATED_EXTRA_METRIC,) if rng.random() < 0.5 else ()
        targets = [(app, LATENCY_IDS + extra) for app in range(n_apps)]
    else:
        targets = [(app, (m,)) for app in range(n_apps) for m in METRICS]
    threshold = MIN_DROPOUT_SESSIONS if anomaly_type == "dropout" else MIN_EXPECTED_SESSIONS
    length = scheduler.draw_length(DURATIONS[anomaly_type])
    app, metrics, start = scheduler.place(targets, length, split, threshold, want_peak)
    return {
        "kind": "anomaly", "type": anomaly_type, "severity": severity, "app_index": app,
        "metric_type_ids": list(metrics), "start_index": start, "length": length,
        "split": split, "at_peak": bool(scheduler.peak[start]),
        "magnitude": {str(m): _magnitude(rng, anomaly_type, severity) for m in metrics},
    }


# --- Inyección (design §3) -------------------------------------------------

def _local_std(trace, start, length):
    """Std local del residuo (serie limpia − base estacional) en ±NEIGHBORHOOD buckets."""
    lo = max(0, start - NEIGHBORHOOD)
    hi = min(trace["clean"].size, start + length + NEIGHBORHOOD)
    residual = trace["clean"] - trace["base"]
    local = residual[lo:hi][trace["n_clean"][lo:hi] > 0]
    if local.size < 10:
        local = residual[trace["n_clean"] > 0]
    return max(float(np.std(local)), 1e-6)


def _inject(event, series, labels, rng):
    """Aplica la anomalía y etiqueta solo las filas existentes que cambiaron de verdad."""
    start, length = event["start_index"], event["length"]
    window = slice(start, start + length)
    for metric_id in event["metric_type_ids"]:
        trace, cfg = series[metric_id], METRICS[metric_id]
        k = event["magnitude"][str(metric_id)]
        sigma = _local_std(trace, start, length)
        if event["type"] == "drift":
            trace["value"][window] += k * sigma * np.arange(1, length + 1) / length
        elif event["type"] == "variance_burst":
            noise = rng.standard_normal(length)
            if cfg["kind"] != "latency":  # tasa/conteo pegados a 0: el ruido negativo se perdería
                noise = np.abs(noise)
            trace["value"][window] += sigma * math.sqrt(k * k - 1.0) * noise
        elif event["type"] == "dropout":
            _dropout(trace, cfg, window, k, rng)
        else:  # spike, level_shift, correlated_incident: escalón
            trace["value"][window] += k * sigma
        if cfg["kind"] == "latency":
            floor = LATENCY_FLOOR * trace["base"][window]
            trace["value"][window] = np.maximum(trace["value"][window], floor)
        kind = cfg["kind"]
        changed = (trace["n"][window] != trace["n_clean"][window]) | (
            _emitted(trace["value"][window], kind) != _emitted(trace["clean"][window], kind))
        idx = start + np.flatnonzero(changed & (trace["n_clean"][window] > 0))
        lab = labels[metric_id]
        lab["is_anomaly"][idx] = 1
        lab["anomaly_type"][idx] = event["type"]
        lab["severity"][idx] = event["severity"]
        lab["event_id"][idx] = event["event_id"]


def _emitted(values, kind):
    """Valor tal como se exporta: recortado a su rango y redondeado a 4 decimales."""
    return np.round(np.clip(values, 0.0, 1.0 if kind == "rate" else math.inf), 4)


def _dropout(trace, cfg, window, fraction, rng):
    """Cae la cobertura de sesiones; el valor se re-agrega con menos sesiones.

    Un bucket sin sesiones sigue vacío: la anomalía no crea filas.
    """
    old = trace["n"][window]
    new = np.where(old > 0, np.maximum(1, np.round(old * (1.0 - fraction))), 0).astype(old.dtype)
    safe_old, safe_new = np.maximum(old, 1), np.maximum(new, 1)
    if cfg["kind"] == "latency":
        shrink = 1.0 / np.sqrt(safe_new) - 1.0 / np.sqrt(safe_old)
        trace["value"][window] *= np.exp(cfg["sample"] * trace["z"][window] * shrink)
    elif cfg["kind"] == "rate":
        trace["value"][window] = rng.binomial(new, trace["level"][window]) / safe_new
    else:
        trace["value"][window] = rng.poisson(new * trace["level"][window]) / safe_new
    trace["n"][window] = new


def _apply_hard_negative(event, series, labels):
    """Efecto benigno en `value` (k sigmas locales) + etiqueta; queda en la serie limpia."""
    window = slice(event["start_index"], event["start_index"] + event["length"])
    for metric_id, k in event["effect"]["value_sigmas"].items():
        trace = series[int(metric_id)]
        sigma = _local_std(trace, event["start_index"], event["length"])
        trace["value"][window] += k * sigma * _benign_shape(event)
        trace["clean"][window] = trace["value"][window]
    for metric_id in event["metric_type_ids"]:
        labels[metric_id]["hard_negative"][window] = 1
        labels[metric_id]["anomaly_type"][window] = event["type"]
        labels[metric_id]["event_id"][window] = event["event_id"]


def _empty_labels(n):
    return {
        "is_anomaly": np.zeros(n, dtype=np.int8), "hard_negative": np.zeros(n, dtype=np.int8),
        "anomaly_type": np.full(n, NONE, dtype=object), "severity": np.full(n, NONE, dtype=object),
        "event_id": np.full(n, "", dtype=object),
    }


def generate(seed=DEFAULT_SEED, days=DEFAULT_DAYS, bucket_seconds=DEFAULT_BUCKET_SECONDS,
             apps=DEFAULT_APPS):
    """Genera el dataset etiquetado en memoria (determinista dada la seed).

    Etapas: agenda (eventos) -> traza base por app -> inyección -> filas.
    """
    _validate_params(days, bucket_seconds, apps)
    tl = _timeline(days, bucket_seconds)
    schedule_ss, series_ss = np.random.SeedSequence(seed).spawn(2)
    place_ss, inject_ss = schedule_ss.spawn(2)
    profiles = APP_PROFILES[:apps]
    scheduler = _Scheduler(np.random.default_rng(place_ss),
                           [_expected_traffic(p, tl) for p in profiles], tl, bucket_seconds)
    events = _schedule_hard_negatives(scheduler, apps, bucket_seconds)
    events = _finalize_events(events + _schedule_anomalies(scheduler, apps), profiles, tl)
    # Un stream por perfil, fijo aunque apps < 3: la serie de una app no depende de --apps.
    app_streams = series_ss.spawn(len(APP_PROFILES))
    inject_rng = np.random.default_rng(inject_ss)
    rows = []
    for index, profile in enumerate(profiles):
        rows.extend(_app_rows(profile, app_streams[index].spawn(STREAMS_PER_APP), events,
                              inject_rng, tl, bucket_seconds))
    params = {"seed": seed, "days": days, "bucket_seconds": bucket_seconds, "apps": apps,
              "start": tl.stamps[0], "train_fraction": TRAIN_FRACTION,
              "boundary": tl.stamps[tl.boundary], "boundary_index": tl.boundary}
    return Dataset(rows=rows, events=events, params=params)


def _validate_params(days, bucket_seconds, apps):
    if bucket_seconds < MIN_BUCKET_SECONDS:
        raise ValueError(f"bucket_seconds must be >= {MIN_BUCKET_SECONDS}")
    if not 1 <= apps <= len(APP_PROFILES):
        raise ValueError(f"apps must be between 1 and {len(APP_PROFILES)}")
    if days < MIN_DAYS:
        raise ValueError(f"days must be >= {MIN_DAYS}: a shorter window cannot fit every"
                         " (type, severity) event in both splits")


def _app_rows(profile, streams, events, inject_rng, tl, bucket_seconds):
    """Traza base de una app, eventos aplicados y filas emitidas."""
    own = [event for event in events if event["app_id"] == profile["app_id"]]
    trace = _app_trace(profile, streams, tl, bucket_seconds, _traffic_multiplier(own, tl))
    labels = {metric_id: _empty_labels(tl.n) for metric_id in METRICS}
    for event in own:  # primero los benignos: forman parte de la serie "limpia"
        if event["kind"] == "hard_negative":
            _apply_hard_negative(event, trace["series"], labels)
    for event in own:
        if event["kind"] == "anomaly":
            _inject(event, trace["series"], labels, inject_rng)
    rows = []
    for metric_id, series in trace["series"].items():
        rows.extend(_series_rows(profile["app_id"], metric_id, series, labels[metric_id],
                                 tl, bucket_seconds))
    return rows


def _finalize_events(events, profiles, tl):
    """Orden temporal estable, ids legibles y timestamps de inicio/fin."""
    events.sort(key=lambda e: (e["start_index"], e["app_index"], e["metric_type_ids"]))
    counters = {"anomaly": 0, "hard_negative": 0}
    for event in events:
        counters[event["kind"]] += 1
        prefix = "A" if event["kind"] == "anomaly" else "H"
        event["event_id"] = f"{prefix}-{counters[event['kind']]:04d}"
        event["app_id"] = profiles[event.pop("app_index")]["app_id"]
        event["start"] = tl.stamps[event["start_index"]]
        event["end"] = tl.stamps[event["start_index"] + event["length"] - 1]
    return events


def _series_rows(app_id, metric_id, series, labels, tl, bucket_seconds):
    values = _emitted(series["value"], METRICS[metric_id]["kind"])
    rows = []
    for i in np.flatnonzero(series["n"] > 0).tolist():
        rows.append({
            "application_id": app_id, "metric_type_id": metric_id,
            "timestamp": tl.stamps[i], "bucket_seconds": bucket_seconds,
            "value": float(values[i]), "session_count": int(series["n"][i]),
            "is_anomaly": int(labels["is_anomaly"][i]),
            "anomaly_type": labels["anomaly_type"][i], "severity": labels["severity"][i],
            "event_id": labels["event_id"][i], "hard_negative": int(labels["hard_negative"][i]),
            "split": "train" if i < tl.boundary else "validation",
        })
    return rows


def write_dataset(dataset, out_dir):
    """Escribe CSV + manifest.json en `out_dir`; devuelve sus rutas."""
    out = pathlib.Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    csv_path = out / CSV_NAME
    with open(csv_path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh, lineterminator="\n")
        writer.writerow(COLUMNS)
        for row in dataset.rows:
            writer.writerow([_fmt(key, row[key]) for key in COLUMNS])
    manifest_path = out / MANIFEST_NAME
    manifest = _manifest(dataset, _sha256(csv_path))
    with open(manifest_path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(manifest, fh, indent=2, sort_keys=True)
        fh.write("\n")
    return csv_path, manifest_path


def _fmt(key, value):
    return f"{value:.4f}" if key == "value" else value


def _sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _count_by_split(rows, column):
    return {split: sum(r[column] for r in rows if r["split"] == split) for split in SPLITS}


def _manifest(dataset, csv_sha256):
    rows = dataset.rows
    by_split = Counter(row["split"] for row in rows)
    anomalous = _count_by_split(rows, "is_anomaly")
    return {
        "generator_version": GENERATOR_VERSION,
        "params": dataset.params,
        "numpy_version": np.__version__,
        "python_version": platform.python_version(),
        "csv_file": CSV_NAME,
        "csv_sha256": csv_sha256,
        "schema": [{"name": n, "type": t, "description": d} for n, t, d in SCHEMA],
        "row_counts": {
            "total": len(rows),
            "by_split": {split: by_split[split] for split in SPLITS},
            "anomalous_by_split": anomalous,
            "hard_negative_by_split": _count_by_split(rows, "hard_negative"),
            "by_anomaly_type": dict(sorted(Counter(r["anomaly_type"] for r in rows).items())),
            "by_severity": dict(sorted(Counter(r["severity"] for r in rows).items())),
        },
        "contamination_by_split": {
            split: round(anomalous[split] / max(by_split[split], 1), 4) for split in SPLITS},
        "value_ranges": _value_ranges(rows),
        "events": dataset.events,
    }


def _value_ranges(rows):
    ranges = {}
    for metric_id, cfg in METRICS.items():
        values = np.array([r["value"] for r in rows if r["metric_type_id"] == metric_id])
        if not values.size:
            continue
        ranges[str(metric_id)] = {
            "name": cfg["name"], "unit": UNITS[metric_id],
            "min": float(values.min()), "max": float(values.max()),
            "mean": round(float(values.mean()), 4),
            "p50": round(float(np.percentile(values, 50)), 4),
            "p99": round(float(np.percentile(values, 99)), 4),
        }
    return ranges


class RowLabel(NamedTuple):
    """Etiquetas de una fila, alineadas por índice con su `MetricBatchInput`."""
    is_anomaly: bool
    anomaly_type: str
    severity: str
    event_id: str
    hard_negative: bool


class LabeledSplit(NamedTuple):
    """Filas del contrato M4 validadas + etiquetas, en el mismo orden."""
    rows: list
    labels: list


def load_labeled_dataset(path):
    """Lee el CSV exportado y devuelve `{split: LabeledSplit}` validado contra M4.

    Acepta la ruta del CSV o su carpeta. Si hay un `manifest.json` al lado,
    verifica el sha256 del CSV (ValueError si no coincide). Solo stdlib + el
    contrato `src.ml.schemas` (sin ingesta, sin DB, sin HTTP).
    """
    # Import diferido: generar el dataset no requiere pydantic ni el paquete src.
    from src.ml.schemas import MetricBatchInput  # pylint: disable=import-outside-toplevel

    csv_path = pathlib.Path(path)
    if csv_path.is_dir():
        csv_path = csv_path / CSV_NAME
    manifest_path = csv_path.with_name(MANIFEST_NAME)
    if manifest_path.exists():
        expected = json.loads(manifest_path.read_text(encoding="utf-8"))["csv_sha256"]
        if _sha256(csv_path) != expected:
            raise ValueError(f"sha256 mismatch for {csv_path} (see {MANIFEST_NAME})")
    data = {split: LabeledSplit(rows=[], labels=[]) for split in SPLITS}
    with open(csv_path, encoding="utf-8", newline="") as fh:
        for raw in csv.DictReader(fh):
            part = data[raw["split"]]
            part.rows.append(MetricBatchInput(
                application_id=raw["application_id"],
                metric_type_id=int(raw["metric_type_id"]),
                timestamp=raw["timestamp"],
                bucket_seconds=int(raw["bucket_seconds"]),
                value=float(raw["value"]),
                session_count=int(raw["session_count"]),
            ))
            part.labels.append(RowLabel(
                is_anomaly=raw["is_anomaly"] == "1", anomaly_type=raw["anomaly_type"],
                severity=raw["severity"], event_id=raw["event_id"],
                hard_negative=raw["hard_negative"] == "1",
            ))
    return data


def main(argv=None):
    """CLI: genera y exporta el dataset."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--days", type=int, default=DEFAULT_DAYS)
    parser.add_argument("--bucket-seconds", type=int, default=DEFAULT_BUCKET_SECONDS)
    parser.add_argument("--apps", type=int, default=DEFAULT_APPS)
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR)
    args = parser.parse_args(argv)
    try:
        dataset = generate(args.seed, args.days, args.bucket_seconds, args.apps)
    except (ValueError, RuntimeError) as exc:
        parser.error(str(exc))  # exit 2 con mensaje claro, sin traceback
    csv_path, manifest_path = write_dataset(dataset, args.out_dir)
    print(f"{len(dataset.rows)} rows -> {csv_path} (+ {manifest_path.name})")


if __name__ == "__main__":
    main()
