# Contrato del agente RUM de navegador v0.1

- **Versión del contrato**: 0.1 (propuesto para revisión)
- **Fecha**: 2026-10-23
- **Tarea**: A.3 — Contrato del agente RUM de navegador v0.1
- **Owner**: Federico
- **Alcance**: habilita B.1 (TTFB, FCP y errores JS). XHR y rage clicks quedan para B.7, diferible a v1.1 (`docs/business/issues-fases-abc.md:256-268`).
- **Estado**: pendiente de revisión de Santiago (QA).

Este documento define qué envía el agente, cómo lo transporta y qué garantiza. El servidor es la autoridad: todo campo aquí listado existe en `openspec/specs/openapi.yaml` o en `src/api/presentation/schemas/ingest.py`. Cuando un dato no tiene destino en el servidor, se declara explícitamente y se registra en §13 o §14.

## 1. Resumen y alcance

| Decisión | Valor v0.1 | Evidencia |
|---|---|---|
| Endpoints | `POST /telemetry/metrics` y `POST /telemetry/exceptions` | `openspec/specs/openapi.yaml:24-123` |
| Semántica | 202 al encolar, rechazo parcial por evento | `docs/architecture/PipelineIngestaRUM.md:37-58` |
| Métricas v0.1 | TTFB y FCP, una vez por page view | `docs/business/issues-fases-abc.md:166-180` |
| Excepciones v0.1 | `window.onerror` y `unhandledrejection` | `docs/research/rum-agent-deep-dive.md:1119-1124` |
| Transporte | `fetch` con `keepalive: true` y header `X-API-Key` | `src/api/presentation/dependencies.py:42` |
| Bundle | tope 30 KB gzip; objetivo 20 KB | `docs/business/issues-fases-abc.md:136,178`; `docs/research/rum-agent-deep-dive.md:1131` |

Fuera de alcance v0.1: LCP, CLS, INP, XHR latency, rage clicks, user ID, geolocalización, persistencia local de eventos y transporte `sendBeacon` (ver §4).

## 2. Modelo de eventos v0.1

### 2.1 Sesión y metadata

El agente genera un `session_id` UUID v4 opaco (sin user ID) y lo conserva en `sessionStorage`. Política del agente: se rota tras 30 minutos de inactividad o 24 horas de vida. El servidor acepta el UUID y crea `user_session` en el primer evento; `app_id` se deriva exclusivamente de la API key (`src/api/infrastructure/ingest/queue.py:253-263`).

El servidor no recibe un fin de sesión: `end_timestamp` y `duration_ms` existen en el DDL (`src/api/infrastructure/db/migrations/versions/0001_initial_schema.py:147-148`) pero el ingest solo inserta `session_id`, `app_id`, `user_agent` y `start_timestamp` (`queue.py:258-263`). La sesión termina por inactividad del lado del agente, sin reporte.

### 2.2 Evento de métricas (`RumEventBatch` → `RumEvent`)

Un `RumEvent` por page view, con TTFB y FCP en el mismo `metrics[]`. Si FCP no ocurre (por ejemplo, pestaña oculta), se envía solo TTFB; nunca se inventa un valor 0. `JS_EXCEPTION_RATE` no se envía: la tasa se calcula en query-time (`docs/architecture/ContratoIngestaRUM.md:27`).

