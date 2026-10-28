# SPEC — synthetic-dataset (Nueva) — A.4

**Tipo**: Delta spec (capability nueva). **Cambio**: A.4 (GitHub #66). **Base**: `proposal.md`, `design.md`, contrato M4 (`src/ml/schemas.py`, ISS-S3-04).
**Alcance**: generador sintético etiquetado, export, split y lector para B.6. Las palabras DEBE, NO DEBE y PUEDE siguen RFC 2119.

## ADDED Requirements

### Requirement: SYN-1 (reproducibilidad)

El generador DEBE ser determinista dado `(seed, days, bucket_seconds, apps)` con la misma versión de numpy.

#### Scenario: SYN-1.1 Misma seed
- GIVEN dos corridas con los mismos parámetros
- WHEN se exportan
- THEN el CSV y el `manifest.json` son idénticos byte a byte

#### Scenario: SYN-1.2 Seed distinta
- GIVEN dos corridas que solo difieren en `seed`
- THEN los CSV difieren

### Requirement: SYN-2 (contrato M4)

Cada fila DEBE validar como `MetricBatchInput`. `timestamp` DEBE ser ISO-8601 UTC con sufijo `Z` y alineado a `bucket_seconds`. NO DEBE haber dos filas con la misma `(application_id, metric_type_id, timestamp)`. Los buckets sin sesiones NO DEBEN emitirse. `value` DEBE ser finito y `≥ 0`; `JS_EXCEPTION_RATE` DEBE ser `≤ 1`.

#### Scenario: SYN-2.1 Validación de filas
- GIVEN el dataset generado
- WHEN cada fila se valida como `MetricBatchInput`
- THEN todas son válidas

#### Scenario: SYN-2.2 Alineación y unicidad
- THEN todo `timestamp` termina en `Z`, es múltiplo de `bucket_seconds` y no se repite por serie

#### Scenario: SYN-2.3 Huecos
- GIVEN una app de bajo tráfico
- THEN ninguna fila tiene `session_count = 0` y la serie tiene menos filas que buckets

#### Scenario: SYN-2.4 Rangos
- THEN `value ≥ 0` en todas las filas y `value ≤ 1` en `metric_type_id = 4`

### Requirement: SYN-3 (realismo)

Las series DEBEN tener estacionalidad diaria, latencias con sesgo a derecha y latencias correlacionadas dentro de una app.

#### Scenario: SYN-3.1 Estacionalidad
- THEN el `session_count` medio en horario pico supera al de la madrugada

#### Scenario: SYN-3.2 Sesgo y correlación
- THEN en latencias la media supera a la mediana, y TTFB y XHR de una app tienen correlación positiva

### Requirement: SYN-4 (catálogo y etiquetas)

El dataset DEBE contener los tipos `spike`, `level_shift`, `drift`, `variance_burst`, `dropout` y `correlated_incident`, cada uno en severidades `low`, `medium` y `high`, en **ambos** splits. Toda fila con `is_anomaly=1` DEBE tener tipo, severidad y `event_id`; toda fila normal DEBE tener `anomaly_type=none`, `severity=none` y `event_id` vacío. La magnitud efectiva DEBE caer en la banda de su severidad (3-4, 4-6, 6-9 sigmas locales).

#### Scenario: SYN-4.1 Cobertura estratificada
- THEN cada combinación `(tipo, severidad)` aparece al menos una vez en `train` y en `validation`

#### Scenario: SYN-4.2 Incidente correlacionado
- THEN cada `event_id` de `correlated_incident` abarca ≥ 2 métricas de una sola app

#### Scenario: SYN-4.3 Bandas de severidad
- THEN la magnitud registrada en el manifest de cada anomalía cae en la banda de su severidad

### Requirement: SYN-5 (agenda)

Los eventos NO DEBEN solaparse en una serie, DEBEN respetar un gap mínimo y NO DEBEN cruzar el corte train/validation. La contaminación (filas anómalas / filas) DEBE quedar entre 1 % y 3 % con los parámetros por defecto. Una parte de las anomalías DEBE ubicarse en horario pico.

#### Scenario: SYN-5.1 Sin solape ni cruce
- THEN por serie los eventos están separados por ≥ 30 buckets y cada evento tiene un único `split`

#### Scenario: SYN-5.2 Contaminación
- GIVEN los parámetros por defecto
- THEN la contaminación está entre 1 % y 3 %

### Requirement: SYN-6 (hard negatives)

El dataset DEBE incluir eventos benignos (`hard_negative=1`, `is_anomaly=0`, `event_id` propio) en ambos splits, para medir falsos positivos.

#### Scenario: SYN-6.1 Benignos
- THEN ninguna fila con `hard_negative=1` tiene `is_anomaly=1`, y hay filas `hard_negative=1` en `train` y en `validation`

### Requirement: SYN-7 (split temporal)

El split DEBE ser temporal con un corte global al 80 % de la ventana; NO DEBE ser aleatorio.

#### Scenario: SYN-7.1 Sin fuga de futuro
- THEN por serie el máximo `timestamp` de `train` es menor que el mínimo de `validation`

### Requirement: SYN-8 (export)

El CSV DEBE tener exactamente las columnas del contrato M4 seguidas de `is_anomaly, anomaly_type, severity, event_id, hard_negative, split`. El `manifest.json` DEBE incluir seed, parámetros, versión de numpy, schema, conteos por split/tipo/severidad, rangos por métrica y el sha256 del CSV.

#### Scenario: SYN-8.1 Manifest consistente
- THEN el sha256 del CSV coincide con el del manifest y los conteos coinciden con el CSV

### Requirement: SYN-9 (consumo por B.6)

El módulo DEBE ofrecer `load_labeled_dataset(path)` que devuelva por split las filas validadas como `MetricBatchInput` y sus etiquetas. El módulo NO DEBE importar `src.api`, ni acceder a DB ni a HTTP.

#### Scenario: SYN-9.1 Lector
- WHEN se lee el CSV exportado
- THEN devuelve `train` y `validation` con filas `MetricBatchInput` y etiquetas alineadas

#### Scenario: SYN-9.2 Integridad
- GIVEN un CSV alterado con su `manifest.json` original
- THEN el lector falla con error de sha256

#### Scenario: SYN-9.3 Sin acoplamiento
- THEN el código fuente no importa `src.api`, `api`, `sqlalchemy`, `httpx`, `requests` ni `urllib`
