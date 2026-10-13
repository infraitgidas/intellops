# Tasks: ISS-S3-02 — Normalización y calidad de datos de ingesta

## Review Workload Forecast

Estimated changed lines: 620–900 (código, tests, docs, ADRs).

Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: pending
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| 1 | Normalizador puro + tests | PR 1 | `pytest tests/test_ingest_normalizer.py -m unit -q` | N/A — puro | Revertir `ingest_normalizer.py` + `ingest_policy.py` |
| 2 | Wiring servicio + validación | PR 2 | `pytest tests/test_ingest_telemetry.py -m unit -q` | N/A — dominio puro | Revertir `ingest_service.py` + `ingest_policy.py` |
| 3 | Limpieza worker + OpenAPI | PR 3 | `pytest tests/test_ingest_telemetry.py -m integration -q` | httpx ASGI + Postgres | Revertir `queue.py` + `openapi.yaml` |
| 4 | Docs/ADR/CHANGELOG + suite | PR 4 | `pytest --cov=src -q` | schemathesis CI | Revertir docs + `CHANGELOG.md` |

## Fase 1 — Núcleo del normalizador (puro)

- [x] 1.1 RED `tests/test_ingest_normalizer.py` (`-m unit`): alias→canónica, idempotencia, `error_type`→`Other`, coerción `"120.5"`, `Infinity`/conteo 1.5 rechazados, 9000ms sin recorte (NORM-1..7).
- [x] 1.2 RED unit: contrato `_canonical_ts` — ISO-8601 UTC tz-aware; ausente/no parseable→`None`; el normalizador NUNCA inventa timestamp; validación rechaza `None` (NORM-2/5).
- [x] 1.3 `ingest_policy.py`: registros compartidos `UNIT_CONVERSIONS`, `METRIC_TYPE_ALIASES`, `ERROR_TYPE_ALIASES`, `ERROR_TYPE_CATALOG`, `COUNT_TYPES` (fuente única, R7) (NORM-3, NORM-4).
- [x] 1.4 Crear `src/api/domain/services/ingest_normalizer.py`: `normalize_rum_event`, `normalize_js_exception`, `_canonical_ts`; puro, sin E/S, nunca lanza (NORM-1..7).
- [x] 1.5 REFACTOR + `pytest -m unit` verde; idempotencia `normalize(normalize(e)) == normalize(e)` (NORM-3/4).

## Fase 2 — Wiring y validación

- [x] 2.1 RED unit: el servicio normaliza ANTES de validar; alias aceptado, desconocido rechazado (policy) (NORM-1, ARCH-5).
- [x] 2.2 `ingest_policy.py` `_in_range`/`_validate_metric`: rechazar conteos no enteros (`invalid_range`) y no finitos (NORM-6, f).
- [x] 2.3 `src/api/domain/services/ingest_service.py` `:59-83`: insertar normalizador antes del validador; encolar payload canónico (NORM-1, ARCH-5).
- [x] 2.4 RED unit NORM-5: requerido ausente→`missing_required_field`; opcionales solo defaults/herencia del contrato (`timestamp`←envelope; nulables) (NORM-5).
- [x] 2.5 Verificar NORM-7: en memoria, CPU-only, sin dep/proceso nuevo, `<2GB RAM`; ML precisión/recall/F1 N/A (NORM-7).

## Fase 3 — Limpieza del worker

- [x] 3.1 RED: el worker persiste el ts canónico; sin `now()` (NORM-2, ARCH-5).
- [x] 3.2 `src/api/infrastructure/ingest/queue.py` `:235-301`: quitar `float()`, `now()` y ts-precedence duplicada; consumir solo el ts canónico (NORM-2/6).

## Fase 4 — Contrato / OpenAPI

- [ ] 4.1 RED contrato: enum `unit` ampliado aceptado; desconocida rechazada (ARCH-6, NORM-3).
- [ ] 4.2 `openspec/specs/openapi.yaml` `:953-956`: ampliar enum `RumMetric.unit` a `[ms, count, s, sec, secs, msec, millis, counts]` + nota `error_type` (ARCH-6).

## Fase 5 — Integración `/telemetry/*`

- [ ] 5.1 RED integración `tests/test_ingest_telemetry.py` (`-m integration`): alias aceptado → canónico persistido; naive rechazado; worker sin `now()` (NORM-1/2/3, ARCH-5).

## Fase 6 — Docs / ADR

- [ ] 6.1 Finalizar `docs/adr/0004-normalize-before-validate.md`, `docs/adr/0005-representation-only-normalization.md`, `docs/adr/0006-error-type-in-code-catalog.md`, `docs/adr/0007-unit-alias-conversion.md` (Propuesto→Aceptado) + `docs/adr/README.md` (ARCH-5/6).
- [ ] 6.2 Actualizar `docs/architecture/ContratoIngestaRUM.md`, `docs/architecture/PipelineIngestaRUM.md` y `CHANGELOG.md` (ARCH-5/6).

## Fase 7 — Verificación

- [ ] 7.1 `pytest --cov=src` ≥70%, flake8/pylint, schemathesis verdes (NORM-1..7, ARCH-5/6).

## Dependencias

1.1/1.2→1.4 (RED→GREEN); 1.3→1.4; 1.4→2.1/2.3; 2.2→2.3; 2.3→3.1/3.2; 2.3→4/5; 4.2→5.1; Fase 6 independiente; 7 al final.
