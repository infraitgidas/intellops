# Tasks: ISS-S2-03 — Ingesta RUM asíncrona

## Review Workload Forecast

Estimated changed lines: 1400–1900. Delivery strategy: single-pr.

Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: size-exception
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| 1 | Política, entidades, contadores | PR 1 | `pytest tests/test_ingest_telemetry.py -q -k policy` | N/A (política pura) | Revertir policy/entidades/config |
| 2 | Servicio, cola, repos | PR 2 | `pytest tests/test_ingest_telemetry.py -q` | httpx ASGI + Postgres | Revertir ingest/ y repos |
| 3 | Router, guard, lifespan | PR 3 | `pytest tests/test_ingest_telemetry.py tests/test_ingest_auth.py -q` | httpx ASGI + Postgres | Revertir router/errors/main |
| 4 | Contrato + docs | PR 4 | `pytest tests/test_contract.py -q` | `schemathesis run` (CI) | Revertir openapi + docs |

## Fase 1 — Fundación e infraestructura

- [x] 1.1 RED `tests/test_ingest_telemetry.py` + crear `src/api/domain/services/ingest_policy.py`: 7 códigos RUM-4 (sin `unknown_application`), límites 500/50, ratings no rechazan, `application_id` opcional.
- [x] 1.2 Crear entidades `src/api/domain/entities/{user_session,rum_metric,js_exception}.py` (mirror DDL 0001).
- [x] 1.3 Agregar `ingest_queue_maxsize=10000`, `ingest_workers=2`, `ingest_shutdown_timeout=10.0` (+ env `INGEST_*`) a `src/api/config.py`; `ServiceUnavailableError` (503) en `src/api/domain/exceptions.py`.
- [x] 1.4 RED + crear `src/api/infrastructure/ingest/counters.py`: received/accepted/rejected{reason}/queue_depth/persisted/dead_letter/metric_id_unknown (`ingest.` prefix) (RUM-8).

## Fase 2 — Núcleo: servicio, cola y persistencia

- [x] 2.1 RED `tests/test_ingest_telemetry.py`: 400 envelope (schema_version ≠ 1.0, 501 eventos) y 202 parcial (rejected[{index,reason}], batch_id, accepted+rejected=total) + crear `src/api/presentation/schemas/ingest.py` (application_id opcional, OAS-12) + `src/api/domain/services/ingest_service.py` (process_batch: uuid4, 2 niveles, enqueue, 202) (RUM-2/3).
- [x] 2.2 RED 503 `queue_full` (maxsize 1) + crear `src/api/infrastructure/ingest/queue.py` (Protocol enqueue/close/join + `AsyncioIngestQueue` put_nowait→503) (RUM-5).
- [x] 2.3 RED persistencia: `user_session` ON CONFLICT con app_id autenticado, bulk `rum_metric`/`js_exception`, retry ≤3, dead-letter (RUM-6).
- [x] 2.4 Crear `src/api/domain/repositories/ingest_repository.py` (Protocol upsert/bulk; sin commit, ADR-10) + `src/api/infrastructure/db/repositories/sqlalchemy_ingest_repository.py` (insert Core, catálogo cacheado, chunks 500, retry 3 backoff 0.5/1/2 transitorios, dead-letter `ingest.dead_letter_total`).

## Fase 3 — Integración y wiring

- [x] 3.1 RED `tests/test_ingest_telemetry.py`: 401 + WWW-Authenticate, 403 `app_inactive`, tenant de key ≠ payload (RUM-1, IAUTH-2) + crear `src/api/presentation/routers/telemetry.py` (`POST /telemetry/{metrics,exceptions}` con `Depends(require_api_key)`) (IAUTH-5).
- [x] 3.2 Handler `RequestValidationError` scoped `/telemetry/*`→400 en `src/api/presentation/errors.py` + registro en `src/api/main.py` (D5).
- [x] 3.3 Lifespan `src/api/main.py`: workers al startup; shutdown `close→join(timeout)→log→dispose`; RED drenado/timeout (RUM-7).
- [x] 3.4 Invertir `tests/test_ingest_auth.py::test_prod_app_has_no_api_key_wiring`: aseverar `/telemetry/*` cubiertos (IAUTH-5).

## Fase 4 — Testing y contrato

- [x] 4.1 Actualizar `openspec/specs/openapi.yaml`: `/telemetry/*` con `security:[apiKey]`, requestBody, 202/400/401/403/503/429 (429 sin impl, D3); quitar `/metrics/ingest`+`/logs/ingest`; scheme descripción; `application_id` fuera de required; sin `unknown_application` (OAS-6/11/12).
- [x] 4.2 Actualizar `tests/test_contract.py`: `_SCOPED_PATH_RE`+telemetry, expected_statuses+503; OAS-6 invertido; OAS-10 sin paths viejos; asserts OAS-9/11/12 + completar `tests/test_ingest_telemetry.py`: RUM-8 log redactado + contadores, aislamiento IAUTH-2.
- [x] 4.3 Suite `pytest --cov=src` ≥70%, flake8 (99), pylint ≥7.0; validar `openspec/specs/openapi.yaml` (read-only).

## Fase 5 — Documentación

- [x] 5.1 Actualizar `openspec/specs/architecture/{interfaces,components,quality-attributes}.md` (nomenclatura `/telemetry/*`, árbol routers/telemetry.py, artefacto `POST /telemetry/metrics`; ARCH-1..3) y docs vivas `docs/architecture/{PipelineIngestaRUM,ContratoIngestaRUM}.md` + `docs/brief-v2.md` (rutas y semántica 202/503; históricos intactos; ARCH-4).
- [x] 5.2 Verificar/ajustar `docs/adr/0002-pipeline-ingesta-async.md` contra DD-7 (Nygard; ya creado) y actualizar `CHANGELOG.md`.