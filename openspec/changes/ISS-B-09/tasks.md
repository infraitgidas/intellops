# Tasks: ISS-B-09 — Quality gates bloqueantes en CI

## Review Workload Forecast

Changed lines (estimado): ≈ 380 de código y tests (`.github/workflows/ci.yml` ≈ 45,
`tests/test_ci_gates.py` ≈ 260 nuevo, árbol `src/`+`tests/` ≈ 30, `Makefile` 1) más ≈ 90 de
`CONTRIBUTING.md` y ≈ 320 de los documentos del cambio (este directorio). Delivery strategy:
work-unit commits por preocupación (árbol → workflow + Makefile → pin → documentación), cada uno
revisable solo.

Decision needed before apply: **No**. El umbral (70 %), el score mínimo (9.0) y las herramientas
ya estaban fijados; la única decisión de diseño fue no agregar supresiones de pylint
(`design.md`, D3), con el árbol pasando el gate sin excepciones.

Chained PRs recommended: **No** en cuanto a PRs (MVP1 es local, S33), pero conviene revisar por
slice: el pin test es lo único con lógica propia.

400-line budget risk: **Low** para el código; el pin test concentra la lectura.

Dependencias: ISS-S3-06 (entorno reproducible). Lo consumen B.5, C.1, C.3 y C.5.

## Fase 0 — Documentos del cambio

- [x] 0.1 `proposal.md`, `spec.md` (QG-1..QG-6), `design.md` (D1..D5) y este `tasks.md`.

## Fase 1 — Árbol que pasa el gate

- [x] 1.1 `metrics.py`: el catálogo `GET /metrics/list` usa `_application`; W0613 queda en 0 sin
      `--disable` (QG-2, D3).
- [x] 1.2 Imports `src.ml.*` → `ml.*` en `src/ml/` y en los tests, y en el loader del dataset
      (`ml/data/generate_labeled_dataset.py`): una sola identidad de `MetricBatchInput` (D4).
- [x] 1.3 Verificación del gate: `pylint src/ --fail-under=9.0 --fail-on=W,E` sale 0 con 0
      mensajes W/E en el entorno del lock.

## Fase 2 — Workflow y entorno local

- [x] 2.1 `--cov-fail-under=70` en el step de la suite; comentarios de S11 y nombres de los steps
      de contrato (QG-1, QG-3).
- [x] 2.2 `--fail-on=W,E` en el step de pylint, sin `--disable`, y comentario con el criterio
      (QG-2).
- [x] 2.3 `make lint` con el mismo comando bloqueante que el CI (QG-5).

## Fase 3 — Documentación y pin

- [x] 3.1 `CONTRIBUTING.md`: tabla de gates bloqueantes, disparador/umbral de cada uno,
      reproducción local del fallo y calibración de pylint (QG-6).
- [x] 3.2 `tests/test_ci_gates.py`: pin de S11 (umbral explícito e igual a `fail_under`), S12
      (`--fail-on=W,E`, sin `--disable`, paridad de `make lint`, sin categorías desactivadas), S13
      (job, `needs` de `docker`) y QG-4 (sin `continue-on-error`), más la documentación (S14).

## Fase 4 — Cierre

- [x] 4.1 Evidencia negativa de S11/S12/S13 en el entorno fijado (cobertura 35 %, un warning,
      spec sin `security`) y suite completa en verde.
- [x] 4.2 `CHANGELOG.md` y registro de T3 en `odd/tasks/mvp1.md` con la evidencia.
