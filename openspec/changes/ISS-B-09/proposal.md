# Proposal: ISS-B-09 — Quality gates bloqueantes en CI

**Cambio**: B.9 (#71). **Base**: `MVP1` (origin/develop 057d46b + #92 B.3 + #91 ISS-S3-06).
**Depende de**: ISS-S3-06 (entorno reproducible de testing, `docker-compose.test.yml`).
**Lo consumen**: B.5 (SPA), C.1 (E2E), C.3 (carga) y C.5 (release): todo lo que se mergee después
pasa por estos gates.

## Intent

La issue pide cuatro criterios: cobertura < 70 % bloquea, lint con warnings/errores bloquea,
OpenAPI/contrato inválido bloquea y gates documentados y verificados con un PR de prueba.

Antes de este cambio el CI tenía los tres jobs, pero el estado real de los gates era desparejo.
Medido sobre `ac10991` con las versiones fijadas en `requirements/dev.lock` (pylint 4.1.3 /
astroid 4.3.4), no supuesto:

- **Cobertura (S11)**: `fail_under = 70` en `[tool.coverage.report]` ya hace fallar la corrida
  por debajo del umbral cuando se pasa `--cov` (`pytest` sale 1 con "Required test coverage of
  70.0% not reached"). Pero el job no lo declaraba: el umbral era invisible en el log y se podía
  bajar cambiando un archivo de configuración sin tocar el workflow.
- **Lint (S12)**: `flake8` ya bloqueaba (sale ≠ 0 ante cualquier hallazgo). `pylint` **no**:
  con `--fail-under=9.0` el árbol de la base pasa con exit 0 **aun teniendo un warning
  (`W0613` en `metrics.py:97`)**, porque un warning deja el score en 9.91. Un gate que tolera
  warnings no cumple S12.
- **Contrato (S13)**: el job `contract` ya corría `tests/test_contract.py`, ya era `needs` de
  `docker` y el test ya falla con un spec roto; faltaba fijarlo y documentarlo, no implementarlo.
- **Documentación y verificación (S14)**: `CONTRIBUTING.md` listaba los jobs y qué los rompe,
  pero no el disparador exacto de cada gate ni cómo reproducir el fallo localmente. Y el "PR de
  prueba" no aplica en este tramo: MVP1 es local y no se pushea (S33 del plan), así que no hay
  PR donde romper un gate a propósito.

## Scope

### In Scope (RFC 2119)

- MUST: el job de la suite pasa `--cov-fail-under=70` explícito, con el mismo valor que
  `fail_under`, y ningún job ni step declara `continue-on-error`.
- MUST: `pylint` corre con `--fail-under=9.0 --fail-on=W,E` y **sin** `--disable`; con las
  versiones del lock el árbol pasa con 0 warnings y 0 errores.
- MUST: el árbol cumple ese gate sin mensajes desactivados en `pyproject.toml`: las
  correcciones son de código (`_application` por el `Depends` no consumido; imports `src.ml.*`
  → `ml.*`).
- MUST: el job `contract` corre `tests/test_contract.py` y `docker` lo requiere en `needs`.
- MUST: `make lint` corre el mismo comando bloqueante que el CI, para que el fallo no aparezca
  recién en el PR.
- MUST: `CONTRIBUTING.md` documenta, por gate, el disparador y el comando para reproducir el
  fallo localmente, más la calibración de pylint.
- MUST: `tests/test_ci_gates.py` lee el workflow, el `pyproject.toml`, el `Makefile` y
  `CONTRIBUTING.md` y falla si alguien afloja un gate (baja un umbral, agrega
  `continue-on-error`, saca `contract` de `needs`, agrega `--disable` o desactiva categorías).

### Out of Scope

- Gates nuevos que la issue no pide (cobertura por archivo, complejidad, mutación, SAST).
- Cambiar los umbrales: 70 % de cobertura y 9.0 de score se mantienen.
- El `PR de prueba` como tal: se reemplaza por el pin test + evidencia negativa local mientras
  MVP1 no se pushee (S33). Cuando haya PRs reales, ese PR se puede hacer igual; no reemplaza el
  pin, lo complementa.

## Capabilities

- **Nuevas**: `ci-gates` (cobertura, lint y contrato bloqueantes + pin y documentación).
- **Modificadas**: ninguna de producto. `lint` y `coverage-gate` del pipeline cambian de
  comportamiento (ahora bloquean de verdad).

## Approach

Cuatro piezas acotadas:

1. **Workflow** (`.github/workflows/ci.yml`): `--cov-fail-under=70` en el step de la suite;
   `--fail-on=W,E` en pylint, sin `--disable`; nombres y comentarios de los steps de contrato.
2. **Árbol**: sacar el único warning real (`_application`) y unificar los imports `src.ml.*` a
   `ml.*`, que además arregla un error de identidad de módulo (ver `design.md`, D4).
3. **Entorno local** (`Makefile`): `make lint` con el mismo comando que el CI.
4. **Documentación y pin** (`CONTRIBUTING.md` + `tests/test_ci_gates.py`): qué dispara cada gate,
   cómo reproducir el fallo y un test que rompe si el gate se afloja.

## Affected Areas

| Área | Impacto | Descripción |
|------|---------|-------------|
| `.github/workflows/ci.yml` | Modificado | Gate de cobertura explícito y lint con W/E bloqueante |
| `Makefile` | Modificado | `make lint` igual al CI |
| `CONTRIBUTING.md` | Modificado | Gates bloqueantes, umbrales y reproducción local |
| `src/api/presentation/routers/metrics.py` | Modificado | `_application` (W0613 real) |
| `src/ml/{main,pipeline/*}.py`, `tests/test_ml_*.py`, `tests/test_labeled_dataset.py` | Modificado | Imports `ml.*` |
| `ml/data/{generate_labeled_dataset.py,README.md}` | Modificado | Mismo import en el loader del dataset |
| `tests/test_ci_gates.py` | Nuevo | Pin de los tres gates |

## Vínculo con la investigación

Los gates son la condición de validez de todo lo que se mida después: sin lint bloqueante y sin
contrato bloqueante, una slice rota llega al piloto (C.3/C.4) y los números del piloto dejan de
ser comparables.

## Recursos

Sin dependencias nuevas y sin cambios en `requirements/dev.lock`: los gates usan las herramientas
que ya están fijadas (pytest-cov, flake8, pylint, schemathesis).

## Rollback

Revertir el commit de CI devuelve el pipeline anterior; el árbol sigue siendo compatible con el
comando viejo (`pylint --fail-under=9.0`, que ahora sale 0 igual). Revertir la unificación de
imports requiere revertir también `ml/data/generate_labeled_dataset.py` y los tests en el mismo
commit, porque el loader y los tests comparten la clase `MetricBatchInput`.
