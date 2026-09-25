# Apply Progress — ISS-S2-03: Ingesta RUM asíncrona

- **Change**: ISS-S2-03 (GitHub #37)
- **Rama**: `feat/ISS-S2-03` (base `origin/develop`, ISS-S2-01 + ISS-S2-02 mergeados)
- **Modo**: Strict TDD (config.yaml `apply.tdd: true` / `testing.strict_tdd: true`)
- **Delivery**: single-pr con **`size:exception` aprobado** por el maintainer (estimado 1400–1900 líneas; autorizado)
- **Store de artefactos**: openspec (repo-local); engram topic_key `sdd/ISS-S2-03/apply-progress`
- **Idioma**: artefactos en español neutro; código/comentarios en inglés (instrucción del orquestador)

## Estado

**17/17 tareas completadas** · Suite: **209 passed, 1 xpassed** (baseline 142) ·
Coverage **93.06%** (≥70 exigido) · flake8 limpio (max-line-length=99) ·
pylint **8.83/10** (≥7.0) · openapi.yaml válido (carga en schemathesis, OAS-9).

## TDD Cycle Evidence

| Tarea | Test File | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|-------|-----------|-------|------------|-----|-------|-------------|----------|
| 1.1 | `tests/test_ingest_telemetry.py` | Unit | ✅ 142/142 | ✅ Written (ModuleNotFound) | ✅ 21 passed | ✅ 21 casos (7 códigos, límites, ratings, tz) | ✅ Constantes extraídas |
| 1.2 | `tests/test_ingest_telemetry.py` | Unit | ✅ 142/142 | ✅ Written (ImportError) | ✅ 1 passed | ➖ Estructural (mirror DDL) | ✅ metadata_json (atributo reservado) |
| 1.3 | `tests/test_ingest_telemetry.py` | Unit | ✅ 142/142 | ✅ Written (AttributeError) | ✅ 3 passed | ✅ 3 casos (defaults, env, error) | ➖ None needed |
| 1.4 | `tests/test_ingest_telemetry.py` | Unit | ✅ 142/142 | ✅ Written (ImportError) | ✅ 4 passed | ✅ 4 casos (snapshot, acumulación) | ➖ None needed |
| 2.1 | `tests/test_ingest_telemetry.py` | Unit/Integration | ✅ 29/29 | ✅ Written (ImportError) | ✅ 12 passed | ✅ 12 casos (envelope, parcial, tenant) | ✅ Evento laxo vs envelope estricto |
| 2.2 | `tests/test_ingest_telemetry.py` | Unit | ✅ 48/48 | ✅ Written (ImportError) | ✅ 4 passed | ✅ 4 casos (full, close, qsize, capacity) | ✅ `worker_loop` con flush de chunk |
| 2.3 | `tests/test_ingest_telemetry.py` | Integration (Postgres real) | ✅ 48/48 | ✅ Written (ImportError repo) | ✅ 3 passed | ✅ 3 casos (persistencia, retry, dead-letter) | ✅ Logger.exception en dead-letter |
| 2.4 | `tests/test_ingest_telemetry.py` | Integration | ✅ 52/52 | N/A (RED cubierto por 2.3) | ✅ cubierto por 2.3 | ✅ pg_insert + `__table__` | ✅ Core insert con `__table__` |
| 3.1 | `tests/test_ingest_telemetry.py` | Integration (httpx ASGI) | ✅ 52/52 | ✅ Written (404 router) | ✅ 7 passed | ✅ 7 casos (401/403/IAUTH-2/503/202) | ➖ None needed |
| 3.2 | `tests/test_ingest_telemetry.py` | Integration | ✅ 59/59 | ✅ Written (422 en telemetry) | ✅ 3 passed | ✅ 3 casos (400 scoped + regresión admin) | ✅ Handler delega 422 estándar |
| 3.3 | `tests/test_ingest_telemetry.py` | Integration/Unit | ✅ 62/62 | ✅ Written (timeout sin log) | ✅ 3 passed | ✅ 3 casos (drenado, timeout, close) | ✅ getMessage() en asserts |
| 3.4 | `tests/test_ingest_auth.py` | Unit (wiring) | ✅ 6/6 | ✅ Test viejo roto (wiring nuevo) | ✅ 7 passed | ✅ 2 paths cubiertos | ✅ `_walk_apiroutes` (_IncludedRouter) |
| 4.1 | `tests/test_contract.py` | Contract (YAML) | ✅ 3/3 | ✅ Written (7 fails vs YAML viejo) | ✅ 10 passed | ✅ 7 aserciones OAS-6/9/10/11/12 | ➖ None needed |
| 4.2 | `tests/test_contract.py` + `test_ingest_telemetry.py` | Contract/Integration | ✅ 10/10 | ✅ Written | ✅ 3 passed | ✅ 3 casos (log redactado, contadores, queue_depth) | ➖ None needed |
| 4.3 | suite + flake8 + pylint | Gate | ✅ 209/209 | N/A | ✅ 209 passed, 93.06% | ✅ flake8/pylint/openapi | ✅ disables pylint inline |
| 5.1 | docs (ARCH-1..4) | Docs | N/A | N/A | ✅ grep sin rutas viejas | ✅ 6 archivos alineados | ➖ None needed |
| 5.2 | ADR-0002 + CHANGELOG | Docs | N/A | N/A | ✅ ADR verificado vs DD-7 | ✅ CHANGELOG registrado | ➖ None needed |

## Work Unit Evidence

| Work unit | Comando de test enfocado + resultado | Runtime harness + resultado | Rollback boundary |
|-----------|--------------------------------------|-----------------------------|-------------------|
| 1 (política, entidades, config, contadores) — commit `47b2e89` | `pytest tests/test_ingest_telemetry.py -q` → 29 passed | N/A (política pura, sin runtime) | Revertir `47b2e89` (policy/entities/config/counters) |
| 2 (schemas, service, queue, repos) — commit `44fd89b` | `pytest tests/test_ingest_telemetry.py -q -k "test_worker or test_queue or service"` → 22 passed | httpx ASGI + Postgres real: persistencia verificada (rum_metric=2, js_exception=1, user_session.app_id=tenant) | Revertir `44fd89b` (ingest/ + repos) |
| 3 (router, guard, errors, main, wiring) — commit `db9906d` | `pytest tests/test_ingest_telemetry.py tests/test_ingest_auth.py -q` → 60 passed | httpx ASGI: 401/403/IAUTH-2/503 backpressure real (maxsize 1) | Revertir `db9906d` (router/errors/main) |
| 4 (openapi + contract tests) — commit `4969a83` | `pytest tests/test_contract.py -q` → 10 passed, 1 xpassed | schemathesis live scoped (incluye /telemetry/*) | Revertir `4969a83` (openapi + tests) |
| 5 (specs de arquitectura + docs + ADR + changelog) — commit `4402e87` | `pytest -q` → 209 passed, 1 xpassed | grep ARCH-1..4: 0 rutas viejas en specs/docs vivas; históricos intactos | Revertir `4402e87` (docs) |

## Notas de implementación y desviaciones menores (documentadas, sin re-abrir decisiones)

1. **Validación del envelope en la frontera Pydantic, no en el service** (fiel a RUM-2/D5): el envelope se valida en los schemas (schema_version, 1..500 events) → 422 → handler scoped → 400 `schema_validation_error`. El service recibe el batch ya validado y aplica SOLO la política por evento.
2. **Eventos Pydantic laxos a propósito**: UUID/timestamps/longitudes/límite de 50 métricas NO se validan en el schema del evento; la política por evento decide (202 parcial con su código). Los `maxLength`/`maxItems` del OpenAPI quedan como contrato declarativo; el enforcement runtime es la política (RUM-3/RUM-4).
3. **Retry transitorio + dead-letter viven en el worker** (`queue.py`, según design DD-4 snippet), no en el repo SQLAlchemy (la tarea 2.4 los mencionaba en el repo). El repo expone `persist_chunk` sin commit (ADR-10); el worker coordina sesión/commit/retry/dead-letter. Decisión alineada con design.md y ADR-0002.
4. **Contador dead-letter**: `ingest.persistence_dead_letter_total` (nombre de la spec RUM-6 y PipelineIngestaRUM §3.1), que cumple el prefijo `ingest.` + sufijo `_total` exigido por el orquestador.
5. **Gotcha de entorno**: `alembic env.py` corre `fileConfig(alembic.ini)` (disable_existing_loggers default True) durante la migración de sesión y deja `disabled` los loggers de `api.*` creados antes → los logs de ingesta no se capturaban con caplog. Fixture `_reenable_ingest_loggers` los re-habilita. En producción no aplica (alembic corre en proceso aparte en el CMD).
6. **FastAPI reciente envuelve los routers en `_IncludedRouter`** (sin `.path` en `app.routes`): el test de wiring IAUTH-5 usa `_walk_apiroutes` para desenvolver `original_router.routes`.
7. **`insert().on_conflict_do_nothing` es de `sqlalchemy.dialects.postgresql.insert`**; y el mapper ORM colisiona con la columna reservada `metadata` → los inserts Core usan `__table__` y `metadata_json` como atributo.

## Resultado de la fase

- Tareas: 17/17 `[x]` en `openspec/changes/2026-09-25-ISS-S2-03/tasks.md`
- Commits (work units): `47b2e89`, `44fd89b`, `db9906d`, `4969a83`, `4402e87`
- Sin PR creado (el orquestador pedirá aprobación); sin push.
- `next_recommended`: **sdd-verify**