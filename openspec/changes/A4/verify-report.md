# Verify report: A.4 (generador sintético etiquetado)

**Veredicto: PASS_WITH_WARNINGS** — 0 CRITICAL, 3 WARNING, 2 SUGGESTION.
Rango: `git diff origin/develop..HEAD` (rama `feat/A4`). Modo: strict TDD. Entorno: Windows 11, Python 3.13.9 (venv), numpy 2.5.3. El CI usa Python 3.11 (no disponible aquí).

## 1. Resultados de ejecución (reales)

| Check | Comando | Resultado |
|---|---|---|
| flake8 (CI) | `flake8 src/ tests/` | 0 warnings, rc=0 |
| flake8 (extra) | `flake8 ml/data/generate_labeled_dataset.py tests/test_labeled_dataset.py` | 0 warnings, rc=0 |
| pylint (CI) | `pylint src/ --fail-under=9.0` | 9.63/10, rc=0 |
| Unit | `PYTHONPATH=. pytest -m unit -q` | 319 passed, 128 deselected (baseline previo: 290; +29 nuevos) |
| Suite + cobertura | `alembic upgrade head` + `PYTHONPATH=. pytest --cov --cov-report=term-missing` | 446 passed, 1 xpassed, 0 failed; cobertura 89.89 % (gate 70 %) |
| Gramática 3.11 | `ast.parse(..., feature_version=(3, 11))` sobre los 2 archivos nuevos | OK |
| Corrida por defecto | `python ml/data/generate_labeled_dataset.py` | 264 670 filas, CSV 25 589 258 bytes, ≈ 1.9 s; sha256 `2ce13c8ee9869279b777d668351c3e1716c9b58520b561613803fb8949f0e625` |
| Lector | `load_labeled_dataset("ml/data/synthetic")` | train 214 909 + validation 49 761 filas validadas, ≈ 3 s |
| Datos fuera de git | `git status --short` | `ml/data/synthetic/` ignorado |

Postgres: la instalación EDB del scratchpad estaba dañada (faltan `share/postgres.bki` y archivos de catálogo del data dir). Se usó un contenedor descartable `postgres:16-alpine` (la misma imagen del CI), detenido y eliminado al terminar.

## 2. Matriz de cumplimiento

Tests en `tests/test_labeled_dataset.py`.

| ID | Test | Estado |
|---|---|---|
| SYN-1.1 | `test_same_seed_is_byte_identical`, `test_cli_writes_the_same_files` | COMPLIANT |
| SYN-1.2 | `test_different_seed_differs` | COMPLIANT |
| SYN-2.1 | `test_every_row_validates_against_m4` | COMPLIANT |
| SYN-2.2 | `test_timestamps_aligned_utc_and_unique_per_series`, `test_bucket_seconds_parameter_is_honoured` | COMPLIANT |
| SYN-2.3 | `test_zero_session_buckets_are_omitted` | COMPLIANT |
| SYN-2.4 | `test_value_ranges` | COMPLIANT |
| SYN-2 (params) | `test_rejects_bucket_below_sixty`, `test_infeasible_window_fails_explicitly` | COMPLIANT |
| SYN-3.1 | `test_daily_seasonality_in_sessions` | COMPLIANT |
| SYN-3.2 | `test_latency_is_right_skewed`, `test_latency_metrics_share_noise_within_app` | COMPLIANT |
| SYN-4 (etiquetas) | `test_labels_are_consistent` | COMPLIANT |
| SYN-4.1 | `test_every_type_and_severity_in_both_splits` | COMPLIANT |
| SYN-4.2 | `test_correlated_incident_spans_metrics_of_one_app` | COMPLIANT |
| SYN-4.3 | `test_severity_magnitude_within_band` | COMPLIANT (ver W1) |
| SYN-5.1 | `test_events_do_not_overlap_and_keep_min_gap`, `test_events_never_cross_the_split_boundary` | COMPLIANT |
| SYN-5 (pico) | `test_some_anomalies_are_placed_at_peak_hours` | COMPLIANT |
| SYN-5.2 | `test_contamination_within_target_for_default_size` (1.84 % real) | COMPLIANT (ver W2) |
| SYN-6.1 | `test_hard_negatives_are_benign_and_in_both_splits`, `test_traffic_surge_raises_session_count` | COMPLIANT |
| SYN-7.1 | `test_split_is_temporal_with_global_boundary` | COMPLIANT |
| SYN-8 | `test_csv_has_exact_columns` | COMPLIANT |
| SYN-8.1 | `test_manifest_matches_csv` | COMPLIANT |
| SYN-9.1 | `test_loader_returns_validated_rows_and_labels` | COMPLIANT |
| SYN-9.2 | `test_loader_rejects_tampered_csv` | COMPLIANT |
| SYN-9.3 | `test_module_is_decoupled_from_ingest` (AST) | COMPLIANT |

Criterios de aceptación de la issue #66: los 5 cubiertos (script reproducible en `ml/`; tipos y severidades etiquetados; CSV + manifest + README; split temporal; lector sin ingesta).

## 3. Hallazgos

| Sev. | ID | Hallazgo |
|---|---|---|
| WARNING | W1 | `dropout` usa bandas de fracción de sesiones perdidas, no sigmas (desviación documentada en design §3 y README). |
| WARNING | W2 | Con ventanas chicas la contaminación supera el 3 % (validation 7-10 % con 3 días y 2 apps): el mínimo de un evento por combinación domina. Con los defaults queda en 1.90 % train / 1.59 % validation. |
| WARNING | W3 | La cobertura del CI mide solo `src/` (`[tool.coverage.run] source`); el generador vive en `ml/` y no suma al 89.89 %. Tampoco entra en el `pylint src/` del CI (localmente: 9.46/10, solo avisos de cantidad de argumentos/locales). |
| SUGGESTION | S1 | B.6 debería reportar métricas por evento (vía `event_id`) además de por fila: los eventos largos dominan las métricas por fila. |
| SUGGESTION | S2 | Chequeo de dificultad (z-score robusto ingenuo, no benchmark): recall por fila 25 % `low`, 44 % `medium`, 59 % `high`, con 6.7 % de filas normales marcadas; `benign_maintenance` se marca el doble que lo normal. Usarlo como piso de referencia en B.6. |

## 4. No verificado

- Ejecución con Python 3.11 (solo chequeo de gramática).
- Reproducibilidad del sha256 en Linux/CI (el hash documentado es de Windows + numpy 2.5.3).
- `pip install -e ".[dev]"` limpio, `pip-licenses`, `docker compose build` (sin cambios de dependencias).
- El manifest incluye `python_version`: su contenido cambia entre versiones de Python aunque el CSV sea idéntico.
