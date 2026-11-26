# Design: ISS-C-03 — Suite E2E en CI y carga con k6

**Cambio**: C.3 (#78). **Base**: `proposal.md`, `spec.md` (LT-1..LT-4).

## Decisiones

### D1 — El job E2E del CI corre el smoke de C.1 tal cual

Sin un segundo guion paralelo: el job `e2e` reutiliza `scripts/smoke.py` y el perfil `smoke` del
compose, con los intervalos de los workers en 5 s (los mismos que `make smoke`). Duplicar el flujo
en YAML sería otro camino que se desactualiza; el script ya falla nombrando la etapa.

Coste: ~3-4 min por corrida (build de tres imágenes + smoke). Se acepta: es el único gate que ve la
stack real. `needs: lint` evita gastarlo cuando el código ni siquiera lintea.

### D2 — k6 por imagen oficial, en la red del compose

`docker run --rm -i --network intellops_intellops-net -v "$PWD/load:/scripts:ro" grafana/k6:0.57.0
run /scripts/ingest.js`. Ventajas: nada que instalar en el repo, el contenedor alcanza
`http://intellops-core:8000` por DNS del compose (mismo criterio que el stub de C.1: no depender de
que el host acepte tráfico de contenedores) y el tag fija la versión. La red se resuelve con
`docker compose ps --format json` en el target, sin hardcodear el nombre del proyecto.

### D3 — La carga estándar es explícita y corta

`VUS=10`, `DURATION=1m`, lote de 10 eventos por iteración (~100 eventos/s con el `sleep(1)` del
escenario). Es una carga de **regresión**, no una prueba de capacidad: mismo host, misma DB, sin
red real. El número (p95 ≤ 500 ms) es el criterio de la issue y se mide con el stack completo
compitiendo por CPU, que es el escenario realista de la demo y del piloto.

### D4 — `setup()` provisiona, `teardown()` no limpia

k6 crea la aplicación y la key en `setup()` (login admin → `POST /applications` → `POST
/applications/{id}/api-key`). No borra nada en `teardown()`: la API no tiene DELETE de
aplicaciones y la app `k6-load-<ts>` es inocua; borrarla requeriría SQL directo. Se documenta que
las apps de carga se acumulan y cómo limpiarlas a mano (`docker compose down -v` o SQL).

### D5 — Umbral de checks propio

Además de `http_req_duration` y `http_req_failed`, un `check` verifica que el 202 traiga `accepted
> 0`: un `202` con todo rechazado mediría latencia de una ingesta que no ingiere.

### D6 — El job de carga es manual

`workflow_dispatch` con entradas `vus`/`duration`. En cada PR duplicaría el coste del job `e2e` sin
agregar señal (la latencia en un runner compartido no es comparable entre corridas); el escenario
versionado + el runbook cubren S25–S27, y el umbral se corre cuando se toca ingesta o
infraestructura, que es cuando aporta.

## Riesgos

| Riesgo | Mitigación |
|--------|------------|
| k6 en un runner de CI mide latencias distintas | El job es manual y el runbook dice que el número es de esa máquina |
| El script de k6 duplica el payload de la ingesta (drift con el contrato) | El test de contrato y el smoke cubren el shape; el `check` de `accepted > 0` rompe si el payload deja de validar |
| Apps de carga acumuladas en la DB de dev | Documentado; `down -v` limpia |
| El job E2E agrega minutos al PR | `needs: lint`; timeout 20 min; se corrió primero en local con `make e2e-ci` |
