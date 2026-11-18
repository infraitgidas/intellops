# SPEC — ISS-C-03: Suite E2E en CI y carga con k6

**Tipo**: Delta spec. **Cambio**: C.3 (GitHub #78). **Base**: `proposal.md`, `design.md`, S24–S27.
**Alcance**: CI (jobs nuevos), escenario k6 versionado y documentación. Sin cambios de producto.

## Capabilities

- **Nuevas**: `e2e-ci`, `load-test`.
- **Modificadas**: ninguna.

---

## 1. e2e-ci (Nueva)

### Requirement: LT-1 (el smoke corre en cada cambio, S24)

El workflow MUST tener un job `e2e` que levante la stack con `docker compose --profile smoke up -d
--build` y corra `python3 scripts/smoke.py` con los intervalos de los workers en 5 s, MUST depender
de `lint` y MUST NOT declarar `continue-on-error`: un flujo roto frena el PR.

#### Scenario: regresión del flujo real

- GIVEN un cambio que rompe la migración, el empaquetado de un worker o la cola de ingesta (los
  tests con ASGI no lo ven)
- WHEN corre el job `e2e`
- THEN el job falla con la etapa del smoke en el log

### Requirement: LT-2 (el escenario de carga es código versionado, S25)

`load/ingest.js` MUST ser un escenario k6 versionado que en `setup()` haga login del admin, cree
una aplicación y obtenga su API key, y que en cada iteración envíe un lote de eventos a
`POST /telemetry/metrics`. MUST aceptar `BASE_URL`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`, `VUS` y
`DURATION` por entorno, con defaults explícitos.

#### Scenario: escenario sin credenciales previas

- GIVEN una stack recién levantada
- WHEN corre `make load`
- THEN el `setup()` obtiene la API key por sí solo y las iteraciones usan esa key

### Requirement: LT-3 (umbral de ingesta ≤ 500 ms, S26)

El escenario MUST declarar `thresholds` con `http_req_duration{expected_response:true}` `p(95) ≤
500` para la ingesta, `http_req_failed ≤ 1 %` y un `checks` al 100 % (que el 202 traiga `accepted >
0`). La carga estándar MUST ser explícita: 10 VUs durante 1 min, lotes de 10 eventos (~100
eventos/s). k6 MUST salir ≠ 0 si un umbral no se cumple.

#### Scenario: umbral incumplido

- GIVEN la API con latencia artificial por encima de 500 ms en el p95
- WHEN corre `make load`
- THEN k6 sale ≠ 0 nombrando el umbral violado

### Requirement: LT-4 (reporte y límites del número, S27)

`make load` MUST exportar el resumen a `reports/k6-summary.json` (ignorado por git) y
`docs/operations/load-test.md` MUST documentar la carga estándar, los umbrales, cómo leer el
summary y qué NO prueba el número (una sola máquina con el stack completo, sin red real ni DB
dedicada). El job `load` del CI MUST correr sólo por `workflow_dispatch` y subir el summary como
artefacto.

#### Scenario: leer el resultado

- GIVEN un `k6-summary.json` de una corrida
- WHEN se sigue el runbook
- THEN se identifican p95, tasa de error, checks y si los umbrales pasaron
