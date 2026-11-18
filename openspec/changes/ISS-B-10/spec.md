# SPEC — ISS-B-10: Despacho de alertas por Telegram y Email

**Tipo**: Delta spec. **Cambio**: B.10 (GitHub #72). **Base**: `proposal.md`, `design.md`,
ADR-0010, S6–S10.
**Alcance**: configuración del despacho, reclamo de alertas `Pending`, envío con retry y
transiciones a `Sent`/`Failed` en `intellops-comms`. No cambia la API ni el esquema.

## Capabilities

- **Nuevas**: `alert-dispatch`, `notification-channels`.
- **Modificadas**: ninguna.

---

## 1. notification-channels (Nueva)

### Requirement: OAS-B10-1 (routing por severidad)

El despacho MUST elegir el canal por severidad, y esa elección MUST ser configurable por entorno
con estos defaults: `critical` y `high` → Telegram; `medium` y `low` → Email. Las variables son
`INTELLOPS_COMMS_CHANNEL_CRITICAL`, `INTELLOPS_COMMS_CHANNEL_HIGH`,
`INTELLOPS_COMMS_CHANNEL_MEDIUM` e `INTELLOPS_COMMS_CHANNEL_LOW`.

El catálogo de canales de la v1 MUST ser exactamente `telegram` y `email`: MUST NOT existir
WhatsApp ni un tercer canal. Un valor fuera del catálogo MUST fallar al construir la
configuración (arranque del worker), no en el primer despacho. Los valores MUST normalizarse a
minúsculas.

#### Scenario: Defaults de la spec

- GIVEN un worker sin variables `INTELLOPS_COMMS_CHANNEL_*`
- WHEN arranca
- THEN `critical` y `high` rutean a Telegram y `medium` y `low` a Email

#### Scenario: Routing configurado

- GIVEN `INTELLOPS_COMMS_CHANNEL_CRITICAL=Email`
- WHEN el worker despacha una alerta `critical`
- THEN el envío sale por Email

#### Scenario: Canal fuera del catálogo

- GIVEN `INTELLOPS_COMMS_CHANNEL_HIGH=whatsapp`
- WHEN se construye la configuración
- THEN falla la validación y el worker no arranca en un estado inválido

### Requirement: OAS-B10-2 (destinos y arranque sin secretos)

Cada canal MUST tener UN destino por la v1, tomado del entorno:
`INTELLOPS_COMMS_TELEGRAM_CHAT_ID` para Telegram y `INTELLOPS_COMMS_SMTP_TO` para Email. Al
despachar con éxito, el destino realmente usado MUST persistirse en `alert.recipient`.

Si un canal no tiene destino o credenciales configuradas, el worker MUST NOT considerarlo un
fallo: MUST dejar sus alertas en `Pending`, MUST registrar el canal una sola vez por proceso con
su nombre y MUST seguir operando los canales configurados. `docker compose up` MUST funcionar sin
ninguna variable de notificación definida y el contenedor MUST NOT reiniciarse en bucle.

#### Scenario: Sin credenciales el stack arranca

- GIVEN un entorno sin token de Telegram ni SMTP
- WHEN se levanta `intellops-comms`
- THEN el proceso arranca, completa ciclos sin errores y loguea una vez cada canal no disponible

#### Scenario: La alerta espera a las credenciales

- GIVEN una alerta `medium` y el canal Email sin configurar
- WHEN corre el ciclo
- THEN la alerta sigue `Pending`, no se registra como `Failed` y el ciclo termina sin excepción

#### Scenario: Destino persistido

- GIVEN una alerta `high` despachada por Telegram con chat `424242`
- WHEN se lee la fila
- THEN `alert.recipient = '424242'` y `channel_id` apunta a `Telegram`

### Requirement: OAS-B10-3 (retry configurable y acotado)

El despacho MUST reintentar con backoff exponencial y estos defaults: 4 intentos (el primero
incluido), base 1 s y factor 2, lo que da esperas de 1, 2 y 4 s. `attempts`, `base_seconds`,
`factor` y `budget_seconds` MUST ser configurables por entorno
(`INTELLOPS_COMMS_RETRY_ATTEMPTS`, `INTELLOPS_COMMS_RETRY_BASE_SECONDS`,
`INTELLOPS_COMMS_RETRY_FACTOR`, `INTELLOPS_COMMS_RETRY_BUDGET_SECONDS`).

El presupuesto MUST acotar el tiempo total de espera: si la próxima espera lo excede, el despacho
MUST cortar y marcar la alerta `Failed` en vez de seguir durmiendo.

#### Scenario: Reintento exitoso

- GIVEN un proveedor que falla una vez de forma transitoria
- WHEN el dispatcher envía
- THEN hace dos intentos, espera 1 s entre ellos y la alerta queda `Sent`

#### Scenario: Presupuesto agotado

- GIVEN `attempts = 5`, base 1 s, factor 2 y presupuesto 4 s
- WHEN el proveedor falla siempre de forma transitoria
- THEN las esperas son 1 s y 2 s, el tercer intento no se sigue durmiendo y la alerta queda
  `Failed`

### Requirement: OAS-B10-4 (secretos y logs)

Los secretos (token del bot y contraseña SMTP) MUST leerse solo del entorno, MUST NOT tener valor
por defecto en el código y MUST NOT aparecer en ningún log ni en el mensaje de un error.

El log del despacho MUST nombrar únicamente id de alerta, canal e intento. MUST NOT incluir el
mensaje de la alerta, el destinatario ni el cuerpo de la respuesta del proveedor.

#### Scenario: Error de transporte sin token

- GIVEN un fallo de conexión de Telegram
- WHEN el proveedor describe el error
- THEN el texto no contiene el token del bot

### Requirement: OAS-B10-5 (empaquetado y operación)

La imagen de `intellops-comms` MUST copiar el árbol `src/` completo, MUST exponer `comms.*` como
paquete top-level (`PYTHONPATH=/app/src`), MUST instalar las dependencias de
`src/api/requirements.txt` y MUST arrancar con `python -m comms.entrypoint`. MUST NOT exponer
puertos ni declarar dependencias nuevas de runtime.

`docker-compose.yml` MUST pasar las variables del worker con default vacío (`${VAR:-}`), de modo
que el stack levante sin un `.env` de notificaciones.

El worker MUST apagarse ordenadamente con SIGTERM y SIGINT, y un ciclo que falle MUST NOT matar el
proceso.

#### Scenario: La imagen arranca el worker

- GIVEN la imagen construida desde `src/comms/Dockerfile`
- WHEN se ejecuta contra la base
- THEN completa al menos un ciclo y se apaga con código 0 al recibir SIGTERM

#### Scenario: Ciclo fallido no es crash-loop

- GIVEN una excepción inesperada en un ciclo
- WHEN el scheduler continúa
- THEN el proceso sigue vivo y el próximo ciclo vuelve a intentar

---

## 2. alert-dispatch (Nueva)

### Requirement: CD-1 (reclamo de Pending por lote)

Cada ciclo MUST reclamar como máximo `INTELLOPS_COMMS_BATCH_SIZE` alertas (default 20) en estado
`Pending`, ordenadas por `created_at`, con una sentencia
`SELECT ... WHERE status = Pending ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT :batch`, y
MUST despacharlas mientras la fila está bloqueada.

El lote MUST ser acotado de modo que un backlog grande se drene en varios ciclos. Una alerta ya
despachada MUST NOT volver a reclamarse.

#### Scenario: Lote acotado

- GIVEN 5 alertas `Pending` y un lote de 2
- WHEN corre el ciclo
- THEN se despachan 2 y quedan 3 `Pending` para el ciclo siguiente

#### Scenario: Dos despachadores no reparten la misma fila

- GIVEN una alerta reclamada por una transacción
- WHEN otra transacción reclama a la vez
- THEN la segunda no obtiene esa fila (`SKIP LOCKED`)

#### Scenario: Alerta ya enviada

- GIVEN una alerta `Sent`
- WHEN corre otro ciclo
- THEN no se reclama ni se vuelve a enviar

### Requirement: CD-2 (canal por severidad)

El despacho MUST enviar cada alerta por el canal que su severidad rutea (OAS-B10-1). Una alerta
`critical` o `high` MUST salir por Telegram; una `medium` o `low` MUST salir por Email, salvo que
la configuración diga otra cosa.

#### Scenario: Las cuatro severidades

- GIVEN una alerta de cada severidad y ambos canales configurados
- WHEN corre el ciclo
- THEN `critical` y `high` salen por Telegram y `medium` y `low` por Email

### Requirement: CD-3 (retry con backoff)

Un fallo transitorio MUST reintentarse según OAS-B10-3, sin propagar la excepción fuera del ciclo.
Un error de proveedor no clasificado MUST tratarse como transitorio.

#### Scenario: Error inesperado del proveedor

- GIVEN un proveedor que levanta un error genérico
- WHEN el dispatcher envía
- THEN reintenta hasta agotar intentos y la alerta queda `Failed`, sin excepción en el ciclo

### Requirement: CD-4 (fallos permanentes)

Los 4xx que el proveedor marca como permanentes MUST ir a `Failed` sin reintento: Telegram 400 y
403, y SMTP 5xx (incluida la autenticación fallida y los destinatarios rechazados). El resto de
los fallos (429, 5xx HTTP, 4xx SMTP, conexión caída, timeout) MUST considerarse transitorio.

#### Scenario: Telegram rechaza el mensaje

- GIVEN un envío que responde 403
- WHEN el dispatcher envía
- THEN hay UN solo intento, sin esperas, y la alerta queda `Failed`

### Requirement: CD-5 (transiciones)

En el éxito, la alerta MUST quedar con `status_id` = `Sent`, `sent_at` = momento del envío,
`channel_id` del catálogo y `recipient` con el destino real.

Al agotar los intentos (o ante un fallo permanente), la alerta MUST quedar con `status_id` =
`Failed` y `sent_at` MUST permanecer NULL: la columna es el momento de entrega y una alerta
fallida nunca se entregó. `channel_id` y `recipient` MUST quedar con el destino del intento: sin
esos datos una alerta fallida no se puede diagnosticar y es indistinguible de una que nadie
intentó despachar.

#### Scenario: Éxito

- GIVEN un envío exitoso
- WHEN se lee la fila
- THEN `status = Sent`, `sent_at` no es NULL, `channel_id` y `recipient` están completos

#### Scenario: Fallo

- GIVEN cuatro fallos transitorios
- WHEN se agota el retry
- THEN `status = Failed`, `sent_at` es NULL y `GET /alerts` muestra `sent_at: null`

### Requirement: CD-6 (resumen y continuidad del ciclo)

Cada ciclo MUST registrar cuántas alertas reclamó, envió y falló. Una alerta que falla MUST NOT
impedir el despacho del resto del lote.

#### Scenario: Un fallo no frena el lote

- GIVEN un lote con una alerta que falla de forma permanente y otra que se envía
- WHEN corre el ciclo
- THEN el resumen cuenta `claimed=2 sent=1 failed=1`

---

## 3. Contrato con B.14

### Requirement: CT-B14-B10 (extensión: la alerta del motor se despacha y se lee)

Una alerta creada por el motor de reglas (`application_id`, `severity`, `message`, estado
`Pending`, sin canal ni destinatario) MUST ser despachable por el dispatcher sin consultar
`alert_rule`. Tras el envío MUST quedar `Sent` con `channel_id`, `recipient` y `sent_at`, y
`GET /alerts` MUST exponerla con `status: sent`, el canal en minúsculas y `sent_at` no nulo, sin
exponer `recipient`.

El mensaje y los datos de la regla (`rule_id`, `threshold`, `observed_value`) MUST conservarse
intactos: el despacho no reescribe el contenido de la alerta.

#### Scenario: De Pending a Sent por el dispatcher

- GIVEN una alerta creada por `RulesEngine` con severidad `high`
- WHEN el dispatcher la envía por Telegram con un transporte falso
- THEN la fila queda `Sent` con canal `Telegram`, destinatario persistido y `sent_at`, y
  `GET /alerts` la muestra con `channel: telegram` y `sent_at`

#### Scenario: Fallo permanente visible por la API

- GIVEN la misma alerta y un transporte que rechaza el mensaje
- WHEN corre el ciclo
- THEN `GET /alerts` la muestra con `status: failed`, `channel: null` y `sent_at: null`
