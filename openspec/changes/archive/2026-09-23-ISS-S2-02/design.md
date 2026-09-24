# DESIGN — ISS-S2-02: Aplicaciones y credenciales de ingesta

**Base**: proposal, spec r1, research r3, código real. **Modo**: openspec. **Idioma**: español neutro técnico.

## 1. Enfoque técnico

Activa la infra dormida de S2-01 sin servicios nuevos: `api_token_hash` único (E1) es la credencial; 0003 agrega `is_active`. Emisión/revocación viven en `ApplicationService` (ADR-10: el servicio commitea); `require_api_key` delega en él y NO se cablea a ningún path (handlers en #37); guard y emisión comparten `api_keys.py`. ADR-16: el hash se retira de `ApplicationRead` (Pydantic + OpenAPI) con sus tests juntos.

### Flujo

```mermaid
sequenceDiagram
  participant A as Admin
  participant R as Router
  participant S as ApplicationService
  participant G as require_api_key
  A->>R: POST /applications/{id}/api-key (bearer Admin)
  R->>S: issue_api_key(id): 404 si no existe; 409 si hash!=NULL
  S-->>A: 201 {api_key, hint} show-once (generate+hash+commit)
  G->>S: authenticate_api_key(X-API-Key)
  S-->>G: 401 formato/hash; 403 app_inactive; o Application
```

## 2. Decisiones de arquitectura (ADR)

| # | Decisión | Opciones | Tradeoff | Decisión |
|---|----------|----------|----------|----------|
| 17 | Credencial | E1 columna vs E2 tabla multi-key | E2 da overlap/auditoría; suma tabla, migración y endpoints | **E1**: `api_token_hash` único |
| 18 | Revocación | DELETE explícito vs POST reemplaza vs overlap | Reemplazo/overlap oculta compromisos (C17) | **DELETE fail-closed** 204 idempotente; POST con key activa 409 |
| 19 | Lookup guard | Igualdad SQL vs prefijo+`compare_digest` | SQL filtra timing (CWE-208); `ilp_` no discrimina | **Gate `ilp_` → lookup indexado SHA-256 → `hmac.compare_digest`** |
| 20 | `is_active` | NOT NULL DEFAULT TRUE vs nullable | Nullable rompe filas | **NOT NULL DEFAULT TRUE** (aditiva) |
| 21 | ADR-16 | Retirar hash ahora vs mantener null | Expone dato interno (C28) | **Retirar de `ApplicationRead`** (Pydantic + OpenAPI + tests juntos) |
| 22 | 401/403 | Todo 403 vs separados | 403 uniforme es laxo (C3) | **401 `invalid_api_key` + `WWW-Authenticate: ApiKey`; 403 `app_inactive`** |
| 23 | Redacción | No loguear vs filtro global | No cubre tracebacks de terceros | **`ApiKeyRedactionFilter`** global sobre `ilp_<43>` |
| 24 | Contract 3.1 | Bloquear vs degradar | Schemathesis 3.1 experimental | **Experimental + `xfail` documentado**, gate verde |

## 3. Archivos afectados

| Archivo | Acción | Cambio |
|---------|--------|--------|
| `.../migrations/versions/0003_is_active.py` | Nuevo | revision 0003, down_revision 0002 |
| `openspec/specs/database/ddl_v1.0.sql` | Mod | `is_active` |
| `.../entities/application.py` | Mod | `is_active` |
| `.../services/application_service.py` | Mod | emitir/revocar/autenticar; `is_active` |
| `.../repositories/application_repository.py` | Mod | docstring |
| `.../presentation/dependencies.py` | Mod | `require_api_key` |
| `.../routers/applications.py` | Mod | POST/DELETE api-key |
| `.../schemas/application.py` | Mod | `is_active`, sin hash; `ApiKeyResponse` |
| `.../domain/exceptions.py` | Mod | `headers` |
| `.../security/api_keys.py` | Mod | `redact_api_key` + filtro |
| `src/api/main.py` | Mod | instala filtro; propaga headers |
| `openspec/specs/openapi.yaml` | Mod | paths api-key, `ApiKeyResponse`, `is_active`, sin hash |
| `tests/test_api_keys_endpoints.py` | Nuevo | emisión/rotación/revocación |
| `tests/test_ingest_auth.py` | Nuevo | guard (app probe) |
| `tests/test_security.py`, `tests/test_migrations.py` | Mod | redacción; 0003 |
| `tests/test_contract.py` | Nuevo | schemathesis 3.1 |
| `pyproject.toml`, `.github/workflows/ci.yml` | Mod | dev-dep + step contract |

## 4. Interfaces / contratos

```python
async def require_api_key(
    api_key: Annotated[str | None, Depends(APIKeyHeader("X-API-Key", auto_error=False))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> Application

class IssuedApiKey(NamedTuple): api_key: str; hint: str
async def issue_api_key(app_id: UUID) -> IssuedApiKey        # 404 | 409
async def revoke_api_key(app_id: UUID) -> None               # 404; idempotente
async def authenticate_api_key(raw_key: str) -> Application  # 401 | 403 app_inactive
```

`DomainError(..., headers=None)`; `main.py` pasa `headers=exc.headers`. `ApiKeyResponse {api_key, hint}` (últimos 4 chars, no persistido). Path `/applications/{application_id}/api-key`.

## 5. Estrategia de tests (strict TDD)

| Capa | Qué | Enfoque |
|------|-----|---------|
| Unit | formato/hash/redacción; guard con repo stub | 401 malformado, 403 inactiva, `compare_digest` |
| Integration | 201/409/404, show-once, DELETE 204 idempotente, rotación, aislamiento A≠B, `is_active`, sin hash | httpx + Postgres |
| Guard | 401 indistinguibles, `WWW-Authenticate`, payload no confiable | app de prueba `/_probe` (prod sin wiring) |
| Contract | openapi válido; 2xx/401/403/404/409/422 | `schemathesis` + `OPEN_API_3_1.enable()`; `xfail` |
| Migración | upgrade head / downgrade 0002 | extiende `test_migrations.py` |

Cada escenario Given/When/Then → test RED antes del código (`tdd: true`).

## 6. Threat Matrix

N/A — endpoints HTTP FastAPI y una migración; sin shell, subprocess, VCS/PR automation, clasificación de ejecutables ni integración de procesos.

## 7. Migración / Rollout

Upgrade: `ALTER TABLE application ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT TRUE`; downgrade: `DROP COLUMN is_active`. 0001/0002 e índice intactos; `ddl_v1.0.sql` sincronizado. Rollback: `alembic downgrade 0002` + revert del PR + del contrato. Footprint intacto (~1µs, CPU-only, <2GB RAM).

## 8. Preguntas abiertas

- [ ] OAS-6 nombra `/telemetry/*` (hoy `/metrics/ingest`, `/logs/ingest`): ¿aplicabilidad = scheme `apiKey` sin `security:` hasta #37?
- [ ] `hint` no se persiste: ¿solo aparece en el 201?

## Next recommended

**tasks** — ADR-17..24 y escenarios a tareas TDD con forecast.
