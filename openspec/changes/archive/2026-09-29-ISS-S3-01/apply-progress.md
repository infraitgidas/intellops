# Apply Progress — ISS-S3-01 (Persistencia de telemetría: verificación + hardening + read path)

**Change**: 2026-09-29-ISS-S3-01
**Mode**: Strict TDD (pytest, Postgres real + httpx ASGI + schemathesis)
**Store**: openspec (tasks.md checkboxes + este archivo) + Engram (topic `sdd/2026-09-29-ISS-S3-01/apply-progress`)
**Delivery**: single-pr con `size:exception` aprobado por maintainer (forecast 900-1300 líneas; NO se parte el PR).

## Estado

13/13 tareas completas. **Ready for verify.**

## TDD Cycle Evidence

| Task | Test File | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|------|-----------|-------|------------|-----|-------|-------------|----------|
| 1.1 | tests/test_ingest_telemetry.py | Unit | ✅ 209/209 | ✅ Written (2) | ✅ Passed | ✅ 3 casos (PersistStats default+explicit, QueryRangeError) | ➖ None needed |
| 1.2 | (port estructural) | Unit | N/A (new) | ✅ DTOs referenciados por 1.5 | ✅ Created | ➖ Single (puramente estructural — anotado) | ➖ None needed |
| 1.3 | tests/test_ingest_telemetry.py | Integration | ✅ 71/71 | ✅ Written (2: C5 + reenvío) | ✅ Passed | ✅ 2 casos | ✅ Clean |
| 1.4 | tests/test_ingest_telemetry.py | Integration | ✅ 71/71 | ✅ Written (3: cross-app/legítima/inexistente) | ✅ Passed | ✅ 3 casos | ✅ Clean |
| 1.5 | tests/test_metrics_query.py | Integration+Unit | N/A (new) | ✅ Written (7) | ✅ Passed | ✅ 7 casos | ✅ Clean (2 fixes: cast Float, email único) |
| 2.1 | (vía 1.3/1.4) | Integration | ✅ 71/71 | ✅ (RED 1.3/1.4) | ✅ Passed | ✅ 3 caminos | ✅ Clean |
| 2.2 | tests/test_ingest_telemetry.py | Unit | ✅ 71/71 | ✅ Written (RUM-11) | ✅ Passed | ✅ 1 caso + integración | ✅ Clean |
| 2.3 | (vía 1.5) | Integration | N/A (new) | ✅ (RED 1.5) | ✅ Passed | ✅ 2 shapes | ✅ Clean (cast Float fix) |
| 2.4 | tests/test_metrics_query.py | Unit | N/A (new) | ✅ Written | ✅ Passed | ✅ 4 límites + defaults | ✅ Clean |
| 3.1 | (vía 1.5) | Integration | N/A (new) | ✅ (RED 1.5) | ✅ Passed | ✅ 2 endpoints | ✅ Clean (quitado ge=60 del router) |
| 3.2 | tests/test_contract.py | Contract | ✅ 12/12 | ✅ Written (OAS-13 estructural) | ✅ Passed | ✅ 2 schemas | ✅ Clean |
| 4.1 | tests/test_contract.py | Contract | ✅ 12/12 | ✅ Written | ✅ Passed | ✅ regex scoped + 2 tests | ✅ Clean |
| 4.2 | suite completa | All | ✅ 209/209 | — (gate, no feature) | ✅ 226 passed 94% cov | — | — |
| 5.1 | docs | Docs | N/A (new) | — | ✅ ADR + CHANGELOG | — | — |

Triangulación 1.2: tarea puramente estructural (puerto Protocol + DTOs frozen sin lógica) — se anota el skip por regla del módulo strict-tdd (una sola salida posible, sin branching).

## Work Unit Evidence

| Evidence | Required value |
|---|---|
| Focused test command and exact result | `pytest tests/test_ingest_telemetry.py -q` → 71 passed; `pytest tests/test_metrics_query.py tests/test_contract.py -q` → 19 passed 1 xpassed; `pytest tests/ --cov=src` → 226 passed, 1 xpassed, 93.91% |
| Runtime harness command/scenario and exact result | httpx ASGI + Postgres real (conftest `db_session`/`client`): C5 collision/replay (sesión de B descartada, `user_session.app_id` intacto, `session_foreign_total=2`), shape ML/buckets con AVG+COUNT(DISTINCT), 422 `invalid_query_range`, 401 sin key, /metrics/list catálogo; schemathesis scoped sobre `_SCOPED_PATH_RE` += metrics (12 passed 1 xpassed) |
| Rollback boundary | Revert del PR: sin DDL nuevo. Files: `src/api/infrastructure/db/repositories/sqlalchemy_ingest_repository.py`, `src/api/infrastructure/ingest/counters.py`, `src/api/infrastructure/ingest/queue.py`, `src/api/domain/repositories/query_repository.py`, `src/api/infrastructure/db/repositories/sqlalchemy_query_repository.py`, `src/api/domain/services/query_service.py`, `src/api/presentation/routers/metrics.py`, `src/api/presentation/schemas/metrics.py`, `src/api/main.py`, `src/api/domain/exceptions.py`, `src/api/domain/repositories/ingest_repository.py`, `openspec/specs/openapi.yaml`, `tests/test_metrics_query.py`, `tests/test_ingest_telemetry.py`, `tests/test_contract.py`, `docs/adr/0003-*.md`, `CHANGELOG.md` |

