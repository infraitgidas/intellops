# ARCHIVE REPORT — ISS-S2-01: Backend Core funcional

**Cambio**: ISS-S2-01 (GitHub #35). **Store**: openspec (file-based). **Fecha de archive**: 2026-09-13.
**Estado al cierre**: verificado PASS — suite 96/96 (90 previos + 6 de `tests/test_container_import_path.py`), cobertura 78.80% (gate ≥70), flake8 limpio, pylint 10.00/10, requirements 35/35, scenarios 24/24, blockers 0, critical 0.

## Final-State Authority

Este reporte describe el estado del cambio AL CIERRE, no en snapshots intermedios:

- **CRITICAL-1 (dualidad de imports `src.api.*` vs `api.*`)** — **RESUELTO** en commit `b4488fb` (main.py con imports absolutos `api.*`, Dockerfile CMD `uvicorn api.main:app`, test `tests/test_container_import_path.py` agregado). El verify-report final (`e9b14e2`, re-ejecutado contra HEAD) confirma 401/403/404/409 correctos con ErrorResponse en probes en vivo del runtime real del contenedor (antes degradaban a 500). Ver `verify-report.md` archivado, sección CRITICAL-1.
- **Tasks**: 23/23 completas (`tasks.md` archivado, 23 checkboxes `[x]`). Gate de completitud de tareas superado.
- **Spec**: reformateado a formato canónico `### Requirement:` (commit `4fb78c3`), validado por dispatcher (`gentle-ai sdd-verify-validate`: valid true, verdict pass).

## Sync de deltas a specs vigentes

El cambio es un delta monolítico (`spec.md` con 4 capabilities: user-auth, users-api, applications-api nuevas; openapi modificada). Los specs vigentes del store que el delta modifica son `openspec/specs/openapi.yaml` (contrato) y `openspec/specs/database/ddl_v1.0.sql` (esquema). Ambos **ya fueron sincronizados durante la implementación** (verificado en este archive, sin edición adicional):

| Spec vigente | Delta aplicado | Evidencia |
|--------------|----------------|-----------|
| `openspec/specs/openapi.yaml` | OAS-1..5: 6 paths / 11 operaciones (POST /auth/login, POST /auth/logout, GET/POST /users, GET/PUT /users/{user_id}, GET/POST /applications, GET/PUT/DELETE /applications/{application_id}); securityScheme `bearerAuth` aplicado a users/applications/logout (login público); `apiKey` declarado sin aplicar (OAS-3); paths preexistentes intactos (OAS-4); schemas `LoginRequest`, `AuthResponse`, `UserCreate`, `UserUpdate`, `UserRead`, `ApplicationCreate`, `ApplicationUpdate`, `ApplicationRead` + `ErrorResponse` reutilizado en 401/403/404/409 (OAS-5). | Commit `c25ef99` (PR-D D4, +554 líneas). Verificado en archive: `security: [bearerAuth]` presente en logout/users/applications; apiKey solo declarado; 37 referencias a ErrorResponse; /auth/login público. |
| `openspec/specs/database/ddl_v1.0.sql` | DATA-1..5: `lab_user.password_hash VARCHAR(255)` nullable, `CREATE UNIQUE INDEX idx_lab_user_email`, `application.api_token_hash VARCHAR(64)` + índice único parcial `idx_application_api_token_hash WHERE api_token_hash IS NOT NULL`, seed Admin (UUID fijo, email admin@intellops.local, rol Admin, is_active, password_hash argon2 dev/CI). | Tarea A9 (`0002_credentials.py` + sync ddl). Verificado en archive: columnas, índices y seed presentes; comentarios de trazabilidad a 0002/ADR. |

**Capabilities nuevas (user-auth, users-api, applications-api)**: el store del repo no mantiene specs de dominio por capability (`openspec/specs/` solo contiene `architecture/`, `database/`, `research/` y los contratos `openapi.yaml`/`asyncapi.yaml`). No se crearon specs de dominio nuevos — la representación persistente de estas capabilities en specs vigentes es el contrato OpenAPI (`/auth/*`, `/users*`, `/applications*` + schemas) y el DDL sincronizado. Los requisitos funcionales detallados (AUTH-1..6, USR-1..7, APP-1..6, SEC-1..6) persisten íntegros en `spec.md`, archivado con el cambio (audit trail completo). Crear `openspec/specs/{capability}/spec.md` habría inventado una estructura sin precedente en el repo.

## Reglas rules.archive (config.yaml)

- **Deltas destructivos**: ninguno — el sync fue 100% aditivo (paths, schemas, columnas, índices, seed). Sin advertencia de merge destructivo.
- **CITATION.cff / experimentos ML**: el archivo `CITATION.cff` no existe en el repo; este cambio no toca componentes ML (SEC-6: N/A, sin servicios nuevos, CPU-only <2GB RAM). Sin actualización requerida.
- **ADR registrado**: ADR-01..16 documentados en `design.md` (tabla de decisiones, §2) y verificados en `verify-report.md` (coherence ADR-01..16 ✅). La convención del repo (docs/adr/ solo contiene ADR-0001 global + template) registra las decisiones de cada cambio en el design del cambio; no se crearon archivos ADR individuales por decisión (sin precedente).

## Verificación del archive (Mechanical Copy Contract)

- Move: `git mv openspec/changes/ISS-S2-01 openspec/changes/archive/2026-09-13-ISS-S2-01` — snapshot recursivo pre-move + `diff -r` post-move: **vacío (byte-identical)**. Sin paso de bytes por el modelo.
- El folder archivado contiene: `proposal.md`, `spec.md`, `design.md`, `tasks.md`, `verify-report.md` (5/5) + este `archive-report.md` (aditivo, excluido del diff).
- `openspec/changes/` ya no contiene el cambio activo.
- `tasks.md` archivado: 23/23 tareas `[x]`, sin tareas pendientes.

## Artefactos leídos (trazabilidad)

- `openspec/changes/ISS-S2-01/proposal.md`, `spec.md`, `design.md`, `tasks.md`, `verify-report.md` (todos leídos antes del move).
- `openspec/specs/openapi.yaml`, `openspec/specs/database/ddl_v1.0.sql` (estado vigente, verificación del sync).
- `openspec/config.yaml` (rules.archive), `docs/adr/` (convención ADR).

## Hallazgos y riesgos residuales (no bloqueantes)

1. **WARNING-1 (verify-report)**: el `/openapi.json` servido por FastAPI no documenta 401/403/404/409 (los routers no declaran `responses=`); el canónico `openspec/specs/openapi.yaml` sí. Drift de documentación servida, no de comportamiento. Preexistente, no relacionado con CRITICAL-1.
2. **WARNING-2 (verify-report)**: cobertura por archivo de la capa de servicios reportada 47-52% por artefacto de medición de coverage.py 7.16.0 (no registra líneas tras `await`); total 78.80% es límite inferior conservador y pasa el gate.
3. **Registro de ADRs**: decisiones del cambio viven en design.md (convención del repo), no como archivos ADR individuales en docs/adr/.
4. **CITATION.cff**: no existe en el repo; sin impacto para este cambio (no ML).

## Verdict

**ARCHIVED** — El cambio ISS-S2-01 cerró el ciclo SDD completo: planificado, especificado, diseñado, implementado (23/23 tareas), verificado (PASS, 96/96, CRITICAL-1 resuelto) y archivado con sync de deltas confirmado sobre los specs vigentes.