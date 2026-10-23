# Proposal: ISS-S2-05 — Entorno reproducible de testing

**Cambio**: ISS-S2-05 (#39). **Base**: develop (`b9220ab`, con ISS-S2-04 mergeado). **Depende de**: ISS-S2-04 (#38).

## Intent

Criterio de #39: **la suite se ejecuta sin depender de la máquina del desarrollador**. Después de ISS-S2-04 el CI corre la suite, pero fuera del CI el resultado seguía dependiendo de la máquina:

- **Dependencias sin fijar**: `pyproject.toml` declara todo con `>=`; cada `pip install` (local, CI, servidor) resuelve versiones distintas según el día.
- **`make test` roto y peligroso**: corre en `intellops-core`, cuya imagen instala `src/api/requirements.txt` (sin `schemathesis` ni `numpy`) → `tests/test_contract.py` falla al importar. Además usa la DB del stack de dev y `clean_db` la trunca.
- **Entorno implícito**: un `.env` local (p. ej. otro `JWT_SECRET` o `DATABASE_URL`) cambia el resultado; `make test-contract`, documentado en CONTRIBUTING, no existía.

## Scope

### In Scope
- `requirements/dev.lock`: runtime + dev fijados con hashes para Python 3.11 / Linux x86_64 (`make lock`, uv).
- `Dockerfile.test`: Python 3.11 fijado a patch + dependencias del lock, solo wheels (sin apt/gcc: los mirrors de Debian están bloqueados en la red del laboratorio); el código se monta.
- `docker-compose.test.yml`: proyecto `intellops-test` con Postgres 16 efímero (tmpfs, sin puertos), variables fijadas y bind mount compatible con SELinux (`:z`).
- `scripts/ci-tests.sh`: mismos pasos y gates que el CI (lint → unit → migraciones → suite + cobertura).
- `Makefile`: `ci`, `test-contract`, `test-down`, `lock`; `test*` y `lint` pasan al entorno de testing.
- CI: los jobs instalan desde el lock; job nuevo `Reproducible Test Env (Docker)` (lock al día + `make ci`).

### Out of Scope
- Runner self-hosted en el servidor del laboratorio: el entorno ya corre ahí con `make ci` (solo Docker); registrar un runner es decisión de infraestructura aparte (riesgo de ejecutar PRs de forks en la red del laboratorio).
- Unificar `src/api/requirements.txt` (imagen de runtime) con el lock.
- Arquitecturas no x86_64 (ARM): el lock se resuelve para `x86_64-manylinux_2_28`.

## Approach

La imagen de testing contiene solo el intérprete y las dependencias; el repo se monta en `/app` porque los tests leen artefactos del repo (`docs/`/`openspec/` para el OpenAPI y el DDL, el `Dockerfile` de runtime). El contenedor corre con el UID/GID del host (`HOST_UID`/`HOST_GID`, exportados por el Makefile) para que los reportes no queden de root. Un mismo comando —`make ci`— es lo que corre un dev, el servidor del laboratorio y el job del CI.

## Affected Areas

| Área | Impacto | Descripción |
|------|--------|-------------|
| `requirements/dev.lock` | Nuevo | dependencias fijadas con hashes |
| `Dockerfile.test`, `docker-compose.test.yml` | Nuevo | entorno de testing aislado |
| `scripts/ci-tests.sh` | Nuevo | pipeline de QA en el contenedor |
| `Makefile` | Modificado | targets de test sobre el entorno de testing; `ci`, `lock`, `test-contract`, `test-down` |
| `.github/workflows/ci.yml` | Modificado | instalación desde el lock; job `reproducible-env` |
| `CONTRIBUTING.md`, `CHANGELOG.md` | Modificado | documentación |

Sin cambios en `src/`, `tests/`, contratos ni runtime.

## Risks

| Riesgo | Mitigación |
|--------|-----------|
| El lock queda desactualizado al tocar `pyproject.toml` | El job `reproducible-env` corre `make lock` y falla si hay diff |
| Upgrades de seguridad quedan congelados | `make lock UV_FLAGS=--upgrade` periódico (Dependabot/Renovate en issue aparte) |
| Branch protection referencia nombres de jobs | Se conservan todos; el nuevo job es adicional |

## Rollback

Revertir el PR: solo archivos de build/CI/docs.
