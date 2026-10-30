# Proposal: ISS-B-01 — Agente RUM de navegador (TTFB, FCP y errores JS)

**Cambio**: ISS-B-01 / B.1 (#67). **Base**: develop (`5a9ce02`). **Depende de**: A.3 — Contrato del agente RUM v0.1 (`docs/architecture/ContratoAgenteRUM.md`) e ISS-S2-03 (#37, endpoints `/telemetry/*`).

## Intent

Criterio de #67: **implementar el agente RUM de navegador que captura TTFB, FCP y errores JS, agrupa en batches y los envía a la ingesta según el contrato A.3**. Hoy los endpoints `/telemetry/metrics` y `/telemetry/exceptions` existen pero no tienen productor real: `src/agent/` está vacío y la única telemetría disponible es la sonda sintética. El contrato v0.1 ya fija qué se envía, cómo se transporta y qué garantiza; esta tarea es su implementación.

## Scope

### In Scope

- `src/agent/`: agente de navegador en JavaScript, **sin dependencias de runtime ni polyfills**, distribuido como un único archivo minificado `dist/rum.js` (IIFE), ≤ 30 KB gzip (objetivo 20 KB).
- **Captura**: TTFB (`responseStart - requestStart` de `PerformanceNavigationTiming`), FCP (`PerformanceObserver`, `first-contentful-paint`); un `RumEvent` por page view, solo TTFB si FCP no ocurre (nunca un 0 inventado). Excepciones: `window.onerror` y `unhandledrejection`, con `error_type` del catálogo canónico, `message` ≤ 2000 y `stack_trace` ≤ 20000 truncados por el agente.
- **Sesión**: `session_id` UUID v4 opaco en `sessionStorage` (fallback manual sin contexto seguro), rotación tras 30 min de inactividad o 24 h de vida.
- **Muestreo**: determinista a nivel sesión, `hash(session_id) < rate * 2^32`, tasa por defecto 1.0, compartida por métricas y excepciones; reporte en `metrics[].metadata.sample_rate`.
- **Batching**: cola en memoria acotada a 500 eventos (descarta los más antiguos); flush por cantidad (20 métricas / 5 excepciones), por intervalo (10 s / 5 s) y por ciclo de vida (`visibilitychange` a `hidden` y `pagehide`); cap de 400 eventos y 32 KiB serializados por request (split en varios requests); descarte con contador de eventos individuales inválidos.
- **Transporte**: `fetch` con `keepalive: true`, `mode: "cors"`, `credentials: "omit"` y header `X-API-Key`; **nunca `sendBeacon`**. Reintentos: máximo 3 intentos con backoff 1 s/2 s/4 s ± 20 % ante 503 `queue_full`, otro 5xx, timeout o error de red; circuito abierto (agente detenido en la página) ante 401 `invalid_api_key` o 403 `app_inactive`; `rejected[]` del 202 se procesa como descarte permanente.
- **Privacidad**: URL saneada (sin query ni fragmento, segmentos numéricos/UUID → `{id}`, ≤ 2048); redacción de emails, tokens y parámetros de query en `message`/`stack_trace` antes de truncar; `user_agent` ≤ 256; DNT/GPC detienen la recolección; opt-out por clave `intellops-optout` en `localStorage`; flag de consentimiento en la configuración; sin persistencia de payloads.
- **Tests del agente** (runner `node --test`, sin framework): TTFB, FCP, error, reintento, muestreo y privacidad (AC-12).
- **Demo** en página HTML (`src/agent/demo/`) servida localmente y apuntando a la ingesta del entorno de testing.

### Out of Scope

- LCP, CLS, INP, XHR latency y rage clicks (B.7, diferible a v1.1).
- Cambios del lado del servidor con seguimiento propio: OD-03 (`sample_rate` en `JsExceptionEvent`), OD-04 (validación `^1\.0$` por evento), D-03, D-04.
- Persistencia local de payloads (prohibida por §9 del contrato).
- Integración del agente en el SPA `src/frontend/` (vacío; la demo cumple el criterio de #67).
- Idempotencia de reintentos por `batch_id` (OD-05, backlog con ADR).

## Approach

Un solo artefacto autocontenido: módulos internos (`config`, `session`, `capture`, `queue`, `transport`, `privacy`) compilados con **esbuild** (única dependencia de desarrollo) a un IIFE minificado. La verificación de bundle corre como script: `gzip -c dist/rum.js | wc -c` contra 30720 bytes. Los tests usan el runner nativo `node --test` con mocks explícitos de las APIs de navegador (`PerformanceObserver`, `sessionStorage`, `fetch`), sin jsdom ni frameworks: se mantiene la cadena de tooling mínima y reproducible, coherente con ISS-S2-05. La configuración pública es `IntellOpsRUM.init({ apiKey, endpoint, sampleRate?, consent? })`. La convención temporal del contrato: `timestamp` del envelope = `performance.timeOrigin` de la navegación; las métricas heredan ese instante.

## Affected Areas

| Área | Impacto | Descripción |
|------|--------|-------------|
| `src/agent/` | Nuevo | fuente, build, tests, demo y `dist/rum.js` del agente |
| `openspec/changes/ISS-B-01/` | Nuevo | proposal, tasks y verify-report |
| `CHANGELOG.md` | Modificado | registro del cambio |

Sin cambios en `src/api/`, contratos OpenAPI, CI ni runtime. El chequeo de bundle es script local de esta tarea; su incorporación al CI se evalúa con B.9 (quality gates).

## Risks

| Riesgo | Mitigación |
|--------|-----------|
| Fuga de PII en `message`/`stack_trace` o URL | Redacción y saneado antes de truncar (§9); tests de privacidad dedicados; DNT/GPC y opt-out cortan la recolección |
| `pagehide` sin `fetch` disponible pierde el buffer | Aceptado por contrato (§7): cola solo en memoria, semántica at-least-once (OD-05) |
| El contrato v0.1 sigue pendiente de revisión QA | El checklist §12 corre en paralelo; cualquier ajuste entra como corrección acotada de este cambio |
| Bundle crece sobre 30 KB | Sin dependencias de runtime; chequeo gzip en cada build |

## Rollback

Revertir el PR: todo el cambio es aditivo (`src/agent/`, OpenSpec, CHANGELOG); el servidor y la sonda sintética no se tocan.
