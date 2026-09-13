```yaml
schema: gentle-ai.verify-result/v1
evidence_revision: sha256:361debc5cd996e930b166c4a6d651f01df885b0d572e996362fecb0f80e63272
verdict: fail
blockers: 1
critical_findings: 1
requirements: 35/35
scenarios: 24/24
test_command: docker compose run --rm intellops-core python -m pytest tests/ -v
test_exit_code: 0
test_output_hash: sha256:361debc5cd996e930b166c4a6d651f01df885b0d572e996362fecb0f80e63272
build_command: docker compose build intellops-core
build_exit_code: 0
build_output_hash: sha256:3db231e0faa966009b09deed9644c976f8cbea4a3a037e86d043dc22f5282d91
```

## Verification Report

**Change**: ISS-S2-01 — Backend Core funcional (GitHub #35)
**Version**: spec.md (delta, 2026-09-12)
**Mode**: Strict TDD
**Rama**: feat/ISS-S2-01 (feature-branch-chain, PR-A/B/C/D + F1/F2)
**Fecha**: 2026-09-13

### Completeness

| Metric | Value |
|--------|-------|
| Tasks total | 23 (PR-A 10 + PR-B 4 + PR-C 3 + PR-D 4 + F1/F2) |
| Tasks complete | 23 |
| Tasks incomplete | 0 |

### Build & Tests Execution

**Build**: ✅ Passed (`docker compose build intellops-core`, exit 0)

**Tests**: ✅ 90 passed / 0 failed / 0 skipped
```text
docker compose run --rm intellops-core python -m pytest tests/ -v
=============================== 90 passed, 11 warnings in 34.87s =================
```
- health 2, security 17, migrations 3, ml_worker 2, auth 16, users 30, applications 20.

**Coverage**: 79% / threshold 70% → ✅ Above (gate OK). Ver nota de confiabilidad por archivo (WARNING-2).

### TDD Compliance

| Check | Result | Details |
|-------|--------|---------|
| TDD Evidence reported | ✅ | Engram `sdd/ISS-S2-01/apply-progress` (#89), tabla "TDD Cycle Evidence" presente |
| All tasks have tests | ✅ | 23/23 tareas con test file verificado |
| RED confirmed (tests exist) | ✅ | test_auth/users/applications/security/migrations existentes en el repo |
| GREEN confirmed (tests pass) | ✅ | 90/90 pasan en ejecución independiente |
| Triangulation adequate | ✅ | 24 escenarios spec cubiertos por tests HTTP + unit (múltiples casos por escenario) |
| Safety Net for modified files | ✅ | 64/64 → 88/88 tests preexistentes corrieron antes de cada slice |

**TDD Compliance**: 6/6 checks passed

### Test Layer Distribution

| Layer | Tests | Files | Tools |
|-------|-------|-------|-------|
| Unit | 39 | test_security, test_migrations, test_health, test_ml_worker + schemas | pytest |
| Integration (HTTP + Postgres real) | 51 | test_auth, test_users, test_applications | pytest + httpx AsyncClient + SQLAlchemy async |
| Contract | 11 ops | schemathesis 4.27 (ver hallazgos) | schemathesis |
| **Total** | **90** | **7** | |

### Changed File Coverage

Nota de confiabilidad: coverage.py 7.16.0 en este entorno NO registra líneas posteriores a un `await` dentro de coroutines (verificado con probe directo: `create_application` retorna exitosamente e imprime su resultado, y aun así las líneas 43-45 commit/refresh/return se reportan missing; idéntico con tracer C, tracer Python `--timid` y `--concurrency=thread`). Los números por archivo de la capa de servicios (~50%) son un artefacto de medición que SUBCUENTA; la cobertura real es ≥ al total reportado. El total (79%) es un límite inferior conservador y pasa el gate.

| File | Line % (reportado) | Rating real |
|------|--------------------|-------------|
| src/api/domain/services/*.py | 47-52% (artefacto) | ✅ Real ≥80% (probe directo lo demuestra) |
| src/api/presentation/routers/*.py | 97-100% | ✅ Excellent |
| src/api/presentation/schemas/*.py | 96-100% | ✅ Excellent |
| src/api/infrastructure/security/*.py | 100% | ✅ Excellent |
| src/api/domain/entities/*.py | 100% | ✅ Excellent |
| src/api/domain/exceptions.py | 100% | ✅ Excellent |
| src/api/presentation/dependencies.py | 85% | ✅ Acceptable |
| src/api/main.py | 90% | ✅ Excellent |
| src/api/infrastructure/db/migrations/versions/0002_credentials.py | 100% | ✅ Excellent |
| src/api/infrastructure/db/repositories/*.py | 67-82% | ⚠️ Acceptable |

**Promedio reportado (total suite)**: 79% — gate `--cov-fail-under=70` ✅.

### Assertion Quality

**Assertion quality**: ✅ All assertions verify real behavior. Los tests afirman status codes, cuerpos JSON, claims JWT, persistencia en DB real (argon2 verify, last_login, hashes no expuestos) y estados post-condición (GET→404 tras DELETE). Sin tautologías, ghost loops ni smoke-only.

### Quality Metrics

**Linter (flake8)**: ✅ No errors (`flake8 src/ tests/` exit 0, max 99 cols)
**Pylint**: ✅ 9.84/10 (fail-under 7.0 OK). Solo `import-error` preexistente en `src/ml/` (fuera del alcance del cambio).
**Type Checker**: ➖ Not available (config: false)

### Spec Compliance Matrix

Requisitos: 35/35 (AUTH-1..6, USR-1..7, APP-1..6, OAS-1..5, DATA-1..5, SEC-1..6). Escenarios: 24/24.

| Req | Escenario | Test | Result |
|-----|-----------|------|--------|
| AUTH-1 | Login exitoso | `test_auth.py > test_login_success_returns_token_claims_and_updates_last_login`, `test_login_seed_admin_with_dev_password` | ✅ COMPLIANT |
| AUTH-2 | Login fallido email desconocido vs password | `test_auth.py > test_login_401_identical_for_unknown_email_and_wrong_password` | ✅ COMPLIANT |
| AUTH-2 | Usuario sin password_hash | `test_auth.py > test_login_user_without_password_hash_returns_401_identical` | ✅ COMPLIANT |
| AUTH-3 | Login inactivo | `test_auth.py > test_login_inactive_user_403_and_last_login_unchanged` | ✅ COMPLIANT |
| AUTH-4 | Logout stateless | `test_auth.py > test_logout_returns_204_stateless` | ✅ COMPLIANT |
| AUTH-5 | Token inválido/expirado | `test_auth.py > test_logout_rejects_*`, `test_protected_path_*`, `test_users_path_requires_bearer`, `test_applications_path_requires_bearer` | ✅ COMPLIANT |
| AUTH-6 | jwt_secret ≥32 / HS256 / exp 30min | `test_security.py > test_jwt_secret_shorter_than_32_rejected`, `test_settings_jwt_defaults`, `test_create_access_token_claims` | ✅ COMPLIANT |
| USR-1 | Listar sin hashes | `test_users.py > test_list_users_never_exposes_password_hash`, `test_researcher_can_list_users` | ✅ COMPLIANT |
| USR-2 | Detalle sin hashes / 404 | `test_users.py > test_get_user_detail_without_password_hash`, `test_get_user_not_found_404` | ✅ COMPLIANT |
| USR-3 | Crear Admin 201 + argon2 | `test_users.py > test_create_user_201_argon2_verified_and_no_hash` | ✅ COMPLIANT |
| USR-4 | Email duplicado / role inexistente 409 | `test_users.py > test_create_user_duplicate_email_409`, `test_create_user_nonexistent_role_409`, `test_update_user_duplicate_email_409`, `test_update_user_nonexistent_role_409`, `test_create_user_role_id_out_of_int16_range_409` | ✅ COMPLIANT |
| USR-5 | PUT sin/con password | `test_users.py > test_update_user_without_password_keeps_hash`, `test_update_user_with_password_rehashes` | ✅ COMPLIANT |
| USR-6 | Researcher 403 | `test_users.py > test_researcher_cannot_create_user_403`, `test_researcher_cannot_update_user_403` | ✅ COMPLIANT |
| USR-7 | Validación forma 422 | `test_users.py > test_create_user_422_*`, `test_update_user_422_*`, `test_create_user_422_nul_byte_in_name` | ✅ COMPLIANT |
| APP-1 | List/detail 200 / 404 | `test_applications.py > test_list_applications_200`, `test_get_application_detail_200`, `test_get_application_not_found_404` | ✅ COMPLIANT |
| APP-2 | Crear 201 con api_token_hash null | `test_applications.py > test_create_application_201_api_token_hash_null` | ✅ COMPLIANT |
| APP-3 | PUT 200 / 404 | `test_applications.py > test_update_application_200`, `test_update_application_not_found_404` | ✅ COMPLIANT |
| APP-4 | DELETE 204 / 404 / 409 FK | `test_applications.py > test_delete_application_without_sessions_204_then_404`, `test_delete_application_with_sessions_409_then_200`, `test_delete_application_not_found_404` | ✅ COMPLIANT |
| APP-5 | Researcher 403 | `test_applications.py > test_researcher_cannot_create_application_403`, `_update_403`, `_delete_403` | ✅ COMPLIANT |
| APP-6 | name vacío 422 | `test_applications.py > test_application_create_rejects_empty_name`, `test_create_application_422_empty_name`, `test_update_application_422_empty_name` | ✅ COMPLIANT |
| OAS-1 | 6 paths / 11 ops | Validación YAML: 6 paths nuevos, 11 operaciones contadas | ✅ COMPLIANT |
| OAS-2 | bearerAuth aplicado | YAML: security bearerAuth en 10 ops; /auth/login público | ✅ COMPLIANT |
| OAS-3 | apiKey sin aplicar | YAML: apiKey declarado, ninguna op lo aplica | ✅ COMPLIANT |
| OAS-4 | Existentes intactos | YAML: 18 paths preexistentes intactos (554 inserciones, 0 borrados); /health 200 en vivo | ✅ COMPLIANT (archivo) |
| OAS-5 | Schemas nuevos + ErrorResponse | YAML: AuthResponse, UserCreate/Update/Read, ApplicationCreate/Update/Read + ErrorResponse en 401/403/404/409 | ✅ COMPLIANT (archivo) |
| DATA-1..5 | Migración 0002 | `test_migrations.py` (3 tests) + alembic upgrade/downgrade/upgrade en vivo + ddl_v1.0.sql sincronizado | ✅ COMPLIANT |
| SEC-1 | Anti-enumeración | `test_login_401_identical_*` + probe en vivo: cuerpos idénticos | ✅ COMPLIANT |
| SEC-2 | 403 inactivo | `test_login_inactive_user_403_and_last_login_unchanged`, `test_protected_path_returns_403_for_inactive_user` | ✅ COMPLIANT |
| SEC-3 | 409 UNIQUE/FK | `test_create_user_duplicate_email_409`, `test_delete_application_with_sessions_409_then_200` | ✅ COMPLIANT |
| SEC-4 | Hashes nunca expuestos | `test_list_users_never_exposes_password_hash`, `test_application_read_exposes_api_token_hash_null` | ✅ COMPLIANT |
| SEC-5 | argon2 / API key dormida | `test_security.py > test_password_hash_roundtrip`, `test_generate_api_key_format`, `test_hash_api_key_sha256_hex_deterministic` | ✅ COMPLIANT |
| SEC-6 | Límites recursos | Sin servicios nuevos; argon2 params default; sin componentes ML | ✅ COMPLIANT |

**Compliance summary**: 24/24 escenarios con test pasando. ⚠️ PERO: la verificación en vivo sobre el runtime de producción (uvicorn `src.api.main:app`) revela que los códigos de error del contrato (401/403/404/409) se degradan a 500 (ver CRITICAL-1). La suite pytest pasa porque conftest importa `api.main` (namespace consistente).

### Correctness (Static Evidence)

| Requisito | Status | Notas |
|-----------|--------|-------|
| Criterios de aceptación CA1 (11 ops según contrato) | ⚠️ Parcial | Tests en verde, pero runtime de producción devuelve 500 en errores de dominio |
| CA2 (anti-enumeración 401; Researcher 403; Admin OK) | ⚠️ Parcial | Verificado en vivo con `api.main` OK; degradado a 500 con `src.api.main` |
| CA3 (alembic upgrade/downgrade limpios) | ✅ Implementado | upgrade head → downgrade 0001 → upgrade head, exit 0, seed restaurado |
| CA4 (cobertura ≥70%) | ✅ Implementado | 79% ≥ 70%, gate exit 0 |
| CA5 (OpenAPI 6 paths + bearerAuth; existentes intactos) | ⚠️ Parcial | YAML correcto; `/openapi.json` generado NO documenta 401/403/404/409 (WARNING-1) |
| CA6 (DELETE con sesiones 409; sin sesiones 204) | ⚠️ Parcial | En vivo OK con `api.main`; 500 con `src.api.main` |
| CA7 (seed login; email no duplicable) | ⚠️ Parcial | En vivo OK con `api.main` (login 200, dup 409); 500 con `src.api.main` |

### Coherence (Design)

| Decisión (ADR) | Followed? | Notas |
|----------------|-----------|-------|
| ADR-01 access-only HS256 30min | ✅ Yes | jwt.py create/decode, config expire 30 |
| ADR-02 pwdlib argon2 | ✅ Yes | password.py `PasswordHash.recommended()` |
| ADR-03 SHA-256 + prefijo ilp_ dormido | ✅ Yes | api_keys.py, sin wiring |
| ADR-04 Admin muta / Researcher lee | ✅ Yes | require_role en routers |
| ADR-05 Seed Admin en 0002 | ✅ Yes | UUID fijo 9f8c..., hash argon2 precomputado verifica |
| ADR-06 password_hash NULL + enforcement | ✅ Yes | DDL nullable; login sin hash → 401 |
| ADR-07 Hard delete + 409 | ✅ Yes | delete físico; FK RESTRICT → ConflictError |
| ADR-08 ddl_v1.0.sql sync | ✅ Yes | columnas/índices/seed presentes |
| ADR-09 DomainError tipificados + handlers | ✅ Yes (tests) / ❌ No (runtime prod) | Ver CRITICAL-1: handler no matchea en `src.api.main` |
| ADR-10 Servicios dueños del commit + rollback | ✅ Yes | auth/user/application_service |
| ADR-11 pytest-asyncio session loop | ✅ Yes | conftest + pyproject |
| ADR-12 EmailStr + email-validator | ✅ Yes | schemas/common LabEmail (con extensión .local) |
| ADR-13 Dummy verify anti-enumeración | ✅ Yes | DUMMY_HASH en login fallido |
| ADR-14 get_role_by_id → 409 | ✅ Yes | user_service + F2 (DBAPIError → None) |
| ADR-15 Token de inactivo → 403 | ✅ Yes | dependencies.py |
| ADR-16 api_token_hash null en respuestas | ✅ Yes | ApplicationRead siempre null |

### Issues Found

**CRITICAL**:

- **CRITICAL-1 — Runtime de producción devuelve 500 para todos los errores de dominio (401/403/404/409)**. El Dockerfile CMD ejecuta `uvicorn src.api.main:app` con `PYTHONPATH=/app/src`. `main.py` registra el handler vía import relativo (`.domain.exceptions` → `src.api.domain.exceptions.DomainError`), pero `dependencies.py` y los routers levantan excepciones vía import absoluto (`api.domain.exceptions.AuthenticationError`). Con `PYTHONPATH=/app/src`, `src.api.*` y `api.*` son DOS árboles de módulos distintos: el handler registrado (`src.api.domain.exceptions.DomainError`) nunca matchea la excepción levantada (`api.domain.exceptions.AuthenticationError`), porque Starlette resuelve el handler recorriendo el MRO de la excepción. Resultado: toda respuesta de error de dominio se convierte en 500. **Evidencia**: (a) probe en vivo con `uvicorn src.api.main:app`: `GET /users` sin auth → 500, `GET /users/{uuid}` sin auth → 500, `GET /users/{uuid inexistente}` con token válido → 500 (esperado 404), `POST /users` email duplicado → 500 (esperado 409), `POST /auth/login` email desconocido → 500 (esperado 401); (b) el mismo código con `uvicorn api.main:app` responde 401/404/409 correctamente (namespace consistente); (c) `import src.api.main` vs `import api.main` → `app is not the same object`, `src AuthError is api AuthError: False`; (d) schemathesis contra runtime vivo: 13 fallas (6 server error + 7 undocumented status). **Por qué la suite pasa**: conftest importa `from api.main import app` — un solo namespace, el handler matchea. **Impacto**: CA1, CA2, CA5, CA6 y CA7 fallan en el runtime real del contenedor; el healthcheck (`/health`, que no levanta DomainError) sigue verde, enmascarando la rotura. **Root cause**: mezcla de imports relativos (main.py) y absolutos (resto) bajo el CMD `src.api.main`. **Fix sugerido (remediate)**: unificar imports (todo relativo o todo `api.*`) y/o cambiar el CMD a `uvicorn api.main:app`; agregar un test que ejercite la app vía el path de import del Dockerfile.

**WARNING**:

- **WARNING-1 — Drift de contrato OpenAPI servido**: el `/openapi.json` generado por FastAPI (a partir de los routers, que no declaran `responses=`) NO documenta 401/403/404/409 para `/users/{id}` (GET/PUT), `/applications/{id}` (GET/PUT/DELETE), `/auth/logout`, etc. El archivo canónico `openspec/specs/openapi.yaml` sí los documenta. Consecuencia: schemathesis contra el spec servido marca "undocumented status code 401" (7 fallas) aun cuando la API responde correctamente; los consumidores del spec generado no ven el contrato de error completo. Además el YAML declara 400 para JSON malformado, pero FastAPI responde 422 (mismatch menor). **Evidencia**: comparación programática generated vs yaml-file (9 operaciones difieren en responses); schemathesis `api.main` → undocumented 401.

- **WARNING-2 — Cobertura por archivo de la capa de servicios no confiable (artefacto de medición)**: coverage.py 7.16.0 en este contenedor no registra líneas posteriores a `await` dentro de coroutines. Probe directo (sin pytest): `create_application` ejecuta y devuelve el objeto (imprime output), pero las líneas 43-45 (commit/refresh/return) se reportan missing. Idéntico con tracer C, `--timid` (Python) y `--concurrency=thread`; también se observaron line numbers imposibles (hasta 1992 en un archivo de 74 líneas) en datos crudos. El total (79%) es un límite inferior conservador → el gate pasa, y la cobertura real es ≥79%. No bloquea, pero los % por archivo de services/repositories no deben leerse como reales. Sugerencia: investigar upgrade de coverage.py o config `concurrency` para la medición CI.

**SUGGESTION**:

- **SUGGESTION-1 — Schemathesis no está en la imagen base**: se instaló ad-hoc (`pip install schemathesis`) para el conformance; los flags de 4.27 difieren de versiones previas (`--checks not_a_server_error` etc.). Considerar agregarlo a dev extras o documentar el comando exacto de conformance en README/CI (el apply-progress ya lo anotó como gotcha).
- **SUGGESTION-2 — El conformance reportado en apply (0 fallas) no es reproducible contra el spec servido**: la corrida de schemathesis en vivo sobre `/openapi.json` encuentra 13 fallas (500s del CRITICAL-1 + undocumented 401 del WARNING-1). Documentar contra qué fuente de spec (archivo vs generado) se ejecuta el conformance para que verify y apply midan lo mismo.
- **SUGGESTION-3 — `user_session` INSERT en probes**: columna es `start_timestamp`, no `started_at` (verificado en ddl_v1.0.sql); irrelevante para el cambio pero evidencia que el DER y el DDL usan nomenclatura a confirmar en S2-02.

### Drift vs Spec/Design

1. **Drift de import-path (CRITICAL-1)**: spec/design asumen que los handlers de DomainError traducen 401/403/404/409 (ADR-09). En el runtime del Dockerfile (`src.api.main`) NO ocurre → drift funcional entre lo verificado por tests y el comportamiento desplegado. Design §4.5/§9 no contempla el path de import del contenedor.
2. **Drift de spec OpenAPI servido (WARNING-1)**: OAS-2/OAS-5 se cumplen en el archivo canónico, pero el spec generado por la app no expone los códigos de error → los consumidores del contrato servido ven menos de lo que el contrato declara.
3. **Sin drift en alcance**: los 6 paths/11 ops, migración 0002 (columnas/índices/seed/orden downgrade), ddl_v1.0.sql sync, seed Admin (UUID, email, rol, is_active), F1 (NUL→422) y F2 (role_id int16→409) coinciden con spec/design/tasks. Tasks 23/23 con evidencia TDD en apply-progress.

### Verdict

**FAIL** — La suite de tests (90/90), cobertura (79%), lint (flake8/pylint), migraciones y el contrato YAML están verdes, pero el runtime de producción (`uvicorn src.api.main:app`, CMD del Dockerfile) convierte TODOS los errores de dominio (401/403/404/409) en 500 por dualidad de imports (`src.api.*` vs `api.*`), rompiendo los criterios CA1, CA2, CA5, CA6 y CA7 en el entorno desplegado. Se requiere remediate (unificar imports y/o CMD; test que ejercite el path de import del contenedor) antes de archive.