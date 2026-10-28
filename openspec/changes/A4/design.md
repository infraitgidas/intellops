# Design: A.4 — Generador sintético etiquetado

> **Enfoque (KISS)**: un módulo (`ml/data/generate_labeled_dataset.py`) con tres etapas puras — traza base → agenda de eventos → inyección — más export (CSV + manifest) y lector. numpy + stdlib, Python 3.11. Sin `src.api`, sin DB, sin HTTP. Fuente: `proposal.md` y decisiones con el usuario (issue #66).

## 1. Flujo

```
seed ─> SeedSequence ─┬─ schedule stream ─> agenda (eventos + hard negatives)
                      └─ app[a] ─┬─ traffic  ─> λ(t), sesiones de la app
                                 ├─ common   ─> factor latente compartido
                                 └─ metric m ─> valor por bucket
traza limpia ─> inyección de anomalías ─> filas (sesiones = 0 se omiten) ─> CSV + manifest
```

Streams: `SeedSequence(seed).spawn(2)` → `[agenda, series]`; `series.spawn(3)` (una por perfil, fija aunque `--apps < 3`) y cada app `spawn(7)` → `[traffic, common, m1..m5]`. Cada inyección usa su propio generador derivado de la agenda: agregar eventos no perturba las series base.

## 2. Modelo generativo

Inicio fijo `2026-08-03T00:00:00Z` (lunes), alineado a `bucket_seconds`. Horas en UTC.

| Componente | Modelo |
|---|---|
| Tráfico λ(t) (sesiones/min) | `peak · diario(h) · semanal(d) · tendencia(+5 %) · día~LogN(0, 0.08) · exp(0.1·AR(0.95))` |
| Diario | `floor + (1-floor)·(0.55·diurno + 0.45·laboral)`; diurno = coseno con mínimo 04:00 y máximo 16:00; laboral = gaussiana centrada 13:00 (σ 3.5 h), atenuada el fin de semana |
| Sesiones | app: `N ~ Poisson(λ·b/60)`; métrica: `n ~ Binomial(N, cobertura_m)` |
| Carga | `load = λ/peak`; sube levemente las latencias (`× (1 + α_m·(load − 0.5))`) |
| Ruido | `e = ρ_m·C + √(1−ρ_m²)·O_m`, con `C` (φ 0.9) compartido por app y `O_m` (φ 0.8) propio; AR(1) de varianza unitaria |
| Latencias (1-3) | `v = base · exp(σ_m·e − σ_m²/2 + s_m·z/√n)`: sesgo a derecha y varianza que crece con el nivel y con pocas sesiones |
| Tasa JS (4) | `p = base·exp(σ_m·e − σ_m²/2)`; `v = Binomial(n, p)/n` ∈ [0, 1] |
| Rage (5) | `r = base·exp(σ_m·e − σ_m²/2)`; `v = Poisson(n·r)/n` (clics por sesión) |
| Huecos | si `n = 0` el bucket **no se emite** (igual que el read path) |
| Redondeo | `value` a 4 decimales; `≥ 0`; tasa `≤ 1` |

### Perfiles de app (`app_id` del generador existente)

| # | Perfil | Peak ses/min | floor noche | Sáb / Dom | TTFB | FCP | XHR | JS rate | Rage |
|---|---|---|---|---|---|---|---|---|---|
| 0 | checkout (alto tráfico) | 90 | 0.15 | 0.85 / 0.80 | 280 | 1600 | 220 | 0.012 | 0.35 |
| 1 | backoffice (horario laboral) | 25 | 0.05 | 0.25 / 0.15 | 450 | 2200 | 380 | 0.025 | 0.60 |
| 2 | portal (bajo tráfico) | 6 | 0.10 | 0.60 / 0.55 | 350 | 2600 | 300 | 0.020 | 0.30 |

### Parámetros por métrica

| id | Métrica | σ | s | α | ρ | Cobertura | Tendencia |
|---|---|---|---|---|---|---|---|
| 1 | TTFB (ms) | 0.12 | 0.6 | 0.15 | 0.6 | 1.00 | +3 % |
| 2 | FCP (ms) | 0.10 | 0.5 | 0.10 | 0.6 | 0.95 | +2 % |
| 3 | XHR_LATENCY (ms) | 0.15 | 0.8 | 0.25 | 0.6 | 0.70 | +4 % |
| 4 | JS_EXCEPTION_RATE | 0.20 | — | 0.10 | 0.2 | 1.00 | 0 |
| 5 | RAGE_CLICK (/sesión) | 0.20 | — | 0.10 | 0.2 | 1.00 | 0 |

## 3. Catálogo de anomalías

Magnitud `k` en sigmas del desvío **local** `σ_loc` = std del residuo (serie limpia − base estacional) en un vecindario de ±60 buckets alrededor del evento. Todas son degradaciones (hacia arriba) salvo `dropout`.

| Tipo | Duración (buckets) | Forma |
|---|---|---|
| `spike` | 1-3 | `v + k·σ_loc` |
| `level_shift` | 20-60 | escalón sostenido `v + k·σ_loc` |
| `drift` | 30-90 | rampa lineal 0 → `k·σ_loc` (la etiqueta cubre toda la rampa) |
| `variance_burst` | 15-45 | `v + σ_loc·√(k²−1)·w`, `w ~ N(0,1)`: desvío ≈ `k·σ_loc`, media igual |
| `dropout` | 5-20 | `n' = max(1, round(n·(1 − f)))`; el valor se re-agrega con `n'` (más ruidoso) |
| `correlated_incident` | 10-40 | escalón en TTFB+FCP+XHR (+ JS rate con prob. 0.5) de una app; un solo `event_id`; `k` por métrica |

| Severidad | `k` (sigmas) | `f` de `dropout` (fracción perdida) |
|---|---|---|
| `low` | 3-4 (sutil: el ruido con cola pesada también llega ahí) | 0.40-0.60 |
| `medium` | 4-6 | 0.60-0.80 |
| `high` | 6-9 | 0.80-0.95 |

`dropout` usa fracción y no sigmas (decisión de apply): el desvío local de `session_count` lo domina Poisson + ruido de tráfico, y 6-9 σ solo era alcanzable en el pico de la app de más tráfico.

## 4. Hard negatives (`is_anomaly=0`, `hard_negative=1`)

| Patrón (`anomaly_type`) | Forma | Por qué engaña |
|---|---|---|
| `benign_traffic_surge` | campaña: λ × 1.8-2.6 en campana, 30-90 buckets, horario diurno; todas las métricas de la app | sube `session_count` y, vía carga, las latencias ~1-2 σ |
| `benign_maintenance` | todos los días 22:00 UTC, 15 min: sesiones × 0.6, TTFB × 1.25, XHR × 1.35 | recurrente (aprendible), parece `dropout` + `level_shift` |

## 5. Agenda estratificada

- Corte **global** `boundary = floor(0.8·n_buckets)`; `split` = `train` antes, `validation` desde el corte.
- Eventos por `(tipo, severidad, split)`: `max(1, round(0.02·filas_split / (3·Σ largo_medio_tipo)))` → contaminación objetivo ~2 % (1-3 % con los defaults).
- Orden: mantenimiento (fijo) → surges → anomalías (validation primero, más largas primero).
- Restricciones por serie: sin solape, gap mínimo de 30 buckets, el evento no cruza el corte, tráfico esperado ≥ 3 sesiones/bucket en toda la ventana (≥ 20 para `dropout`) (en la ventana de la anomalía `n ≥ 1` se fuerza para que la fila exista).
- 1 de cada 3 anomalías se ubica en horario pico (lun-vie 10-17 UTC): casos difíciles.
- Muestreo por rechazo; si no entra, `RuntimeError` explícito (ventana demasiado chica).

## 6. Salida

`ml/data/synthetic/labeled_dataset.csv` (UTF-8, `\n`, orden app → métrica → timestamp):

| Columna | Tipo | Nota |
|---|---|---|
| `application_id`, `metric_type_id`, `timestamp`, `bucket_seconds`, `value`, `session_count` | contrato M4 | `timestamp` ISO-8601 `Z`, alineado |
| `is_anomaly` | 0/1 | |
| `anomaly_type` | str | tipo, patrón benigno o `none` |
| `severity` | str | `low`/`medium`/`high` o `none` |
| `event_id` | str | `A-0001`, `H-0001` o vacío |
| `hard_negative` | 0/1 | |
| `split` | str | `train` / `validation` |

`manifest.json`: versión del generador, seed, parámetros, versión de numpy/Python, schema, conteos (split, tipo, severidad), contaminación, rangos por métrica, lista de eventos (con `k` efectivo), sha256 del CSV.

Lector: `load_labeled_dataset(csv_path)` → `{split: LabeledSplit(rows: list[MetricBatchInput], labels: list[RowLabel])}`; importa `src.ml.schemas` de forma diferida y verifica el sha256 si hay `manifest.json` al lado.

## 7. Decisiones

| Tema | Opciones | Decisión |
|---|---|---|
| Formato | CSV / JSON / Parquet | **CSV stdlib**: liviano, diffeable, sin pyarrow |
| Split | aleatorio / temporal | **temporal 80/20** con corte global: sin fuga de futuro |
| Severidad | absoluta / sigmas | **sigmas locales**: comparable entre métricas y apps |
| Huecos | rellenar con 0 / omitir | **omitir**: igual que el read path real |
| Booleanos | `true/false` / `0/1` | **0/1**: neutro para cualquier lector |

## 8. Limitaciones (honestas)

- Las anomalías tienen la forma que este generador les da: un modelo puede aprender el generador. No reportar F1 "de producción" con este dataset.
- Supuestos: ruido AR(1) gaussiano/lognormal, estacionalidad fija, sin eventos de calendario reales, sin deploys reales, sin interacción entre apps.
- Revalidar con datos reales (R.2) cuando existan.
- El sha256 es reproducible con la misma versión de numpy y plataforma; numpy no garantiza el stream de `Generator` entre versiones.
