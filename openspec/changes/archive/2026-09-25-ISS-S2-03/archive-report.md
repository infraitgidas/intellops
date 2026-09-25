# ARCHIVE REPORT — ISS-S2-03: Ingesta RUM asíncrona

**Cambio**: ISS-S2-03 (GitHub #37). **Store**: openspec (file-based). **Fecha de archive**: 2026-09-25.
**Estado al cierre**: verificado PASS — suite 209 passed + 1 xpassed (exit 0), cobertura 93.06% (gate ≥70), `docker compose build intellops-core` exit 0, flake8 src/ limpio, pylint 8.93/10 ≥ 7.0, requirements 18/18, scenarios 32/32, blockers 0, critical 0, warning 0, 4 SUGGESTIONs.

## Final-State Authority

Este reporte describe el estado del cambio AL CIERRE, no en snapshots intermedios. Jerarquía aplicada:

1. **`tasks.md` persistido** (fuente de verdad de completitud): 17/17 tareas `[x]`, 0 `- [ ]`. Gate de completitud superado.
2. **Hechos finales de estado del lanzamiento (orchestrator)** — tienen precedencia sobre `verify-report`/`apply-progress`.
3. **`verify-report` y `apply-progress`** — snapshots intermedios: historia válida de su momento, nunca evidencia de estado final.

### Hechos finales del ciclo

- **Verdict final `verify-report`**: PASS — 18/18 requisitos (17 activos RUM-1..8, OAS-6/11/12, IAUTH-2/5, ARCH-1..4 + 1 REMOVED "Paths /metrics/ingest y /logs/ingest" verificado como evidencia de eliminación por `test_oas10_ingest_paths_replaced_by_telemetry` PASSED), 32/32 escenarios, 209 passed + 1 xpassed, cobertura 93.06% ≥ 70, flake8 src/ limpio, pylint 8.93/10 ≥ 7.0. Reporte admitido por `gentle-ai sdd-verify-validate` (valid: true).
- **Suite final**: 209 passed + 1 xpassed, coverage 93.06%, build `docker compose build intellops-core` exit 0, flake8 src/ limpio, pylint 8.93 ≥ 7.0. La cifra "pylint 8.83" de `apply-progress.md` (snapshot de 11:18) es stale frente al `verify-report` posterior (11:28) y a los hechos finales del lanzamiento; el valor vigente es 8.93.
- **SUG-1..4 de `verify-report` NO corregidos** (no bloqueantes, aceptados al cierre): (SUG-1) flake8 no cubre `tests/` (E501/W292 en `test_ingest_telemetry.py`); (SUG-2) handler `ingest_exceptions` sin test HTTP directo con key válida (87%, ≥80% Acceptable); (SUG-3) premisa experimental de OAS-9 superada — schemathesis 4.x trae OpenAPI 3.1 nativo, xpass documentado (ADR-24); (SUG-4) el REMOVED cuenta como 18º heading de requisito, verificado como evidencia de eliminación.
- **Commits de work units en la rama** (6): `47b2e89` (política/entidades/config/contadores), `44fd89b` (schemas/service/queue/repos), `db9906d` (router/guard/errors/main/wiring), `4969a83` (openapi `/telemetry/*` + tests de contrato), `4402e87` (specs de arquitectura + docs vivas + ADR-0002 + CHANGELOG), `c122534` (apply-progress). Rama `feat/ISS-S2-03`, base `origin/develop` con ISS-S2-01 e ISS-S2-02 mergeados.
- **Sync de deltas YA aplicado durante apply** (commits `4969a83` y `4402e87`): este archive lo verificó contra los specs vigentes sin edición adicional.

## Sync de deltas a specs vigentes

El cambio es un delta monolítico y plano (`spec.md` con 4 secciones: rum-ingest nueva + openapi/ingest-auth/architecture modificadas). Los specs vigentes del store que el delta modifica son `openspec/specs/openapi.yaml` (contrato) y `openspec/specs/architecture/{interfaces,components,quality-attributes}.md`, más las docs vivas `docs/architecture/{PipelineIngestaRUM,ContratoIngestaRUM}.md` y `docs/brief-v2.md`. Todos **ya fueron sincronizados durante la implementación** (verificado en este archive, sin edición adicional):

| Spec vigente | Delta aplicado | Evidencia verificada en archive |
|--------------|----------------|---------------------------------|
| `openspec/specs/openapi.yaml` | **OAS-6/11/12 + REMOVED**: paths `POST /telemetry/metrics` (L24) y `POST /telemetry/exceptions` (L74) con `security: [apiKey]` (L30, L80), requestBody (`RumEventBatch`/`JsExceptionBatch`) y respuestas 202/400/401/403/503/429 (429 declarado sin impl, D3); paths `/metrics/ingest` y `/logs/ingest` eliminados (0 ocurrencias, `rg` exit 1); `application_id` fuera de `required` en `RumEvent` (required L810: `[schema_version, timestamp, session_id, metrics]`) y `JsExceptionEvent` (required L903: `[error_type, message, session_id, timestamp]`) con descripciones D2 (L827, L924); códigos de `rejected[].reason` (L957) sin `unknown_application` (0 ocurrencias); scheme `apiKey` (L1187-1191) con descripción actualizada documentando su aplicabilidad a `/telemetry/*` (OAS-6, ISS-S2-03). | `openapi.yaml:24,30,74,80` (paths + security), `:810,:903` (required sin application_id), `:827,:924` (descripción D2), `:957` (enum de rechazo), `:1187-1191` (scheme apiKey). 0 ocurrencias de `/metrics/ingest`, `/logs/ingest` y `unknown_application`. |
| `openspec/specs/architecture/interfaces.md` | **ARCH-1**: nomenclatura revertida a `/telemetry/*` — `POST /telemetry/metrics` y `POST /telemetry/exceptions` en tabla §1.1 (L23-24), snippets (L43, L69) y texto de reversión de la decisión S1 (L13-14); sin `/metrics/ingest` ni `/logs/ingest`. | `interfaces.md:13-14,23-24,43,69`. |
| `openspec/specs/architecture/components.md` | **ARCH-2**: árbol de routers con `telemetry.py ← POST /telemetry/metrics, POST /telemetry/exceptions` (antes `routers/ingest.py`) (L16) y diagrama mermaid con `POST /telemetry/metrics` (L142). | `components.md:16,142`. |
| `openspec/specs/architecture/quality-attributes.md` | **ARCH-3**: artefacto de calidad de ingesta renombrado a `Endpoint POST /telemetry/metrics` (L35). | `quality-attributes.md:35`. |
| `docs/architecture/PipelineIngestaRUM.md`, `docs/architecture/ContratoIngestaRUM.md`, `docs/brief-v2.md` | **ARCH-4**: rutas `/telemetry/*` y semántica 202 (encolado) / 503 (backpressure) (Pipeline L22, L79; Contrato L15-16, L80; brief-v2 L301). Históricos `docs/informe-avance-1/` y `docs/business/issues-s1-s2.md` conservan las rutas viejas (registros intactos, verificado con `rg -l`). | `PipelineIngestaRUM.md:22,79` · `ContratoIngestaRUM.md:15-16,80` · `brief-v2.md:301` · históricos: `informe-avance-1/evaluacion-equipo.md`, `business/issues-s1-s2.md`. |

**Capability nueva (`rum-ingest`)**: el store del repo no mantiene specs de dominio por capability (`openspec/specs/` solo contiene `architecture/`, `database/`, `research/` y los contratos `openapi.yaml`/`asyncapi.yaml`). No se creó spec de dominio nuevo — la representación persistente de `rum-ingest` en specs vigentes es el contrato OpenAPI (`/telemetry/*` + `security: apiKey` + semántica 202/400/401/403/503/429) y los requisitos funcionales detallados (RUM-1..8, OAS-6/11/12, IAUTH-2/5, ARCH-1..4) persisten íntegros en `spec.md`, archivado con el cambio (audit trail completo). Misma convención que los archives de ISS-S2-01 e ISS-S2-02.

## Reglas rules.archive (config.yaml)

- **Deltas destructivos**: el delta contiene 1 REMOVED (`Paths /metrics/ingest y /logs/ingest`) con `(Reason: criterio 8 de #37 — nomenclatura definitiva /telemetry/*)` y `(Migration: tests, docs vivas y specs de arquitectura actualizados en el mismo cambio)`. El sync se aplicó durante apply sin runtime que romper (no existía implementación de ingesta con esas rutas) y fue verificado en este archive. Sin advertencia de merge destructivo pendiente.
- **CITATION.cff / experimentos ML**: el archivo `CITATION.cff` no existe en el repo (verificado); este cambio no toca componentes ML (D4: sin prometheus-client, sin dependencias nuevas, CPU-only <2GB RAM, $0/mo). Sin actualización requerida.
- **ADR registrado**: ADR-0002 (`docs/adr/0002-pipeline-ingesta-async.md`, formato Nygard, DD-7) creado en task 5.2 y verificado contra DD-7 en `verify-report` (coherence DD-1..DD-7 ✅). CHANGELOG.md registra el cambio (L28-38, sección Unreleased). Decisiones D1..D6 documentadas en `design.md` (tabla de decisiones) y confirmadas en `verify-report` (coherence D1..D6 ✅). La convención del repo registra las decisiones de cada cambio en el design del cambio; no se crearon archivos ADR individuales adicionales (sin precedente).

## Decisiones de arquitectura (D1..D6)

Confirmadas en `design.md` y reflejadas en el código (verificado en `verify-report` §Coherence):

| # | Decisión | Estado |
|---|----------|--------|
| D1 | Persistencia a BD: `user_session` ON CONFLICT DO NOTHING, bulk `rum_metric`/`js_exception` (catálogo cacheado), chunks 500, retry 3, dead-letter | ✅ |
| D2 | `application_id` sin autoridad de tenant (fuera de `required`, sin `unknown_application`) | ✅ |
| D3 | 429 `rate_limit_exceeded` declarado en el contrato sin implementación | ✅ |
| D4 | Sin prometheus-client; contadores en proceso (`ingest.*`) sin endpoint `/metrics` | ✅ |
| D5 | Handler global 422→400 scoped a `/telemetry/*` (resto conserva 422) | ✅ |
| D6 | Shutdown: `close() → join(timeout) → log → dispose_engine()` con timeout configurable | ✅ |

## Verificación del archive (Mechanical Copy Contract)

- Move: `git mv openspec/changes/2026-09-25-ISS-S2-03 openspec/changes/archive/2026-09-25-ISS-S2-03` — snapshot recursivo pre-move + `diff -r` post-move: **vacío (byte-identical)**. Ningún byte pasó por el modelo.
- El folder archivado contiene: `exploration.md`, `proposal.md`, `spec.md`, `design.md`, `tasks.md`, `apply-progress.md`, `verify-report.md` (7/7) + este `archive-report.md` (aditivo, excluido del diff).
- `openspec/changes/` ya no contiene el cambio activo (solo `archive/`).
- `tasks.md` archivado: 17/17 tareas `[x]`, sin tareas pendientes.
- `git status`: `apply-progress.md` y `tasks.md` (previamente trackeados) figuran como `R` (rename) hacia el archive; los 5 artefactos untracked (`exploration.md`, `proposal.md`, `spec.md`, `design.md`, `verify-report.md`) viajaron con el move del directorio y se incorporan al commit del archive.

### Salida verbatim del `diff -r` (snapshot vs destination)

```
=== MANDATORY diff -r readback (snapshot vs destination) ===
=== diff_status=0 ===
```

Sin diferencias (vacío) — única evidencia de aprobación.

## Artefactos leídos (trazabilidad)

- `openspec/changes/2026-09-25-ISS-S2-03/{exploration.md, proposal.md, spec.md, design.md, tasks.md, apply-progress.md, verify-report.md}` (leídos antes del move).
- `openspec/specs/openapi.yaml`, `openspec/specs/architecture/{interfaces,components,quality-attributes}.md` (estado vigente, verificación del sync).
- `docs/architecture/PipelineIngestaRUM.md`, `docs/architecture/ContratoIngestaRUM.md`, `docs/brief-v2.md`, `docs/adr/0002-pipeline-ingesta-async.md`, `CHANGELOG.md`, `docs/informe-avance-1/evaluacion-equipo.md`, `docs/business/issues-s1-s2.md` (docs vivas e históricos).
- `openspec/config.yaml` (rules.archive), `openspec/changes/archive/2026-09-23-ISS-S2-02/archive-report.md` (convención de formato).

## Hallazgos y riesgos residuales (no bloqueantes)

1. **SUG-1 (verify-report) — flake8 no cubre `tests/`**: el gate configurado es `flake8 src/` (limpio); `flake8 tests/` reporta E501 (L177, 100 > 99 chars) y W292 en `test_ingest_telemetry.py`. Trivial y fuera del gate; corregible si se decide incluir tests en el lint.
2. **SUG-2 (verify-report) — Handler `ingest_exceptions` sin ejercicio HTTP directo con key válida**: `telemetry.py` 87% (L54-58); el 202 de `/telemetry/exceptions` con key válida no tiene test HTTP propio (la lógica duplicada se cubre vía `/telemetry/metrics` + service con `JsExceptionBatch`). Coverage ≥80% (Acceptable); sin impacto de comportamiento.
3. **SUG-3 (verify-report) — Premisa experimental de OAS-9 superada (ADR-24)**: schemathesis 4.x trae OpenAPI 3.1 nativo; `test_schemathesis_live_contract_scoped` xpassed (mismo patrón que SUG-2 de ISS-S2-02). El gate contract queda verde (1 xpassed).
4. **SUG-4 (verify-report) — Conteo de requisitos 18/18**: 17 activos + 1 REMOVED verificado como evidencia de eliminación (`test_oas10_ingest_paths_replaced_by_telemetry` PASSED).
5. **Delivery pendiente**: el cambio NO está pusheado ni tiene PR al cierre de este archive — el orquestador pedirá aprobación del usuario antes de crear el PR. Sin push, sin PR en este paso.

## Verdict

**ARCHIVED** — El cambio ISS-S2-03 cerró el ciclo SDD completo: explorado, propuesto, especificado, diseñado, implementado (17/17 tareas, strict TDD), verificado (PASS, 18/18 requisitos, 32/32 escenarios, 209 passed + 1 xpassed, cobertura 93.06%, 0 critical/0 warning) y archivado con sync de deltas confirmado sobre los specs vigentes (openapi.yaml + architecture/* + docs vivas). Nomenclatura definitiva `/telemetry/*` sin referencias funcionales a rutas viejas; históricos intactos. Entrega (push/PR) pendiente de aprobación del usuario.