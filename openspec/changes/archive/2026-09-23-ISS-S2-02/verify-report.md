```yaml
schema: gentle-ai.verify-result/v1
evidence_revision: sha256:058522c4884473f608fa8fc052246a6cc0e391114dfd066a2e88ed420893b27a
verdict: pass
blockers: 0
critical_findings: 0
requirements: 26/26
scenarios: 18/18
test_command: PYTHONPATH=. .venv/bin/pytest -q --no-header
test_exit_code: 0
test_output_hash: sha256:b160551f2a0e294860753732fc9d8c4e09022e2613b8282233d7d535bf06f288
build_command: docker compose build intellops-core
build_exit_code: 0
build_output_hash: sha256:7788785f36355e4c034add9f4c4bbaa48dd55f6dd2da11b9852c3151bd3802d3
```

## Verification Report

**Change**: ISS-S2-02 — Aplicaciones y credenciales de ingesta (GitHub #36)
**Version**: spec.md (delta, 2026-09-18)
**Mode**: Strict TDD (config.yaml `apply.tdd:true`, `testing.strict_tdd:true`, runner pytest)
**Rama**: feat/ISS-S2-02
**Fecha**: 2026-09-23
**Tipo de verificación**: Independiente y fresca — suite completa re-ejecutada contra el estado actual del árbol (`HEAD` = 322cc1b). `evidence_revision` = SHA-256 del tree hash (`git rev-parse HEAD^{tree}` → `sha256:` + digest).

### Completeness

| Metric | Value |
|--------|-------|
| Tasks total | 23 |
| Tasks complete | 23 |
| Tasks incomplete | 0 |

Todas las tareas de `tasks.md` están marcadas `[x]` (verificado: 23 checkboxes, 23 completas; fases 1–5).

### Build & Tests Execution

**Build**: ✅ Passed (`docker compose build intellops-core`, exit 0)
```text
#17 DONE 14.6s
 Image intellops-intellops-core Built
```
- Imagen del build reconstruida con cache; el Dockerfile no cambió en este cambio (el CMD `alembic upgrade head && uvicorn api.main:app` queda intacto).

**Tests**: ✅ 142 passed / 0 failed / 1 xpassed
```text
PYTHONPATH=. .venv/bin/pytest -q --no-header
================= 142 passed, 1 xpassed, 31 warnings in 21.61s =================
```
- Distribución: `test_api_keys_endpoints.py` 18, `test_applications.py` 27, `test_auth.py` 16, `test_container_import_path.py` 6, `test_contract.py` 6 passed + 1 xpassed, `test_health.py` 2, `test_ingest_auth.py` 7, `test_migrations.py` 6, `test_ml_worker.py` 2, `test_security.py` 24, `test_users.py` 28. Total 143 colectados.
- El xpass corresponde a `test_schemathesis_live_contract_scoped` (xfail documentado, ADR-24): la corrida live de schemathesis contra la app ASGI valida casos reales y pasa — el gate contract queda verde (6 passed + 1 xpassed).

**Coverage**: 92.63% / threshold 70% → ✅ Above
```text
PYTHONPATH=. .venv/bin/pytest --cov=src --cov-report=term-missing --cov-fail-under=70 -q --no-header
Required test coverage of 70% reached. Total coverage: 92.63%
================= 142 passed, 1 xpassed, 31 warnings in 22.32s =================
```

**Lint**: ✅ `flake8 src/ tests/` exit 0 (sin salida). **Pylint**: ✅ `pylint src/ --fail-under=7.0` exit 0, 9.85/10 (única nota: E0401 `import-error` en `src/ml/pipeline/mock_reader.py`, archivo ML preexistente fuera del alcance de este cambio; no afecta el gate).

**Migraciones** (Postgres real vía docker, contenedor `intellops-intellops-db-1` healthy):
- `alembic current` → `0003 (head)`.
- `alembic downgrade 0002` → `Running downgrade 0003 -> 0002` (DROP `is_active`).
- `alembic upgrade head` → `Running upgrade 0002 -> 0003` (ADD `is_active`), `alembic current` → `0003 (head)`.
- Cobertura por tests: `tests/test_migrations.py` 6/6 passed (DATA-6..DATA-9 con Postgres real).

**openapi.yaml**: ✅ válido (YAML 3.1.0 cargado; 25 paths). Verificación estructural independiente: `ApplicationRead.required` = `[app_id, name, description, is_active, created_at]` (sin `api_token_hash`), `api_token_hash` ausente de `properties`; `apiKey` scheme declarado (`type: apiKey`, `in: header`, `name: X-API-Key`) sin `security: [apiKey]` en ningún path existente; paths POST/DELETE `/applications/{application_id}/api-key` presentes; `ApiKeyResponse` con `required: [api_key, hint]`.

### TDD Compliance

| Check | Result | Details |
|-------|--------|---------|
| TDD Evidence reported | ✅ | `apply-progress.md` con tabla "TDD Cycle Evidence" (23 filas) y "Work Unit Evidence" (unit único fases 1–5) |
| All tasks have tests | ✅ | 23/23 tareas con test file verificado en el repo |
| RED confirmed (tests exist) | ✅ | `test_api_keys_endpoints.py`, `test_ingest_auth.py`, `test_contract.py` (nuevos), `test_migrations.py`, `test_applications.py`, `test_security.py` (modificados) existen |
| GREEN confirmed (tests pass) | ✅ | 142 passed + 1 xpassed en ejecución independiente (exit 0) |
| Triangulation adequate | ✅ | 18 escenarios spec cubiertos por tests unit + integración + contract (múltiples casos por escenario: emisión 201/404/409, guard 401/403, rotación 2 pasos, aislamiento A≠B) |
| Safety Net for modified files | ✅ | `test_applications.py` 22/22→27/27, `test_security.py` 17/17→24/24, `test_migrations.py` 3/3→6/6 previos antes de modificar; archivos nuevos declaran `N/A (nuevo)` y efectivamente son untracked (verificado en git status) |

**TDD Compliance**: 6/6 checks passed

### Test Layer Distribution

| Layer | Tests | Files | Tools |
|-------|-------|-------|-------|
| Unit | 24 | `test_security.py` (24) | pytest |
| Integration (HTTP + Postgres real) | 58 | `test_api_keys_endpoints.py` (18), `test_applications.py` (27), `test_ingest_auth.py` (7), `test_migrations.py` (6) | pytest + httpx AsyncClient + SQLAlchemy async + Alembic |
| Contract | 7 (6 passed + 1 xpassed) | `test_contract.py` | schemathesis 4.x + yaml |
| **Total** | **143** | **4 changed + suite completa** | |

### Changed File Coverage

| File | Line % | Uncovered | Rating |
|------|--------|-----------|--------|
| `src/api/domain/entities/application.py` | 100% | — | ✅ Excellent |
| `src/api/domain/exceptions.py` | 100% | — | ✅ Excellent |
| `src/api/domain/services/application_service.py` | 99% | L150 | ✅ Excellent |
| `src/api/domain/repositories/application_repository.py` | 97% | L40 | ✅ Excellent |
| `src/api/infrastructure/db/migrations/versions/0003_is_active.py` | 100% | — | ✅ Excellent |
| `src/api/infrastructure/security/api_keys.py` | 97% | L62 | ✅ Excellent |
| `src/api/main.py` | 97% | L75 | ✅ Excellent |
| `src/api/presentation/dependencies.py` | 100% | — | ✅ Excellent |
| `src/api/presentation/errors.py` | 100% | — | ✅ Excellent |
| `src/api/presentation/routers/applications.py` | 100% | — | ✅ Excellent |
| `src/api/presentation/schemas/application.py` | 100% | — | ✅ Excellent |

**Promedio de archivos cambiados**: ≥97% — todos ≥80% (gate de calidad strict-TDD sin WARNING).

### Assertion Quality

**Assertion quality**: ✅ All assertions verify real behavior. Los tests afirman status codes (201/204/401/403/404/409/422), códigos de error del contrato (`invalid_api_key`, `app_inactive`, `key_exists`, `not_found`), header `WWW-Authenticate: ApiKey`, persistencia de hash SHA-256 hex en DB real, show-once (plaintext nunca expuesto en GET/PUT/listado), fail-closed (key revocada → 401 idéntico), aislamiento A≠B, redacción en msg/args/traceback y esquema de migración en información_schema. Sin tautologías, ghost loops ni smoke-only (el loop de `test_probe_401_identical_for_missing_and_invalid_keys` itera sobre 2 respuestas fijas no vacías).

### Spec Compliance Matrix

Requisitos: 26/26 (CRED-1..5, IAUTH-1..5, APP-7..9, OAS-6..10, DATA-6..9, SEC-7..10). Escenarios: 18/18.

| Req | Escenario | Test | Result |
|-----|-----------|------|--------|
| CRED-1 | Emisión show-once | `test_api_keys_endpoints.py > test_post_api_key_201_show_once`, `test_service_issue_api_key_returns_key_and_persists_only_sha256` | ✅ COMPLIANT |
| CRED-2 | Emisión sobre aplicación inexistente | `test_api_keys_endpoints.py > test_post_api_key_404_unknown_app`, `test_service_issue_api_key_404_for_unknown_app`, `test_delete_api_key_404_unknown_app` | ✅ COMPLIANT |
| CRED-3 | Regenerar con key activa | `test_api_keys_endpoints.py > test_post_api_key_409_with_active_key_previous_key_still_valid`, `test_service_issue_api_key_409_when_active_key_exists` | ✅ COMPLIANT |
| CRED-3/4 | Rotación en dos pasos | `test_api_keys_endpoints.py > test_two_step_rotation_old_key_invalid_new_key_valid` | ✅ COMPLIANT |
| CRED-4 | DELETE fail-closed idempotente | `test_api_keys_endpoints.py > test_delete_api_key_204_fail_closed_idempotent`, `test_service_revoke_api_key_is_idempotent_and_fail_closed` | ✅ COMPLIANT |
| CRED-5 | Aislamiento entre aplicaciones | `test_api_keys_endpoints.py > test_isolation_key_of_app_a_authenticates_as_a_never_b` | ✅ COMPLIANT |
| CRED-5 | Show-once (ni key ni hash en GET/PUT) | `test_api_keys_endpoints.py > test_api_key_never_exposed_in_list_or_update` | ✅ COMPLIANT |
| IAUTH-1 | Key ausente | `test_ingest_auth.py > test_probe_401_missing_key_with_www_authenticate` | ✅ COMPLIANT |
| IAUTH-1/3 | Key inválida | `test_ingest_auth.py > test_probe_401_identical_for_missing_and_invalid_keys`, `test_api_keys_endpoints.py > test_service_authenticate_api_key_rejects_no_prefix_format` | ✅ COMPLIANT |
| IAUTH-1/APP-8 | Aplicación inactiva | `test_ingest_auth.py > test_probe_403_app_inactive_then_reactivate`, `test_api_keys_endpoints.py > test_service_authenticate_api_key_inactive_app_403` | ✅ COMPLIANT |
| IAUTH-1 | Key revocada | `test_ingest_auth.py > test_probe_401_revoked_key_indistinguishable`, `test_api_keys_endpoints.py > test_service_authenticate_api_key_rejects_revoked_key` | ✅ COMPLIANT |
| IAUTH-2 | Binding 1:1 — payload no confiable | `test_ingest_auth.py > test_probe_binding_1_1_ignores_claimed_app_id_in_payload` | ✅ COMPLIANT |
| IAUTH-4 | Redacción de logs | `test_security.py > test_redact_api_key_hides_full_key_value`, `test_redaction_filter_redacts_record_message`, `test_redaction_filter_redacts_record_args`, `test_redaction_filter_redacts_traceback_text` | ✅ COMPLIANT |
| IAUTH-5 | Guard reutilizable sin wiring | `test_ingest_auth.py > test_prod_app_has_no_api_key_wiring`, `test_probe_injects_authenticated_application` | ✅ COMPLIANT |
| APP-7 | Inactivar aplicación | `test_ingest_auth.py > test_probe_403_app_inactive_then_reactivate`, `test_applications.py > test_update_application_is_active_mutable_and_persisted` | ✅ COMPLIANT |
| APP-8 | Reactivar aplicación | `test_ingest_auth.py > test_probe_403_app_inactive_then_reactivate` (segunda mitad: PUT true → 200 + key vuelve a autenticar) | ✅ COMPLIANT |
| APP-9 | ApplicationRead sin hash | `test_applications.py > test_application_read_does_not_expose_api_token_hash`, `test_get_application_detail_200`, `test_contract.py > test_oas8_application_read_has_no_api_token_hash` | ✅ COMPLIANT |
| OAS-6/10 | Contrato válido tras ADR-16 | `test_contract.py > test_oas6_api_key_scheme_declared_without_security_on_existing_paths`, `test_oas7_api_key_paths_declared_with_expected_statuses`, `test_oas7_api_key_response_schema_show_once`, `test_oas8_application_read_has_no_api_token_hash`, `test_oas9_openapi_document_loads_in_schemathesis`, `test_schemathesis_live_contract_scoped` (xpassed) | ✅ COMPLIANT |
| OAS-6/10 | Ingesta existente sin exigencia de key | `test_contract.py > test_oas6_api_key_scheme_declared_without_security_on_existing_paths` (202/400/429/503 en /metrics/ingest y /logs/ingest sin security) | ✅ COMPLIANT |
| DATA-6/7 | Upgrade a head | `test_migrations.py > test_upgrade_head_adds_is_active_default_true_for_existing_rows`, `test_upgrade_head_adds_columns_indexes_and_seed` | ✅ COMPLIANT |
| DATA-8 | Downgrade a 0002 | `test_migrations.py > test_downgrade_0002_removes_is_active_only` | ✅ COMPLIANT |
| DATA-9 | ddl_v1.0.sql sincronizado | `test_migrations.py > test_ddl_v1_0_sql_synced_with_0003` | ✅ COMPLIANT |

**Compliance summary**: 18/18 escenarios con test pasando en ejecución independiente.

### Correctness (Static Evidence)

| Requisito | Status | Notas |
|-----------|--------|-------|
| CRED-1..5 | ✅ Implementado | `issue_api_key`/`revoke_api_key` en `application_service.py` (404/409/204, show-once, hash SHA-256 hex); router POST/DELETE `/applications/{id}/api-key` solo Admin (201/204/404/409/403); `ApiKeyResponse {api_key, hint}` |
| IAUTH-1..5 | ✅ Implementado | `require_api_key` en `dependencies.py`: `APIKeyHeader("X-API-Key", auto_error=False)`; 401 `invalid_api_key` + `WWW-Authenticate: ApiKey`; 403 `app_inactive`; inyecta `Application`; sin wiring en paths existentes |
| APP-7..9 | ✅ Implementado | `is_active` default true en Create, mutable en Update, presente en Read; `api_token_hash` ausente de `ApplicationRead` (Pydantic y openapi.yaml) |
| OAS-6..10 | ✅ Implementado | scheme `apiKey` declarado sin `security:` en paths existentes; paths api-key con bearerAuth y statuses declarados; `ApiKeyResponse`; Documento 3.1 carga en schemathesis |
| DATA-6..9 | ✅ Implementado | `0003_is_active.py` (revision 0003, down_revision 0002, ADD/DROP `is_active`, no toca 0001/0002); `ddl_v1.0.sql` sincronizado con comentario de trazabilidad |
| SEC-7 | ✅ Implementado | Plaintext nunca persiste (solo SHA-256 hex); show-once verificado; prefijo `ilp_` no es secreto |
| SEC-8 | ✅ Implementado | `secrets.token_bytes(32)` (≥256 bits); SHA-256 hex; `hmac.compare_digest` timing-safe; sin KDF lento en hot path |
| SEC-9 | ✅ Implementado | 409 ante regeneración con key activa; revocación inmediata fail-closed |
| SEC-10 | ✅ Implementado | Lookup indexado por hash + SHA-256 (~1μs); sin servicios nuevos (evidencia estática; sin benchmark de latencia dedicado) |

### Coherence (Design)

| Decisión (ADR) | Followed? | Notas |
|----------------|-----------|-------|
| ADR-17 (E1: `api_token_hash` único) | ✅ Yes | Columna única; `issue_api_key` → 409 si hash != NULL |
| ADR-18 (DELETE fail-closed 204 + 409 en key activa) | ✅ Yes | `revoke_api_key` 204 idempotente; `issue_api_key` 409 `key_exists` |
| ADR-19 (gate `ilp_` → SHA-256 → `compare_digest`) | ✅ Yes | `authenticate_api_key`: `startswith("ilp_")`, `hash_api_key`, `hmac.compare_digest` |
| ADR-20 (NOT NULL DEFAULT TRUE) | ✅ Yes | Migración 0003 + entidad `server_default=text("TRUE")` |
| ADR-21 (ADR-16: retirar hash de ApplicationRead) | ✅ Yes | Pydantic + openapi.yaml sin `api_token_hash`; tests en el mismo cambio |
| ADR-22 (401/403 separados con WWW-Authenticate) | ✅ Yes | 401 `invalid_api_key` + `WWW-Authenticate: ApiKey`; 403 `app_inactive` |
| ADR-23 (filtro global de redacción) | ✅ Yes | `ApiKeyRedactionFilter` instalado en `main.py` sobre el root logger |
| ADR-24 (schemathesis 4.x con xfail documentado) | ✅ Yes | `schemathesis>=4.0.0` dev-dep; `OPEN_API_3_1.enable()` con rama legacy + fallback; test live envuelto en xfail documentado (xpassed en la corrida) |

### Issues Found

**CRITICAL**: None

**WARNING**: None

**SUGGESTION**:
- **SUG-1 — SEC-10 sin benchmark de latencia**: el objetivo de ~1μs de validación se sustenta en evidencia estática (lookup indexado + SHA-256, sin servicios nuevos), pero no hay un test/benchmark que lo mida. No bloquea: el requisito es operativo y el diseño lo cumple por construcción.
- **SUG-2 — Premisa experimental de OAS-9 superada (ADR-24)**: la spec asumía soporte experimental de OpenAPI 3.1 en schemathesis; 4.x lo trae nativo y el `OPEN_API_3_1.enable()` queda como rama legacy documentada. Documentado en apply-progress; el gate queda verde (xpassed).
- **SUG-3 — Drift del /openapi.json servido (preexistente)**: FastAPI genera el spec servido desde los routers (sin `responses=` declarados), por lo que no documenta los códigos de error 401/403/404/409 de los paths api-key. El archivo canónico `openspec/specs/openapi.yaml` sí los documenta. Mismo hallazgo WARNING-1 de ISS-S2-01; no afecta comportamiento ni archive.

### Verdict

**PASS** — Suite completa 142 passed + 1 xpassed (exit 0), cobertura 92.63% ≥ 70%, flake8 limpio y pylint 9.85/10. Migraciones `alembic downgrade 0002` / `upgrade head` limpias sobre Postgres real (docker). Contrato openapi.yaml válido con ADR-16 aplicado (`api_token_hash` fuera de `ApplicationRead`), scheme `apiKey` declarado sin `security:` en paths existentes (wiring diferido a #37) y paths api-key con bearerAuth. 18/18 escenarios de spec con test pasando en ejecución independiente; 26/26 requisitos con evidencia. ADR-17..24 reflejados en el código. Sin hallazgos críticos ni blockers.