| Campo agente | Campo servidor | Tipo / enum | Obligatorio | Regla y evidencia |
|---|---|---|---|---|
| `schemaVersion` | `schema_version` (envelope y evento) | string `"1.0"` | Sí | El envelope exige `^1\.0$` (`src/api/presentation/schemas/ingest.py:40`); el evento lo requiere la política (`src/api/domain/services/ingest_policy.py:116`). |
| `timestamp` | `timestamp` | string ISO 8601 con zona | Sí | Un timestamp sin zona se rechaza con `invalid_timestamp` (`ingest_policy.py:133-147`). El agente envía `new Date().toISOString()`. |
| `sessionId` | `session_id` | string UUID | Sí | UUID válido o `invalid_uuid` (`ingest_policy.py:206-208`). |
| `metrics[]` | `metrics` | array 1..50 | Sí | Máximo 50 métricas por evento (`ingest_policy.py:110-111,217-218`). |
| `metrics[].type` | `metrics[].type` | `"TTFB"` o `"FCP"` | Sí | Enum del servidor: TTFB, FCP, XHR_LATENCY, JS_EXCEPTION_RATE, RAGE_CLICK (`openspec/specs/openapi.yaml:945-948`). |
| `metrics[].value` | `metrics[].value` | number ≥ 0 | Sí | TTFB 0..60000 ms; FCP 0..120000 ms (`ingest_policy.py:102-108`). |
| `metrics[].unit` | `metrics[].unit` | `"ms"` | Sí | Unidad canónica por tipo (`ingest_policy.py:35-41`); el agente no usa alias (`s`, `sec`, `msec`, etc.). |
| `metrics[].timestamp` | `metrics[].timestamp` | string ISO 8601 | No | Si falta, hereda el del envelope (`src/api/domain/services/ingest_normalizer.py:125-138`). El agente la omite. |
| `metrics[].pageUrl` | `metrics[].page_url` | string saneada | No | Se persiste en `rum_metric.page_url` (`queue.py:275-277`). |
| `metrics[].metadata` | `metrics[].metadata` | objeto JSON | No | Se persiste como JSONB (`migrations/0001_initial_schema.py:175`); es el único lugar donde el agente puede añadir contexto propio. |
| `metadata.page_url` | `metadata.page_url` | string | No | Solo fallback de `metrics[].page_url` (`queue.py:275-276`). |
| `metadata.user_agent` | `user_session.user_agent` | string | No | Único campo de metadata de evento que el servidor consume (`queue.py:254-263`). |
| `application_id` | `application_id` | UUID | No | Se omite: el tenant se deriva de la API key y el payload nunca es autoridad (`openspec/specs/openapi.yaml:906-909`). |

Definiciones de medición:

| Métrica | Fórmula / API | Rango de cordura | Rating de referencia (no rechazo) |
|---|---|---|---|
| TTFB | `navigation.responseStart - navigation.requestStart`, en ms | 0..60000 | ≤800 good / ≤1800 needs-improvement / >1800 poor |
| FCP | `entry.startTime` del `first-contentful-paint`, en ms | 0..120000 | ≤1800 good / ≤3000 needs-improvement / >3000 poor |

Evidencia: TTFB `docs/research/rum-agent-deep-dive.md:556-575`; FCP `docs/research/rum-agent-deep-dive.md:588-606`; umbrales y definiciones `docs/research/frontend-observability.md:165-187`; rangos de rechazo `docs/architecture/ContratoIngestaRUM.md:22-30`. Los ratings son referencia de dashboard, nunca criterio de rechazo (`ContratoIngestaRUM.md:30`).

El servidor no define el ancla temporal de una duración. Convención v0.1: `timestamp` del envelope = `performance.timeOrigin` de la navegación; las métricas omiten timestamp y heredan ese instante.

### 2.3 Evento de excepción (`JsExceptionBatch` → `JsExceptionEvent`)

| Campo agente | Campo servidor | Tipo / enum | Obligatorio | Regla y evidencia |
|---|---|---|---|---|
| `schemaVersion` | `schema_version` | string `"1.0"` | Sí (implementación) | Requerido por Pydantic (`src/api/presentation/schemas/ingest.py:47`), aunque el OpenAPI no lo declara (ver §14). |
| `errorType` | `error_type` | string ≤ 100 | Sí | Catálogo canónico: `Error`, `TypeError`, `ReferenceError`, `RangeError`, `SyntaxError`, `EvalError`, `URIError`, `AggregateError`, `InternalError`, `UnhandledRejection`, `Other` (`ingest_policy.py:76-90`). Desconocido se agrupa en `Other` (`ingest_normalizer.py:93-100`). |
| `message` | `message` | string ≤ 2000 | Sí | Exceder el límite produce `oversized_event` (`ingest_policy.py:234-236`). |
| `stackTrace` | `stack_trace` | string ≤ 20000 | No | Exceder el límite produce `oversized_event` (`ingest_policy.py:237-241`). El agente trunca antes de enviar. |
| `sessionId` | `session_id` | string UUID | Sí | UUID válido o `invalid_uuid` (`ingest_policy.py:242-243`). |
| `timestamp` | `timestamp` | string ISO 8601 con zona | Sí | `invalid_timestamp` si falta zona (`ingest_policy.py:250-251`). |
| `application_id` | `application_id` | UUID | No | Se omite por la misma razón que en métricas. |
| `metricId` | `metric_id` | UUID | No | Se omite: el servidor genera `metric_id` al persistir (`queue.py:269`), por lo que el cliente no puede conocerlo. |

