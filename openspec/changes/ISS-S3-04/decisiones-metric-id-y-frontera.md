# DECISION BRIEF — ISS-S3-04: `metric_id` (D2) y frontera de implementación (D4)

- **Cambio**: ISS-S3-04 (GitHub #43 — "Dataset operativo para ML")
- **Base**: `feat/ISS-S3-04` sobre `origin/develop` con ISS-S3-01 (PR #57) mergeado
- **Owners**: Federico (Dataset) + Romeo (ML)
- **Alcance de este documento**: análisis, no implementación. No decide. Prepara a Federico para cerrar D2 y D4 con Romeo.
- **Estado**: entradas fijas confirmadas; D2 y D4 **pendientes**.
- **Fuentes**: `openspec/changes/ISS-S3-04/exploration.md` (P1), `openspec/changes/ISS-S3-04/research.md` (evidencia S1–S28 / P1–P10).

---

## 1. Propósito y cómo usar este documento

Este brief aísla las **dos decisiones que dependen de Romeo** y que bloquean el `sdd-propose` del cambio. Federico lo recorre con Romeo para cerrarlas; cada sección está pensada para leerse en voz alta y responder las preguntas de la sección 5.

- **D2 — `metric_id`**: cómo se resuelve el desajuste entre el shape agregado del productor (sin `metric_id`) y el contrato de entrada del ML (`metric_id` requerido). Ver §3.
- **D4 — frontera de implementación**: dónde vive el reader/adaptador y quién lo escribe. Ver §4.

Las entradas fijas de §2 son **decididas y no se re-abren**. La recomendación de §5 es **no vinculante** (soporte a la decisión). §6 es el registro en blanco que llenan Federico + Romeo.

---

## 2. Contexto (recap corto)

### 2.1 Productor — read path de telemetría (ISS-S3-01, mergeado)

- `GET /metrics/query` (`queryMetrics`) y `GET /metrics/list` (`listMetrics`), autenticados con `Depends(require_api_key)`; el tenant se deriva **exclusivamente** de la API key (OAS-14, ADR-0003).
- `MetricAggregate = (application_id, metric_type_id, timestamp, value, session_count)` — fila **agregada** (`AVG(value)` + `COUNT(DISTINCT session_id)` por bucket). **No tiene `metric_id`** (P5; `openspec/specs/openapi.yaml:1054-1074`, P9).
- Límites TQ-2: ventana default 15 min, máximo 7 días, bucket mínimo 60 s; `start < end` → 422 `invalid_query_range`.

### 2.2 Consumidor — módulo ML (dominio de Romeo)

- `src/ml/schemas.py` — `MetricBatchInput` con `application_id`, **`metric_id: UUID4` (requerido)**, `metric_type_id`, `timestamp`, `value`, `session_count` (P4).
- `src/ml/pipeline/mock_reader.py` lee el mock estático `src/ml/mock_data.json` (2 registros, con `metric_id`); `src/ml/main.py` no consume el read path.
- El contenedor `intellops-ai-engine` hoy solo copia `entrypoint.py` (placeholder); la app FastAPI de `src/ml` se ejerce en tests, no está desplegada.

### 2.3 Salida del motor — contrato y persistencia

- `docs/architecture/IsolationForest/ContratoEntradaSalida.md` — la entrada requiere `metric_id`; el registro `ANOMALY` **persiste `metric_id`** (P7).
- `openspec/specs/database/ddl_v1.0.sql:258-277` — `anomaly.metric_id UUID NOT NULL` con `FK (metric_id) REFERENCES rum_metric(metric_id) ON DELETE RESTRICT` (P8). El ancla es una fila física de `rum_metric`.

### 2.4 Entradas fijas (decididas; no re-abrir)

- **Mecanismo**: E1 — HTTP pull del read path (`GET /metrics/query`).
- **Dataset**: key por aplicación.
- **Alcance funcional**: dataset + reader validado, **sin entrenamiento**.
- **Consumo**: pull bajo demanda.

### 2.5 Restricciones y reglas vigentes

- CPU-only, **< 2 GB RAM**, $0/mes; footprint del AI engine limitado a 1000 MB (`containers.md` §2.3).
- `containers.md` §5.1 — **no cross-imports** entre `intellops-core` y `intellops-ai-engine`.
- `containers.md` §2.3 / C4 declara `Rel(ai, db, "Read batch", "RUM_METRIC (read)")`; ADR-0003 fija el consumo vía HTTP. Tensión documental ya identificada (D1/R1), fuera de este brief salvo como contexto.
- EDT: `Dataset` = Federico, `ML` = Romeo; "un módulo, un owner"; mandato **contract-first** ("se definirá un contrato de dataset en S1-S3", EDT §6).
- Migraciones: Alembic en `src/api/infrastructure/db/migrations/versions/` (última `0003_is_active.py`). Todo cambio de DDL de `ANOMALY` implicaría una migración nueva.

---

## 3. D2 — Matriz de decisión de `metric_id` (núcleo)

### 3.0 Restricción dura (hecho vinculante)

`MetricBatchInput.metric_id` es requerido (P4) y `anomaly.metric_id` es `UUID NOT NULL` con **FK a `rum_metric.metric_id`** (P8). Una fila agregada (P5) **no tiene una fila `rum_metric` asociada**.

> **Ninguna opción conserva simultáneamente (i) el anclaje a la serie agregada y (ii) la FK física actual, sin un cambio deliberado de contrato y/o DDL.** La elección es sobre **qué** se relaja:
> - **M1** y **M4** tocan la entidad ML/DDL (dominio de Romeo); M1 deriva a M4 para recuperar el anclaje.
> - **M2** conserva el shape de entrada pero exige reemplazar la FK (DDL).
> - **M3** es la única que preserva la FK sin migración, pero es scope nuevo y reintroduce acoplamiento.

---

### 3.1 M1 — `metric_id` opcional (nullable)

**Qué cambia**

| Área | Cambio |
|---|---|
| Contrato (`MetricBatchInput`) | `metric_id: UUID4 \| None` (deja de ser requerido). |
| Adaptador | Mapea el bucket sin `metric_id` (pasa `None`). |
| Entidad `ANOMALY` | `metric_id` pasa a nullable; para no quedar huérfana, la anomalía necesita anclarse a la clave del bucket → **deriva a M4**. |
| DDL / migración | **Sí** — `ALTER TABLE anomaly ALTER COLUMN metric_id DROP NOT NULL`. Si se completa el anclaje a bucket, además se agregan columnas de serie (→ migración tipo M4). |
| Productor (`src/api`) | **Sin cambios** (el read path ya devuelve el agregado sin `metric_id`). |

**Consecuencias**

- Acoplamiento: bajo en el productor; rompe semanticamente el contrato de entrada ML.
- Trazabilidad / FK: pierde el ancla física; un FK nullable queda "colgando" salvo que se agregue la clave de serie. Evidencia C8/S10: el registro de anomalía debería conservar una referencia a su origen.
- Footprint: neutral (~0); no materializa filas.
- Testabilidad: alta (test de contrato simple).
- Versionado / back-compat: cambio de contrato ML (semántica de `NULL` + persistencia); debe versionarse (C11).

**Evidencia que habla de M1**: C7/S9 (no derivar clave si existe un id estable), C8/S10 (la anomalía debe conservar referencia al origen). La investigación concluye que **M1 sola no alcanza**: al nulear el FK obliga a re-anclar y deriva en M4.

**Impacto de owner**: `MetricBatchInput`, entidad `ANOMALY` y migración son **dominio de Romeo** (+ DB). Federico solo documenta el contrato del dataset.

---

### 3.2 M2 — `uuid5` determinista

**Qué cambia**

| Área | Cambio |
|---|---|
| Contrato (`MetricBatchInput`) | **Sin cambios** (`metric_id` sigue requerido). |
| Adaptador | Calcula `uuid5(namespace, app + type + bucket)` por fila agregada. |
| Entidad `ANOMALY` | Forma sin cambios, pero el valor de `metric_id` **no existe** en `rum_metric`. |
| DDL / migración | **Sí** (o falla en runtime) — la FK `fk_anomaly_metric → rum_metric` viola al insertar un id sintético: hay que eliminar/redefinir la FK o crear tabla de mapeo. |
| Productor (`src/api`) | Sin cambios de shape; posible necesidad de **exponer los parámetros de agregación** (`bucket_seconds`) para que ambos lados calculen el mismo `uuid5` (C6/V2). |

**Consecuencias**

- Acoplamiento: mínimo en el shape, pero acopla ambos lados a una **receta de derivación compartida** (namespace + campos exactos + parámetros de bucket).
- Trazabilidad / FK: id sintético; se pierde el vínculo a la fila física `rum_metric`.
- Footprint: ~0.
- Testabilidad: buena y determinista (C7/C9).
- Versionado / back-compat: `MetricBatchInput` no cambia; el cambio de FK es breaking para el contrato de BD y la receta pasa a ser una convención versionada.

**Evidencia que habla de M2**: C7/S9 (clave computada solo si no hay id durable; aquí sí existe, pero es de la fila, no de la serie), C6/S25 (la identidad incluye los parámetros de agregación), C9 (OpenAPI/JSON Schema y determinismo; variante de derivación reproducible).

**Impacto de owner**: adaptador + migración de FK de `ANOMALY` (**Romeo** + DB). Exponer `bucket_seconds` sería cambio de productor (**Federico**) si se elige esta vía.

---

### 3.3 M3 — Exponer filas crudas (con `metric_id` real)

**Qué cambia**

| Área | Cambio |
|---|---|
| Contrato (`MetricBatchInput`) | Sin cambios estructurales (`metric_id` con valor real). |
| Adaptador | Mapea filas crudas de `rum_metric` → `MetricBatchInput` (con `metric_id` físico). |
| Entidad `ANOMALY` | **Sin cambios**; FK preservada. |
| DDL / migración | **No** (usa la PK existente de `rum_metric`). |
| Productor (`src/api`) | **Sí** — nuevo endpoint/vista de `rum_metric` sin agregar (scope nuevo: S3-01 entregó solo agregados), con auth, límites y entrada OpenAPI. |

**Consecuencias**

- Acoplamiento: reintroduce acoplamiento a la **forma cruda** y a la volatilidad de su esquema (C2), aunque del lado del productor.
- Trazabilidad / FK: la mejor — `metric_id` real y FK intacta.
- Footprint: mayor payload hacia el proceso ML (filas crudas vs agregados); requiere acotar por rango para respetar < 2 GB RAM.
- Testabilidad: más pesada (endpoint nuevo + verificación de FK contra Postgres).
- Versionado / back-compat: endpoint aditivo (seguro, C11), pero suma superficie de mantenimiento y expone un shape más volátil.

**Evidencia que habla de M3**: C3/S4 (vistas de solo lectura legítimas para batch/reporting, como excepción acotada), C2 (acoplamiento al esquema crudo), C8/S10 (conserva referencia al origen).

**Impacto de owner**: endpoint productor = **Federico**; adaptador/consumo = **Romeo**. Es el único camino que preserva la FK sin migración, a costa de scope nuevo y acoplamiento.

---

### 3.4 M4 — Anclar la anomalía al bucket y quitar `metric_id` del input ML

**Qué cambia**

| Área | Cambio |
|---|---|
| Contrato (`MetricBatchInput`) | Elimina `metric_id`; la identidad es `(application_id, metric_type_id, timestamp, [bucket_seconds])`. |
| Adaptador | Mapeo directo desde `MetricAggregate` (que ya coincide) — transformación mínima o nula. |
| Entidad `ANOMALY` | Reemplaza `metric_id` por la clave de serie (columnas `application_id`/`metric_type_id`/`timestamp` o una tabla `metric_series` con id de serie). |
| DDL / migración | **Sí** — `ALTER TABLE anomaly`: quitar `metric_id` NOT NULL y su FK; agregar columnas/entidad de serie (migración nueva tipo `0004`). |
| Productor (`src/api`) | Sin cambios (el read path ya devuelve el shape del bucket); salvo exponer `bucket_seconds` si se incluye en la identidad. |

**Consecuencias**

- Acoplamiento: el más bajo — el contrato del dataset es el contrato del agregado; alinea con C13/C14 (definición de la serie separada de su materialización).
- Trazabilidad / FK: la anomalía referencia la **serie** (bucket), no una fila; soporta trazabilidad a la serie (C8) pero no el vínculo por fila.
- Footprint: ~0; no materializa filas.
- Testabilidad: buena (mapeo puro, sin derivación sintética); requiere tests de las columnas/entidad nuevas.
- Versionado / back-compat: cambio **breaking** de contrato de entrada ML + entidad `ANOMALY` + DDL (C11); exige bump de versión y coordinación de despliegue.

**Evidencia que habla de M4**: C5/S7 (Time Series ID compuesto), C6/S25 (la identidad es el conjunto completo de atributos; el bucket forma parte de la identidad), C7/S9 (clave determinista y estable), C13/C14/S17–S20 (definición de serie versionada y con owner), C8/S10 (preservar referencia al origen).

**Impacto de owner**: `MetricBatchInput`, entidad `ANOMALY` y migración = **dominio de Romeo** (+ DB). Federico documenta el contrato del dataset y expone `bucket_seconds` si aplica.

---

### 3.5 Comparación lado a lado

| Dimensión | M1 (nullable) | M2 (uuid5) | M3 (crudas) | M4 (bucket) |
|---|---|---|---|---|
| Cambia `MetricBatchInput` | Sí (nullable) | No | No | Sí (quita `metric_id`) |
| Cambia entidad `ANOMALY` | Sí | Forma no, valor sí | No | Sí |
| DDL / migración | Sí (drop NOT NULL) | Sí (FK) | **No** | Sí (drop FK + columnas serie) |
| Impacto productor `src/api` | No | Posible (`bucket_seconds`) | **Sí (endpoint nuevo)** | No / posible (`bucket_seconds`) |
| Preserva FK real | No | No | **Sí** | No (ancla a serie) |
| Preserva anclaje a la serie | Vía M4 (drift) | Parcial | Sí (fila, no serie) | **Sí** |
| Acoplamiento | Bajo/roto | Receta compartida | Alto (forma cruda) | **Mínimo** |
| Footprint < 2 GB | OK | OK | Mayor (crudas) | OK |
| Back-compat contrato ML | Breaking | No rompe shape | No rompe shape | **Breaking** |
| Dominio Romeo | Sí | Sí | No (adaptador) | Sí |

---

## 4. D4 — Frontera de implementación

### 4.1 Opción (a) — S3-04 incluye el reader/adaptador en `src/ml`

**Descripción**: S3-04 entrega, además del contrato y la exposición del productor, el cliente HTTP y el adaptador `MetricAggregate` → `MetricBatchInput` dentro de `src/ml`.

| Eje | Implicancia |
|---|---|
| Ownership / EDT | `src/ml` es dominio de Romeo; editarlo desde S3-04 viola "un módulo, un owner" salvo coautoría/revisión de Romeo. PR que cruza módulos. |
| Acoplamiento de PR | Un PR abarca `src/api` + `src/ml` → revisores de ambos; mayor riesgo de bloqueo y de conflictos. |
| Dueño de tests | Mixto: tests del reader en `src/ml` (Romeo), tests del productor en `src/api` (Federico). |
| Secuencia / dependencias | No depende de la disponibilidad de Romeo si hay coordinación; depende de la decisión D2 (contrato). |
| Riesgo de edición cross-módulo | Alto si Federico toca `src/ml` sin Romeo; el contrato es el árbitro. |

### 4.2 Opción (b) — S3-04 entrega solo contrato + exposición; reader como cambio de Romeo

**Descripción**: S3-04 cierra el lado productor (documento de contrato de dataset + formalización OpenAPI/interfaces; o nuevo endpoint si M3). El reader/adaptador se implementa como **cambio separado** en el dominio de Romeo.

| Eje | Implicancia |
|---|---|
| Ownership / EDT | Limpio: S3-04 en dominio de Federico; reader en dominio de Romeo. Respeta "un módulo, un owner". |
| Acoplamiento de PR | Dos PRs desacoplados; el contrato es la interfaz. Habilita paralelismo (EDT §6, contract-first). |
| Dueño de tests | Federico: contrato/productor. Romeo: reader. |
| Secuencia / dependencias | El contrato debe **congelarse** antes del reader; M1/M4 requieren además decisión de entidad/DDL (Romeo + DB). |
| Riesgo de edición cross-módulo | Bajo; riesgo residual = drift del contrato si no se congela ni versiona. |

---

## 5. Soporte a la decisión (no vinculante)

### 5.1 Lectura de la evidencia

- La identidad natural de una serie agregada es la **clave compuesta del bucket** (C5/S7, C6/S25); derivar un id sintético solo se justifica cuando el origen no tiene id durable (C7/S9) — y aquí el problema no es falta de id, sino que el id existente representa la **fila**, no la **unidad agregada**.
- Por eso la evidencia empuja conceptualmente hacia **M4** como el camino más limpio (contrato de serie versionado y con owner, C13/C14/S17–S20), asumiendo el costo de tocar contrato ML + entidad `ANOMALY` + DDL (dominio de Romeo).
- **M2** es el intermedio que conserva el shape de entrada, pero **no elimina** el problema del ancla: exige reemplazar la FK e impone una receta compartida que además debe incluir los parámetros de agregación (C6/V2).
- **M3** es el único que preserva la FK sin migración, pero es **scope nuevo** en el productor y reintroduce acoplamiento a la forma cruda (C2).
- **M1** sola no cierra: al nulear el FK deriva en M4.

**Recomendación no vinculante**: si el objetivo del modelo es detectar anomalías **por serie/bucket**, la opción alineada con la evidencia es **M4**; su costo es el cambio de contrato ML + entidad + DDL (Romeo). Si el objetivo requiere rastrear la anomalía a una **fila física** (explicabilidad por registro), **M3** es el único FK-preserving, asumiendo scope nuevo y acoplamiento. **M2** queda como compromiso solo si se acepta pagar la migración de FK. La decisión es de producto (Federico + Romeo + DB).

Para D4, la evidencia de la frontera (EDT §6, contract-first; `containers.md` §5.1) respalda **(b)**: publicar el contrato y la exposición en S3-04 y dejar el reader como cambio de Romeo. La opción (a) solo si se decide explícitamente coautorar `src/ml` con Romeo.

### 5.2 Preguntas para cerrar con Romeo

Cada pregunta indica las opciones que habilita.

1. **¿El modelo detecta anomalías por serie agregada (bucket) o por métrica cruda individual?** Define el terreno: serie → M4/M2; fila cruda → M3.
2. **¿La entidad `ANOMALY` (y su DDL) puede cambiar en esta fase, o es un contrato congelado?** Habilita M1/M2/M4 (requieren migración) vs M3 (única sin migración).
3. **¿La anomalía debe poder rastrearse a una fila física de `rum_metric`, o basta anclarla a la serie/bucket?** Fila → M3; serie → M4.
4. **¿Aceptás un `metric_id` sintético determinista (`uuid5`) que no existe en `rum_metric` (M2), o preferís quitar `metric_id` del input y anclar al bucket (M4)?**
5. **Si la identidad de la serie incluye los parámetros de agregación (`bucket_seconds`), ¿el read path debe exponerlos?** Afecta M2/M4 y al productor (`src/api`).
6. **¿Quién escribe el reader/adaptador: Romeo como cambio separado (D4-b) o Federico coordinado en S3-04 (D4-a)?**
7. **¿Se mantiene compatibilidad con `src/ml/mock_data.json` y `ml/data/generate_mock_dataset.py`, que hoy usan `metric_id`?** Impacta el costo de M1/M4 en el dominio ML.
8. **¿El entrenamiento queda en ISS-S3-05 (#44) y S3-04 cierra en "dataset + reader validado"?** Confirma el alcance funcional fijo.

---

## 6. Registro de decisión (para completar Federico + Romeo)

| Decisión | Opción elegida | Fecha | Quién |
|---|---|---|---|
| D2 — `metric_id` (M1 / M2 / M3 / M4) | _(pendiente)_ | | |
| D4 — frontera de implementación ((a) / (b)) | _(pendiente)_ | | |
| Observaciones / condiciones | | | |

---

## 7. Referencias

- `openspec/changes/ISS-S3-04/exploration.md` — estado, E1/E2/E3, M1–M4, D1–D6, R1–R7.
- `openspec/changes/ISS-S3-04/research.md` — evidencia S1–S28 / P1–P10; C1–C20; §5(b) matriz M1–M4.
- `src/ml/schemas.py` — `MetricBatchInput` (`metric_id` requerido).
- `docs/architecture/IsolationForest/ContratoEntradaSalida.md` — `ANOMALY` persiste `metric_id`.
- `openspec/specs/database/ddl_v1.0.sql:258-277` — `anomaly` (FK a `rum_metric`); `:163-195` — `rum_metric`.
- `openspec/specs/architecture/containers.md` §2.3 / §5.1 — footprint y aislamiento de módulos.
- `docs/adr/0003-ownership-tenant-read-path.md` — read path app-scoped; S3-04 mapea el agregado.
- `docs/business/EDT intellops.md` §5 (ownership) y §6 (contract-first).
