# Tasks: ISS-B-01 — Agente RUM de navegador (TTFB, FCP y errores JS)

## Review Workload Forecast

Estimated changed lines: ~900 (fuente ~450, tests ~300, docs/demo ~150). Delivery strategy: work-units en `feat/ISS-B-01`, single PR a develop.

## Fase 1 — Toolchain y scaffold

- [x] 1.1 `src/agent/package.json` con esbuild como única devDependency; build IIFE minificado a `dist/rum.js`.
- [x] 1.2 Script de chequeo de bundle: `gzip -c dist/rum.js` ≤ 30720 bytes; build en verde.

## Fase 2 — Captura

- [x] 2.1 Sesión: `session_id` UUID v4 en `sessionStorage`, rotación 30 min/24 h, fallback sin contexto seguro.
- [x] 2.2 TTFB (`responseStart - requestStart`) y FCP (`first-contentful-paint`); un `RumEvent` por page view; FCP ausente no se envía como 0; `timestamp` del envelope = `timeOrigin`.
- [x] 2.3 Muestreo determinista por sesión (`hash(session_id) < rate * 2^32`), default 1.0, reporte en `metadata.sample_rate`.
- [x] 2.4 Excepciones: `onerror` + `unhandledrejection`, `error_type` canónico, truncado 2000/20000, dedup por huella 60 s, tope 20/sesión.

## Fase 3 — Transporte y privacidad

- [x] 3.1 Cola acotada 500 con descarte de antiguos; flush por cantidad (20/5), intervalo (10 s/5 s) y ciclo de vida (`visibilitychange` hidden, `pagehide`); split por 400 eventos/32 KiB.
- [x] 3.2 Transporte: `fetch` keepalive + `X-API-Key`, sin `sendBeacon`; reintentos 1/2/4 s ±20 % ante 503/5xx/red; circuito abierto ante 401/403; `rejected[]` = descarte permanente.
- [x] 3.3 Privacidad: URL saneada (`{id}`, sin query/fragmento), redacción PII en message/stack, `user_agent` ≤ 256, DNT/GPC, opt-out `intellops-optout`, flag de consentimiento.

## Fase 4 — Tests, demo y verificación

- [x] 4.1 Tests `node --test`: TTFB, FCP, error, reintento (AC-12), muestreo, privacidad, batching.
- [x] 4.2 Demo HTML en `src/agent/demo/` contra la ingesta del entorno de testing.
- [x] 4.3 Verificación E2E: page view real → `RumEvent` con TTFB/FCP en la ingesta; error provocado → `JsExceptionEvent`; bundle ≤ 30 KB medido.
- [x] 4.4 `verify-report.md` con evidencia; `CHANGELOG.md`.
