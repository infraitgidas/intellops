# Proposal: ISS-S2-02 — Aplicaciones y credenciales de ingesta

**Cambio**: ISS-S2-02 (#36). **Base**: PR #53.

## Intent

Emisión/rotación/revocación de API key por aplicación, activación/inactivación y guard `require_api_key` para ingesta `/telemetry/*` (binding 1:1 key→app). Activa infra dormida de S2-01; cubre criterios 2–5; prerrequisito de #37; aporta a H3.

## Scope

### In Scope
- Migración 0003: `application.is_active BOOLEAN NOT NULL DEFAULT TRUE` + sync ddl_v1.0.sql.
- POST /applications/{id}/api-key (Admin): key `ilp_` CSPRNG 32 B, hash SHA-256, show-once; 404; 409 si key activa.
- `is_active` en schemas; app inactiva invalida su key (403).
- Guard `require_api_key` (X-API-Key): ausente/inválida → 401; app inactiva → 403; inyecta `Application` (app_id del payload nunca se confía).
- OpenAPI: `apiKey` en /telemetry/* (handlers #37); retiro `api_token_hash` de `ApplicationRead` (ADR-16).
- Redacción de X-API-Key en logs.

### Out of Scope
- Handlers /telemetry/* (#37); multi-credencial/overlap (E2); rate limiting; ingesta S1.

## Capabilities

### New Capabilities
- `app-credentials`: emisión/rotación/revocación de key (show-once, SHA-256, 409).
- `ingest-auth`: guard `require_api_key`, 401/403, binding 1:1 key→app.

### Modified Capabilities
- `applications-api`: `is_active`; retiro de `api_token_hash`; endpoint api-key.
- `openapi`: `apiKey` en /telemetry/*; ApplicationRead sin `api_token_hash`.

## Approach

E1: guard reutilizable + emisión sobre `api_token_hash` existente; 0003 solo agrega `is_active`. Validación SHA-256 hex timing-safe, lookup por prefijo `ilp_`. Regenerar sobre key activa → 409. Strict TDD: unit, integration (httpx + Postgres), contract (schemathesis; 3.1 experimental), migración. Footprint: sin servicios nuevos; ~1μs/validación.

## Affected Areas

| Area | Impact | Descripción |
|------|--------|-------------|
| `.../migrations/versions/0003_is_active.py` + `ddl_v1.0.sql` | Nuevo/Mod | is_active |
| `src/api/domain/{entities/application.py,services/application_service.py}` | Modificado | is_active, emitir/rotar, activar/inactivar |
| `src/api/presentation/{dependencies.py,routers/applications.py,schemas/application.py}` | Modificado | require_api_key, api-key, retiro hash |
| `src/api/infrastructure/security/api_keys.py` | Modificado | uso activo |
| `openspec/specs/openapi.yaml` | Modificado | apiKey /telemetry/* |
| `tests/` | Nuevo | key endpoints, ingest auth, 0003 |

Módulos: seguridad, QA.

## Risks

| Riesgo | Prob. | Mitigación |
|--------|-------|------------|
| Single-active-key vs overlap | Media | Rotación 2 pasos (C14–C17) |
| OpenAPI 3.1 experimental (Schemathesis) | Media | Flag experimental |
| ADR-16 breaking: `api_token_hash` es `required` (openapi.yaml:978) | Alta | Spec: quitar de required + tests en el mismo cambio |
| Scope creep a #37 | Media | Guard reutilizable; handlers fuera |
| Fuga de key o logs | Media | Plaintext nunca persiste; redacción en logs |

## Rollback Plan

- DB: `alembic downgrade 0002` (0003 aditiva, DEFAULT TRUE).
- Código: revert del PR.
- Contrato: revert diff de openapi.yaml.

## Dependencies

- ISS-S2-01: `api_token_hash`, `get_by_api_token_hash`, `api_keys`.
- Postgres 16 CI; schemathesis.

## Success Criteria

- [ ] Tests TDD: emisión (201/409/404, show-once), guard (401/403), aislamiento A≠B.
- [ ] `alembic upgrade/downgrade` limpios; cobertura ≥70%.
- [ ] openapi.yaml válido; `api_token_hash` fuera de ApplicationRead; schemathesis verde.