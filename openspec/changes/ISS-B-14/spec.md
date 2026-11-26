# SPEC — ISS-B-14: Motor determinístico de reglas de umbral

**Tipo**: Delta spec. **Cambio**: B.14 (GitHub #74). **Base**: `proposal.md`, `design.md`,
ADR-0010, ADR-0012, D1.
**Alcance**: configuración de umbrales por aplicación y por métrica, evaluación periódica y
creación de `ALERT` en Pending. El despacho (Sent/Failed, `sent_at`, canal) es B.10.

## Capabilities

- **Nuevas**: `alert-rules`, `alert-engine`.
- **Modificadas**: `database`, `contract`.

---

## 1. alert-rules (Nueva)

### Requirement: DB-RULE-1 (tabla `alert_rule`)

La migración `0008` MUST crear `alert_rule` con: `rule_id UUID` PK, `application_id UUID` NOT NULL
FK a `application` ON DELETE RESTRICT, `metric_type_id SMALLINT` NOT NULL FK a `metric_type` ON
DELETE RESTRICT, `comparison TEXT` NOT NULL CHECK en (`gt`, `lt`), `threshold NUMERIC` NOT NULL,
`window_minutes INTEGER` NOT NULL CHECK entre 1 y 10080, `min_samples INTEGER` NOT NULL CHECK
≥ 1, `cooldown_minutes INTEGER` NOT NULL CHECK ≥ 1, `severity TEXT` NOT NULL CHECK en (`low`,
`medium`, `high`, `critical`), `is_active BOOLEAN` NOT NULL DEFAULT TRUE y `created_at TIMESTAMPTZ`
NOT NULL DEFAULT `now()`.

MUST crear `uq_alert_rule_key (application_id, metric_type_id, comparison, threshold)` y
`idx_alert_rule_app_active (application_id, is_active)`.

`0008` MUST declarar `down_revision = "0007"`: un solo head en Alembic.

#### Scenario: Regla por aplicación y por métrica

- GIVEN dos aplicaciones con reglas sobre `TTFB`
- WHEN se configuran umbrales distintos
- THEN cada fila de `alert_rule` guarda su `application_id` y su `threshold`

#### Scenario: Umbral inválido rechazado por el esquema

- GIVEN una regla con `comparison = 'ge'`
- WHEN se intenta insertar
- THEN PostgreSQL rechaza la fila por `CHECK`

### Requirement: DB-RULE-2 (columnas de regla en `alert`)

La migración `0008` MUST agregar a `alert`: `rule_id UUID` nullable FK a `alert_rule` ON DELETE
RESTRICT, `threshold NUMERIC` nullable y `observed_value NUMERIC` nullable, e índices
`idx_alert_rule_created (rule_id, created_at DESC)`.

MUST NOT tocar `status_id`, `severity`, `application_id`, `created_at`, `recipient`, `channel_id`,
`sent_at` ni `anomaly_id`.
El downgrade de `0008` MUST abortar con un mensaje claro si `alert` tiene filas con `rule_id` no
nulo: `rule_id`, `threshold` y `observed_value` no se pueden derivar.

#### Scenario: Alerta de ML sin regla

- GIVEN una alerta con `anomaly_id` no nulo (M3)
- WHEN se lee
- THEN `rule_id`, `threshold` y `observed_value` son NULL

### Requirement: OAS-B14-1 (`POST /alerts/config`)

`POST /alerts/config` MUST exigir un JWT con rol `Admin` y MUST aceptar
`application_id`, `metric_type_id`, `comparison` (`gt`/`lt`), `threshold`, `window_minutes`,
`min_samples`, `cooldown_minutes`, `severity` e `is_active` (opcional, default `true`; sin ese
campo una regla no se podría desactivar por la API).

MUST validar que `application_id` exista (404 `application_not_found`) y que `metric_type_id`
exista en el catálogo (404 `metric_type_not_found`), antes de escribir.
MUST validar `threshold` finito, `window_minutes` 1..10080, `min_samples` ≥ 1, `cooldown_minutes`
≥ 1, `comparison` y `severity` en sus dominios: una violación responde 422 `invalid_alert_rule`
con `ErrorResponse`, sin escribir.
Si ya existe una regla con la misma (`application_id`, `metric_type_id`, `comparison`,
`threshold`), MUST actualizar `window_minutes`, `min_samples`, `cooldown_minutes`, `severity` e
`is_active` y responder 200 con la regla resultante, en vez de crear un duplicado.

#### Scenario: Idempotencia de la configuración

- GIVEN una regla de `TTFB` `gt 800` para la aplicación A
- WHEN se repite el POST con `cooldown_minutes` distinto
- THEN la respuesta es 200, hay UNA sola fila y su `cooldown_minutes` quedó actualizado

#### Scenario: Severidad fuera del dominio

- GIVEN un POST con `severity = "urgent"`
- WHEN se procesa
- THEN la respuesta es 422 `invalid_alert_rule` y `alert_rule` no gana filas

### Requirement: OAS-B14-2 (`GET /alerts/config`)

`GET /alerts/config?application_id=<uuid>` MUST exigir un JWT con rol `Admin` o `Researcher` y
MUST devolver las reglas de esa aplicación, activas e inactivas, ordenadas por `created_at`
ascendente. Una aplicación inexistente MUST responder 404 `application_not_found`.

#### Scenario: Reglas de otra aplicación no se mezclan

- GIVEN reglas de las aplicaciones A y B
- WHEN se listan las de A
- THEN solo aparecen las de A

---

## 2. alert-engine (Nueva)

### Requirement: AR-1 (ventana y muestras)

Cada ciclo MUST evaluar cada regla con `is_active = true` sobre la ventana
`[now() - window_minutes, now())`, y MUST contar las muestras de esa ventana.

#### Scenario: Ventana vacía

- GIVEN una regla con `min_samples = 1` y una aplicación sin métricas en la ventana
- WHEN corre el ciclo
- THEN no se crea ninguna alerta y la regla cuenta como `insufficient`

### Requirement: AR-2 (agregación por tipo de métrica)

La agregación MUST derivarse de `metric_type`:

- `TTFB`, `FCP`, `XHR_LATENCY` y `RAGE_CLICK` por `percentile_cont(0.95)` de `rum_metric.value`;
- `AVAILABILITY` por `AVG(rum_metric.value)`;
- `JS_EXCEPTION_RATE` por `count(js_exception) / count(user_session)` en la ventana.

MUST usar las filas del tenant de la regla y MUST limitarse a la ventana.

#### Scenario: Disponibilidad medida por la sonda

- GIVEN 4 corridas de sonda en la ventana con valores 1, 1, 1, 0
- WHEN se agrega `AVAILABILITY`
- THEN el valor observado es 0,75

#### Scenario: Aislamiento por tenant

- GIVEN métricas de las aplicaciones A y B en la ventana
- WHEN se evalúa una regla de A
- THEN el valor observado solo usa las filas de A

### Requirement: AR-3 (comparación inclusiva)

`gt` MUST disparar cuando `observado >= threshold`; `lt` MUST disparar cuando
`observado <= threshold`. La igualdad MUST disparar en ambos sentidos.

#### Scenario: Valor exactamente en el umbral

- GIVEN una regla `gt 800` y un observado de 800
- WHEN se evalúa
- THEN la regla dispara

#### Scenario: Justo debajo del umbral

- GIVEN una regla `gt 800` y un observado de 799,9
- WHEN se evalúa
- THEN la regla no dispara

#### Scenario: Disponibilidad justo en el piso

- GIVEN una regla `lt 0.99` y un uptime de 0,99
- WHEN se evalúa
- THEN la regla dispara

### Requirement: AR-4 (datos insuficientes)

Si `samples < min_samples`, la regla MUST NOT crear alerta y MUST NOT fallar el ciclo; cuenta
como `insufficient`. `samples = 0` cae en este caso.

#### Scenario: Una sola muestra con mínimo dos

- GIVEN una regla con `min_samples = 2` y una sola muestra en la ventana
- WHEN corre el ciclo
- THEN no se crea alerta y el resumen cuenta un `insufficient`

### Requirement: AR-5 (ALERT en Pending)

Cuando una regla dispara, el motor MUST insertar una fila en `alert` con `application_id` de la
regla, `severity` de la regla, `message` determinístico, `status_id` = catálogo `Pending`,
`rule_id`, `threshold` y `observed_value` de la evaluación, y MUST dejar `recipient`,
`channel_id`, `sent_at` y `anomaly_id` en NULL.

El `message` MUST nombrar la métrica, el valor observado, el umbral y la ventana.

#### Scenario: Alerta creada y legible

- GIVEN una regla `TTFB gt 800` con ventana 15 min y un observado de 912,4
- WHEN dispara
- THEN existe una alerta Pending de esa aplicación con `rule_id`, `threshold = 800`,
  `observed_value = 912,4`, sin canal ni destinatario, y su mensaje menciona `TTFB`, `912,4`,
  `800` y `15`

### Requirement: AR-6 (cooldown)

Si existe una alerta con la misma `rule_id` y `created_at` posterior a
`now() - cooldown_minutes`, el motor MUST NOT crear otra y MUST contar la regla como `cooled`.
Una alerta fuera del cooldown MUST NOT bloquear una nueva.

#### Scenario: Segunda corrida dentro del cooldown

- GIVEN una alerta de la regla R creada hace 1 minuto y un cooldown de 15
- WHEN el ciclo vuelve a disparar R
- THEN no se crea una segunda alerta

#### Scenario: Cooldown vencido

- GIVEN una alerta de la regla R creada hace 16 minutos y un cooldown de 15
- WHEN el ciclo dispara R
- THEN se crea una nueva alerta

---

## 3. Contrato con B.10

### Requirement: CT-B14-B10 (fila despachable)

Toda alerta creada por el motor MUST ser despachable por el dispatcher de B.10 sin consultar
`alert_rule`: `application_id`, `severity`, `message`, `status` = `pending` son suficientes para
decidir canal y texto. Un test de contrato MUST fijar esa forma y MUST verificar que
`GET /alerts` la expone con `status: pending` y `anomaly_id`, `channel` y `sent_at` en NULL.

#### Scenario: La alerta del motor aparece en la API de lectura

- GIVEN una alerta creada por el motor
- WHEN se consulta `GET /alerts` con la key de la aplicación
- THEN aparece una alerta `pending` con la severidad y el mensaje del motor
