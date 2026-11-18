# SPEC — ISS-C-01: Integración de punta a punta

**Tipo**: Delta spec. **Cambio**: C.1 (GitHub #76). **Base**: `proposal.md`, `design.md`, S20–S23.
**Alcance**: smoke reproducible sobre la stack de `docker-compose.yml`, base URL de Telegram
configurable y documentación de operación/demo. Sin migraciones, sin cambios de contrato.

## Capabilities

- **Nuevas**: `e2e-smoke`, `operations-runbook`.
- **Modificadas**: `notification-channels` (base URL configurable, aditiva).

---

## 1. notification-channels (Modificada)

### Requirement: E2E-1 (base URL de Telegram configurable)

`CommsSettings` MUST aceptar `INTELLOPS_COMMS_TELEGRAM_API_BASE` con default
`https://api.telegram.org`, y `TelegramProvider` MUST usarlo en la URL
`{base}/bot{token}/sendMessage`. Un valor distinto MUST NOT cambiar el resto del contrato
(payload, retry ni clasificación de errores).

#### Scenario: default sin la variable

- GIVEN un worker sin `INTELLOPS_COMMS_TELEGRAM_API_BASE`
- WHEN envía una alerta por Telegram
- THEN la URL es `https://api.telegram.org/bot<token>/sendMessage` (comportamiento actual)

#### Scenario: stub local

- GIVEN `INTELLOPS_COMMS_TELEGRAM_API_BASE=http://host.docker.internal:8099`
- WHEN envía una alerta
- THEN la request llega al stub y la alerta pasa a `sent` con `sent_at` no nulo

---

## 2. e2e-smoke (Nueva)

### Requirement: E2E-2 (un comando recorre el flujo completo, S20, S22)

`make smoke` (o `python3 scripts/smoke.py`) MUST verificar, contra la stack real levantada con
`docker-compose.yml`, esta secuencia y en este orden: `GET /health` 200; `POST /auth/login` con el
admin del seed; `POST /applications` + `POST /applications/{id}/api-key`; `POST /telemetry/metrics`
con `202` y `accepted ≥ min_samples`; lectura del dato por `GET /metrics/query`;
`POST /alerts/config`; alerta visible en `GET /alerts`; y el mensaje correspondiente en el stub de
Telegram con la alerta en `sent`.

MUST NOT exigir credenciales reales de Telegram ni SMTP, MUST usar sólo la librería estándar de
Python y MUST fallar con exit ≠ 0 nombrando el paso que falló y el cuerpo de la respuesta cuando
hay uno.

#### Scenario: flujo completo verde

- GIVEN la stack recién levantada (`docker compose up -d --build`) y los intervalos en 5 s
- WHEN corre `make smoke`
- THEN termina en verde e imprime el `app_id`, el `session_id`, el `alert_id` y los segundos de
  cada tramo

#### Scenario: dato no persistido

- GIVEN una ingesta que la API aceptó pero que no aparece en `/metrics/query` dentro del timeout
- WHEN corre el smoke
- THEN falla en el paso de lectura con el `batch_id` y los contadores de la ingesta (no sigue con
  la regla como si nada)

### Requirement: E2E-3 (stub de notificación verificable)

El stub MUST escuchar en un puerto configurable (default 8099), MUST responder 200 al
`sendMessage`, MUST acumular los mensajes recibidos y MUST exponerlos en `GET /_messages` con el
`chat_id` y el texto, para que el smoke verifique contenido y destinatario. MUST NOT requerir
dependencias externas.

#### Scenario: mensaje con el contenido de la alerta

- GIVEN una alerta `critical` de TTFB
- WHEN el despacho la envía
- THEN `GET /_messages` devuelve un mensaje cuyo texto incluye la métrica, el umbral y el valor
  observado

### Requirement: E2E-4 (runbook reproducible, S22)

`docs/operations/smoke-e2e.md` MUST documentar: prerequisitos, el comando exacto, la secuencia de
pasos con los endpoints, los tiempos de espera esperados (ciclo de reglas y de despacho), cómo
interpretar cada fallo y cómo limpiar el entorno. `CONTRIBUTING.md` MUST sumar `make smoke` a los
comandos.

#### Scenario: reproducir desde cero

- GIVEN una máquina con Docker y Python 3.11+
- WHEN se siguen los pasos del runbook
- THEN el smoke termina en verde sin credenciales externas

### Requirement: E2E-5 (demo de punta a punta, S23)

`docs/operations/demo-mvp1.md` MUST describir una demo reproducible: abrir la página del agente
(`src/agent/demo/index.html`) con endpoint y API key, generar telemetría, verla en la SPA
(latencias y heatmap), disparar la regla y ver la notificación; MUST indicar qué se muestra en
pantalla y qué se verifica en cada paso.

#### Scenario: demo sin sorpresas

- GIVEN la stack levantada y la SPA servida (`npm run preview`)
- WHEN se sigue el guion de la demo
- THEN cada paso tiene su lugar en la pantalla y su verificación asociada

## 3. Cierre de S21 (sin conflictos de integración abiertos)

### Requirement: E2E-6 (verde de integración)

La rama MUST quedar con la suite completa en verde (Python y frontend), el smoke en verde y sin
conflictos abiertos con `origin/develop`. Como MVP1 no se pushea (S33), "funcionando en `develop`"
(S20) se cumple como *mergeable*: `git merge-tree` sin conflictos contra `origin/develop`.
