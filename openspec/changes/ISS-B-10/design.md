# Design: ISS-B-10 — Despacho de alertas por Telegram y Email

Base: `proposal.md`, ADR-0010, D1, S6–S10, `openspec/changes/ISS-B-14/spec.md` (CT-B14-B10).

## 1. Dónde vive el despachador

ADR-0010 ya asigna a `intellops-comms` el "polling de `ALERT` Pending, despacho por
Telegram/Email con retry + backoff y actualización a Sent/Failed, sin puertos". Este cambio
reemplaza el placeholder por ese worker y no agrega contenedores ni puertos: el ciclo es propio
(no comparte scheduler con el motor de reglas) y el proceso se apaga con SIGTERM/SIGINT.

No hay migración: las columnas que usa el despacho (`status_id`, `channel_id`, `recipient`,
`sent_at`) existen desde `0001`/`0007`. `alert_channel` ya trae `Telegram` y `Email` desde la
`0001`, y `alert_status` trae `Pending`, `Sent` y `Failed`.

Alternativas descartadas:

- **Despachar en `intellops-core`**: la API es el camino caliente (C.3) y un envío a un proveedor
  externo con backoff no puede vivir en el request path.
- **Despachar en `intellops-ai-engine`**: mezcla dominio (evaluar reglas) con transporte y le da a
  un contenedor de 1000 MB trabajo de red con retry.
- **Un quinto contenedor**: excede el presupuesto de 4 contenedores y el límite de RAM del MVP.

## 2. Routing por severidad y catálogo de la v1

El canal se elige por severidad, configurable por entorno:

| Severidad | Default |
|---|---|
| `critical` | Telegram |
| `high` | Telegram |
| `medium` | Email |
| `low` | Email |

Variables: `INTELLOPS_COMMS_CHANNEL_{CRITICAL,HIGH,MEDIUM,LOW}` con valores `telegram` o `email`
(normalizados a minúsculas, aceptando `Email`/`EMAIL`). Un valor fuera del catálogo es
configuración inválida y **falla al arrancar** (`ValidationError`), no en el primer despacho: un
typo no puede convertirse en alertas que nunca salen. La v1 no tiene WhatsApp: el catálogo es el
de `alert_channel` (`0001`) y agregar un canal exige migración + proveedor.

Un destino por canal (no hay multi-destinatario en la v1): `INTELLOPS_COMMS_TELEGRAM_CHAT_ID` y
`INTELLOPS_COMMS_SMTP_TO`. El diseño deja el destino en el proveedor, cuyo contrato
(`AlertProvider`) expone `name` y `destination`; el dispatcher no sabe si detrás hay una Bot API o
un SMTP.

## 3. Reclamo: `FOR UPDATE SKIP LOCKED` por lote

El ciclo reclama con una sola sentencia:

```sql
SELECT alert_id, application_id, severity, message, created_at
FROM alert
WHERE status_id = :pending AND severity IN (:severities)
ORDER BY created_at, alert_id
FOR UPDATE SKIP LOCKED
LIMIT :batch
```

Y despacha **con el lock tomado**: la transacción de la sesión se cierra con la transición de cada
alerta (`mark_sent`/`mark_failed` hacen commit). Tres consecuencias, todas deliberadas:

1. **`SKIP LOCKED`** evita que un segundo proceso espere o repita filas: si mañana hay dos
   despachadores, cada fila la toma uno solo. Un test de integración contra Postgres lo fija con
   dos sesiones concurrentes.
2. **El filtro por severidad** deja fuera, en la misma sentencia, las alertas cuyo canal no tiene
   credenciales: nunca se bloquean y siguen `Pending` (§6).
3. **Se hace I/O de red dentro de la transacción.** El lock de las filas del lote se libera en el
   primer commit, así que un lote de 20 alertas no mantiene 20 locks durante 20 envíos. Es
   aceptable porque **la v1 corre un único contenedor de comms** (ADR-0010): no hay un segundo
   despachador compitiendo por esas filas y la alerta se actualiza igual al final del intento. Si
   el proceso muere a mitad de lote, la transacción se descarta y las alertas sin commit siguen
   `Pending`: el próximo ciclo las reintenta, sin pérdida.

El lote es acotado (default 20, configurable 1..100): un backlog grande se drena en varios ciclos
en vez de sostener un lock sobre toda la tabla.

## 4. Retry y backoff

`RetryPolicy` (defaults) es `attempts = 4`, `base_seconds = 1`, `factor = 2`,
`budget_seconds = 60`. `attempts` cuenta el **primer** intento, así que hay tres esperas:

| Intento | Espera antes del siguiente |
|---|---|
| 1 | 1 s |
| 2 | 2 s |
| 3 | 4 s |
| 4 | — (si falla, `Failed`) |

Configurables por `INTELLOPS_COMMS_RETRY_{ATTEMPTS,BASE_SECONDS,FACTOR,BUDGET_SECONDS}`. El
presupuesto acota el **tiempo total** del despacho de una alerta: si la próxima espera excediera
`budget_seconds`, el dispatcher no duerme más y marca `Failed`. Sin ese tope, un `attempts` alto
con un `factor` alto podría dormir horas con el lote abierto.

Clasificación de fallos (S7):

| Proveedor | Permanente (sin reintento) | Transitorio (reintenta) |
|---|---|---|
| Telegram | 400, 403 | 429, 5xx, error de transporte, timeout |
| Email (SMTP) | 5xx (`SMTPResponseException` 500–599, autenticación, destinatarios rechazados) | 4xx SMTP, conexión caída, timeout |

