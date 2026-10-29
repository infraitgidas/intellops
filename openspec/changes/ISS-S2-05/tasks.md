# Tasks: ISS-S2-05 — Entorno reproducible de testing

## Review Workload Forecast

Estimated changed lines: ~200 (sin contar el lock generado). Delivery strategy: single-pr.

## Fase 1 — Dependencias fijadas

- [x] 1.1 Generar `requirements/dev.lock` (runtime + dev, hashes, Python 3.11 / x86_64) con uv.
- [x] 1.2 Target `make lock` (mantiene pins; `UV_FLAGS=--upgrade` para actualizar).

## Fase 2 — Entorno de testing

- [x] 2.1 `Dockerfile.test` (python:3.11.14-slim-bookworm + lock, solo wheels: sin apt/gcc).
- [x] 2.2 `docker-compose.test.yml`: proyecto `intellops-test`, Postgres efímero en tmpfs, variables fijadas, UID del host.
- [x] 2.3 `scripts/ci-tests.sh`: lint → unit → migraciones → suite + cobertura.
- [x] 2.4 `Makefile`: `ci`, `test-contract`, `test-down`; `test*`/`lint` sobre el entorno de testing.

## Fase 3 — CI

- [x] 3.1 Jobs instalan desde el lock (`--require-hashes`) + `pip install --no-deps -e .`.
- [x] 3.2 Job `Reproducible Test Env (Docker)`: lock al día + `make ci`.

## Fase 4 — Verificación y documentación

- [x] 4.1 `CONTRIBUTING.md` (sección "Entorno reproducible de testing") y `CHANGELOG.md`.
- [x] 4.2 `make ci` en verde en una máquina distinta a la del dev (VM `intellops` del laboratorio).
- [x] 4.3 Primera corrida del job `Reproducible Test Env (Docker)` en GitHub Actions (al abrir el PR): en verde el 2026-10-25.
- [x] 4.5 Ajustes de review: uv fijado en `make lock`, `.dockerignore`, UID en el uso directo documentado, ARM y versiones mayores aclarados.
- [x] 4.4 `verify-report.md` con evidencia.
