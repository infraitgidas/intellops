# SPEC — ISS-S2-03: Ingesta RUM asíncrona

**Tipo**: Delta spec. **Cambio**: ISS-S2-03 (GitHub #37). **Base**: proposal r1 (decisiones D1–D6), exploration §1–§4, `openspec/specs/openapi.yaml` (paths `/metrics/ingest` y `/logs/ingest` sin `security`; scheme `apiKey` declarado; schemas `RumEventBatch`/`JsExceptionBatch`/`IngestResponse`/`ErrorResponse`), `docs/architecture/PipelineIngestaRUM.md` (§2 política, §3 cola, §3.4 semántica 202) y `ContratoIngestaRUM.md` (matrices de validación).
**Alcance**: handlers `POST /telemetry/metrics` y `POST /telemetry/exceptions` con `Depends(require_api_key)` (IAUTH-5), validación envelope→400 (D5) y por evento→202 parcial, cola asíncrona acotada + workers (E1), backpressure 503 `queue_full`, persistencia a BD (D1), drenado en shutdown (D6), observabilidad mínima (D4) y nomenclatura definitiva `/telemetry/*`. Strict TDD (config.yaml apply.tdd:true): cada escenario Given/When/Then se convierte en test red antes de implementar.

## Capabilities

- **Nuevas**: `rum-ingest`
- **Modificadas**: `openapi`, `ingest-auth`, `architecture`

---

## 1. rum-ingest (Nueva)

### Purpose

Pipeline de ingesta RUM: endpoints autenticados por API key, validación de dos niveles (envelope → 400; evento → 202 parcial), cola en proceso acotada con backpressure, persistencia asíncrona a `rum_metric`/`js_exception`/`user_session` y drenado en shutdown. Footprint objetivo: CPU-only, < 2GB RAM, $0/mes (config.yaml).

### Requirement: RUM-1

Los endpoints `POST /telemetry/metrics` (body `RumEventBatch`) y `POST /telemetry/exceptions` (body `JsExceptionBatch`) DEBEN existir y DEBEN aplicar la dependencia `require_api_key`: X-API-Key ausente o inválida → 401 `invalid_api_key` con header `WWW-Authenticate`; key de aplicación inactiva → 403 `app_inactive`. La aplicación autenticada por la key DEBE ser el tenant de todos los eventos del batch (IAUTH-2); el `application_id` del payload, si está presente, NUNCA DEBE usarse como autoridad de tenant (D2).

#### Scenario: Key ausente

- GIVEN un request a `/telemetry/metrics` sin header X-API-Key
- WHEN se evalúa el guard
- THEN 401 con `ErrorResponse{code: invalid_api_key}` y header `WWW-Authenticate`

#### Scenario: Key inválida

- GIVEN un header X-API-Key con formato o hash inválido
- WHEN se evalúa el guard
- THEN 401 idéntico al caso ausente (fail-closed, sin información de causa)

#### Scenario: Aplicación inactiva

- GIVEN una aplicación con `is_active=false` y key válida
- WHEN se envía un batch a `/telemetry/exceptions`
- THEN 403 con `ErrorResponse{code: app_inactive}` y el batch no se procesa

#### Scenario: Tenant desde la key (IAUTH-2)

- GIVEN la key de la aplicación A y un payload cuyo `application_id` es B
- WHEN se envía el batch
- THEN el tenant es A y los eventos se persisten bajo `user_session.app_id = A`

### Requirement: RUM-2

Un batch cuyo envelope no cumpla el contrato (`schema_version ≠ "1.0"`, `events` vacío o > 500, estructura inválida) DEBE rechazarse completo con 400 y `ErrorResponse{code: schema_validation_error}`; el handler global DEBE traducir los 422 de validación Pydantic del envelope a 400 en estos paths (D5). Un envelope inválido NO DEBE encolar ningún evento.

#### Scenario: schema_version inválida

- GIVEN un batch con `schema_version: "2.0"`
- WHEN POST /telemetry/metrics
- THEN 400 `schema_validation_error` y ningún evento se encola

#### Scenario: Envelope sobre el límite

- GIVEN un batch con 501 eventos
- WHEN POST /telemetry/metrics
- THEN 400 `schema_validation_error` (el batch completo se rechaza, no se valida por evento)

### Requirement: RUM-3

Un batch válido DEBE responder 202 Accepted con `IngestResponse {batch_id, accepted, rejected[]}`: `batch_id` UUID generado por el servidor (correlación; no se persiste); `rejected[]` DEBE listar `{index, reason}` con la posición original en `events`; `accepted + len(rejected)` DEBE ser igual al total de eventos. El 202 DEBE responderse al ENCOLAR los eventos aceptados, no al persistir (semántica §3.4). Los eventos rechazados NUNCA DEBEN encolarse ni persistirse.

#### Scenario: Batch mixto

- GIVEN un batch de 3 eventos con 1 inválido en la posición 1
- WHEN POST /telemetry/exceptions
- THEN 202 con `{batch_id, accepted: 2, rejected: [{index: 1, reason}]}` y solo 2 eventos se encolan

#### Scenario: Batch íntegramente válido

- GIVEN un batch de N eventos todos válidos
- WHEN POST /telemetry/metrics
- THEN 202 con `accepted: N` y `rejected: []`

#### Scenario: Batch íntegramente inválido

- GIVEN un batch bien formado cuyos N eventos fallan la política por evento
- WHEN POST /telemetry/metrics
- THEN 202 con `accepted: 0` y `rejected` con los N índices (el nivel evento no rechaza el batch)

### Requirement: RUM-4

La validación por evento DEBE aplicar la política de `ContratoIngestaRUM.md` + `PipelineIngestaRUM.md` §2.3 con los códigos: `missing_required_field`, `invalid_uuid`, `invalid_metric_type`, `invalid_unit`, `invalid_range`, `invalid_timestamp`, `oversized_event`. El código `unknown_application` NO DEBE existir en el flujo (D2). Rangos de cordura: TTFB 0–60000 ms, FCP 0–120000 ms, XHR_LATENCY 0–60000 ms, JS_EXCEPTION_RATE ≥0 count, RAGE_CLICK ≥0 count; `error_type` ≤100 chars, `message` ≤2000, `stack_trace` ≤20000; ≤500 eventos por batch y ≤50 métricas por evento. Los ratings good/poor del contrato NO DEBEN ser criterio de rechazo (rango de cordura, no de calidad).

#### Scenario: Valor fuera de rango

- GIVEN un evento TTFB con `value: 61000` y otro con `value: 9000`
- WHEN POST /telemetry/metrics
- THEN el primero se rechaza con `invalid_range` y el segundo se acepta (9000 ms es dato legítimo de cordura)

#### Scenario: UUID inválido

- GIVEN un evento con `session_id: "no-es-uuid"`
- WHEN POST /telemetry/metrics
- THEN se rechaza con `invalid_uuid`

#### Scenario: Unidad incoherente

- GIVEN un evento JS_EXCEPTION_RATE con `unit: "ms"`
- WHEN POST /telemetry/metrics
- THEN se rechaza con `invalid_unit`

#### Scenario: Evento sobredimensionado

- GIVEN una excepción con `stack_trace` de 20001 caracteres
- WHEN POST /telemetry/exceptions
- THEN se rechaza con `oversized_event`

#### Scenario: application_id ausente

- GIVEN un evento RUM sin `application_id` en el payload
- WHEN POST /telemetry/metrics
- THEN el evento se acepta (campo fuera de `required`, D2; el tenant viene de la key)

### Requirement: RUM-5

Los eventos aceptados DEBEN encolarse en una cola en proceso acotada detrás de una interfaz abstraída (puerto con `enqueue`/`close`/`join`, migrable a broker durable), con `maxsize` configurable (default 10000); worker tasks DEBEN consumir la cola y persistir. Cola llena → el endpoint DEBE responder 503 con `ErrorResponse{code: queue_full}` sin bloquear el request (backpressure, §3.3). La cola es por proceso: el runtime DEBE mantenerse en un único worker uvicorn (CMD actual) para no fragmentarla.

#### Scenario: Backpressure

- GIVEN la cola llena (maxsize 1 y worker sin consumir)
- WHEN POST /telemetry/metrics con un batch válido
- THEN 503 `queue_full` y el request no bloquea

#### Scenario: Encolado con capacidad

- GIVEN la cola con capacidad disponible
- WHEN POST /telemetry/metrics con un batch válido
- THEN 202 y los eventos aceptados quedan encolados para el worker

### Requirement: RUM-6

El worker DEBE persistir en Postgres 16: resolver/crear `user_session` (`INSERT ... ON CONFLICT (session_id) DO NOTHING`; `app_id` = aplicación autenticada), bulk insert de `rum_metric` (resolviendo `type` → `metric_type_id` del catálogo) y de `js_exception` (`metric_id` se persiste si existe; si no, NULL + contador de correlación blanda). Chunks de 500 filas, una transacción por chunk; errores transitorios de BD DEBEN reintentarse 3 veces con backoff exponencial (0.5/1/2 s); errores permanentes DEBEN ir a dead-letter (log + contador), nunca pérdida silenciosa (D1, D6).

#### Scenario: Persistencia verificada

- GIVEN un batch encolado con 2 métricas y 1 excepción de una sesión nueva
- WHEN el worker procesa el chunk
- THEN existen filas en `rum_metric` y `js_exception`, y `user_session` quedó creada con `app_id` de la app autenticada

#### Scenario: Retry transitorio

- GIVEN una falla transitoria de BD durante el chunk
- WHEN el worker reintenta con backoff
- THEN el chunk persiste en el intento ≤ 3 y no hay pérdida de eventos

#### Scenario: Dead-letter

- GIVEN un error permanente de BD (p.ej. constraint violation irrecuperable)
- WHEN el worker agota los 3 retries
- THEN el chunk va a dead-letter (log + contador `ingest.persistence_dead_letter_total`), sin excepción silenciosa

### Requirement: RUM-7

En shutdown, el sistema DEBE dejar de aceptar eventos nuevos (cola llena → 503) y DEBE drenar los eventos encolados antes de `dispose_engine()`, con un timeout acotado y configurable; los eventos no persistidos al vencer el timeout DEBEN loguearse explícitamente (nunca descartarse en silencio) (D6).

#### Scenario: Drenado en shutdown

- GIVEN una cola con eventos pendientes y un evento de shutdown
- WHEN el lifespan ejecuta el cierre
- THEN los eventos encolados se persisten antes de cerrar el engine

#### Scenario: Timeout de drenado

- GIVEN más eventos pendientes que los procesables dentro del timeout
- WHEN vence el timeout de shutdown
- THEN los eventos no persistidos se loguean con su cantidad y el proceso cierra igual

### Requirement: RUM-8

El sistema DEBE emitir logs estructurados por rechazo con `batch_id`, `index` y `reason` (ADR-23: X-API-Key y valores de key NUNCA en logs) y DEBE mantener contadores en proceso: `ingest.received_total`, `ingest.accepted_total`, `ingest.rejected_total{reason}`, `ingest.queue_depth`. En este cambio NO DEBE agregarse `prometheus-client` ni endpoint `/metrics` (D4).

#### Scenario: Log de rechazo redactado

- GIVEN un batch con un evento rechazado
- WHEN se procesa la validación por evento
- THEN el log estructurado contiene `batch_id`, `index` y `reason` y no contiene la X-API-Key

#### Scenario: Contadores en proceso

- GIVEN un batch de 3 eventos con 1 rechazado
- WHEN se completa el request
- THEN `ingest.received_total` +3, `ingest.accepted_total` +2, `ingest.rejected_total{reason}` +1 y `ingest.queue_depth` refleja lo encolado

---

## 2. openapi (Modificada)

## MODIFIED Requirements

### Requirement: OAS-6

El securityScheme `apiKey` (header `X-API-Key`) DEBE permanecer declarado y DEBE aplicarse con `security: [apiKey]` a los paths nuevos `/telemetry/metrics` y `/telemetry/exceptions`; la descripción del scheme DEBE actualizarse (eliminando "en este cambio ningún path existente exige apiKey" y documentando su aplicabilidad vigente a `/telemetry/*`). (Previously: scheme declarado sin `security` en ningún path; wiring diferido a #37.)

#### Scenario: Ingesta protegida

- GIVEN el openapi.yaml con `security: [apiKey]` en `/telemetry/metrics` y `/telemetry/exceptions`
- WHEN schemathesis ejecuta los checks sobre esos paths
- THEN se exige X-API-Key y los status codes 401/403 se declaran como esperados junto a 202/400/503

## ADDED Requirements

### Requirement: OAS-11

Los paths POST `/telemetry/metrics` y POST `/telemetry/exceptions` DEBEN declararse con requestBody (`RumEventBatch`/`JsExceptionBatch`) y respuestas: 202 (`IngestResponse`), 400 (`schema_validation_error`), 401/403 (guard), 503 (`queue_full`); 429 `rate_limit_exceeded` DEBE permanecer declarado SIN implementación (D3).

#### Scenario: Contrato de respuestas completo

- GIVEN el documento con los paths `/telemetry/*`
- WHEN se valida el contrato
- THEN 202/400/401/403/503/429 están declarados y el 429 no tiene implementación asociada

### Requirement: OAS-12

`application_id` DEBE salir de `required` en `RumEvent` y `JsExceptionEvent` (D2: no es autoridad de tenant); los códigos documentados de `IngestResponse.rejected[].reason` NO DEBEN incluir `unknown_application`.

#### Scenario: Schemas alineados con IAUTH-2

- GIVEN el contrato actualizado
- WHEN se inspecciona `required` de `RumEvent`/`JsExceptionEvent`
- THEN `application_id` no figura en `required` y `unknown_application` no aparece como código de rechazo

## REMOVED Requirements

### Requirement: Paths `/metrics/ingest` y `/logs/ingest`

Los paths `POST /metrics/ingest` y `POST /logs/ingest` DEBEN eliminarse del documento OpenAPI, reemplazados por `/telemetry/metrics` y `/telemetry/exceptions`.
(Reason: criterio 8 de #37 — nomenclatura definitiva `/telemetry/*`; sin runtime que romper, no existía implementación de ingesta.)
(Migration: `tests/test_contract.py` (OAS-6/OAS-9/OAS-10, `_SCOPED_PATH_RE` sumando `telemetry`), `tests/test_ingest_auth.py` y las docs vivas se actualizan en el mismo cambio; `openspec/specs/architecture/*` se alinea según ARCH-1..4.)

---

## 3. ingest-auth (Modificada)

## MODIFIED Requirements

### Requirement: IAUTH-5

El guard `require_api_key` DEBE cablearse a los paths de producción `/telemetry/metrics` y `/telemetry/exceptions` en este cambio (cierra IAUTH-5); `test_prod_app_has_no_api_key_wiring` DEBE invertirse para aseverar que los paths de ingesta SÍ aplican el guard. Costo de validación objetivo ~1μs, sin servicios nuevos (CPU-only, <2GB RAM). (Previously: guard desacoplado y probado aisladamente, sin aplicar a ningún path de producción.)

#### Scenario: Wiring a producción

- GIVEN el guard `require_api_key` implementado y la app de producción
- WHEN se listan los paths con dependencia del guard
- THEN `/telemetry/metrics` y `/telemetry/exceptions` están cubiertos y el test de wiring lo asevera

### Requirement: IAUTH-2

La aplicación autenticada DEBE derivarse EXCLUSIVAMENTE de la key (binding 1:1 credencial→app); el `application_id` del payload DEBE quedar fuera de `required` y NUNCA DEBE decidir el tenant; el flujo de rechazo por evento NO DEBE incluir `unknown_application` (D2). (Previously: `application_id` requerido en el contrato y código `unknown_application` en la política — tensión resuelta por D2.)

#### Scenario: Payload sin autoridad

- GIVEN la key de A y un evento sin `application_id` (o con el de B)
- WHEN el guard autentica y la política valida el evento
- THEN el tenant es A, el evento se acepta y no se evalúa `unknown_application`

---

## 4. architecture (Modificada)

## MODIFIED Requirements

### Requirement: ARCH-1

`openspec/specs/architecture/interfaces.md` DEBE revertir la decisión S1 de nomenclatura (ISS-S1-02): los endpoints de ingesta DEBEN documentarse como `POST /telemetry/metrics` y `POST /telemetry/exceptions` (tabla §1.1 y snippets), reemplazando `/metrics/ingest` y `/logs/ingest`; el texto de "Arquitectura de nomenclatura unificada" DEBE actualizarse documentando el cambio a `/telemetry/*`. (Previously: `/metrics/ingest` canonical sobre `/telemetry/metrics`, con prefijo `/metrics/` para toda la ingesta.)

#### Scenario: Tabla y snippets alineados

- GIVEN interfaces.md editado
- WHEN se revisa §1.1 y los endpoints críticos
- THEN figuran `/telemetry/metrics` y `/telemetry/exceptions` y no hay referencias a `/metrics/ingest` ni `/logs/ingest`

### Requirement: ARCH-2

`openspec/specs/architecture/components.md` DEBE alinear el árbol de routers (routers/ingest.py → routers/telemetry.py exponiendo `POST /telemetry/*`) y el diagrama de secuencia mermaid del flujo de ingesta con las rutas nuevas.

#### Scenario: Árbol y mermaid sincronizados

- GIVEN components.md editado
- WHEN se revisa el árbol de `src/api/` y el sequence diagram
- THEN el router es `telemetry.py` con `POST /telemetry/metrics` y `POST /telemetry/exceptions`

### Requirement: ARCH-3

`openspec/specs/architecture/quality-attributes.md` DEBE actualizar el artefacto de calidad de ingesta (hoy `Endpoint /metrics/ingest`) a `POST /telemetry/metrics`, preservando el escenario de atributo de calidad asociado.

#### Scenario: Artefacto renombrado

- GIVEN quality-attributes.md editado
- WHEN se revisa la fila de artefacto de ingesta
- THEN el artefacto es `POST /telemetry/metrics`

### Requirement: ARCH-4

Las docs vivas `docs/architecture/PipelineIngestaRUM.md`, `docs/architecture/ContratoIngestaRUM.md` y `docs/brief-v2.md` DEBEN actualizarse con las rutas `/telemetry/*` y la semántica 202 (encolado) / 503 (backpressure); las referencias históricas (`docs/informe-avance-1/`, `docs/business/issues-s1-s2.md`) NO DEBEN reescribirse (registros).

#### Scenario: Docs vivas sin rutas viejas

- GIVEN las docs vivas actualizadas
- WHEN se buscan referencias de ingesta
- THEN las rutas vigentes son `/telemetry/metrics` y `/telemetry/exceptions`, y los históricos conservan `/metrics/ingest`

---

## Criterios de aceptación verificables

1. Tests TDD: 400 envelope (`schema_validation_error`), 202 parcial con `rejected[{index, reason}]` por código (7 códigos, sin `unknown_application`), 401/403 del guard, 503 `queue_full` con cola llena, aislamiento IAUTH-2, persistencia verificada en BD.
2. `openapi.yaml`: `/telemetry/*` exigen `apiKey`; paths `/metrics/ingest` y `/logs/ingest` ausentes; descripción del scheme actualizada; schemathesis verde (202/400/401/403/503/429 declarados).
3. Worker persiste `rum_metric`/`js_exception`/`user_session` (D1); shutdown drena la cola con timeout acotado (D6); contadores en proceso (D4).
4. Cobertura ≥70% (`pytest --cov=src`); `pytest` verde; CHANGELOG y ADR de la decisión de pipeline async registrados.
5. Límites de recursos: CPU-only, <2GB RAM, sin dependencias nuevas (sin prometheus-client), uvicorn 1 worker.

## Next recommended

**design** — la fase design toma la interfaz `IngestQueue` + `asyncio.Queue` acotada, el lifespan con workers/drenado, la validación de dos niveles, el handler global 422→400, las entidades/repos de persistencia y el ADR de pipeline async para definir arquitectura y tareas.