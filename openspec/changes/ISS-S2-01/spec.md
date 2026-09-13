# SPEC — ISS-S2-01: Backend Core funcional

**Tipo**: Delta spec. **Cambio**: ISS-S2-01 (GitHub #35). **Base**: proposal `sdd/ISS-S2-01/proposal`, explore `sdd/ISS-S2-01/explore`, ddl_v1.0.sql, migración 0001, `openspec/specs/openapi.yaml`.
**Alcance**: 6 paths / 11 operaciones de auth, users y applications; migración 0002; contrato OpenAPI. Strict TDD (config.yaml apply.tdd:true): cada escenario Given/When/Then se convierte en test red antes de implementar.

## Capabilities

- **Nuevas**: `user-auth`, `users-api`, `applications-api`
- **Modificada**: `openapi`

---

## 1. user-auth (Nueva)

### Requisitos funcionales

| ID | Requisito |
|----|-----------|
| AUTH-1 | POST /auth/login (público) DEBE autenticar email+password contra `lab_user` y responder 200 con `{access_token, token_type: "bearer", expires_in}`. JWT HS256 con claims `sub=user_id`, `role` (nombre denormalizado), `iat`, `exp`, `iss="intellops-api"`; expiración default 30 min; SIN refresh (S4). DEBE actualizar `lab_user.last_login`. |
| AUTH-2 | Login con email desconocido, password incorrecta o `password_hash` NULL DEBE responder 401 con código y mensaje idénticos (anti-enumeración). |
| AUTH-3 | Login con `is_active=false` DEBE responder 403 con ErrorResponse y NO actualizar `last_login`. |
| AUTH-4 | POST /auth/logout (requiere bearer) DEBE responder 204 stateless: el servidor NO persiste estado; el cliente descarta el token. |
| AUTH-5 | Paths protegidos (users, applications, logout) DEBEN rechazar bearer ausente, malformado, expirado o de firma inválida con 401. |
| AUTH-6 | `jwt_secret` DEBE tener ≥32 bytes; algoritmo HS256; expiración configurable (`jwt_access_token_expire_minutes`, default 30 min). |

### Escenarios

#### Scenario: Login exitoso
- GIVEN un `lab_user` activo con `password_hash` argon2 válido
- WHEN POST /auth/login con email y password correctos
- THEN 200 con `access_token`, `token_type: "bearer"`, `expires_in: 1800`
- AND el token decodifica con `sub=user_id`, `role`, `iss="intellops-api"` e `iat`/`exp` (exp = iat + 30 min)
- AND `last_login` del usuario se actualiza

#### Scenario: Login fallido — email desconocido vs password incorrecta
- GIVEN un email inexistente y un `lab_user` existente con password distinto al enviado
- WHEN POST /auth/login en ambos casos
- THEN ambas respuestas son 401 con el mismo código y mensaje (indistinguibles)

#### Scenario: Login de usuario sin password_hash
- GIVEN un `lab_user` activo preexistente a 0002 con `password_hash` NULL
- WHEN POST /auth/login con su email y cualquier password
- THEN 401 idéntico al caso de credenciales inválidas
- AND un Admin puede setear su password vía PUT /users/{id} y luego loguea

#### Scenario: Login de usuario inactivo
- GIVEN un `lab_user` con `is_active=false` y credenciales válidas
- WHEN POST /auth/login
- THEN 403 con ErrorResponse
- AND `last_login` NO cambia

#### Scenario: Logout stateless
- GIVEN un bearer JWT válido
- WHEN POST /auth/logout
- THEN 204 sin cuerpo y sin estado nuevo en servidor

#### Scenario: Token inválido o expirado
- GIVEN un token con firma inválida o con `exp` vencido
- WHEN GET /users con ese bearer
- THEN 401

## 2. users-api (Nueva)

### Requisitos funcionales

| ID | Requisito |
|----|-----------|
| USR-1 | GET /users (bearer; Admin y Researcher) DEBE listar usuarios y NUNCA exponer `password_hash`. |
| USR-2 | GET /users/{id} (bearer; Admin y Researcher) DEBE devolver el detalle sin `password_hash`; 404 si no existe. |
| USR-3 | POST /users (bearer; SOLO Admin) DEBE crear usuario: `name` y `email` requeridos, email con formato válido, `password` ≥ 8 chars, `role_id` existente (FK), `is_active` default true; DEBE hashear password con argon2 (pwdlib). |
| USR-4 | POST/PUT /users con email duplicado DEBEN responder 409; `role_id` inexistente (FK) DEBE responder 409. |
| USR-5 | PUT /users/{id} (bearer; SOLO Admin) DEBE actualizar name/email/is_active/role_id y, SOLO si se envía `password`, re-hashear; 404 si no existe. |
| USR-6 | Researcher NO DEBE mutar: POST/PUT /users → 403. |
| USR-7 | Validaciones de forma (email malformado, password < 8, campos faltantes) DEBEN responder 422. |

### Escenarios

#### Scenario: Listar usuarios sin exponer hashes
- GIVEN bearer de Admin o Researcher y ≥1 usuario persistido
- WHEN GET /users
- THEN 200 con la lista de usuarios y ningún `password_hash` presente

#### Scenario: Crear usuario como Admin
- GIVEN bearer de Admin y payload `{name, email, password ≥ 8, role_id válido}`
- WHEN POST /users
- THEN 201 con el usuario creado (is_active=true), sin `password_hash` en la respuesta
- AND el `password_hash` persistido verifica contra la password con argon2

#### Scenario: Crear usuario con email duplicado
- GIVEN un `lab_user` existente con email E
- WHEN POST /users con email E
- THEN 409 con ErrorResponse

#### Scenario: Crear usuario con role_id inexistente
- GIVEN un role_id sin fila en `user_role`
- WHEN POST /users con ese role_id
- THEN 409 con ErrorResponse

#### Scenario: Researcher intenta crear
- GIVEN bearer de Researcher
- WHEN POST /users
- THEN 403

#### Scenario: Actualizar usuario sin password
- GIVEN usuario existente con `password_hash` y bearer de Admin
- WHEN PUT /users/{id} con name/email/is_active/role_id (sin password)
- THEN 200 y el `password_hash` previo permanece intacto

#### Scenario: Actualizar usuario con password
- GIVEN usuario existente y bearer de Admin
- WHEN PUT /users/{id} incluyendo `password`
- THEN 200 y el nuevo `password_hash` reemplaza al previo (argon2)

#### Scenario: Detalle de usuario inexistente
- GIVEN bearer válido y un id UUID sin usuario
- WHEN GET /users/{id}
- THEN 404

## 3. applications-api (Nueva)

### Requisitos funcionales

| ID | Requisito |
|----|-----------|
| APP-1 | GET /applications y GET /applications/{id} (bearer; Admin y Researcher) DEBEN listar/detallar aplicaciones; 404 en detalle si no existe. |
| APP-2 | POST /applications (bearer; SOLO Admin) DEBE crear aplicación: `name` requerido no vacío, `description` opcional; `api_token_hash` DEBE quedar NULL (columna dormida hasta S2-02). |
| APP-3 | PUT /applications/{id} (bearer; SOLO Admin) DEBE actualizar name/description; 404 si no existe. |
| APP-4 | DELETE /applications/{id} (bearer; SOLO Admin) DEBE eliminar físicamente la aplicación; 404 si no existe; DEBE responder 409 si la FK RESTRICT de `user_session.app_id` lo impide. |
| APP-5 | Researcher NO DEBE mutar aplicaciones: POST/PUT/DELETE → 403. |
| APP-6 | `name` vacío/ausente en POST/PUT DEBE responder 422. |

### Escenarios

#### Scenario: Crear aplicación como Admin
- GIVEN bearer de Admin y payload `{name: "web-app"}`
- WHEN POST /applications
- THEN 201 con la aplicación creada y `api_token_hash: null`

#### Scenario: Listar y detallar aplicaciones
- GIVEN bearer de Admin o Researcher y ≥1 aplicación
- WHEN GET /applications y GET /applications/{id}
- THEN 200 en ambos; detalle de id inexistente → 404

#### Scenario: Researcher intenta crear aplicación
- GIVEN bearer de Researcher
- WHEN POST /applications
- THEN 403

#### Scenario: Eliminar aplicación sin sesiones
- GIVEN una aplicación sin `user_session` asociadas y bearer de Admin
- WHEN DELETE /applications/{id}
- THEN 204 y la aplicación ya no existe (GET → 404)

#### Scenario: Eliminar aplicación con sesiones (FK RESTRICT)
- GIVEN una aplicación con ≥1 `user_session` (FK ON DELETE RESTRICT) y bearer de Admin
- WHEN DELETE /applications/{id}
- THEN 409 con ErrorResponse y la aplicación permanece (GET → 200)

#### Scenario: Actualizar aplicación inexistente
- GIVEN bearer de Admin y un id UUID sin aplicación
- WHEN PUT /applications/{id}
- THEN 404

## 4. openapi (Modificada)

### Requisitos

| ID | Requisito |
|----|-----------|
| OAS-1 | `openspec/specs/openapi.yaml` DEBE agregar 6 paths (11 operaciones): POST /auth/login, POST /auth/logout, GET/POST /users, GET/PUT /users/{id}, GET/POST /applications, GET/PUT/DELETE /applications/{id}. |
| OAS-2 | DEBE declarar securityScheme `bearerAuth` (HTTP bearer) y aplicarlo a users, applications y logout; `/auth/login` permanece público. |
| OAS-3 | `apiKey` (X-API-Key) DEBE permanecer declarado sin aplicar a ningún path (aplicación en S2-02). |
| OAS-4 | Los paths existentes (/health, /ready, /metrics/ingest, /logs/ingest, telemetría/dashboard) DEBEN quedar intactos (sin romper backward compatibility; schemathesis en verde). |
| OAS-5 | DEBE incorporar schemas `AuthResponse`, `UserCreate`, `UserUpdate`, `UserRead`, `ApplicationCreate`, `ApplicationUpdate`, `ApplicationRead` y reutilizar `ErrorResponse` para 401/403/404/409. |

## 5. Requisitos de datos — Migración 0002

### Requisitos

| ID | Requisito |
|----|-----------|
| DATA-1 | `0002_credentials.py` (revision `0002`, down_revision `0001`, escrita a mano; NO modifica 0001) DEBE: `ALTER TABLE lab_user ADD COLUMN password_hash VARCHAR(255) NULL`; `CREATE UNIQUE INDEX idx_lab_user_email ON lab_user(email)`; `ALTER TABLE application ADD COLUMN api_token_hash VARCHAR(64) NULL`; `CREATE UNIQUE INDEX idx_application_api_token_hash ON application(api_token_hash) WHERE api_token_hash IS NOT NULL`. |
| DATA-2 | `password_hash` DEBE quedar nullable en DDL; el enforcement (no login sin hash) es responsabilidad del servicio. |
| DATA-3 | Seed Admin: `INSERT lab_user` con UUID fijo, name='Admin', email='admin@intellops.local', role_id=(rol Admin de user_role), is_active=TRUE, `password_hash` = argon2 de password dev documentada en .env.example/README (solo dev/CI; sin secrets reales en el repo). |
| DATA-4 | Downgrade DEBE ser completo y ordenado: DROP índice único parcial → DROP `api_token_hash` → DROP índice email → DROP `password_hash` → DELETE seed Admin (seguro: user_favorite_metric CASCADE, user_session SET NULL). |
| DATA-5 | Decisión (riesgo #6 del proposal, delegada a spec): ddl_v1.0.sql DEBE sincronizarse con 0002 (columnas, índices y seed), porque su header condiciona su modificación a la creación de una migración nueva (condición cumplida) y preserva el DDL como fuente de verdad del esquema; 0001 NO se toca. |

### Escenarios

#### Scenario: Upgrade a head
- GIVEN una DB en revisión 0001 con catálogos (Admin/Researcher en user_role)
- WHEN `alembic upgrade head`
- THEN revisión 0002 aplicada; columnas e índices existen; seed Admin persistido (email admin@intellops.local, rol Admin, is_active)

#### Scenario: Login con seed Admin
- GIVEN migración 0002 aplicada y password dev documentada
- WHEN POST /auth/login con admin@intellops.local + password dev
- THEN 200 con token (expiración 30 min)

#### Scenario: Email único en DB
- GIVEN el seed Admin existente
- WHEN POST /users con email admin@intellops.local
- THEN 409 (idx_lab_user_email)

#### Scenario: Downgrade a 0001
- GIVEN DB en revisión 0002
- WHEN `alembic downgrade 0001`
- THEN columnas e índices de 0002 eliminados; seed Admin eliminado; esquema de 0001 intacto

## 6. Requisitos de seguridad (transversales)

| ID | Requisito |
|----|-----------|
| SEC-1 | Anti-enumeración: 401 idéntico (código, mensaje y comportamiento) para email desconocido, password incorrecta y `password_hash` NULL. |
| SEC-2 | 403 ante `is_active=false` en login. |
| SEC-3 | 409 con ErrorResponse para UNIQUE email violado (users) y para DELETE bloqueado por FK RESTRICT (applications). |
| SEC-4 | `password_hash` y `api_token_hash` NUNCA se exponen en respuestas. |
| SEC-5 | Passwords: argon2 (pwdlib). `api_token_hash`: solo schema en S2-01 (SHA-256 hex en S2-02); sin generación/validación de keys en este cambio. |
| SEC-6 | Límites de recursos: login dominado por argon2 (parámetros default); JWT y CRUD con overhead despreciable; sin nuevos servicios (CPU-only, <2GB RAM). ML: N/A (sin componentes ML en este cambio). |

## Criterios de aceptación verificables

1. Las 11 operaciones responden según contrato (tests TDD red-green).
2. Anti-enumeración: 401 indistinguible en login; Researcher 403 en mutaciones; Admin OK.
3. `alembic upgrade head` y `downgrade 0001` limpios sobre Postgres real.
4. Cobertura ≥70% (`pytest --cov=src`).
5. OpenAPI: 6 paths + bearerAuth; /health, /ready e ingesta intactos (schemathesis verde).
6. DELETE de aplicación con sesiones → 409; sin sesiones → 204.
7. Seed Admin loguea con password dev; el email del seed no se puede duplicar (409).

## Next recommended

**design** — la fase design toma el contrato de endpoints, la migración 0002 y las capabilities para definir arquitectura y ADRs.