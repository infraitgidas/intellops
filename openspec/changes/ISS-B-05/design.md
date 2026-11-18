# Design: ISS-B-05 — SPA React: latencias RUM y heatmap UX

**Cambio**: B.5 (#69). **Base**: `proposal.md`, `spec.md` (QS-1..QS-6, QF-1).
**Alcance**: `src/frontend/` + job `frontend` del CI + documentación.

## Contexto del contrato (verificado en código, no inferido)

| Llamada | Params | Respuesta |
|---|---|---|
| `GET /metrics/query` | `start`, `end`, `bucket_seconds` ≥ 60, `metric_type` — todos opcionales; ventana ≤ 7 d, `start < end`, default 15 min/60 s | `[{application_id, metric_type_id, timestamp, value (AVG), session_count}]`, orden bucket asc |
| `GET /metrics/list` | — | `[{metric_type_id, name, description?}]` |
| `GET /metrics/probes` | `limit` 1..500 (default 50) | `[{timestamp, target, http_status, outcome, latency_ms, available}]` |

Los tres exigen `X-API-Key`; el tenant sale de la key (no hay `application_id` como parámetro).
CORS ya está abierto (`src/api/main.py:86-96`, `allow_origins=["*"]`, sin credenciales).

## Decisiones

### D1 — React 19 + TypeScript + Vite, sin librería de gráficos

ADR-0009 fija React + TS + Vite y menciona D3.js. D3 no se usa: la serie es un `<polyline>`/barras
SVG y el heatmap una grilla de `<rect>`, ambos con escalas lineales propias. Un heatmap
rectangular no necesita D3 y evitamos ~80 KB de dependencia. Queda documentado como desvío del
ADR: D3 se reconsidera cuando haya zoom/brush o escalas logarítmicas interactivas.

Las carpetas siguen el layout planificado (`docs/infrastructure/Estructura-de-Carpetas-V1.1.2.md`):
`src/{App,main}.tsx`, `views/`, `components/`, `hooks/`, `services/`, `styles/`. Los tests viven
junto al código (`*.test.tsx`) y el E2E en `src/frontend/e2e/`; el plan decía `tests/frontend/`,
se prefiere el paquete autocontenido para que `npm ci` + `npm test` no dependan del root del repo.

### D2 — Autenticación: API key que pega el operador (`sessionStorage`)

`/metrics/*` es `apiKey` y el JWT no está cableado a esos paths. Habilitar el JWT sería backend
nuevo (fuera de alcance), así que la v1 es una herramienta interna y la key la aporta el operador:

- Gate inicial: input `ilp_...` + "Conectar"; se guarda en `sessionStorage` (por pestaña, muere al
  cerrarla) y nunca en `localStorage`, cookies, URL, logs ni bundle.
- 401/403: se borra la key y se vuelve al gate con el mensaje de la API.
- Trade-off explícito: una key en el navegador es un secreto bearer; se acepta para una
  herramienta interna de operación y queda como deuda con dueño: un endpoint de lectura con
  `require_role` (JWT) reemplaza el gate. Se documenta en `CONTRIBUTING.md`.

### D3 — Qué es el "heatmap UX" con estos datos

La API pública no expone `page_url` ni `metadata`, así que no hay grilla página × posición. El
heatmap es temporal y multi-métrica: **filas = `metric_type`, columnas = buckets, color = AVG**.
Es la lectura que el dato sostiene: cuándo y en qué métrica se degrada la experiencia.

- Una sola llamada a `/metrics/query` sin `metric_type` (todas las métricas en un request).
- Normalización **por fila** (mín/máx de esa fila): TTFB en ms y JS_EXCEPTION_RATE en fracción no
  comparten escala. Celda sin dato → color neutro (`--cell-empty`), nunca interpolada.
- Accesibilidad: color no es el único canal. Tooltip por celda con `name`, hora del bucket,
  `value` y `session_count`, más una tabla "Ver como tabla" con los mismos datos.

### D4 — Un solo cliente HTTP con estados explícitos

`services/api.ts` expone `getMetrics`, `getMetricTypes`, `getProbes` (tipos TS espejo del
contrato). `hooks/useApi.ts` devuelve una unión discriminada
`{status: 'idle'|'loading'|'error'|'success', data?, error?, reload()}`: las vistas no manejan
`try/catch` sueltos ni renderizan datos viejos como si fueran nuevos (al cambiar de ventana el
estado vuelve a `loading`).

Ventanas y bucket (siempre ≥ 60 s y ventana ≤ 7 d):

| Preset | Ventana | `bucket_seconds` |
|---|---|---|
| 15 min | 900 s | 60 |
| 1 h | 3 600 s | 60 |
| 6 h | 21 600 s | 300 |
| 24 h | 86 400 s | 900 |

### D5 — Tests: Vitest + RTL para componentes, Playwright para el smoke

- Componentes: Vitest + `@testing-library/react` + `jsdom`, `fetch` stubbeado con
  `vi.stubGlobal('fetch', ...)` (sin MSW: una dependencia menos y el stub es explícito por test).
  Casos por vista: carga, error + reintento, éxito, vacío; gate de key (401 limpia y vuelve al
  gate); normalización del heatmap con dos escalas distintas; celda vacía neutra.
- E2E: Playwright con **dos** `webServer` — una API stub en `e2e/stub-api.mjs` (Node `http`, sin
  dependencias) y `vite preview` sobre un build con `VITE_API_BASE_URL` apuntando al stub, para
  que el smoke corra contra el artefacto real y no contra el dev server.
- Navegador: en CI `npx playwright install --with-deps chromium`. En local, si la revisión del
  navegador instalado no coincide, se usa `PLAYWRIGHT_CHROMIUM_PATH` (por ejemplo
  `/usr/bin/chromium`) como `executablePath`; el config lo respeta.

### D6 — Gate de tamaño (S17)

`scripts/check-size.mjs`: suma los bytes de todos los archivos de `dist/` (raw) y el gzip de los
`.js`/`.css`; falla con exit 1 si el raw supera 1 MB (1 000 000 B, el criterio de la issue) e
informa ambos números. Sin `dist/` → error explícito (el gate no puede pasar sin build).

### D7 — Job `frontend` del CI

`setup-node` con `node-version: 22` (Vite 8 pide ≥ 20.19/22.12; `engines: ">=22"` en
`package.json`), `npm ci`, `npm run lint` (`eslint . --max-warnings=0`), `npm test`
(`vitest run`), `npm run build`, `npm run check-size` y `npx playwright install --with-deps
chromium && npm run test:e2e`. Sin `continue-on-error`; `needs: lint` para no gastar minutos si el
lint de Python falla.

## Layout y comandos

```
src/frontend/
  package.json  package-lock.json  tsconfig.json  vite.config.ts  eslint.config.js
  playwright.config.ts  index.html  .nvmrc
  scripts/check-size.mjs
  src/{main.tsx,App.tsx,styles.css}
  src/services/{api.ts,api.test.ts,types.ts}
  src/hooks/{useApi.ts,useApi.test.ts,useSessionKey.ts}
  src/components/{KeyGate.tsx,SeriesChart.tsx,HeatmapGrid.tsx,ProbeTable.tsx,AsyncPanel.tsx,...}
  src/views/{LatencyView.tsx,HeatmapView.tsx,(+ .test.tsx)}
  e2e/{stub-api.mjs,dashboard.spec.ts}
```

| Comando | Qué hace |
|---|---|
| `npm ci` | instala desde el lock |
| `npm run lint` | eslint, 0 warnings |
| `npm test` | vitest run (componentes) |
| `npm run build` | `tsc --noEmit && vite build` → `dist/` |
| `npm run check-size` | gate de 1 MB sobre `dist/` |
| `npm run test:e2e` | build con stub + playwright |

## Riesgos

| Riesgo | Mitigación |
|--------|------------|
| Key en el navegador | `sessionStorage`, nunca bundle/URL/log, 401 limpia; deuda documentada (JWT) |
| Heatmap sin dimensión de página | Se documenta qué mide (tiempo × métrica) en la UI y en el spec |
| Divergencia de versión de navegador en E2E | `PLAYWRIGHT_CHROMIUM_PATH` como escape; CI instala el suyo |
| Bundle creciendo con cada vista | Gate en CI con presupuesto explícito |
| `MetricTypeInfo.description` nullable y OpenAPI dice `string` | El cliente tipa `description?: string \| null`; no se toca el contrato (fuera de alcance) |
