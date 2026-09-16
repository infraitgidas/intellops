# Proposal: ISS-S2-01 — Backend Core funcional

## Resumen ejecutivo

Implementar el núcleo funcional del backend de gestión: autenticación JWT de usuarios, CRUD de usuarios y aplicaciones, persistencia vía modelos ORM + repositorios + servicios, migración 0002 con columnas de credenciales y contrato OpenAPI con bearerAuth. Criterios de aceptación del issue #35: recursos accesibles vía API, persistencia correcta, aislamiento/autorización entre aplicaciones.

## Intención

El backend hoy (post PR #46) solo expone /health, /ready e ingesta RUM/logs; no hay modelos ORM, repositorios, auth ni routers de gestión sobre los recursos core. Este cambio habilita login de usuarios y administración de usuarios/aplicaciones, condición necesaria para la ingesta autorizada por API key (S2-02) y para el resto del sprint S2.

## Scope

### In Scope
- POST /auth/login, POST /auth/logout (stateless; JWT HS256 access-only 30 min, sin refresh).
- GET/POST /users, GET/PUT /users/{id} (sin DELETE físico; desactivación vía is_active).
- GET/POST /applications, GET/PUT/DELETE /applications/{id} (DELETE → 409 ante FK RESTRICT).
- Modelos ORM (Application, LabUser, UserRole), repositorios (Protocols + SQLAlchemy), servicios.
- Migración 0002: password_hash nullable (enforcement en servicio), UNIQUE email, api_token_hash + índice único parcial, seed Admin.
- Dependencias PyJWT + pwdlib[argon2] (pyproject.toml + src/api/requirements.txt).
- openspec/specs/openapi.yaml: 6 paths nuevos (11 operaciones) + securityScheme bearerAuth.

### Out of Scope
- Generación/rotación/revocación de api_token, middleware X-API-Key, autorización de ingesta (S2-02).
- application.is_active (migración 0003, S2-02).
- Refresh tokens / denylist / revocación de JWT (hardening S4).
- DELETE físico de usuarios; endpoints de telemetría/dashboard; CORS hardening.

## Endpoints (contrato para la fase spec)

| Path | Método | Auth | Rol | Qué hace | Validaciones clave |
|------|--------|------|-----|----------|--------------------|
| /auth/login | POST | pública | — | Autentica email+password → 200 {access_token, token_type:"bearer", expires_in}; 403 si is_active=false; actualiza lab_user.last_login | Email formato; password no vacío; 401 con mensaje idéntico para email desconocido vs password incorrecta (anti-enumeración) |
| /auth/logout | POST | bearer | — | 204 stateless; el cliente descarta el token; sin estado en servidor | Ninguna |
| /users | GET | bearer | Researcher, Admin | Lista usuarios (nunca expone password_hash) | — |
| /users | POST | bearer | Admin | Crea usuario; hashea password (argon2) | Email formato + UNIQUE → 409; password ≥8 chars; role_id existente (FK); is_active default true |
| /users/{id} | GET | bearer | Researcher, Admin | Detalle de usuario | 404 si no existe |
| /users/{id} | PUT | bearer | Admin | Actualiza name/email/is_active/role_id; password opcional (re-hash solo si se envía) | Email UNIQUE → 409; 404 si no existe |
| /applications | GET | bearer | Researcher, Admin | Lista aplicaciones | — |
| /applications | POST | bearer | Admin | Crea aplicación | name requerido no vacío; api_token_hash NO se setea en S2-01 (NULL, columna dormida) |
| /applications/{id} | GET | bearer | Researcher, Admin | Detalle de aplicación | 404 si no existe |
| /applications/{id} | PUT | bearer | Admin | Actualiza name/description | 404 si no existe |
| /applications/{id} | DELETE | bearer | Admin | Hard delete físico | 409 si FK RESTRICT lo impide (user_session existentes); 404 si no existe |

## Migración 0002 (0002_credentials.py) — detalle por cambio

- ALTER TABLE lab_user ADD COLUMN password_hash VARCHAR(255) NULL — nullable en DDL; enforcement en servicio (usuario sin hash no puede loguear; NOT NULL rompería upgrades sobre filas existentes).
- CREATE UNIQUE INDEX idx_lab_user_email ON lab_user(email) — requerido para login por email y anti-duplicados.
- ALTER TABLE application ADD COLUMN api_token_hash VARCHAR(64) NULL — hash SHA-256 hex; dormida hasta S2-02.
- CREATE UNIQUE INDEX idx_application_api_token_hash ON application(api_token_hash) WHERE api_token_hash IS NOT NULL — índice único parcial.
- Seed Admin: INSERT lab_user (UUID fijo, name='Admin', email='admin@intellops.local', role_id=(SELECT role_id FROM user_role WHERE name='Admin'), is_active=TRUE, password_hash=hash argon2 de password dev documentada en .env.example/README).
- Downgrade: DROP índice parcial → DROP api_token_hash → DROP índice email → DROP password_hash → DELETE seed Admin (seguro: user_favorite_metric CASCADE, user_session SET NULL).
- Escritura a mano, consistente con 0001 y env.py target_metadata=None; NO tocar 0001.

## Capabilities (contrato con sdd-spec)

### New Capabilities
- user-auth: login/logout, JWT HS256 access-only, hashing argon2.
- users-api: CRUD de usuarios con política de roles Admin muta / Researcher lee.
- applications-api: CRUD de aplicaciones con DELETE→409.

### Modified Capabilities
- openapi: contrato con +6 paths (11 operaciones) y securityScheme bearerAuth aplicado a users/applications; apiKey queda declarado sin aplicar hasta S2-02.

## Approach

Monolito modular FastAPI: presentation (routers + schemas Pydantic + dependencies) → services (casos de uso) → repositories (SQLAlchemy async) → PostgreSQL canónico. JWT con PyJWT (HS256; claims sub=user_id, role denormalizado, iat, exp, iss="intellops-api"; secret settings.jwt_secret ≥32 bytes, expiración default 30 min). Passwords con pwdlib[argon2]. Autorización por rol vía dependencias get_current_user/require_role; el tenant scoping por credencial (app_id resuelto de la API key, nunca del payload) se implementa en S2-02. Strict TDD: fixtures async (httpx AsyncClient + session override) contra Postgres real; CI provee servicio Postgres. Entrega en PRs encadenados (ver riesgos).

## Affected Areas

| Area | Impact | Descripción |
|------|--------|-------------|
| src/api/config.py | Modificado | Settings: jwt_secret, jwt_algorithm, jwt_access_token_expire_minutes |
| src/api/main.py | Modificado | Include routers auth/users/applications; exception handlers |
| pyproject.toml, src/api/requirements.txt | Modificado | + PyJWT, pwdlib[argon2] |
| openspec/specs/openapi.yaml | Modificado | +6 paths (11 ops), bearerAuth, schemas auth/user/application |
| .env.example | Modificado | + JWT_SECRET, password admin de bootstrap (dev) |
| src/api/domain/entities/{__init__,user_role,lab_user,application}.py | Nuevo | Modelos ORM |
| src/api/domain/repositories/{__init__,user_repository,application_repository}.py | Nuevo | Protocols |
| src/api/domain/services/{__init__,auth_service,user_service,application_service}.py | Nuevo | Casos de uso |
| src/api/infrastructure/db/migrations/versions/0002_credentials.py | Nuevo | Migración |
| src/api/infrastructure/db/repositories/{__init__,sqlalchemy_user_repository,sqlalchemy_application_repository}.py | Nuevo | Implementaciones SQLAlchemy |
| src/api/infrastructure/security/{__init__,password,jwt,api_keys}.py | Nuevo | hash/verify, create/decode token, generate/hash key (API keys solo utilidades; uso en S2-02) |
| src/api/presentation/{__init__,dependencies}.py | Nuevo | get_current_user, require_role |
| src/api/presentation/schemas/{__init__,auth,user,application}.py | Nuevo | Pydantic |
| src/api/presentation/routers/{__init__,auth,users,applications}.py | Nuevo | Endpoints |
| tests/{conftest,test_auth,test_users,test_applications}.py | Nuevo | Fixtures async + casos TDD |

## Risks

| Riesgo | Prob. | Mitigación |
|--------|-------|------------|
| Tamaño: ~1200-1800 líneas añadidas > presupuesto de review (400) | Alta | PRs encadenados: 1) auth+modelos+migración, 2) users, 3) applications; decidir delivery_strategy antes de apply |
| Dependencias nuevas (PyJWT, pwdlib) | Media | Espejar en pyproject + requirements.txt + rebuild imagen docker; licencias MIT/BSD compatibles |
| Secretos dev/CI (JWT_SECRET, seed password) | Media | Defaults dev documentados + override por env en prod; no commitear secrets reales |
| Contrato OpenAPI: schemathesis sobre openapi.yaml | Media | No romper /health, /ready ni ingesta; bearerAuth solo en paths nuevos |
| Tests con Postgres real (cobertura ≥70%) | Media | Fixtures async con aislamiento por test (truncate); CI ya levanta servicio Postgres |
| FK RESTRICT: DELETE de application con sesiones | Media | 409 controlado con ErrorResponse; documentar semántica |
| ddl_v1.0.sql (fuente de verdad de 0001) no refleja columnas de 0002 | Baja | Decidir en fase spec: sincronizar DDL o documentar divergencia; no modificar 0001 |

