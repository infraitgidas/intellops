# Tasks: ISS-S3-01 — Persistencia de telemetría (verificación + hardening + read path)

## Review Workload Forecast

Estimated changed lines: 900–1300. Delivery strategy: single-pr.

Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: size-exception
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| 1 | Hardening ownership (repo + contadores) | PR 1 | `pytest tests/test_ingest_telemetry.py -q` (read-only) | httpx ASGI + Postgres | Revertir `/home/federico/Projects/intellops/ingest/` + repos de ingesta |
| 2 | Query repo + service | PR 2 | `pytest tests/test_metrics_query.py -q` (read-only) | httpx ASGI + Postgres | Revertir `/home/federico/Projects/intellops/src/api/domain/repositories/query_repository.py`, `/home/federico/Projects/intellops/src/api/domain/services/query_service.py` |
| 3 | Router + openapi | PR 3 | `pytest tests/test_metrics_query.py tests/test_contract.py -q` (read-only) | httpx ASGI + Postgres + schemathesis | Revertir `/home/federico/Projects/intellops/routers/metrics.py`, `/home/federico/Projects/intellops/src/api/main.py`, openapi |
| 4 | Contrato + docs + suite | PR 4 | `pytest --cov=src -q` (read-only) + flake8/pylint | schemathesis run (CI) | Revertir docs + `/home/federico/Projects/intellops/tests/test_contract.py` |

## Fase 1 — Fundación e infraestructura

- [x] 1.1 RED + ampliar `/home/federico/Projects/intellops/src/api/domain/repositories/ingest_repository.py`: `PersistStats` (read-only) + `session_foreign` (read-only)/`metric_id_foreign` (read-only) (defaults) + crear `QueryRangeError` (read-only) (422 `invalid_query_range` (read-only)) en `/home/federico/Projects/intellops/src/api/domain/exceptions.py` (DD-8/10).
- [x] 1.2 Crear `/home/federico/Projects/intellops/src/api/domain/repositories/query_repository.py`: puerto `QueryRepository` (read-only) (Protocol) + DTOs `MetricAggregate` (read-only) (5 campos C6) y `MetricTypeInfo` (read-only) (TQ-1).
- [x] 1.3 RED `/home/federico/Projects/intellops/tests/test_ingest_telemetry.py`: collision/replay C5 + reenvío mismo tenant — asserts en BD (filas no persistidas, `user_session.app_id` (read-only) intacto, `session_foreign_total` (read-only)) (RUM-9/11).
- [x] 1.4 RED `/home/federico/Projects/intellops/tests/test_ingest_telemetry.py`: correlación scoped — cross-app→`NULL` (read-only)+contador, legítima conserva `metric_id` (read-only), inexistente→`metric_id_unknown_total` (read-only) (RUM-10).
- [x] 1.5 RED crear `/home/federico/Projects/intellops/tests/test_metrics_query.py`: shape ML exacto, 1 fila por bucket, app-scoped, límites→422, 401 sin key, aislamiento por key, `/metrics/list` (read-only) (TQ-1/2, OAS-14).

## Fase 2 — Núcleo: ownership y read path

- [x] 2.1 Modificar `/home/federico/Projects/intellops/src/api/infrastructure/db/repositories/sqlalchemy_ingest_repository.py`: `_upsert_sessions` (read-only) → `set[UUID]` (read-only) de sesiones extranjeras (SELECT por PK pre-insert, DD-8); `persist_chunk` (read-only) filtra metrics/exceptions de extranjeras y cuenta descartes; `_bulk_exceptions` (read-only) correlación con JOIN scoped por app_id (RUM-9/10).
- [x] 2.2 Modificar `/home/federico/Projects/intellops/src/api/infrastructure/ingest/counters.py` (`session_foreign` (read-only)/`metric_id_foreign` (read-only) + keys `ingest.session_foreign_total` (read-only), `ingest.metric_id_foreign_total` (read-only)) y `/home/federico/Projects/intellops/src/api/infrastructure/ingest/queue.py` (worker incrementa desde `PersistStats` (read-only)) (DD-10/RUM-11).
- [x] 2.3 Crear `/home/federico/Projects/intellops/src/api/infrastructure/db/repositories/sqlalchemy_query_repository.py`: `query_metrics` (read-only) SQL agregado (epoch-bucket anclado a `:start` (read-only), `AVG` (read-only) + `COUNT(DISTINCT session_id)` (read-only), JOIN app-scoped, sin materializar) + `list_metric_types` (read-only) (DD-9/TQ-1).
- [x] 2.4 Crear `/home/federico/Projects/intellops/src/api/domain/services/query_service.py`: límites TQ-2 (default 15 min, ≤ 7 d, bucket ≥ 60 s, start < end → 422 sin tocar el repo).

## Fase 3 — Integración y wiring

- [x] 3.1 Crear `/home/federico/Projects/intellops/src/api/presentation/schemas/metrics.py` (`MetricAggregateOut` (read-only), `MetricTypeInfoOut` (read-only)) + `/home/federico/Projects/intellops/src/api/presentation/routers/metrics.py` (`GET /metrics/query` (read-only) operation_id `queryMetrics` (read-only), `GET /metrics/list` (read-only) `listMetrics` (read-only), ambos `Depends(require_api_key)` (read-only) + `Depends(get_session)` (read-only)) y registrar en `/home/federico/Projects/intellops/src/api/main.py` (OAS-13/14).
- [x] 3.2 Actualizar `/home/federico/Projects/intellops/openspec/specs/openapi.yaml` 124-137: `security:[apiKey]` (read-only), parámetros (`start` (read-only), `end` (read-only), `bucket_seconds` (read-only), `metric_type` (read-only) opcional), respuestas 200 (shape ML / catálogo) + 401/403/422; operationIds y paths intactos (OAS-13).

## Fase 4 — Testing y contrato

- [x] 4.1 Actualizar `/home/federico/Projects/intellops/tests/test_contract.py`: OAS-13 estructural (operationIds, security, parámetros, statuses) + `_SCOPED_PATH_RE` (read-only) += `metrics` (read-only); Schemathesis scoped verde.
- [x] 4.2 Suite `pytest --cov=src` (read-only) ≥ 70% + flake8/pylint; validar `/home/federico/Projects/intellops/openspec/specs/openapi.yaml` (read-only).

## Fase 5 — Documentación

- [x] 5.1 Crear `/home/federico/Projects/intellops/docs/adr/0003-ownership-tenant-read-path.md` (Nygard, DD-8/9/10) + actualizar `/home/federico/Projects/intellops/CHANGELOG.md`.

## Dependencias

1.1→2.1/2.2 (PersistStats antes del repo/contadores); 1.2→2.3→2.4→3.1 (puerto → impl → service → router); 1.3/1.4→2.1/2.2 (RED antes de GREEN); 1.5→2.3/2.4; 3.1/3.2→4.1→4.2; 5.1 al final (independiente).