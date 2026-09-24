# SPEC — ISS-S2-02: Aplicaciones y credenciales de ingesta

**Tipo**: Delta spec. **Cambio**: ISS-S2-02 (GitHub #36). **Base**: proposal r1 (decisiones a–g), research r3 (claims C1–C28), `openspec/specs/openapi.yaml` (openapi 3.1.0; `api_token_hash` en `required` de `ApplicationRead`), `openspec/specs/database/ddl_v1.0.sql`, migración 0002 (ISS-S2-01).
**Alcance**: emisión/rotación/revocación de API key, `is_active`, guard `require_api_key`, contrato OpenAPI (ADR-16), migración 0003, redacción de logs. Strict TDD (config.yaml apply.tdd:true): cada escenario Given/When/Then se convierte en test red antes de implementar.

## Capabilities

- **Nuevas**: `app-credentials`, `ingest-auth`
- **Modificadas**: `applications-api`, `openapi` (migración 0003 + sync ddl_v1.0.sql)

---

## 1. app-credentials (Nueva)

### Requisitos funcionales

### Requirement: CRED-1
POST /applications/{id}/api-key (bearer; SOLO Admin) DEBE emitir una API key con prefijo `ilp_` generada con CSPRNG (32 bytes, ≥256 bits de entropía) y persistir SOLO su hash SHA-256 hex (64 chars) en `application.api_token_hash`; DEBE responder 201 con `{api_key, hint}` (show-once). El plaintext NUNCA se persiste ni se puede recuperar posteriormente.

### Requirement: CRED-2
POST/DELETE /applications/{id}/api-key sobre una aplicación inexistente DEBEN responder 404 con ErrorResponse.

### Requirement: CRED-3
POST /applications/{id}/api-key sobre una aplicación con key activa DEBE responder 409 con ErrorResponse y NO alterar la key vigente: la rotación es un flujo explícito de dos pasos (revocar → regenerar), sin ventana de overlap automática.

### Requirement: CRED-4
DELETE /applications/{id}/api-key (bearer; SOLO Admin) DEBE revocar la key de forma inmediata y fail-closed (la key deja de validar al instante): 204 con `api_token_hash` = NULL; idempotente (204 aunque no haya key); materializa la revocación explícita de la decisión (d).

### Requirement: CRED-5
La key en claro DEBE mostrarse una sola vez (solo en el 201 de emisión); GET/PUT /applications y el resto de las respuestas NUNCA DEBEN exponer la key ni su hash (el hash es dato interno).

### Escenarios

#### Scenario: Emisión show-once
- GIVEN bearer de Admin y una aplicación sin key
- WHEN POST /applications/{id}/api-key
- THEN 201 con `{api_key: "ilp_...", hint}` y el plaintext no se persiste
- AND `application.api_token_hash` = SHA-256 hex de la key (64 chars)
- AND GET /applications/{id} NO devuelve la key ni el hash

#### Scenario: Emisión sobre aplicación inexistente
- GIVEN un id UUID sin aplicación
- WHEN POST /applications/{id}/api-key
- THEN 404 con ErrorResponse

#### Scenario: Regenerar con key activa
- GIVEN una aplicación con `api_token_hash` no NULL
- WHEN POST /applications/{id}/api-key
- THEN 409 con ErrorResponse y la key previa sigue validando

#### Scenario: Rotación en dos pasos
- GIVEN una aplicación con key activa
- WHEN DELETE /applications/{id}/api-key → 204, y luego POST /applications/{id}/api-key
- THEN la segunda emisión responde 201 con una key nueva
- AND la key revocada deja de validar de inmediato (fail-closed)

#### Scenario: Aislamiento entre aplicaciones
- GIVEN aplicaciones A y B con keys propias
- WHEN la key de A se envía en un request dirigido a B
- THEN el request se autentica como A, nunca como B

## 2. ingest-auth (Nueva)

### Requisitos funcionales

### Requirement: IAUTH-1
El guard reutilizable `require_api_key` DEBE autenticar el header **X-API-Key** (decisión g) y responder: 401 con `WWW-Authenticate` para key ausente o inválida; 403 con código `app_inactive` para key válida de aplicación inactiva; 401 para key revocada (tratada como inexistente, fail-closed). Key válida DEBE inyectar la `Application` autenticada en el handler.

### Requirement: IAUTH-2
La aplicación autenticada DEBE derivarse EXCLUSIVAMENTE de la key (binding 1:1 credencial→app, decisión e); el `app_id` del payload NUNCA se confía para decidir qué aplicación es (mitigación BOLA/API1).

### Requirement: IAUTH-3
La validación DEBE ser timing-safe (CWE-208): lookup por prefijo `ilp_` + comparación SHA-256 en tiempo constante; hash o formato sin prefijo → 401 indistinguible del caso ausente.

### Requirement: IAUTH-4
X-API-Key y cualquier valor de key en requests/responses DEBEN redactarse en logs (access logs, tracebacks, métricas): el plaintext nunca se registra (decisión g, requisito operativo).

### Requirement: IAUTH-5
El guard DEBE ser una dependencia reutilizable desacoplada de handlers: en este cambio NO se aplica a ningún path existente (wiring a `/telemetry/*` en #37). Costo de validación objetivo ~1μs, sin servicios nuevos (CPU-only, <2GB RAM).

### Escenarios

#### Scenario: Key ausente
- GIVEN un request de ingesta sin header X-API-Key
- WHEN el guard `require_api_key` evalúa el request
- THEN 401 con ErrorResponse y `WWW-Authenticate` indicando el esquema

#### Scenario: Key inválida
- GIVEN un header con formato sin prefijo `ilp_` o con hash que no coincide
- WHEN el guard evalúa el request
- THEN 401 idéntico al caso de key ausente (sin información de causa)

#### Scenario: Aplicación inactiva
- GIVEN una aplicación con `is_active=false` y key válida
- WHEN el guard evalúa el request
- THEN 403 con código `app_inactive`

#### Scenario: Key revocada
- GIVEN una key revocada vía DELETE /applications/{id}/api-key
- WHEN el guard evalúa un request con esa key
- THEN 401 (fail-closed, indistinguible de key inexistente)

#### Scenario: Binding 1:1 — payload no confiable
- GIVEN la key de la aplicación A y un payload cuyo `app_id` es B
- WHEN el guard autentica el request
- THEN la aplicación inyectada es A y el `app_id` del payload se ignora

#### Scenario: Redacción de logs
- GIVEN un request con X-API-Key válida que genera logs y un error
- WHEN se inspeccionan access logs y tracebacks
- THEN el valor de la key no aparece en ningún log

## 3. applications-api (Modificada)

### Requisitos funcionales

### Requirement: APP-7
`is_active` DEBE incorporarse a los schemas de aplicación: default true en `ApplicationCreate`; mutable vía PUT /applications/{id} con `is_active` en `ApplicationUpdate`; presente en `ApplicationRead` (sin PATCH dedicado, decisión c).

### Requirement: APP-8
Una aplicación con `is_active=false` DEBE invalidar su key en ingesta: el guard responde 403 `app_inactive` (decisión c). Reactivar la app (`is_active=true`) DEBE restaurar la validez de la key vigente.

### Requirement: APP-9
`api_token_hash` DEBE retirarse de `ApplicationRead` (ADR-16, decisión f): fuera de `required` y de `properties`; GET/POST/PUT /applications NUNCA lo exponen (el hash es dato interno). (Previously: `api_token_hash` nullable en `ApplicationRead`, siempre null — columna dormida de S2-01.)

### Escenarios

#### Scenario: Inactivar aplicación
- GIVEN una aplicación activa con key emitida y bearer de Admin
- WHEN PUT /applications/{id} con `is_active: false`
- THEN 200 con `is_active: false` y un request de ingesta con su key responde 403 `app_inactive`

#### Scenario: Reactivar aplicación
- GIVEN la aplicación inactiva del escenario previo con la misma key vigente
- WHEN PUT /applications/{id} con `is_active: true`
- THEN 200 y la key vuelve a autenticar en ingesta

#### Scenario: ApplicationRead sin hash
- GIVEN una aplicación con key emitida y bearer válido
- WHEN GET /applications/{id}
- THEN 200 sin el campo `api_token_hash` en la respuesta

## 4. openapi (Modificada)

### Requisitos

### Requirement: OAS-6
El securityScheme `apiKey` (header `X-API-Key`) DEBE permanecer declarado y DEBE declararse su aplicabilidad obligatoria a los paths `/telemetry/*` (handlers en #37). En este cambio NO se agrega `security: [apiKey]` a ningún path existente: `/metrics/ingest` y `/logs/ingest` quedan sin security hasta #37, preservando la suite schemathesis vigente en verde (riesgo 4 resuelto: scheme declarado + guard probado aisladamente + wiring diferido).

### Requirement: OAS-7
DEBEN agregarse los paths POST y DELETE `/applications/{id}/api-key` (bearerAuth, solo Admin) con respuestas 201/204/401/403/404/409/422 y el schema `ApiKeyResponse` (`api_key`, `hint`; show-once).

### Requirement: OAS-8
`ApplicationRead` DEBE quedar sin `api_token_hash` en `required` y en `properties` (breaking declarado, ADR-16); los tests y schemathesis DEBEN actualizarse en el mismo cambio (riesgo 1 resuelto: el delta y su migración de tests viajan juntos, sin ventana de contrato roto).

### Requirement: OAS-9
El contract testing DEBE ejecutarse con el soporte experimental de OpenAPI 3.1 de schemathesis (`--experimental=openapi-3.1` / `OPEN_API_3_1.enable()`) y NO DEBE bloquear el contract layer por su carácter experimental: la validación de respuestas sigue el spec 3.1; los checks declaran los status codes esperados (2xx/401/403/404/409/422); una limitación de herramienta se degrada documentada sin romper el gate (riesgo 2 resuelto).

### Requirement: OAS-10
Los paths preexistentes (/health, /ready, /metrics/ingest, /logs/ingest, telemetría, dashboard) DEBEN quedar intactos (backward compatibility; schemathesis verde).

### Escenarios

#### Scenario: Contrato válido tras ADR-16
- GIVEN el openapi.yaml editado (ApplicationRead sin api_token_hash, paths api-key nuevos)
- WHEN se valida el documento y se corre schemathesis con el flag experimental 3.1
- THEN el contrato es válido y la suite contract queda verde

#### Scenario: Ingesta existente sin exigencia de key
- GIVEN el scheme apiKey declarado sin `security` en /metrics/ingest y /logs/ingest
- WHEN schemathesis ejecuta los checks sobre esos paths
- THEN no se exige X-API-Key y los status codes vigentes (202/400/429/503) se declaran como esperados

## 5. Requisitos de datos — Migración 0003

### Requisitos

### Requirement: DATA-6
`0003_is_active.py` (revision `0003`, down_revision `0002`, escrita a mano; NO modifica 0001/0002) DEBE: `ALTER TABLE application ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT TRUE`.

### Requirement: DATA-7
La migración DEBE ser aditiva y compatible con filas existentes: todas las aplicaciones vigentes quedan `is_active=TRUE` (default); NO altera `api_token_hash` ni el índice único parcial `idx_application_api_token_hash` de 0002 (riesgo 6 resuelto: sin breaking de filas).

### Requirement: DATA-8
Downgrade DEBE ser completo: `DROP COLUMN is_active`; `alembic downgrade 0002` limpio y reversible (rollback plan).

### Requirement: DATA-9
`ddl_v1.0.sql` DEBE sincronizarse con 0003 (columna `is_active` + comentario de trazabilidad), condición del header cumplida por la creación de la migración nueva; 0001/0002 no se tocan.

### Escenarios

#### Scenario: Upgrade a head
- GIVEN una DB en revisión 0002 con aplicaciones existentes
- WHEN `alembic upgrade head`
- THEN revisión 0003 aplicada; `is_active` existe con default TRUE; las filas previas quedan activas

#### Scenario: Downgrade a 0002
- GIVEN una DB en revisión 0003
- WHEN `alembic downgrade 0002`
- THEN `is_active` eliminada; `api_token_hash` y su índice único parcial intactos

## 6. Requisitos de seguridad (transversales)

### Requirement: SEC-7
Show-once: la key en claro solo se muestra en el 201 de emisión; NUNCA se persiste ni se expone en respuestas; el prefijo `ilp_` no es secreto, el hash completo sí (C8/C9/C13).

### Requirement: SEC-8
Generación CSPRNG ≥256 bits; SHA-256 sin salt aceptable para keys de alta entropía; comparación timing-safe; sin KDF lento (bcrypt/argon2) en el hot path de validación (C7/C10/C12).

### Requirement: SEC-9
409 ante regeneración con key activa (rotación explícita en dos pasos); revocación por compromiso inmediata y fail-closed (C14/C17).

### Requirement: SEC-10
Límites de recursos: validación de key ~1μs (lookup indexado por prefijo + SHA-256); sin servicios nuevos; footprint CPU-only <2GB RAM.

## Criterios de aceptación verificables

1. Tests TDD: emisión (201/409/404, show-once), guard (401/403), aislamiento A≠B.
2. `alembic upgrade head` y `downgrade 0002` limpios sobre Postgres real; cobertura ≥70% (`pytest --cov=src`).
3. openapi.yaml válido; `api_token_hash` fuera de `ApplicationRead`; schemathesis verde con flag experimental OpenAPI 3.1 y checks 2xx/401/403/404/409/422.
4. X-API-Key redactada en logs: ausente en access logs y tracebacks.
5. App inactiva → 403 `app_inactive`; key revocada → 401; rotación en dos pasos (409 → DELETE 204 → 201).

## Next recommended

**design** — la fase design toma el contrato de los paths api-key, el guard reutilizable, la migración 0003 y las capabilities para definir arquitectura y ADRs (incluida la materialización de la revocación explícita vía DELETE /applications/{id}/api-key).