## Files Changed

| File | Action | What Was Done |
|------|--------|---------------|
| `src/api/domain/repositories/ingest_repository.py` | Modified | `PersistStats` + `session_foreign`/`metric_id_foreign` (defaults 0, DD-10) |
| `src/api/domain/exceptions.py` | Modified | `QueryRangeError` (422 `invalid_query_range`, ADR-09) |
| `src/api/domain/repositories/query_repository.py` | Created | Puerto `QueryRepository` (Protocol) + DTOs `MetricAggregate` (5 campos C6) y `MetricTypeInfo` |
| `src/api/infrastructure/db/repositories/sqlalchemy_ingest_repository.py` | Modified | `_upsert_sessions` → `set[UUID]` de sesiones extranjeras (SELECT pre-insert, DD-8); `persist_chunk` filtra + cuenta descartes; `_bulk_exceptions` correlación scoped por ownership (RUM-10) |
| `src/api/infrastructure/ingest/counters.py` | Modified | `session_foreign`/`metric_id_foreign` + keys snapshot `ingest.session_foreign_total`/`ingest.metric_id_foreign_total` |
| `src/api/infrastructure/ingest/queue.py` | Modified | Worker incrementa contadores desde `PersistStats` |
| `src/api/infrastructure/db/repositories/sqlalchemy_query_repository.py` | Created | `query_metrics` SQL agregado (epoch-bucket anclado a :start, AVG + COUNT DISTINCT, JOIN app-scoped) + `list_metric_types` |
| `src/api/domain/services/query_service.py` | Created | Límites TQ-2 (default 15 min, ≤ 7 d, bucket ≥ 60 s, start < end → 422 sin tocar repo) |
| `src/api/presentation/schemas/metrics.py` | Created | `MetricAggregateOut`, `MetricTypeInfoOut` |
| `src/api/presentation/routers/metrics.py` | Created | `GET /metrics/query` (`queryMetrics`) + `GET /metrics/list` (`listMetrics`), ambos `require_api_key` + `get_session` |
| `src/api/main.py` | Modified | `app.include_router(metrics.router)` |
| `openspec/specs/openapi.yaml` | Modified | 124-137 completado: security apiKey, parámetros, respuestas 200/401/403/422 + schemas `MetricAggregate`/`MetricTypeInfo`; operationIds intactos |
| `tests/test_ingest_telemetry.py` | Modified | C5 collision/replay, reenvío mismo tenant, correlación cross-app/legítima/inexistente, RUM-11 snapshot, PersistStats/QueryRangeError |
| `tests/test_metrics_query.py` | Created | TQ-1 shape/buckets/app-scoped, TQ-2 límites (unit sin tocar repo + HTTP 422), OAS-14 401/aislamiento, /metrics/list |
| `tests/test_contract.py` | Modified | OAS-13 estructural (2 tests) + `_SCOPED_PATH_RE` += metrics |
| `docs/adr/0003-ownership-tenant-read-path.md` | Created | ADR Nygard (DD-8/DD-9/DD-10) |
| `CHANGELOG.md` | Modified | Registro ISS-S3-01 |

## Test Results (evidence goal)

- `pytest --cov=src`: **226 passed, 1 xpassed, 93.91%** (threshold 70% ✓)
- `flake8 src/ tests/`: **clean**
- `pylint src/ --fail-under=7.0`: **9.72/10** (threshold 7.0 ✓)
- openapi.yaml: válido (yaml.safe_load + aserciones OAS-13 OK); schemathesis scoped xpass

## Deviations from Design

1. **Router sin `ge=60` en `bucket_seconds`**: el diseño delega la validación del bucket en `QueryService` (→ 422 `invalid_query_range` con el envelope ErrorResponse). FastAPI `ge=60` devolvería el 422 estándar de validación Pydantic (body `detail`), rompiendo el contrato de error OAS-13. Se quitó del query param; el servicio valida.
2. **`func.avg(...).cast(Float)` (no `cast(float)`)**: `cast(float)` (builtin Python) rompía el cache key de SQLAlchemy (`AttributeError: 'float' object has no attribute '_static_cache_key'`). Corregido con el tipo SQL `Float`.
3. **Correlación scoped por sesión→tenant del lote** (no JOIN global por `app_id`): el chunk puede contener eventos de varios tenants (cola compartida). `_bulk_exceptions` recibe `session_tenants` (session_id→app_id del lote) y compara el dueño persistido de la métrica contra el tenant de la sesión de la excepción — cubre el caso cross-app aunque ambas sesiones estén en el mismo chunk.
4. **`/metrics/list` declara 422** aunque no tiene parámetros: OAS-13 exige 200/401/403/422; se declara por completitud del contrato.

## Issues Found

1. **Gotcha de tests**: `make_admin` usa el mismo email default por llamada → `UniqueViolationError idx_lab_user_email` al crear 2 admins en un test (read path). Helper con email único por llamada.
2. **Riesgo residual same-chunk** (ver ADR-0003, Negativas): dos tenants enviando el MISMO `session_id` NUEVO en el mismo chunk no se detecta en el SELECT pre-insert (ninguno existe aún). Fuera de la spec C5 (cubre sesión ya persistida); mitigación futura: índice único `(session_id, app_id)` o dedup intra-chunk. **WARNING**.

## Remaining Tasks

Ninguna — 13/13 completas. Siguiente fase: sdd-verify.