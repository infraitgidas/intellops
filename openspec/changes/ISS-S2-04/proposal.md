# Proposal: ISS-S2-04 — Pipeline CI/CD inicial

**Cambio**: ISS-S2-04 (#38). **Base**: develop (`7a2b5ae`, con ISS-S2-01..03 y S3-05 mergeados).

## Intent

Incorporar la pipeline de QA con los tres criterios de #38: **lint**, **unit tests** y **reporte de cobertura**. El CI de develop ya corría flake8/pylint y la suite completa contra Postgres, pero:

- No existían unit tests como capa: los fixtures `autouse` de `tests/conftest.py` (`_migrated_database`, `clean_db`) obligaban a que **todo** test tuviera Postgres, incluso los puros (hash de API keys, schemas Pydantic, política de ingesta).
- El reporte de cobertura solo se enviaba a Codecov, sin `CODECOV_TOKEN` configurado y con `fail_ci_if_error: false`: fallaba en silencio y no quedaba ningún reporte visible.
- El gate de pylint (`--fail-under=7.0`) estaba ~3 puntos por debajo del score real (9.90), sin efecto práctico.
- Config de cobertura inconsistente: `pyproject.toml` declaraba `source = ["api"]` mientras el CI usaba `--cov=src`, y el umbral estaba duplicado (`fail_under` + `--cov-fail-under`).

## Scope

### In Scope
- Capas de test `unit` / `integration` con markers de pytest, asignadas automáticamente según los fixtures de DB que usa cada test.
- Fixtures de DB condicionales: los tests `unit` no migran ni truncan la base.
- Job `Unit Tests` sin Postgres (feedback rápido) entre `lint` y la suite completa.
- Reporte de cobertura publicado dentro de GitHub: Job Summary (total + tabla por archivo) y artefacto `coverage-report` (`coverage.xml`, `htmlcov/`, `reports/junit.xml`).
- Gate único de cobertura (70%) en `[tool.coverage.report]` de `pyproject.toml`.
- Pylint `--fail-under=9.0`.
- Higiene del workflow: cache de pip, `concurrency` con cancelación, `timeout-minutes`, `workflow_dispatch`, `permissions: contents: read`.
- Targets `make test-unit` / `make test-integration`; `make test-cov` genera HTML.

### Out of Scope
- **Codecov**: se quita el paso porque no funcionaba sin token. Se reincorpora en una issue aparte cuando un admin del repo cargue `CODECOV_TOKEN`; `coverage.xml` ya se genera en el job `test`, así que es solo agregar el paso de la action (+ badge opcional).
- Jobs `contract`, `license-scan` y `docker`: sin cambios.
- Evolución posterior (nota de #38): integration-test como job separado, build/publish de imagen, staging, E2E, quality gates OTel (T2.2).
- Gate de lint "0 warnings de pylint" (plan de trabajo T1.2).

## Capabilities

### Modified Capabilities
- `ci-pipeline`: `lint → unit → test (cobertura + reporte)`; `contract`/`license-scan` en paralelo tras `lint`; `docker` al final.
- `test-suite`: capas `unit`/`integration` seleccionables con `-m`.

## Approach

`pytest_collection_modifyitems` en `tests/conftest.py` marca `integration` a todo test cuyo cierre de fixtures incluya `db_session`, `test_engine`, `alembic_cfg` o `conn`; el resto queda `unit`. Los tests que tocan la DB sin fixtures (vía engine global) se marcan explícitamente: `tests/test_health.py` (módulo) y `test_schemathesis_live_contract_scoped`. `clean_db` deja de depender de `db_session` en su firma y resuelve el TRUNCATE con `request.getfixturevalue` solo para tests `integration`; `_migrated_database` corre alembic solo si la selección incluye integración. `--strict-markers` evita markers mal escritos.

Un test nuevo sin fixtures de DB es `unit` automáticamente; si en realidad toca Postgres, falla en el job `Unit Tests` (que no tiene DB) y se corrige agregando `@pytest.mark.integration`.

## Affected Areas

| Área | Impacto | Descripción |
|------|--------|-------------|
| `.github/workflows/ci.yml` | Modificado | job `unit` nuevo; `lint`/`test` reforzados; reporte de cobertura; sin Codecov |
| `tests/conftest.py` | Modificado | clasificación unit/integration; fixtures de DB condicionales |
| `tests/test_health.py`, `tests/test_contract.py` | Modificado | marker `integration` explícito |
| `pyproject.toml` | Modificado | markers, `--strict-markers`, config de coverage unificada |
| `Makefile` | Modificado | `test-unit`, `test-integration`, `test-cov` con HTML, pylint 9.0 |
| `.gitignore` | Modificado | `reports/` |
| `CONTRIBUTING.md`, `CHANGELOG.md` | Modificado | documentación del pipeline |

Módulos: QA (owner). Sin impacto en código de producción (`src/`), contratos OpenAPI/AsyncAPI ni footprint de recursos en runtime.

## Risks

| Riesgo | Mitigación |
|--------|-----------|
| Branch protection referencia nombres de jobs | Se conservan `Lint & Format` y `Unit & Integration Tests`; el nuevo job es `Unit Tests` |
| Un test que toca DB queda clasificado `unit` | El job `Unit Tests` corre sin Postgres → falla visible; se marca `integration` |
| Pylint baja de 9.0 por código nuevo | Margen actual de 0.9; el umbral es configurable en `ci.yml` y `Makefile` |

## Rollback

Revertir el PR: los archivos tocados son solo de CI, tests y configuración; no hay migraciones ni cambios de runtime.

## Vínculo de investigación

H-QA (openspec/specs/research/hypotheses.md), EXP-301 "Pipeline CI/CD baseline": deja medibles cobertura (≥ 70%) y tiempo de pipeline por commit (target ≤ 10 min).
