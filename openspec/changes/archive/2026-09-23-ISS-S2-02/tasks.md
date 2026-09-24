# Tasks: ISS-S2-02 — Aplicaciones y credenciales de ingesta

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 900–1300 |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR 1 → PR 2 → PR 3 → PR 4 |
| Delivery strategy | single-pr |
| Chain strategy | size-exception |

Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: size-exception
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| 1 | Migración 0003 + `is_active` + redacción | PR 1 | `pytest tests/test_migrations.py tests/test_applications.py -q` | `alembic upgrade head && alembic downgrade 0002` | Revertir 0003, ddl y schemas |
| 2 | Credenciales + endpoints api-key | PR 2 | `pytest tests/test_api_keys_endpoints.py -q` | httpx ASGI + Postgres | Revertir router/servicio/schemas |
| 3 | Guard `require_api_key` + `/_probe` | PR 3 | `pytest tests/test_ingest_auth.py tests/test_security.py -q` | `/_probe` test-only (sin wiring prod) | Revertir `dependencies.py` y el probe |
| 4 | Contrato OpenAPI + schemathesis + CI | PR 4 | `pytest tests/test_contract.py -q` | `schemathesis run` en CI | Revertir `openapi.yaml` y CI |

## Fase 1 — Fundación e infraestructura

- [x] 1.1 RED `tests/test_migrations.py`: upgrade head/downgrade 0002 (DATA-6..DATA-9).
- [x] 1.2 Crear `src/api/infrastructure/db/migrations/versions/0003_is_active.py` (`0003`→`0002`, ADD/DROP `is_active`).
- [x] 1.3 Sincronizar `openspec/specs/database/ddl_v1.0.sql` con `is_active`.
- [x] 1.4 RED `tests/test_applications.py`: APP-7/APP-8 (`is_active` default true, mutable por PUT).
- [x] 1.5 `is_active` en `src/api/domain/entities/application.py` y `src/api/presentation/schemas/application.py`.
- [x] 1.6 `headers` en `DomainError` (`src/api/domain/exceptions.py`) y propagación en `src/api/main.py`.
- [x] 1.7 `redact_api_key` + `ApiKeyRedactionFilter` en `src/api/infrastructure/security/api_keys.py`; instalar en `src/api/main.py`.

## Fase 2 — Núcleo: credenciales y guard

- [x] 2.1 RED `tests/test_api_keys_endpoints.py`: CRED-1..CRED-5 (201/404/409/204, show-once).
- [x] 2.2 `issue_api_key`/`revoke_api_key`/`authenticate_api_key` en `src/api/domain/services/application_service.py`; docstring de `src/api/domain/repositories/application_repository.py`.
- [x] 2.3 `ApiKeyResponse` y retiro de `api_token_hash` de `ApplicationRead` en `src/api/presentation/schemas/application.py` (ADR-16) con `tests/test_applications.py`.
- [x] 2.4 RED `tests/test_ingest_auth.py`: IAUTH-3 formato sin `ilp_` y `compare_digest` → 401.
- [x] 2.5 `require_api_key` en `src/api/presentation/dependencies.py` (401 `invalid_api_key` + WWW-Authenticate; 403 `app_inactive`; inyecta `Application`).

## Fase 3 — Integración y wiring

- [x] 3.1 POST/DELETE `/applications/{application_id}/api-key` (read-only) (solo Admin) en `src/api/presentation/routers/applications.py`.
- [x] 3.2 App `/_probe` (read-only) en `tests/conftest.py` con `require_api_key` (prod sin wiring, IAUTH-5).
- [x] 3.3 Paths api-key + `ApiKeyResponse` y `apiKey` sin `security:` en `openspec/specs/openapi.yaml` (OAS-6/OAS-7).
- [x] 3.4 Quitar `api_token_hash` de `ApplicationRead` en `openspec/specs/openapi.yaml` (OAS-8).

## Fase 4 — Testing

- [x] 4.1 `tests/test_api_keys_endpoints.py`: aislamiento A≠B y rotación en dos pasos (CRED-1..CRED-5).
- [x] 4.2 `tests/test_ingest_auth.py`: 401 indistinguibles, 403 `app_inactive`, binding 1:1 (IAUTH-1..IAUTH-3, APP-8).
- [x] 4.3 `tests/test_security.py`: redacción de X-API-Key en logs y tracebacks (IAUTH-4, SEC-7..SEC-10).
- [x] 4.4 `tests/test_contract.py`: schemathesis `OPEN_API_3_1.enable()`, checks 2xx/401/403/404/409/422 (OAS-9/OAS-10, `xfail`).
- [x] 4.5 `schemathesis` en `pyproject.toml` dev-deps y step contract en `.github/workflows/ci.yml` (OAS-9).
- [x] 4.6 `pytest --cov=src` ≥70% y validar `openspec/specs/openapi.yaml` (read-only).

## Fase 5 — Limpieza y documentación

- [x] 5.1 Actualizar CHANGELOG/docs; sin `api_token_hash` en respuestas ni código temporal.
