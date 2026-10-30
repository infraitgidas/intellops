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

## Remediación (revisión independiente)

Mismo modo (strict TDD) y estrategia (`single-pr`). Tests del generador: 29 → 42 (2 reemplazados, 3 reescritos).

| Commit | Mensaje | Concern |
|---|---|---|
| `fd78755` | fix(ml): etiqueta solo filas existentes que la anomalía modificó de verdad (A.4) | W2 |
| `4500f3c` | fix(ml): escala duraciones y gap al tamaño del bucket y valida --days con mensaje claro (A.4) | W3 |
| `b9f8751` | fix(ml): garantiza 3 eventos por tipo y severidad en validation y amplía la ventana por defecto a 28 días (A.4) | W1 |
| `0430c0d` | fix(ml): hard negatives con hora sorteada, sin zona de exclusión y efecto visible en value (A.4) | W4 |
| `2794fab` | test(ml): endurece pico horario, cobertura con 3 seeds, lector fila a fila y splits sin eventos compartidos (A.4) | S3 |
| `c6d57e8` | docs(ml): advierte qué columnas no usar como features y actualiza números, sha256 y tiempos de la corrida por defecto (A.4) | S2 + números |
| (este commit) | docs(openspec/changes/A4): ... | artefactos |

### TDD Cycle Evidence (remediación)

| Tarea | RED (falla vista) | GREEN | Triangulación / notas | REFACTOR |
|---|---|---|---|---|
| 5.1 W2 | `test_labels_match_real_changes_against_clean_run`: filas que solo existían por la inyección (`session_count >= 1` forzado) | 30 passed | misma comprobación sobre la corrida por defecto (script): 0 filas extra, 0 filas mal etiquetadas | `_emitted()` compartido por inyección y export (mismo redondeo); línea larga de `_dropout` partida |
| 5.2 W3 | 900/3600/7000 s: `RuntimeError cannot place`; `days=1` sin `ValueError` con mínimo; CLI con traceback; `MIN_GAP_MINUTES` inexistente | 34 passed | 3 tamaños de bucket; barrido seeds 0-19 × apps 1-3 × 5 buckets: con 2 días falla, con 3 no (MIN_DAYS = 3 en este commit) | gap = `round(30·60/b)` (puede ser 0) en lugar de mínimo 1: con 7000 s el gap de 1 bucket hacía inviable 1 app |
| 5.3 W1 | `assert 1 >= 3` (eventos por celda en validation), en el fixture chico y en la corrida por defecto | 35 passed | 21 días: validation 2.43-3.15 % en seeds 0-9 (seed 5 > 3 %) → se eligió 28 días (1.80-2.29 %); MIN_DAYS re-medido = 8 (7 falla con 7000 s, 1 app) | SMALL pasa a 8 días |
| 5.4 W4 | hora fija (`{'22:00'}`), ninguna anomalía a < 30 min de un benigno, `KeyError value_sigmas` | 38 passed | z-score ingenuo: mantenimiento marcado 37 % (> `low` 28 %), surge 12 %, normal 6.5 %; MIN_DAYS = 8 sigue valiendo (barrido de 20 seeds) | `_benign_shape`, `_traffic_multiplier`; se eliminó el multiplicador de base por métrica |
| 5.5 S3 | — (tests de caracterización: pasaron al primer intento) | 42 passed | sensibilidad comprobada con una mutación temporal del lector (`is_anomaly` mal parseado): el test nuevo falla; mutación revertida | — |

### Desviaciones

1. `DEFAULT_DAYS = 28` (no 21): con 21 días la contaminación de validation llega a 3.15 % en una seed (fuera del 1-3 %). Costo: CSV de 51 MB y ≈ 3.5 s.
2. `MIN_DAYS = 8` es empírico (seeds 0-19), no una cota analítica; para combinaciones raras queda el `RuntimeError` con mensaje claro (código 2 en el CLI).
3. Gap entre anomalías en minutos sin mínimo de 1 bucket (con 7000 s es 0).
4. `NEIGHBORHOOD` (σ local) sigue en buckets: es una ventana estadística, no una duración.
5. Una ventana de anomalía puede tener filas sin etiquetar (sin cambio real, p. ej. tasa ya en 1); `events[].length` sigue siendo el largo de la ventana.
6. `GENERATOR_VERSION` sigue en `1.0.0` aunque la salida cambió (no pedido; ver verify-report).
