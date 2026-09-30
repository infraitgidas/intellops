```yaml
schema: gentle-ai.verify-result/v1
evidence_revision: sha256:1c8ce65112eaf37eaee167728c9e5283e2d68d1827e0b2521985404f366098b9
verdict: pass
blockers: 0
critical_findings: 0
requirements: 7/7
scenarios: 12/12
test_command: PYTHONPATH=. .venv/bin/pytest --cov=src --cov-report=term-missing -q --no-header
test_exit_code: 0
test_output_hash: sha256:7376e95edd6a39addeab60022afaf7e65306d01ca4aac49be1156fcf70252d88
build_command: docker compose build intellops-core
build_exit_code: 0
build_output_hash: sha256:e1a01d1cf9f7efe6b3e519be49c174fe5bcff62e0d489ddc0a15719d5dd98e51
```

## Verification Report

**Change**: ISS-S3-01 — Persistencia de telemetría (verificación + hardening + read path) (GitHub #40)
**Version**: spec.md (delta, 2026-09-29)
**Mode**: Strict TDD (config.yaml `apply.tdd:true`, `testing.strict_tdd:true`, runner pytest)
**Rama**: working tree sobre develop (HEAD = 1707caf, PR #55/ISS-S2-03 mergeado) — cambio sin commitear, verificado contra el árbol actual
**Fecha**: 2026-09-29
**Tipo de verificación**: Independiente y fresca — suite completa re-ejecutada contra el estado actual del árbol (working tree). `evidence_revision` = SHA-256 del tree hash (`git rev-parse HEAD^{tree}` → `sha256:` + digest).

### Completeness

| Metric | Value |
|--------|-------|
| Tasks total | 14 |
| Tasks complete | 14 |
| Tasks incomplete | 0 |

Todas las tareas de `tasks.md` están marcadas `[x]` (verificado: 14 checkboxes, 14 completas; fases 1–5). Requisitos: 7/7 headings `### Requirement:` de la spec (RUM-9, RUM-10, RUM-11, TQ-1, TQ-2, OAS-13, OAS-14). Escenarios: 12/12 headings `#### Scenario:`.

### Build & Tests Execution

**Build**: ✅ Passed (`docker compose build intellops-core`, exit 0)
```text
#18 DONE 0.0s
 Image intellops-intellops-core Built
```
- Dockerfile sin cambios en este cambio; CMD `alembic upgrade head && uvicorn api.main:app` intacto.

**Tests**: ✅ 226 passed / 0 failed / 1 xpassed
```text
PYTHONPATH=. .venv/bin/pytest --cov=src --cov-report=term-missing -q --no-header
================= 226 passed, 1 xpassed, 36 warnings in 42.74s =================
```
- El xpass corresponde a `test_schemathesis_live_contract_scoped` (xfail documentado, ADR-24): la corrida live de schemathesis contra la app ASGI valida casos reales y pasa — el gate contract queda verde.
- Focussed re-runs secuenciales (sin interferencia de DB compartida): `test_metrics_query.py test_contract.py` → 19 passed + 1 xpassed; `test_ingest_telemetry.py -k "foreign or correlation or ownership or persist_stats or query_range"` → 8 passed.

**Coverage**: 93.91% / threshold 70% → ✅ Above
```text
Required test coverage of 70.0% reached. Total coverage: 93.91%
```

**Lint**: ✅ `flake8 src/ tests/` exit 0 (max-line-length=99). **Pylint**: ✅ `pylint src/ --fail-under=7.0` 9.72/10 ≥ 7.0 (única nota informativa: R0801 duplicate-code entre `query_repository.py` y `schemas/metrics.py`, DTOs del mismo shape).

**openapi.yaml**: ✅ válido — `test_oas9_openapi_document_loads_in_schemathesis` PASSED (carga 3.1, ≥30 operaciones). Verificación estructural independiente + ASGI smoke: operationIds `queryMetrics`/`listMetrics` intactos, `security: [apiKey]` en `/metrics/query` y `/metrics/list`, parámetros `start`/`end`/`bucket_seconds`/`metric_type`, respuestas 200/401/403/422, schemas `MetricAggregate`/`MetricTypeInfo`. Runtime: 401 `invalid_api_key` + `WWW-Authenticate: ApiKey` en ambos paths sin key (OAS-14).

**Schemathesis scoped metrics**: ✅ 10 casos validados contra la app ASGI real (`path_regex=/metrics/(query|list)`), exit 0 — ejercita 401/422 y shape 200 contra el spec 3.1.

### TDD Compliance

| Check | Result | Details |
|-------|--------|---------|
| TDD Evidence reported | ✅ | `apply-progress.md` con tabla "TDD Cycle Evidence" (14 filas) + "Work Unit Evidence" |
| All tasks have tests | ✅ | 14/14 tareas con test file verificado en el repo (`test_ingest_telemetry.py`, `test_metrics_query.py`, `test_contract.py`) |
| RED confirmed (tests exist) | ✅ | Archivos de test verificados; RED declarado por tarea (task 1.2 puramente estructural, skip anotado por regla strict-tdd: puerto Protocol + DTOs frozen sin branching) |
| GREEN confirmed (tests pass) | ✅ | 226 passed + 1 xpassed en ejecución independiente (exit 0) |
| Triangulation adequate | ✅ | 12 escenarios spec cubiertos por tests unit + integración + contract; valores distintos por comportamiento (session_foreign=2 vs 0, metric_id NULL vs conservado, AVG 700/3 vs 300, 401/422/200) |
| Safety Net for modified files | ✅ | Archivos nuevos (`query_repository.py`, `sqlalchemy_query_repository.py`, `query_service.py`, `metrics.py`, `schemas/metrics.py`, `test_metrics_query.py`) untracked previo (git status) → `N/A (new)` correcto; archivos modificados con suite completa previa 209/209 |

**TDD Compliance**: 6/6 checks passed

### Test Layer Distribution

| Layer | Tests | Files | Tools |
|-------|-------|-------|-------|
| Unit | ~10 (QueryService límites/defaults, PersistStats, QueryRangeError, contadores ownership RUM-11) | `test_metrics_query.py`, `test_ingest_telemetry.py` | pytest |
| Integration (Postgres real + httpx ASGI) | ~10 (C5 collision/replay, reenvío mismo tenant, correlación cross-app/legítima/inexistente, shape ML/buckets/app-scoped, 422/401 HTTP, /metrics/list) | `test_ingest_telemetry.py`, `test_metrics_query.py` | pytest + httpx AsyncClient + SQLAlchemy async |
| Contract | 13 (12 passed + 1 xpassed) | `test_contract.py` | schemathesis 4.28 + yaml |
| **Total** | **227 colectados (226 passed + 1 xpassed)** | **3 changed + suite completa** | |

### Changed File Coverage

| File | Line % | Uncovered | Rating |
|------|--------|-----------|--------|
| `src/api/domain/repositories/ingest_repository.py` | 100% | — | ✅ Excellent |
| `src/api/domain/exceptions.py` | 100% | — | ✅ Excellent |
| `src/api/domain/repositories/query_repository.py` | 100% | — | ✅ Excellent |
| `src/api/domain/services/query_service.py` | 97% | L71 | ✅ Excellent |
| `src/api/infrastructure/db/repositories/sqlalchemy_ingest_repository.py` | 99% | L213 | ✅ Excellent |
| `src/api/infrastructure/db/repositories/sqlalchemy_query_repository.py` | 96% | L79 (rama filtro `metric_type`) | ✅ Excellent |
| `src/api/infrastructure/ingest/counters.py` | 100% | — | ✅ Excellent |
| `src/api/infrastructure/ingest/queue.py` | 91% | L179-183, 189, 202-207, 293, 297-298, 300, 302 | ✅ Excellent |
| `src/api/presentation/routers/metrics.py` | 100% | — | ✅ Excellent |
| `src/api/presentation/schemas/metrics.py` | 100% | — | ✅ Excellent |
| `src/api/main.py` | 98% | L109 | ✅ Excellent |

**Average changed file coverage**: 98.3% — todos ≥ 91% (sin WARNING de coverage).

### Assertion Quality

**Assertion quality**: ✅ All assertions verify real behavior. Los tests de este cambio afirman persistencia real en Postgres (`rum_metric=1` solo de A, `js_exception=0` descartada, `user_session.app_id == app_a` intacto), contadores exactos (`ingest.session_foreign_total == 2` vs `== 0`, `metric_id_foreign_total == 1` vs `== 0`, `metric_id_unknown_total == 1`), shape ML exacto (set de 5 keys), `value == 100.0`/`approx(700/3)` y `session_count == 2` (COUNT DISTINCT), 1 fila por bucket con timestamps anclados al `:start`, 422 `invalid_query_range` (con `repo.called is False` — la agregación nunca se ejecutó), 401 `invalid_api_key` + `WWW-Authenticate` en ambos paths. Sin tautologías, ghost loops, smoke-only ni mocks excesivos (fakes de repo implementan puertos Protocol).

### Spec Compliance Matrix

Requisitos: 7/7. Escenarios: 12/12.

| Req | Escenario | Test | Result |
|-----|-----------|------|--------|
| RUM-9 | Replay cross-tenant (C5) | `test_ingest_telemetry.py > test_worker_drops_foreign_session_rows_cross_tenant` (BD: filas de B no persistidas, `app_id` intacto, `session_foreign_total=2`) | ✅ COMPLIANT |
| RUM-9 | Reenvío del mismo tenant | `test_ingest_telemetry.py > test_worker_same_tenant_resend_is_noop_without_foreign_counter` (no-op, sin contador, `persisted_total=1`) | ✅ COMPLIANT |
| RUM-10 | Reivindicación cross-app | `test_ingest_telemetry.py > test_worker_correlation_cross_app_metric_id_is_null_and_counted` (`metric_id` NULL + `metric_id_foreign_total=1`) | ✅ COMPLIANT |
| RUM-10 | Reivindicación legítima | `test_ingest_telemetry.py > test_worker_correlation_legitimate_keeps_metric_id` (`metric_id` conservado, contadores 0) | ✅ COMPLIANT |
| RUM-11 | Snapshot con descartes | `test_ingest_telemetry.py > test_counters_snapshot_exposes_ownership_keys` + asserts de snapshot en C5/correlación (keys `ingest.session_foreign_total`/`ingest.metric_id_foreign_total` con valores exactos; resto de keys presentes) | ✅ COMPLIANT |
| TQ-1 | Shape ML exacto | `test_metrics_query.py > test_metrics_query_shape_ml_exact_and_app_scoped` (5 campos, solo A, `session_count=1`) | ✅ COMPLIANT |
| TQ-1 | Agregación por bucket | `test_metrics_query.py > test_metrics_query_one_row_per_bucket_with_avg_and_distinct_count` (2 buckets, AVG 700/3, COUNT DISTINCT 2) | ✅ COMPLIANT |
| TQ-2 | Rango fuera de límite | `test_metrics_query.py > test_service_rejects_out_of_bounds_without_calling_repo` (unit, repo nunca llamado) + `test_metrics_query_422_invalid_range` (HTTP 422 `invalid_query_range`) | ✅ COMPLIANT |
| OAS-13 | Contrato intacto | `test_contract.py > test_oas13_metrics_paths_complete_contract` + `test_oas13_metric_aggregate_shape_ml` (operationIds/security/params/respuestas/required) + schemathesis scoped 10 casos | ✅ COMPLIANT |
| OAS-13 | Respuesta con shape ML | `test_metrics_query.py > test_metrics_query_shape_ml_exact_and_app_scoped` (200 con 5 campos de la app autenticada) + `test_oas13_metric_aggregate_shape_ml` | ✅ COMPLIANT |
| OAS-14 | Sin key | `test_metrics_query.py > test_metrics_query_and_list_401_without_key` (401 + WWW-Authenticate en ambos paths) + ASGI smoke independiente | ✅ COMPLIANT |
| OAS-14 | Aislamiento por key | `test_metrics_query.py > test_metrics_query_shape_ml_exact_and_app_scoped` (datos de B invisibles para key de A; tenant solo de la key, sin parámetro de app) | ✅ COMPLIANT |

**Compliance summary**: 12/12 escenarios con test pasando en ejecución independiente.

### Correctness (Static Evidence)

| Requisito | Status | Notas |
|-----------|--------|-------|
| RUM-9 | ✅ Implementado | `_upsert_sessions` SELECT por PK pre-insert → `set[UUID]` de extranjeras (DD-8); `persist_chunk` filtra metrics/exceptions de sesiones extranjeras y cuenta en `PersistStats.session_foreign` → `ingest.session_foreign_total` |
| RUM-10 | ✅ Implementado | `_bulk_exceptions` recibe `session_tenants` (session_id→app_id del lote): `metric_id` solo se reivindica si la métrica existe Y su sesión es del tenant de la excepción; cross-app → NULL + `metric_id_foreign`; inexistente → NULL + `metric_id_unknown` |
| RUM-11 | ✅ Implementado | `IngestCounters.session_foreign(n)`/`metric_id_foreign(n)` + keys `ingest.session_foreign_total`/`ingest.metric_id_foreign_total` en `snapshot()` (naming contract `ingest.` + `_total`); worker de `queue.py` incrementa desde `PersistStats` |
| TQ-1 | ✅ Implementado | `SQLAlchemyQueryRepository.query_metrics`: una sentencia SQL con JOIN `user_session`→`rum_metric` app-scoped, GROUP BY `metric_type_id` + bucket epoch anclado a `:start`, `AVG(value)::float` + `COUNT(DISTINCT session_id)` → shape `MetricAggregate` (5 campos C6) sin materializar filas |
| TQ-2 | ✅ Implementado | `QueryService` acota antes del repo: default 15 min, ≤ 7 d, bucket ≥ 60 s, `start < end` → `QueryRangeError` 422 `invalid_query_range` (ADR-09); plan indexado (idx existentes), CPU-only, sin dependencias nuevas |
| OAS-13 | ✅ Implementado | openapi.yaml 124-137 completado: security apiKey, parámetros, respuestas 200/401/403/422 + schemas `MetricAggregate`/`MetricTypeInfo`; operationIds y paths intactos (diff verificado) |
| OAS-14 | ✅ Implementado | Router `metrics.py`: ambos GET con `Depends(require_api_key)` + `Depends(get_session)`; tenant exclusivo de la key (sin parámetro de aplicación); 401 `invalid_api_key` sin key |

### Coherence (Design)

| Decisión | Followed? | Notas |
|----------|-----------|-------|
| DD-8 (ownership en `_upsert_sessions`, SELECT pre-insert) | ✅ Yes | SELECT por PK ≤ 500 ids antes del insert; extranjeras → descarte + contador; sin TOCTOU (mismo AsyncSession del chunk); sin DDL |
| DD-9 (agregación EN SQL, sin materializar) | ✅ Yes | Una sentencia `SELECT ... GROUP BY metric_type_id + bucket` (epoch anclado a `:start`), `AVG` + `COUNT(DISTINCT session_id)`; el proceso recibe solo filas agregadas |
| DD-10 (contadores por el mecanismo `snapshot()` existente) | ✅ Yes | Keys `ingest.session_foreign_total`/`ingest.metric_id_foreign_total`; `PersistStats` con defaults 0 (compat mocks); wiring mínimo en `queue.py`; sin prometheus-client |
| ADR-0003 (Nygard, DD-8/9/10) | ✅ Yes | `docs/adr/0003-ownership-tenant-read-path.md` con contexto C2-C4, decisión, consecuencias (positivas/negativas), alternativas y recursos |

**Desviaciones documentadas (apply-progress, ninguna rompe spec)**: (1) router sin `ge=60` en `bucket_seconds` — la validación vive en `QueryService` para emitir 422 `invalid_query_range` con el envelope ErrorResponse (el `ge=60` de Pydantic rompería el contrato de error OAS-13); (2) `func.avg(...).cast(Float)` (tipo SQL, no builtin) por cache key de SQLAlchemy; (3) correlación scoped por sesión→tenant del lote (no JOIN global por `app_id`) para cubrir chunks multi-tenant; (4) `/metrics/list` declara 422 por completitud del contrato OAS-13.

### Issues Found

**CRITICAL**: None

**WARNING**:
- **W-1 — Colisión same-chunk de primera vez (residual, fuera de scope)**: dos tenants enviando el MISMO `session_id` NUEVO en el mismo chunk no se detecta en el SELECT pre-insert (ninguno existe aún); `ON CONFLICT DO NOTHING` conserva una de las filas y las métricas del otro tenant quedan bajo esa sesión. Documentado en ADR-0003 (Negativas) y apply-progress. La spec C5 cubre sesión YA persistida (cumplida); la mitigación futura (índice único `(session_id, app_id)` o dedup intra-chunk) requiere DDL y queda fuera de scope. No bloquea delivery.

**SUGGESTION**:
- **SUG-1 — Rama de filtro `metric_type` sin test end-to-end**: `sqlalchemy_query_repository.py` L79 (filtro opcional `metric_type_id`) queda sin cubrir (96%); el parámetro está declarado en el contrato y delegado, pero ningún test HTTP ejerce el filtro. Coverage ≥ 80% (Acceptable); sin impacto de comportamiento.
- **SUG-2 — Pylint R0801 duplicate-code**: `query_repository.py:25-32` y `schemas/metrics.py:16-23` comparten el shape de 5 campos (DTOs planos por diseño, capas distintas); informativo, sin acción requerida.
- **SUG-3 — `QueryService._as_utc` L71 sin cubrir (97%)**: rama defensiva de datetime naive; sin impacto funcional.

### Verdict

**PASS** — Suite completa 226 passed + 1 xpassed (exit 0), cobertura 93.91% ≥ 70%, `flake8 src/ tests/` limpio y pylint 9.72/10 ≥ 7.0. Build `docker compose build intellops-core` exit 0. Contrato openapi.yaml válido: operationIds `queryMetrics`/`listMetrics` intactos con `security: [apiKey]`, parámetros y respuestas 200/401/403/422; schemathesis scoped a metrics (10 casos) verde; ASGI smoke 401 `invalid_api_key` + `WWW-Authenticate` en ambos GET. 12/12 escenarios de spec con test pasando en ejecución independiente (7/7 requisitos). Decisiones DD-8/DD-9/DD-10 reflejadas en el código y ADR-0003. Ownership de sesión (C5) y correlación `metric_id` scoped verificados con Postgres real; agregación 100% en SQL, sin DDL nuevo, sin dependencias nuevas, CPU-only. Un WARNING residual documentado (colisión same-chunk de primera vez, fuera de scope de la spec) — no bloquea.