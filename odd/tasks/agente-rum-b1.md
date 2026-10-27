# B.1 — Agente RUM: TTFB, FCP y errores JS (ISS-B-01, issue #67)

Owner: Federico. Fase B (02/11–13/11), 16 h estimadas, prioridad CRÍTICA.
Contrato normativo: `docs/architecture/ContratoAgenteRUM.md` v0.1 (A.3). Rama: `feat/ISS-B-01`.

## Specs

Criterios de aceptación de la issue #67 (verbatim):

- **S1**: `src/agent/rum.js` (o estructura equivalente) implementado.
- **S2**: Captura TTFB, FCP y errores JS no manejados.
- **S3**: Batching, muestreo y transporte según A.3.
- **S4**: Bundle < 30 KB gzip.
- **S5**: Envío exitoso a `/telemetry/metrics` y `/telemetry/exceptions`.
- **S6**: Demo en página HTML y tests del agente.

Nota de la issue (verbatim): _"Fuente: `docs/business/issues-fases-abc.md`. Las decisiones D1–D13 son propuestas pendientes de acuerdo (`docs/business/brief-v1.md` §8.3–§8.4)."_

## Tasks

| ID | Tarea | Specs | Ruta | Commit |
|----|-------|-------|------|--------|
| T1 | OpenSpec change `ISS-B-01`: proposal.md + tasks.md (convención del repo) | S1–S6 | parent | — |
| T2 | Scaffold `src/agent/` + build/minify + chequeo gzip ≤ 30 KB en CI local | S1, S4 | parent | — |
| T3 | Captura TTFB/FCP: session_id (rotación 30 min/24 h), muestreo determinista por sesión, convención timestamp = timeOrigin | S2, S3 | parent | — |
| T4 | Captura de excepciones: `onerror` + `unhandledrejection`, error_type canónico, truncado 2000/20000, dedup 60 s, tope 20/sesión | S2, S3 | parent | — |
| T5 | Transporte: cola acotada 500, flush 20/10 s y 5/5 s, `pagehide`/`visibilitychange`, fetch keepalive + X-API-Key, reintentos 1/2/4 s ±20 % (503/5xx/red), circuito abierto 401/403, split por 400 eventos/32 KiB | S3, S5 | parent | — |
| T6 | Privacidad: sanitización URL (`{id}`, sin query/fragmento), redacción PII en message/stack, DNT/GPC, opt-out `intellops-optout`, flag de consentimiento | S3 | parent | — |
| T7 | Tests del agente: TTFB, FCP, error, reintento (AC-12), muestreo, privacidad | S6 | parent | — |
| T8 | Demo en página HTML que usa el agente contra la ingesta | S6 | parent | — |
| T9 | Verificación E2E contra ingesta real (entorno Docker de testing) + verify-report de OpenSpec | S5 | parent | — |

## Log

- **L1** (2026-10-27, Federico): "bien, arraquemos con mi proxima tarea" — refiere a B.1 (#67), identificada como su próxima tarea propia (owner Federico, critico, estado:listo) tras mergear lo pendiente del tablero.
- **L2** (2026-10-27): El contrato A.3 v0.1 figura "pendiente de revisión de Santiago (QA)"; no bloquea la implementación pero la revisión QA (checklist §12) corre en paralelo.
