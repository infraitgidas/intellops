# Tasks: ISS-S3-06 — Pruebas unitarias de módulos críticos

## Review Workload Forecast

Changed lines (medido): ≈ 2100, de las cuales ≈ 1730 son tests (con docstrings que citan el requisito de cada caso) y el resto documentos del cambio y changelog. Código de producción: 0 líneas. Delivery strategy: single-pr. El volumen supera el presupuesto de 400 líneas, pero cada archivo de test es independiente y se revisa por separado (un commit por archivo).

Decision needed before apply: No (meta por módulo acordada con el owner).
Chained PRs recommended: No.
400-line budget risk: Medium (volumen de tests, sin riesgo funcional).

Dependencias: ISS-S2-04 (capas `unit`/`integration` en `conftest.py`) e ISS-S2-05 (entorno reproducible). B.9 depende de esta issue.

## Fase 0 — Documentos del cambio

- [x] 0.1 `proposal.md`, `spec.md` (QA-U1..QA-U5), `design.md` y este `tasks.md`.

## Fase 1 — Validaciones y normalización (100 %)

- [x] 1.1 `tests/test_ingest_policy.py` (nuevo): casos límite de tipo de `ingest_policy`.
- [x] 1.2 `tests/test_ingest_normalizer.py`: tipos que no son string, métricas que no son objeto, `metrics` que no es lista, unidad desconocida y valor no finito con alias.
- [x] 1.3 `tests/test_metrics_query.py`: delegación del catálogo, `limit` de probes, normalización a UTC en `QueryService`.

## Fase 2 — Lógica de negocio (≥ 90 %)

- [x] 2.1 `tests/conftest.py`: fixture `fake_session` (registra `commit`/`rollback`/`refresh`).
- [x] 2.2 `tests/test_application_service.py` (nuevo): CRUD, API keys y autenticación (QA-U2).
- [x] 2.3 `tests/test_user_service.py` (nuevo): alta, actualización, roles y hash de password (QA-U2).
- [x] 2.4 `tests/test_auth_service.py` (nuevo): login, anti-enumeración y usuario inactivo (QA-U3).
- [x] 2.5 `tests/test_ingest_telemetry.py`: gauge de profundidad de cola de `IngestService`.

## Fase 3 — Autorización (100 %)

- [x] 3.1 `tests/test_dependencies.py` (nuevo): `get_current_user`, `require_role`, `require_api_key`, `domain_error_handler` y `validation_error_handler` (QA-U4).

## Fase 4 — Transformaciones (≥ 90 %)

- [x] 4.1 `tests/test_ingest_transform.py` (nuevo): `_parse_ts`, `_build_rows` y contadores de `_persist_chunk`.
- [x] 4.2 `tests/test_metrics_query.py`: `_as_int`.
- [x] 4.3 `tests/test_ml_dataset_reader.py`: 4xx sin cuerpo ErrorResponse en `api_reader`.

## Fase 5 — Medición y documentación

- [x] 5.1 Cobertura unitaria antes/después por módulo en `verify-report.md`.
- [x] 5.2 `pytest -m unit` y `flake8 src/ tests/` en verde.
- [x] 5.3 `CHANGELOG.md`.
- [x] 5.4 Suite completa con cobertura en el entorno reproducible (`make test-cov`, Postgres efímero): 660 passed, 1 xfailed, 1 xpassed; cobertura total 95,45 %.

## Seguimiento (fuera de alcance)

- **Bug** (QA-U5): `ApplicationService.create_application` ignora `ApplicationCreate.is_active` (APP-7). Fijado con `xfail(strict=True)` en `test_create_application_honours_is_active_false`. Abrir una issue para corregirlo y quitar la marca.
- B.9: sumar los tests del agente JS (`cd src/agent && npm test`) al CI; hoy ningún job los corre.
- B.9: decidir si el gate de cobertura se aplica también por módulo crítico, con la tabla de `verify-report.md` como línea base.
- Robustez menor en `_build_rows`: el camino de métricas asume que `metadata` es un objeto (el de sesión lo verifica con `isinstance`). Hoy no es alcanzable porque Pydantic garantiza `dict | None`, pero conviene unificar el criterio si el worker empieza a recibir eventos por otra vía.
