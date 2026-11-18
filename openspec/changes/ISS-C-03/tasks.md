# Tasks: ISS-C-03 — Suite E2E en CI y carga con k6

## Review Workload Forecast

Changed lines (estimado): ≈ 520, de las cuales ≈ 150 son el escenario k6, ≈ 90 CI, ≈ 40 Makefile,
≈ 30 el pin de los jobs, ≈ 200 documentación. Delivery strategy: work-unit commits por
preocupación (k6 + make → CI → docs y pin), cada uno revisable solo.

Decision needed before apply: **No**. La carga estándar (10 VUs, 1 min, lotes de 10) y el p95 ≤ 500
ms salen de la issue; el job de carga se deja manual y se justifica en `design.md` (D6).

Chained PRs recommended: **No** (MVP1 es local, S33).

400-line budget risk: **Low**.

Dependencias: C.1 (`make smoke`, perfil `smoke` del compose). Lo consume C.5.

## Fase 0 — Documentos del cambio

- [x] 0.1 `proposal.md`, `spec.md` (LT-1..LT-4), `design.md` (D1..D6) y este `tasks.md`.

## Fase 1 — Escenario k6

- [x] 1.1 `load/ingest.js`: `setup()` (login → app → key), iteración con lote de 10 eventos,
  `thresholds` (`p(95) ≤ 500` ms, error < 1 %, checks 100 %) y `sleep(1)`.
- [x] 1.2 `make load`: resolver la red del compose, correr `grafana/k6` pinneado y exportar
  `reports/k6-summary.json`.
- [x] 1.3 Corrida real con la stack arriba: umbrales cumplidos y summary versionado en el runbook.

## Fase 2 — CI

- [x] 2.1 Job `e2e` (bloqueante, `needs: lint`): `--profile smoke up -d --build` + smoke con
  intervalos de 5 s.
- [x] 2.2 Job `load` (`workflow_dispatch` con `vus`/`duration`) que corre `make load` y sube el
  summary como artefacto.
- [x] 2.3 `make e2e-ci` y pin en `tests/test_ci_gates.py` (jobs presentes, sin
  `continue-on-error`, k6 versionado).

## Fase 3 — Documentación y cierre

- [x] 3.1 `docs/operations/load-test.md`: carga estándar, umbrales, lectura del summary, límites y
  limpieza de apps de carga.
- [x] 3.2 `CONTRIBUTING.md` con `make load` / `make e2e-ci`.
- [x] 3.3 `CHANGELOG.md` y registro de T6 en `odd/tasks/mvp1.md`.
