# Verify report: ISS-S3-04 (dataset operativo ML, M4)

**Veredicto: PASS_WITH_WARNINGS** — 0 CRITICAL, 3 WARNING, 6 SUGGESTION.
Rango revisado: `git diff 9b85365..HEAD` (rama `feat/ISS-S3-04`). Modo: strict TDD, runner pytest. Entorno: Python 3.13.9 (venv), Postgres 16.4 local (EDB). El CI usa 3.11, no disponible aquí.

## 1. Resultados de ejecución (reales)

| Check | Comando | Resultado |
|---|---|---|
| V2 flake8 | `flake8 src/ tests/` | 0 warnings, rc=0 |
| V2 pylint | `pylint src/ --fail-under=9.0` | 9.61/10, rc=0 (solo `duplicate-code` R0801 preexistente/ruido entre `api.*` y `ml.pipeline.__init__`) |
| V3 unit | `PYTHONPATH=. pytest -m unit` | 193 passed, 126 deselected, 0 fallos |
| V4 migraciones | `alembic upgrade head` -> `downgrade 0003` -> `upgrade head` (DB intellops) | OK; `alembic current` = `0004 (head)`. El primer `upgrade head` fue no-op (la DB ya estaba en 0004 de una corrida previa); el ciclo down/up sí corrió |
| V5 suite + cobertura | `pytest --cov --cov-report=term-missing` | 318 passed, 1 xpassed, 0 failed; cobertura total 89.48% (gate 70%). `src/ml`: config 100%, mapper 100%, schemas 100%, api_reader 96% (líneas 37-38 sin cubrir: rama `_error_code` ante JSON inválido). `0004` 100%. No se pidieron `--cov-report=xml/html/--junitxml` |
| V6 contract + migraciones | `pytest tests/test_contract.py tests/test_migrations.py` | 27 passed, 1 xpassed |
| V9 diff acotado | `git diff 9b85365..HEAD --name-only -- CHANGELOG.md openapi.yaml docs/adr src/api` | solo `0004_anomaly_series_anchor.py`; ADR-0008 ya estaba en el commit base `9b85365` |
| V10 | búsqueda `metric_id` en `src/ml`, generador y `ContratoEntradaSalida.md` | una sola coincidencia: nota histórica en `ContratoEntradaSalida.md:5` |
| Aislamiento | búsqueda `src.api|sqlalchemy|rum_metric|asyncpg` en `src/ml` | sin coincidencias (más test AST) |

**No ejecutados**: V1 (`pip install -e ".[dev]"` limpio), V7 (pip-licenses), V8 (`docker compose build`), Python 3.11 (solo hay 3.13), artefactos xml/html/junit de V5.

## 2. Matriz de cumplimiento

Evidencia: código `archivo:línea`; test = función en `tests/…`.

### ml-operational-dataset

| ID | Código | Test | Estado |
|---|---|---|---|
| MLD-1.1 | `src/ml/schemas.py:12-27` | `test_ml_worker::test_valid_record_without_metric_id`, `test_metric_id_is_forbidden` | COMPLIANT |
| MLD-1.2 | `schemas.py:19` | `test_missing_bucket_seconds_fails` | COMPLIANT |
| MLD-1.3 | `mock_data.json`, `ml/data/generate_mock_dataset.py` | `test_mock_data_json_has_no_metric_id`, `test_generator_output_validates_without_metric_id` (requiere numpy, ahora en dev) | COMPLIANT |
| MLD-2.1/2.2 | `pipeline/mapper.py:41-58` | `test_to_batch_maps_rows_and_propagates_bucket_seconds`, `test_to_batch_empty_list` | COMPLIANT |
| MLD-3.1 | `api_reader.py:41-47,87-91` | `test_reader_sends_authenticated_aligned_request` | COMPLIANT |
| MLD-3.2 | sin imports `src.api` | `test_src_ml_does_not_import_src_api` | COMPLIANT |
| MLD-4.1/4.2/4.3 | `api_reader.py:16-31` | `test_align_window_properties` (4 buckets x 8 offsets), `_start_not_aligned`, `_300_seconds`, `_overlapping_pulls_share_bucket_keys` | COMPLIANT |
| MLD-5.1 | `config.py:12-14` | `test_settings_defaults` | COMPLIANT |
| MLD-5.2 | `config.py:13` (`ge=60`) | `test_settings_bucket_seconds_below_60_fails` | COMPLIANT (no emite request: falla al instanciar) |
| MLD-6.1 | `api_reader.py:26` | `test_align_window_accepts_exactly_seven_days` | COMPLIANT (ver W-1 para buckets que no dividen 7 d) |
| MLD-6.2 | `config.py:16` (`le=10080`), `api_reader.py:26-27` | `test_settings_window_out_of_range_fails[10081]`, `test_align_window_rejects_more_than_seven_days_after_aligning` | COMPLIANT |
| MLD-6.3 | `api_reader.py:57-63` | `test_reader_422_includes_status_and_code` | COMPLIANT |
| MLD-7.1 | `mapper.py:51` | `test_to_batch_rejects_mixed_applications` | PARTIAL: solo verifica consistencia interna; no hay `application_id` esperado, un lote entero de otra app no se detecta (inherente al diseño: tenant por key) |
| MLD-7.2 | `mapper.py:51-52` | idem | PARTIAL (compara contra la 1.ª fila, no contra una app esperada) |
| MLD-8.1/8.2 | `mapper.py:24-38,47-57` | `test_to_batch_fail_fast_on_malformed_row`, `test_reader_malformed_row_returns_no_partial_data` | COMPLIANT (spec reconciliada a fail-fast) |
| MLD-9.1 | `api_reader.py:51-56` | `test_reader_auth_errors[401,403]` | COMPLIANT (el test solo verifica el status en el mensaje, no `exc.status`/`exc.code`) |
| MLD-9.2 | `api_reader.py:46-49,64-67` | `test_reader_5xx_is_unavailable`, `test_reader_timeout_is_unavailable` | COMPLIANT (la ausencia de fallback al mock no se afirma; solo se verifica que lanza) |
| MLD-9.3 | `api_reader.py:68-74` | `test_reader_body_out_of_contract` | COMPLIANT |
| MLD-10.1 | `config.py:10-11` | `test_settings_missing_required_names_variable` | COMPLIANT (ver W-2: vacío cuenta como presente) |
| MLD-10.2 | `SecretStr`, `api_reader.py:48,53` solo tipo/estado | `test_settings_api_key_not_in_repr`, `test_reader_does_not_fall_back_to_mock_and_does_not_log_key` | COMPLIANT |

