# SPEC — ISS-B-05: SPA React — latencias RUM y heatmap UX

**Tipo**: Delta spec. **Cambio**: B.5 (GitHub #69). **Base**: `proposal.md`, `design.md`, S15–S19.
**Alcance**: `src/frontend/` (SPA nueva), job `frontend` del CI y documentación. Sin backend nuevo,
sin cambios de contrato y sin tocar el esquema.

## Capabilities

- **Nuevas**: `rum-dashboard`, `frontend-build`.
- **Modificadas**: ninguna.

Entradas de datos (contrato existente, verificado en código):

- `GET /metrics/query` → `[{application_id, metric_type_id, timestamp, value, session_count}]`,
  `value` = AVG del bucket, buckets anclados a `start`; params opcionales `start`, `end`,
  `bucket_seconds` (≥ 60), `metric_type`; ventana ≤ 7 días, `start < end`, default 15 min/60 s.
- `GET /metrics/list` → `[{metric_type_id, name, description?}]`.
- `GET /metrics/probes?limit=1..500` → `[{timestamp, target, http_status, outcome, latency_ms,
  available}]`, más nuevo primero.
- Los tres exigen `X-API-Key: ilp_...`; 401 `invalid_api_key`, 403 `app_inactive`.

---

## 1. rum-dashboard (Nueva)

### Requirement: QS-1 (gate de API key)

La SPA MUST pedir la API key al operador antes de consultar la API, MUST guardarla sólo en
`sessionStorage` y MUST NOT incluirla en el bundle, en el código versionado ni en la URL. Un 401 o
un 403 MUST descartar la key guardada y volver al gate con el mensaje del error.

#### Scenario: primer arranque

- GIVEN la SPA recién servida, sin key en `sessionStorage`
- WHEN abre
- THEN muestra el gate de key y no hace ninguna llamada a `/metrics/*`

#### Scenario: key inválida

- GIVEN una key guardada que la API rechaza con 401
- WHEN la vista consulta
- THEN la key se borra, se vuelve al gate y se muestra `invalid_api_key`

### Requirement: QS-2 (vista de latencias, S15)

La vista de latencias MUST consultar `GET /metrics/list` (catálogo) y `GET /metrics/query` con una
métrica seleccionable y una ventana seleccionable entre 15 min, 1 h, 6 h y 24 h, y MUST mostrar la
serie de `value` por bucket con su `session_count`. MUST mostrar además las últimas corridas de la
sonda (`GET /metrics/probes`, límite 50) con `available`, `http_status`, `latency_ms` y `outcome`.

#### Scenario: serie con datos

- GIVEN el catálogo con `TTFB` y 12 buckets
- WHEN la vista carga con la ventana de 1 h
- THEN pinta 12 puntos ordenados por `timestamp` y la tabla de sondas

#### Scenario: sin datos

- GIVEN una métrica sin filas en la ventana
- WHEN la vista carga
- THEN muestra el estado vacío ("sin datos en la ventana") y no un gráfico en blanco

### Requirement: QS-3 (heatmap temporal, S15)

El heatmap MUST mostrar una grilla de filas = `metric_type` del catálogo y columnas = buckets de
tiempo, con UNA sola llamada a `GET /metrics/query` sin filtro de métrica, color de celda derivado
de `value` normalizado por fila y MUST exponer `value` y `session_count` de cada celda en tooltip
y en una tabla alternativa accesible.

#### Scenario: normalización por fila

- GIVEN dos métricas con escalas distintas (TTFB ~ 200 ms, JS_EXCEPTION_RATE ~ 0,02)
- WHEN se pinta la grilla
- THEN cada fila usa su propio mínimo/máximo y el color no queda saturado por la escala ajena

#### Scenario: celda vacía

- GIVEN un bucket sin filas para una métrica
- WHEN se pinta la grilla
- THEN la celda queda neutra (sin color de valor) y no se interpola un valor inexistente

### Requirement: QS-4 (estados de carga, error y responsive, S18)

Cada vista MUST mostrar un estado de carga mientras espera, un estado de error legible con botón
de reintento ante fallo de red o 5xx, y MUST NOT renderizar datos parciales como si estuvieran
completos. El layout MUST pasar a una columna por debajo de 720 px, con la tabla de sondas y la
tabla del heatmap desplazables horizontalmente sin romper el ancho de la página.

#### Scenario: fallo de red

- GIVEN la API caída
- WHEN la vista consulta
- THEN muestra el mensaje de error y el botón "Reintentar"; al volver la API, el reintento carga

### Requirement: QS-5 (build estático reproducible, S16, S17)

`npm ci` MUST instalar desde `package-lock.json` versionado, `npm run build` MUST generar `dist/`
con `vite build` y `tsc --noEmit`, y el total de `dist/` MUST ser < 1 MB (gate `npm run
check-size`, que falla con exit ≠ 0 si lo supera e informa el peso raw y gzip). El build MUST NOT
requerir la API, ni red más allá de `npm ci`, ni variables de entorno.

#### Scenario: gate de tamaño

- GIVEN un cambio que infla el bundle por encima de 1 MB
- WHEN corre `npm run check-size`
- THEN sale ≠ 0 nombrando el tamaño total

#### Scenario: build sin backend

- GIVEN una máquina sin la API levantada
- WHEN corre `npm ci && npm run build`
- THEN `dist/index.html` existe y el build sale 0

### Requirement: QS-6 (tests de componentes y smoke E2E, S19)

Los componentes y hooks MUST tener tests con Vitest + Testing Library sobre `fetch` stubbeado
(carga, error, datos, gate de key, normalización del heatmap). El smoke E2E MUST correr con
Playwright sobre `vite preview` con una API stub y MUST verificar, en un navegador real, que el
gate de key aparece primero y que, con key válida, las dos vistas renderizan datos.

#### Scenario: smoke E2E

- GIVEN el build servido y una API stub con 3 buckets y 2 métricas
- WHEN el navegador entra, pega la key y navega a las dos vistas
- THEN ve la serie, la tabla de sondas y la grilla del heatmap

#### Scenario: regresión de datos vacíos

- GIVEN la API stub devolviendo `[]`
- WHEN se abre cada vista
- THEN se ve el estado vacío y no hay excepción en consola

---

## 2. frontend-build (Nueva)

### Requirement: QF-1 (job de CI bloqueante)

El workflow MUST tener un job `frontend` que corra `npm ci`, `npm run lint`, `npm test`, `npm run
build` y `npm run check-size` con Node fijado, y MUST NOT declarar `continue-on-error`.

#### Scenario: bundle inflado

- GIVEN un PR que supera el presupuesto de 1 MB
- WHEN corre el job `frontend`
- THEN el job queda rojo y no se puede mergear
