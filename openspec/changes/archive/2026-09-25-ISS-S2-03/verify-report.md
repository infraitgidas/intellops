```yaml
schema: gentle-ai.verify-result/v1
evidence_revision: sha256:c461e91e416811bd55d5b27e019c3565ea8a21ede74bd9eb775204149796e267
verdict: pass
blockers: 0
critical_findings: 0
requirements: 18/18
scenarios: 32/32
test_command: PYTHONPATH=. .venv/bin/pytest --cov=src --cov-report=term-missing -q --no-header
test_exit_code: 0
test_output_hash: sha256:f4add399aa153bfcdc1483e64d7615bcd9993a4663794800830f404fbd5ca137
build_command: docker compose build intellops-core
build_exit_code: 0
build_output_hash: sha256:e7309a5e67136237d806e454baab394b024ecb865716ccb465e5f97da4af4c23
```

## Verification Report

**Change**: ISS-S2-03 — Ingesta RUM asíncrona (GitHub #37)
**Version**: spec.md (delta, 2026-09-25)
**Mode**: Strict TDD (config.yaml `apply.tdd:true`, `testing.strict_tdd:true`, runner pytest)
**Rama**: feat/ISS-S2-03 (base origin/develop con ISS-S2-01 y ISS-S2-02 mergeados)
**Fecha**: 2026-09-25
**Tipo de verificación**: Independiente y fresca — suite completa re-ejecutada contra el estado actual del árbol (`HEAD` = c122534). `evidence_revision` = SHA-256 del tree hash (`git rev-parse HEAD^{tree}` → `sha256:` + digest).

### Completeness

| Metric | Value |
|--------|-------|
| Tasks total | 17 |
| Tasks complete | 17 |
| Tasks incomplete | 0 |

Todas las tareas de `tasks.md` están marcadas `[x]` (verificado: 17 checkboxes, 17 completas; fases 1–5). Requisitos: 18/18 headings `### Requirement:` de la spec — 17 activos verificables (RUM-1..8, OAS-6/11/12, IAUTH-2/5, ARCH-1..4) + 1 REMOVED (`Paths /metrics/ingest y /logs/ingest`) verificado como evidencia de eliminación (`test_oas10_ingest_paths_replaced_by_telemetry`, PASSED). Escenarios: 32/32.

### Build & Tests Execution

**Build**: ✅ Passed (`docker compose build intellops-core`, exit 0)
```text
#17 DONE 1.5s
 Image intellops-intellops-core Built
```
- Imagen reconstruida con cache; el Dockerfile no cambió en este cambio. CMD `alembic upgrade head && uvicorn api.main:app` intacto (uvicorn 1 worker, RUM-5).

**Tests**: ✅ 209 passed / 0 failed / 1 xpassed
```text
PYTHONPATH=. .venv/bin/pytest --cov=src --cov-report=term-missing -q --no-header
================= 209 passed, 1 xpassed, 34 warnings in 42.17s =================
```
- Distribución: `test_ingest_telemetry.py` (nuevo, ~45 tests: política, schemas, service, cola, guard, persistencia, retry/dead-letter, shutdown), `test_contract.py` (10 passed + 1 xpassed), `test_ingest_auth.py` (wiring IAUTH-5 invertido) + suite preexistente.
- El xpass corresponde a `test_schemathesis_live_contract_scoped` (xfail documentado, ADR-24): la corrida live de schemathesis contra la app ASGI valida casos reales y pasa — el gate contract queda verde.

**Coverage**: 93.06% / threshold 70% → ✅ Above
```text
Required test coverage of 70.0% reached. Total coverage: 93.06%
```

**Lint**: ✅ `flake8 src/` exit 0 (gate configurado, max-line-length=99). **Pylint**: ✅ `pylint src/` 8.93/10 ≥ 7.0 (única nota: E0401 `import-error` en `src/ml/pipeline/mock_reader.py`, archivo ML preexistente fuera del alcance de este cambio).

**openapi.yaml**: ✅ válido — `test_oas9_openapi_document_loads_in_schemathesis` PASSED (carga 3.1, ≥30 operaciones, incluye `/telemetry/*`). Verificación estructural independiente: `security: [apiKey]` en `/telemetry/metrics` y `/telemetry/exceptions`; respuestas 202/400/401/403/503/429 declaradas; paths `/metrics/ingest` y `/logs/ingest` ausentes; `application_id` fuera de `required` en `RumEvent`/`JsExceptionEvent`; `unknown_application` ausente de los códigos de rechazo.

### TDD Compliance

| Check | Result | Details |
|-------|--------|---------|
| TDD Evidence reported | ✅ | `apply-progress.md` con tabla "TDD Cycle Evidence" (17 filas) y "Work Unit Evidence" (5 commits) |
| All tasks have tests | ✅ | 17/17 tareas con test file verificado en el repo |
| RED confirmed (tests exist) | ✅ | `tests/test_ingest_telemetry.py` (1292 líneas, nuevo) + `test_contract.py`/`test_ingest_auth.py` modificados; RED declarado por tarea (ModuleNotFound/ImportError/404 router/test viejo roto) |
| GREEN confirmed (tests pass) | ✅ | 209 passed + 1 xpassed en ejecución independiente (exit 0) |
| Triangulation adequate | ✅ | 32 escenarios spec cubiertos por tests unit + integración + contract; casos con valores distintos por comportamiento (61000 vs 9000, 501 vs 3 eventos, etc.) |
| Safety Net for modified files | ✅ | `test_ingest_auth.py` 6/6, `test_contract.py` 3/3→10/10, suite 142/142→209/209 previos antes de modificar; archivo nuevo `test_ingest_telemetry.py` declara `N/A (new)` y es untracked previo (git status) |

**TDD Compliance**: 6/6 checks passed

### Test Layer Distribution

| Layer | Tests | Files | Tools |
|-------|-------|-------|-------|
| Unit | ~28 | `test_ingest_telemetry.py` (política, contadores, schemas, settings, cola sin workers, service con fake queue) | pytest |
| Integration (HTTP + Postgres real) | ~17 | `test_ingest_telemetry.py` (httpx ASGI + Postgres real: persistencia, retry, dead-letter, shutdown, 401/403/503/202), `test_ingest_auth.py` (wiring) | pytest + httpx AsyncClient + SQLAlchemy async |
| Contract | 11 (10 passed + 1 xpassed) | `test_contract.py` | schemathesis 4.x + yaml |
| **Total** | **210 colectados (209 passed + 1 xpassed)** | **3 changed + suite completa** | |

### Changed File Coverage

| File | Line % | Uncovered | Rating |
|------|--------|-----------|--------|
| `src/api/domain/services/ingest_policy.py` | 93% | L63,70,80,87,117,120,131,183 | ✅ Excellent |
| `src/api/domain/services/ingest_service.py` | 95% | L98-99 | ✅ Excellent |
| `src/api/infrastructure/ingest/counters.py` | 100% | — | ✅ Excellent |
| `src/api/infrastructure/ingest/queue.py` | 90% | L179-183,189,202-207,219,289,293-294,296,298 | ✅ Excellent |
| `src/api/infrastructure/db/repositories/sqlalchemy_ingest_repository.py` | 90% | L108-111,117-118,138 | ✅ Excellent |
| `src/api/presentation/routers/telemetry.py` | 87% | L54-58 (handler `ingest_exceptions`) | ⚠️ Acceptable |
| `src/api/presentation/schemas/ingest.py` | 100% | — | ✅ Excellent |
| `src/api/presentation/errors.py` | 100% | — | ✅ Excellent |
| `src/api/domain/entities/{user_session,rum_metric,js_exception}.py` | 100% | — | ✅ Excellent |
| `src/api/main.py` | 98% | L108 | ✅ Excellent |
| `src/api/config.py` | 100% | — | ✅ Excellent |

**Promedio de archivos cambiados**: ≥95% — todos ≥80% (sin WARNING de coverage).

### Assertion Quality

**Assertion quality**: ✅ All assertions verify real behavior. Los tests afirman status codes (400/401/403/503/202), códigos de error del contrato (`invalid_api_key`, `app_inactive`, `schema_validation_error`, `queue_full`), header `WWW-Authenticate: ApiKey`, `rejected[{index, reason}]` con índices originales, `accepted + len(rejected) == total`, tenant desde la key ≠ payload (IAUTH-2), persistencia real en Postgres (`rum_metric=2`, `js_exception=1`, `user_session.app_id=tenant`), retry transitorio con 3 llamadas y backoff, dead-letter con contador + log, drenado en shutdown y timeout logueado, logs redactados (key nunca en caplog), contadores `ingest.*` con valores exactos. Sin tautologías, ghost loops ni smoke-only; los fakes de repos implementan puertos (Protocol), no mocks excesivos.

### Spec Compliance Matrix

Requisitos: 18/18 (17 activos RUM-1..8, OAS-6/11/12, IAUTH-2/5, ARCH-1..4 + 1 REMOVED `Paths /metrics/ingest y /logs/ingest` verificado por OAS-10). Escenarios: 32/32.

| Req | Escenario | Test | Result |
|-----|-----------|------|--------|
| RUM-1 | Key ausente | `test_ingest_telemetry.py > test_telemetry_401_missing_key_with_www_authenticate` | ✅ COMPLIANT |
| RUM-1 | Key inválida | `test_ingest_telemetry.py > test_telemetry_exceptions_401_invalid_key_indistinguishable` (401 idéntico, fail-closed) | ✅ COMPLIANT |
| RUM-1 | Aplicación inactiva | `test_ingest_telemetry.py > test_telemetry_403_app_inactive` (403 + batch no procesado) | ✅ COMPLIANT |
| RUM-1 | Tenant desde la key (IAUTH-2) | `test_ingest_telemetry.py > test_telemetry_tenant_comes_from_key_not_payload` (tenant A, payload B) | ✅ COMPLIANT |
| RUM-2 | schema_version inválida | `test_ingest_telemetry.py > test_telemetry_422_becomes_400_schema_validation_error` (400 + nada encolado) + `test_envelope_schema_rejects_unknown_schema_version` | ✅ COMPLIANT |
| RUM-2 | Envelope sobre el límite | `test_ingest_telemetry.py > test_telemetry_422_becomes_400_for_501_events` + `test_envelope_schema_rejects_501_events` | ✅ COMPLIANT |
| RUM-3 | Batch mixto | `test_ingest_telemetry.py > test_telemetry_metrics_202_partial_rejection` + `test_service_process_batch_partial_rejection_with_index_and_reason` (rejected[{index:1, reason}], accepted+rejected=total) | ✅ COMPLIANT |
| RUM-3 | Batch íntegramente válido | `test_ingest_telemetry.py > test_service_process_batch_returns_202_with_batch_id_and_totals` (accepted N, rejected []) | ✅ COMPLIANT |
| RUM-3 | Batch íntegramente inválido | `test_ingest_telemetry.py > test_service_process_batch_all_invalid_returns_accepted_zero` (202, accepted 0, N índices) | ✅ COMPLIANT |
| RUM-4 | Valor fuera de rango | `test_ingest_telemetry.py > test_policy_rejects_ttfb_out_of_sanity_range_but_accepts_9000` (61000 invalid_range; 9000 aceptado) | ✅ COMPLIANT |
| RUM-4 | UUID inválido | `test_ingest_telemetry.py > test_policy_rejects_invalid_session_uuid` | ✅ COMPLIANT |
| RUM-4 | Unidad incoherente | `test_ingest_telemetry.py > test_policy_rejects_incoherent_unit` (JS_EXCEPTION_RATE con unit ms → invalid_unit) | ✅ COMPLIANT |
| RUM-4 | Evento sobredimensionado | `test_ingest_telemetry.py > test_policy_rejects_oversized_exception_stack_trace` (20001 chars → oversized_event) | ✅ COMPLIANT |
| RUM-4 | application_id ausente | `test_ingest_telemetry.py > test_policy_accepts_rum_without_application_id` (D2: aceptado, tenant de la key) | ✅ COMPLIANT |
| RUM-5 | Backpressure | `test_ingest_telemetry.py > test_telemetry_503_queue_full_when_queue_maxsize_1` + `test_queue_enqueue_when_full_raises_503_queue_full` (put_nowait, sin bloqueo) | ✅ COMPLIANT |
| RUM-5 | Encolado con capacidad | `test_ingest_telemetry.py > test_telemetry_202_enqueued_with_capacity` + `test_queue_accepts_events_with_capacity` | ✅ COMPLIANT |
| RUM-6 | Persistencia verificada | `test_ingest_telemetry.py > test_worker_persists_batch_to_postgres` (Postgres real: rum_metric=2, js_exception=1, user_session.app_id=tenant) | ✅ COMPLIANT |
| RUM-6 | Retry transitorio | `test_ingest_telemetry.py > test_worker_retries_transient_db_error_then_persists` (2 fallos + éxito en 3ª llamada, sin pérdida) | ✅ COMPLIANT |
| RUM-6 | Dead-letter | `test_ingest_telemetry.py > test_worker_sends_permanent_error_to_dead_letter` (IntegrityError → dead-letter log + contador, 1 llamada) | ✅ COMPLIANT |
| RUM-7 | Drenado en shutdown | `test_ingest_telemetry.py > test_queue_drains_pending_events_on_shutdown` (close→join→persistido antes de dispose) | ✅ COMPLIANT |
| RUM-7 | Timeout de drenado | `test_ingest_telemetry.py > test_queue_shutdown_timeout_logs_unpersisted_events` (timeout → log "1 events not persisted") | ✅ COMPLIANT |
| RUM-8 | Log de rechazo redactado | `test_ingest_telemetry.py > test_ingest_rejection_log_redacted_with_batch_id_index_reason` (batch_id/index/reason; key ausente de caplog, ADR-23) | ✅ COMPLIANT |
| RUM-8 | Contadores en proceso | `test_ingest_telemetry.py > test_ingest_counters_updated_on_http_request` + `test_service_process_batch_updates_counters` + `test_ingest_queue_depth_counter_reflects_enqueued` (received +3, accepted +2, rejected{reason} +1, queue_depth) | ✅ COMPLIANT |
| OAS-6 | Ingesta protegida | `test_contract.py > test_oas6_telemetry_paths_require_api_key` + `test_oas6_scheme_description_no_longer_defers_wiring` (security apiKey + 401/403 declarados junto a 202/400/503) | ✅ COMPLIANT |
| OAS-11 | Contrato de respuestas completo | `test_contract.py > test_oas11_telemetry_paths_declare_request_body_and_responses` (requestBody + 202/400/401/403/503/429; 429 sin impl, D3) | ✅ COMPLIANT |
| OAS-12 | Schemas alineados con IAUTH-2 | `test_contract.py > test_oas12_application_id_not_required_and_no_unknown_application` | ✅ COMPLIANT |
| IAUTH-5 | Wiring a producción | `test_ingest_auth.py > test_prod_app_wires_api_key_guard_to_telemetry_paths` (test invertido: cubre exactamente {/telemetry/metrics, /telemetry/exceptions}) | ✅ COMPLIANT |
| IAUTH-2 | Payload sin autoridad | `test_ingest_telemetry.py > test_service_process_batch_queued_event_carries_tenant_from_key` + `test_policy_accepts_rum_without_application_id` + `test_policy_has_no_unknown_application_code` | ✅ COMPLIANT |
| ARCH-1 | Tabla y snippets alineados | grep verificado: `interfaces.md` §1.1 con `POST /telemetry/metrics`/`/telemetry/exceptions`, sin `/metrics/ingest` ni `/logs/ingest` | ✅ COMPLIANT |
| ARCH-2 | Árbol y mermaid sincronizados | grep verificado: `components.md` árbol con `telemetry.py` (antes routers/ingest.py) y mermaid con `POST /telemetry/metrics` | ✅ COMPLIANT |
| ARCH-3 | Artefacto renombrado | grep verificado: `quality-attributes.md` artefacto `Endpoint POST /telemetry/metrics` | ✅ COMPLIANT |
| ARCH-4 | Docs vivas sin rutas viejas | grep verificado: `PipelineIngestaRUM.md`, `ContratoIngestaRUM.md`, `brief-v2.md` con `/telemetry/*` y semántica 202/503; históricos `informe-avance-1/` e `issues-s1-s2.md` conservan rutas viejas | ✅ COMPLIANT |

**Compliance summary**: 32/32 escenarios con test pasando en ejecución independiente (los escenarios ARCH-1..4 por inspección de archivos + suite de contrato).

### Correctness (Static Evidence)

| Requisito | Status | Notas |
|-----------|--------|-------|
| RUM-1 | ✅ Implementado | Router `telemetry.py` con `Depends(require_api_key)` en ambos POST; 401 `invalid_api_key` + `WWW-Authenticate: ApiKey`; 403 `app_inactive`; tenant = app autenticada |
| RUM-2 | ✅ Implementado | Envelope estricto en `schemas/ingest.py` (schema_version 1.0, 1..500 events) → 422 → handler scoped → 400 `schema_validation_error` (D5); nada se encola |
| RUM-3 | ✅ Implementado | `IngestService.process_batch`: batch_id uuid4, 202 al encolar, `rejected[{index, reason}]`, accepted + rejected = total |
| RUM-4 | ✅ Implementado | `ingest_policy.py` puro: 7 códigos (missing_required_field, invalid_uuid, invalid_metric_type, invalid_unit, invalid_range, invalid_timestamp, oversized_event), límites 500/50, rangos de cordura, ratings no rechazan, sin `unknown_application` (D2) |
| RUM-5 | ✅ Implementado | Puerto `IngestQueue` (Protocol enqueue/close/join) + `AsyncioIngestQueue` (asyncio.Queue maxsize default 10000); `put_nowait` → `ServiceUnavailableError` 503 `queue_full` |
| RUM-6 | ✅ Implementado | Worker: `user_session` ON CONFLICT DO NOTHING con app_id de la key, bulk `rum_metric` (type→metric_type_id catálogo cacheado) y `js_exception` (metric_id inexistente→NULL + contador), chunks 500, retry 3 backoff 0.5/1/2 transitorios, dead-letter log + `ingest.persistence_dead_letter_total` (D1) |
| RUM-7 | ✅ Implementado | Lifespan: `close()` → `join(timeout=ingest_shutdown_timeout)` → log no persistidos → `dispose_engine()` (D6) |
| RUM-8 | ✅ Implementado | Logs estructurados por rechazo (batch_id/index/reason, ADR-23 redacción); contadores `ingest.received_total`/`accepted_total`/`rejected_total{reason}`/`queue_depth`/`persisted_total`/`persistence_dead_letter_total`/`metric_id_unknown_total`; sin prometheus-client ni endpoint `/metrics` (D4) |
| OAS-6/11/12 | ✅ Implementado | openapi.yaml: `security: [apiKey]` en `/telemetry/*`, requestBody RumEventBatch/JsExceptionBatch, respuestas 202/400/401/403/503/429 (429 sin impl, D3), scheme descripción actualizada, `application_id` fuera de required, sin `unknown_application` |
| IAUTH-2/5 | ✅ Implementado | Guard cableado a `/telemetry/*` (test invertido); tenant exclusivo de la key; `application_id` opcional e ignorado como autoridad |
| ARCH-1..4 | ✅ Implementado | interfaces/components/quality-attributes.md + PipelineIngestaRUM/ContratoIngestaRUM/brief-v2.md alineados a `/telemetry/*`; históricos intactos; ADR-0002 + CHANGELOG registrados (task 5.2) |

### Coherence (Design)

| Decisión | Followed? | Notas |
|----------|-----------|-------|
| D1 (persistencia a BD) | ✅ Yes | `SQLAlchemyIngestRepository.persist_chunk`: ON CONFLICT DO NOTHING, bulk inserts, catálogo cacheado; verificado con Postgres real |
| D2 (application_id sin autoridad, sin unknown_application) | ✅ Yes | Fuera de `required` en Pydantic y OpenAPI; `unknown_application` ausente del flujo (solo aparece en asserts de ausencia); tenant fijado en encolado |
| D3 (429 declarado sin impl) | ✅ Yes | 429 `rate_limit_exceeded` declarado en openapi.yaml (3 respuestas); grep en `src/` sin implementación |
| D4 (sin prometheus-client) | ✅ Yes | Sin dependencia en pyproject.toml; contadores en proceso (`counters.py`); sin endpoint `/metrics` |
| D5 (422→400 scoped /telemetry/*) | ✅ Yes | `validation_error_handler` en `errors.py` + registro en `main.py`; test de regresión confirma 422 intacto en `/applications` |
| D6 (drenado en shutdown) | ✅ Yes | Lifespan `close → join(timeout) → log → dispose_engine`; tests de drenado y timeout |
| DD-1..DD-7 | ✅ Yes | Puerto `IngestQueue` + asyncio.Queue acotada (DD-1); política pura (DD-2); worker con chunks/retry/dead-letter (DD-3/4); handler scoped (DD-5); shutdown ordenado (DD-6); ADR-0002 Nygard (DD-7) |

### Nomenclatura (criterio 8 de #37)

| Superficie | `/metrics/ingest` / `/logs/ingest` | Resultado |
|------------|------------------------------------|-----------|
| `openspec/specs/openapi.yaml` | Ausentes (test OAS-10 PASSED) | ✅ |
| Implementación `src/` | Ausentes (grep sin resultados) | ✅ |
| Tests | Solo aserciones de ausencia (`assert "/metrics/ingest" not in doc["paths"]`) | ✅ |
| Schemathesis | Scope `/(health|ready|auth|users|applications|telemetry)` | ✅ |
| Docs vivas (PipelineIngestaRUM, ContratoIngestaRUM, brief-v2) | Ausentes | ✅ |
| Specs de arquitectura | Ausentes | ✅ |
| Frontend | No existe directorio frontend en el repo | ✅ |
| Históricos (`docs/informe-avance-1/`, `docs/business/issues-s1-s2.md`) | Conservan rutas viejas (registros intactos) | ✅ |
| CHANGELOG.md / ADR-0002 | Referencias históricas a la decisión S1 (registro del cambio, no funcionales) | ✅ |

### Issues Found

**CRITICAL**: None

**WARNING**: None

**SUGGESTION**:
- **SUG-1 — flake8 no cubre `tests/`**: el gate configurado es `flake8 src/` (limpio), pero `flake8 tests/` reporta E501 (línea 177, 100 > 99 chars) y W292 (sin newline al final) en `test_ingest_telemetry.py`. Trivial y fuera del gate; corregible en apply si se decide incluir tests en el lint.
- **SUG-2 — Handler `ingest_exceptions` sin ejercicio HTTP directo con key válida**: `telemetry.py` 87% (L54-58 = `ingest_exceptions`); el 202 de `/telemetry/exceptions` con key válida no tiene test HTTP propio (la lógica duplicada se cubre vía `/telemetry/metrics` + service con `JsExceptionBatch`). Coverage ≥80% (Acceptable); sin impacto de comportamiento.
- **SUG-3 — Premisa experimental de OAS-9 superada (ADR-24)**: schemathesis 4.x trae OpenAPI 3.1 nativo; `test_schemathesis_live_contract_scoped` xpassed (mismo patrón que SUG-2 de ISS-S2-02). Documentado; el gate queda verde.
- **SUG-4 — Conteo de requisitos 18/18**: la spec declara 18 headings `### Requirement:` (17 activos + REMOVED `Paths /metrics/ingest y /logs/ingest`); el reporte refleja 18/18 con el REMOVED verificado como evidencia de eliminación (`test_oas10_ingest_paths_replaced_by_telemetry`, PASSED), habilitando el conteo nativo del dispatcher para archive.

### Verdict

**PASS** — Suite completa 209 passed + 1 xpassed (exit 0), cobertura 93.06% ≥ 70%, flake8 src/ limpio y pylint 8.93/10 ≥ 7.0. Build `docker compose build intellops-core` exit 0. Contrato openapi.yaml válido con `/telemetry/*` exigiendo `apiKey`, paths viejos eliminados, `application_id` fuera de `required` y sin `unknown_application`. 32/32 escenarios de spec con test pasando en ejecución independiente; 18/18 requisitos con evidencia (17 activos + 1 REMOVED verificado como evidencia de eliminación). Decisiones D1–D6 y DD-1..7 reflejadas en el código. Persistencia real en Postgres, retry/dead-letter, drenado en shutdown y contadores en proceso verificados. Nomenclatura `/telemetry/*` sin referencias funcionales a rutas viejas; históricos intactos. Sin hallazgos críticos ni blockers.