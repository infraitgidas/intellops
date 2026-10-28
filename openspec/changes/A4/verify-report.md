# Verify report: A.4 (generador sintético etiquetado)

**Veredicto: PASS_WITH_WARNINGS** — 0 CRITICAL, 3 WARNING, 2 SUGGESTION (tras remediar W1-W4, S2 y S3 de la revisión independiente).
Rango: `git diff origin/develop..HEAD` (rama `feat/A4`). Modo: strict TDD. Entorno: Windows 11, Python 3.13.9 (venv), numpy 2.5.3. El CI usa Python 3.11 (no disponible aquí).

## 1. Resultados de ejecución (reales, tras la remediación)

| Check | Comando | Resultado |
|---|---|---|
| flake8 (CI) | `flake8 src/ tests/` | 0 warnings, rc=0 |
| flake8 (extra) | `flake8 ml/data/generate_labeled_dataset.py tests/test_labeled_dataset.py` | 0 warnings, rc=0 |
| pylint (CI) | `pylint src/ --fail-under=9.0` | 9.63/10, rc=0 |
| Unit | `PYTHONPATH=. pytest -m unit -q` | 332 passed, 128 deselected (generador: 42 tests, antes 29) |
| Suite + cobertura | `alembic upgrade head` + `PYTHONPATH=. pytest --cov --cov-report=term-missing` | 459 passed, 1 xpassed, 0 failed; cobertura 89.89 % (gate 70 %) |
| Gramática 3.11 | `ast.parse(..., feature_version=(3, 11))` sobre generador y tests | OK |
| Corrida por defecto (×2) | `python ml/data/generate_labeled_dataset.py` (28 días) | 530 667 filas, CSV 51 327 189 bytes, ≈ 3.5 s CLI; sha256 `a90b1eccc9a8c524c143d157e861a6afdb95a7c8e5a2bb3a24b055cc343c26ed` en ambas corridas (igual al README); manifests idénticos |
| Lector | `load_labeled_dataset("ml/data/synthetic")` | train 425 029 + validation 105 638 filas validadas, ≈ 6 s |
| CLI inválido | `--days 1` | código 2, `days must be >= 8: ...`, sin traceback |
| Datos fuera de git | `git status --short` | `ml/data/synthetic/` ignorado |

Postgres: la instalación EDB del scratchpad sigue dañada. Se usó un contenedor descartable `postgres:16-alpine` (la imagen del CI) en `localhost:5432`, eliminado al terminar.

### Números de la corrida por defecto

| Dato | train | validation |
|---|---|---|
| Filas | 425 029 | 105 638 |
| Filas anómalas | 8 207 (1.93 %) | 1 981 (1.88 %) |
| Eventos por (tipo, severidad) | 12 | 3 |
| Filas hard negative | 10 656 | 3 044 |

Contaminación en seeds 0-9 con los defaults: train 1.83-1.97 %, validation 1.82-2.15 %. Filas por celda de validation: ver `ml/data/README.md`.

## 2. Matriz de cumplimiento

Tests en `tests/test_labeled_dataset.py`.

