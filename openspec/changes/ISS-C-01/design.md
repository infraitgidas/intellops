# Design: ISS-C-01 — Integración de punta a punta

**Cambio**: C.1 (#76). **Base**: `proposal.md`, `spec.md` (E2E-1..E2E-6).

## Estado verificado antes del cambio

- La stack de `docker-compose.yml` levanta cuatro servicios; sólo `intellops-core` corre
  `alembic upgrade head` (`Dockerfile:32`) y siembra el admin (`0002_credentials.py:35-59`).
- `intellops-ai-engine` evalúa reglas cada `INTELLOPS_RULES_INTERVAL_SECONDS` (default 60) y
  `intellops-comms` despacha cada `INTELLOPS_COMMS_INTERVAL_SECONDS` (default 30). Ninguno tiene
  healthcheck: un smoke tiene que esperar ciclos, no servicios.
- Sin credenciales, el despacho deja la alerta en `Pending` y loguea una vez
  (`src/comms/entrypoint.py:157`): el tramo "notificación" nunca se había probado end-to-end.
- La URL de Telegram es una constante (`src/comms/providers.py:33`), así que no hay forma de
  apuntar el proveedor a un stub.
- No hay ningún script que recorra el flujo: `scripts/ci-tests.sh` corre pytest dentro del
  contenedor de test y `src/agent/scripts/e2e.mjs` sólo verifica los dos `202` de ingesta.
- El admin del seed falta en algunas bases viejas (`odd/tasks/b13-sonda-http.md:121-124`), así que
  el smoke debe fallar en el login con un mensaje accionable, no con un timeout.

## Decisiones

### D1 — El smoke es un script stdlib y la orquestación vive en `make smoke`

`scripts/smoke.py` usa sólo `urllib` y `argparse`: corre en el host con Python 3.11+, sin instalar
nada y sin depender del lock de test. La orquestación (exportar intervalos cortos, `docker compose
up -d --build`, después el smoke) vive en el target `make smoke`, porque el script no debe decidir
por el operador si se reconstruyen imágenes ni si se baja la stack. El script sí levanta y baja su
propio stub de Telegram (subproceso), que es parte del contrato del test.

Variables del smoke: `SMOKE_API_URL` (default `http://localhost:8000`), `SMOKE_STUB_PORT` (8099),
`SMOKE_ADMIN_EMAIL`/`SMOKE_ADMIN_PASSWORD` (defaults del seed), `SMOKE_TIMEOUT_*` por etapa.

### D2 — `INTELLOPS_COMMS_TELEGRAM_API_BASE` (aditivo)

`CommsSettings.telegram_api_base` con default `TELEGRAM_API_BASE` (la constante actual) y
`TelegramProvider` recibiéndolo por constructor. Es el único cambio de producción y no altera el
comportamiento por defecto: sin la variable, la URL es exactamente la de hoy. Se testea con un
`httpx.MockTransport`/stub de proveedor que verifica la URL construida.

### D3 — El contenedor llega al stub por `host.docker.internal`

`docker-compose.yml` suma `extra_hosts: ["host.docker.internal:host-gateway"]` al servicio
`intellops-comms` (funciona en Linux con Docker ≥ 20.10, en macOS/Windows ya existe) y
`INTELLOPS_COMMS_TELEGRAM_API_BASE=${INTELLOPS_COMMS_TELEGRAM_API_BASE:-}` a su lista de variables,
como todas las demás: default vacío, sin cambiar nada si no se usa. El stub bindea `0.0.0.0`.

### D4 — Esperas por ciclo, no por reloj fijo

El smoke hace polling con timeout por etapa y sin `sleep` a ciegas:

| Etapa | Condición | Timeout |
|---|---|---|
| `/health` | 200 | 120 s (build + migración) |
| Ingesta visible | `/metrics/query` devuelve el bucket de la sesión enviada | 60 s |
| Alerta creada | `GET /alerts` trae una alerta de la regla en cualquier estado | 60 s |
| Notificación | stub tiene el mensaje y la alerta está `sent` | 120 s |

Con `make smoke` los intervalos bajan a 5 s para que las etapas de reglas y despacho sean seguras;
con los defaults de producción (60/30 s) los timeouts siguen siendo suficientes pero el smoke
tarda más. Cada fallo imprime la etapa, la request, el status y el cuerpo (truncado).

### D5 — Qué se verifica del mensaje

`_telegram_text` (`src/comms/providers.py:43`) define el formato. El smoke asserta los campos que
el formateador realmente incluye (severidad, mensaje, aplicación y valor/umbral cuando estén), no
una plantilla inventada: si el texto no incluye el umbral, el test del smoke lo dice en vez de
relajar la aserción en silencio.

### D6 — La demo usa lo que ya existe, sin código nuevo

Página del agente (`src/agent/demo/index.html`, ya acepta endpoint + API key), la SPA
(`npm run preview`) y `GET /alerts`. La notificación se muestra en el stub local o en Telegram si
el operador tiene credenciales. El guion de `docs/operations/demo-mvp1.md` indica, paso a paso, qué
se genera, dónde se ve y qué se verifica, con los tiempos de espera explícitos.

### D7 — S21 sin `develop`

MVP1 no se pushea (S33), así que "flujo funcionando en `develop`" se cumple como *mergeable*:
`git merge-tree --write-tree origin/develop HEAD` sin conflictos, más suite Python y frontend en
verde y el smoke en verde sobre esta rama. Se documenta en el runbook.

## Riesgos

| Riesgo | Mitigación |
|--------|------------|
| El smoke tarda por los ciclos (60/30 s) | `make smoke` baja los intervalos a 5 s; timeouts holgados |
| `host.docker.internal` no resuelve en Docker viejo | El runbook documenta la alternativa: correr el stub en un contenedor o exportar `INTELLOPS_COMMS_TELEGRAM_API_BASE` con la IP del host |
| El seed admin no existe (base vieja) | El smoke falla en el login diciendo cómo recrear el admin/volumen |
| El stub queda escuchando si el smoke se corta | `try/finally` + `atexit`; el puerto es configurable |
| Reconstruir imágenes en cada `make smoke` | `smoke` no reconstruye si el operador pasa `SMOKE_NO_BUILD=1` |
