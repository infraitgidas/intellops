# Delta para ingest-normalization

**Cambio**: ISS-S3-02 (#41). **Tipo**: Capacidad nueva. **Store**: openspec. **Base**: proposal r1, exploration, research r1, `ContratoIngestaRUM.md:30`, config.yaml (<2GB RAM, CPU-only, TDD estricto).

## Purpose

Una etapa de normalización pura canonicaliza **solo representaciones** de la telemetría RUM antes de la validación por evento, de modo que la validación sigue siendo la autoridad única de rechazo: timestamps UTC con zona horaria explícita, unidades `ms`/`count`, nombres `UPPER_SNAKE`, `error_type` canónico, y defaults opcionales definidos por el contrato.

## ADDED Requirements

### Requirement: NORM-1 (etapa pura, pre-validación)

El sistema DEBE aplicar una etapa de normalización pura y sin E/S a cada evento antes de la validación por evento. NO DEBE decidir la aceptación; la validación DEBE seguir siendo la autoridad única de rechazo. El fallo de normalización de un solo evento NO DEBE hacer fallar el lote: DEBE preservarse la semántica parcial `202` (`accepted` / `rejected[{index, reason}]`).

#### Scenario: Aceptación parcial preservada
- GIVEN un lote con un evento que lleva una unidad no resoluble
- WHEN se procesa
- THEN la respuesta sigue siendo `202`, ese evento en `rejected[]`
- AND el normalizador no realiza E/S

### Requirement: NORM-2 (timestamps)

La normalización DEBE canonicalizar los timestamps aceptados a UTC con zona horaria explícita. Un `timestamp` de métrica ausente DEBE heredar el `timestamp` del envelope. Los timestamps naïve o no parseables DEBEN rechazarse (`invalid_timestamp`) y NO DEBEN reescribirse al tiempo de ingesta; el fallback silencioso `now()` DEBE eliminarse.

#### Scenario: Offset canonicalizado
- GIVEN un timestamp de envelope `2026-10-13T12:00:00-03:00`
- WHEN se acepta
- THEN el timestamp canónico es UTC con zona horaria explícita

#### Scenario: La métrica hereda el envelope
- GIVEN una métrica sin `timestamp` y un `timestamp` de envelope
- WHEN se normaliza
- THEN el timestamp de la métrica es igual al del envelope

#### Scenario: Naive rechazado
- GIVEN `timestamp: "2026-10-13T12:00:00"` (sin offset)
- WHEN se procesa
- THEN `invalid_timestamp`, NO reemplazado por `now()`

### Requirement: NORM-3 (unidades)

La normalización DEBE convertir los alias de duración (`s`, `sec`, `secs`, `msec`, `millis`) a la unidad canónica `ms` (familia `s` ×1000) y `counts` a `count`, además de las canónicas `ms`/`count`. La conversión DEBE ser idempotente, indexada por la unidad de entrada declarada. Las unidades desconocidas DEBEN seguir rechazándose (`invalid_unit`).

#### Scenario: Segundos convertidos
- GIVEN TTFB `value: 2`, `unit: "s"`
- WHEN se normaliza
- THEN `value: 2000`, `unit: "ms"`

#### Scenario: Idempotente
- GIVEN una métrica con `unit: "ms"`
- WHEN se normaliza dos veces
- THEN su valor queda sin cambios en ambas pasadas

#### Scenario: Unidad desconocida rechazada
- GIVEN `unit: "furlongs"`
- WHEN se procesa
- THEN `invalid_unit`

### Requirement: NORM-4 (nombres)

La normalización DEBE canonicalizar los nombres de tipo de métrica (trim/case más mapa de alias) a `{TTFB, FCP, XHR_LATENCY, JS_EXCEPTION_RATE, RAGE_CLICK}`; los nombres desconocidos DEBEN seguir rechazándose (`invalid_metric_type`). DEBE canonicalizar `error_type` (trim/case más mapa de alias) y llevar los valores desconocidos a `Other`. NO DEBE introducirse catálogo DDL ni migración.

#### Scenario: Nombre con case-fold
- GIVEN `type: "ttfb"`
- WHEN se normaliza
- THEN `type: "TTFB"`

#### Scenario: error_type desconocido agrupado en bucket
- GIVEN `error_type: "WeirdError"`
- WHEN se normaliza
- THEN `error_type: "Other"`, sin cambio de esquema

### Requirement: NORM-5 (valores ausentes)

Un campo requerido ausente DEBE rechazarse (`missing_required_field`). Los campos opcionales PUEDEN recibir solo los defaults/herencia definidos por el contrato (`timestamp` de métrica ← envelope; nulables `page_url`, `stack_trace`, `metric_id`, `user_agent`); NO DEBE inventarse ningún default semántico.

#### Scenario: Requerido ausente
- GIVEN un evento sin `session_id`
- WHEN se procesa
- THEN `missing_required_field`

#### Scenario: Opcional ausente
- GIVEN un evento sin `stack_trace`
- WHEN se procesa
- THEN aceptado, sin valor fabricado

### Requirement: NORM-6 (valores inválidos: solo representación)

La normalización DEBE reparar solo la representación: coaccionar cadenas numéricas finitas (`"120.5"` → `120.5`) y recortar espacios en blanco. DEBE rechazar `NaN`/`Infinity`/cadenas no finitas. NO DEBE recortar, limitar, redondear ni reparar magnitudes o valores fuera de rango; los conteos no enteros DEBEN rechazarse como `invalid_range`. Los campos portadores de anomalía DEBEN conservar su magnitud.

#### Scenario: Cadena numérica coaccionada
- GIVEN `value: "120.5"`
- WHEN se normaliza
- THEN `value: 120.5`

#### Scenario: No finito rechazado
- GIVEN `value: "Infinity"`
- WHEN se procesa
- THEN rechazado, no convertido

#### Scenario: Sin recorte
- GIVEN TTFB `value: 9000` (dentro del rango de sanity)
- WHEN se normaliza
- THEN 9000 se preserva sin cambios

#### Scenario: Conteo fraccionario rechazado
- GIVEN JS_EXCEPTION_RATE `value: 1.5`
- WHEN se procesa
- THEN `invalid_range`, sin redondeo

### Requirement: NORM-7 (límites de recursos)

La normalización DEBE ser pura en memoria, CPU-only, NO DEBE agregar dependencias ni procesos, y DEBE mantenerse dentro de `<2GB RAM` / `$0/mes`. La aceptación de precisión/recall/F1 del ML **no aplica**: la normalización es de solo representación, sin modelo ni entrenamiento.

## Non-goals

- Recorte/reparación de magnitudes de valores fuera de rango (la señal de anomalía).
- Catálogo DDL/migración de `error_type`.
- Backfill/replay de eventos ya rechazados.
- Cambios de envelope, `202` o backpressure.

## Next recommended

**design** — definir la interfaz pura de `ingest_normalizer`, los registros compartidos con `ingest_policy`, y la secuencia de normalizar-antes-de-validar.
