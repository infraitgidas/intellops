## Verification Report

**Change**: ISS-S2-04 — Pipeline CI/CD inicial (GitHub #38)
**Rama**: feat/ISS-S2-04 (base origin/develop `7a2b5ae`)
**Fecha**: 2026-10-02
**Entorno**: verificación local (Python 3.12, Postgres 16 local en `DATABASE_URL`); el CI corre Python 3.11 + `postgres:16-alpine`. Pendiente: confirmar la primera corrida en GitHub Actions al abrir el PR.

### Criterios de aceptación (#38)

| Criterio | Estado | Evidencia |
|----------|--------|-----------|
| Lint | ✅ | Job `Lint & Format`: flake8 0 warnings; pylint 9.90/10 con gate `--fail-under=9.0` |
| Unit tests | ✅ | Job `Unit Tests`: `pytest -m unit` sin Postgres → 102 passed en ~2 s |
| Reporte de cobertura | ✅ | Job `Unit & Integration Tests`: Job Summary + artefacto `coverage-report` (xml, html, junit); gate 70% |

### Ejecución

| Paso | Comando | Resultado |
|------|---------|-----------|
| Workflow | `actionlint -shellcheck=shellcheck .github/workflows/ci.yml` | OK, sin hallazgos |
| Lint | `flake8 src/ tests/` | OK |
| Lint | `pylint src/ --fail-under=9.0` | 9.90/10, exit 0 |
| Unit | `DATABASE_URL=<puerto cerrado> PYTHONPATH=. pytest -m unit` | 102 passed, 108 deselected, 1.83 s |
| Integración | `PYTHONPATH=. pytest -m integration` | 107 passed, 1 xpassed |
| Suite + cobertura | `PYTHONPATH=. pytest --cov --cov-report=term-missing --cov-report=xml --cov-report=html --junitxml=reports/junit.xml` | 209 passed, 1 xpassed; **87.83%** (≥ 70%); ~37 s |
| Contract | `PYTHONPATH=. pytest tests/test_contract.py -q` | 10 passed, 1 xpassed |
| Resumen | script del paso "Resumen de cobertura" con `GITHUB_STEP_SUMMARY` local | markdown con total + tabla por archivo |

### Checks negativos

- **Unit sin DB**: con `DATABASE_URL` apuntando a un puerto cerrado, 0 errores de conexión. Antes del cambio, los 209 tests fallaban en ese escenario por los fixtures `autouse` de DB.
- **Gate de cobertura**: con `fail_under = 99` en una config temporal, `pytest --cov` termina con `FAIL Required test coverage of 99.0% not reached` y exit 1. El umbral se lee de `pyproject.toml`, sin flag en la línea de comando.
- **`--strict-markers`**: un marker mal escrito (`@pytest.mark.unitt`) aborta la colección.

### No regresión

Mismos 210 tests que develop antes del cambio (209 passed + 1 xpassed) y misma cobertura (87.83%). La suma unit (102) + integration (107) + xpass (1) = 210 confirma que ningún test quedó fuera de las dos capas.

### Observaciones

- `test_schemathesis_live_contract_scoped` (xfail no estricto) ejercita la app real incluyendo `/health` → Postgres. Sin DB "fallaba" y el xfail lo ocultaba; se marcó `integration` para que no corra en el job sin base.
- `tests/test_migrations.py` define un autouse `_no_clean_db` cuyo docstring dice "override de clean_db", pero tiene otro nombre y no lo reemplaza (comportamiento previo, sin cambios en esta issue).
- Codecov removido; reincorporar en issue aparte (requiere `CODECOV_TOKEN`, admin del repo).