### database

| ID | Código | Test | Estado |
|---|---|---|---|
| DB-ANOM-1.1 | `0004:45-64` | fixture `seeded` + `test_anomaly_timestamp_is_independent_of_bucket_start` | COMPLIANT |
| DB-ANOM-1.2 | `0004:50-51` | `test_anomaly_rejects_bucket_seconds_below_60` | COMPLIANT |
| DB-ANOM-1.3 | `0004:55-58` | `test_anomaly_rejects_unknown_application` | COMPLIANT |
| DB-ANOM-1.4 | columna `timestamp` conservada | `test_anomaly_timestamp_is_independent_of_bucket_start` | COMPLIANT |
| DB-ANOM-2.1 | `0004:41-42` | `test_0004_replaces_metric_id_with_series_anchor` | COMPLIANT |
| DB-ANOM-2.2 | sin FK a rum_metric | sin test | UNTESTED (consecuencia trivial de DB-ANOM-2.1) |
| DB-ANOM-3.1/3.2/3.3 | `0004:65-68` | `test_anomaly_unique_series_bucket_model` | COMPLIANT |
| DB-MIG-1.1 | `0004:39-68` | `test_0004_replaces_metric_id_with_series_anchor` | COMPLIANT |
| DB-MIG-1.2 | `0004:71-92` | `test_downgrade_0004_empty_table_restores_metric_id` | COMPLIANT |
| DB-MIG-1.3 | `0004:28-36,72` | `test_downgrade_0004_with_rows_fails_and_stays_at_0004` | COMPLIANT |
| DB-MIG-1.4 | `0004:39-40` | mismo test de DB-MIG-1.2 (`command.upgrade` sin datos, línea 435) | COMPLIANT |
| DB-DDL-1.1 | `ddl_v1.0.sql:258-297` | `test_ddl_v1_0_sql_synced_with_0004` | COMPLIANT (compara el texto de §9, no una DB cargada con el DDL; ver S-5) |
| DB-SCOPE-1.1 | `git diff --name-only` | verificado por ejecución (V9) | COMPLIANT |

### architecture

| ID | Evidencia | Estado |
|---|---|---|
| ARCH-AI-1.1 | `containers.md`/`interfaces.md` no actualizados (follow-up declarado) | PARTIAL, declarado |
| ARCH-AI-1.2 | sin SQL/sesiones en `src/ml` (búsqueda + test AST de imports) | COMPLIANT |
| ARCH-AI-2.1 | diagrama C4 no actualizado (follow-up declarado) | PARTIAL, declarado |
| ARCH-AI-3.1 | `docs/adr/0008-ml-dataset-http-pull-series-anchor.md` (commit base `9b85365`), 0004-0007 sin tocar | COMPLIANT |
| ARCH-AI-3.2 | test AST en un solo sentido (`src/ml` -> `src.api`); la dirección `src/api` -> `src/ml` no se verifica con test | PARTIAL (verificable a mano: sin imports) |

Resumen: 38 escenarios/requisitos evaluados; 31 COMPLIANT, 5 PARTIAL (2 declarados), 1 UNTESTED trivial, 0 MISSING.

## 3. Strict TDD

