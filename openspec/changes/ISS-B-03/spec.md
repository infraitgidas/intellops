# SPEC — ISS-B-03: API de lectura de series, anomalías y alertas

**Tipo**: Delta spec. **Cambio**: B.3 (GitHub #68). **Base**: `proposal.md`, ADR-0003, ADR-0008, ADR-0012, TQ-2.
**Alcance**: lectura app-scoped de anomalías y alertas, y forma de la tabla `alert` para la v1. Las series ya cumplen el criterio desde ISS-S3-01 y B.13.

## Capabilities

- **Nuevas**: `anomalies-read`, `alerts-read`
- **Modificadas**: `database`, `contract`

---

## 1. anomalies-read (Nueva)

### Requirement: RD-1 (listado de anomalías app-scoped)

`GET /anomalies` MUST exigir `X-API-Key` y MUST devolver solo anomalías cuyo `application_id` es la aplicación de la key, detectadas en `[start, end)`, ordenadas por `detected_at` descendente (desempate por `anomaly_id`), como máximo `limit`. El filtro opcional `metric_type` MUST dejar solo ese tipo.

#### Scenario: Aislamiento por tenant

- GIVEN anomalías de las aplicaciones A y B
- WHEN se lista con la key de A
- THEN solo aparecen las de A, de la más nueva a la más vieja

#### Scenario: Sin detector (v1)

- GIVEN una aplicación sin anomalías
- WHEN se lista
- THEN la respuesta es 200 `[]`

### Requirement: RD-2 (detalle de anomalía)

`GET /anomalies/{anomaly_id}` MUST filtrar por `anomaly_id` AND `application_id`. Una anomalía de otra aplicación MUST responder lo mismo que una inexistente: 404 `anomaly_not_found`.

#### Scenario: Anomalía de otro tenant

- GIVEN una anomalía de A
- WHEN se pide con la key de B
- THEN la respuesta es 404 `anomaly_not_found`, idéntica a la de un id inexistente

## 2. alerts-read (Nueva)

### Requirement: RD-3 (listado de alertas app-scoped)

`GET /alerts` MUST exigir `X-API-Key` y MUST devolver solo alertas de la aplicación de la key, creadas en `[start, end)`, ordenadas por `created_at` descendente (desempate por `alert_id`), como máximo `limit`. El filtro opcional `status` (`pending`, `sent`, `failed`) MUST dejar solo ese estado.

`status` y `channel` MUST exponerse en minúsculas. `channel` y `sent_at` MUST ser null mientras la alerta no se despachó, y `anomaly_id` MUST ser null en las alertas sin anomalía. La respuesta MUST NOT incluir `recipient`.

#### Scenario: Alerta de umbral pendiente

- GIVEN una alerta en Pending, sin anomalía ni canal
- WHEN se lista
- THEN aparece con `status: pending`, `anomaly_id`, `channel` y `sent_at` en null, y sin `recipient`

## 3. Límites comunes (anomalies-read, alerts-read)

### Requirement: RD-4 (ventana y limit acotados)

Los listados MUST usar una ventana default de 24 h hasta ahora, MUST rechazar `start >= end` y ventanas de más de 7 días, y MUST aceptar `limit` de 1 a 500 (default 50) sin clamp silencioso. `GET /alerts` MUST rechazar un `status` fuera del catálogo. Toda violación MUST responder 422 `invalid_query_range` con `ErrorResponse {error: {code, message}}`, sin ejecutar la consulta. Los datetimes naive MUST asumirse UTC.

#### Scenario: limit fuera de rango

- GIVEN `limit=501`
- WHEN se lista
- THEN la respuesta es 422 `invalid_query_range` y el mensaje nombra el valor rechazado

### Requirement: RD-5 (autenticación)

Sin key, o con una key inválida, los endpoints MUST responder 401 `invalid_api_key` con `WWW-Authenticate: ApiKey`. Con la key de una aplicación inactiva MUST responder 403 `app_inactive`.

## 4. database (Modificada)

### Requirement: DB-ALERT-1 (alerta independiente, migración 0007)

Después de la `0007`, `alert` MUST tener `application_id UUID NOT NULL` (`fk_alert_application`, ON DELETE RESTRICT), `severity TEXT NOT NULL` con `ck_alert_severity` (`low`, `medium`, `high`, `critical`) y `created_at TIMESTAMPTZ NOT NULL DEFAULT now()`. `anomaly_id`, `recipient` y `channel_id` MUST aceptar NULL. MUST existir `idx_alert_app_created (application_id, created_at DESC)` e `idx_anomaly_app_timestamp (application_id, timestamp DESC)`.

#### Scenario: Severidad desconocida

- GIVEN una alerta con `severity = 'urgent'`
- WHEN se inserta
- THEN falla con `ck_alert_severity`

### Requirement: DB-ALERT-2 (guarda de tabla vacía)

Upgrade y downgrade de la `0007` MUST abortar con un `RuntimeError` claro si `alert` tiene filas, y la revisión MUST quedar donde estaba. Con `alert` vacía, el downgrade MUST restaurar la forma de 0001, NOT NULL incluidos.

### Requirement: DB-ALERT-3 (DDL sincronizado)

`openspec/specs/database/ddl_v1.0.sql` MUST reflejar el estado final de `alert` y el índice nuevo de `anomaly`.

## 5. contract (Modificada)

### Requirement: OAS-B3-1 (paths y schemas)

El OpenAPI MUST declarar `security: [apiKey]`, los parámetros acotados y las respuestas 200/401/403/422 (y 404 en el detalle) de los tres endpoints. Los schemas `Anomaly` y `Alert` MUST declarar exactamente los campos de `AnomalyOut` y `AlertOut`. El path del detalle MUST ser `/anomalies/{anomaly_id}`. El subset de schemathesis MUST incluir los tres endpoints y excluir `/alerts/config` y `/alerts/{id}/ack`, que no están implementados.

---

## Límites de recursos

Cada consulta es una sola sentencia acotada por tenant, ventana y `limit` (máximo 500 filas), sobre los índices de la `0007`. CPU-only.

## Criterios ML

No aplica: no se entrenan ni evalúan modelos. El schema `Anomaly` refleja lo que escribe el detector (ADR-0008).
