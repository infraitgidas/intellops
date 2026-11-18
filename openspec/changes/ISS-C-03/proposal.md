# Proposal: ISS-C-03 — Suite E2E en CI y carga con k6

**Cambio**: C.3 (#78). **Base**: `MVP1` (C.1 smoke + B.14/B.10/B.5).
**Depende de**: C.1 (smoke reproducible, `make smoke`). **Lo consume**: C.5 (release).

## Intent

C.1 dejó el flujo completo verificable con un comando, pero **nadie lo corre en cada cambio**: la
suite de CI no levanta la stack, así que una rotura del camino real (migración, empaquetado,
colas, ciclos de los workers) sólo se ve a mano. Y no hay ninguna medición de performance: la v1
promete "ingesta ≤ 500 ms bajo carga estándar" sin escenario, sin umbral versionado y sin reporte.

## Scope

### In Scope (RFC 2119)

- MUST: job de CI que corre el smoke E2E de C.1 sobre la stack real (build + `up` + smoke), sin
  `continue-on-error` (S24).
- MUST: escenario k6 versionado en `load/` con `setup()` propio (login admin → aplicación → API
  key), umbral de `p(95) ≤ 500 ms` en la ingesta y `http_req_failed < 1 %` (S25, S26).
- MUST: `make load` reproducible (k6 en contenedor `grafana/k6`, en la red del compose) y
  `--summary-export` a `reports/k6-summary.json` (S27).
- MUST: documentar la carga estándar (VUs, duración, tamaño de lote), los umbrales y cómo leer el
  reporte, más qué NO prueba (capacidad de producción, red real, DB dedicada).

### Out of Scope

- Tuning de performance o cambios en la ingesta: si el umbral no se cumple, se reporta con números.
- Pruebas de estrés/soak de horas y comparación entre máquinas.
- Correr k6 en cada PR: el job de carga es manual (`workflow_dispatch`) y el bloqueante es el
  smoke; el escenario queda versionado para correrlo cuando se toque ingesta o infraestructura.

## Capabilities

- **Nuevas**: `e2e-ci`, `load-test`.
- **Modificadas**: ninguna de producto.

## Approach

1. **CI**: job `e2e` (`needs: lint`) que exporta los intervalos cortos y la base del stub, corre
   `docker compose --profile smoke up -d --build` + `python3 scripts/smoke.py`, y publica el log.
   Job `load` sólo en `workflow_dispatch` que corre el escenario k6 y sube el summary como
   artefacto.
2. **k6**: `load/ingest.js` con `options.thresholds`, `setup()` que crea la aplicación y la key
   contra la API, y `teardown()` con el resumen; variables `BASE_URL`, `ADMIN_EMAIL`,
   `ADMIN_PASSWORD`, `VUS`, `DURATION`.
3. **Makefile**: `make load` (k6 en contenedor sobre `intellops-net`, summary a `reports/`) y
   `make e2e-ci` = lo mismo que el job.
4. **Docs**: `docs/operations/load-test.md` con la carga estándar, umbrales, lectura del summary y
   límites del número.

## Affected Areas

| Área | Impacto | Descripción |
|------|---------|-------------|
| `load/ingest.js` | Nuevo | Escenario k6 con thresholds y setup |
| `.github/workflows/ci.yml` | Modificado | Jobs `e2e` (bloqueante) y `load` (manual) |
| `Makefile` | Modificado | `load`, `e2e-ci` |
| `docs/operations/load-test.md` | Nuevo | Carga estándar, umbrales y lectura |
| `tests/test_ci_gates.py` | Modificado | Pin de los jobs nuevos |
| `CHANGELOG.md`, `odd/tasks/mvp1.md` | Docs | Trazabilidad |

## Recursos

k6 no se instala en el repo: se corre la imagen oficial `grafana/k6` (pinneada por tag) en la red
del compose. Sin dependencias nuevas de Python ni Node.

## Rollback

Revertir los commits saca los jobs y el escenario; la stack y el producto no cambian.
