# Apply Progress — ISS-S3-02: Normalización y calidad de datos

**Cambio**: ISS-S3-02 (#41) · **Rama**: `feat/ISS-S3-02` (base `origin/develop` @ `1a46eb4`)
**Store**: openspec · **Modo**: Strict TDD (`strict_tdd: true`) · **Idioma**: español neutro técnico
**Delivery**: single PR con `size:exception` (aprobado por el mantenedor; presupuesto 800 líneas).
**Estado**: 18/18 tareas completas · listo para `sdd-verify`.

## Resumen

Se implementó una etapa de normalización pura y con nombre (`ingest_normalizer`)
que corre **antes** de la validación por evento (`Raw → Normalize → Validate →
Enqueue → Store`). La normalización resuelve **solo representación** y nunca
recorta magnitudes; la validación sigue siendo la autoridad única de rechazo.
El worker dejó de reescribir timestamps con `now()` y de re-coaccionar el valor.

## Estado por tarea

| Fase | Tarea | Estado | Evidencia principal |
|------|-------|--------|---------------------|
| 1 | 1.1 RED tests del normalizador | [x] | `tests/test_ingest_normalizer.py` (56 tests) |
| 1 | 1.2 RED contrato `_canonical_ts` | [x] | parametrizado aware/naïve/garbage/None |
| 1 | 1.3 Registros compartidos en `ingest_policy` | [x] | `UNIT_CONVERSIONS`, `METRIC_TYPE_ALIASES`, `ERROR_TYPE_CATALOG/ALIASES`, `COUNT_TYPES` |
| 1 | 1.4 `ingest_normalizer.py` (puro) | [x] | 97% cobertura |
| 1 | 1.5 REFACTOR + idempotencia | [x] | `normalize(normalize(e)) == normalize(e)` |
| 2 | 2.1 RED: normalizar antes de validar | [x] | 4 tests de servicio |
| 2 | 2.2 `_in_range`/`_validate_metric` (no finitos / no enteros) | [x] | +3 tests de política |
| 2 | 2.3 Wiring en `ingest_service` | [x] | encola payload canónico |
| 2 | 2.4 NORM-5 (ausentes / herencia) | [x] | herencia de ts de métrica; sin fabricación |
| 2 | 2.5 NORM-7 (límites de recursos) | [x] | pureza/determinismo + guard de dependencias |
| 3 | 3.1 RED limpieza del worker | [x] | guard estructural + ts canónico exacto |
| 3 | 3.2 `queue.py` sin `float()`/`now()`/precedencia | [x] | payload canónico del normalizador |
| 4 | 4.1 RED contrato enum `unit` | [x] | 3 tests de contrato (OAS-14) |
| 4 | 4.2 `openapi.yaml` enum ampliado + nota `error_type` | [x] | `[ms, count, s, sec, secs, msec, millis, counts]` |
| 5 | 5.1 RED integración `/telemetry/*` | [x] | alias→canónico persistido; naïve rechazado |
| 6 | 6.1 ADRs 0004..0007 + índice | [x] | Propuesto → Aceptado |
| 6 | 6.2 Docs + CHANGELOG | [x] | Contrato/Pipeline + entrada #41 |
| 7 | 7.1 Verificación (cobertura/lint/schemathesis) | [x] | 300 passed, 94.12% |

## Evidencia de Work Units (comando + resultado + rollback)

| Unit | Comando enfocado | Resultado | Harness runtime | Rollback |
|------|------------------|-----------|-----------------|----------|
| 1 Normalizador puro | `pytest tests/test_ingest_normalizer.py -m unit -q` | 63 passed (56 al cerrar Fase 1) | N/A — función pura | Revertir `ingest_normalizer.py` + registros de `ingest_policy.py` |
| 2 Wiring/validación | `pytest tests/test_ingest_telemetry.py -m unit -q` | 57 passed | N/A (dominio puro) | Revertir `ingest_service.py` + guards de `ingest_policy.py` |
| 3 Limpieza worker | `pytest tests/test_ingest_telemetry.py -m integration -q` (docker 3.11) | 20 passed (22 con Fase 5) | Postgres real + worker asyncio | Revertir `queue._build_rows` + payloads canónicos de tests |
| 4 Contrato/OpenAPI | `pytest tests/test_contract.py -m unit -q` | 15 passed | `from_path(openapi.yaml)` (schemathesis) | Revertir `openapi.yaml` + tests OAS-14 |
| 5 Integración HTTP | `pytest tests/test_ingest_telemetry.py -m integration -q` | 22 passed | httpx ASGI + Postgres real | Revertir tests de integración |
| 6 Docs/ADR | revisión de artefactos | ADRs Aceptado + docs + CHANGELOG | N/A | Revertir el commit de docs |
| 7 Verificación | `pytest tests/ --cov --cov-report=term-missing` | **300 passed, 1 xpassed; 94.12%** | suite completa (host venv + Postgres compose) | Revertir el PR completo |

## TDD Cycle Evidence

| Task | Test file | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|------|-----------|-------|------------|-----|-------|-------------|----------|
| 1.1 | `tests/test_ingest_normalizer.py` | Unit | N/A (nuevo) | ✅ escrito | ✅ 56 passed | ✅ 56 casos | ✅ lint 10/10 |
| 1.2 | `tests/test_ingest_normalizer.py` | Unit | N/A (nuevo) | ✅ escrito | ✅ passed | ✅ aware/naïve/garbage/datetime | ✅ `_as_datetime` extraído |
| 1.3 | (constantes) | Unit | ✅ 109 unit baseline | ✅ registros requeridos | ✅ passed | n/a estructural | ✅ lookup `_ERROR_TYPE_BY_FOLD` |
| 1.4 | `tests/test_ingest_normalizer.py` | Unit | N/A (nuevo) | ✅ módulo inexistente | ✅ 56 passed | ✅ NORM-1..7 | ✅ helpers extraídos |
| 1.5 | `tests/test_ingest_normalizer.py` | Unit | ✅ 56 | ✅ idempotencia | ✅ passed | ✅ cada alias | ✅ 97% cov |
| 2.1 | `tests/test_ingest_normalizer.py` | Unit | ✅ 165 unit | ✅ 4 tests servicio | ✅ passed | ✅ alias/desconocido/parcial/herencia | ➖ limpio |
| 2.2 | `tests/test_ingest_telemetry.py` | Unit | ✅ 54 | ✅ 3 tests política | ✅ passed | ✅ inf/nan/1.5/2.0 | ✅ guard `math.isfinite` |
| 2.3 | `tests/test_ingest_normalizer.py` | Unit | ✅ 165 | ✅ escrito | ✅ passed | ✅ 2 rutas (metric/js) | ➖ limpio |
| 2.4 | `tests/test_ingest_normalizer.py` | Unit | ✅ 165 | ✅ requerido/opcional | ✅ passed | ✅ herencia ts | ➖ limpio |
| 2.5 | `tests/test_ingest_normalizer.py` | Unit | ✅ | ✅ pureza/deps | ✅ passed | ✅ determinismo | ➖ limpio |
| 3.1 | `tests/test_ingest_telemetry.py` | Unit+Integration | ✅ 20 integración | ✅ guard `now()`/`float(` | ✅ passed | ✅ ts exacto + métrica | ✅ docstring refinado |
| 3.2 | `tests/test_ingest_telemetry.py` | Integration | ✅ 20 | ✅ (mismo) | ✅ 20 passed | ✅ persistencia real | ✅ worker limpio |
| 4.1 | `tests/test_contract.py` | Contract (`-m unit`) | ✅ 12 contrato | ✅ enum `[ms,count]` | ✅ 15 passed | ✅ enum + nota + unknown | ➖ limpio |
| 4.2 | `tests/test_contract.py` | Contract | ✅ | ✅ | ✅ passed | ✅ schemathesis carga | ➖ limpio |
| 5.1 | `tests/test_ingest_telemetry.py` | Integration | ✅ 20 integración | ✅ escrito (comportamiento de 2.x/3.x) | ✅ 22 passed | ✅ alias persistido + naïve | ➖ limpio |
| 6.1 | — | — | N/A | N/A (docs) | ✅ Aceptado | N/A | N/A |
| 6.2 | — | — | N/A | N/A (docs) | ✅ actualizado | N/A | N/A |
| 7.1 | suite completa | Unit+Integration+Contract | ✅ | N/A (verificación) | ✅ 300 passed | N/A | N/A |

## Comandos y resultados (verbatim)

```
# Safety net (baseline)
pytest -m unit                        -> 109 passed, 118 deselected
pytest tests/test_ingest_telemetry.py -m integration  -> 20 passed

# Cierre de fase 1
pytest tests/test_ingest_normalizer.py -m unit        -> 56 passed
flake8 <nuevos archivos>                              -> OK
pylint ingest_normalizer.py ingest_policy.py          -> 10.00/10

# Cierre de fase 2
pytest -m unit                        -> 175 passed, 118 deselected

# Cierre de fase 3
pytest tests/test_ingest_telemetry.py -m integration  -> 20 passed (docker, py3.11)

# Cierre de fase 4
pytest tests/test_contract.py -m unit                 -> 15 passed

# Cierre de fase 5
pytest tests/test_ingest_telemetry.py -m integration  -> 22 passed (docker, py3.11)

# Verificación final (fase 7)
flake8 src/ tests/                                    -> OK
pylint src/                                           -> 9.74/10 (sin issues nuevos)
pytest tests/ --cov --cov-report=term-missing         -> 300 passed, 1 xpassed; 94.12%
    ingest_normalizer.py: 94 stmts, 3 miss, 97%
```

> **Nota de entorno (verificado honestamente)**: la imagen de `intellops-core`
> del compose **no copia** `openspec/` ni instala `schemathesis`, por lo que los
> tests de contrato y de migraciones (`test_ddl_v1_0_sql_synced_with_0003`) no
> pueden correr dentro del contenedor (fallan por `FileNotFoundError` incluso en
> `develop`, sin relación con este cambio). La verificación final se corrió en el
> **venv del host** (con `openspec/` + `schemathesis`) apuntando al Postgres del
> compose vía IP de red (`172.18.0.4:5432`), replicando el job de CI. La capa
> `-m integration` también se verificó de forma independiente dentro del
> contenedor (py3.11): 22 passed.

## Deviations from Design

1. **Recorte de espacios en blanco acotado a campos de clasificación.** NORM-6/ADR-0005 mencionan "recortar espacios en blanco" de forma general. Se aplicó el trim **solo** a los campos de clasificación (`type`, `unit`, `error_type` — necesarios para canonicalizar). `message` y `stack_trace` **no** se recortan: son campos portadores de anomalía que D4/ADR-0005 prohíben reescribir. Documentado en el docstring del módulo.
2. **Contrato de `QueuedEvent.payload` = canónico.** El worker ahora consume payloads canónicos; los tests que encolaban directo al worker (saltando `IngestService`) se actualizaron para normalizar el payload (`_canonical_rum`/`_canonical_js`), reflejando el nuevo contrato. No se alteró ninguna aserción de comportamiento.
3. **`_build_rows` sin fallback.** Al quitar `now()`, un timestamp ausente se propaga como `None` y la BD (NOT NULL) lo rechaza (dead-letter) en lugar de inventarse. En producción el normalizador garantiza el `timestamp`, por lo que el evento aceptado siempre lo tiene.
4. **Ejemplo del test de política.** `test_policy_rejects_unknown_unit` usaba `unit: "s"`, que ahora es un alias aceptado en el borde del servicio; se cambió el ejemplo a `"furlongs"` para que represente una unidad realmente desconocida (la política sigue estricta sobre el payload canónico).

## Issues Found

Ninguno bloqueante. Notas:
- La aserción de pureza NORM-7 sobre dependencias se implementó inspeccionando el AST del módulo (`ast`) — es un guard estructural, no un test de comportamiento de I/O.
- `pylint src/` reporta warnings **preexistentes** en `queue.py` (ellipsis de `Protocol`, `too-many-instance-attributes`/`too-many-arguments` de `AsyncioIngestQueue`); no fueron introducidos por este cambio y el rating global mejoró (9.72 → 9.74).

## Remaining

Ninguna tarea pendiente. `size:exception` aplicado y declarado (ver abajo).

## Workload / PR Boundary

- **Mode**: single PR con `size:exception` (aprobado por el mantenedor; presupuesto 800 líneas).
- **Boundary**: `ingest_normalizer` puro + registros compartidos → wiring del servicio → limpieza del worker → contrato OpenAPI → integración → docs/ADR → verificación. Verificable y rebobínable como un único PR.
- **Impacto en el presupuesto**: cambio cohesivo (normalización end-to-end); no se dividió porque la ejecución de normalizar-antes-de-validar pierde sentido sin sus tres patas (normalizador + wiring + limpieza del worker).

## Commits locales (no se pusheó, no se abrió PR)

1. `feat(ingest): normalizador puro de representación RUM (ISS-S3-02)`
2. `feat(ingest): normalizar antes de validar y rechazar conteos no enteros (ISS-S3-02)`
3. `refactor(ingest): worker consume payload canónico del normalizador (ISS-S3-02)`
4. `feat(contract): amplía el enum unit de RumMetric con la familia de alias (ISS-S3-02)`
5. `test(ingest): integración /telemetry/* con normalización de unidad y ts (ISS-S3-02)`
6. `docs(ingest): ADRs 0004-0007 aceptados y documentación del pipeline (ISS-S3-02)`
7. `docs(openspec/changes/ISS-S3-02): marca la verificación completa (ISS-S3-02)`
