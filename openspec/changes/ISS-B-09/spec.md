# SPEC — ISS-B-09: Quality gates bloqueantes en CI

**Tipo**: Delta spec. **Cambio**: B.9 (GitHub #71). **Base**: `proposal.md`, `design.md`, S11–S14.
**Alcance**: `.github/workflows/ci.yml`, `Makefile`, `CONTRIBUTING.md`, árbol de `src/ml/` y el pin
`tests/test_ci_gates.py`. No cambia la API, el contrato ni la base de datos.

## Capabilities

- **Nuevas**: `ci-gates`.
- **Modificadas**: ninguna de producto.

Entorno de referencia de todos los umbrales: el de `requirements/dev.lock` (pylint 4.1.3 /
astroid 4.3.4, Python 3.11), que es el que corren el CI y `make lint`.

---

## 1. ci-gates (Nueva)

### Requirement: QG-1 (cobertura < 70 % bloquea el PR, S11)

El job que corre la suite con `--cov` MUST pasar `--cov-fail-under=70` explícito. El valor MUST
ser igual a `fail_under` de `[tool.coverage.report]` en `pyproject.toml`, y ninguno de los dos MUST
bajar de 70. Ni el job ni el step MUST declarar `continue-on-error`, y el step MUST correr siempre
(sin `if`).

#### Scenario: cobertura insuficiente

- GIVEN la suite pasa pero la cobertura total de `src/` es 35 %
- WHEN el job corre `pytest --cov --cov-fail-under=70`
- THEN `pytest` sale con código ≠ 0 y reporta "Required test coverage of 70.0% not reached"

#### Scenario: alguien afloja el umbral

- GIVEN un cambio que baja `--cov-fail-under` o `fail_under` por debajo de 70
- WHEN corre `tests/test_ci_gates.py`
- THEN el test de S11 falla antes del PR

### Requirement: QG-2 (un warning o error de lint bloquea el PR, S12)

`flake8 src/ tests/` MUST correr sin `continue-on-error`: cualquier hallazgo (E/F/W) sale ≠ 0.
`pylint src/` MUST correr con `--fail-under=9.0` **y** `--fail-on=W,E`. El comando del CI MUST NOT
llevar `--disable`, y `pyproject.toml` MUST NOT desactivar categorías de mensajes. Con las
versiones del lock, `src/` MUST pasar con 0 warnings y 0 errores.

#### Scenario: warning aislado

- GIVEN el árbol contiene un `W0613` (un argumento sin usar) y el score queda en 9.91
- WHEN corre el gate del CI (`--fail-under=9.0 --fail-on=W,E`)
- THEN pylint sale ≠ 0 (verificado: exit 12 en la base `ac10991`)

#### Scenario: comando viejo, mismo árbol

- GIVEN el mismo árbol con el `W0613`
- WHEN corre el comando anterior (`--fail-under=9.0`, sin `--fail-on`)
- THEN pylint sale 0 y el PR podría mergearse: por eso S12 no se cumplía

#### Scenario: árbol actual

- WHEN corre `pylint src/ --fail-under=9.0 --fail-on=W,E` sobre este cambio
- THEN sale 0 con 9.91/10 y 0 mensajes W/E

### Requirement: QG-3 (contrato inválido bloquea el PR, S13)

El job `contract` MUST correr `tests/test_contract.py`, MUST NOT tolerar el fallo y `docker` MUST
tener `contract` en `needs`: un contrato roto frena el flujo completo y no queda como job
informativo.

#### Scenario: spec roto

- GIVEN `openspec/specs/openapi.yaml` sin el bloque `security` de `POST /telemetry/metrics`
- WHEN corre `pytest tests/test_contract.py`
- THEN falla `test_oas6_telemetry_paths_require_api_key` y el job queda rojo (verificado)

### Requirement: QG-4 (ningún gate traga fallos)

Ningún job ni step del workflow MUST declarar `continue-on-error: true`. Un gate que puede fallar
sin romper el check no es un gate.

#### Scenario: supresión agregada

- GIVEN un job o step con `continue-on-error: true`
- WHEN corre `tests/test_ci_gates.py`
- THEN el test de supresiones falla nombrando el job/step

### Requirement: QG-5 (el gate local es el mismo que el del CI)

`make lint` MUST correr el mismo comando bloqueante que el CI (`flake8 src/ tests/` y
`pylint src/ --fail-under=9.0 --fail-on=W,E`), sin `--disable`. El fallo MUST aparecer en la
máquina del que hace el cambio, no recién en el PR.

#### Scenario: fallo reproducido localmente

- GIVEN un warning nuevo
- WHEN se corre `make lint`
- THEN sale ≠ 0 con el mismo diagnóstico que el CI

### Requirement: QG-6 (gates documentados y verificados, S14)

`CONTRIBUTING.md` MUST documentar, por gate, el job, el umbral, qué lo dispara y el comando para
reproducir el fallo localmente, además de la calibración de pylint. Mientras MVP1 sea local y no
se pushee (S33 del plan), la verificación MUST ser `tests/test_ci_gates.py` (pin que lee workflow,
`pyproject.toml`, `Makefile` y `CONTRIBUTING.md`) **más** la evidencia negativa de cada gate en
este cambio; el "PR de prueba" de la issue se hace cuando existan PRs reales.

#### Scenario: documentación desactualizada

- GIVEN alguien borra de `CONTRIBUTING.md` el comando que reproduce el gate de lint
- WHEN corre `tests/test_ci_gates.py`
- THEN el test de S14 falla

#### Scenario: evidencia negativa de S11–S13

- GIVEN este cambio
- WHEN se fuerza cada fallo (cobertura 35 %, un warning, `security` borrado del spec)
- THEN los tres gates salen ≠ 0 y se vuelven a verde al restaurar la condición
