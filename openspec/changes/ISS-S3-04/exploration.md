# EXPLORATION — ISS-S3-04: Dataset operativo para ML

**Cambio**: ISS-S3-04 (GitHub #43). **Base**: `feat/ISS-S3-04` sobre `origin/develop @ 1a46eb4`, con ISS-S3-01 (PR #57) mergeado (read path `GET /metrics/query` + `/metrics/list` listo). **Fuente de verdad**: `docs/business/issues-s2-s3.md` §ISS-S3-04. **Owners**: Federico + Romeo (módulo `src/ml` = dominio de Romeo → coordinar frontera). **Modo**: openspec (repo-local) + Engram (`discovery`). **Idioma**: español neutro técnico.

**Descripción del issue #43**: "Exponer los datos necesarios para el motor ML sin acoplarlo a la implementación interna de la ingesta." **Sin criterios de aceptación checkbox**: el entregable es la exposición del dataset operativo.

> **Nota de alcance**: la issue no prescribe mecanismo ni estructura. La exploración debe fijar (a) qué significa "dataset operativo", (b) la frontera/contrato entre el módulo de telemetría (Federico) y el módulo ML (Romeo), y (c) cómo se resuelve el desajuste de contrato documentado en ADR-0003 (`MetricAggregate` sin `metric_id` vs `MetricBatchInput` con `metric_id`).

---

## 1. Estado actual (código real, con evidencia)

### 1.1. Productor: read path de telemetría (ISS-S3-01, mergeado PR #57)

- `src/api/presentation/routers/metrics.py` — `GET /metrics/query` (operationId `queryMetrics`) y `GET /metrics/list` (`listMetrics`), ambos `Depends(require_api_key)`. El tenant se deriva **exclusivamente** de la key; no existe parámetro de aplicación en el request (OAS-14).
- `src/api/domain/repositories/query_repository.py:22-30` — `MetricAggregate = (application_id, metric_type_id, timestamp, value, session_count)`. **No tiene `metric_id`** (es una fila agregada: `AVG(value)` + `COUNT(DISTINCT session_id)` por bucket).
- `src/api/infrastructure/db/repositories/sqlalchemy_query_repository.py` — agregación EN SQL (una sentencia), bucket anclado al inicio de ventana.
- `src/api/domain/services/query_service.py` — límites TQ-2: ventana default 15 min, máximo 7 días, bucket mínimo 60 s, `start < end` → 422 `invalid_query_range`.
- `src/api/presentation/schemas/metrics.py` — `MetricAggregateOut` (espejo serializable).
- `openspec/specs/openapi.yaml` — paths `GET /metrics/query` y `GET /metrics/list` (~líneas 124-223) con `security: [apiKey]`, y `components/schemas/MetricAggregate` (~línea 1054) con `required: [application_id, metric_type_id, timestamp, value, session_count]`.

### 1.2. Consumidor: módulo ML (dominio de Romeo)

- `src/ml/schemas.py:6-13` — `MetricBatchInput` con `application_id: UUID4`, **`metric_id: UUID4` (requerido)**, `metric_type_id: int`, `timestamp: datetime`, `value: float`, `session_count: int`.
- `src/ml/pipeline/mock_reader.py` — `load_mock_data()` lee el **mock estático** `src/ml/mock_data.json` y valida cada item con `MetricBatchInput`. No hay lectura de datos reales.
- `src/ml/mock_data.json` — 2 registros, con `metric_id` presente.
- `src/ml/main.py` — app FastAPI con `/ml/status`; en `startup` solo lee el mock. No consume el read path.
- `src/ml/Dockerfile` + `src/ml/entrypoint.py` — **el contenedor `intellops-ai-engine` desplegado copia únicamente `entrypoint.py`** y ejecuta un loop `sleep` (placeholder); **no instala dependencias ni corre `main.py`**. Es decir: la app FastAPI de `src/ml` hoy solo se ejerce en tests (`tests/test_ml_worker.py`), no está desplegada.
- `ml/data/generate_mock_dataset.py` — generador sintético (dominio `ml/`, ISS-S3-05) que respeta `MetricBatchInput` **con `metric_id`**.

### 1.3. Contratos y salida del motor ML

- `docs/architecture/IsolationForest/ContratoEntradaSalida.md` — contrato de entrada (batch) **requiere `metric_id`**; el registro de salida `ANOMALY` **persiste `metric_id`** (FK a `rum_metric.metric_id`, ver `openspec/specs/database/ddl_v1.0.sql:260-270`). Por eso `metric_id` no es decorativo: la anomalía se ancla a una métrica física.
- `docs/architecture/IsolationForest/pipelinePropuesto.md` — el pipeline parte de `PostgreSQL: rum_metric` ("Consulta Batch") → Feature Engineering → Isolation Forest → ANOMALY → LLM → ALERT.

### 1.4. Reglas de frontera y ownership (evidencia dura)

- `docs/business/EDT intellops.md:1203-1213` — tabla de ownership: **`Dataset` = Federico**; `ML` = Romeo. `Federico` cubre la cadena `Collector → RUM → Exceptions → Normalization → Aggregation → Dataset` (L1152-1168); Romeo cubre `Dataset → Features → Model → ...` (L1172-1188).
- `docs/business/EDT intellops.md:40-42` — "Cada módulo tiene un único responsable técnico. Los demás integrantes pueden consumir ese módulo mediante interfaces y contratos definidos".
- `docs/business/EDT intellops.md:1219-1251` — **contract-first**: "se definirá un contrato de dataset en S1-S3" con un ejemplo JSON. **Drift**: el ejemplo usa `metric_type` (nombre, p.ej. "LCP") y un campo `error_count` que **no existen** en `MetricAggregate` (usa `metric_type_id` int) ni en `MetricBatchInput`.
- `openspec/specs/architecture/containers.md:116` (§5 regla 1) — **"Aislamiento de módulos (no cross-imports): el código de `intellops-ai-engine` no puede importar funciones, clases o modelos ORM definidos en `intellops-core`, y viceversa."** → descarta un módulo compartido que importe objetos de `src/api`.
- `openspec/specs/architecture/containers.md:34,79` — el C4/§2.3 declara `Rel(ai, db, "Read batch", "RUM_METRIC (read)")`: el diseño documentado es que el AI engine **lee `RUM_METRIC` directo de la DB** (solo lectura, prohibido escribir).
- `docs/adr/0003-ownership-tenant-read-path.md:43` + `openspec/changes/archive/2026-09-29-ISS-S3-01/design.md:95-100` — en cambio, ADR-0003 y el C4 del design S3-01 dicen: "ML Worker (S3-04, futuro) **consume `/metrics/query`** como dataset operativo (`MetricBatchInput`)". **Tensión de arquitectura: DB-directa (containers.md) vs HTTP read path (ADR-0003).**

### 1.5. ISS-S3-02 (normalización) NO es dependencia

El issue lista como dependencia única a ISS-S3-01. `ISS-S3-02` (#41, normalización/calidad) no está implementada. Por lo tanto el dataset expuesto consume los **valores canónicos almacenados** (el `AVG(value)` de `rum_metric`), sin asumir una capa de normalización posterior.

---

## 2. La brecha concreta

1. **No existe adaptador/cliente** que mapee `MetricAggregate` → `MetricBatchInput` (ADR-0003 lo declara explícitamente como trabajo de S3-04).
2. **No existe un "contrato de dataset operativo" documentado** (el EDT lo promete para S1-S3; solo hay un ejemplo informal con drift).
3. **El motor ML sigue leyendo el mock estático** (`mock_reader.py`); no hay consumo de datos reales.
4. **Desajuste de contrato clave**: `MetricBatchInput` exige `metric_id` (UUID de una fila `rum_metric` física), pero `MetricAggregate` es una fila **agregada** de muchas métricas → no hay un `metric_id` natural. Sin resolverlo, el mapeo es imposible tal cual.
5. **No hay mecanismo/configuración** para que el AI engine obtenga el dataset (base URL + credencial, o conexión DB, o export).

---

## 3. Enfoques (mecanismo de exposición del dataset)

| Enfoque | Descripción | Pros | Contras | Esfuerzo |
|---|---|---|---|---|
| **E1 — Pull HTTP del read path** (cliente + mapeo en `src/ml`; contrato de dataset documentado) | El AI engine consume `GET /metrics/query` con una `X-API-Key` y mapea `MetricAggregate` → `MetricBatchInput` en un adaptador propio | Desacopla del **interno de la ingesta** (solo depende del contrato público, que es justo lo que pide #43); reusa toda la inversión S3-01 (auth, agregación en SQL, límites TQ-2); sin cross-import (respeta containers.md §5.1); footprint 0 (no materializa); testable con `httpx.MockTransport` (unit) + httpx ASGI (integration) | Requiere config nueva en `src/ml` (base URL + API key); la key es **app-scoped** → un dataset multi-app necesita una key por app o credencial de servicio; hay que resolver el `metric_id`; agrega `httpx` al contenedor ML | **Medio** |
| **E2 — Export materializado** (Federico produce archivo/tabla; ML lo lee) | Un job del módulo de telemetría materializa un dataset (JSON/Parquet en volumen compartido, o tabla `dataset`/staging) que el AI engine lee | Snapshot reproducible y estable (bueno para EDA/reproducibilidad FAIR); desacopla el runtime ML del core | Productor nuevo (job/proceso) + artefacto/estado nuevo; **staleness** (latencia de refresco); si es tabla → DDL nuevo (fuera de las restricciones de "sin migración" de la cadena); footprint de disco; duplica el problema del `metric_id` | **Medio-Alto** |
| **E3 — Lectura directa de `RUM_METRIC` desde la DB** (lo que hoy documenta containers.md) | El AI engine conecta a PostgreSQL y lee `rum_metric` (batch, solo lectura) y hace su propio feature engineering | Es el diseño vigente en `containers.md` (C4/§2.3); es la fuente de verdad; permite a Romeo features sobre filas **crudas** (con `metric_id` real → resuelve el `ANOMALY.metric_id`) | Acopla ML al **esquema de almacenamiento** (internos de la ingesta) — choca de frente con "sin acoplarlo a la implementación interna de la ingesta"; duplica la lógica de agregación/scoping multi-tenant (que S3-01 ya resolvió); sin auth de contrato (acceso DB directo); contradice ADR-0003 | **Medio** |

**Descartado — Módulo compartido read-only** (importar `MetricAggregate` desde `src/ml`): viola `containers.md` §5.1 (prohibido cross-import core↔ai-engine) y la regla "un módulo, un owner" del EDT. No es viable sin romper la constitución del repo.

---

## 4. El gap de `metric_id` (decisión de contrato)

`MetricBatchInput.metric_id` es requerido y `ANOMALY.metric_id` es FK a `rum_metric`. Opciones:

| Opción | Descripción | Implicancia |
|---|---|---|
| **M1 — `metric_id` opcional en el dataset agregado** | Relajar `MetricBatchInput.metric_id` a `UUID4 | None`; la fila agregada no lo trae | Cambia el contrato de entrada ML (dominio Romeo); `ANOMALY.metric_id` necesitaría re-anclarse a la clave del bucket `(application_id, metric_type_id, timestamp)` o quedar nullable → cambio de entidad/DDL de ML |
| **M2 — `metric_id` sintético determinista** | Derivar `uuid5(namespace, app+type+bucket)` por fila agregada, manteniendo el campo requerido | No cambia `MetricBatchInput`; la trazabilidad de la anomalía apunta a un id sintético (no a una fila física) → pierde el FK real |
| **M3 — Exponer filas crudas (con `metric_id`) además del agregado** | Nuevo endpoint/vista de `rum_metric` sin agregar | Preserva `metric_id` real y el FK de `ANOMALY`; pero es scope nuevo (S3-01 entregó solo agregados) y materializa filas hacia EL proceso ML (footprint) |
| **M4 — Quitar `metric_id` de la entrada ML y anclar la anomalía al bucket** | El contrato ML pasa a identificar la serie por `(application_id, metric_type_id, timestamp)` | Conceptualmente el más limpio para datos agregados; pero es un **cambio de contrato de entrada y de la entidad ANOMALY** (dominio Romeo + posible DDL) |

No hay decisión tomada; **requiere confirmación de Federico + Romeo** (es la decisión bloqueante principal).

---

## 5. Áreas afectadas (proyección)

| Área | Afectación | Owner |
|---|---|---|
| `src/ml/pipeline/` (nuevo cliente/reader real + adaptador `MetricAggregate`→`MetricBatchInput`) | Nuevo | **Romeo** (coordinar) |
| `src/ml/schemas.py` (`metric_id` según M1/M2/M4) | Modificado | **Romeo** |
| `src/ml/config` (nuevo: base URL + API key del core) | Nuevo (si E1) | **Romeo/Federico** |
| `src/ml/requirements` / `Dockerfile` (httpx u otra dep; hoy el contenedor no instala nada) | Modificado (si E1/E3) | **Romeo** |
| `src/api/**` (productor) | Probablemente **sin cambios** (read path S3-01 ya expone el shape); solo si M3 necesita endpoint crudo | Federico |
| `docs/architecture/...` (documento de **contrato de dataset operativo**) | Nuevo | Federico + Romeo |
| `openspec/specs/architecture/interfaces.md` (§2.1 ML Engine API) + `components.md` | Modificado (formalizar el contrato) | Federico |
| `docs/adr/` (ADR de reconciliación: DB-directa vs HTTP read path) | Nuevo | Federico + Romeo |
| `tests/` (unit del mapper con `httpx.MockTransport`; integration contra `GET /metrics/query`; ML reader) | Nuevo/Modificado | Federico + Romeo |
| `CHANGELOG.md` | Modificado | Federico |

---

## 6. Recomendación

**E1 (pull HTTP del read path) + contrato de dataset documentado**, con estos puntos fijos:

1. **El read path S3-01 es el mecanismo de desacoplamiento** que pide #43: el ML depende del **contrato público** (`MetricAggregate`), no de los internos de la ingesta (tablas, validación, upsert). Es la opción que mejor respeta el enunciado y evita el cross-import prohibido por `containers.md` §5.1.
2. **Definir el "contrato de dataset operativo"** como documento (`docs/architecture/`) + formalizarlo en `interfaces.md` §2.1: el shape canónico es `MetricAggregate` (5 campos); el adaptador a `MetricBatchInput` vive del lado consumidor (Romeo).
3. **Resolver el `metric_id` (sección 4) antes de proponer** — decisión Federico + Romeo; impacta `MetricBatchInput`, el adaptador y posiblemente `ANOMALY`.
4. **Config del AI engine**: `INTELLOPS_API_BASE_URL` (p. ej. `http://intellops-core:8000` dentro de `intellops-net`) + credencial. Documentar si el dataset es **por app** (key por app) o requiere **credencial de servicio transversal** (decisión, ver D3).
5. **Coordinar con Romeo la frontera**: la edición de `src/ml/**` es de su dominio; el cambio se implementa como **par productor/consumidor** (Federico expone/documenta, Romeo consume), con el contrato como árbitro.
6. **Tests (strict TDD)**: unit puros del adaptador (sin DB ni red, con `httpx.MockTransport`) + integration del reader contra `GET /metrics/query` (patrón `httpx.AsyncClient` existente en `tests/`); no se requiere Postgres para el mapeo puro.

Alternativa si el equipo prioriza la fidelidad al diseño vigente: **E3 (DB directa)**, pero requiere un **ADR que revierta explícitamente** la regla de "sin acoplar a la ingesta" y reconcilie `containers.md` con ADR-0003; además duplica la lógica multi-tenant que S3-01 ya resolvió. **E2** queda para un follow-up de reproducibilidad/EDA, no para el MVP de S3-04.

---

## 7. Riesgos

- **R1 — Tensión de arquitectura no resuelta (Alto)**: `containers.md` (DB-directa) vs ADR-0003/design S3-01 (HTTP read path). Sin un ADR que la resuelva, dos implementaciones divergen. **Requiere decisión.**
- **R2 — `metric_id` sin dueño claro (Alto)**: el contrato ML y la entidad `ANOMALY` dependen de él; la decisión M1-M4 toca el dominio de Romeo (y posiblemente DDL). Bloquea el mapeo.
- **R3 — Frontera de ownership (Medio)**: el rewiring del reader vive en `src/ml` (Romeo). Sin coordinación, riesgo de que Federico modifique el módulo de Romeo (viola EDT Regla 3) o de bloqueo cruzado.
- **R4 — Dataset multi-app con key app-scoped (Medio)**: `GET /metrics/query` autoriza una sola app por key; un dataset global de entrenamiento necesita varias keys o credencial de servicio → decisión de seguridad.
- **R5 — Alcance difuso (Medio)**: la issue no tiene criterios checkbox; sin acotar (¿solo exponer+reader, o también entrenamiento/EDA?), S3-04 puede solaparse con ISS-S3-05 (#44, Romeo) y con el entrenamiento del modelo.
- **R6 — Drift de contrato EDT (Bajo)**: el ejemplo del EDT (`metric_type` por nombre, `error_count`) no coincide con los schemas reales (`metric_type_id`, sin `error_count`). Actualizar el contrato documentado para eliminar la ambigüedad.
- **R7 — El contenedor ML no está operativo (Bajo)**: `intellops-ai-engine` corre un placeholder; el "rewiring" no tiene un runtime desplegado que romper, pero tampoco existe la infra para probarlo end-to-end en compose.

---

## 8. Preguntas abiertas (decisiones ANTES de proponer)

- **D1 — Mecanismo de exposición**: ¿E1 (pull HTTP del read path), E3 (lectura directa de `RUM_METRIC` desde la DB, como hoy documenta `containers.md`) o E2 (export materializado)? Define si se crea un ADR que reconcilia `containers.md` con ADR-0003.
- **D2 — `metric_id`**: ¿M1 (opcional), M2 (sintético determinista), M3 (exponer crudas), o M4 (anclar la anomalía al bucket y quitar `metric_id` del input ML)? Impacta `MetricBatchInput`, `ANOMALY` y posible DDL.
- **D3 — Alcance del dataset**: ¿una aplicación por key (el AI engine recibe/configura una key por app) o una credencial de servicio transversal para todas las apps? ¿Y el AI engine consume un tenant o todos?
- **D4 — Frontera de implementación**: ¿S3-04 incluye el código del reader en `src/ml` (Romeo, coordinado) o solo el contrato + la exposición del productor, dejando el reader a un cambio de Romeo?
- **D5 — Alcance funcional**: ¿S3-04 termina en "dataset exponible + reader validado" (sin entrenamiento) y deja entrenamiento/EDA a ISS-S3-05 (#44)/issues ML posteriores?
- **D6 — Cadencia/ventana**: ¿el dataset es un pull puntual bajo demanda o una ventana deslizante (p. ej. 15 min/7 d de TQ-2) para features temporales? Define parámetros de config.

## Ready for Proposal

**Sí, con confirmación previa de D1..D6** (la principal: D1 + D2, que son de arquitectura/contrato y tocan ownership de Romeo). La exploración deja identificado: el productor ya existe (read path S3-01 merged, con evidencia de archivos), el consumidor sigue en mock, la regla de aislamiento que descarta el módulo compartido, la tensión `containers.md` vs ADR-0003, el gap de `metric_id`, las tres opciones de mecanismo con tradeoffs, y las áreas/owners afectados. El orquestador debe llevar D1..D6 a Federico + Romeo antes de lanzar `sdd-propose`.
