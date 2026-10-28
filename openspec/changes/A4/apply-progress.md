# Apply progress: A.4

Estrategia: `single-pr`, 4 commits atómicos. Modo: strict TDD (runner `pytest -m unit`). Rama `feat/A4` desde `origin/develop`.

## Commits (`git log --oneline origin/develop..HEAD`)

| Commit | Mensaje | Work unit |
|---|---|---|
| `3d1261e` | docs(openspec/changes/A4): propuesta, spec, diseño y tareas del generador sintético etiquetado (A.4) | 1 |
| `f1410e3` | feat(ml): generador sintético reproducible con anomalías etiquetadas, hard negatives y split temporal (A.4) | 2 |
| `443691c` | docs(ml): documenta el dataset sintético etiquetado y excluye los datos generados (A.4) | 3 |
| (este commit) | docs(openspec/changes/A4): verify-report, apply-progress y tareas tildadas (A.4) | 4 |

## Estado de tareas

| Tarea | Estado |
|---|---|
| 1.1 | Hecha |
| 2.1 a 2.6 | Hechas |
| 3.1, 3.2 | Hechas |
| 4.1, 4.2 | Hechas |

## TDD Cycle Evidence

| Tarea | RED (falla vista) | GREEN | Triangulación / notas | REFACTOR |
|---|---|---|---|---|
| 2.1 contrato y reproducibilidad | `FileNotFoundError` del módulo (8 tests) | 8 passed | seed igual vs distinta; bucket 60 vs 300; error < 60 s | — |
| 2.2 realismo | correlación de latencias `-0.01` (sin factor común) | 11 passed tras agregar factor latente AR compartido | el estadístico pasó a diferencias de bloques de 15 buckets: 0.02 sin factor vs 0.38 con factor (medido). Estacionalidad y sesgo pasaron al primer intento: ya los traía la traza base de 2.1 | — |
| 2.3 catálogo y agenda | 5 fallas (sin eventos) | 19 passed | bandas, gap, corte, pico, contaminación con tamaño por defecto | — |
| 2.4 hard negatives y split | 2 fallas (sin hard negatives); `bucket_seconds=300` con 7 días pasó a ser inviable | 23 passed | test de 300 s llevado a 14 días (duraciones en buckets) + test nuevo de ventana inviable con `RuntimeError`. El test de split temporal pasó al primer intento (ya implementado en 2.1) | — |
| 2.5 manifest y lector | 3 fallas (`KeyError csv_sha256`, sin `load_labeled_dataset`) | 29 passed | CSV alterado ⇒ `ValueError` sha256. Columnas exactas, CLI y desacople pasaron al primer intento (ya cubiertos) | — |
| 2.6 refactor | — | 29 passed tras cada paso | — | `_validate_params`, `_app_rows`, `_place_anomaly` extraídos (mismo orden de sorteos); flake8 0 en `ml/data` y `tests` |

## Desviaciones del diseño acordado

1. **Severidad de `dropout`** por fracción de sesiones perdidas (0.40-0.60 / 0.60-0.80 / 0.80-0.95), no en sigmas: el desvío local de `session_count` está dominado por Poisson y por el ruido de tráfico, y con sigmas el `high` (6-9 σ) solo era alcanzable en el pico de checkout. Documentado en design §3 y README.
2. `--apps` limitado a 1-3 (perfiles fijos).
3. Duraciones y gaps en buckets (calibrados para 60 s); ventanas inviables fallan con `RuntimeError` explícito.
4. Dentro de una anomalía se fuerza `session_count ≥ 1` para que la fila exista.
5. Los hard negatives son eventos de app: se etiquetan en las 5 métricas.
6. El manifest incluye `python_version` además de `numpy_version` (informativo).

## Archivos

| Archivo | Acción |
|---|---|
| `ml/data/generate_labeled_dataset.py` | Nuevo (generador, export, lector) |
| `tests/test_labeled_dataset.py` | Nuevo (29 tests `unit`) |
| `ml/data/README.md` | Nuevo |
| `.gitignore` | `ml/data/synthetic/` |
| `openspec/changes/A4/*` | Nuevos |
