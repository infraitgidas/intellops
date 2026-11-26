# Design: ISS-B-09 — Quality gates bloqueantes en CI

**Cambio**: B.9 (#71). **Base**: `proposal.md`, `spec.md` (QG-1..QG-6).
**Alcance**: el pipeline y el árbol que lo pasa. Sin cambios de producto.

## Contexto verificado (no supuesto)

Medido en un worktree detached de `ac10991` montado en el contenedor de
`docker-compose.test.yml` (versiones del lock):

| Gate | Comando | Resultado en la base |
|------|---------|----------------------|
| flake8 | `flake8 src/ tests/` | exit 0 (ya bloqueaba) |
| pylint (comando viejo) | `pylint src/ --fail-under=9.0` | exit 0 con 1 `W0613` (no bloqueaba) |
| pylint (gate nuevo) | `pylint src/ --fail-under=9.0 --fail-on=W,E` | exit 12 con 1 `W0613` |
| cobertura | `pytest ... --cov` (sin flag) | exit 1 por `fail_under = 70` |
| contrato | `pytest tests/test_contract.py` con spec roto | 1 failed |

Conclusión: S11 y S13 ya se cumplían en el fondo pero no estaban declarados ni fijados; S12 **no**
se cumplía.

## Decisiones

### D1 — `--cov-fail-under=70` explícito, además de `fail_under`

`pytest-cov` ya honra `[tool.coverage.report] fail_under` cuando se pasa `--cov`, así que el
umbral bloqueaba. Se declara igual en el job por dos razones: el umbral queda visible en el log del
CI (quien lee la corrida ve el gate, no lo infiere) y el pin `test_ci_gates.py` puede verificar los
dos valores y su igualdad. El valor no cambia: 70.

### D2 — `--fail-on=W,E` en lugar de subir `--fail-under`

Subir el score es la solución equivocada: un único warning deja el score en 9.9x y el job pasaría
igual, que es exactamente lo que pasaba con `W0613`. `--fail-on=W,E` convierte cada warning o error
en fallo del job, y `--fail-under=9.0` se mantiene como piso de calidad global. Los mensajes de
categoría `R` (refactor) y `C` (convención) siguen informativos: la convención del repo es no
romper el job por un `duplicate-code` (hoy hay 15 `R0801` en `src/`).

### D3 — Cero supresiones: se arregla el código

El primer intento de este cambio resolvía el `W0613` con `--disable=unused-argument` global. Se
descartó: desactivar `unused-argument` en todo el repo silencia también los `W0613` reales que
vendrán (hay tres routers más con `Depends`). La corrección es local y nombra la intención: el
catálogo `GET /metrics/list` es global, así que el parámetro que consume el `Depends` sin uso se
llama `_application` (pylint no reporta argumentos con guion bajo inicial).

Por la misma razón no se agregaron `# pylint: disable=not-callable` ni
`[tool.pylint."messages control"] disable = [...]`: con las versiones del lock esos mensajes
(`E1102` de `func.*`, `W2301` de `...` tras docstring, `E0401` de paquetes namespace) **no se
reportan**. Agregar supresiones "por las dudas" achica el gate sin necesidad.

Consecuencia operativa: la referencia es el lock. Un venv propio con `astroid` 4.0.x reporta 4
`E1101` falsos positivos sobre `FieldInfo.startswith` (pydantic) que el entorno fijado ya no
reporta. Se documenta en `CONTRIBUTING.md` y se corre `make lint` (contenedor), no el venv.

### D4 — Imports `src.ml.*` → `ml.*`

Los módulos de `src/ml/` importaban `src.ml.schemas`, mientras el resto del repo usa `api.*`,
`ml.rules`, `comms.*` y las imágenes resuelven con `PYTHONPATH=/app/src`. Dos problemas reales:

1. **Identidad de módulo**: cargar `src/ml/schemas.py` como `src.ml.schemas` y como `ml.schemas`
   produce **dos clases distintas** `MetricBatchInput`. El loader del dataset importaba
   `src.ml.schemas` y los tests `ml.schemas`, así que `isinstance(row, MetricBatchInput)` era
   falso aunque los datos fueran válidos. Se vio como test rojo en la primera corrida de este
   cambio, y desaparece unificando el import en el loader (`ml/data/generate_labeled_dataset.py`)
   y en los tests.
2. **Runtime de las imágenes**: `PYTHONPATH=/app/src` no expone `src.*`; el import sólo funcionaba
   por la presencia del repo root en `sys.path` (pytest), no en el contenedor.

En el entorno del lock, pylint 4.1.3 ya no reporta `E0401` para estos imports: la corrección es
por identidad y runtime, no para complacer al linter.

### D5 — Pin test en lugar del PR de prueba

S14 pide "gates documentados y verificados con un PR de prueba". MVP1 es local y no se pushea
(S33), así que no hay PR donde romper un gate a propósito. Se reemplaza por:

1. `tests/test_ci_gates.py`: lee `.github/workflows/ci.yml`, `pyproject.toml`, `Makefile` y
   `CONTRIBUTING.md` y falla si alguien baja un umbral, agrega `continue-on-error`, saca
   `contract` de `needs`, agrega `--disable`, desactiva categorías o deja la documentación sin el
   comando de reproducción.
2. Evidencia negativa local en el entorno fijado: cobertura 35 % → exit 1; un warning → exit 12;
   `security` borrado del spec → `test_oas6_telemetry_paths_require_api_key` falla.

El pin no reemplaza al PR de prueba (no prueba el pipeline real de GitHub), pero sí prueba las
condiciones que ese PR habría demostrado. Cuando MVP1 se mergee y haya PRs, el PR de prueba se
puede hacer igual.

## Alternativas descartadas

- **Gate por archivos cambiados** (`--fail-on` sólo sobre el diff): el CI no tiene esa
  información sin un paso extra, y el árbol entero ya pasa, así que no aporta.
- **`pylint --errors-only`**: no cumple S12 (los warnings son la mitad del criterio).
- **Cobertura por archivo** (`--cov-fail-under` por módulo): no lo pide la issue y obligaría a
  fijar umbrales por archivo sin datos de base.

## Riesgos

| Riesgo | Mitigación |
|--------|------------|
| Un warning nuevo rompe el job | Es el objetivo; el diagnóstico lo da `make lint` local |
| Falso positivo de pylint con una versión nueva | El lock fija la versión; actualizarla es un cambio explícito con su corrida |
| El pin se vuelve burocrático | Fija cinco invariantes, no estilos: umbral, `needs`, `--disable`, `continue-on-error` y reproducción local |
| Bajar el umbral "porque el árbol no llega" | El pin test lo impide; bajar el umbral es un cambio de política y rompe los tests |