| ID | Test | Estado |
|---|---|---|
| SYN-1.1 | `test_same_seed_is_byte_identical`, `test_cli_writes_the_same_files` | COMPLIANT |
| SYN-1.2 | `test_different_seed_differs` | COMPLIANT |
| SYN-1.3 | `test_days_too_small_fails_with_clear_message`, `test_cli_reports_invalid_params_without_traceback` | COMPLIANT |
| SYN-2.1 | `test_every_row_validates_against_m4` | COMPLIANT |
| SYN-2.2 | `test_timestamps_aligned_utc_and_unique_per_series`, `test_bucket_seconds_parameter_is_honoured` | COMPLIANT |
| SYN-2.3 | `test_zero_session_buckets_are_omitted` | COMPLIANT |
| SYN-2.4 | `test_value_ranges` | COMPLIANT |
| SYN-2.5 | `test_large_buckets_keep_wall_clock_durations[900/3600/7000]` | COMPLIANT |
| SYN-2 (params) | `test_rejects_bucket_below_sixty` | COMPLIANT |
| SYN-3.1 | `test_daily_seasonality_in_sessions` | COMPLIANT |
| SYN-3.2 | `test_latency_is_right_skewed`, `test_latency_metrics_share_noise_within_app` | COMPLIANT |
| SYN-4 (etiquetas) | `test_labels_are_consistent` | COMPLIANT |
| SYN-4.1 | `test_every_type_and_severity_in_both_splits[7/8/9]`, `test_every_cell_has_min_events_in_both_splits`, `test_default_size_contamination_and_validation_depth` | COMPLIANT |
| SYN-4.2 | `test_correlated_incident_spans_metrics_of_one_app` | COMPLIANT |
| SYN-4.3 | `test_severity_magnitude_within_band` | COMPLIANT (ver W1) |
| SYN-4.4 | `test_labels_match_real_changes_against_clean_run` | COMPLIANT |
| SYN-5.1 | `test_events_do_not_overlap_and_anomalies_keep_min_gap`, `test_events_never_cross_the_split_boundary`, `test_train_and_validation_share_no_event` | COMPLIANT |
| SYN-5 (pico) | `test_about_a_third_of_anomalies_are_at_peak_hours` | COMPLIANT |
| SYN-5.2 | `test_default_size_contamination_and_validation_depth` (1.93 % / 1.88 %) | COMPLIANT (ver W2) |
| SYN-5.3 | `test_anomalies_can_sit_next_to_hard_negatives` | COMPLIANT |
| SYN-6.1 | `test_hard_negatives_are_benign_and_in_both_splits` | COMPLIANT |
| SYN-6.2 | `test_traffic_surge_raises_session_count_and_latency`, `test_hard_negatives_move_value_like_low_medium_anomalies` | COMPLIANT |
| SYN-6.3 | `test_maintenance_start_is_jittered` | COMPLIANT |
| SYN-7.1 | `test_split_is_temporal_with_global_boundary` | COMPLIANT |
| SYN-8 | `test_csv_has_exact_columns` | COMPLIANT |
| SYN-8.1 | `test_manifest_matches_csv` | COMPLIANT |
| SYN-9.1 | `test_loader_returns_validated_rows_and_labels`, `test_loader_parses_labels_and_values_row_by_row` | COMPLIANT |
| SYN-9.2 | `test_loader_rejects_tampered_csv` | COMPLIANT |
| SYN-9.3 | `test_module_is_decoupled_from_ingest` (AST) | COMPLIANT |

Criterios de aceptación de la issue #66: los 5 cubiertos (script reproducible en `ml/`; tipos y severidades etiquetados; CSV + manifest + README; split temporal; lector sin ingesta).

## 3. Revisión independiente: estado

| ID | Hallazgo | Estado |
|---|---|---|
| W1 | Validation con 1 evento por celda | RESUELTO: 3 por celda en cada split, 28 días por defecto (`b9f8751`) |
| W2 | Filas etiquetadas sin cambio real y filas creadas por la inyección | RESUELTO: test contra corrida limpia, 0 casos (`fd78755`) |
| W3 | `--bucket-seconds` grande inviable, `--days 1` con traceback | RESUELTO: duraciones en minutos, validación previa, código 2 (`4500f3c`) |
| W4 | Hard negatives memorizables y casi sin efecto en `value` | RESUELTO: hora sorteada, sin gap, 3-6 σ en `value` (`0430c0d`) |
| S2 | Advertir columnas que no son features | RESUELTO en README (`c6d57e8`) |
| S3 | Tests débiles | RESUELTO (`2794fab` y tests de cada fix) |

## 4. Hallazgos vigentes

| Sev. | ID | Hallazgo |
|---|---|---|
| WARNING | W1 | `dropout` usa bandas de fracción de sesiones perdidas, no sigmas (desviación documentada en design §3 y README). |
| WARNING | W2 | Con ventanas chicas la contaminación supera el 3 % (el mínimo de 3 eventos por combinación domina). Con los defaults queda en 1.93 % train / 1.88 % validation. |
| WARNING | W3 | La cobertura del CI mide solo `src/`; el generador vive en `ml/` y no suma al 89.89 %. Tampoco entra en el `pylint src/` del CI (localmente: 9.42/10, avisos de cantidad de argumentos/locales e `import-error` del import diferido). |
| SUGGESTION | S1 | B.6 debería reportar métricas por evento (vía `event_id`) además de por fila: validation tiene 3 eventos por celda y los eventos largos dominan las métricas por fila. |
| SUGGESTION | S4 | Subir `GENERATOR_VERSION` (sigue en `1.0.0` aunque la salida cambió) para distinguir datasets viejos por manifest. |

Chequeo de dificultad (z-score robusto ingenuo, no benchmark): recall por fila 28 % `low`, 42 % `medium`, 54 % `high`; marca 6.5 % de filas normales, 37 % de `benign_maintenance` y 12 % de `benign_traffic_surge`.

## 5. No verificado

- Ejecución con Python 3.11 (solo chequeo de gramática).
- Reproducibilidad del sha256 en Linux/CI (el hash documentado es de Windows + numpy 2.5.3).
- `MIN_DAYS = 8` es empírico (seeds 0-19); no hay garantía analítica para toda seed.
- `pip install -e ".[dev]"` limpio, `pip-licenses`, `docker compose build` (sin cambios de dependencias).
- El manifest incluye `python_version`: su contenido cambia entre versiones de Python aunque el CSV sea idéntico.