## Rollback Plan

- DB: alembic downgrade 0001 revierte 0002 completo (pierde solo credenciales y seed; 0002 es aditiva y no toca 0001).
- Código: revert por slice (PR encadenado); cada PR es reversible independientemente.
- Contrato: revert del diff de openapi.yaml.
- Dependencias: remover PyJWT/pwdlib de pyproject + requirements.txt + rebuild.

## Dependencies

- PR #46 (base, mergeado en develop) — capa DB: session async, Alembic 0001, /health.
- PyJWT ≥2.x, pydlib[argon2] — nuevas.
- Servicio Postgres en CI (ya existente).

## Success Criteria

- [ ] Las 11 operaciones responden según contrato (tests TDD red-green en verde).
- [ ] Persistencia correcta: alembic upgrade head y downgrade limpios sobre DB real.
- [ ] Cobertura ≥70% (pytest --cov=src).
- [ ] OpenAPI: 6 paths nuevos + bearerAuth aplicado; /health, /ready e ingesta intactos.
- [ ] Aislamiento/autorización: Researcher recibe 403 en mutaciones; Admin OK; login 401 anti-enumeración.

## Observaciones (sin cambio de alcance)

1. El alcance fijado menciona "9 paths": la lista concreta suma 6 paths / 11 operaciones (2 auth + 2 users + 2 user-detail + 2 applications + 3 application-detail). Se documenta la lista completa como contrato; la fase spec debe usar esta lista.
2. password_hash nullable en DDL + enforcement en servicio implica que usuarios preexistentes (sin hash) no pueden loguear hasta setear password vía PUT /users/{id} — comportamiento esperado, documentar.

## Next recommended

**spec** — la fase spec toma el contrato de endpoints, la migración 0002 detallada y las capabilities definidas.