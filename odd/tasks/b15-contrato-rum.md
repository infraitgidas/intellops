# B.15 — Seguimiento de contrato RUM (ISS-B-15, issue #75)

Owner: Federico. Fase B, prioridad Alta. Depende de A.3 (cerrada, #64).
Contrato normativo: `docs/architecture/ContratoAgenteRUM.md` §13–§14. Rama: `feat/ISS-B-15`.

## Objetivo

Ejecutar las cuatro correcciones que quedaron como seguimiento al cerrar A.3, para que
la implementación quede alineada con el contrato v0.1 del agente RUM, más la corrección
de redacción de secretos detectada en la revisión posterior al merge de B.1.

## Problema

El contrato y el código divergieron en cuatro puntos (OD-03, OD-04/D-02, D-03, D-04).
Dos de ellos (D-03, D-04) documentan campos y respuestas que no existen o que el ingest
no persiste; B.15 es justamente el cambio que elimina ese patrón, así que declarar
`sample_rate` sin persistirlo repetiría el defecto que se está corrigiendo.

## Alcance

Dentro:

- OD-03: `sample_rate` opcional en `JsExceptionEvent`, enviado por el agente y
  **persistido** en `js_exception`.
- OD-04/D-02: validación por evento de `schema_version` con `^1\.0$` en la política de
  ingesta (no en Pydantic).
- D-03: quitar `viewport` y `connection` del OpenAPI de `RumEvent.metadata`.
- D-04: quitar el `429` de `/telemetry/metrics` y `/telemetry/exceptions` (el `429` de
  `/assistant/query` **se mantiene**).
- Redacción de secretos: `SECRET_PAIR_RE` con `(^|[?&;,\s])` (ya commiteado en `28181c2`).

Fuera:

- `page_url` y `agent_version` en `JsExceptionEvent` (diferidos por OD-03).
- Rate limit real (queda en OD-06).
- Tests del agente en CI: se dejan locales por decisión del owner.
- CI: no se toca `.github/workflows/ci.yml`.

## Decisiones

- **D1 — `sample_rate` se persiste.** Declararlo en el contrato sin guardarlo es
  exactamente el defecto que D-03 corrige, y el análisis de §5 necesita pesar por
  `1 / sample_rate`. Se agrega columna nullable, entidad, repositorio y cola.
- **D2 — `sample_rate` es opcional.** §3: un campo obligatorio nuevo exigiría
  `schema_version` 1.1. `required` no cambia.
- **D3 — nuevo código de rechazo `invalid_schema_version`.** Los siete códigos existentes
  no describen un valor presente pero inválido; reutilizar `missing_required_field` o
  `invalid_range` mentiría en el campo `rejected[].reason`. Pasa a ser el octavo código.
- **D4 — la validación por evento vive en `ingest_policy`.** Un `Field(pattern=...)` en
  los modelos de evento devolvería 400 de batch completo y rompería el 202 parcial.

## Tasks

| ID | Tarea | Specs | Ruta | Estado | Commit |
|----|-------|-------|------|--------|--------|
| T0 | Redacción de secretos al inicio del texto | OD contrato §9 | parent | ✅ | `28181c2` |
| T1 | OpenSpec change `ISS-B-15`: proposal + tasks | — | delegated | ✅ | `8a0d9fa` |
| T2 | D-04: quitar `429` de telemetría en OpenAPI, interfaces y docs + tests | D-04 | delegated | ✅ | `439a022` |
| T3 | D-03: quitar `viewport`/`connection` del OpenAPI + test | D-03 | delegated | ✅ | `811e770` |
| T4 | OD-04/D-02: validación por evento de `schema_version` + código `invalid_schema_version` | OD-04 | delegated | ✅ | `96170b1` |
| T5 | OD-03: `sample_rate` en contrato, agente, ingest y persistencia (DDL + migración) | OD-03 | delegated | ✅ | `7457232` |
| T6 | Actualizar estado de §13/§14 en el contrato + CHANGELOG | — | delegated | ✅ | `39212c9` |
| T7 | Revisión de la issue #75: validar `sample_rate` (0..1, finito) en `ingest_policy`, matrices de ingesta/agente y tests de migración 0005 | OD-03 | parent | ✅ | `7eabf92` |

## Criterios de aceptación

- [x] OD-03: `sample_rate` presente en `JsExceptionEvent` (OpenAPI + Pydantic), enviado
      por el agente y persistido en `js_exception`.
- [x] OD-03: `sample_rate` fuera de 0..1 o no finito se rechaza con `invalid_range`
      antes de encolar (202 parcial), igual que el rango declarado en OpenAPI.
- [x] OD-04/D-02: un evento con `schema_version` distinto de `1.0` se rechaza y el resto
      del batch se acepta (202 parcial).
- [x] D-03: `viewport` y `connection` ya no están en el OpenAPI.
- [x] D-04: `/telemetry/*` ya no declara `429`; `/assistant/query` lo conserva.
- [x] Contract tests verdes y OpenAPI actualizado.

## Verificación

```bash
.venv/bin/python -m pytest tests/test_contract.py -q
.venv/bin/python -m pytest -m unit -q
.venv/bin/python -m pytest tests/test_migrations.py -q   # requiere Postgres aislado
.venv/bin/python -m pytest -m integration -q            # requiere Postgres aislado
cd src/agent && npm test
```

Falla ambiental conocida en la base: `tests/test_ml_worker.py::
test_generator_output_validates_without_metric_id` falla por `ModuleNotFoundError:
No module named 'numpy'` en `.venv`. No es causada por este cambio.

## Log

- **L1** (2026-10-30): B.15 arranca con la corrección de redacción de secretos
  (`28181c2`), detectada en la revisión post-merge de B.1.
- **L2** (2026-10-30): exploración del alcance completo. Estado actual verificado:
  `sample_rate` existe en métricas pero no en excepciones; `schema_version` sólo se valida
  en el envelope; `viewport`/`connection` se declaran y se descartan; el `429` no está
  implementado en el servidor.

- **L3** (2026-10-30, cierre de implementación): T1–T6 commiteadas (`8a0d9fa`, `439a022`,
  `811e770`, `96170b1`, `7457232`, `39212c9`) más el documento (`bffeac9`). Verificación
  observada: contract tests 19 passed + 1 xpassed; unit 298 passed con la única falla
  ambiental de `numpy`; agente 79/79. Riesgo nativo: **medium**, 23 paths / 533 líneas,
  `review_due` por `slice_budget_reached`. Review bloqueada por `managed_assets_outdated`
  (requiere `gentle-ai sync --agent opencode`).

- **L4** (2026-10-30, review de la issue #75): dos huecos corregidos en T7.
  1. `sample_rate` llegaba a `ExceptionRow` y a la DB **sin validación**, aunque el
     OpenAPI que este mismo cambio declara impone 0..1 y el análisis pondera por
     `1 / sample_rate` (un `NaN` o `Infinity` rompe la ponderación). Se valida en
     `validate_js_exception` con `invalid_range` (nuevo `_sample_rate_is_valid`) contra
     el rango declarado **0..1 inclusivo**, antes de encolar: el 202 parcial se mantiene
     y la fila inválida no se escribe. Queda anotada para QA la tensión de
     `sample_rate = 0` con `1 / sample_rate` (el contrato lo admite, el análisis no): no
     se cambia el rango por decisión unilateral.
  2. La rama agregaba la migración `0005` sin tocar `tests/test_migrations.py`: varias
     precondiciones `_current_revision(conn) == REV_0004` fallaban al subir head a 0005
     y no había test de la migración nueva. Se actualizaron a `REV_0005` y se agregaron
     `test_0005_adds_sample_rate_to_js_exception` (upgrade/downgrade) y
     `test_ddl_v1_0_sql_synced_with_0005`. Además se completaron las matrices de
     `ContratoIngestaRUM` (`schema_version`, `sample_rate`, DDL) y el `sampleRate` de la
     tabla de excepciones en `ContratoAgenteRUM`.
  Verificación: contract 19 passed + 1 xpassed; unit 298 passed (única falla ambiental
  de `numpy`); agente 79/79; `tests/test_migrations.py` 17 passed y `-m integration`
  130 passed sobre una base Postgres aislada (`intellops_b15_verify`, creada y eliminada
  para la corrida). T7 commiteada en `7eabf92`.

- **L5** (2026-10-30, bloqueo de review nativa, causa real): la nota de L3 decía
  `managed_assets_outdated` + `--agent opencode`; el stop real es `--agent pi`, y tras
  `gentle-ai sync --agent pi` (y `--agent opencode`) los assets ya estaban al día, pero el
  stop siguió hasta refrescar el STATUS: se destrabó. El bloqueo de fondo es otro y es
  estructural: el controlador deriva la base de **`origin/main`** (`a58e0cd`), que está 220
  commits atrás de `develop` (base real de las PR de este repo). El candidato resultante
  son 286 paths / ~46k líneas, y `review start` falla en preflight con
  `lens_context_budget_exceeded` (sin crear autoridad: `mutation_outcome: not_started`,
  nada que reparar). Pasar `baseRef=develop` + `committedOnly: true` al START se rechaza
  con `native-start-retained-selection-candidate-mismatch`, porque la selección retenida
  quedó atada al árbol de `origin/main`. Es decir: la review nativa no puede cubrir el
  slice B.15 mientras la base derivada sea `main`.
  Verificación del mismo día: `make ci` en el entorno docker (Postgres 16 efímero) en
  verde — lint OK, 431 passed + 1 xpassed, cobertura 90.39 % (ahí el fallo de `numpy` del
  host no aparece).
  Salidas posibles (decisión del owner): (a) política de review repo-local que fije
  `develop` como base (`--policy`), (b) refrescar el espejo local de `origin/main` al tip
  de `develop` para el scope de review, o (c) `gentle-ai review mode disable --scope clone`
  y seguir con revisión humana + CI, que ya está verde.
