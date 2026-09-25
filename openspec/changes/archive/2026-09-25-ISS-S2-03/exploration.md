# EXPLORATION — ISS-S2-03: Ingesta RUM asíncrona

**Cambio**: ISS-S2-03 (GitHub #37). **Base**: `develop` con ISS-S2-01 (PR #53) e ISS-S2-02 (PR #54) mergeados. **Fuente de verdad**: `docs/business/issues-s2-s3.md` (issue #37). **Modo**: openspec (repo-local) + Engram (`sdd/ISS-S2-03/explore`). **Idioma**: español neutro técnico.

**Criterios de aceptación del issue #37** (mapeados a código real relevado):

| # | Criterio | Estado hoy | Evidencia |
|---|----------|-----------|-----------|
| 1 | Batches aceptados | **FALTA** (sin handlers de ingesta) | No existe router/servicio de ingesta en `src/api` (solo `auth`, `users`, `applications`). El contrato OpenAPI S1 ya declara `202` + `IngestResponse` para `/metrics/ingest` y `/logs/ingest` |
| 2 | Validación de batches y de eventos según la política por evento | **FALTA (política YA especificada)** | `docs/architecture/ContratoIngestaRUM.md` (matrices por tipo de métrica y de excepción) y `PipelineIngestaRUM.md` §2 (2 niveles: envelope→400 batch completo; evento→202 parcial con códigos de rechazo) |
| 3 | Respuesta adecuada que informa el resultado del batch de forma consistente | **FALTA (contrato definido)** | `IngestResponse {batch_id, accepted, rejected[{index, reason}]}` ya en openapi.yaml; semántica: 202 = encolado, no persistido (`PipelineIngestaRUM.md` §3.4) |
| 4 | Procesamiento desacoplado del request | **FALTA** | Sin cola ni workers en código (grep de `asyncio.Queue`/`BackgroundTasks`/`create_task` → solo documentación). Diseño S1 aprobado: cola en proceso + workers en lifespan (`PipelineIngestaRUM.md` §3) |
| 5 | Backpressure | **FALTA** | `503 queue_full` ya declarado en OpenAPI (202/400/429/503); sin implementación. 429 = rate limit por API key, sin infra de rate limiting |
| 6 | Errores controlados | **PARCIAL** | `DomainError` tipificadas 401/403/404/409 → `ErrorResponse` (ADR-09) con handler global. **No existe** subtipo 503 (queue_full) ni 429; el middleware/ dir está vacío |
| 7 | Observabilidad mínima | **FALTA** | Sin `prometheus_client` (no está en pyproject ni requirements.txt), sin endpoint `/metrics`. Solo existe logging estructurado + filtro global de redacción de keys (ADR-23) |
| 8 | Nomenclatura definitiva (rutas viejas) | **PARCIAL** | OpenAPI mantiene `/metrics/ingest` y `/logs/ingest` (renombrar). **Ventaja**: no existe implementación ni tests funcionales de ingesta → no hay runtime que romper. Referencias en specs y docs (ver §2) |

---

## 1. Estado actual (código real, S2-01 + S2-02 mergeados)

### Contrato OpenAPI (S1, `openspec/specs/openapi.yaml`)

- Paths de ingesta vigentes: `POST /metrics/ingest` (RumEventBatch) y `POST /logs/ingest` (JsExceptionBatch), ambos con respuestas `202/400/429/503`. **Sin `security:`** (OAS-6 de S2-02: el scheme `apiKey` se declara pero no se aplica a ningún path hasta #37).
- Schemas completos listos para reutilizar: `RumEventBatch` (≤500 eventos, schema_version "1.0"), `RumEvent` (required: schema_version, timestamp, session_id, application_id, metrics; metadata opcional), `RumMetric` (type enum TTFB/FCP/XHR_LATENCY/JS_EXCEPTION_RATE/RAGE_CLICK, value≥0, unit ms/count, ≤50 por evento), `JsExceptionBatch`, `JsExceptionEvent` (required: error_type≤100, message≤2000, session_id, application_id, timestamp; stack_trace≤20000, metric_id opcional), `IngestResponse`, `ErrorResponse`.
- `securitySchemes.apiKey` (X-API-Key) descripción dice "Aplicable a /telemetry/* (handlers en #37, OAS-6); en este cambio ningún path existente exige apiKey" — **este texto debe actualizarse en #37**.
- `asyncapi.yaml`: no referencia rutas de ingesta (canales anomaly/alert/metrics-batch/system-health genéricos) → **sin cambios por nomenclatura**.

### Guard `require_api_key` (S2-02, listo y probado)

- `src/api/presentation/dependencies.py`: X-API-Key ausente/inválida → 401 `invalid_api_key` con `WWW-Authenticate: ApiKey` (indistinguible, fail-closed); key de app inactiva → 403 `app_inactive`; inyecta `Application` autenticada. **Binding 1:1 key→app: el app_id del payload nunca se confía (IAUTH-2)**.
- Probado aisladamente en `tests/test_ingest_auth.py` contra la app de test `/_probe` (conftest). **El wiring a paths de producción es exactamente este cambio #37** (docstring de IAUTH-5).
- `test_prod_app_has_no_api_key_wiring`: aserción `"/metrics/ingest" not in all_paths` seguirá pasando tras #37 (los paths nuevos son `/telemetry/*`), pero el test documenta una intención que cambia → **revisar/actualizar este test en #37** (p.ej. aserción inversa: los paths de ingesta SÍ usan el guard).

### Política por evento (la "política" que cita la issue)

- `docs/architecture/ContratoIngestaRUM.md`: matriz por tipo — TTFB number ms 0–60000; FCP number ms 0–120000; XHR_LATENCY number ms 0–60000; JS_EXCEPTION_RATE count ≥0; RAGE_CLICK count ≥0. Los ratings good/poor son referencia de dashboard, **NO criterio de rechazo** (aclaración explícita del doc). Excepciones: error_type≤100, message≤2000, stack_trace≤20000, UUIDs válidos, ISO 8601 UTC.
- `docs/architecture/PipelineIngestaRUM.md` §2: **nivel envelope** (schema_version, estructura, ≤500) → 400 batch completo; **nivel evento** (UUIDs, tipo, unidad, rango, required, application_id conocido) → 202 parcial. Códigos de rechazo: `missing_required_field`, `invalid_uuid`, `invalid_metric_type`, `invalid_unit`, `invalid_range`, `invalid_timestamp`, `unknown_application`, `oversized_event`. §2.4: rechazados nunca se persisten; log estructurado + contador.
- ⚠️ **Tensión con S2-02**: el código `unknown_application` valida `application_id` contra la BD, pero IAUTH-2 establece que el payload nunca es autoridad de tenant. Definir la interacción (ver D2).

### Infraestructura async disponible

- SQLAlchemy 2.0 async + asyncpg (`session.py`): engine global, pool `db_pool_size=20`, `db_max_overflow=10`, `pool_pre_ping`. Dependencia `get_session` lista para inyectar en los nuevos endpoints.
- FastAPI `lifespan` en `main.py` (hoy solo `dispose_engine()` al apagar) → **punto natural para crear la cola y los worker tasks**.
- Runtime: Dockerfile CMD `uvicorn api.main:app` **sin `--workers`** (proceso único) → la cola en proceso es coherente; `test_container_import_path.py` ancla el CMD (cualquier cambio de CMD debe actualizar ese test).
- DDL listo (S1): `rum_metric`, `js_exception`, `user_session` existen con FKs a `application`/`metric_type`; catálogo `metric_type` sembrado con los 5 tipos. `conftest.py` trunca estas tablas por test (`clean_db`) → **los tests de persistencia pueden asertar filas sin fixtures extra**.

### Schemathesis / contract tests (estado actual)

- `pyproject.toml` dev: `schemathesis>=4.0.0`. CI: job `contract` corre `pytest tests/test_contract.py` (con Postgres 16 service + alembic upgrade head).
- `tests/test_contract.py` — **aserciones que #37 debe cambiar deliberadamente**:
  - `test_oas6_api_key_scheme_declared_without_security_on_existing_paths`: itera `/metrics/ingest` y `/logs/ingest` y asevera que NO tienen `security` y respuestas `{202,400,429,503}` → pasa a aseverar que `/telemetry/*` SÍ exigen `apiKey` (y sumar 401/403).
  - `test_oas10_preexisting_paths_intact`: el set esperado incluye `/metrics/ingest` y `/logs/ingest` → reemplazar por `/telemetry/metrics` y `/telemetry/exceptions` (los paths viejos desaparecen del documento).
  - `test_oas9_openapi_document_loads_in_schemathesis`: asevera `/metrics/ingest` en paths.
  - `_SCOPED_PATH_RE = r"/(health|ready|auth|users|applications)"`: el subset live debe sumar `telemetry` (schemathesis generará `X-API-Key` por el scheme; el `positive_data_acceptance` ya acepta 401/403 → compatible con el guard).
  - `test_schemathesis_live_contract_scoped` (xfail ADR-24): el subset scoped se amplía con telemetry.

### Observabilidad (brecha)

- No existe `prometheus_client` ni endpoint `/metrics`. `quality-attributes.md` e `interfaces.md` planifican `/metrics` OpenMetrics y contadores (`ingest.received_total`, `ingest.accepted_total`, `ingest.rejected_total{reason}`, `ingest.queue_depth`, `ingest.request_duration_seconds`, dead-letter). `PipelineIngestaRUM.md` §4 lista las mismas métricas.
- "Observabilidad mínima" del criterio 7 se puede satisfacer con logs estructurados (logging + `ApiKeyRedactionFilter` global ya instalado en `main.py`) y contadores en proceso; prometheus-client sería una dependencia nueva (ver D4).

### Referencias a rutas viejas (criterio 8 — "documentación")

- **Specs vivas (actualizar)**: `openspec/specs/openapi.yaml`, `openspec/specs/architecture/interfaces.md` (**registra la decisión S1 de `/metrics/ingest` sobre `/telemetry/metrics` — debe revertirse documentando el cambio**), `components.md` (árbol `routers/ingest.py` y mermaid), `quality-attributes.md` (artefacto `/metrics/ingest`).
- **Docs de arquitectura (actualizar)**: `docs/architecture/PipelineIngestaRUM.md`, `docs/architecture/ContratoIngestaRUM.md`, `docs/brief-v2.md` (extracto de ejemplo).
- **Frontend**: `src/frontend/` sin referencias a ingest/telemetry (grep vacío) → no tocar.
- **Ejemplos**: no existe dir `examples/`.
- **Históricos (NO tocar, son registros)**: `docs/informe-avance-1/evaluacion-equipo.md`, `docs/business/issues-s1-s2.md` (documenta la decisión S1 y la unificación pendiente — útil como evidencia del cambio de nomenclatura).

---

## 2. Áreas afectadas (proyección)

| Archivo | Afectación |
|---|---|
| `src/api/presentation/routers/telemetry.py` | **Nuevo** — `POST /telemetry/metrics` y `POST /telemetry/exceptions` con `Depends(require_api_key)` |
| `src/api/domain/services/ingest_service.py` | **Nuevo** — validación envelope + por evento (política), generación de `batch_id`, encolado |
| `src/api/domain/entities/` + `repositories/` | **Nuevos** (si #37 persiste): entidades/repos de `rum_metric`, `js_exception`, `user_session` (ver D1) |
| `src/api/infrastructure/ingest/queue.py` (o similar) | **Nuevo** — interfaz de cola abstraída + `asyncio.Queue` acotada + workers (si E1) |
| `src/api/presentation/schemas/ingest.py` | **Nuevo** — schemas Pydantic espejo de `RumEventBatch`/`RumMetric`/`JsExceptionBatch`/`IngestResponse` (hoy solo existen en openapi.yaml, no como código) |
| `src/api/domain/exceptions.py` | **Nuevo subtipo** 503 (p.ej. `ServiceUnavailableError` code `queue_full`) para backpressure |
| `src/api/config.py` | Settings nuevos: `ingest_queue_maxsize` (10000), `ingest_workers` (2), chunk/retry (si E1) |
| `src/api/main.py` | Registrar router de telemetría; crear cola/workers en `lifespan` (startup) y drenar/cerrar en shutdown |
| `openspec/specs/openapi.yaml` | Renombrar paths a `/telemetry/*`, aplicar `security: [apiKey]`, sumar 401/403 a respuestas, actualizar descripción del scheme |
| `openspec/specs/architecture/interfaces.md` (+ components.md, quality-attributes.md) | Revertir decisión S1 de nomenclatura; alinear diagramas |
| `docs/architecture/PipelineIngestaRUM.md`, `ContratoIngestaRUM.md`, `docs/brief-v2.md` | Rutas nuevas + semántica del 202/backpressure |
| `tests/test_contract.py` | OAS-6/OAS-9/OAS-10: paths nuevos con `apiKey`, respuestas con 401/403, `_SCOPED_PATH_RE` + telemetry |
| `tests/test_ingest_auth.py` | Actualizar `test_prod_app_has_no_api_key_wiring` (los paths de ingesta YA existen y SÍ usan el guard) |
| `tests/test_ingest_telemetry.py` | **Nuevo** — validación envelope→400, por evento→202 parcial con `rejected[{index, reason}]`, 401/403 del guard, 503 con cola llena, batch_id, persistencia (si D1) |
| `docs/adr/` | **Nuevo ADR** para la decisión de pipeline async (cola en proceso vs alternativas) — ver R7 |
| `CHANGELOG.md` | Registro del cambio (convención del repo) |

---

## 3. Enfoques (la issue NO prescribe estructura interna — evaluar opciones)

| Enfoque | Pros | Contras | Esfuerzo |
|---|---|---|---|
| **E1 — Cola `asyncio.Queue` acotada + worker tasks en el lifespan** (diseño S1 aprobado en `PipelineIngestaRUM.md` §3) | Sin infra nueva ($0/mo, footprint mínimo); backpressure natural (`maxsize` → 503); coherente con proceso único de uvicorn; testable con pytest-asyncio; interfaz de cola abstraíble a broker futuro (el propio doc lo exige); workers comparten el engine async de SQLAlchemy | Sin durabilidad ante reinicios (pérdida de eventos en cola — limitación aceptada explícitamente en S1); cola por proceso (uvicorn `--workers>1` la fragmentaría — hoy el CMD es 1 worker); requiere shutdown graceful | **Medio** |
| **E2 — `BackgroundTasks` de FastAPI** | Integrado, trivial | Sin backpressure real (acumulación ilimitada de tareas); sin batching/chunking; sin control de orden ni cola; difícil testear determinísticamente; no satisface el criterio "Backpressure" | Bajo (pero no cumple criterios) |
| **E3 — Broker externo (Redis/AMQP/Celery)** | Durabilidad, escala horizontal | **Excluido explícitamente** por la issue ("SIN broker externo"); viola $0/mes y <2GB RAM; agrega contenedor y operación | Alto (fuera de alcance) |
| **E4 — Worker en contenedor separado (patrón ai-engine)** | Aislamiento de OOM (containers.md §2.3) | Contradice `PipelineIngestaRUM.md` (cola en core, workers en proceso); sin broker obligaría DB-polling (tabla staging, latencia, schema extra); overkill para S2; "desacoplado del request" se cumple igual en proceso | Alto |

---

## 4. Recomendación

**E1 — cola en proceso acotada + worker tasks en el lifespan**, con puntos fijados:

1. **Interfaz de cola abstraída** (puerto `IngestQueue` con `enqueue/close/join`) para migración futura a broker durable (lo exige `PipelineIngestaRUM.md` §3); implementación concreta `asyncio.Queue(maxsize=configurable)`.
2. **Config**: `INGEST_QUEUE_MAXSIZE=10000`, `INGEST_WORKERS=2`, chunk 500, retry 3 con backoff exponencial (0.5/1/2s) solo errores transitorios de DB, dead-letter = log + contador.
3. **Lifespan**: crear cola y lanzar worker tasks en startup; en shutdown, dejar de aceptar (`queue_full` → 503) y drenar lo encolado antes de `dispose_engine()` (evitar pérdida silenciosa; loguear lo no persistido).
4. **Validación en el request** (no en el worker): envelope → 400 (FastAPI/Pydantic valida schema y ≤500); por evento → 202 parcial con `rejected[{index, reason}]` según `PipelineIngestaRUM.md` §2.3. El 202 se responde al ENCOLAR (semántica §3.4).
5. **Guard**: `Depends(require_api_key)` en ambos endpoints; tenant = app de la key; aplicar `security: [apiKey]` en OpenAPI.
6. **Errores**: nuevo subtipo `ServiceUnavailableError` (503, `queue_full`) en `exceptions.py`; 400 lo da FastAPI (422 por defecto para schema — **definir mapeo a 400 `schema_validation_error` según contrato**, decisión de diseño).
7. **Observabilidad mínima**: logs estructurados con `batch_id` + `index` + `reason` por rechazo (el filtro ADR-23 ya redacta keys); contadores en proceso si no se agrega prometheus-client.

**Nota de alcance crítica**: los criterios de #37 NO mencionan persistencia a BD (eso es ISS-S3-01/#40), pero el EDT (`2.6/2.7`: "Debe ser posible recibir y **persistir** métricas y excepciones") y `PipelineIngestaRUM.md` asumen el pipeline completo con bulk insert. Un worker que solo encola sin consumir no demuestra "procesamiento desacoplado". **Definir con el usuario si #37 persiste a `rum_metric`/`js_exception` (sink mínimo según pipeline S1) o deja un sink log/no-op para #40 (ver D1).**

**Tests requeridos (strict TDD, pytest + Postgres real):**

- **Unit**: validación por evento (cada código de rechazo de §2.3, incl. límites 500/50), generación de `batch_id`, política envelope vs evento.
- **Integration** (httpx AsyncClient): 202 con `{batch_id, accepted, rejected}`; batch inválido → 400; 401 sin key/key inválida; 403 app inactiva; 503 con cola llena (fixture con maxsize 1); 202 se responde aunque el worker no persista aún; aislamiento IAUTH-2 (app_id del payload ≠ app de la key).
- **Contract** (schemathesis): `apiKey` aplicado a `/telemetry/*`, respuestas con 401/403, paths viejos ausentes del documento.
- **Persistencia** (si D1=persistir): filas en `rum_metric`/`js_exception`/`user_session` tras procesar; chunk/retry/dead-letter.

---

## 5. Riesgos

- **R1 — Scope de persistencia (Alto)**: si #37 persiste a BD, roza ISS-S3-01 (#40); si NO persiste, el worker no demuestra el pipeline y el criterio "procesamiento desacoplado" queda ambiguo. Requiere decisión D1 antes de proponer.
- **R2 — Interacción guard ↔ `application_id` del payload (Alto)**: IAUTH-2 (payload nunca confiado) choca con el contrato S1 que exige `application_id` y el código `unknown_application`. Definir: ¿ignorar el campo, rechazar si ≠ app autenticada, o quitarlo del contrato? Es un cambio de contrato con impacto en schemas y tests.
- **R3 — Breaking del contrato de ingesta (Medio)**: renombrar paths, aplicar `apiKey` y cambiar respuestas rompe las aserciones OAS-6/OAS-10 de `test_contract.py` (hoy verdes) y el texto del scheme; deben actualizarse en el mismo cambio. No hay runtime que romper (no existía implementación), lo que reduce el riesgo.
- **R4 — Observabilidad sin dependencia (Medio)**: prometheus-client no existe; agregarlo es dependencia nueva (impacta Dockerfile/requirements) o se degrada a logs + contadores en proceso. `config.yaml` (verify) valida coverage 70%, no métricas.
- **R5 — Cola en proceso sin durabilidad (Medio)**: pérdida de eventos ante reinicio (aceptada en S1); shutdown sin drenar agrava la pérdida. Mitigar con drenado en lifespan y dead-letter logueada.
- **R6 — Fragmentación de cola con multi-worker (Bajo hoy)**: el CMD de uvicorn es 1 worker; si en el futuro se escala `--workers>1`, cada proceso tendría su propia cola. Documentar la restricción.
- **R7 — Registro ADR incompleto (Bajo)**: `docs/adr/` solo contiene 0000/0001; ADR-03..24 viven en comentarios de código y artefactos archivados. La decisión de pipeline async de #37 debe registrarse (¿nuevo archivo en `docs/adr/`? ¿en el cambio archivado?) — acordar dónde.
- **R8 — Docs históricas con rutas viejas (Bajo)**: `informe-avance-1/evaluacion-equipo.md` e `issues-s1-s2.md` referencian `/metrics/ingest`; son registros históricos. El criterio "documentación" aplica a docs vivas; no reescribir historia sin confirmación.

---

## 6. Supuestos

- La política por evento = `ContratoIngestaRUM.md` + `PipelineIngestaRUM.md` §2 (es la única especificación existente; EDT e HU no agregan detalle de validación).
- Los rangos del contrato son de cordura (rechazo de absurdos), no de calidad (un TTFB 9000ms se acepta) — aclaración explícita del contrato.
- El 202 se responde al encolar, no al persistir (§3.4); el `batch_id` no se persiste en BD (S1).
- El tenant de cada evento es la aplicación autenticada por la key; el `application_id` del payload no es autoridad (IAUTH-2, decisión S2-01 ya tomada).
- El guard se cablea en ESTE cambio (IAUTH-5: "wiring en #37").
- Persistencia: supuesto base = implementar sink de persistencia mínima (EDT/PipelineIngestaRUM.md) salvo decisión contraria en D1.
- 429 (rate limit) se mantiene declarado en el contrato sin implementación en #37 (no hay infra; criterio de aceptación pide backpressure, no rate limiting) — confirmar en D3.

---

## 7. Preguntas abiertas (requieren decisión del usuario ANTES de proponer)

- **D1 — Persistencia en #37**: ¿el worker persiste a `rum_metric`/`js_exception`/`user_session` (sink mínimo según pipeline S1/EDT) o #37 termina en validación + cola + 202, dejando la persistencia a ISS-S3-01 (#40)? Impacta entidades/repositorios nuevos y el alcance del cambio.
- **D2 — `application_id` en el payload vs guard (IAUTH-2)**: ¿ignorar el campo (informacional), rechazar el evento si no coincide con la app autenticada (código de rechazo nuevo, p.ej. `application_mismatch`), o quitarlo del contrato? Define si `unknown_application` (código S1) sigue existiendo.
- **D3 — 429 rate limit**: ¿implementar un limiter mínimo en proceso (por key) o mantener 429 solo declarado en el contrato (sin infra)? El criterio de aceptación pide backpressure (503), no rate limiting.
- **D4 — Observabilidad mínima**: ¿logs estructurados + contadores en proceso (sin dependencia nueva) o agregar `prometheus-client` y exponer `/metrics` (alineado con `quality-attributes.md`/`interfaces.md` pero dependencia + footprint nuevos)?
- **D5 — Mapeo 422→400**: el contrato declara `400 schema_validation_error`, pero FastAPI responde 422 por defecto en errores de schema. ¿Handler global que traduzca 422→400 en estos paths, o actualizar el contrato a 422?
- **D6 — Shutdown**: ante apagado, ¿drenar la cola (acepta latencia de apagado) o descartar y loguear lo no procesado? (Pipeline S1 no lo define; el lifespan actual solo cierra el engine).

## Ready for Proposal

**Sí** — con confirmación previa de D1..D6. La exploración deja identificado: criterios cubiertos vs faltantes, política por evento ya especificada (contrato + pipeline S1), guard listo para cablear (IAUTH-5), infra async disponible (SQLAlchemy async, lifespan, DDL completo, uvicorn 1 worker), aserciones de contract tests que cambiarán deliberadamente, enfoque recomendado (E1) y riesgos (el principal: interacción guard ↔ `application_id` del payload). El orquestador debe llevar D1..D6 al usuario antes de lanzar sdd-propose.