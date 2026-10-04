# Tasks: ISS-S2-04 — Pipeline CI/CD inicial

## Review Workload Forecast

Estimated changed lines: ~250 (mayoría YAML/docs). Delivery strategy: single-pr.

## Fase 1 — Capas de test (unit / integration)

- [x] 1.1 Registrar markers `unit` e `integration` en `pyproject.toml` y activar `--strict-markers`.
- [x] 1.2 `tests/conftest.py`: `pytest_collection_modifyitems` clasifica por fixtures de DB (`db_session`, `test_engine`, `alembic_cfg`, `conn`).
- [x] 1.3 `tests/conftest.py`: `_migrated_database` solo migra si hay tests `integration` seleccionados; `clean_db` trunca solo en `integration` (vía `_truncate_data_tables`).
- [x] 1.4 Marcar `integration` explícito en tests que tocan DB sin fixtures: `tests/test_health.py`, `test_schemathesis_live_contract_scoped`.
- [x] 1.5 Verificar `pytest -m unit` con `DATABASE_URL` inalcanzable (0 errores de conexión).

## Fase 2 — Pipeline (`.github/workflows/ci.yml`)

- [x] 2.1 `lint`: flake8 + pylint `--fail-under=9.0`.
- [x] 2.2 Job `unit` (sin Postgres) entre `lint` y `test`.
- [x] 2.3 `test`: cobertura xml/html/term + JUnit; Job Summary con total y tabla; artefacto `coverage-report` (14 días).
- [x] 2.4 Quitar Codecov (sin token) — reincorporar en issue aparte.
- [x] 2.5 Cache pip, `concurrency`, `timeout-minutes`, `workflow_dispatch`, `permissions`.
- [x] 2.6 Validar workflow con actionlint + shellcheck.

## Fase 3 — Config y DX local

- [x] 3.1 `[tool.coverage]`: `source = ["src"]`, `fail_under = 70` (gate único), `show_missing`, `skip_empty`, salidas xml/html.
- [x] 3.2 `Makefile`: `test-unit`, `test-integration`, `test-cov` con HTML, pylint 9.0, `clean` borra `reports/`.
- [x] 3.3 `.gitignore`: `reports/`.

## Fase 4 — Documentación

- [x] 4.1 `CONTRIBUTING.md`: sección "Pipeline de CI" y comandos por capa.
- [x] 4.2 `CHANGELOG.md`: entrada ISS-S2-04 (#38).
- [x] 4.3 `verify-report.md` con evidencia local.
