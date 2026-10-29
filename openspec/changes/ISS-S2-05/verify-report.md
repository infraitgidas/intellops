## Verification Report

**Change**: ISS-S2-05 — Entorno reproducible de testing (GitHub #39)
**Rama**: feat/ISS-S2-05 (base develop `b9220ab`)
**Fecha**: 2026-10-23
**Entorno**: VM del laboratorio GIDAS `intellops` (192.168.1.130, acceso por Twingate): x86_64, familia RHEL, SELinux `Enforcing`, Docker 29.4.1, Compose v5.1.3, GNU Make 4.4.1. Código copiado con `rsync` desde la máquina del dev (sin `.git`), sin Python ni dependencias instaladas en el host. GitHub Actions: el job `Reproducible Test Env (Docker)` y el resto del workflow (7/7) en verde en el PR el 2026-10-25.

### Criterio de aceptación (#39)

| Criterio | Estado | Evidencia |
|----------|--------|-----------|
| La suite se ejecuta sin depender de la máquina del desarrollador | ✅ | `make ci` en la VM del laboratorio (solo Docker + make): lint, unit, migraciones y suite completa en verde |

### Ejecución (VM del laboratorio)

| Paso | Comando | Resultado |
|------|---------|-----------|
| Pipeline completo | `make ci` (→ `docker compose -f docker-compose.test.yml run --rm --build tests` → `scripts/ci-tests.sh`) | exit 0 |
| Lint | `flake8 src/ tests/` + `pylint src/ --fail-under=9.0` | OK (el script corre con `set -e`; llegó a la suite) |
| Unit | `pytest -m unit` | OK |
| Migraciones | `alembic upgrade head` contra `test-db` efímero | OK |
| Suite + cobertura | `pytest --cov ... --junitxml=reports/junit.xml` | **414 passed, 1 xpassed**, 53 warnings, 42.88 s; cobertura **90.11%** (gate 70%) |

El xpass es `test_schemathesis_live_contract_scoped` (xfail no estricto documentado, OAS-9/ADR-24), igual que en ISS-S2-04.

### Hallazgos durante la verificación

Problemas que la verificación fuera de la máquina del dev sacó a la luz:

- **Mirrors de Debian bloqueados en la red del laboratorio**: `apt-get update` en el build devolvía `403 Forbidden` desde `deb.debian.org`. Se quitó el paso de `apt`/`gcc` de `Dockerfile.test` y se instala con `pip --only-binary=:all:`; se verificó que las 75 dependencias del lock tienen wheel cp311/abi3 manylinux x86_64.
- **SELinux `Enforcing`**: el bind mount del repo lleva `:z` en `docker-compose.test.yml` para que el contenedor pueda leerlo (ignorado en hosts sin SELinux, como el runner de GitHub).
- **Docker de la VM (fuera del alcance del repo)**:
  - `docker.socket` fallaba al boot (`Failed to resolve group 902401123`, status 216/GROUP). El override `/etc/systemd/system/docker.socket.d/override.conf` usa un grupo de FreeIPA que todavía no resuelve cuando arranca el socket. Se levantó a mano (`systemctl start`); sugerencia para infraestructura: `After=/Wants=sssd.service` en el override y `systemctl enable docker.socket`.
  - El usuario `infra` no tiene acceso al socket aunque figura en el grupo `docker`, así que se corrió con `sudo make ci`. Queda a revisar con infraestructura junto con el punto anterior.
- **Restos de una corrida fallida**: si el build falla, `test-db` queda levantado (`docker compose run` arranca primero las dependencias). `make test-down` lo limpia; en CI corre con `if: always()`.

### No regresión

- Sin cambios en `src/` ni `tests/`.
- Los jobs existentes del CI conservan sus nombres; solo cambia la instalación (lock con hashes + `pip install --no-deps -e .`).
- Respecto de ISS-S2-04 (209 passed + 1 xpassed, 87.83%), la suite creció por las issues mergeadas después (S3-02, S3-04).

### Observaciones

- `make test`, `make test-unit`, `make test-integration`, `make test-cov` y `make lint` ya no corren en `intellops-core`: antes fallaban al colectar `tests/test_contract.py` (sin `schemathesis` en `src/api/requirements.txt`) y truncaban la DB de desarrollo.
- El lock fija versiones nuevas respecto de develop (fastapi 0.160, SQLAlchemy 2.1.6, pytest 9.1.1, schemathesis 4.32.3): son las que `pip install -e ".[dev]"` resolvía al momento; la suite pasa con ellas.
- Runner self-hosted en la VM: fuera de alcance (ver proposal).
- ARM: `pip download --only-binary=:all: --require-hashes -r requirements/dev.lock` para `manylinux*_aarch64` / cp311 baja las 75 dependencias (el lock trae hashes de todas las plataformas). No se corrió la suite en un host ARM.