Para `errorType`, el agente usa `error.name` y, para promesas rechazadas, `"UnhandledRejection"` (`ingest_policy.py:92-97`).

### 2.4 Datos que el servidor no recibe

| Dato propuesto | Estado en el servidor | Tratamiento v0.1 |
|---|---|---|
| `viewport.width/height` | Declarado en OpenAPI (`openspec/specs/openapi.yaml:927-936`) pero no leído por el ingest ni persistido; D-03 lo retira del OpenAPI | No se envía; si se necesita, va en `metrics[].metadata` como JSONB |
| `connection.effectiveType` | Declarado en OpenAPI (`openapi.yaml:937-940`) pero no persistido; D-03 lo retira del OpenAPI | No se envía; opcional dentro de `metrics[].metadata` |
| `agentVersion` | No existe campo en el evento | Se envía en `metrics[].metadata.agent_version`; en excepciones no hay destino |
| `sampleRate` de excepción | No existe `metadata` en `JsExceptionEvent` (`ingest.py:44-54`) | No se puede reportar en v0.1; OD-03 agrega solo `sample_rate` como seguimiento de código pendiente |
| `page_url` de excepción | No existe campo en `JsExceptionEvent` | Solo se correlaciona por `session_id` y `timestamp` |
| IP del usuario | Existe `user_session.ip_address` (`migrations/0001_initial_schema.py:143`) pero el ingest nunca la escribe | El agente no la envía |

## 3. Versionado y compatibilidad

El servidor acepta exclusivamente `schema_version: "1.0"` en el envelope; cualquier otro valor produce 400 para el batch completo (`ingest.py:40-41`; `src/api/presentation/errors.py:44-53`).

| Concepto | Campo | Dónde viaja | Regla |
|---|---|---|---|
| Versión del contrato de ingesta | `schemaVersion` | `schema_version` del envelope y de cada evento | Inmutable en v0.1: siempre `"1.0"` |
| Versión del agente | `agentVersion` | `metrics[].metadata.agent_version` | Semver (`MAJOR.MINOR.PATCH`), informativa; el servidor la persiste como JSONB opaco |
| Compatibilidad hacia atrás | — | — | El agente debe tolerar que el servidor ignore campos extra (Pydantic descarta campos no declarados) y que `rejected[]` sea no vacío |
| Compatibilidad hacia adelante | — | — | Campos nuevos solo como opcionales dentro de `metrics[].metadata`; un campo obligatorio nuevo o un `metric_type` nuevo exige `schema_version` 1.1 y despliegue del servidor |
| Negociación de versión | — | — | No existe en el servidor; el agente no negocia, solo declara la versión que implementa |

Cambios incompatibles (renombrar o quitar campos, cambiar unidades canónicas, agregar valores al enum de `type`) requieren nueva versión del envelope y coordinación de despliegue. El agente nunca envía una versión superior a la configurada.

## 4. Transporte y autenticación: conflicto `sendBeacon` / `X-API-Key`

El servidor autentica la ingesta con el header `X-API-Key` (`dependencies.py:42`; `openspec/specs/openapi.yaml:1302-1307`). `navigator.sendBeacon(url, data)` no admite un parámetro de headers: por especificación del API solo recibe URL y cuerpo. Por lo tanto, `sendBeacon` no puede autenticarse contra el contrato vigente, aunque la investigación lo mencione como flush de descarga (`docs/research/rum-agent-deep-dive.md:801-805`).

