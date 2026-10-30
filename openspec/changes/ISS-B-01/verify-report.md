# Verify Report: ISS-B-01 — Agente RUM de navegador

**Fecha**: 2026-10-27 · **Rama**: `feat/ISS-B-01` · **Contrato**: `docs/architecture/ContratoAgenteRUM.md` v0.1

## Entorno

| Elemento | Valor |
|---|---|
| Node | v26.2.0 (runner nativo `node --test`, sin frameworks) |
| Build | esbuild 0.28.2 → IIFE minificado `dist/rum.js` |
| Ingesta E2E | `docker compose` local: `intellops-core` en `http://localhost:8000`, Postgres `intellops-db` |
| App de prueba | `RUM E2E (ISS-B-01)` creada en la DB de desarrollo; API key efímera fuera del repo |

## Criterios de aceptación de la issue #67

| # | Criterio | Estado | Evidencia |
|---|---|---|---|
| S1 | `src/agent/rum.js` (o estructura equivalente) implementado | Cumplido | `src/agent/src/` con 7 módulos; bundle `dist/rum.js` generado por `npm run build` |
| S2 | Captura TTFB, FCP y errores JS no manejados | Cumplido | `test/capture.test.js` (TTFB, FCP, `onerror`, `unhandledrejection`) |
| S3 | Batching, muestreo y transporte según A.3 | Cumplido | `test/queue.test.js`, `test/session.test.js`, `test/transport.test.js` |
| S4 | Bundle < 30 KB gzip | Cumplido | `npm run build` → **4299 bytes gzip** (tope 30720, objetivo 20480) |
| S5 | Envío exitoso a `/telemetry/metrics` y `/telemetry/exceptions` | Cumplido | `scripts/e2e.mjs`: 202 `accepted=1 rejected=0` en ambos endpoints; filas verificadas en `rum_metric` y `js_exception` |
| S6 | Demo en página HTML y tests del agente | Cumplido | `demo/index.html`; **78 tests, 78 en verde** |

## Criterios del contrato (AC-01…AC-12)

| AC | Verificación |
|---|---|
| AC-02 | Page view con TTFB y FCP en el mismo `RumEvent`; sin FCP se envía solo TTFB (tests `page view`) |
| AC-03 | `responseStart - requestStart` y `entry.startTime`, ambos en ms (test `TTFB`, `FCP`) |
| AC-04 | `error_type` del catálogo, `message` ≤ 2000 y `stack_trace` ≤ 20000 (test `normalización`) |
| AC-05 | `schema_version: "1.0"` en envelope y en cada evento (test E2E del envelope) |
| AC-06 | `fetch` con `keepalive: true` y `X-API-Key`; el entorno no expone `sendBeacon` (test `transporte`) |
| AC-08 | Muestreo determinista, batching y reintentos 1 s/2 s ±20 % (tests `muestreo`, `reintentos`) |
| AC-09 | Payload sin query strings ni credenciales; DNT, GPC y opt-out detienen la recolección (tests `privacidad`) |
| AC-10 | Bundle 4299 bytes gzip ≤ 30720 (script de build) |
| AC-11 | Sin persistencia de payloads: solo `session_id` y opt-out en `sessionStorage`/`localStorage` |
| AC-12 | Demo HTML + tests que cubren TTFB, FCP, error y reintento |

AC-01 (aprobación de QA del contrato) y AC-07 (preflight CORS desde origen de
terceros) dependen de Santiago y del despliegue: quedan fuera de esta
implementación.

## Evidencia E2E (2026-10-27)

```
agente inicializado — sesión 2cd40fe1-2e62-496b-8102-bda21818d649
OK /telemetry/metrics: 202 accepted=1 rejected=0 batch=3bb965d5-...
OK /telemetry/exceptions: 202 accepted=1 rejected=0 batch=66d65200-...
counters: {"sent":2,"dropped":0,"rejected":0,"failed":0}
```

Persistencia verificada en la DB de desarrollo:

| Tabla | Observación |
|---|---|
| `rum_metric` | `TTFB = 200`, `page_url = https://shop.example.com/product/{id}` (sin query), `metadata = {user_agent, sample_rate: 1, agent_version: "1.0.0"}` |
| `js_exception` | `error_type = TypeError`, `message = "e2e: render falló para [REDACTED]"`, `stack_trace` de 208 caracteres |
| `user_session` | `session_id` del agente, `app_id` derivado de la API key, `user_agent` poblado |

## Hallazgos corregidos durante la verificación

1. **`user_agent` no llegaba a `user_session`**: el agente lo enviaba en
   `metrics[].metadata` y el ingest lo lee del metadata **del evento**
   (`queue.py:253-263`). Corregido: viaja en `metadata` del `RumEvent`; verificado
   con `SELECT user_agent FROM user_session`.
2. **Ambigüedad del contrato en el backoff (§7)**: el texto pide "máximo 3
   intentos" y una secuencia 1 s/2 s/4 s, que no pueden darse juntas. Se
   implementan 3 intentos con 1 s y 2 s, alineado con el checklist de QA (§12).
   Queda para la revisión de QA definir si se agrega un cuarto intento.

## Pendientes y seguimientos

| Ítem | Estado |
|---|---|
| Job de CI que ejecute build + tests del agente y el chequeo de bundle | Fuera de alcance declarado; se evalúa con B.9 (quality gates en CI) |
| Revisión del contrato A.3 por QA (Santiago) | Pendiente, según §12 del contrato |
| OD-03 y OD-04 (seguimiento de código del servidor) | Fuera de alcance de B.1 |

## Reproducción

```bash
cd src/agent
npm install
npm test          # 78 tests
npm run build     # bundle + presupuesto gzip
INTELLOPS_API_KEY=ilp_... INTELLOPS_ENDPOINT=http://localhost:8000 node scripts/e2e.mjs
```
