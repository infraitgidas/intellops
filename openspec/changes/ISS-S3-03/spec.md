# SPEC — ISS-S3-03: Gestión de sesiones (lectura app-scoped de `user_session`)

**Tipo**: Delta spec. **Cambio**: ISS-S3-03 (GitHub #42). **Base**: `proposal.md`, ADR-0002, ADR-0003, ADR-0011, `docs/architecture/ContratoAgenteRUM.md` §2.1 y §9, `openspec/specs/database/ddl_v1.0.sql:131-140`.
**Alcance**: lectura de sesiones por aplicación y política de campos de `user_session`. Sin escritura, sin DDL y sin cambios en la ingesta ni en el agente.

## Capabilities

- **Nuevas**: `session-read`
- **Modificadas**: `openapi`

---

## 1. session-read (Nueva)

## ADDED Requirements

### Requirement: SES-1 (listado app-scoped)

`GET /sessions` MUST exigir X-API-Key y MUST devolver solo sesiones cuyo `app_id` sea el de la aplicación autenticada. El tenant MUST derivarse exclusivamente de la key; el request MUST NOT aceptar un parámetro de aplicación. El listado MUST ordenarse por `start_timestamp` descendente, desempatando por `session_id` descendente.

#### Scenario: Aislamiento por key

- GIVEN sesiones de la app A y de la app B en la ventana
- WHEN A llama a `GET /sessions` con su key
- THEN la respuesta contiene solo las sesiones de A, de la más nueva a la más vieja

### Requirement: SES-2 (ventana y límite)

El listado MUST filtrar por `start_timestamp` en `[start, end)`. Sin `end`, MUST usar el instante actual; sin `start`, `end - 24 h`. Sin `limit`, MUST usar 50. MUST responder 422 `invalid_query_range` sin ejecutar la consulta si `start >= end`, si la ventana supera 7 días o si `limit` sale de 1..500. El `limit` MUST NOT recortarse en silencio.

#### Scenario: Ventana default

- GIVEN una sesión iniciada hace 1 h y otra hace 2 días
- WHEN se llama a `GET /sessions` sin parámetros
- THEN solo aparece la de hace 1 h

#### Scenario: Límite fuera de rango

- GIVEN `limit=0` o `limit=501`
- WHEN se llama a `GET /sessions`
- THEN la respuesta es 422

#### Scenario: Ventana inválida

- GIVEN `start >= end` o una ventana de 8 días
- WHEN se llama a `GET /sessions`
- THEN la respuesta es 422 con `error.code = invalid_query_range`

### Requirement: SES-3 (detalle sin fuga entre tenants)

`GET /sessions/{session_id}` MUST filtrar por `session_id` AND `app_id`, no solo por la clave primaria. Una sesión inexistente o de otra aplicación MUST responder 404 `session_not_found` con el mismo cuerpo en ambos casos. MUST NOT responder 403 por una sesión ajena. Un `session_id` que no es UUID MUST responder 422.

#### Scenario: Sesión de otro tenant

- GIVEN la sesión S de la app A
- WHEN la app B pide `GET /sessions/S`
- THEN la respuesta es 404 `session_not_found`, idéntica a la de un UUID inexistente

#### Scenario: Sesión propia

- GIVEN la sesión S de la app A
- WHEN A pide `GET /sessions/S`
- THEN la respuesta es 200 con la misma forma que un elemento del listado

### Requirement: SES-4 (forma de la respuesta y actividad observada)

Cada sesión MUST exponer exactamente `session_id`, `application_id`, `start_timestamp`, `last_activity_at`, `user_agent`, `metric_count` y `exception_count`:

- `metric_count` y `exception_count` MUST ser la cantidad de filas `rum_metric` y `js_exception` de la sesión.
- `last_activity_at` MUST ser el timestamp más reciente entre ambas tablas, o null si la sesión no tiene filas.
- La respuesta MUST NOT incluir `user_id`, `ip_address`, `os_version`, `end_timestamp` ni `duration_ms`.

#### Scenario: Actividad entre tablas

- GIVEN una sesión con métricas hasta t+10 s y una excepción en t+40 s
- WHEN se la lista
- THEN `metric_count = 2`, `exception_count = 1` y `last_activity_at = t+40 s`

#### Scenario: Sesión sin actividad

- GIVEN una sesión sin métricas ni excepciones
- WHEN se la lista
- THEN los conteos son 0 y `last_activity_at` es null

### Requirement: SES-5 (política de campos de la ingesta)

La ingesta MUST dejar `user_id`, `ip_address`, `os_version`, `end_timestamp` y `duration_ms` en NULL, y MUST NOT tomarlos del payload aunque `metadata` traiga claves con esos nombres. MUST NOT existir `POST /sessions` ni `POST /sessions/{id}/finish`.

#### Scenario: Payload con claves de identidad

- GIVEN un evento RUM con `metadata.user_id`, `metadata.ip_address` y `metadata.os_version`
- WHEN el worker lo persiste
- THEN la sesión aparece en `GET /sessions` y esas columnas, junto con `end_timestamp` y `duration_ms`, quedan NULL

### Requirement: SES-6 (autenticación)

Ambos paths MUST responder 401 `invalid_api_key` con `WWW-Authenticate: ApiKey` sin key o con key inválida, y 403 `app_inactive` con la key de una aplicación inactiva. Es el mismo guard que `/metrics/*`.

---

## 2. openapi (Modificada)

### Requirement: OAS-S303

`openapi.yaml` MUST declarar `GET /sessions` (`listSessions`, respuestas 200/401/403/422, parámetros `start`, `end` y `limit` 1..500 con default 50) y `GET /sessions/{session_id}` (`getSession`, respuestas 200/401/403/404/422), ambos con `security: [apiKey]` y devolviendo el schema `Session` (SES-4). MUST NOT declarar métodos de escritura en `/sessions*` ni paths `/finish`.

---

## Límites de recursos

- Una sentencia SQL por request, sobre índices existentes. La respuesta tiene como máximo 500 filas.
- Latencia objetivo < 500 ms con la ventana default sobre el volumen del piloto. CPU-only, sin memoria adicional relevante.

## Criterios ML

No aplica: el cambio no entrena ni evalúa modelos.
