# Smoke E2E de la v1 (ISS-C-01)

Runbook del smoke que recorre el flujo completo sobre la stack real de
`docker-compose.yml`: agente → ingesta → PostgreSQL → motor de reglas → alerta →
despacho → notificación. Verifica en un solo comando lo que ninguna suite por
pieza puede ver: que las cuatro piezas del compose —más el stub de Telegram del
perfil `smoke`— se hablen.

Alcance: verificación local de la rama `MVP1` (S20–S23). Carga, performance y
release son C.3 y C.5. Las credenciales reales de Telegram o SMTP **no** hacen
falta: el camino de la notificación se verifica contra el stub de Telegram, un
servicio opcional del compose (perfil `smoke`) que simula la Bot API.

---

## 1. Qué verifica

| # | Etapa | Endpoint / artefacto | Espera | Timeout |
|---|-------|----------------------|--------|---------|
| 0 | Stub de Telegram | `GET /health` del stub | 200 | 15 s |
| 1 | API arriba | `GET /health` | 200 | 120 s (build + migraciones) |
| 2 | Login del Admin | `POST /auth/login` | 200 + `access_token` | request |
| 3 | Aplicación y key | `POST /applications`, `POST /applications/{id}/api-key` | 201, `api_key` | request |
| 4 | Catálogo | `GET /metrics/list` | `metric_type_id` de TTFB | request |
| 5 | Ingesta | `POST /telemetry/metrics` | 202 con `accepted >= 5` y sin rechazos | request |
| 6 | Lectura | `GET /metrics/query?metric_type=<TTFB>&start=...` | bucket con `session_count >= 1` | 60 s |
| 7 | Regla | `POST /alerts/config` (`gt`, `critical`, ventana 5 min, 5 muestras) | 201 o 200 | request |
| 8 | Alerta | `GET /alerts` | alerta con el mensaje del motor | 60 s (ciclo de reglas) |
| 9 | Notificación | `GET /alerts` + `GET /_messages` del stub | alerta `sent` + mensaje en el stub | 120 s (ciclo de despacho) |

El smoke espera **por ciclo y con polling**, no con `sleep` a ciegas: los
workers de reglas y de despacho avanzan cada `INTELLOPS_RULES_INTERVAL_SECONDS` y
`INTELLOPS_COMMS_INTERVAL_SECONDS`. `make smoke` los baja a 5 s.

Cuando termina en verde imprime `app_id`, `session_id`, `alert_id`, `rule_id`, el
`metric_type_id` de TTFB, el mensaje exacto que recibió el stub y los segundos de
cada etapa.

---

## 2. Prerequisitos

| Requisito | Cómo se comprueba |
|---|---|
| Docker con Compose v2 | `docker compose version` |
| Python 3.11+ en el host (sólo stdlib) | `python3 --version` |
| Puerto **8099** libre en loopback (el stub lo publica en `127.0.0.1`) | `ss -ltn \| grep 8099` |
| Imagen `python:3.11-slim` (ya la usan los builds del compose) | `docker image ls python` |
| El Admin del seed en la base (`admin@intellops.local`) | lo siembra la migración `0002`; una base vieja puede no tenerlo |
| Stack propia o reutilizable | `make smoke` reconstruye imágenes; `SMOKE_NO_BUILD=1` las reusa |

No hace falta ninguna credencial externa: ni bot de Telegram, ni SMTP, ni
cuenta real. Tampoco hace falta que el host acepte tráfico desde los
contenedores: el stub vive en la red del compose (ver §4).

Si el smoke falla en el **login**, la base no tiene el Admin del seed
(migración `0002`): recreá el volumen con `docker compose down -v` y volvé a
correr `make smoke`.

---

## 3. Un solo comando

```bash
make smoke
```

Qué hace el target:

1. Exporta los intervalos cortos, las credenciales de mentira del stub y la base
   de la Bot API apuntando al servicio del compose:
   `INTELLOPS_RULES_INTERVAL_SECONDS=5`, `INTELLOPS_COMMS_INTERVAL_SECONDS=5`,
   `INTELLOPS_COMMS_TELEGRAM_BOT_TOKEN=smoke-token`,
   `INTELLOPS_COMMS_TELEGRAM_CHAT_ID=smoke-chat` y
   `INTELLOPS_COMMS_TELEGRAM_API_BASE=http://intellops-telegram-stub:8099`.
2. Levanta la stack con el perfil del stub:
   `docker compose --profile smoke up -d --build` (la primera vez baja y
   construye las tres imágenes: contá hasta ~5 min).
   Con `SMOKE_NO_BUILD=1 make smoke` reusa las imágenes ya construidas.
