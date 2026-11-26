# Proposal: ISS-C-01 — Integración de punta a punta (flujo completo + smoke + demo)

**Cambio**: C.1 (#76). **Base**: `MVP1` (B.1 agente, B.3 lectura, B.10 despacho, B.13 sonda, B.14 reglas, B.5 SPA).
**Depende de**: todas las de la fase B. **Lo consumen**: C.3 (carga), C.5 (release).

## Intent

Cada pieza de la v1 funciona y está probada por separado (903 tests de Python, 50 + 5 del
frontend), pero **nadie probó el flujo completo sobre la stack real**: `docker compose up`, agente
→ ingesta → PostgreSQL → motor de reglas → alerta → despacho → notificación. El brief lo dice
explícito: "No existe: no hay suite E2E, escenario k6 ni agente instalado"
(`docs/business/brief-v1.md:58`), y C.1 pide "Smoke test documentado y reproducible"
(`:155`).

Además, hoy la notificación **no se puede verificar sin credenciales reales**: el proveedor de
Telegram tiene la URL de la API fija en una constante (`src/comms/providers.py:33`), así que un
smoke reproducible sólo podría llegar hasta `Pending`, que es justo el tramo que quedó sin probar
en B.10 (S6 bloqueado por credenciales).

## Scope

### In Scope (RFC 2119)

- MUST: un smoke reproducible, en un solo comando, que recorra el flujo completo contra la stack
  de `docker-compose.yml`: login admin → alta de aplicación + API key → ingesta de métricas →
  lectura (`/metrics/query`, `/sessions`) → regla de umbral → alerta → despacho → notificación.
- MUST: la notificación se verifica contra un **stub local** de la API de Telegram, sin exigir
  credenciales reales: `INTELLOPS_COMMS_TELEGRAM_API_BASE` configurable (default
  `https://api.telegram.org`, o sea el comportamiento actual).
- MUST: `make smoke` y la documentación de operación con el flujo, los prerequisitos, qué esperar
  y qué mirar cuando falla.
- MUST: una demo de punta a punta documentada (agente en una página + panel + alerta en Telegram)
  que el equipo pueda repetir.
- SHOULD: el smoke deja un resumen legible (paso, latencia, ids) y falla con el paso exacto.

### Out of Scope

- Carga y umbrales de performance: es C.3 (T6).
- Release, tag y guía de despliegue: es C.5 (T7).
- Credenciales reales de Telegram/SMTP: el stub cubre el camino; el envío real sigue necesitando
  las credenciales que aporta el usuario (S35 del plan).
- Merge a `develop`: MVP1 es local (S33); "funcionando" se verifica en esta rama.

## Capabilities

- **Nuevas**: `e2e-smoke` (script + stub + target), `operations-runbook` (docs de operación y demo).
- **Modificadas**: `notification-channels` (base URL de Telegram configurable, aditiva).

## Approach

1. **Stub de Telegram** (`scripts/telegram_stub.py`, stdlib): recibe `POST /bot<token>/sendMessage`,
   guarda los mensajes en memoria y los expone en `GET /_messages` para que el smoke los verifique.
2. **Override aditivo** en `intellops-comms`: `telegram_api_base` en `CommsSettings` (default la
   constante actual) pasado a `TelegramProvider`.
3. **Compose**: `extra_hosts: host.docker.internal:host-gateway` en comms + intervalos
   (`INTELLOPS_RULES_INTERVAL_SECONDS`, `INTELLOPS_COMMS_INTERVAL_SECONDS`) y el base URL del stub
   por entorno, con defaults que no cambian el comportamiento de producción.
4. **Smoke** (`scripts/smoke.py`, stdlib, sin dependencias): levanta el stub, espera `/health`,
   recorre el flujo, espera los ciclos (reglas y despacho) con polling acotado y verifica el
   mensaje en el stub; `make smoke`.
5. **Docs**: `docs/operations/smoke-e2e.md` (runbook) y `docs/operations/demo-mvp1.md` (demo).

## Affected Areas

| Área | Impacto | Descripción |
|------|---------|-------------|
| `scripts/smoke.py`, `scripts/telegram_stub.py` | Nuevo | Smoke y stub, sólo stdlib |
| `src/comms/{config,providers}.py` | Modificado | `telegram_api_base` configurable (aditivo) |
| `docker-compose.yml` | Modificado | `extra_hosts` y defaults por entorno |
| `Makefile` | Modificado | `make smoke` |
| `tests/test_comms_dispatch.py` | Modificado | Test del override del base URL |
| `docs/operations/**`, `CHANGELOG.md`, `odd/tasks/mvp1.md` | Docs | Runbook, demo y trazabilidad |

## Recursos

Sin dependencias nuevas: el smoke usa `urllib` de la stdlib y el stub `http.server`. Docker ya es
requisito del proyecto. El smoke baja y construye las tres imágenes la primera vez.

## Rollback

Revertir los commits deja el compose y el despacho como estaban (el base URL vuelve a la constante)
y borra el smoke y el runbook; no hay migración ni contrato que revertir.
