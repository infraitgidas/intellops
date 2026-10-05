# SPEC — ISS-S3-01: Persistencia de telemetría (verificación + hardening + read path)

**Tipo**: Delta spec. **Cambio**: ISS-S3-01 (GitHub #40). **Base**: proposal r1 (re-scope post-S2-03), exploración obs #215 (gap CRITICAL cross-tenant), investigación obs #216 (C2/C3/C4/C5/C6/C8), `openspec/specs/openapi.yaml:124-137` (`GET /metrics/query` operationId `queryMetrics`, `GET /metrics/list` `listMetrics`), `src/ml/schemas.py` (`MetricBatchInput`), config.yaml (CPU-only, < 2GB RAM, strict TDD).
**Alcance**: ownership de tenant en upsert de `user_session` y en correlación `metric_id` (cierra C2-C4), query repository app-scoped con agregación temporal y shape ML, endpoints `GET /metrics/query` + `GET /metrics/list` sin romper el contrato (openapi 124-137), tests de collision/replay (C5) y contadores de descartes por ownership. Sin DDL nuevo, sin rewiring de ML (S3-04).

## Capabilities

- **Nuevas**: `telemetry-query`
- **Modificadas**: `rum-ingest`, `openapi`

---

## 1. rum-ingest (Modificada) — Hardening de aislamiento + observabilidad

## ADDED Requirements

### Requirement: RUM-9 (ownership de sesión en upsert)

El upsert de `user_session` DEBE aplicar un predicado de ownership de tenant: por cada `session_id` del chunk, el repositorio DEBE resolver el `app_id` existente; un `session_id` que ya existe bajo OTRA aplicación NO DEBE persistirse ni servir de sesión para las filas del lote — las métricas y excepciones que lo referencian DEBEN descartarse y contarse en `ingest.session_foreign_total`. Un `session_id` del mismo tenant DEBE comportarse como hoy (`ON CONFLICT (session_id) DO NOTHING`, sin descarte ni contador). (Traceability: proposal In Scope §1; issue #40 criterio "Aplicación"; investigación C2/C3.)

#### Scenario: Replay cross-tenant (C5)

- GIVEN la sesión S persistida bajo la app A
- WHEN la app B envía métricas y excepciones con `session_id = S`
- THEN esas filas NO se persisten bajo A, `ingest.session_foreign_total` incrementa en el total descartado y los datos de A quedan intactos

#### Scenario: Reenvío del mismo tenant

- GIVEN la sesión S existente bajo la app A
- WHEN A reenvía eventos con `session_id = S`
- THEN el upsert es no-op, sin descarte y sin incremento de `ingest.session_foreign_total`

### Requirement: RUM-10 (correlación metric_id scoped por ownership)

La correlación de `js_exception.metric_id` DEBE filtrarse por ownership: solo DEBE reivindicarse un `metric_id` que exista Y pertenezca a la misma app/sesión del lote; en caso contrario DEBE persistirse `NULL` e incrementar el contador de fallback. (Traceability: proposal In Scope §2; investigación C4.)

#### Scenario: Reivindicación cross-app

- GIVEN la métrica M de la app A y una excepción de la app B con `metric_id = M`
- WHEN se persiste el chunk
- THEN `js_exception.metric_id` es `NULL` y el contador de correlación descartada incrementa

#### Scenario: Reivindicación legítima

- GIVEN la métrica M de la misma sesión del lote
- WHEN se persiste la excepción
- THEN `metric_id = M` se conserva y el contador no incrementa

### Requirement: RUM-11 (contadores de descartes por ownership)

Los contadores en proceso DEBEN exponer los descartes por ownership en `snapshot()` siguiendo el naming contract `ingest.` + `_total`: `ingest.session_foreign_total` (filas de métricas/excepciones descartadas por sesión extranjera) y el contador de correlación `metric_id` descartada (RUM-10). (Traceability: proposal In Scope §6 (SHOULD); investigación C3/C4; counters.py RUM-8.)

#### Scenario: Snapshot con descartes

- GIVEN un chunk con sesiones extranjeras y correlaciones cross-app
- WHEN se persiste el chunk y se toma `snapshot()`
- THEN ambos contadores reflejan los descartes y el resto de los keys existentes permanecen

---

## 2. telemetry-query (Nueva) — Query repository + endpoints

### Purpose

Read path app-scoped: query repository con agregación temporal en SQL (sin N+1, CPU-only) que produce el shape ML `(application_id, metric_type_id, timestamp, value, session_count)` (C6; `MetricBatchInput`) listo para consumir en S3-04.

### Requirement: TQ-1 (query repository app-scoped time-bucketed)

El query repository DEBE consultar únicamente filas cuyo `user_session.app_id` sea el tenant autenticado, agregando `rum_metric` por `metric_type_id` y bucket temporal (JOIN `user_session`→`rum_metric`, `GROUP BY`, `AVG(value)`, `COUNT(DISTINCT session_id)`); cada fila DEBE tener el shape `(application_id, metric_type_id, timestamp, value, session_count)`. La agregación DEBE ejecutarse en SQL, sin materializar filas en el proceso. (Traceability: proposal In Scope §3; issue #43 dependencia; investigación C6/C8.)

#### Scenario: Shape ML exacto

- GIVEN métricas de las apps A y B dentro del rango
- WHEN se consulta con tenant A, rango y bucket
- THEN el resultado contiene solo filas de A con los 5 campos y `session_count` correcto

#### Scenario: Agregación por bucket

- GIVEN métricas de un tipo distribuídas en 2 buckets temporales
- WHEN se consulta con ese bucket
- THEN se devuelve una fila por bucket con el promedio (`value`) y el `session_count` agregado

### Requirement: TQ-2 (recursos y límites)

La consulta DEBE acotarse: ventana temporal por defecto 15 minutos, máximo 7 días y bucket mínimo 60 s; DEBE apoyarse en los índices existentes (`idx_user_session_app_id`, `idx_rum_metric_session_timestamp`, `idx_rum_metric_metric_type_timestamp`) y DEBE responder en < 2 s para la ventana por defecto, CPU-only y sin dependencias nuevas (< 2GB RAM, config.yaml). (Traceability: config.yaml; investigación S13/C8.)

#### Scenario: Rango fuera de límite

- GIVEN una ventana mayor a 7 días o un bucket menor a 60 s
- WHEN se ejecuta la consulta
- THEN se rechaza con 400/422 y no se ejecuta la agregación

---

## 3. openapi (Modificada) — Endpoints de consulta

## ADDED Requirements

### Requirement: OAS-13 (contrato de consulta completado)

Los paths `GET /metrics/query` (operationId `queryMetrics`) y `GET /metrics/list` (`listMetrics`) DEBEN completar su declaración: `security: [apiKey]`, parámetros de query (`start`, `end`, `bucket`, `metric_type` en `/metrics/query`), respuestas 200 (shape ML en `/metrics/query`; catálogo en `/metrics/list`) y 401/403/422. Los operationIds y paths DEBEN permanecer intactos (no romper openapi 124-137). (Traceability: proposal In Scope §4; investigación S9:124-137; riesgo "romper contrato OpenAPI".)

#### Scenario: Contrato intacto

- GIVEN el documento con 124-137 completado
- WHEN schemathesis valida los paths de consulta
- THEN `queryMetrics`/`listMetrics` existen sin cambios de operationId y exigen `apiKey`

#### Scenario: Respuesta con shape ML

- GIVEN una apiKey válida y datos dentro del rango
- WHEN `GET /metrics/query`
- THEN 200 con filas `(application_id, metric_type_id, timestamp, value, session_count)` de la app autenticada

### Requirement: OAS-14 (read path app-scoped en runtime)

El router `metrics.py` DEBE exponer ambos GET aplicando `require_api_key`; el tenant DEBE derivarse exclusivamente de la key y NUNCA de un parámetro de request (no existe parámetro de aplicación). (Traceability: proposal Approach; IAUTH-2; investigación C1/C6.)

#### Scenario: Sin key

- GIVEN un request sin X-API-Key a `/metrics/query`
- WHEN se evalúa el guard
- THEN 401 `invalid_api_key` y ninguna consulta se ejecuta

#### Scenario: Aislamiento por key

- GIVEN la key de la app A y datos de A y B
- WHEN `GET /metrics/query`
- THEN la respuesta contiene únicamente datos de A

---

## Criterios de aceptación verificables

1. Tests TDD de collision/replay (C5): sesión de A reutilizada por B → filas de B descartadas + `ingest.session_foreign_total`; datos de A intactos.
2. Tests de correlación por ownership: `metric_id` cross-app → `NULL` + contador de fallback; reivindicación legítima conserva `metric_id`.
3. Tests de read path: query repo devuelve el shape ML exacto; `GET /metrics/query` + `GET /metrics/list` responden 200 con apiKey y app-scoped; openapi 124-137 intacto; Schemathesis verde.
4. `pytest` verde, cobertura ≥ 70% (`pytest --cov=src`); límites: CPU-only, < 2GB RAM, sin DDL nuevo; CHANGELOG + ADR actualizados.

## Next recommended

**design** — la fase design toma el predicado de ownership en `_upsert_sessions`/`_bulk_exceptions`, los DTOs y SQL del query repository, el router `metrics.py` y las declaraciones OAS-13/OAS-14 para definir arquitectura, secuencias y tareas.