| Alternativa | ¿Funciona hoy? | Límite de tamaño | Cambio requerido |
|---|---|---|---|
| `fetch(url, {method:"POST", headers:{"X-API-Key":...}, keepalive:true})` | Sí | Cuota de 64 KiB para cuerpos keepalive en vuelo (plataforma) | Ninguno |
| `sendBeacon` + key en query string | No | ~64 KiB | Servidor: leer la key de query; OpenAPI: nuevo security scheme; riesgo de key en logs y URLs |
| `sendBeacon` + `Authorization` | No | ~64 KiB | Imposible: el API no acepta headers; exigiría cambiar el esquema de auth y el servidor |
| `sendBeacon` con key en el body | No | ~64 KiB | Servidor: aceptar key en body; contradice `X-API-Key` y el contrato |
| Relay same-origin del cliente | No sin infraestructura | Sin límite práctico | El sitio debe desplegar un proxy; no es parte de v0.1 |

Decisión v0.1: `fetch` con `keepalive: true`, `mode: "cors"`, `credentials: "omit"`, `Content-Type: application/json` y header `X-API-Key`, incluso en `pagehide`/`visibilitychange`. `sendBeacon` no se usa. **OD-01 (resuelta el 23/10/2026)**: la autenticación de `sendBeacon` no se implementa en v0.1; solo se escribirá un ADR si aparece una necesidad real.

## 5. Muestreo

| Aspecto | Métricas | Excepciones |
|---|---|---|
| Tasa por defecto | 1.0 (100 %) | 1.0 (100 %) |
| Decisión | Nivel de sesión, determinista: `hash(session_id) < rate * 2^32` | Igual, para no mezclar sesiones muestreadas y no muestreadas |
| Reporte de tasa | `metrics[].metadata.sample_rate` (JSONB persistido) | No hay campo en v0.1; si la tasa baja de 1.0 no puede reportarse. OD-03 agrega `sample_rate` como seguimiento de código pendiente |
| Límite adicional | Ninguno | Máximo 20 excepciones por sesión y deduplicación por huella (`error_type` + `message` normalizado) durante 60 s |
| Sesgo | No muestrear por performance ni por página; TTFB y FCP comparten la misma decisión | No descartar excepciones por tipo ni por stack; el tope es por sesión |

El análisis debe ponderar por `1 / sample_rate`. Con tasa 1.0 no hay ponderación. El agente no muestrea métricas individuales ni recorta valores lentos: un TTFB de 9000 ms es la señal buscada (`ContratoIngestaRUM.md:30`).

## 6. Batching

| Parámetro | Métricas | Excepciones |
|---|---|---|
| Flush por cantidad | 20 eventos | 5 eventos |
| Flush por intervalo | 10 s | 5 s |
| Flush por ciclo de vida | `visibilitychange` a `hidden` y `pagehide` | Igual |
| Cap de eventos por request | 400 (margen bajo el máximo 500) | 400 |
| Cap de bytes serializados | 32 KiB (margen bajo la cuota keepalive de 64 KiB) | 32 KiB |
| Cap por evento | 50 métricas (límite del servidor) | 1 excepción |

El servidor rechaza el batch completo si `events` está fuera de 1..500 (`ingest.py:41,61`; `errors.py:44-53`). Por eso el agente nunca envía más de 400 eventos: si el buffer supera el cap, se parte en varios requests. Si un evento individual supera el cap de bytes o el cap de métricas, se descarta y se incrementa un contador local; no se envía un batch inválido. La cola en memoria se acota a 500 eventos y descarta los más antiguos ante desborde. Los valores de esta tabla son política del agente: el servidor solo fija el máximo de 500 eventos y 50 métricas por evento.

## 7. Reintentos y resiliencia

