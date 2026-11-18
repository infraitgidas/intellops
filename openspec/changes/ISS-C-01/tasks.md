# Tasks: ISS-C-01 — Integración de punta a punta

## Review Workload Forecast

Changed lines (estimado): ≈ 900, de las cuales ≈ 420 son el smoke y el stub (`scripts/smoke.py`,
`scripts/telegram_stub.py`, stdlib), ≈ 60 el override del base URL con su test, ≈ 30 compose y
Makefile, y ≈ 350 documentación de operación (runbook + demo). Delivery strategy: work-unit
commits por preocupación (override + test → compose → stub → smoke + target → docs), cada uno
revisable solo.

Decision needed before apply: **No**. D2 (base URL configurable con default actual) es el único
cambio de producción y es aditivo; el resto es herramienta de verificación y documentación.

Chained PRs recommended: **No** (MVP1 es local, S33).

400-line budget risk: **Medium**: el smoke concentra la lectura; el runbook es el complemento
necesario para que sea reproducible.

Dependencias: B.1, B.3, B.10, B.13, B.14 y B.5. Lo consume C.3 (carga) y C.5 (release).

## Fase 0 — Documentos del cambio

- [x] 0.1 `proposal.md`, `spec.md` (E2E-1..E2E-6), `design.md` (D1..D7) y este `tasks.md`.

## Fase 1 — Notificación verificable

- [ ] 1.1 `CommsSettings.telegram_api_base` (default `TELEGRAM_API_BASE`) y `TelegramProvider`
  usándolo en `{base}/bot{token}/sendMessage` (E2E-1).
- [ ] 1.2 Test del override: con la variable configurada la URL apunta al stub; sin ella, al default
  de siempre.

## Fase 2 — Compose y stub

- [ ] 2.1 `docker-compose.yml`: `extra_hosts` en `intellops-comms`, `INTELLOPS_COMMS_TELEGRAM_API_BASE`
  con default vacío e `INTELLOPS_RULES_INTERVAL_SECONDS` en `intellops-ai-engine`.
- [ ] 2.2 `scripts/telegram_stub.py`: `POST /bot<token>/sendMessage` → 200, acumula y expone
  `GET /_messages`; bindea `0.0.0.0`, puerto configurable, sin dependencias (E2E-3).

## Fase 3 — Smoke

- [ ] 3.1 `scripts/smoke.py`: login → app + API key → ingesta → lectura → regla → alerta →
  notificación en el stub, con polling por etapa, ids y tiempos en el resumen, y fallo accionable
  (E2E-2, D4).
- [ ] 3.2 `make smoke` (intervalos cortos + `docker compose up -d --build` + script; `SMOKE_NO_BUILD=1`
  para no reconstruir).
- [ ] 3.3 Corrida real completa en verde sobre la stack y registro de la evidencia (ids, tiempos).

## Fase 4 — Documentación

- [ ] 4.1 `docs/operations/smoke-e2e.md`: prerequisitos, comando, pasos, tiempos, interpretación de
  fallos, limpieza y el chequeo de mergeabilidad contra `origin/develop` (S21).
- [ ] 4.2 `docs/operations/demo-mvp1.md`: guion de la demo de punta a punta (S23).
- [ ] 4.3 `CONTRIBUTING.md` con `make smoke` en la lista de comandos.

## Fase 5 — Cierre

- [ ] 5.1 `CHANGELOG.md` y registro de T5 en `odd/tasks/mvp1.md` con la evidencia.
