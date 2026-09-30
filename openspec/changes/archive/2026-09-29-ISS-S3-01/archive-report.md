# ARCHIVE REPORT — ISS-S3-01: Persistencia de telemetría (verificación + hardening + read path)

**Cambio**: ISS-S3-01 (GitHub #40). **Store**: openspec (file-based) + Engram (hybrid). **Fecha de archive**: 2026-09-29.
**Estado al cierre**: verificado PASS — suite 226 passed + 1 xpassed (exit 0), cobertura 93.91% (gate ≥70), `docker compose build intellops-core` exit 0, flake8 src/ tests/ limpio, pylint 9.72/10 ≥ 7.0, requisitos 7/7, escenarios 12/12 (Postgres real), schemathesis scoped 10 casos validados, blockers 0, critical 0, warning 1 (W-1 residual, fuera de scope, no bloquea), 3 SUGGESTIONs.

## Final-State Authority

Este reporte describe el estado del cambio AL CIERRE, no en snapshots intermedios. Jerarquía aplicada:

1. **`tasks.md` persistido** (fuente de verdad de completitud): 14/14 tareas `[x]`, 0 `- [ ]`. Gate de completitud superado.
2. **Hechos finales de estado del lanzamiento (orchestrator)** — tienen precedencia sobre `verify-report`/`apply-progress`.
3. **`verify-report` y `apply-progress`** — snapshots intermedios: historia válida de su momento, nunca evidencia de estado final.

### Hechos finales del ciclo

- **Verdict final `verify-report`** (obs Engram #224): PASS — 7/7 requisitos (RUM-9/10/11, TQ-1/2, OAS-13/14), 12/12 escenarios con test pasando en ejecución independiente (Postgres real + httpx ASGI + schemathesis 4.28), 226 passed + 1 xpassed (exit 0), cobertura 93.91% ≥ 70, flake8 src/ tests/ limpio, pylint 9.72/10 ≥ 7.0, build `docker compose build intellops-core` exit 0, schemathesis scoped a metrics (10 casos) exit 0, `evidence_revision` sha256:1c8ce65…098b9, `test_output_hash` sha256:7376e95…2d88, `build_output_hash` sha256:e1a01d1…8e51. **CRITICAL: 0. Bloqueantes: 0.**
- **Reconciliación de conteo de tareas (13/13 vs 14/14)**: `apply-progress.md` (snapshot 17:47) declara "13/13 tareas completas", pero su propia tabla TDD lista 14 filas (1.1–5.1). La fuente de verdad persistida (`tasks.md`) tiene **14 checkboxes, 14 `[x]`**, y `verify-report` §Completeness confirma "Tasks total 14, complete 14" con verificación explícita de los 14 checkboxes. El estado final reconciliado del lanzamiento es **14/14**. El "13/13" de `apply-progress` es una claim stale del snapshot, sin evidencia de tarea incompleta; se registra como discrepancia reconciliada por la jerarquía (tasks.md > lanzamiento > snapshots).
- **W-1 residual (no bloqueante, fuera de scope)**: colisión same-chunk de primera vez (dos tenants envían el mismo `session_id` NUEVO en el mismo chunk; el SELECT pre-insert no lo detecta y `ON CONFLICT DO NOTHING` conserva una fila). Documentado en ADR-0003 (Negativas) y en `apply-progress` §Issues. La spec C5 cubre sesión YA persistida (cumplida); la mitigación futura (índice único `(session_id, app_id)` o dedup intra-chunk) requiere DDL y queda para un cambio futuro. **NO es bloqueante al archive** (el lanzamiento lo instruyó explícitamente).
- **Ledger de runtime settleado**: objetivo de apply completo (14/14, suite 226 passed, cobertura 93.91%, flake8 limpio, pylint 9.72); objetivo de verify completo (PASS, 7/7, 12/12, build exit 0).
- **SUG-1..3 de `verify-report` NO corregidos** (no bloqueantes, aceptados al cierre): (SUG-1) rama de filtro `metric_type` en `sqlalchemy_query_repository.py` L79 sin test end-to-end (96%, ≥80% Acceptable); (SUG-2) pylint R0801 duplicate-code entre `query_repository.py:25-32` y `schemas/metrics.py:16-23` (DTOs del mismo shape por diseño, informativo); (SUG-3) `QueryService._as_utc` L71 sin cubrir (97%, rama defensiva).
- **Desviaciones de diseño (4, ninguna rompe spec)**: (1) router sin `ge=60` en `bucket_seconds` — la validación vive en `QueryService` para emitir 422 `invalid_query_range` con el envelope ErrorResponse (el `ge=60` de Pydantic rompería el contrato de error OAS-13); (2) `func.avg(...).cast(Float)` (tipo SQL, no builtin) por cache key de SQLAlchemy; (3) correlación scoped por sesión→tenant del lote (no JOIN global por `app_id`) para chunks multi-tenant; (4) `/metrics/list` declara 422 por completitud del contrato OAS-13.
- **Implementación SIN commitear** en el working tree (git status: 9 `M` + untracked nuevos): la entrega (push/PR) es una decisión humana separada — sin push, sin PR en este paso.
- **ADR-0003 + CHANGELOG actualizados**: `docs/adr/0003-ownership-tenant-read-path.md` (Nygard, DD-8/DD-9/DD-10, aceptado) y `CHANGELOG.md` (sección Unreleased, entrada ISS-S3-01).

## Sync de deltas a specs vigentes

El cambio es un delta monolítico y plano (`spec.md` con 3 secciones: rum-ingest RUM-9/10/11 + telemetry-query TQ-1/2 + openapi OAS-13/14), **puramente ADDED** (2 bloques `## ADDED Requirements`, 0 MODIFIED/REMOVED/RENAMED). Los specs vigentes del store que el delta toca son `openspec/specs/openapi.yaml` (contrato, OAS-13/14) y, como representación persistente de las capabilities `rum-ingest`/`telemetry-query`, el propio contrato + specs de arquitectura. **El sync se aplicó durante apply (task 3.2, working tree sin commitear) y este archive lo verificó contra los specs vigentes sin edición adicional** — misma convención que los archives de ISS-S2-01/02/03:

| Spec vigente | Delta aplicado | Evidencia verificada en archive |
|--------------|----------------|---------------------------------|
| `openspec/specs/openapi.yaml` | **OAS-13/14**: paths `GET /metrics/query` (operationId `queryMetrics`) y `GET /metrics/list` (`listMetrics`) completados (diff del working tree): `security: [apiKey]`, parámetros `start`/`end`/`bucket_seconds`/`metric_type` (query, opcional el último), respuestas 200 (shape ML `MetricAggregate` / catálogo `MetricTypeInfo`) + 401/403/422 (ErrorResponse); schemas nuevos `MetricAggregate` (required 5 campos) y `MetricTypeInfo` en components. **operationIds y paths INTACTOS** (líneas de contexto en el diff, no modificadas); el contrato de ingesta `/telemetry/*` (OAS-6/11/12) sin cambios (0 líneas +/- de telemetry/operationId en el diff). | `git diff openspec/specs/openapi.yaml`: bloque 125-223 (+80 líneas aditivas), bloques 1051+ (schemas `MetricAggregate`/`MetricTypeInfo`); `rg "queryMetrics|listMetrics"` → L127, L189 intactos. |
| `openspec/specs/architecture/components.md` | **TQ-1/2 (read path)**: el árbol de routers ya referencia `metrics.py ← GET /metrics/query, GET /metrics/list` (L17, agregado en commit `4402e87`/S2-03 como planificado; consistente con la implementación real en `src/api/presentation/routers/metrics.py`). | `components.md:17`. |
| `openspec/specs/architecture/interfaces.md` | **TQ-1/2/OAS-13**: filas `GET /metrics/query` (Consulta de métricas históricas) y `GET /metrics/list` (Listado de métricas disponibles) ya declaradas (L25-26, contrato planeado pre-S3-01; ahora implementadas). | `interfaces.md:25-26`. |
| `openspec/specs/database/ddl_v1.0.sql` | Sin cambios — el fix de ownership y el read path son lógica de upsert/repo + SELECT, sin DDL nuevo (verificado: sin diff). | `git status` sin `M` en database/. |

**Capability `telemetry-query` (nueva) y `rum-ingest` (modificada)**: el store del repo no mantiene specs de dominio por capability (`openspec/specs/` solo contiene `architecture/`, `database/`, `research/` y los contratos `openapi.yaml`/`asyncapi.yaml`). No se creó spec de dominio nuevo — la representación persistente de ambas capabilities en specs vigentes es el contrato OpenAPI (`/metrics/query` + `/metrics/list` con `security: apiKey` y shape ML; ingesta `/telemetry/*` intacta) y los requisitos funcionales detallados (RUM-9/10/11, TQ-1/2, OAS-13/14) persisten íntegros en `spec.md`, archivado con el cambio (audit trail completo). Misma convención que los archives de ISS-S2-01/02/03.

## Verificación de deltas destructivos (rules.archive)

- **Deltas destructivos: NINGUNO.** El delta es ADDED-only (2 bloques ADDED, sin MODIFIED/REMOVED/RENAMED). El diff de openapi.yaml es puramente aditivo (+80 líneas en los 2 paths declarados, +schemas nuevos): **ningún operationId ni path existente fue cambiado o eliminado** (`queryMetrics`/`listMetrics` en contexto; `/telemetry/metrics` y `/telemetry/exceptions` sin líneas +/-). Los endpoints GET eran stubs declarados sin implementación previa (openapi 124-137, "Planificado"): S3-01 los completa (security, parámetros, respuestas) — aditivo, sin consumidores previos, backward compatible. **Sin advertencia de merge destructivo pendiente.**
- **CITATION.cff / experimentos ML**: el archivo `CITATION.cff` no existe en el repo (verificado); este cambio no toca componentes ML (sin rewiring — scope de ISS-S3-04/#43; sin dependencias nuevas, CPU-only, <2GB RAM, $0/mo). Sin actualización requerida.
- **ADR registrado**: ADR-0003 (`docs/adr/0003-ownership-tenant-read-path.md`, formato Nygard: contexto C2-C4, decisión DD-8/DD-9/DD-10, consecuencias positivas/negativas, alternativas) creado en task 5.1 y verificado en `verify-report` §Coherence (DD-8/9/10 ✅). CHANGELOG.md registra el cambio (sección Unreleased, entrada ISS-S3-01). Decisiones DD-8..DD-10 documentadas en `design.md` y confirmadas en `verify-report`.

## Decisiones de arquitectura (DD-8..DD-10, ADR-0003)

| # | Decisión | Estado |
|---|----------|--------|
| DD-8 | Ownership resuelto en `_upsert_sessions` (SELECT por PK pre-insert, extranjeras → descarte + `session_foreign_total`); sin TOCTOU (mismo AsyncSession del chunk); sin DDL | ✅ |
| DD-9 | Agregación del read path EN SQL (una sentencia GROUP BY metric_type_id + bucket epoch anclado a `:start`, AVG + COUNT(DISTINCT session_id)); sin materializar filas; plan indexado existente | ✅ |
| DD-10 | Contadores de descartes por el mecanismo `snapshot()` existente (keys `ingest.session_foreign_total`/`ingest.metric_id_foreign_total`, naming `ingest.` + `_total`); `PersistStats` con defaults 0 | ✅ |

## Verificación del archive (Mechanical Copy Contract)

- Move: `git mv openspec/changes/2026-09-29-ISS-S3-01 openspec/changes/archive/2026-09-29-ISS-S3-01` falló con `fatal: source directory is empty` (el folder completo es untracked en el working tree — `??` en git status; git mv no tiene archivos trackeados que mover). Fallback del contrato aplicado: `diff -r` snapshot pre-move vs source (vacío) → `mv` plano → **`diff -r` post-move snapshot vs destination: vacío (byte-identical)**. Ningún byte pasó por el modelo.
- El folder archivado contiene: `proposal.md`, `spec.md`, `design.md`, `tasks.md`, `apply-progress.md`, `verify-report.md`, `.gentle-ai-instance` (7/7) + este `archive-report.md` (aditivo, excluido del diff).
- `openspec/changes/` ya no contiene el cambio activo (solo `archive/`).
- `tasks.md` archivado: **14/14 tareas `[x]`, sin tareas pendientes** (verificado: 14 checkboxes, 0 `- [ ]`).
- `git status` tras el move: el folder viajó íntegro al archive (untracked); los archivos modificados del cambio (openapi.yaml, src/*, tests/*, CHANGELOG.md) permanecen en el working tree sin commitear, listos para la decisión humana de entrega.

### Salida verbatim del `diff -r` (snapshot vs destination)

```
=== MANDATORY diff -r readback (snapshot vs destination) ===
=== diff_status=0 ===
```

Sin diferencias (vacío) — única evidencia de aprobación.

## Artefactos leídos (trazabilidad)

- `openspec/changes/2026-09-29-ISS-S3-01/{proposal.md, spec.md, design.md, tasks.md, apply-progress.md, verify-report.md}` (leídos antes del move).
- Engram (hybrid): obs #215 `sdd/2026-09-29-ISS-S3-01/explore`, #216 `research`, #217 `proposal`, #218 `spec`, #219 `design`, #220 `tasks`, #222 `apply-progress`, #224 `verify-report` (proyecto `intellops`, scope project).
- `openspec/specs/openapi.yaml` (diff del working tree), `openspec/specs/architecture/{components,interfaces,quality-attributes}.md`, `openspec/specs/asyncapi.yaml`, `openspec/specs/database/ddl_v1.0.sql` (sin diff).
- `docs/adr/0003-ownership-tenant-read-path.md`, `CHANGELOG.md`, `openspec/config.yaml` (rules.archive), `openspec/changes/archive/2026-09-25-ISS-S2-03/archive-report.md` (convención de formato).

## Hallazgos y riesgos residuales (no bloqueantes)

1. **W-1 (verify-report) — Colisión same-chunk de primera vez (residual, fuera de scope)**: dos tenants enviando el MISMO `session_id` NUEVO en el mismo chunk no se detecta en el SELECT pre-insert (ninguno existe aún); `ON CONFLICT DO NOTHING` conserva una de las filas y las métricas del otro tenant quedan bajo esa sesión. Documentado en ADR-0003 (Negativas) y apply-progress. La spec C5 cubre sesión YA persistida (cumplida); la mitigación futura (índice único `(session_id, app_id)` o dedup intra-chunk) requiere DDL y queda fuera de scope. No bloquea delivery ni archive.
2. **SUG-1 (verify-report) — Rama de filtro `metric_type` sin test end-to-end**: `sqlalchemy_query_repository.py` L79 (96%); el parámetro está declarado en el contrato y delegado, pero ningún test HTTP ejerce el filtro. Coverage ≥ 80% (Acceptable); sin impacto de comportamiento.
3. **SUG-2 (verify-report) — Pylint R0801 duplicate-code**: `query_repository.py:25-32` y `schemas/metrics.py:16-23` comparten el shape de 5 campos (DTOs planos por diseño, capas distintas); informativo, sin acción requerida.
4. **SUG-3 (verify-report) — `QueryService._as_utc` L71 sin cubrir (97%)**: rama defensiva de datetime naive; sin impacto funcional.
5. **Follow-up documentado — asyncapi.yaml stale**: `metrics/batch`/`MetricBatchEvent` (asyncapi.yaml L21-27, L86-87) siguen declarados como "Extensión futura" (interfaces.md §1.2); el rework del contrato AsyncAPI quedó fuera de scope del proposal (MAY note, "Out of Scope: rework AsyncAPI") — cambio futuro.
6. **Follow-up de cadena — Rewiring del worker ML**: ISS-S3-04 (#43) consume `/metrics/query` como dataset operativo (`MetricBatchInput`); fuera de scope de ISS-S3-01 (solo se dejó el read path listo).
7. **Drift pre-existente (no del delta)**: `components.md` §1.1 muestra el árbol de routers bajo `src/api/routers/` mientras la implementación real vive en `src/api/presentation/routers/` (drift heredado de la era S2-03, afecta por igual a `telemetry.py` y `metrics.py`). Fuera del alcance del delta; sin impacto funcional.
8. **Delivery pendiente**: el cambio NO está pusheado ni tiene PR al cierre de este archive (working tree sin commitear) — el orquestador pedirá aprobación del usuario antes de crear el PR. Sin push, sin PR en este paso.

## Verdict

**ARCHIVED** — El cambio ISS-S3-01 cerró el ciclo SDD completo: explorado, propuesto, especificado, diseñado, implementado (14/14 tareas, strict TDD), verificado (PASS, 7/7 requisitos, 12/12 escenarios con Postgres real, 226 passed + 1 xpassed, cobertura 93.91%, build exit 0, schemathesis 10 casos, 0 critical) y archivado con sync de deltas confirmado sobre los specs vigentes (openapi.yaml: OAS-13/14 aditivo, operationIds y contrato de ingesta intactos — sin deltas destructivos). Ownership de sesión (C5) y correlación `metric_id` scoped verificados; read path app-scoped con shape ML listo para ISS-S3-04; ADR-0003 y CHANGELOG actualizados. Un WARNING residual documentado (colisión same-chunk de primera vez, fuera de scope de la spec) — no bloquea. Entrega (push/PR) pendiente de aprobación del usuario.