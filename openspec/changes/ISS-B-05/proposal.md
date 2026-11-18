# Proposal: ISS-B-05 — SPA React: latencias RUM y heatmap UX

**Cambio**: B.5 (#69). **Base**: `MVP1` (origin/develop 057d46b + #92 B.3 + #91 ISS-S3-06 + B.14 + B.10 + B.9).
**Depende de**: B.3 (contrato de lectura de métricas, `/metrics/*`), B.13 (sonda `AVAILABILITY`).
**Lo consumen**: C.1 (flujo E2E), C.5 (release: `docker compose up` sin el frontend, que es build estático).

## Intent

La v1 necesita dos vistas sobre los datos que ya existen: latencias RUM y un heatmap de UX. Hoy
`src/frontend/` son cuatro `.gitkeep` y el visor que se usó en las demos no está versionado
(`docs/business/brief-v1.md:55`). El backend de lectura está completo (B.3/B.13): `GET
/metrics/query` (AVG por bucket + `session_count`), `GET /metrics/list` (catálogo) y `GET
/metrics/probes` (corridas de la sonda). No hace falta backend nuevo.

Decisión D1 (23/10/2026): el panel de predicciones sale de la v1 y se difiere a M3 con B.6; las
vistas son exactamente dos.

## Scope

### In Scope (RFC 2119)

- MUST: SPA React + TypeScript + Vite con las dos vistas (ADR-0009), build estático a `dist/`.
- MUST: vista de latencias contra `GET /metrics/query` + `GET /metrics/list`, con selector de
  métrica y de ventana, y la tabla de corridas de la sonda (`GET /metrics/probes`).
- MUST: heatmap temporal: filas = tipos de métrica, columnas = buckets de tiempo, color = `value`
  normalizado por fila, tooltip/leyenda con `value` y `session_count`.
- MUST: la API key se ingresa en la UI (el operador la pega), se guarda en `sessionStorage` y
  nunca se versiona ni se hornea en el bundle; 401/403 la descarta y muestra el error.
- MUST: estados de carga y de error con reintento en cada vista, y layout responsive (una columna
  por debajo de 720 px).
- MUST: `npm ci` reproducible con `package-lock.json` versionado y Node fijado por `engines`.
- MUST: bundle total de `dist/` < 1 MB (gate en script `npm run check-size`).
- MUST: tests de componentes (Vitest + Testing Library) y smoke E2E (Playwright sobre el build).
- MUST: job de CI `frontend` bloqueante con lint + tests + build + tamaño.

### Out of Scope

- Backend nuevo o cambios de contrato: si el heatmap necesitara una dimensión que la API no
  expone (`page_url`, `metadata`), NO se agrega en B.5.
- Autenticación JWT para `/metrics/*`: hoy esos paths son `apiKey` y el JWT no está cableado
  (`require_role` se usa sólo en `/users`, `/applications`, `/alerts/config`); habilitarlo es un
  cambio de backend fuera de alcance.
- Panel de predicciones (M3, B.6), D3.js y gráficos interactivos avanzados.
- Servir la SPA desde el compose: es un build estático (ADR-0010), se sirve aparte.

## Capabilities

- **Nuevas**: `rum-dashboard` (vistas de latencias y heatmap), `frontend-build` (build estático y
  gate de tamaño).
- **Modificadas**: ninguna. `ci.yml` gana un job `frontend`.

## Approach

1. **Paquete autocontenido** en `src/frontend/` (package.json, tsconfig, vite.config, eslint):
   `src/{App,main}.tsx`, `views/`, `components/`, `hooks/`, `services/`, `styles/`, `e2e/`.
2. **Acceso a datos**: un `services/api.ts` con las tres llamadas tipadas, un `hooks/useApi.ts`
   que resuelve `loading | error | data` y reintento, y la key como `sessionStorage`.
3. **Vistas**: `LatencyView` (selector de métrica + ventana + serie SVG + tabla de sondas) y
   `HeatmapView` (grilla SVG + leyenda + tabla accesible alternativa).
4. **CI**: job `frontend` con `setup-node`, `npm ci`, `npm run lint`, `npm test`, `npm run build`,
   `npm run check-size`; sin `continue-on-error`.

## Affected Areas

| Área | Impacto | Descripción |
|------|---------|-------------|
| `src/frontend/**` | Nuevo | SPA completa, configs, tests y e2e |
| `.github/workflows/ci.yml` | Modificado | Job `frontend` bloqueante |
| `CONTRIBUTING.md` | Modificado | Cómo correr lint/tests/build del frontend |
| `Makefile` | Modificado | `fe-install`, `fe-test`, `fe-build`, `fe-e2e` |
| `openspec/changes/ISS-B-05/**`, `CHANGELOG.md`, `odd/tasks/mvp1.md` | Docs | Spec, decisión y evidencia |

## Recursos

Dependencias de runtime: `react`, `react-dom` (sin librería de gráficos: la grilla y la serie son
SVG propio). Dev: `vite`, `typescript`, `vitest`, `@testing-library/{react,user-event,dom}`,
`jsdom`, `eslint`, `@playwright/test`. Sin backend nuevo y sin cambios en `requirements/`.

## Rollback

Revertir los commits deja `src/frontend/` como estaba (placeholders) y el job `frontend` fuera del
CI; el backend no se toca, así que no hay migración ni contrato que revertir.
