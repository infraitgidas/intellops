# Dataset sintético etiquetado (A.4)

`generate_labeled_dataset.py` genera, con seed fija, series RUM **sintéticas** con el contrato M4 (`MetricBatchInput`), anomalías inyectadas y etiquetadas por tipo y severidad, *hard negatives* y un split temporal train/validation. Es la entrada de B.6 (baseline estadístico vs Isolation Forest) mientras no haya datos reales del laboratorio.

> **Es sintético.** Las anomalías tienen la forma que este generador les da. Sirve para comparar modelos entre sí y depurar el pipeline, **no** para reportar un F1 "de producción". Ver [Limitaciones](#limitaciones).

## Quick path

```bash
# 1. Generar (≈ 2 s, ≈ 25 MB; no se commitea: ml/data/synthetic/ está en .gitignore)
.venv/Scripts/python ml/data/generate_labeled_dataset.py

# 2. Verificar que es el dataset esperado
sha256sum ml/data/synthetic/labeled_dataset.csv   # comparar con la tabla de abajo

# 3. Correr los tests del generador
PYTHONPATH=. .venv/Scripts/python -m pytest tests/test_labeled_dataset.py -m unit
```

| CLI | Default | Regla |
|---|---|---|
| `--seed` | `66` | entero |
| `--days` | `14` | ≥ 1 (con ventanas chicas puede fallar la agenda: error explícito) |
| `--bucket-seconds` | `60` | ≥ 60; duraciones y gaps se miden en buckets (con 300 s usar ≥ 14 días) |
| `--apps` | `3` | 1 a 3 (perfiles fijos) |
| `--out-dir` | `ml/data/synthetic` | carpeta de salida |

## Corrida por defecto (referencia)

| Dato | Valor |
|---|---|
| Comando | `python ml/data/generate_labeled_dataset.py` (seed 66, 14 días, 60 s, 3 apps) |
| Filas | 264 670 (train 214 909, validation 49 761) |
| Filas anómalas | 4 876 (train 4 083 = 1.90 %, validation 793 = 1.59 %; total 1.84 %) |
| Filas hard negative | 7 196 (train 6 018, validation 1 178) |
| Eventos | 126 anomalías (108 train, 18 validation; 74 en horario pico) + 56 hard negatives |
| Tamaño | CSV 25 589 258 bytes; `manifest.json` 90 913 bytes |
| Tiempo | ≈ 1.9 s generar; ≈ 3 s `load_labeled_dataset` (validación pydantic de todas las filas) |
| sha256 del CSV | `2ce13c8ee9869279b777d668351c3e1716c9b58520b561613803fb8949f0e625` |
| Entorno | numpy 2.5.3, Python 3.13.9, Windows 11 |

El hash es reproducible con la misma versión de numpy. numpy no garantiza el mismo stream de `Generator` entre versiones, y las funciones matemáticas pueden variar en el último bit entre plataformas: si el hash no coincide, mirá primero `numpy_version` en el manifest.

## Formato

Dos archivos en `--out-dir`:

- `labeled_dataset.csv`: UTF-8, separador `,`, fin de línea `\n`, una fila por bucket y serie, ordenado por app → métrica → timestamp.
- `manifest.json`: seed, parámetros, versiones de numpy y Python, schema, conteos (split, tipo, severidad), contaminación por split, rangos por métrica, lista completa de eventos y `csv_sha256`.

### Columnas

| Columna | Tipo | Rango / valores |
|---|---|---|
| `application_id` | UUID4 | uno por perfil de app |
| `metric_type_id` | int | 1 TTFB, 2 FCP, 3 XHR_LATENCY, 4 JS_EXCEPTION_RATE, 5 RAGE_CLICK |
| `timestamp` | ISO-8601 UTC (`Z`) | inicio del bucket, alineado a `bucket_seconds` (epoch) |
| `bucket_seconds` | int | ≥ 60 |
| `value` | float (4 decimales) | ≥ 0; JS_EXCEPTION_RATE ≤ 1 |
| `session_count` | int | ≥ 1 (los buckets sin sesiones **no se emiten**, como en el read path) |
| `is_anomaly` | 0/1 | 1 = bucket dentro de una anomalía |
| `anomaly_type` | str | tipo de anomalía, patrón benigno o `none` |
| `severity` | str | `low`, `medium`, `high` o `none` |
| `event_id` | str | `A-NNNN` anomalía, `H-NNNN` hard negative, vacío si normal |
| `hard_negative` | 0/1 | 1 = evento benigno que parece anómalo |
| `split` | str | `train` o `validation` |

Las seis primeras columnas son exactamente el contrato M4: cada fila valida como `MetricBatchInput` (está testeado).

### Rangos por métrica (corrida por defecto, todas las filas)

| id | Métrica | Unidad | min | p50 | p99 | max |
|---|---|---|---|---|---|---|
| 1 | TTFB | ms | 13.49 | 334.83 | 1 070.03 | 6 345.18 |
| 2 | FCP | ms | 116.13 | 1 946.34 | 5 769.04 | 16 392.46 |
| 3 | XHR_LATENCY | ms | 11.96 | 272.02 | 1 372.30 | 6 207.19 |
| 4 | JS_EXCEPTION_RATE | proporción | 0 | 0 | 0.5 | 1 |
| 5 | RAGE_CLICK | clics/sesión | 0 | 0.36 | 2 | 5 |

Las colas largas son esperables: buckets con 1-2 sesiones (app de bajo tráfico, madrugada) son muy ruidosos.

## Modelo generativo (resumen)

| Rasgo | Cómo se genera |
|---|---|
| 3 perfiles de app | checkout (90 ses/min pico), backoffice (25, casi nada el fin de semana), portal (6, con huecos de noche) |
| Estacionalidad | diaria (mínimo 04:00, pico laboral 10-17 UTC) y semanal (caída el fin de semana); tendencia +5 % de tráfico |
| Sesiones | `Poisson(λ)` por app, `Binomial` por métrica según cobertura (XHR 70 %) |
| Latencias | lognormales (sesgo a derecha), varianza que crece con el nivel y con pocas sesiones |
| Tasa y rage | binomial y Poisson sobre las sesiones del bucket |
| Ruido | AR(1) autocorrelado; un factor latente compartido por app correlaciona las tres latencias |
| Carga | más tráfico ⇒ latencias levemente más altas |

Detalle y parámetros: `openspec/changes/A4/design.md` §2.

## Anomalías

| `anomaly_type` | Duración (buckets) | Forma |
|---|---|---|
| `spike` | 1-3 | salto puntual `+k·σ` |
| `level_shift` | 20-60 | escalón sostenido |
| `drift` | 30-90 | rampa lineal hasta `k·σ` (toda la rampa queda etiquetada) |
| `variance_burst` | 15-45 | desvío × `k`, misma media |
| `dropout` | 5-20 | `session_count` cae una fracción; el valor se recalcula con menos sesiones |
| `correlated_incident` | 10-40 | escalón simultáneo en TTFB + FCP + XHR (+ JS rate a veces) de una app, un solo `event_id` |

`σ` es el desvío **local** del residuo de la serie limpia respecto de su base estacional (±60 buckets alrededor del evento). Todas son degradaciones hacia arriba, salvo `dropout`.

| Severidad | `k` (sigmas) | `dropout` (fracción de sesiones perdidas) |
|---|---|---|
| `low` | 3-4 (sutil) | 0.40-0.60 |
| `medium` | 4-6 | 0.60-0.80 |
| `high` | 6-9 | 0.80-0.95 |

La magnitud efectiva de cada evento está en `manifest.json` → `events[].magnitude` (por métrica).

**Chequeo de dificultad (no es un benchmark).** Un z-score robusto ingenuo (mediana/MAD de las 60 filas previas, umbral 3) sobre la corrida por defecto marca el 25 % de las filas `low`, 44 % `medium` y 59 % `high`, con 6.7 % de filas normales marcadas. Los `low` son realmente sutiles. La comparación seria es trabajo de B.6.

## Hard negatives

Eventos benignos que **parecen** anómalos: `is_anomaly=0`, `hard_negative=1`, `event_id` propio, `severity=none`. Sirven para medir la tasa de falsos positivos (KPI del proyecto).

| `anomaly_type` | Qué pasa | Por qué engaña |
|---|---|---|
| `benign_traffic_surge` | campaña: tráfico × 1.8-2.6 en campana durante 30-90 buckets, todas las métricas de la app | suben `session_count` y, por carga, las latencias |
| `benign_maintenance` | todos los días 22:00 UTC, 15 min: sesiones × 0.6, TTFB × 1.25, XHR × 1.35 | recurrente (un modelo estacional lo aprende), pero parece `dropout` + `level_shift`; el z-score ingenuo lo marca el doble que a una fila normal |

## Agenda y split

- **Split temporal**: un único corte global al 80 % de la ventana (`params.boundary` en el manifest; `2026-08-14T04:48:00Z` por defecto). Todo lo anterior es `train`, lo demás `validation`. Nunca aleatorio: así no hay fuga de futuro ni entre series.
- **Estratificación**: cada combinación (tipo, severidad) aparece al menos una vez en cada split; la cantidad se calcula para una contaminación de ~2 % de filas.
- **Restricciones**: sin solapes por serie, gap mínimo de 30 buckets entre eventos, ningún evento cruza el corte, solo donde se esperan ≥ 3 sesiones por bucket (≥ 20 para `dropout`).
- **Casos difíciles**: 1 de cada 3 anomalías se fuerza a horario pico (lun-vie 10-17 UTC); `events[].at_peak` lo indica.
- Con ventanas chicas la contaminación sube (el mínimo por combinación domina): con 3 días y 2 apps, validation queda entre 7 % y 10 % (train ~2 %).

## Cómo lo consume B.6

```python
import importlib.util

spec = importlib.util.spec_from_file_location(
    "generate_labeled_dataset", "ml/data/generate_labeled_dataset.py")
gld = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gld)

data = gld.load_labeled_dataset("ml/data/synthetic")  # verifica el sha256 del manifest
train, validation = data["train"], data["validation"]
# train.rows: list[MetricBatchInput]; train.labels: list[RowLabel] (mismo orden)
y_train = [label.is_anomaly for label in train.labels]
```

- Correr con `PYTHONPATH=.` (el lector importa `src.ml.schemas`). Generar el dataset no lo necesita.
- Sin acoplamiento a la ingesta: el módulo no importa `src.api`, ni usa DB ni HTTP (está testeado).
- Para métricas por evento (recall por evento, falsos positivos por evento) usar `event_id` y `manifest.json` → `events`.
- Para la tasa de falsos positivos sobre casos difíciles, filtrar `hard_negative=1`.

## Limitaciones

- **El modelo puede aprender el generador.** Formas, duraciones y bandas de severidad son decisiones de diseño, no observaciones. No reportar F1, recall o precisión de este dataset como desempeño esperado en producción.
- **Revalidar con datos reales** (R.2) cuando existan; este dataset no reemplaza esa validación.
- Supuestos del modelo: ruido AR(1) gaussiano/lognormal, estacionalidad fija en UTC, sin feriados ni eventos de calendario reales, sin deploys reales, apps independientes entre sí, cobertura de métricas constante.
- Todas las anomalías son degradaciones (hacia arriba), salvo `dropout`; no hay mejoras abruptas.
- Dentro de una anomalía se fuerza `session_count ≥ 1` para que la fila exista (sesgo mínimo: los eventos solo se ubican donde se esperan ≥ 3 sesiones).
- Duraciones y gaps están calibrados para buckets de 60 s.

## Otros archivos de esta carpeta

| Archivo | Qué es |
|---|---|
| `generate_mock_dataset.py`, `rum_mock.json`, `*.png` | dataset mock y gráficos del EDA de ISS-S3-05 (sin etiquetas; no se usa para B.6) |
| `synthetic/` | salida del generador etiquetado (ignorada por git) |
