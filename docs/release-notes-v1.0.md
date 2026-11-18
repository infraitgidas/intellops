# Release v1.0 — notas para el equipo

**Tag**: `v1.0.0` (local en la rama `MVP1`). **Fecha**: 18/11/2026.
**Alcance**: MVP v1 completo sobre `MVP1` = `origin/develop` (0f7531b, con #91 y #92) + B.14, B.10,
B.9, B.5, C.1 y C.3.

## Qué entra en la v1

| Pieza | Estado | Dónde se ve |
|---|---|---|
| Agente RUM de navegador (B.1) | completo | `src/agent/` (4.3 KB gzip), demo en `src/agent/demo/index.html` |
| Ingesta asíncrona `/telemetry/*` (S2-03) | completo | `POST /telemetry/metrics`, `/telemetry/exceptions` |
| Lectura de métricas y sesiones (B.3, S3-03) | completo | `/metrics/query`, `/metrics/list`, `/metrics/probes`, `/sessions` |
| Sonda de disponibilidad (B.13) | completo | `python -m probe`, filas `AVAILABILITY` |
| Motor determinístico de umbrales (B.14) | completo | `intellops-ai-engine`, `POST/GET /alerts/config` |
| Despacho por Telegram y mail (B.10) | completo | `intellops-comms`, `GET /alerts` |
| Gates de calidad bloqueantes (B.9) | completo | `tests/test_ci_gates.py`, `.github/workflows/ci.yml` |
| SPA: latencias RUM y heatmap UX (B.5) | completo | `src/frontend/`, `npm run build` → `dist/` |
| Flujo E2E + smoke reproducible (C.1) | completo | `make smoke`, `docs/operations/smoke-e2e.md` |
| E2E en CI + carga k6 (C.3) | completo | job `e2e`, `make load`, `docs/operations/load-test.md` |

## Números verificados (18/11/2026)

- Suite Python: **906 passed**, 1 skipped, 1 xfailed, 1 xpassed; cobertura **93.26 %** (gate 70 %).
- Lint: `flake8` 0 hallazgos; `pylint 9.91/10` con **0 warnings y 0 errores** (gate: cualquier W/E
  falla).
- Frontend: **50 tests** de componentes, **5** de smoke E2E; bundle **243 kB raw / 75 kB gzip**
  (tope 1 MB).
- Smoke E2E del flujo completo: **10/10 etapas en ~8 s** (stub de Telegram incluido).
- Carga estándar (10 VUs, 1 min): **p95 10.39 ms**, 0 % de fallos, 600 iteraciones, umbrales de la
  v1 (`p95 ≤ 500 ms`) en verde.

## Requisitos para levantarlo

- Docker con compose v2 y ≥ 4 GB de RAM libre (cuatro servicios: `core`, `db`, `ai-engine`,
  `comms`).
- Node ≥ 22 sólo si se sirve la SPA (`src/frontend/`); no es parte del compose (ADR-0010).
- Python 3.11+ en el host sólo para el smoke y la carga.

Ver `docs/operations/deploy-v1.0.md` para el despliegue paso a paso y el rollback.

## Limitaciones conocidas (no son bloqueantes, sí contexto)

1. **El envío real de notificaciones necesita credenciales** (`INTELLOPS_COMMS_TELEGRAM_BOT_TOKEN`
   + `_CHAT_ID`, SMTP). Sin ellas la alerta queda `Pending` y el worker loguea una vez; el smoke
   verifica el camino completo contra un stub, no contra Telegram real (S6 sigue abierto hasta que
   las credenciales estén).
2. **El heatmap es tiempo × métrica**, no página × posición: la API pública no expone `page_url`
   ni `metadata`. Agregarlo es backend nuevo (post-v1).
3. **La SPA guarda la API key en `sessionStorage`** (la pega el operador): `/metrics/*` es `apiKey`
   y el JWT no está cableado a esos paths. Endurecerlo es backend nuevo.
4. **El número de k6 es de una sola máquina** con el stack completo, sin red real ni DB dedicada:
   sirve como regresión, no como capacidad de producción.
5. **B.7 (RUM completo: XHR y rage clicks) no entra**: la detección de anomalías ML es M3. La v1
   detecta por umbrales (B.14).
6. **`MVP1` no se pushea ni se mergea a `develop`** mientras el equipo no lo decida (S33): el tag
   `v1.0.0` es local y el flujo "funciona en develop" se verificó como *mergeable* (`git merge-tree`
   sin conflictos contra `origin/develop`).

## Fuera de la v1 (M3 / backlog)

- Detección con Isolation Forest y panel de predicciones (B.6/B.11), RUM completo (B.7), sitios
  piloto (C.2/C.4), informes de PPS y autoría humana (C.6/C.7).

## Cómo demostrarlo

`docs/operations/demo-mvp1.md`: guion de punta a punta (agente → SPA → regla → alerta →
notificación) con lo que se muestra en pantalla y lo que se verifica en cada paso.
