# Dataset sintético etiquetado (A.4)

`generate_labeled_dataset.py` genera, con seed fija, series RUM **sintéticas** con el contrato M4 (`MetricBatchInput`), anomalías inyectadas y etiquetadas por tipo y severidad, *hard negatives* y un split temporal train/validation. Es la entrada de B.6 (baseline estadístico vs Isolation Forest) mientras no haya datos reales del laboratorio.

> **Es sintético.** Las anomalías tienen la forma que este generador les da. Sirve para comparar modelos entre sí y depurar el pipeline, **no** para reportar un F1 "de producción". Ver [Limitaciones](#limitaciones).

> **Etiquetas, no features.** La etiqueta es solo `is_anomaly`. **Nunca** usar `anomaly_type`, `severity`, `event_id`, `hard_negative` ni `split` como features: delatan la respuesta. Ojo: los hard negatives tienen `anomaly_type` distinto de `none` (`benign_*`) con `is_anomaly=0`; derivar la etiqueta de `anomaly_type != "none"` los convertiría en positivos.

## Quick path

```bash
# 1. Generar (≈ 3.5 s, ≈ 51 MB; no se commitea: ml/data/synthetic/ está en .gitignore)
.venv/Scripts/python ml/data/generate_labeled_dataset.py

# 2. Verificar que es el dataset esperado
sha256sum ml/data/synthetic/labeled_dataset.csv   # comparar con la tabla de abajo

# 3. Correr los tests del generador
PYTHONPATH=. .venv/Scripts/python -m pytest tests/test_labeled_dataset.py -m unit
```

| CLI | Default | Regla |
|---|---|---|
| `--seed` | `66` | entero |
| `--days` | `28` | ≥ 8; con menos sale con código 2 y `days must be >= 8: ...` (sin traceback) |
| `--bucket-seconds` | `60` | ≥ 60; duraciones y gap están en minutos de reloj y se convierten a buckets (mínimo 1) |
| `--apps` | `3` | 1 a 3 (perfiles fijos) |
| `--out-dir` | `ml/data/synthetic` | carpeta de salida |

El mínimo de 8 días está medido (seeds 0-19 × apps 1-3 × buckets 60/300/900/3600/7000 s). Si una combinación rara no entra, el CLI también sale con código 2 y el mensaje `cannot place ... increase --days`.

## Corrida por defecto (referencia)

| Dato | Valor |
|---|---|
| Comando | `python ml/data/generate_labeled_dataset.py` (seed 66, 28 días, 60 s, 3 apps) |
| Filas | 530 667 (train 425 029, validation 105 638) |
| Filas anómalas | 10 188 (train 8 207 = 1.93 %, validation 1 981 = 1.88 %) |
| Filas hard negative | 13 700 (train 10 656, validation 3 044) |
| Eventos | 270 anomalías (216 train = 12 por combinación; 54 validation = 3 por combinación; 184 en horario pico) + 112 hard negatives (84 mantenimiento, 28 surges) |
| Tamaño | CSV 51 327 189 bytes; `manifest.json` 193 170 bytes |
| Tiempo | ≈ 3.5 s el CLI completo (≈ 1 s generar, ≈ 2 s escribir el CSV); ≈ 6 s `load_labeled_dataset` (validación pydantic de todas las filas) |
| sha256 del CSV | `a90b1eccc9a8c524c143d157e861a6afdb95a7c8e5a2bb3a24b055cc343c26ed` |
| Entorno | numpy 2.5.3, Python 3.13.9, Windows 11 |

El hash es reproducible con la misma versión de numpy (dos corridas por defecto dan el mismo hash). numpy no garantiza el mismo stream de `Generator` entre versiones, y las funciones matemáticas pueden variar en el último bit entre plataformas: si el hash no coincide, mirá primero `numpy_version` en el manifest.

### Validation por combinación (corrida por defecto)

Cada celda tiene **3 eventos**. Entre paréntesis, filas anómalas de la celda.

| Tipo | `low` | `medium` | `high` |
|---|---|---|---|
| `spike` | 3 (7) | 3 (6) | 3 (9) |
| `level_shift` | 3 (73) | 3 (96) | 3 (116) |
| `drift` | 3 (159) | 3 (155) | 3 (182) |
| `variance_burst` | 3 (121) | 3 (61) | 3 (108) |
| `dropout` | 3 (49) | 3 (27) | 3 (38) |
| `correlated_incident` | 3 (298) | 3 (251) | 3 (225) |

El recall por celda en validation descansa en 3 eventos: sirve para ver tendencias, no para afirmar diferencias finas. `spike` tiene pocas filas por diseño (1-3 minutos): medirlo por evento.

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
| `is_anomaly` | 0/1 | **la etiqueta**: 1 = fila que una anomalía inyectada modificó |
| `anomaly_type` | str | tipo de anomalía, patrón benigno o `none` (solo para análisis) |
| `severity` | str | `low`, `medium`, `high` o `none` (solo para análisis) |
| `event_id` | str | `A-NNNN` anomalía, `H-NNNN` hard negative, vacío si normal (solo para análisis) |
| `hard_negative` | 0/1 | 1 = evento benigno que parece anómalo (solo para análisis) |
| `split` | str | `train` o `validation` |

Las seis primeras columnas son exactamente el contrato M4: cada fila valida como `MetricBatchInput` (está testeado).

### Rangos por métrica (corrida por defecto, todas las filas)

| id | Métrica | Unidad | min | p50 | p99 | max |
|---|---|---|---|---|---|---|
| 1 | TTFB | ms | 17.47 | 337.44 | 1 198.54 | 4 203.51 |
| 2 | FCP | ms | 83.33 | 1 955.31 | 6 139.88 | 19 393.74 |
| 3 | XHR_LATENCY | ms | 10.76 | 273.04 | 1 587.14 | 6 150.45 |
| 4 | JS_EXCEPTION_RATE | proporción | 0 | 0 | 0.4475 | 1 |
| 5 | RAGE_CLICK | clics/sesión | 0 | 0.36 | 2 | 6 |

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

| `anomaly_type` | Duración (minutos) | Forma |
|---|---|---|
| `spike` | 1-3 | salto puntual `+k·σ` |
| `level_shift` | 20-60 | escalón sostenido |
| `drift` | 30-90 | rampa lineal hasta `k·σ` |
| `variance_burst` | 15-45 | latencias: desvío × `k`, misma media; tasa y rage: `+σ·√(k²−1)·abs(w)` (solo hacia arriba: el valor suele estar en 0) |
| `dropout` | 5-20 | `session_count` cae una fracción; el valor se recalcula con menos sesiones |
| `correlated_incident` | 10-40 | escalón simultáneo en TTFB + FCP + XHR (+ JS rate a veces) de una app, un solo `event_id` |

`σ` es el desvío **local** del residuo de la serie limpia respecto de su base estacional (±60 buckets alrededor del evento). Todas son degradaciones hacia arriba, salvo `dropout`. Con buckets de más de 60 s la duración se convierte a buckets (`round(minutos·60/bucket_seconds)`, mínimo 1).

**Etiqueta = cambio real.** La inyección no crea ni borra filas: un bucket sin sesiones sigue vacío. `is_anomaly=1` solo en filas cuyo `value` exportado o `session_count` difiere de la misma corrida sin inyección (testeado contra una corrida limpia con la misma seed). Por eso una ventana puede tener filas sin etiquetar (p. ej. una tasa ya en 1 que no puede subir).

| Severidad | `k` (sigmas) | `dropout` (fracción de sesiones perdidas) |
|---|---|---|
| `low` | 3-4 (sutil) | 0.40-0.60 |
| `medium` | 4-6 | 0.60-0.80 |
| `high` | 6-9 | 0.80-0.95 |

La magnitud efectiva de cada evento está en `manifest.json` → `events[].magnitude` (por métrica).

**Chequeo de dificultad (no es un benchmark).** Un z-score robusto ingenuo (mediana/MAD de las 60 filas previas de la serie, umbral 3) sobre la corrida por defecto marca:

| Filas | Marcadas |
|---|---|
| anómalas `low` / `medium` / `high` | 28 % / 42 % / 54 % |
| normales | 6.5 % |
| `benign_maintenance` | 37 % (más que una anomalía `low`) |
| `benign_traffic_surge` | 12 % |

Los `low` son realmente sutiles y los benignos engañan a un detector que solo mira el valor. La comparación seria es trabajo de B.6.

## Hard negatives

Eventos benignos que **parecen** anómalos: `is_anomaly=0`, `hard_negative=1`, `event_id` propio, `severity=none`, `anomaly_type` = nombre del patrón. Sirven para medir la tasa de falsos positivos (KPI del proyecto) en casos difíciles.

| `anomaly_type` | Qué pasa | Por qué engaña |
|---|---|---|
| `benign_traffic_surge` | campaña: tráfico × 1.8-2.6 en campana durante 30-90 minutos; TTFB, FCP y XHR suben `k·σ` (k 3-6) con la misma campana | `session_count` y latencias suben juntos, con magnitud de anomalía `low`/`medium` |
| `benign_maintenance` | todos los días, por app, a una hora sorteada entre 19:00 y 23:45 UTC, 15 min: sesiones × 0.6, TTFB y XHR `+k·σ` (k 3-6, escalón) | parece `dropout` + `level_shift`; es recurrente pero no a hora fija |

- El efecto usa el mismo `σ` local que las anomalías y la banda `low`/`medium` (3-6): en `value` un benigno no es más chico que una anomalía sutil.
- No hay zona de exclusión alrededor de los benignos: una anomalía puede empezar justo al lado (nunca se solapan en la misma serie).
- Lo que los distingue es el **contexto** (tráfico que sube a la par, recurrencia nocturna diaria), no la magnitud. Un modelo con features de hora o de `session_count` puede aprender parte de eso; un detector que solo mira el valor los marca como anomalía.
- Medir la tasa de falsos positivos de B.6 sobre `hard_negative=1` **y** sobre filas normales, por separado. Es una tasa sobre este generador: no extrapolar a producción.

## Agenda y split

- **Split temporal**: un único corte global al 80 % de la ventana (`params.boundary` en el manifest; `2026-08-25T09:36:00Z` por defecto). Todo lo anterior es `train`, lo demás `validation`. Nunca aleatorio: así no hay fuga de futuro ni entre series. Ningún `event_id` aparece en los dos splits (testeado).
- **Estratificación**: cada combinación (tipo, severidad) tiene **al menos 3 eventos en cada split**; si la ventana alcanza, la cantidad se calcula para una contaminación de ~2 % de filas (train recibe proporcionalmente más: 12 por combinación con los defaults).
- **Contaminación**: con los defaults 1.93 % train y 1.88 % validation (seeds 0-9: 1.83-1.97 % train, 1.82-2.15 % validation). Con ventanas chicas sube (el mínimo de 3 eventos por combinación domina).
- **Restricciones**: sin solapes por serie, gap mínimo de 30 minutos entre anomalías, ningún evento cruza el corte, solo donde se esperan ≥ 3 sesiones por bucket (≥ 20 para `dropout`).
- **Casos difíciles**: 1 de cada 3 anomalías se fuerza a horario pico (lun-vie 10-17 UTC); `events[].at_peak` lo indica.

## Cómo lo consume B.6

```python
import importlib.util

spec = importlib.util.spec_from_file_location(
    "generate_labeled_dataset", "ml/data/generate_labeled_dataset.py")
gld = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gld)

data = gld.load_labeled_dataset("ml/data/synthetic")  # verifica el sha256 del manifest
train, validation = data["train"], data["validation"]
# train.rows: list[MetricBatchInput] (features); train.labels: list[RowLabel] (mismo orden)
y_train = [label.is_anomaly for label in train.labels]  # la única etiqueta
```

- Features: solo de `train.rows` (contrato M4). El resto de `RowLabel` sirve para cortar métricas, nunca para entrenar.
- Correr con `PYTHONPATH=.` (el lector importa `src.ml.schemas`). Generar el dataset no lo necesita.
- Sin acoplamiento a la ingesta: el módulo no importa `src.api`, ni usa DB ni HTTP (está testeado).
- Para métricas por evento (recall por evento, falsos positivos por evento) usar `event_id` y `manifest.json` → `events`.
- Para la tasa de falsos positivos sobre casos difíciles, filtrar `hard_negative=1`.

## Limitaciones

- **El modelo puede aprender el generador.** Formas, duraciones y bandas de severidad son decisiones de diseño, no observaciones. No reportar F1, recall o precisión de este dataset como desempeño esperado en producción.
- **Revalidar con datos reales** (R.2) cuando existan; este dataset no reemplaza esa validación.
- Supuestos del modelo: ruido AR(1) gaussiano/lognormal, estacionalidad fija en UTC, sin feriados ni eventos de calendario reales, sin deploys reales, apps independientes entre sí, cobertura de métricas constante.
- Todas las anomalías son degradaciones (hacia arriba), salvo `dropout`; no hay mejoras abruptas.
- Los benignos tienen un patrón aprendible (surge con tráfico, mantenimiento nocturno diario): su tasa de falsos positivos mide eso, no la variedad de los benignos reales.
- Validation tiene 3 eventos por combinación: el recall por celda es ruidoso.
- Con buckets grandes (≥ 900 s) las anomalías cortas ocupan 1 bucket y el `σ` local (±60 buckets) cubre horas o días: la dificultad no es comparable con la corrida de 60 s.

## Otros archivos de esta carpeta

| Archivo | Qué es |
|---|---|
| `generate_mock_dataset.py`, `rum_mock.json`, `*.png` | dataset mock y gráficos del EDA de ISS-S3-05 (sin etiquetas; no se usa para B.6) |
| `synthetic/` | salida del generador etiquetado (ignorada por git) |
