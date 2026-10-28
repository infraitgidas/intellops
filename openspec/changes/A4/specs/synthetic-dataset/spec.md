# SPEC — synthetic-dataset (Nueva) — A.4

**Tipo**: Delta spec (capability nueva). **Cambio**: A.4 (GitHub #66). **Base**: `proposal.md`, `design.md`, contrato M4 (`src/ml/schemas.py`, ISS-S3-04).
**Alcance**: generador sintético etiquetado, export, split y lector para B.6. Las palabras DEBE, NO DEBE y PUEDE siguen RFC 2119.

## ADDED Requirements

### Requirement: SYN-1 (reproducibilidad)

El generador DEBE ser determinista dado `(seed, days, bucket_seconds, apps)` con la misma versión de numpy. Parámetros inválidos (`days < 8`, `bucket_seconds < 60`, `apps` fuera de 1-3) DEBEN fallar antes de generar con un mensaje que indique el mínimo; el CLI DEBE salir con código 2 sin traceback.

#### Scenario: SYN-1.1 Misma seed
- GIVEN dos corridas con los mismos parámetros
- WHEN se exportan
- THEN el CSV y el `manifest.json` son idénticos byte a byte

#### Scenario: SYN-1.2 Seed distinta
- GIVEN dos corridas que solo difieren en `seed`
- THEN los CSV difieren

#### Scenario: SYN-1.3 Ventana insuficiente
- GIVEN `--days 1`
- THEN el CLI termina con código 2 y el mensaje `days must be >= 8`, sin escribir archivos

### Requirement: SYN-2 (contrato M4)

Cada fila DEBE validar como `MetricBatchInput`. Las duraciones de eventos y el gap DEBEN expresarse en minutos de reloj y convertirse a buckets (mínimo 1), para que `bucket_seconds` > 60 no cambie el significado del catálogo. `timestamp` DEBE ser ISO-8601 UTC con sufijo `Z` y alineado a `bucket_seconds`. NO DEBE haber dos filas con la misma `(application_id, metric_type_id, timestamp)`. Los buckets sin sesiones NO DEBEN emitirse. `value` DEBE ser finito y `≥ 0`; `JS_EXCEPTION_RATE` DEBE ser `≤ 1`.

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

#### Scenario: SYN-2.5 Buckets grandes
- GIVEN `bucket_seconds` 900, 3600 o 7000 con los días por defecto
- THEN la generación termina y la duración de reloj de cada anomalía cae en el rango de su tipo (± medio bucket, mínimo 1 bucket)

### Requirement: SYN-3 (realismo)

Las series DEBEN tener estacionalidad diaria, latencias con sesgo a derecha y latencias correlacionadas dentro de una app.

#### Scenario: SYN-3.1 Estacionalidad
- THEN el `session_count` medio en horario pico supera al de la madrugada

#### Scenario: SYN-3.2 Sesgo y correlación
- THEN en latencias la media supera a la mediana, y TTFB y XHR de una app tienen correlación positiva

### Requirement: SYN-4 (catálogo y etiquetas)

El dataset DEBE contener los tipos `spike`, `level_shift`, `drift`, `variance_burst`, `dropout` y `correlated_incident`, cada uno en severidades `low`, `medium` y `high`, con **al menos 3 eventos por combinación en cada split**. La inyección NO DEBE crear ni borrar filas respecto de la misma corrida sin inyección; `is_anomaly=1` DEBE marcar solo filas cuyo `value` exportado o `session_count` cambió. Toda fila con `is_anomaly=1` DEBE tener tipo, severidad y `event_id`; toda fila normal DEBE tener `anomaly_type=none`, `severity=none` y `event_id` vacío. La magnitud efectiva DEBE caer en la banda de su severidad (3-4, 4-6, 6-9 sigmas locales; en `dropout`, fracción de sesiones perdidas 0.40-0.60, 0.60-0.80, 0.80-0.95).

#### Scenario: SYN-4.1 Cobertura estratificada
- GIVEN las seeds 7, 8 y 9 (y la corrida por defecto)
- THEN cada combinación `(tipo, severidad)` tiene ≥ 3 `event_id` distintos en `train` y en `validation`

#### Scenario: SYN-4.4 Etiqueta = cambio real
- GIVEN la misma seed generada con y sin inyección de anomalías
- THEN ambos tienen exactamente las mismas filas, toda fila `is_anomaly=1` difiere en `value` o `session_count` y toda fila `is_anomaly=0` es idéntica

#### Scenario: SYN-4.2 Incidente correlacionado
- THEN cada `event_id` de `correlated_incident` abarca ≥ 2 métricas de una sola app

#### Scenario: SYN-4.3 Bandas de severidad
- THEN la magnitud registrada en el manifest de cada anomalía cae en la banda de su severidad

### Requirement: SYN-5 (agenda)

Los eventos NO DEBEN solaparse en una serie y NO DEBEN cruzar el corte train/validation. Las anomalías DEBEN respetar entre sí un gap mínimo de 30 minutos; los hard negatives NO DEBEN tener zona de exclusión (una anomalía PUEDE caer al lado). La contaminación (filas anómalas / filas) DEBE quedar entre 1 % y 3 % **en cada split** con los parámetros por defecto. Al menos un 30 % de las anomalías DEBE ubicarse en horario pico. Ningún `event_id` DEBE aparecer en ambos splits.

#### Scenario: SYN-5.1 Sin solape ni cruce
- THEN por serie ningún par de eventos se solapa, las anomalías están separadas por ≥ 30 minutos, cada evento tiene un único `split` y train y validation no comparten `event_id`

#### Scenario: SYN-5.2 Contaminación
- GIVEN los parámetros por defecto
- THEN la contaminación de `train` y la de `validation` están, cada una, entre 1 % y 3 %

#### Scenario: SYN-5.3 Benignos sin zona de exclusión
- THEN existe al menos una anomalía a menos de 30 minutos de un hard negative en la misma serie

### Requirement: SYN-6 (hard negatives)

El dataset DEBE incluir eventos benignos (`hard_negative=1`, `is_anomaly=0`, `event_id` propio) en ambos splits, para medir falsos positivos. Su efecto DEBE verse en `session_count` **y** en `value`, con magnitud de anomalía `low`/`medium` (3-6 sigmas locales). El mantenimiento NO DEBE ocurrir a una hora fija: su inicio se sortea por app y día.

#### Scenario: SYN-6.1 Benignos
- THEN ninguna fila con `hard_negative=1` tiene `is_anomaly=1`, y hay filas `hard_negative=1` en `train` y en `validation`

#### Scenario: SYN-6.2 Efecto visible
- THEN cada surge sube `session_count` (> 1.3×) y TTFB respecto de los 60 buckets previos; cada benigno registra `k` ∈ [3, 6) por métrica afectada y la mediana del desplazamiento estandarizado de `value` supera 1.5

#### Scenario: SYN-6.3 Hora sorteada
- THEN más de la mitad de los mantenimientos tienen una hora de inicio distinta

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
- THEN devuelve `train` y `validation` con filas `MetricBatchInput` y etiquetas alineadas; fila a fila, `0/1` se leen como booleanos, `none` y `event_id` vacío se preservan y `value`/`session_count` coinciden con lo generado

#### Scenario: SYN-9.2 Integridad
- GIVEN un CSV alterado con su `manifest.json` original
- THEN el lector falla con error de sha256

#### Scenario: SYN-9.3 Sin acoplamiento
- THEN el código fuente no importa `src.api`, `api`, `sqlalchemy`, `httpx`, `requests` ni `urllib`
