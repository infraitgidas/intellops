# Tasks: ISS-B-05 — SPA React: latencias RUM y heatmap UX

## Review Workload Forecast

Changed lines (estimado): ≈ 1 700, de las cuales ≈ 700 son código de la SPA (servicios, hooks,
componentes, dos vistas), ≈ 450 tests (Vitest + Playwright + stub de API), ≈ 130 configuración
(package.json, tsconfig, vite, eslint, playwright, `.nvmrc`) y el resto CI, Makefile,
`CONTRIBUTING.md`, `CHANGELOG.md` y estos documentos. Delivery strategy: work-unit commits por
preocupación (scaffold + tooling → cliente HTTP y gate de key → vista de latencias → heatmap →
E2E + CI → documentación), cada uno revisable solo.

Decision needed before apply: **No**. Las tres decisiones de producto quedan tomadas y
justificadas en `design.md`: D2 (key que pega el operador en `sessionStorage`, sin backend nuevo),
D3 (heatmap = tiempo × métrica, la única lectura que el contrato sostiene) y D1 (Vite/TS sin D3).
Si el cliente pide autenticación por usuario, eso es backend nuevo y sale de B.5.

Chained PRs recommended: **No** (MVP1 es local, S33), pero conviene revisar por los cinco slices.

400-line budget risk: **Medium**: el medio millar de líneas de tests de componentes concentra la
lectura; el resto es scaffold y vistas pequeñas.

Dependencias: B.3 (contrato `/metrics/*`), B.13 (sonda). Lo consumen C.1 (E2E) y C.5 (release).

## Fase 0 — Documentos del cambio

- [x] 0.1 `proposal.md`, `spec.md` (QS-1..QS-6, QF-1), `design.md` (D1..D7) y este `tasks.md`.

## Fase 1 — Scaffold y tooling

- [ ] 1.1 `src/frontend/`: `package.json` (runtime `react`/`react-dom`; dev Vite/TS/Vitest/RTL/
  jsdom/eslint/Playwright), `package-lock.json`, `tsconfig.json`, `vite.config.ts`,
  `eslint.config.js`, `.nvmrc`, `index.html`, borrar los `.gitkeep`.
- [ ] 1.2 `scripts/check-size.mjs`: gate de 1 MB sobre `dist/` (raw + gzip informado).
- [ ] 1.3 `npm run build` sin API y `npm run check-size` verdes.

## Fase 2 — Acceso a datos y gate de key

- [ ] 2.1 `services/types.ts` + `services/api.ts`: espejo tipado del contrato y las tres llamadas
  con `X-API-Key`; errores 401/403/5xx tipados.
- [ ] 2.2 `hooks/useSessionKey.ts` (`sessionStorage`, borrado en 401/403) y `hooks/useApi.ts`
  (unión `loading|error|success` + `reload`).
- [ ] 2.3 `components/KeyGate.tsx` + tests (401 limpia y vuelve al gate).

## Fase 3 — Vista de latencias

- [ ] 3.1 `views/LatencyView.tsx`: selector de métrica y de ventana (tabla de presets, D4), serie
  SVG por bucket, tabla de sondas (`/metrics/probes`), estados de carga/error/vacío.
- [ ] 3.2 Tests de la vista (carga, error + reintento, datos, vacío) y de `SeriesChart`.

## Fase 4 — Heatmap

- [ ] 4.1 `views/HeatmapView.tsx` + `components/HeatmapGrid.tsx`: una llamada sin `metric_type`,
  normalización por fila, celda vacía neutra, tooltip, leyenda y tabla alternativa accesible.
- [ ] 4.2 Tests (dos escalas, celda vacía, tabla accesible).

## Fase 5 — E2E, CI y documentación

- [ ] 5.1 `e2e/stub-api.mjs` + `e2e/dashboard.spec.ts` + `playwright.config.ts` (dos `webServer`,
  `PLAYWRIGHT_CHROMIUM_PATH` opcional); smoke verde en local.
- [ ] 5.2 `.github/workflows/ci.yml`: job `frontend` bloqueante (lint, test, build, size, e2e).
- [ ] 5.3 `Makefile` (`fe-install`, `fe-lint`, `fe-test`, `fe-build`, `fe-e2e`) y
  `CONTRIBUTING.md` (comandos y la deuda de autenticación).
- [ ] 5.4 `CHANGELOG.md` y registro de T4 en `odd/tasks/mvp1.md` con la evidencia.