| Respuesta / condición | ¿Reintentar? | Acción del agente |
|---|---|---|
| 202 | No | Éxito; procesar `rejected[]`: cada evento rechazado es permanente (`invalid_*`, `oversized_event`) y se descarta con contador |
| 400 `schema_validation_error` | No | Bug de envelope o límite excedido; descartar el batch y registrar una vez |
| 401 `invalid_api_key` | No | Detener el agente en esta página (circuito abierto); no reintentar |
| 403 `app_inactive` | No | Detener el agente en esta página; no reintentar |
| 429 | No en v0.1 | Código retirado del contrato hasta implementar rate limit (D-04); si el servidor lo devolviera, respetar `Retry-After` |
| 503 `queue_full` | Sí | Backoff y reintento; es backpressure de la cola (`docs/architecture/PipelineIngestaRUM.md:100-107`) |
| Otro 5xx, timeout o error de red | Sí | Backoff y reintento |

Política: máximo 3 intentos por batch, backoff exponencial 1 s, 2 s y 4 s con jitter de ±20 %. Agotados los intentos, el batch se descarta y se cuenta. No hay persistencia local de payloads (ver §9): un `pagehide` sin `fetch` disponible pierde el buffer. El servidor no ofrece idempotencia por `batch_id` (`PipelineIngestaRUM.md:121-132`), por lo que un timeout después de un 202 puede duplicar eventos; v0.1 acepta semántica at-least-once y lo registra como OD-05.

## 8. CORS

Estado real del servidor: `allow_origins=["*"]`, `allow_credentials=False`, `allow_methods=["*"]` y `allow_headers=["*"]` (`src/api/main.py:77-88`; `allow_credentials` corregido el 23/10/2026 — D-05). El wildcard es válido porque no hay credenciales CORS. `Access-Control-Max-Age` no se configura y toma el default de 600 s del middleware instalado.

Consecuencia: el agente ya puede enviar desde un sitio de terceros. El preflight se dispara por `Content-Type: application/json` y por `X-API-Key`; cachear el preflight es clave para no duplicar requests por cada flush.

Requisito de contrato para cuando se restrinja:

| Elemento | Valor requerido |
|---|---|
| Métodos | `POST`, `OPTIONS` |
| Headers permitidos | `Content-Type`, `X-API-Key` |
| Origen | Allowlist por aplicación, no `*` |
| Credenciales | Deshabilitadas (`credentials: "omit"`); no se usan cookies |
| `Access-Control-Max-Age` | 86400 s recomendado |

El origen wildcard se acepta en v0.1 porque `allow_credentials=False`. El allowlist por aplicación queda en backlog post-v1 con ADR (OD-02). La API key es, por diseño, visible en el navegador (OD-06); el rate limit también queda post-v1.

## 9. Privacidad

| Dato | Política |
|---|---|
| `session_id` | Permitido: UUID opaco, sin user ID ni email |
| URL | Permitida solo sin query ni fragmento; segmentos numéricos o UUID reemplazados por `{id}`; máximo 2048 caracteres (`docs/research/rum-agent-deep-dive.md:888,898-904`) |
| `user_agent` | Permitido y truncado a 256 caracteres; el servidor lo persiste en `user_session` (`queue.py:254-262`) |
| IP | Prohibida: el agente no la envía y el ingest no la escribe (`migrations/0001_initial_schema.py:143`) |
| Cookies y `localStorage` | Prohibido leerlos o enviarlos; `credentials: "omit"` |
| PII en `message`/`stack_trace` | Prohibida: se redactan emails, tokens y parámetros de query antes de truncar a 2000/20000 |
| Viewport / conexión | Opcionales, solo dentro de `metrics[].metadata`; nunca como huella adicional |
| Consentimiento | Flag de configuración; sin consentimiento no se inicializa el agente |
| Do Not Track / GPC | Si `navigator.doNotTrack === "1"` o `navigator.globalPrivacyControl === true`, el agente no recolecta |
| Opt-out | Clave `intellops-optout` en `localStorage`; si existe, no se recolecta (`rum-agent-deep-dive.md:890`) |
| Retención del agente | Solo memoria; `sessionStorage` guarda `session_id` y opt-out. No se persisten payloads ni stack traces |

La retención del lado del servidor (`< 90 días` en la investigación, `rum-agent-deep-dive.md:891`) no está definida en el código del servidor; queda fuera de este contrato.

## 10. Presupuesto de bundle

