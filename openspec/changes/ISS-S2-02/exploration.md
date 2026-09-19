# EXPLORATION — ISS-S2-02: Aplicaciones y credenciales de ingesta

**Cambio**: ISS-S2-02 (GitHub #36). **Base**: `develop` con ISS-S2-01 mergeado (PR #53). **Fuente de verdad**: `docs/business/issues-s2-s3.md` (reemplaza a `issues-s1-s2.md`, ver Riesgo R1). **Modo**: openspec. **Idioma**: español neutro técnico.

**Criterios de aceptación del issue #36** (mapeados a código real relevado):

| # | Criterio | Estado hoy | Evidencia |
|---|----------|-----------|-----------|
| 1 | Creación de aplicaciones | **YA CUBIERTO (S2-01)** | `POST /applications` (Admin, 201), `GET/PUT/DELETE /applications/{id}` — APP-1..APP-6 en spec archivada; tests en `tests/test_applications.py` |
| 2 | Activación/inactivación | **FALTA** | `application` NO tiene columna `is_active` (migración 0001; 0002 solo agrega `api_token_hash`). Diseño archivado ADR-07 y proposal S2-01 planifican `application.is_active` en **migración 0003** |
| 3 | Validación de credenciales | **FALTA (infra dormida lista)** | `infrastructure/security/api_keys.py` (generate/hash SHA-256, test A6 en `test_security.py`), `ApplicationRepository.get_by_api_token_hash` implementado pero sin uso; NO hay endpoint de emisión ni dependency de validación X-API-Key |
| 4 | Autorización de ingesta | **FALTA (guard; endpoints son de #37)** | `main.py` NO tiene routers de ingesta; OpenAPI declara `securitySchemes.apiKey` (X-API-Key) **sin aplicar a ningún path** (OAS-3: "aplicación en S2-02"). Los endpoints `/telemetry/metrics` y `/telemetry/exceptions` son del issue #37 (ISS-S2-03), dependiente de este |
| 5 | Aislamiento entre aplicaciones | **FALTA (decisión arquitectónica ya tomada)** | Proposal S2-01: "tenant scoping por credencial (app_id resuelto de la API key, nunca del payload) se implementa en S2-02" — el mecanismo de aislamiento es binding 1:1 credencial→aplicación |

---

## 1. Estado actual (código real, ISS-S2-01 mergeado)

### Modelo de APPLICATION

- **DDL** (`openspec/specs/database/ddl_v1.0.sql`, fuente de verdad): `application(app_id UUID PK, name TEXT NOT NULL, description TEXT, api_token_hash VARCHAR(64), created_at)` + `idx_application_api_token_hash UNIQUE WHERE api_token_hash IS NOT NULL`. **Sin `is_active`.**
- **Migración 0001** crea la tabla sin credenciales; **0002** (`0002_credentials.py`) agrega `api_token_hash VARCHAR(64)` nullable (dormida, ADR-03) e índice único parcial. No existe 0003.
- **Entidad** `src/api/domain/entities/application.py`: SQLAlchemy 2.0 typed, `api_token_hash: Mapped[str | None]`, índice único parcial declarado.
- **Repositorio** `sqlalchemy_application_repository.py`: `get_by_id/list/create/update/delete` + **`get_by_api_token_hash` ya implementado** (dormido, sin callers). Protocol `ApplicationRepository` ya declara el método (contrato para S2-02).
- **Servicio** `application_service.py`: CRUD completo; create deja `api_token_hash=None` (ADR-16); delete físico con 409 por FK RESTRICT (ADR-07/ADR-10).
- **Schemas** `presentation/schemas/application.py`: `ApplicationCreate{name≥1, description?}`, `ApplicationUpdate`, `ApplicationRead{..., api_token_hash: None, created_at}` — ADR-16: campo presente y SIEMPRE null en S2-01; **S2-02 lo retira de respuestas** (comentario en schema y en openapi.yaml).
- **Router** `presentation/routers/applications.py`: GET (Admin+Researcher), POST/PUT/DELETE (Admin vía `require_role`), response_model solo lectura.

### Infraestructura de seguridad disponible (dormida, para activar)

- `infrastructure/security/api_keys.py`: `generate_api_key()` → `ilp_` + 43 chars base64url (32 bytes); `hash_api_key()` → SHA-256 hex 64 chars. Tests A6 ya verdes.
- `config.py`: `api_key_prefix = "ilp_"`.
- OpenAPI (`openspec/specs/openapi.yaml`): `securitySchemes.apiKey {type: apiKey, in: header, name: X-API-Key}` declarado, sin paths que lo usen (OAS-3 de S2-01). Paths de ingesta actuales `/metrics/ingest` y `/logs/ingest` son contrato S1 (renombrados a `/telemetry/*` por #37).
- Patrón de auth vigente: `dependencies.py` (`get_current_user` bearer + `require_role`), `DomainError` tipificadas (401/403/404/409) → `ErrorResponse`, servicios dueños del commit (ADR-10).

### Tests existentes relevantes

- `test_security.py` A6: formato/unicidad/hash de API keys (unit).
- `test_applications.py`: APP-1..APP-6 con fixtures async reales (Postgres, alembic upgrade head, `clean_db` truncando `application`, `make_admin`/`make_researcher`).
- CI (`.github/workflows/ci.yml`): `pytest --cov=src --cov-fail-under=70`, Postgres 16 service. Schemathesis declarado en config.yaml (contract layer) aunque no aparece en el job de CI actual.

---

## 2. Áreas afectadas (proyección)

| Archivo | Afectación |
|---|---|
| `src/api/infrastructure/db/migrations/versions/0003_*.py` | **Nuevo** — `application.is_active` (planificado como 0003 en ADR-07/proposal S2-01); posible tabla de credenciales si se decide multi-key |
| `openspec/specs/database/ddl_v1.0.sql` | Sync con 0003 (precedente DATA-5 de S2-01) |
| `src/api/domain/entities/application.py` | `is_active` (y entidad de credencial si aplica) |
| `src/api/domain/services/application_service.py` | Casos de uso: activar/inactivar, emitir/rotar/revocar key, validar credencial |
| `src/api/presentation/routers/applications.py` + `schemas/application.py` | Endpoint de emisión de key (Admin); campo `is_active`; **retirar `api_token_hash` de `ApplicationRead`** (ADR-16) |
| `src/api/presentation/dependencies.py` | Nueva dependency `require_api_key` (X-API-Key → hash → `get_by_api_token_hash` → check is_active) |
| `src/api/infrastructure/security/api_keys.py` | Uso activo (generate en emisión, hash en validación); posible rotación |
| `openspec/specs/openapi.yaml` | Aplicar `apiKey` a paths de ingesta; schemas nuevos; `ApplicationRead` sin `api_token_hash` |
| `tests/` | `test_applications.py` (ampliar), nuevo `test_api_keys_endpoints.py` / `test_ingest_auth.py`, `test_migrations.py` (0003), contract (schemathesis) |

---

## 3. Enfoques

### E1 — Guard X-API-Key + emisión de credencial + is_active (alcance mínimo de #36)

Credencial de una sola key activa por aplicación (columna existente `api_token_hash`), migración 0003 solo agrega `is_active`. El guard `require_api_key` resuelve la aplicación DESDE la key (nunca del payload — decisión ya tomada en S2-01) y rechaza keys de apps inactivas. En OpenAPI se aplica `apiKey` a los paths de ingesta (`/telemetry/*`) como contrato; los handlers los implementa #37.

- Pros: respeta el alcance declarado (#37 hace los endpoints); mínimo delta de schema (sin tabla nueva); activa infra ya dormida; aislamiento 1:1 por construcción.
- Cons: rotación sin ventana de overlap (la key vieja muere al regenerar); no soporta multi-credencial por app.
- Esfuerzo: Medio.

### E2 — E1 + tabla de credenciales (multi-key con rotación/revocación)

Modelo `app_credential(credential_id, app_id FK, api_token_hash UNIQUE, is_active, created_at, revoked_at)` en 0003; endpoints para listar/revocar/rotar con ventana de overlap opcional.

- Pros: rotación sin downtime; revocación selectiva; mayor fidelidad al criterio "gestionar credenciales" (plural).
- Cons: migración más grande (tabla nueva + backfill desde `application.api_token_hash`); más superficie de API y tests; el criterio de aceptación no exige multi-key explícitamente.
- Esfuerzo: Alto.

### E3 — E1 + implementar endpoints de ingesta en #36

Además del guard, implementar `/telemetry/metrics` y `/telemetry/exceptions` (aunque el dispatcher los asigna a #37).

- Pros: "autorización de ingesta" demostrable end-to-end en este cambio.
- Cons: **viola el alcance declarado** (el contrato de ingesta es de #37); solapa y duplica trabajo del issue #37; riesgo de conflictos de merge. No recomendado.
- Esfuerzo: Alto (y fuera de alcance).

---

## 4. Recomendación

**E1** (guard reutilizable + emisión de credencial + `is_active` en 0003), con estos puntos fijados:

1. **Migración 0003**: `ALTER TABLE application ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT TRUE` (+ sync ddl_v1.0.sql). Mantener el modelo de una sola key por aplicación (columna existente). Si el usuario elige multi-key, se migra a E2.
2. **Emisión**: `POST /applications/{id}/api-key` (solo Admin) → genera key con `generate_api_key()`, persiste `hash_api_key(key)` (SHA-256), devuelve la key en claro **una única vez** (SEC: nunca recuperable después). 404 si la app no existe; 409 si ya tiene key activa (o 200 con regeneración — decisión del usuario).
3. **Activación/inactivación**: `is_active` en `ApplicationUpdate`/`ApplicationRead` (o endpoint dedicado — decisión del usuario); la inactivación invalida la key en ingesta (403 `app_inactive`).
4. **Guard de ingesta**: `require_api_key` en `dependencies.py` — X-API-Key ausente/malformada/sin match → 401; app inactiva → 403; OK → inyecta `Application` en el handler. **Binding 1:1 key→app = aislamiento entre aplicaciones** (decisión S2-01: app_id del payload nunca se confía).
5. **Contrato**: aplicar `apiKey` a `/telemetry/metrics` y `/telemetry/exceptions` en openapi.yaml (son los paths que #37 implementará; #37 depende de #36). Retirar `api_token_hash` de `ApplicationRead` (ADR-16) — breaking change del contrato a confirmar.

**Tests requeridos (strict TDD, pytest + Postgres real; sin implementar en esta fase):**

- **Unit**: servicio de emisión (key generada una vez, hash persistido, key no re-expuesta); validación de credencial (match/non-match); activación/inactivación de app.
- **Integration** (httpx AsyncClient): `POST /applications/{id}/api-key` 201/200 + 404 + roles (Researcher → 403); GET/PUT con `is_active`; guard de ingesta sobre un path protegido: sin header → 401, key inválida → 401, key de app inactiva → 403, key válida → pasa (handler mock/placeholder); aislamiento: key de app A NO autoriza contexto de app B.
- **Contract** (schemathesis): `apiKey` aplicado a los paths de ingesta; `ApplicationRead` sin `api_token_hash`; openapi.yaml válido 3.1.
- **Migración**: upgrade/downgrade de 0003 (columna `is_active` y default TRUE sobre filas existentes); integridad del índice único parcial.

---

## 5. Riesgos

- **R1 — Conflicto de numeración (documentación)**: `docs/business/issues-s1-s2.md` usa "ISS-S2-02" para Autenticación (hoy ISS-S2-01/#35) y "ISS-S2-03" para CRUD de applications (hoy ISS-S2-01). Es un doc desactualizado; la fuente vigente es `issues-s2-s3.md` + issue #36. Riesgo de confusión en README/docs; no bloquea, pero conviene corregir/archivar el doc viejo (fuera de alcance de este cambio; se reporta como observación).
- **R2 — Scope creep hacia #37**: "Autorización de ingesta" roza los endpoints `/telemetry/*` que son del issue #37. Sin la decisión D1, apply podría implementar endpoints de ingesta duplicando #37. El guard debe ser reutilizable, no acoplado a handlers inexistentes.
- **R3 — Breaking change de contrato**: retirar `api_token_hash` de `ApplicationRead` (ADR-16) y aplicar `apiKey` a paths aún no implementados altera `openapi.yaml`; schemathesis y tests de contrato actuales deben actualizarse en el mismo cambio (no romper la suite).
- **R4 — Numeración de migración**: `0003` ya está reservado por ADR-07/proposal S2-01 para `is_active`; cualquier otra migración nueva en paralelo (p.ej. multi-key) debe coordinarse con 0003.
- **R5 — Semántica de rotación**: con una sola columna, regenerar key rompe clientes conectados al instante (sin ventana de overlap). Si el producto lo exige, empuja hacia E2 (tabla de credenciales).
- **R6 — Secretos**: la key en claro se devuelve UNA vez; pruebas y fixtures no deben loguearla ni persistirla. El hash SHA-256 de key aleatoria de 32 bytes es suficiente (ADR-03), no aplicar KDF en el hot path de ingesta.
- **R7 — Sin endpoints de ingesta para demostrar el guard**: el guard se prueba contra paths del contrato o un path de prueba; la verificación end-to-end real llega con #37. Criterio de aceptación "autorización de ingesta" debe leerse como "mecanismo de autorización listo y probado a nivel de dependency/contrato".

---

## 6. Supuestos

- El criterio 1 (creación de aplicaciones) se considera satisfecho por ISS-S2-01; este cambio no reimplementa CRUD.
- `application_id` en payloads de ingesta nunca se confía como autoridad de tenant: la credencial es la autoridad (decisión S2-01, proposal §enfoque).
- La key se valida con SHA-256 hex (ADR-03) y el prefijo `ilp_` (config `api_key_prefix`).
- La migración 0003 es aditiva y con `DEFAULT TRUE` para no romper filas existentes (mismo criterio ADR-06 de `password_hash`).

---

## 7. Preguntas abiertas (requieren decisión del usuario ANTES de proponer)

- **D1 — Alcance de "autorización de ingesta" en #36**: ¿construir el guard `require_api_key` reutilizable y aplicarlo a `/telemetry/*` solo a nivel de contrato OpenAPI (handlers en #37), o exige el usuario demostración end-to-end (lo que implicaría tocar endpoints de #37 — NO recomendado)?
- **D2 — Modelo de credenciales**: ¿una única key activa por aplicación (columna `api_token_hash` existente, E1) o tabla de credenciales multi-key con rotación/revocación (E2)? Afecta migración 0003, API y aislamiento.
- **D3 — Semántica de activación/inactivación**: ¿campo `is_active` en `ApplicationUpdate`/`ApplicationRead` o endpoint dedicado (PATCH)? ¿Inactivar una app debe invalidar su key en ingesta (403 `app_inactive`)?
- **D4 — Rotación**: al regenerar key (`POST /applications/{id}/api-key` sobre una app con key activa), ¿409 (exigir revocación explícita) o 200 reemplazando la key al instante (downtime de clientes)? ¿Se necesita ventana de overlap (empuja a E2)?
- **D5 — Alcance de aislamiento en #36**: ¿basta con el binding 1:1 credencial→aplicación (la key identifica UNA app; el payload nunca se confía), dejando el aislamiento de datos de consulta/persistencia a #37/#40?
- **D6 — ADR-16 (breaking contract)**: confirmar que retirar `api_token_hash` de `ApplicationRead` y del openapi.yaml en este cambio es aceptable, actualizando schemathesis y tests en el mismo PR.

## Ready for Proposal

**Sí** — con confirmación previa de D1..D6. La exploración deja identificado: criterios cubiertos vs faltantes, infra dormida a activar, enfoque recomendado (E1), tests requeridos (unit/integration/contract/migración) y riesgos. El orquestador debe llevar D1..D6 al usuario antes de lanzar sdd-propose.