- Cada commit incluye tests y código juntos (`773b084`, `e623787`, `7c1aa88`): el historial no permite probar que el RED precedió al GREEN; tampoco lo contradice. Se reporta como no verificable, no como incumplimiento.
- Los tests afirman comportamiento observable (excepciones tipadas, parámetros del request, constraints en DB real), no implementación, con tres excepciones menores: 401/403 sin assert de `status/code`; "sin fallback al mock" no afirmado; reintentos de `HTTPTransport` no probados.
- `pytestmark = pytest.mark.unit` está a mitad de `tests/test_ml_worker.py` (aplica al módulo completo; funciona, solo es poco legible).

## 4. Hallazgos

### CRITICAL
Ninguno.

### WARNING

| # | Ubicación | Escenario de fallo concreto |
|---|---|---|
| W-1 | `src/ml/config.py:16`, `api_reader.py:22-27` | `bucket_seconds` no divisor de 604800 (p. ej. 500) con `window_minutes=10080` (permitido por config): al alinear `start` y `end` con floor, la ventana alineada mide 604500 o 605000 s según `now`. Probado: 43 de 72 offsets lanzan "window exceeds the 7 day read path limit" de forma intermitente. Con 60/300/900/3600/86400 funciona. Mitigación: validar en config `window_minutes*60 <= 604800 - bucket_seconds` cuando no divide, o alinear `start` hacia arriba (ceil) |
| W-2 | `config.py:10-11` | `INTELLOPS_API_BASE_URL=""` o `INTELLOPS_ML_API_KEY=""` se aceptan (probado). Falla recién en tiempo de request (UnsupportedProtocol -> DatasetReadError o 401). MLD-10.1 pide error de configuración explícito ante falta. Mitigación: `min_length=1` |
| W-3 | `tests/test_ml_dataset_reader.py:259-264,312-317` | Asserts débiles: 401/403 solo `match=status` (no `exc.status`/`exc.code`, que la spec MLD-9.1/design exigen como error tipado); "no fallback al mock" no verifica que el mock no se leyó. Un regreso que pierda `code` pasaría el CI |

### SUGGESTION

| # | Ubicación | Detalle |
|---|---|---|
| S-1 | `schemas.py:25` | Timestamp con sub-segundos (`21:15:00.900Z`) pasa la alineación porque `int()` trunca (probado). Usar `timestamp.microsecond == 0` o `timestamp() % b == 0` en float. La migración (`::bigint` redondea) tiene el mismo borde |
| S-2 | `schemas.py:15,20` | `value` acepta NaN/inf en el schema (solo `mapper.py:36` lo filtra); `metric_type_id` sin cota superior pese a `SMALLINT` (99999 pasa y falla recién al insertar anomalía); `session_count=True`/`1.0` aceptados. Usar `allow_inf_nan=False`, `le=32767`, `StrictInt` |
| S-3 | `config.py:18` | `http_timeout_seconds=inf` aceptado (probado); acotar con `le` |
| S-4 | `api_reader.py:57-63` | El mensaje 422 dice "alignment bug" aun cuando el código sea otro; mensaje engañoso en diagnóstico |
| S-5 | `test_ddl_v1_0_sql_synced_with_0004` | Compara texto; un test más fuerte aplicaría el DDL a una DB temporal y compararía `information_schema` |
| S-6 | `mapper.py:51`, `schemas.py:16` | MLD-7 sin `application_id` esperado en config; `UUID4` rechaza UUID no v4 (open question del design sin cerrar) |

## 5. Verificaciones adversarias sin defecto

- `align_window`: naive tz, `start>=end`, ventana >7 d y exacta de 7 d, fin exactamente en frontera y zona horaria no UTC (-03:00 normalizada a UTC) manejados correctamente.
- Mapeo de errores: 401/403/422/5xx/timeout/cuerpo no JSON/no lista/URL inválida se traducen a `DatasetReadError` con `status`/`code` donde corresponde; `HTTPError` cubre timeouts y errores de conexión; sin follow_redirects (3xx cae como no disponible).
- Migración `0004`: el guard cuenta filas de `anomaly` en upgrade y downgrade; DDL transaccional revierte (probado por test). `alert` referencia `anomaly`, por lo que `anomaly` vacía implica nada que romper. Tipos coinciden con las FK (la migración aplica). Índice único incluye las 5 columnas de la spec. CHECKs presentes.
- Sin cross-import `src/ml` -> `src/api`; sin SQL en `src/ml`.
- Sintaxis: solo `typing.List/Optional/Tuple` y f-strings simples; compatible con 3.11 por inspección (no ejecutado en 3.11).

## 6. No verificado

Ejecución en Python 3.11; V1, V7 (licencias), V8 (docker build); orden RED/GREEN real; reportes xml/html/junit de cobertura; carga real del `ddl_v1.0.sql` en una DB.

## 7. Follow-ups

1. Corregir W-1 y W-2 (cambios pequeños en `config.py`/`api_reader.py`) con test previo.
2. Reforzar asserts de W-3.
3. ARCH-AI-1/2: actualizar `containers.md` §2.3/C4 e `interfaces.md` §2.1 (declarado).
4. Decidir sobre `UUID4` vs UUID cualquiera.
5. Avisar a Santiago (owner DB) sobre `0004` antes del merge; documentar en el PR el estado de `rum_mock.json`.