| Regla | Valor |
|---|---|
| Tope duro | 30 KB gzip (`docs/business/issues-fases-abc.md:136,178`) |
| Objetivo de ingeniería | 20 KB gzip (`docs/research/rum-agent-deep-dive.md:1131`) |
| Dependencias de runtime | Ninguna; sin `web-vitals` ni SDK de OTel |
| Polyfills / transpilación | Ninguno; baseline de navegadores modernos |
| APIs permitidas | `PerformanceObserver`, `PerformanceNavigationTiming`, `fetch` con `keepalive`, `sessionStorage`, `crypto.randomUUID` (con fallback manual si no hay contexto seguro) |
| Formato de distribución | Un archivo minificado (IIFE o ESM), sin source maps publicados |
| Verificación | `gzip -c dist/rum.js > /tmp/rum.js.gz && wc -c < /tmp/rum.js.gz` en CI, con fallo si supera 30720 bytes |

## 11. Criterios de aceptación

| ID | Criterio verificable |
|---|---|
| AC-01 | El contrato v0.1 está versionado en `docs/architecture/ContratoAgenteRUM.md` y aprobado por QA |
| AC-02 | Un page view genera un `RumEvent` con TTFB y FCP, o solo TTFB si FCP no ocurrió |
| AC-03 | TTFB usa `responseStart - requestStart` y FCP usa `entry.startTime`; ambos en ms |
| AC-04 | Todo error no manejado genera un `JsExceptionEvent` con `error_type` canónico, `message` ≤ 2000 y `stack_trace` ≤ 20000 |
| AC-05 | Todos los envelopes y eventos llevan `schema_version: "1.0"` |
| AC-06 | El agente envía con `fetch keepalive` y `X-API-Key`; no usa `sendBeacon` |
| AC-07 | El preflight desde un origen de terceros responde 200 y permite `X-API-Key` |
| AC-08 | Muestreo, batching y reintentos siguen las tablas §5, §6 y §7 |
| AC-09 | El payload no contiene query strings, cookies, IP ni PII; DNT y opt-out detienen la recolección |
| AC-10 | El bundle minificado pesa ≤ 30 KB gzip |
| AC-11 | El agente no persiste payloads ni datos sensibles en el navegador |
| AC-12 | Existen demo HTML y tests del agente que cubren TTFB, FCP, error y reintento |

## 12. Checklist de revisión de QA (Santiago)

- [ ] Verificar que cada campo enviado existe en `openapi.yaml` o en `schemas/ingest.py`, sin campos inventados.
- [ ] Ejecutar un page view de prueba y confirmar un `RumEvent` con `metrics[].type` TTFB y FCP.
- [ ] Confirmar que un FCP ausente no se envía como `0`.
- [ ] Provocar un `TypeError` y una promesa rechazada; confirmar `error_type` y longitudes.
- [ ] Enviar `schema_version: "1.1"` y confirmar 400 del batch completo.
- [ ] Enviar una métrica con `value` fuera de rango y confirmar 202 con `rejected[]` y `reason: invalid_range`.
- [ ] Confirmar que el request lleva `X-API-Key` y que `sendBeacon` no se usa.
- [ ] Simular 503 y verificar 3 intentos con backoff; simular 401 y verificar que no reintenta.
- [ ] Revisar el payload y comprobar ausencia de query strings, cookies, IP y PII.
- [ ] Medir el bundle con gzip y confirmar ≤ 30 KB.

## 13. Decisiones resueltas (23/10/2026)

| ID | Decisión | Seguimiento |
|---|---|---|
| OD-01 | La autenticación de `sendBeacon` no se implementa en v0.1. El transporte es `fetch` con `keepalive: true`. | Ninguno inmediato: solo se escribe ADR si aparece una necesidad real. |
| OD-02 | El allowlist CORS por aplicación queda en backlog post-v1 con ADR. Hoy `allow_origins=["*"]` con `allow_credentials=False` es válido. | Backlog post-v1 con ADR de hardening. |
| OD-03 | Se agrega únicamente `sample_rate` a `JsExceptionEvent`; `page_url` y `agent_version` quedan diferidos. | **Seguimiento de código pendiente**: no se implementa en esta edición. |
| OD-04 | Se valida el valor de `schema_version` por evento con `^1\.0$`. Cierra D-02. | **Seguimiento de código pendiente**: no se implementa en esta edición. |
| OD-05 | La idempotencia de reintentos queda en backlog con ADR. | Backlog con ADR de idempotencia. |
| OD-06 | La exposición de la API key en el navegador se acepta por diseño; el rate limit queda post-v1. | Backlog post-v1; sin cambio en v0.1. |