Cualquier excepción no clasificada de un proveedor se trata como transitoria: es preferible
reintentar un error inesperado a perder la alerta. Nunca se propaga fuera del ciclo, así que una
alerta con problemas no frena el resto del lote (CD-6).

## 5. Transiciones y el `sent_at` de una alerta fallida

| Resultado | `status_id` | `sent_at` | `channel_id` | `recipient` |
|---|---|---|---|---|
| Éxito | `Sent` | `now()` del envío | catálogo `alert_channel` | destino real usado |
| Intentos agotados | `Failed` | **NULL** | catálogo `alert_channel` | destino del intento |

`sent_at` es el **momento de entrega**: una alerta que nunca se entregó no tiene uno, así que un
fallo no lo completa con `now()`. Es una lectura deliberada de S8 —"éxito: `Sent` + `sent_at`;
fallo: `Failed`"— y no un olvido: rellenarlo haría indistinguible una alerta enviada de una que se
rindió.

El canal y el destinatario **sí** se persisten en `Failed`: son el destino del intento, y sin ellos
el operador no puede saber qué canal falló ni distinguir una alerta que se rindió de una que nadie
intentó despachar. `GET /alerts` devuelve entonces `status: failed`, `channel: telegram` (o
`email`) y `sent_at: null`, que es lo que hace diagnosticable el fallo.

`sent_at` lo calcula el dispatcher (reloj inyectable en tests) y no un `now()` de PostgreSQL, para
que el mismo reloj decida el backoff y el timestamp de la fila.

## 6. Canal sin credenciales

Si un canal no tiene destino o credenciales configuradas (`telegram_bot_token` **y**
`telegram_chat_id`; `smtp_host` **y** `smtp_to`), ese canal no se instancia como proveedor y:

1. el ciclo no reclama alertas de las severidades que rutean a él (§3: filtro en el `SELECT`);
2. el canal se avisa **una vez por proceso** con su nombre
   (`comms channel unavailable channel=email reason=missing_credentials`);
3. la alerta **sigue Pending**: cuando el operador configure las credenciales, el próximo ciclo la
   toma.

No es un fallo y no puede serlo: `docker compose up` corre sin secretos en desarrollo y en CI, y
un contenedor que trata "no hay token" como error entraría en crash-loop. El registro de "ya
avisado" se comparte entre ciclos (el worker crea un `Dispatcher` por ciclo) para no repetir el
aviso cada 30 s.

Consecuencia aceptada: las alertas de un canal sin configurar se acumulan en `Pending`. Es
preferible a perderlas o a marcarlas `Failed`, que sería mentir sobre una entrega que nadie
intentó.

## 7. Secretos y logs

Los secretos (token del bot, contraseña SMTP) se leen **solo** del entorno, no tienen valor por
defecto en el código y nunca se loguean: el arranque registra intervalo, lote, canales
configurados y la URL de base sin credenciales (`...@host:5432/db`). Durante el despacho el log
nombra **id de alerta, canal e intento** y nada más: ni el mensaje, ni el destinatario, ni el
cuerpo de la respuesta del proveedor. Los errores de transporte se describen por tipo
(`telegram request failed: ConnectError`), no con el mensaje original de `httpx`, que incluye la
URL y con ella el token.

## 8. Ciclo y scheduler

`CommsScheduler` repite un ciclo cada `INTELLOPS_COMMS_INTERVAL_SECONDS` (default **30 s**, frente
a los 60 s del motor de reglas: el despacho es la latencia que percibe una persona). Es una
réplica deliberada de `src/ml/rules/scheduler.py` porque ADR-0010 prohíbe cross-imports entre
contenedores.

Cada ciclo: construir la lista de severidades ruteables → reclamar el lote → enviar con retry →
transicionar → loguear `claimed/sent/failed`. Una excepción del ciclo (base caída, proveedor roto)
se loguea y **no mata el proceso**: sin política de reinicio externa, el próximo ciclo es el
reintento.

## 9. Proveedores y dependencias

Sin dependencias nuevas (S10):

- **Telegram**: `httpx.AsyncClient` (ya es dependencia del core) contra
  `https://api.telegram.org/bot<token>/sendMessage`, con `chat_id` y texto
  `"[SEVERIDAD] <mensaje>"`. Timeout de 10 s configurable.
- **Email**: `smtplib.SMTP` + `email.message.EmailMessage` de la stdlib, en
  `asyncio.to_thread` porque `smtplib` es bloqueante y bloquear el event loop congelaría el ciclo
  completo. STARTTLS por defecto, login opcional. Asunto `[IntellOps] Alerta <severidad>` y
  cuerpo con el mensaje del motor, id de alerta, aplicación y severidad.

El contrato `AlertProvider` (`name`, `destination`, `send`) es estructural: los tests usan
proveedores en memoria y los proveedores reales se prueban con `httpx.MockTransport` y un
`smtplib.SMTP` falso, sin salir a la red.

## 10. Alternativas consideradas

- **Marcar la alerta como "en proceso" antes de enviar**: agrega un estado al catálogo
  (`alert_status`), una migración y un estado zombi si el proceso muere. El lock de §3 da la misma
  exclusión sin tocar el esquema.
- **Reintentos dentro de la base (una tabla de intentos)**: duplica estado que el lock y el log ya
  cubren, y agranda el esquema de la v1.
- **Backoff lineal**: con 4 intentos, 1/2/3 s no despega un 429 de Telegram; el exponencial sí.
- **Marcar `Failed` cuando falta un token**: convierte un problema de configuración en un fallo de
  entrega y rompe `docker compose up` sin secretos (§6).