3. Corre `python3 scripts/smoke.py`, que verifica el `/health` del stub, recorre
   las nueve etapas y resume. El stub no lo baja el script: se baja con la stack
   (§6).

Salida esperada (verde):

```
SMOKE E2E EN VERDE
  app_id:            ...
  session_id:        ...
  alert_id:          ...
  rule_id:           ...
  TTFB metric_type:  1
  batch_id:          ...
  alerta:            status=sent channel=telegram
  mensaje en el stub: '[CRITICAL] TTFB p95 1500,0 ms supera el umbral de 500,0 ms en los últimos 5 min.'

Segundos por etapa:
  ...
  total                                                  xx.x s
```

Con los intervalos en 5 s el flujo completo tarda del orden de **15 s** una vez
que la stack está arriba; con los defaults de producción (60/30 s) tarda más
pero los timeouts alcanzan.

### Corrida manual

Equivalente sin `make`:

```bash
INTELLOPS_RULES_INTERVAL_SECONDS=5 \
INTELLOPS_COMMS_INTERVAL_SECONDS=5 \
INTELLOPS_COMMS_TELEGRAM_BOT_TOKEN=smoke-token \
INTELLOPS_COMMS_TELEGRAM_CHAT_ID=smoke-chat \
INTELLOPS_COMMS_TELEGRAM_API_BASE=http://intellops-telegram-stub:8099 \
  docker compose --profile smoke up -d --build

python3 scripts/smoke.py
```

### Variables del smoke

| Variable | Default | Qué cambia |
|---|---|---|
| `SMOKE_API_URL` | `http://localhost:8000` | Base de la API |
| `SMOKE_STUB_URL` | `http://127.0.0.1:8099` | Stub de Telegram visto desde el host |
| `SMOKE_ADMIN_EMAIL` | `admin@intellops.local` | Admin del seed |
| `SMOKE_ADMIN_PASSWORD` | `admin-dev-password` | Password dev del seed |
| `SMOKE_TIMEOUT_HEALTH` | `120` | Segundos para `/health` |
| `SMOKE_TIMEOUT_INGEST` | `60` | Segundos para ver el dato en `/metrics/query` |
| `SMOKE_TIMEOUT_ALERT` | `60` | Segundos para ver la alerta en `/alerts` |
| `SMOKE_TIMEOUT_NOTIFICATION` | `120` | Segundos para la alerta `sent` + el mensaje |

Cada una tiene su flag equivalente: `python3 scripts/smoke.py --help`.

El smoke habla con el stub por `SMOKE_STUB_URL` (el puerto publicado en
loopback); el worker de `comms` habla con el stub por DNS del compose
(`http://intellops-telegram-stub:8099`). Si cambiás el puerto en `docker-compose.yml`
cambiá los dos.

---

## 4. El stub de Telegram

`scripts/telegram_stub.py` (sólo stdlib) hace de Bot API y permite verificar el
envío sin cuenta real. Es un servicio **opcional** del compose, bajo
`profiles: ["smoke"]`:

```yaml
  intellops-telegram-stub:
    image: python:3.11-slim
    profiles: ["smoke"]
    command: ["python", "/app/telegram_stub.py"]
    volumes: ["./scripts:/app:ro"]
    ports: ["127.0.0.1:8099:8099"]   # para leer /_messages desde el host
    mem_limit: 80m
    restart: "no"
```

Sin `--profile smoke`, `docker compose up` sigue levantando **cuatro** servicios:
la stack por defecto no cambia. Con el perfil, el stub entra en la red del
compose y el worker de `comms` le llega por DNS (`http://intellops-telegram-stub:8099`).
Esa es la razón de que el smoke no dependa de `host.docker.internal`: hay hosts
(con firewall de entrada restrictivo) donde un contenedor no puede abrir
conexiones TCP hacia el host, y el smoke fallaría sin que el producto tenga un
problema.

| Ruta | Qué hace |
|---|---|
| `POST /bot<token>/sendMessage` | 200 `{"ok": true}`; guarda `chat_id`, `text` y `received_at` |
| `GET /_messages` | Lista JSON de los mensajes recibidos |
| `GET /health` | 200 `{"ok": true}` |
| cualquier otra | 404 JSON |

Levantarlo solo (con la stack ya arriba) y probarlo a mano:

```bash
docker compose --profile smoke up -d intellops-telegram-stub
docker compose ps intellops-telegram-stub                 # Up

curl -s -X POST http://127.0.0.1:8099/botsmoke-token/sendMessage \
  -H 'Content-Type: application/json' \
  -d '{"chat_id":"smoke-chat","text":"hola"}'
curl -s http://127.0.0.1:8099/_messages
```

