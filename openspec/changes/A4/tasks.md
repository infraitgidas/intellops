# Tasks: A.4 — Generador sintético y anomalías inyectadas etiquetadas

> Fuentes: `proposal.md`, `design.md`, `specs/synthetic-dataset/spec.md`.
> Modo: strict TDD (RED → GREEN → REFACTOR). Runner: `pytest -m unit` (sin Postgres).

## Review Workload Forecast

| Campo | Valor |
|---|---|
| Líneas cambiadas estimadas | ~1100 (≈ 450 de código, ≈ 300 de tests, el resto docs) |
| Estrategia de entrega | `single-pr` (una issue, un PR); 4 commits atómicos |
| Chained PRs recommended | No |
| 400-line budget risk | Medium (la mitad es documentación) |
| Decision needed before apply | No |

## Reglas transversales

- Conventional commits en español con sufijo `(A.4)`, sin co-author ni atribución IA. Paths explícitos al stagear.
- Python 3.11, numpy + stdlib. Sin `src.api`, DB ni HTTP.
- Vedados: `src/api`, `src/ml`, `generate_mock_dataset.py`, `rum_mock.json`, notebook EDA, `CHANGELOG.md`, `openapi.yaml`.
- Los datos generados no se commitean (`ml/data/synthetic/` en `.gitignore`).

## Commit 1 — `docs(openspec/changes/A4): ...`

- [ ] 1.1 `proposal.md`, `specs/synthetic-dataset/spec.md`, `design.md`, `tasks.md`.

## Commit 2 — `feat(ml): ... (A.4)`

- [ ] 2.1 RED/GREEN contrato y reproducibilidad (SYN-1, SYN-2): traza base, filas M4, export CSV.
- [ ] 2.2 RED/GREEN realismo (SYN-3): estacionalidad, sesgo, correlación, huecos.
- [ ] 2.3 RED/GREEN catálogo y agenda (SYN-4, SYN-5): 6 tipos × 3 severidades por split, sin solapes, sin cruzar el corte, contaminación.
- [ ] 2.4 RED/GREEN hard negatives y split (SYN-6, SYN-7).
- [ ] 2.5 RED/GREEN manifest y lector (SYN-8, SYN-9).
- [ ] 2.6 REFACTOR: constantes con nombre, funciones chicas; flake8 limpio también en `ml/data/`.

Verificación: `PYTHONPATH=. pytest tests/test_labeled_dataset.py -m unit`.

## Commit 3 — `docs(ml): ... (A.4)`

- [ ] 3.1 `ml/data/README.md`: propósito, regeneración, columnas, catálogo, bandas, hard negatives, split, rangos, sha256 esperado + versión de numpy, tiempo y tamaño de la corrida por defecto, limitaciones, consumo por B.6.
- [ ] 3.2 `.gitignore`: `ml/data/synthetic/`.

## Commit 4 — `docs(openspec/changes/A4): ...`

- [ ] 4.1 Verificación completa (flake8, pylint, unit, suite con cobertura) y corrida real por defecto.
- [ ] 4.2 `apply-progress.md` y `verify-report.md` (matriz SYN-* vs tests); tildar `tasks.md`.
