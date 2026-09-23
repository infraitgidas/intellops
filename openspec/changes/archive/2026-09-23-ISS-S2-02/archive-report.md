# ARCHIVE REPORT — ISS-S2-02: Aplicaciones y credenciales de ingesta

**Cambio**: ISS-S2-02 (GitHub #36). **Store**: openspec (file-based). **Fecha de archive**: 2026-09-23.
**Estado al cierre**: verificado PASS — suite 142 passed + 1 xpassed (exit 0), cobertura 92.63% (gate ≥70), flake8 limpio, pylint 9.85/10, requirements 26/26, scenarios 18/18, blockers 0, critical 0, warning 0, 3 SUGGESTIONs.

## Final-State Authority

Este reporte describe el estado del cambio AL CIERRE, no en snapshots intermedios. Jerarquía aplicada:

1. **`tasks.md` persistido** (fuente de verdad de completitud): 23/23 tareas `[x]`, 0 `- [ ]`. Gate de completitud superado.
2. **Hechos finales de estado del lanzamiento (orchestrator)** — tienen precedencia sobre `verify-report`/`apply-progress`.
3. **`verify-report` y `apply-progress`** — snapshots intermedios: historia válida de su momento, nunca evidencia de estado final.

### Hechos finales del ciclo

- **Verdict final `verify-report`**: PASS — 26/26 requisitos, 18/18 escenarios, 142 passed + 1 xpassed, cobertura 92.63%, 0 blockers, 0 critical, 0 warning. Reporte admitido por `gentle-ai sdd-verify-validate`.
- **`apply-progress` corregido**: tras la primera escritura, el orquestador lo corrigió para declarar `Next recommended: sdd-verify`. Los números válidos son: comando de test focalizado **88 passed + 1 xpassed (89 colectados)**; suite completa **142 passed + 1 xpassed** con `PYTHONPATH=.`. La cifra "129 passed" que apareció en el borrador inicial es stale y **NO** debe usarse (el propio `apply-progress` la identifica como agregado no reproducible).
- **Ledger de runtime**: la work unit de apply excedió su presupuesto de líneas cambiadas (1730 > 1400). El maintainer autorizó explícitamente un reset objetivo (`size:exception`, PR único); el ledger quedó `complete` con outcome `passed`. Es un resultado esperado, no un defecto.
- **Entrega (delivery)**: el cambio **NO está commiteado** al cierre de este archive (design.md, tasks.md, apply-progress.md, verify-report.md y los archivos nuevos de código/test están untracked; el archive movió los 5 artefactos que estaban trackeados vía `git mv`). La entrega (commit/PR/push) es una decisión humana separada y **NO** forma parte de este paso de archive. No se commiteó, pusheó ni abrió PR.

## Sync de deltas a specs vigentes

El cambio es un delta monolítico y plano (`spec.md` con 5 secciones: app-credentials, ingest-auth, applications-api, openapi, requisitos de datos y seguridad transversales). Los specs vigentes del store que el delta modifica son `openspec/specs/openapi.yaml` (contrato) y `openspec/specs/database/ddl_v1.0.sql` (esquema). Ambos **ya fueron sincronizados durante la implementación** (verificado en este archive, sin edición adicional):

| Spec vigente | Delta aplicado | Evidencia verificada en archive |
|--------------|----------------|---------------------------------|
| `openspec/specs/openapi.yaml` | **OAS-6..10**: paths POST/DELETE `/applications/{application_id}/api-key` (bearerAuth solo Admin; statuses 201/204/401/403/404/409/422); schema `ApiKeyResponse` (`api_key`, `hint`; show-once); `ApplicationRead` **sin** `api_token_hash` en `required` y en `properties` (ADR-16); securityScheme `apiKey` (header `X-API-Key`) declarado **sin** `security: [apiKey]` en ningún path existente (wiring a `/telemetry/*` diferido a #37); paths preexistentes intactos (backward compatibility). | `openapi.yaml:680` (path api-key), `:700` (`$ref ApiKeyResponse`), `:1087` (schema `ApiKeyResponse`), `:1068` (`required: [app_id, name, description, is_active, created_at]` — sin hash), `:1159` (scheme `apiKey`), `:517` (descripción). 0 ocurrencias de `api_token_hash` en `properties`; los 12 bloques `security:` existentes son todos `bearerAuth: []`, ninguno `apiKey`. |
| `openspec/specs/database/ddl_v1.0.sql` | **DATA-9**: columna `application.is_active BOOLEAN NOT NULL DEFAULT TRUE` con comentario de trazabilidad a la migración 0003 (ISS-S2-02, ADR-20); 0001/0002 intactos. | `ddl_v1.0.sql:59-61` (`-- is_active agregado por la migración 0003 (ISS-S2-02, ADR-20)` + `is_active BOOLEAN NOT NULL DEFAULT TRUE`). |

**Capabilities nuevas (`app-credentials`, `ingest-auth`)**: el store del repo no mantiene specs de dominio por capability (`openspec/specs/` solo contiene `architecture/`, `database/`, `research/` y los contratos `openapi.yaml`/`asyncapi.yaml`). No se crearon specs de dominio nuevos — la representación persistente de estas capabilities en specs vigentes es el contrato OpenAPI (`/applications/{id}/api-key` + `ApiKeyResponse` + scheme `apiKey`) y el DDL sincronizado. Los requisitos funcionales detallados (CRED-1..5, IAUTH-1..5, APP-7..9, OAS-6..10, DATA-6..9, SEC-7..10) persisten íntegros en `spec.md`, archivado con el cambio (audit trail completo). Crear `openspec/specs/{capability}/spec.md` habría inventado una estructura sin precedente en el repo (misma convención que el archive de ISS-S2-01).

## Reglas rules.archive (config.yaml)

- **Deltas destructivos**: ninguno — el sync fue 100% aditivo (2 paths nuevos, 1 schema nuevo, retiro de un campo de un schema de salida declarado como breaking controlado por ADR-16, 1 columna con DEFAULT). Sin advertencia de merge destructivo.
- **CITATION.cff / experimentos ML**: el archivo `CITATION.cff` no existe en el repo; este cambio no toca componentes ML (SEC-10: sin servicios nuevos, CPU-only <2GB RAM). Sin actualización requerida.
- **ADR registrado**: ADR-17..24 documentados en `design.md` (tabla de decisiones) y verificados en `verify-report.md` (coherence ADR-17..24 ✅). La convención del repo registra las decisiones de cada cambio en el design del cambio; no se crearon archivos ADR individuales (sin precedente).

## Verificación del archive (Mechanical Copy Contract)

- Move: `git mv openspec/changes/ISS-S2-02 openspec/changes/archive/2026-09-23-ISS-S2-02` — snapshot recursivo pre-move + `diff -r` post-move: **vacío (byte-identical)**. Ningún byte pasó por el modelo.
- El folder archivado contiene: `exploration.md`, `preproposal.md`, `proposal.md`, `research.md`, `spec.md`, `design.md`, `tasks.md`, `apply-progress.md`, `verify-report.md` (9/9) + `.gentle-ai-instance` + este `archive-report.md` (aditivo, excluido del diff).
- `openspec/changes/` ya no contiene el cambio activo (solo `archive/`).
- `tasks.md` archivado: 23/23 tareas `[x]`, sin tareas pendientes.
- `git status`: los 5 artefactos previamente trackeados figuran como `R` (rename) hacia el archive; los untracked viajaron con el move del directorio.

### Salida verbatim del `diff -r` (snapshot vs destination)

```
=== MANDATORY diff -r readback (snapshot vs destination) ===
=== diff_status=0 ===
```

Sin diferencias (vacío) — única evidencia de aprobación.

## Artefactos leídos (trazabilidad)

- `openspec/changes/ISS-S2-02/{proposal.md, spec.md, design.md, tasks.md, verify-report.md, apply-progress.md}` (leídos antes del move).
- `openspec/specs/openapi.yaml`, `openspec/specs/database/ddl_v1.0.sql` (estado vigente, verificación del sync).
- `openspec/config.yaml` (rules.archive), `openspec/changes/archive/2026-09-13-ISS-S2-01/archive-report.md` (convención de formato).

## Hallazgos y riesgos residuales (no bloqueantes)

1. **SUG-1 (verify-report) — SEC-10 sin benchmark de latencia**: el objetivo de ~1μs de validación se sustenta en evidencia estática (lookup indexado por hash + SHA-256, sin servicios nuevos), sin test/benchmark dedicado. El requisito es operativo y el diseño lo cumple por construcción.
2. **SUG-2 (verify-report) — Premisa experimental de OAS-9 superada (ADR-24)**: la spec asumía soporte experimental de OpenAPI 3.1 en schemathesis; la versión 4.x lo trae nativo y `OPEN_API_3_1.enable()` queda como rama legacy documentada. El gate contract queda verde (1 xpassed).
3. **SUG-3 (verify-report) — Drift del `/openapi.json` servido (preexistente)**: FastAPI genera el spec servido desde los routers (sin `responses=` declarados), por lo que no documenta 401/403/404/409 de los paths api-key; el canónico `openspec/specs/openapi.yaml` sí. Mismo hallazgo WARNING-1 de ISS-S2-01; no afecta comportamiento ni archive.
4. **Ledger de runtime**: work unit de apply excedió el presupuesto (1730 > 1400); reset objetivo autorizado por el maintainer (`size:exception`, PR único), ledger `complete`/`passed`.
5. **Delivery pendiente**: el cambio no está commiteado/pusheado al cierre del archive — decisión humana separada, fuera del alcance de este paso.

## Verdict

**ARCHIVED** — El cambio ISS-S2-02 cerró el ciclo SDD completo: explorado, propuesto, especificado, diseñado, implementado (23/23 tareas, strict TDD), verificado (PASS, 26/26 requisitos, 18/18 escenarios, 142 passed + 1 xpassed, cobertura 92.63%, 0 critical/0 warning) y archivado con sync de deltas confirmado sobre los specs vigentes. Entrega (commit/PR) pendiente de decisión humana.