El token no se valida: alcanza con que la ruta termine en `/sendMessage`. Los
mensajes viven en memoria del contenedor: se pierden al recrearlo.

---

## 5. Cuando falla

El smoke imprime la etapa, el request, el status y el cuerpo truncado, y sale con
código ≠ 0. Tabla de lectura rápida:

| Etapa que falla | Causa probable | Qué mirar |
|---|---|---|
| `stub de Telegram` | El servicio no está arriba (falta `--profile smoke`) o el puerto 8099 está ocupado | `docker compose --profile smoke up -d intellops-telegram-stub`; `docker compose ps intellops-telegram-stub` |
| `make smoke` aborta con `Bind for 127.0.0.1:8099 failed: port is already allocated` | Quedó un stub de una corrida anterior (o de un nombre viejo del servicio) con el puerto tomado | `docker compose --profile smoke down`; si persiste, `docker ps -a --filter name=telegram-stub` y `docker rm -f <nombre>` |
| `health` | La API no arrancó, migración falló o el build no terminó | `docker compose logs intellops-core` |
| `login` | La base no tiene el Admin del seed | `docker compose down -v && make smoke`; migración `0002` |
| `aplicación` / `catálogo` | Roles, JWT o catálogo `metric_type` incompletos | logs de `intellops-core`; `GET /metrics/list` |
| `ingesta` | Payload rechazado (`rejected` no vacío) o backpressure (503) | el `reason` de cada rechazo en el cuerpo del 202; logs del worker de ingesta |
| `lectura` | La API aceptó el lote pero el dato no se persistió | el mensaje trae `batch_id` y `accepted`; `docker compose logs intellops-core` |
| `regla` | Payload fuera de dominio (422) o app/métrica inexistente (404) | el cuerpo trae el código del contrato |
| `alerta` | El motor de reglas no evaluó todavía o la ventana quedó sin muestras | `docker compose logs intellops-ai-engine`; intervalo y `window_minutes` |
| `notificación` | El despacho no pudo enviar: credenciales, base URL o el stub inalcanzable | `docker compose logs intellops-comms`; alerta en `failed` |

### El worker de comms no llega al stub

El worker sale al stub por el DNS del compose (`http://intellops-telegram-stub:8099`). Si
no hay mensaje en `/_messages` pero el stub está arriba, revisá en este orden:

```bash
# 1. El stub está en la misma red que comms?
docker compose ps intellops-telegram-stub
docker compose exec intellops-comms python -c \
  "import urllib.request; print(urllib.request.urlopen('http://intellops-telegram-stub:8099/health', timeout=3).read())"

# 2. El worker tiene la base URL, el token y el chat id?
docker compose exec intellops-comms env | grep TELEGRAM

# 3. Qué dijo el despacho?
docker compose logs --tail=50 intellops-comms
```

Síntoma típico en los logs (`comms delivery attempt failed ... channel=telegram`)
con la alerta terminando en `failed`: el worker conservó variables viejas. Un
`docker compose up -d` sin las variables del smoke recrea `comms` apuntando a
`https://api.telegram.org` (y ahí el token `smoke-token` no existe): volvé a
correr `make smoke` completo para que las tres variables y el stub queden
coherentes.

Si el puerto 8099 ya está ocupado en el host (otro stub suelto, otra stack), el
contenedor no arranca: liberá el puerto o cambiá el mapeo en `docker-compose.yml`
y `SMOKE_STUB_URL` a la vez.

---

## 6. Limpieza

```bash
make down                              # baja la stack, conserva la base
docker compose --profile smoke down    # incluye el stub de Telegram
docker compose --profile smoke down -v # y borra el volumen de Postgres
```

El stub se baja con la stack del perfil: no queda escuchando en 8099 cuando
temina la corrida. Si querés sacarlo sin bajar lo demás:
`docker compose --profile smoke stop intellops-telegram-stub`.

Los datos del smoke quedan en la base de desarrollo: una aplicación
`smoke-<timestamp>` y sus métricas y alertas. Para dejarla limpia, `docker
compose --profile smoke down -v` (borra también el Admin del seed: la próxima
corrida lo recrea).

---

## 7. Mergeabilidad contra `develop` (E2E-6, S33)

`MVP1` no se pushea, así que "el flujo funciona en `develop`" se cumple como
*mergeable*: sin conflictos abiertos con `origin/develop`.

```bash
git fetch origin develop
git merge-tree --write-tree origin/develop HEAD   # sin conflictos = sólo el árbol
```

Si imprime conflictos, resolvelos antes de cerrar el cambio. Además, antes de
declarar S21 cerrado: suite Python (`make ci`), suite frontend (`npm test`) y
`make smoke` en verde sobre esta rama.
