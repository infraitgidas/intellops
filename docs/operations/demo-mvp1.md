# Demo de punta a punta de la v1 (ISS-C-01, S23)

Guion reproducible para mostrar el flujo completo de IntellOps en ~10 minutos:
un sitio de ejemplo con el agente RUM cargado → ingesta → panel con latencias y
heatmap → regla de umbral → alerta → notificación.

Todo usa lo que ya existe: la página del agente (`src/agent/demo/index.html`), la
SPA (`src/frontend`, `npm run build && npm run preview`) y la API de la stack de
`docker-compose.yml`.
No hace falta escribir código para la demo ni tener credenciales reales de
Telegram: la notificación se muestra en el stub local (o en Telegram, si tenés un
bot).

Verificación automatizada del mismo flujo: `make smoke`
([`smoke-e2e.md`](./smoke-e2e.md)). Este documento es el guion para mostrarlo a
personas.

---

## 0. Preparación (una vez, antes de la demo)

```bash
# 1. Stack (build incluido la primera vez). El compose exige JWT_SECRET sin
#    default: `make setup` crea `.env` desde `.env.example` si falta.
make setup && make up

# 2. Agente RUM: genera src/agent/dist/rum.js (está en .gitignore)
cd src/agent && npm ci && npm run build && cd ../..

# 3. SPA: build de producción servido por `vite preview` (http://localhost:4173)
cd src/frontend && npm ci && npm run build && npm run preview
```

Para que las etapas de reglas y despacho no tarden un minuto delante del
público, bajá los intervalos (opcional, pero recomendado):

```bash
INTELLOPS_RULES_INTERVAL_SECONDS=5 INTELLOPS_COMMS_INTERVAL_SECONDS=5 \
  docker compose up -d
```

| Qué | Dónde | Esperado |
|---|---|---|
| API | `http://localhost:8000` | `curl -s localhost:8000/health` responde `{"status":"ok"...}` |
| SPA | `http://localhost:4173` | pide la API key (gate) |

`vite preview` escucha en el loopback IPv6 (`[::1]`): entrá por `localhost`, no
por `127.0.0.1`.
| Agente | `http://localhost:8080/demo/` | se abre en el paso 3 |
| Notificación | stub en `:8099` o tu bot real | ver paso 6 |

---

## 1. Alta de la aplicación y su API key (1 min)

Sólo un Admin puede crear aplicaciones y emitir keys. El Admin del seed es
`admin@intellops.local` / `admin-dev-password` (sólo dev/CI).

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@intellops.local","password":"admin-dev-password"}' \
  | python3 -c 'import json,sys; print(json.load(sys.stdin)["access_token"])')

APP_ID=$(curl -s -X POST http://localhost:8000/applications \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"name":"demo-mvp1"}' \
  | python3 -c 'import json,sys; print(json.load(sys.stdin)["app_id"])')

API_KEY=$(curl -s -X POST http://localhost:8000/applications/$APP_ID/api-key \
  -H "Authorization: Bearer $TOKEN" \
  | python3 -c 'import json,sys; print(json.load(sys.stdin)["api_key"])')

echo "app_id=$APP_ID"; echo "api_key=$API_KEY"
```

**Qué se ve:** un `app_id` (UUID) y una `api_key` que empieza con `ilp_`.
**Qué se verifica:** la key se muestra **una sola vez** (show-once): no se
vuelve a poder leer, sólo rotar. Guardala para los pasos 2 y 3.

---

## 2. Telemetría desde la página del agente (2 min)

```bash
cd src/agent && python3 -m http.server 8080    # servir la demo del agente
# abrir http://localhost:8080/demo/
```

En la página:

1. **Endpoint de ingesta**: `http://localhost:8000`.
2. **API key**: la del paso 1.
3. **Tasa de muestreo**: `1`.
4. Tildá **“Doy consentimiento de recolección”**.
5. **Iniciar agente**: el panel de estado muestra el `session_id` y los eventos
   enviados.
6. **Forzar flush** para que el lote salga ya (el agente agrupa y espera).
7. El bloque grande de la página dispara el FCP; podés usar
   **“Lanzar TypeError no manejado”** y **“Error con PII”** para mostrar la
   redacción en el servidor.

**Qué se ve en pantalla:** el estado del agente con la sesión iniciada y el
contador de eventos enviados.
**Qué se verifica:** la ingesta responde `202`; desde la consola del navegador se
ve el `POST /telemetry/metrics`. Si el consentimiento está apagado, el agente no
envía nada (a propósito).

---

## 3. El dato en el panel: latencias y heatmap (2 min)

En la SPA (`http://localhost:4173`), pegá la API key del paso 1.

| Paso | Qué se ve | Qué se verifica |
|---|---|---|
| Gate de API key | Campo para pegar la key | Sin key no se monta ninguna vista (no hay llamadas a `/metrics/*`) |
| Pestaña **Latencias** | Selector de métrica (TTFB seleccionada por defecto) y de ventana; serie de valores medios por bucket y la tabla de corridas de la sonda | La serie de TTFB trae el bucket de la sesión que acabás de generar (ventana 15 min) |
| Cambiar a **Heatmap UX** | Grilla de métricas × tiempo, normalizada por fila | La sesión enviada entra en la columna del minuto actual |
| Ventana `1h` / `24h` | La serie se recalcula | El selector cambia `start`/`end` de `/metrics/query` (nada se cachea) |