## 14. Discrepancias entre contrato, OpenAPI e implementación

| ID | Discrepancia | Evidencia |
|---|---|---|
| D-01 | **Corregido (23/10/2026)**: `schema_version` se declara requerido en `JsExceptionEvent` con enum `1.0`, alineado con `RumEvent`. OD-04 resuelve la validación del valor con seguimiento de código pendiente | `openspec/specs/openapi.yaml`; `tests/test_contract.py::test_oas12_js_exception_event_declares_schema_version` |
| D-02 | **Resuelto (23/10/2026) por OD-04**: se valida el valor de `schema_version` por evento con `^1\.0$`. Seguimiento de código pendiente | `openapi.yaml:894-897` vs `ingest_policy.py:201-223` |
| D-03 | **Resuelto (23/10/2026)**: se quitan `viewport` y `connection` del OpenAPI porque el ingest no los persiste. Seguimiento de código pendiente | `openapi.yaml:917-940` vs `queue.py:254-277` |
| D-04 | **Resuelto (23/10/2026)**: se quita el 429 del contrato hasta implementar rate limit; queda registrado en OD-06. Seguimiento de código pendiente | `openapi.yaml:68-73,118-123` |
| D-05 | **Corregido (23/10/2026)**: `allow_credentials=False`, por lo que el wildcard de orígenes es válido en navegadores. El allowlist por aplicación queda en backlog post-v1 (OD-02) | `src/api/main.py:77-88`; `tests/test_cors.py` |
| D-06 | **Resuelto (23/10/2026)**: se acepta `metric_id` nulo en v1; la correlación excepción→métrica queda post-v1 | `queue.py:269`; `openapi.yaml:1007-1010` |

D-01 y D-05 se corrigieron el 23/10/2026 con test de regresión. D-02, D-03, D-04 y D-06 quedaron resueltas el 23/10/2026: D-02 por OD-04, D-03 y D-04 con seguimiento de código pendiente, y D-06 como aceptación de `metric_id` nulo en v1.

## 15. Fuentes

- `openspec/specs/openapi.yaml` — endpoints, schemas, security scheme.
- `openspec/specs/asyncapi.yaml` — contratos asíncronos; no define canal de ingesta RUM.
- `src/api/presentation/schemas/ingest.py` — schemas Pydantic de ingesta.
- `src/api/presentation/dependencies.py` — `require_api_key` y `X-API-Key`.
- `src/api/presentation/routers/telemetry.py` — rutas y códigos de respuesta.
- `src/api/presentation/errors.py` — traducción 422→400 en `/telemetry/*`.
- `src/api/main.py` — configuración CORS.
- `src/api/domain/services/ingest_policy.py` — límites, rangos y validación.
- `src/api/domain/services/ingest_normalizer.py` — normalización del servidor.
- `src/api/domain/entities/rum_metric.py` y `js_exception.py` — campos persistidos.
- `src/api/infrastructure/db/migrations/versions/0001_initial_schema.py` — DDL y catálogo.
- `src/api/infrastructure/ingest/queue.py` — mapeo de metadata y generación de IDs.
- `docs/architecture/ContratoIngestaRUM.md` y `docs/architecture/PipelineIngestaRUM.md`.
- `docs/business/issues-fases-abc.md` — A.3, B.1 y B.7.
- `docs/research/rum-agent-deep-dive.md` y `docs/research/frontend-observability.md` — TTFB, FCP, privacidad y bundle.
- `docs/adr/0008-ml-dataset-http-pull-series-anchor.md` — dataset por HTTP.
- `docs/adr/0010-arquitectura-de-4-contenedores.md` — el agente no es un contenedor del MVP.
