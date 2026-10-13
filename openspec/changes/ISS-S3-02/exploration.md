# EXPLORATION — ISS-S3-02: Normalización y calidad de datos

**Cambio**: ISS-S3-02 (GitHub #41). **Sprint**: S3. **Owner**: Federico. **Prioridad**: Alta.
**Base**: `feat/ISS-S3-02` off `origin/develop` @ `1a46eb4` (ISS-S2-03 PR #55 mergeado; ISS-S3-01 PR #57 mergeado).
**Fuente de verdad**: `docs/business/issues-s2-s3.md` (issue #41, líneas 171-191).
**Store**: openspec (repo-local). **Idioma**: español neutro técnico.

---

## Planteo del problema

El issue #41 pide implementar el flujo de normalización `Raw → Validation → Normalization → Storage` y satisfacer cinco criterios de calidad: resolver inconsistencias de timestamp, resolver inconsistencias de unidad, resolver inconsistencias de nombres, manejar valores ausentes y manejar valores inválidos.

Hoy la ruta de ingesta tiene **Validation** y una normalización *de facto* dispersa e implícita:
- Una política de validación dedicada rechaza eventos por evento con 7 códigos (`src/api/domain/services/ingest_policy.py`).
- El `_build_rows`/`_parse_ts` del worker (`src/api/infrastructure/ingest/queue.py`) es el único lugar que hace coerción de representación (parseo ISO, `float()`, nombre→id de catálogo, fallback `now()`), y vive en el **worker de infraestructura**, no en una etapa de normalización con nombre.
- **No existe** ningún módulo `normaliz*.py` / `transform*.py` en `src/api`. `components.md:72` planifica un `transformers.py` "Normalization, scaling, encoding", pero eso pertenece al **motor de ML** (`src/ml/features/`), no a la ingesta.

Así, la brecha no es "no existe coerción" sino "la coerción es implícita, dividida entre la validación (rechazo) y el worker (reparación-o-fallback), e inconsistente con la etapa de pipeline con nombre del issue". La normalización no tiene un único responsable, no es testeable por unidad de forma aislada, y no puede resolver inconsistencias de unidad/nombre porque la validación las rechaza primero.

**Restricción de diseño crítica descubierta en el contrato**: `docs/architecture/ContratoIngestaRUM.md:30` establece que los rangos de sanity son cotas de **rechazo**, no cotas de calidad — "un TTFB de 9000ms es un dato legítimo que el sistema acepta; es justamente el valor que el sistema debe detectar como anomalía". Por lo tanto la normalización DEBE limitarse a **representación** (zona horaria, alias de unidad, capitalización/alias de nombre, defaults opcionales ausentes) y NUNCA DEBE recortar/reparar magnitudes, o destruye la señal de anomalía del ML.

---

## Estado actual

### 1. Capa de validación (existe, rechazo estricto)

`src/api/domain/services/ingest_policy.py` — puro, sin E/S, orden determinista (`:1-11`):
- 7 códigos de rechazo (`:18-28`): `missing_required_field`, `invalid_uuid`, `invalid_metric_type`, `invalid_unit`, `invalid_range`, `invalid_timestamp`, `oversized_event`.
- `METRIC_TYPES` (`:30-32`) = exacto `{TTFB, FCP, XHR_LATENCY, JS_EXCEPTION_RATE, RAGE_CLICK}`.
- `VALID_UNITS` (`:33`) = `{ms, count}`; `UNIT_BY_TYPE` (`:34-40`) exige coherencia exacta; `RANGE_BY_TYPE` (`:42-48`) cotas de sanity.
- `_is_timestamp` (`:73-87`) acepta solo datetime con tz o ISO-8601 con tz explícita; naïve/basura → `invalid_timestamp`.
- `_validate_metric` (`:114-132`): el chequeo de coherencia de unidad en `:125-126` es de **solo rechazo** — sin conversión.
- `validate_rum_event` (`:135-157`) / `validate_js_exception` (`:160-186`).

### 2. Esquema de envelope (envelope estricto, evento laxo)

`src/api/presentation/schemas/ingest.py`: envelope estricto (`schema_version ^1\.0$`, 1..500 eventos, `:37-41` / `:57-61`); evento intencionalmente laxo para que la política por evento produzca rechazo parcial `202` en lugar de un `422` de todo el lote (`:3-9`). `RumMetric.value: float` (`:18`) y `unit: str` (`:19`) — sin enum en la capa Pydantic.

### 3. Lo más cercano a la normalización (worker de infraestructura)

`src/api/infrastructure/ingest/queue.py`:
- `_build_rows` (`:235-287`): mapea los payloads encolados a filas de BD. `float(metric["value"])` (`:266`), el string de tipo de métrica se preserva (`:265`), precedencia de timestamp `metric.timestamp or payload.timestamp` (`:260`).
- `_parse_ts` (`:290-301`): parseo ISO con `Z`→`+00:00`, naïve → `None`.
- Fallback `datetime.now(timezone.utc)` para timestamps no parseables en `:254`, `:268`, `:282` — **la única "reparación" hoy**, y para eventos aceptados es casi código muerto porque la política ya garantiza timestamps con tz parseables.
- Corre dentro del worker async después del `202`; las fallas aquí van a la dead-letter (`:225-232`), invisibles al cliente.

`src/api/domain/services/ingest_service.py:38-90`: valida por evento (`:61`) y luego encola solo lo aceptado (`:75-83`). Sin paso de normalización.

### 4. Expectativas de almacenamiento

`openspec/specs/database/ddl_v1.0.sql`:
- Catálogo `metric_type` (`:15-20`) sembrado con los 5 tipos (`:324-330`).
- `rum_metric.unit TEXT NOT NULL` (`:168`) — texto libre, sin enum en la BD.
- `js_exception.error_type TEXT NOT NULL` (`:205`) — **sin catálogo**; el contrato lista ejemplos `TypeError, ReferenceError, RangeError, UnhandledRejection, Other` (`ContratoIngestaRUM.md:36`).
- `sqlalchemy_ingest_repository.py:209-219` `_metric_type_id` resuelve nombre→id con `scalar_one()` (match exacto; lanza si no existe) y cachea por nombre.

### 5. Contrato (OpenAPI)

`openspec/specs/openapi.yaml`:
- Enum `RumMetric.type` (5 valores, `:945-948`); enum `unit` **`[ms, count]`** (`:953-956`); `value ≥ 0` (`:949-951`).
- `JsExceptionEvent.error_type` es un `string` libre maxLength 100 (`:987-990`) — sin enum.
- `/telemetry/metrics` y `/telemetry/exceptions` declaran `202/400/401/403/503/429` (`:24-123`); `security: [apiKey]`.

### 6. Decisiones ya registradas

- `docs/adr/0002-pipeline-ingesta-async.md`: cola async en proceso, `202` al encolar, dead-letter ante errores permanentes.
- `openspec/changes/archive/2026-09-29-ISS-S3-01/proposal.md:30`: difirió explícitamente **"Normalización de error_type a catálogo (ISS-S3-02, #41)"** → la normalización de error_type está en alcance de este cambio.
- `docs/business/EDT intellops.md:559-564` §3.3 "Normalización": *convertir unidades, validar timestamps, normalizar nombres de métricas, remover o marcar payloads inválidos* — los cinco criterios del issue son la expresión concreta de esto.
- `docs/business/issues-s2-s3.md:254` (ISS-S3-06) espera *"cobertura sobre normalización / transformaciones"* → la nueva etapa debe ser testeable por unidad.
- `openspec/specs/architecture/components.md:72`: `transformers.py` se planifica bajo `src/ml/features/` (feature engineering de ML), **no** en la ingesta — no confundir ambos.

### 7. Verificación de auditoría previa

La auditoría previa queda confirmada: unidades de solo rechazo, timestamps de rechazo-o-fallback, `error_type` sin catalogar, sin módulo de normalización, sin carpeta S3-02. Un matiz: `_parse_ts`/`_build_rows` **es** normalización parcial, solo que mal ubicada (infraestructura, post-202) y sin nombre.

---

## Criterios de aceptación → estado actual → opciones de normalización

| # | Criterio | Hoy | Opción de normalización (dirección recomendada) |
|---|-----------|-------|----------------------------------------------|
| 1 | Inconsistencias de timestamp | `_is_timestamp` rechaza naïve/basura; `_parse_ts` parsea ISO; fallback `now()` | Canonicalizar todo timestamp aceptado a UTC con tz (idempotente); heredar el ts del envelope cuando falta el ts de la métrica; mantener el rechazo solo para no parseables/sin tz. Decidir la política de clock skew (recortar vs aceptar). |
| 2 | Inconsistencias de unidad | Solo rechazo (`invalid_unit`, `:125-126`); sin conversión | Convertir alias conocidos a la unidad del contrato para métricas con tipo sanity (p. ej. `s`→`ms` ×1000, `ms`/`count` idempotentes). **Decisión de semántica de contrato** (acepta entrada antes rechazada). Mantener rechazo estricto para unidades desconocidas. |
| 3 | Inconsistencias de nombres | `type` match exacto (`:122-123`); `error_type` texto libre; resolución de catálogo exacta (`repo :218`) | Canonicalizar nombres de tipo de métrica (trim/case + mapa de alias explícito, p. ej. `ttfb`→`TTFB`); canonicalizar `error_type` (trim/case + mapear desconocido → `Other`) con catálogo opcional en BD. |
| 4 | Valores ausentes | Requerido → rechazar; opcional heredar (ts de métrica, `page_url`, `stack_trace`, `metric_id`, `user_agent`) | Formalizar defaults/herencia de opcionales como un paso de normalización explícito; decidir si un `unit` ausente se infiere del tipo o se sigue rechazando. |
| 5 | Valores inválidos | Rechazo vía 7 códigos; coerción `float()` en el worker | Reparar solo **representación** (coerción de cadenas numéricas, trim); NUNCA recortar magnitudes/fuera de rango (contrato: los límites de sanity son de rechazo, no de calidad). Los valores semánticamente inválidos siguen rechazados. |

**Tensión de orden**: el diagrama del issue es `Raw → Validation → Normalization → Storage`, pero si la validación corre primero y rechaza las inconsistencias de unidad/nombre, la normalización nunca puede resolverlas. Para hacer alcanzables los criterios 2 y 3, la normalización debería ser una etapa de **canonicalización laxa pre-validación**; la validación sigue siendo la autoridad única de rechazo → flujo efectivo `Raw → Normalize → Validate → Enqueue → Store`.

---

## Áreas afectadas

- `src/api/domain/services/ingest_normalizer.py` — **NUEVO**: funciones puras de normalización (timestamp/unidad/nombre/ausente/representación inválida), sin E/S.
- `src/api/domain/services/ingest_service.py` — insertar el paso de normalización antes de la validación/encolado (`:59-83`).
- `src/api/domain/services/ingest_policy.py` — la validación interactúa con la entrada normalizada; puede necesitar registros compartidos de unidad/tipo (`:30-48`) para evitar duplicación.
- `src/api/infrastructure/ingest/queue.py` — `_build_rows`/`_parse_ts` (`:235-301`) deberían consumir payloads canónicos y eliminar la lógica de fallback duplicada.
- `src/api/infrastructure/db/repositories/sqlalchemy_ingest_repository.py` — `_metric_type_id` (`:209-219`) si cambia el alias de nombres/catálogo.
- `src/api/presentation/schemas/ingest.py` — solo si se introduce tipado DTO normalizado.
- `openspec/specs/openapi.yaml` — solo si se amplían las unidades/nombres aceptados (`:945-956`).
- `openspec/specs/database/ddl_v1.0.sql` + una migración (`.../versions/0004_*.py`) — solo si `error_type` pasa a ser un catálogo real.
- `docs/architecture/ContratoIngestaRUM.md`, `PipelineIngestaRUM.md` — documentar la etapa de normalización y el flujo.
- `tests/test_ingest_telemetry.py` (deltas de contrato/comportamiento) y **NUEVO** `tests/test_ingest_normalizer.py` (unidad, sin BD).
- `CHANGELOG.md` + un nuevo ADR para la decisión de normalizar-antes-de-validar.

---

## Enfoques

1. **Etapa de normalización de dominio pura antes de la validación/encolado** (recomendado)
   - Nuevo `domain/services/ingest_normalizer.py` con funciones puras; `IngestService` normaliza el payload crudo, luego la política existente valida el evento canónico, y luego el encolado almacena el payload canónico.
   - Pros: un único responsable de la normalización; puro → testeable por unidad de forma aislada (satisface TDD estricto y S3-06); las fallas de normalización se exponen como rechazos por evento, preservando la semántica parcial `202`; mantiene limpio el layering dominio/infraestructura; elimina la coerción duplicada del worker.
   - Contras: toca la ruta de request (CPU despreciable); ampliar la entrada aceptada es una decisión de semántica de contrato; debe garantizarse la idempotencia.
   - Esfuerzo: **Medio**

2. **Extraer la normalización al worker de infraestructura** (refactor de `_build_rows`)
   - Mover `_parse_ts` + el mapeo de nombre/unidad a `infrastructure/ingest/normalizer.py`; dejar la ruta de request sin cambios.
   - Pros: cambio mínimo en la ruta de request; es donde ya vive el parseo; a nivel de lote.
   - Contras: la normalización corre **después** del `202`, por lo que las fallas/reparaciones son invisibles al cliente y alimentan la dead-letter; las reglas de negocio (unidades/tipos) se filtran a infraestructura; mala testeabilidad por unidad pura; no satisface limpiamente "etapa de normalización".
   - Esfuerzo: **Bajo–Medio**

3. **Normalizar en el límite de escritura (repositorio) + coerción fina en el esquema**
   - Normalizar al resolver ids de catálogo e insertar filas.
   - Pros: lo más cercano al almacenamiento.
   - Contras: los repositorios no deben contener reglas de negocio; solo tests atados a la BD; mezcla responsabilidades; no puede reportar rechazos; viola el patrón existente de reglas-en-dominio.
   - Esfuerzo: **Medio** (pero capa incorrecta)

---

## Recomendación

**Enfoque 1**, acotado de la siguiente manera.

**Alcance recomendado para ISS-S3-02 (en alcance)**
- Nuevo `ingest_normalizer` puro invocado en la ruta de request **antes** de la validación; la validación sigue siendo la autoridad única de rechazo.
- Timestamp: canonicalizar a UTC con tz (idempotente); heredar el timestamp del envelope cuando falta el timestamp de la métrica.
- Unidad: conversión acotada alias→canónica para los 5 tipos sanity (objetivo canónico `ms`/`count`), idempotente; unidades desconocidas aún rechazadas.
- Nombres: canonicalizar nombres de tipo de métrica (trim/case + mapa de alias explícito); canonicalizar `error_type` (trim/case, mapear desconocido → `Other`).
- Valores ausentes: defaults/herencia explícitos para campos opcionales; mantener el rechazo de campos requeridos.
- Valores inválidos: reparar solo representación (coerción de cadenas numéricas, espacios en blanco); nunca recortar magnitudes.
- TDD estricto: tests de unidad puros por criterio + tests de comportamiento sobre `/telemetry/*`; documentar el flujo.

**Fuera de alcance (se recomienda diferir)**
- Recortar/reparar valores fuera de rango (destruiría la señal de anomalía).
- Catálogo en BD + migración para `error_type` (salvo que Q3 resuelva a catálogo; entonces es un sub-alcance explícito con mapeo de backfill).
- Backfill/replay de eventos ya rechazados (la normalización es solo hacia adelante salvo pedido explícito).
- Cualquier cambio a la semántica de envelope/`202`/backpressure.

---

## Riesgos

- **R1 — Cambio de semántica de contrato (Alto)**: aceptar `s`→`ms` y alias de nombres convierte entradas antes rechazadas en aceptadas. Retrocompatible para clientes pero cambia la semántica documentada y las expectativas de Schemathesis/contrato. Mitigar mediante decisión explícita (Q1/Q8) y OpenAPI actualizado si se amplía.
- **R2 — Destruir la señal de anomalía (Alto)**: cualquier recorte/reparación de magnitudes (p. ej. limitar el TTFB de 9000ms) contradice `ContratoIngestaRUM.md:30` y rompe el objetivo del ML. Regla dura: solo representación.
- **R3 — El catálogo de `error_type` requiere DDL (Medio)**: un catálogo real implica una migración, datos semilla y un mapeo para las filas de texto libre existentes. La canonicalización en código (map→`Other`) evita DDL y tiene menor riesgo. Decisión de alcance (Q3).
- **R4 — Idempotencia (Medio)**: la conversión de unidad no es idempotente si se aplica dos veces (p. ej. `1000 ms` reinterpretado como `1 s`). El normalizador debe ser idempotente y marcar/evitar la doble aplicación; testear explícitamente.
- **R5 — Ambigüedad del orden del pipeline (Medio)**: el diagrama del issue ubica Validation antes de Normalization, lo que hace inalcanzables los criterios 2/3. Requiere una decisión explícita (Q2) registrada en el design/ADR.
- **R6 — Semántica de placeholder/fallback (Medio)**: hoy se usa `now()` para timestamps no parseables. La normalización debe definir si un timestamp ausente/inválido se repara (fallback) o se rechaza; un `now()` silencioso puede corromper el análisis temporal.
- **R7 — Duplicación del conocimiento de negocio (Bajo–Medio)**: los registros de unidad/tipo viven hoy en `ingest_policy.py`; el normalizador debe reutilizarlos (fuente única) o ambos divergirán.
- **R8 — Interacción cola async / dead-letter (Bajo)**: si la normalización queda post-encolado (Enfoque 2), los eventos reparados/rechazados solo aparecen en la dead-letter; el Enfoque 1 evita esto.
- **R9 — Estrictez de OpenAPI vs flexibilidad del servidor (Bajo)**: si el contrato mantiene `unit enum [ms, count]` mientras el servidor acepta alias, el contrato documentado y el comportamiento en runtime divergen.

---

## Preguntas abiertas (requieren decisión antes de la propuesta)

- **Q1 — Significado del criterio de unidad**: ¿"resuelve inconsistencias de unidad" significa **conversión** (aceptar `s`, almacenar `ms`) según EDT §3.3, o rechazo estricto con códigos más claros? Si es conversión: ¿qué alias están en el conjunto aceptado?
- **Q2 — Orden**: ¿normalizar **antes** de la validación (canonicalización laxa; hace alcanzables los criterios 2/3) o después (diagrama literal del issue)? Se recomienda antes.
- **Q3 — Profundidad de `error_type`**: ¿canonicalización en código con fallback `Other` (sin DDL), o un catálogo real en BD (tabla `error_type` + migración + backfill)?
- **Q4 — `unit` ausente**: ¿inferir del tipo de métrica, o mantener el rechazo `missing_required_field`?
- **Q5 — Coerción de cadenas numéricas**: ¿reparar `value: "120.5"` → `120.5`, o rechazar?
- **Q6 — Clock skew / timestamps futuros**: ¿recortar, aceptar o rechazar? (Recortar arriesga ocultar anomalías.)
- **Q7 — Contrato de idempotencia**: ¿la doble normalización está prohibida, tolerada (idempotente) o detectada?
- **Q8 — OpenAPI**: ¿ampliar las unidades/nombres aceptados documentados, o mantener el contrato estricto y tratar la flexibilidad del servidor como no documentada?
- **Q9 — Interacción con el read path**: ¿la normalización es solo de ingesta, o también toca el read path / la exportación del dataset de S3-04?

---

## Ready for Proposal

**Sí, condicionalmente** — después de que el usuario/orquestador resuelva Q1–Q3 (como mínimo Q1 semántica de unidad, Q2 orden, Q3 profundidad de `error_type`), que determinan si este cambio es una etapa de dominio pura y acotada o también incluye una migración DDL y una ampliación del contrato OpenAPI. La exploración dejó fijados: el estado actual con evidencia de archivos, la brecha por criterio, el flujo de normalizar-antes-de-validar, tres enfoques con uno recomendado, y la restricción dura de que la normalización nunca debe reparar magnitudes.

## Next recommended

**propose** — llevar el alcance recomendado (Enfoque 1, acotado), las decisiones Q1–Q3 y la lista de módulos afectados a `sdd-propose` para escribir intención/alcance/rollback, luego `sdd-spec` para los requisitos delta (Given/When/Then por criterio) y `sdd-design` para la secuencia de normalizar-antes-de-validar.
