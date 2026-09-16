# TASKS — ISS-S2-01: Backend Core funcional

**Base**: proposal `sdd/ISS-S2-01/proposal`, spec `sdd/ISS-S2-01/spec`, design `sdd/ISS-S2-01/design`, código real en `feat/ISS-S2-01` (develop + PR #46). **Modo**: engram. **Idioma**: español neutro técnico. **TDD estricto** (config.yaml tdd:true): cada escenario de spec → test RED antes del código. Threat matrix del design: N/A (sin tasks RED extra).

## Review Workload Forecast

| Slice | Líneas est. | >400 |
|-------|-------------|------|
| PR-A core-auth-infra | ~500 | Sí → size:exception |
| PR-B core-auth | ~250 | No |
| PR-C core-users | ~350 | No |
| PR-D core-applications | ~300 | No |
| Total | ~1200–1800 | Sí |

Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: feature-branch-chain
400-line budget risk: High

### Work Units (bases: PR-A→feat/ISS-S2-01; PR-B→rama PR-A; PR-C→rama PR-B; PR-D→rama PR-C)

| Unit | Goal | PR | Test enfocado | Runtime harness | Rollback |
|------|------|----|---------------|-----------------|----------|
| 1 | Infra/auth base | PR-A ~500 | `pytest tests/test_security.py tests/test_migrations.py` | Postgres real (servicio CI) | Revert PR-A + `alembic downgrade 0001` |
| 2 | Auth login/logout | PR-B ~250 | `pytest tests/test_auth.py` | httpx AsyncClient + Postgres real | Revert PR-B |
| 3 | Users CRUD | PR-C ~350 | `pytest tests/test_users.py` | ídem | Revert PR-C |
| 4 | Applications + OpenAPI | PR-D ~300 | `pytest tests/test_applications.py` + schemathesis openapi.yaml | ídem | Revert PR-D + diff openapi.yaml |

## PR-A: core-auth-infra

- [x] A1 deps: `pyproject.toml` + `src/api/requirements.txt` (+PyJWT>=2.9, pwdlib[argon2], email-validator; dev pytest-asyncio). Done: `pip install -e ".[dev]"`. Dep: —
- [x] A2 config: `src/api/config.py` jwt_secret (validator ≥32), jwt_algorithm=HS256, jwt_access_token_expire_minutes=30, api_key_prefix="ilp_". RED: test_security AUTH-6 (secret<32 → error settings). Done: verde. Dep: —
- [x] A3 exceptions: `src/api/domain/exceptions.py` DomainError + subtipos 401/403/404/409. Done: importable con códigos. Dep: —
- [x] A4 security/password.py: hasher argon2 (pwdlib) + DUMMY_HASH. RED: test_security roundtrip hash/verify + verify falso. Done: verde. Dep: —
- [x] A5 security/jwt.py: create/decode (sub, role, iss, iat, exp=iat+30min). RED: test_security claims + expirado/firma inválida. Done: verde. Dep: —
- [x] A6 security/api_keys.py: generate `ilp_`+43 b64url, hash sha256 hex (dormido). RED: test_security formato. Done: verde. Dep: —
- [x] A7 entities: `src/api/domain/entities/{base,user_role,lab_user,application}.py` ORM 2.0 typed (FK RESTRICT, índices 0002). Done: importable. Dep: A1
- [x] A8 repos: Protocol `src/api/domain/repositories/{user,application}_repository.py` + impls async `src/api/infrastructure/db/repositories/*.py` (sin commit; IntegrityError→ConflictError). Done: importable. Dep: A7
- [x] A9 migración 0002 + sync: `.../versions/0002_credentials.py`, `openspec/specs/database/ddl_v1.0.sql`, `.env.example`. RED: test_migrations (upgrade: columnas/índices/seed; downgrade 0001 limpio; upgrade restaura). Done: upgrade→downgrade→upgrade OK. Dep: A2, A3
- [x] A10 conftest: `tests/conftest.py` fixtures async (db_session, clean_db, seed_admin, client, make_admin/make_researcher). Done: suite async colecta sobre Postgres real. Dep: A1

## PR-B: core-auth

- [x] B1 schemas: `src/api/presentation/schemas/auth.py` LoginRequest{email: EmailStr}, AuthResponse{token, "bearer", expires_in}. Done: importable. Dep: A2
- [x] B2 auth_service: `src/api/domain/services/auth_service.py` login (dummy verify anti-enumeración; 403 inactivo sin last_login; last_login+commit; token) + logout stateless. RED: test_auth AUTH-1 (login OK+claims+last_login), AUTH-2 (401 indistinguible), AUTH-3 (403 sin last_login), sin-hash→401. Done: verde. Dep: A8, A9
- [x] B3 dependencies: `src/api/presentation/dependencies.py` get_current_user (inválido/expirado→401; inexistente→401; inactivo→403) + require_role. RED: test_auth AUTH-5. Done: verde. Dep: A5, B2
- [x] B4 router + wiring: `src/api/presentation/routers/auth.py` (login público, logout 204) + `src/api/main.py` (include_router, handlers DomainError→ErrorResponse). RED: test_auth AUTH-4 (logout 204). Done: suite auth verde, /health intacto. Dep: B2, B3

## PR-C: core-users

- [x] C1 schemas: `src/api/presentation/schemas/user.py` UserCreate/Update/Read (sin password_hash; password min 8). RED: test_users USR-7 (422 forma). Done: verde. Dep: A1
- [x] C2 user_service: `src/api/domain/services/user_service.py` list/get(404)/create(409 rol inexistente + email dup; argon2; commit)/update(404; re-hash solo si password). RED: test_users USR-1..USR-6 (list sin hashes; create 201+argon2; dup 409; role 409; Researcher 403; PUT conserva/re-hashea; GET 404). Done: verde. Dep: A8, B3
- [x] C3 router + wiring: `src/api/presentation/routers/users.py` + `src/api/main.py`. RED: escenarios USR a nivel HTTP. Done: suite verde. Dep: C2

## PR-D: core-applications

- [x] D1 schemas: `src/api/presentation/schemas/application.py` Create/Update/Read (api_token_hash: null, ADR-16). RED: test_applications APP-6 (name vacío 422). Done: verde (schema + HTTP 422). Dep: —
- [x] D2 application_service: `src/api/domain/services/application_service.py` list/get(404)/create(api_token_hash=None)/update(404)/delete(404; FK RESTRICT→409+rollback). RED: test_applications APP-1..APP-5 (create 201 null; list/detail 200; detail 404; Researcher 403; delete 204→GET 404; delete con sesiones 409→GET 200; PUT 404). Done: verde. Dep: A8, B3
- [x] D3 router + wiring: `src/api/presentation/routers/applications.py` + `src/api/main.py`. Done: suite verde. Dep: D2
- [x] D4 OpenAPI: `openspec/specs/openapi.yaml` +6 paths (11 ops), bearerAuth aplicado, schemas nuevos, apiKey sin aplicar, existentes intactos (OAS-1..5). Done: YAML válido + schemathesis conformance verde (not_a_server_error, status_code/content_type/response_headers/response_schema_conformance; 11 ops, 304-357 casos según seed, 0 fallas). Dep: B4, C3, D3

### Fixes de contrato (contract testing de D4, bugs latentes de PR-C)

- [x] F1 NoNul: strings con NUL (`\x00`) → 422 (antes 500: CharacterNotInRepertoireError de Postgres). Validador compartido en schemas/common aplicado a name/password (user) y name/description (application).
- [x] F2 role_id fuera de rango SMALLINT (int16) → 409 (antes 500: OverflowError de asyncpg). get_role_by_id traduce DBAPIError → None (USR-4, ADR-14).

## Next recommended

**verify** — el cambio ISS-S2-01 quedó completo (21/21 tareas: PR-A 10, PR-B 4, PR-C 3, PR-D 4 + fixes F1-F2). Ejecutar verificación independiente del cambio completo: pytest --cov=src (78.8%), lint, openapi.yaml y schemathesis conformance.