Si la serie sale vacía: pasaron más de 15 minutos desde el paso 2 (elegí una
ventana mayor) o el worker de ingesta todavía no persistió (mirá
`docker compose logs intellops-core`).

---

## 4. La regla de umbral (1 min)

Reportá el TTFB p95 por encima de un umbral que el dato supere (la demo del
paso 2 suele dar cientos de ms; usá un umbral bajo, p. ej. 50 ms, para que
dispare seguro):

```bash
curl -s -X POST http://localhost:8000/alerts/config \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"application_id":"'$APP_ID'","metric_type_id":1,"comparison":"gt",
       "threshold":50,"window_minutes":5,"min_samples":3,
       "cooldown_minutes":5,"severity":"critical"}'
```

`metric_type_id: 1` es TTFB (confirmalo con `GET /metrics/list`).

**Qué se ve:** la regla creada (`rule_id`, `threshold`, `severity`).
**Qué se verifica:** `201` la primera vez y `200` si repetís la misma regla
(idempotente por app + métrica + comparación + umbral).

---

## 5. La alerta (30 s con intervalos en 5 s, hasta 60 s con defaults)

```bash
curl -s "http://localhost:8000/alerts" -H "X-API-Key: $API_KEY"
```

El motor de reglas evalúa cada `INTELLOPS_RULES_INTERVAL_SECONDS` y crea la
alerta cuando el p95 de la ventana supera el umbral con `min_samples` muestras.

**Qué se ve:** una alerta con `status` (`pending` → `sent`), `severity`,
`channel` y el mensaje del motor, por ejemplo:

```
TTFB p95 312,4 ms supera el umbral de 50,0 ms en los últimos 5 min.
```

**Qué se verifica:** el mensaje nombra la métrica, el valor observado, el umbral
y la ventana (no es una plantilla genérica). Si la alerta queda `pending`,
faltan muestras en la ventana o el despacho no tiene canal configurado.

---

## 6. La notificación (30 s)

### Opción A — stub local (sin credenciales)

El stub es un servicio opcional del compose (perfil `smoke`):

```bash
INTELLOPS_COMMS_INTERVAL_SECONDS=5 \
INTELLOPS_COMMS_TELEGRAM_BOT_TOKEN=demo-token \
INTELLOPS_COMMS_TELEGRAM_CHAT_ID=demo-chat \
INTELLOPS_COMMS_TELEGRAM_API_BASE=http://intellops-telegram-stub:8099 \
  docker compose --profile smoke up -d intellops-telegram-stub intellops-comms

curl -s http://127.0.0.1:8099/_messages     # el mensaje recibido
```

El worker llega al stub por el DNS del compose (`intellops-telegram-stub`), no por el
host: no hace falta que el host acepte tráfico de contenedores.

### Opción B — Telegram real (si tenés un bot)

```bash
INTELLOPS_COMMS_INTERVAL_SECONDS=5 \
INTELLOPS_COMMS_TELEGRAM_BOT_TOKEN=<token del bot> \
INTELLOPS_COMMS_TELEGRAM_CHAT_ID=<chat id> \
  docker compose up -d intellops-comms
```

Sin `INTELLOPS_COMMS_TELEGRAM_API_BASE` el proveedor usa
`https://api.telegram.org` (comportamiento de siempre).

**Qué se ve:** el mensaje en el chat de Telegram o la lista de `/_messages` del
stub, con `chat_id`, `text` y `received_at`.
**Qué se verifica:** el texto incluye severidad (`[CRITICAL]`), métrica, valor
observado y umbral, y la alerta pasó a `sent` con `sent_at` no nulo
(`GET /alerts`).

Si la alerta queda `failed` con `comms delivery attempt failed` en los logs, el
contenedor no llegó al destino: revisá el token, el chat id y —con el stub— que
`intellops-telegram-stub` esté arriba y en la misma red (`docker compose ps intellops-telegram-stub`,
[`smoke-e2e.md`](./smoke-e2e.md) §5).

---

## 7. Cierre

```bash
make down                              # conserva la base (sin el stub)
docker compose --profile smoke down    # baja también el stub de Telegram
docker compose --profile smoke down -v # y borra la base (recrea el Admin al subir)
```

La aplicación `demo-mvp1`, sus métricas y sus alertas quedan en la base de
desarrollo hasta que borres el volumen.

---

## Guion resumido (para llevar)

| # | Acción | Se ve | Se verifica |
|---|---|---|---|
| 1 | Login Admin, alta de app, emisión de key | `app_id` + `ilp_...` | Key show-once |
| 2 | Página del agente con endpoint + key, consentimiento, flush | Estado de la sesión | Ingesta `202` |
| 3 | SPA con la key: Latencias y Heatmap | Serie de TTFB y grilla | El dato de la sesión aparece |
| 4 | `POST /alerts/config` | Regla creada | `201` / `200` idempotente |
| 5 | `GET /alerts` | Alerta del motor | Mensaje con métrica, observado, umbral y ventana |
| 6 | Stub o Telegram | Mensaje entregado | Alerta `sent` + mensaje con el mismo contenido |
