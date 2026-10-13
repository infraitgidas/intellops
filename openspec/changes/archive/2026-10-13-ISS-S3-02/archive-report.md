# ARCHIVE REPORT — ISS-S3-02: Normalización y calidad de datos de ingesta

**Cambio**: ISS-S3-02 (GitHub #41). **Store**: openspec (file-based). **Fecha de archive**: 2026-10-13.
**Estado al cierre**: verificado PASS WITH WARNINGS — suite 300 passed + 1 xpassed (exit 0), cobertura 94.12% (gate ≥70), `flake8 src/ tests/` limpio, `pylint src/` 9.80/10 ≥ 9.0, `docker compose build intellops-core` exit 0, requisitos 9/9, escenarios 18/18, blockers 0, critical 0, 2 WARNING de entorno (W-1/W-2, no bloqueantes) y 3 SUGGESTIONs. 18/18 tareas completas.

## Final-State Authority

Este reporte describe el estado del cambio AL CIERRE, no en snapshots intermedios. Jerarquía aplicada:

1. **`tasks.md` persistido** (fuente de verdad de completitud): 18/18 tareas `[x]`, 0 `- [ ]`. Gate de completitud superado (verificado por conteo directo sobre el artefacto archivado).
2. **Hechos finales de estado del lanzamiento (orquestador)** — tienen precedencia sobre `verify-report`/`apply-progress`: 18/18 tareas, `verdict: pass_with_warnings`, 9/9 requisitos, 18/18 escenarios, 300 passed + 1 xpassed, cobertura 94.12%, flake8 limpio, pylint 9.80/10, build OK.
3. **`verify-report` y `apply-progress`** — snapshots intermedios: historia válida de su momento, nunca evidencia de estado final.

Estado nativo refrescado (`gentle-ai sdd-status ISS-S3-02 --json --instructions`): `dependencies.archive: ready`, `nextRecommended: archive`, `taskProgress 18/18 allComplete: true`, `dependencies.verify: ready`, `blockedReasons: []`. **Archive Readiness OK.**

### Hechos finales del ciclo

- **Verdict final**: PASS WITH WARNINGS — 9/9 requisitos (NORM-1..7 + ARCH-5/6), 18/18 escenarios con test pasando en ejecución independiente, `test_exit_code: 0`, `build_exit_code: 0`. **CRITICAL: 0. Blockers: 0.**
- **Métricas finales**: 300 passed + 1 xpassed (el xpass es `test_contract.py::test_schemathesis_live_contract_scoped`, xfail documentado ADR-24, que pasó); cobertura total 94.12% (gate 70%); capas: 181 unit + 119 integration = 300 (sin solapamiento); `flake8 src/ tests/` exit 0; `pylint src/` 9.80/10.
- **WARNINGs de entorno (no defectos, no bloquean archive)**:
  - **W-1 — Paridad de entorno Python**: la suite se ejecutó en el venv del host con Python 3.14.7, mientras el CI y la imagen `intellops-core` usan Python 3.11. `apply-progress` declara la capa integration verificada en contenedor py3.11 (22 passed), pero el verificador no re-ejecutó toda la suite en 3.11. Resultados consistentes; paridad exacta con CI no reproducida aquí. Sin impacto de implementación.
  - **W-2 — La imagen `intellops-core` no puede correr contrato/migraciones (preexistente, sin relación con este cambio)**: `docker exec ... pytest tests/test_contract.py` falla con `ModuleNotFoundError: No module named 'schemathesis'` y `test_migrations.py` falla `test_ddl_v1_0_sql_synced_with_0003` con `FileNotFoundError: 'openspec/specs/database/ddl_v1.0.sql'` (5 passed, 1 failed). La imagen no copia `openspec/` ni instala `schemathesis`. Los tests corren en el host (venv) y en CI (checkout + `pip install -e .[dev]`), por lo que el gate real queda cubierto; falla igual en `develop` → se sigue como cambio separado.
- **SUGGESTIONs de `verify-report` NO corregidas** (no bloqueantes, aceptadas al cierre): (SUG-1) la no-E/S de NORM-1 se cubre por inspección AST, no por test conductual; (SUG-2) `ingest_policy.py` 93% y `queue.py` 91% (ramas defensivas, ≥80% Acceptable); (SUG-3) pylint R0801 duplicate-code preexistente (DTOs de capas distintas, informativo).
- **Desviaciones de diseño documentadas (4, ninguna rompe spec)**: (1) trim de whitespace acotado a campos de clasificación (`type`/`unit`/`error_type`); `message`/`stack_trace` intactos (portadores de anomalía); (2) `QueuedEvent.payload` = canónico (tests de worker actualizados); (3) `_build_rows` sin fallback: ts ausente → `None` → BD NOT NULL lo rechaza; (4) ejemplo de `test_policy_rejects_unknown_unit` cambiado a `"furlongs"` (unidad realmente desconocida).
- **ADRs 0004–0007 Aceptados**: `docs/adr/0004-normalize-before-validate.md`, `0005-representation-only-normalization.md`, `0006-error-type-in-code-catalog.md`, `0007-unit-alias-conversion.md`, indexados en `docs/adr/README.md`.
- **Conteo de commits del lanzamiento (8) vs repo (9)**: el lanzamiento declaró 8 commits locales; `git rev-list --count origin/develop..HEAD` = **9** (la serie ISS-S3-02 incluye el commit de planificación SDD `150155d`, no listado en la tabla de `apply-progress`). Reconciliado con la evidencia del repo (ground truth del working tree): **9 commits** locales sobre `origin/develop`, sin pushear. No hay contradicción de estado — solo un subconteo del snapshot del lanzamiento.
- **Delivery**: single PR con `size:exception` aprobado por el mantenedor (presupuesto 800 líneas), **NO pusheado, sin PR** al cierre. Este archive agrega un commit local documental (`docs(openspec): archiva ISS-S3-02 …`); sin push.

## Sync de deltas a specs vigentes

El cambio define 2 dominios de delta en `openspec/changes/ISS-S3-02/specs/`: `ingest-normalization` (NORM-1..7, capacidad nueva) y `architecture` (ARCH-5/6, capability modificada). Ambos son **ADDED-only** (0 MODIFIED/REMOVED/RENAMED).

El orquestador instruyó explícitamente sincronizar los deltas dentro de `openspec/specs/` (skill `sdd-archive` §Step 2). Se aplicó el procedimiento del skill según exista o no el spec principal:

| Dominio | Spec principal | Acción | Detalle |
|---------|----------------|--------|---------|
| `ingest-normalization` | **No existía** → el delta ES el spec completo | **Creado** por copia mecánica | `openspec/specs/ingest-normalization/spec.md` (6040 bytes, copia byte-idéntica del delta) — NORM-1..7 + Purpose + Non-goals |
| `architecture` | **Existía** `openspec/specs/architecture/spec.md` | **Actualizado** (merge de ADDED) | Sección `## Requirements` nueva con **ARCH-5** y **ARCH-6** (2 requisitos, 3 escenarios) apendizada verbatim desde el delta; resto del spec preservado |
| `openapi.yaml` (contrato) | Existía | **Ya sincronizado durante apply** (commit `158f612`) | `RumMetric.unit` enum → `[ms, count, s, sec, secs, msec, millis, counts]` + nota de canonicalización (ARCH-6). Verificado en este archive: `openapi.yaml:953-955`. Sin edición adicional. |

### Desviación de convención de archive (intencional, instrucción explícita)

Los archives previos (ISS-S2-01/02/03, ISS-S3-01) NO mantenían specs de dominio por capability en `openspec/specs/`: la representación persistente de las capabilities era el contrato `openspec/specs/openapi.yaml` + los specs de arquitectura, y los deltas quedaban archivados íntegros en el change folder. En este archive, por instrucción explícita del orquestador (sincronizar los deltas dentro de `openspec/specs/`), se **creó** `openspec/specs/ingest-normalization/spec.md` y se **mergearon** ARCH-5/6 en `architecture/spec.md`. Se registra esta desviación para que el mantenedor pueda revisarla; si se prefiere la convención previa, revertir `openspec/specs/ingest-normalization/` y la sección `## Requirements` de `architecture/spec.md` no afecta el audit trail (los deltas persisten íntegros en este folder archivado).

### Reglas `rules.archive` (config.yaml)

- **Deltas destructivos: NINGUNO.** Ambos deltas son `## ADDED Requirements` puros. El merge a `architecture/spec.md` es aditivo (30 inserciones, 1 modificación de metadato de fecha). Sin REMOVED que requieran `(Reason/Migration)`. Sin advertencia de merge destructivo pendiente.
- **CITATION.cff**: no existe en el repo (verificado); el cambio no toca componentes ML (sin nuevas dependencias, CPU-only, <2GB RAM, $0/mes). Sin actualización requerida.
- **Experimentos ML**: N/A — normalización de solo representación, sin modelo ni entrenamiento (NORM-7 lo declara explícitamente). Límites de recursos respetados.
- **ADR registrado**: ADRs 0004–0007 en formato Nygard, estado **Aceptado**, indexados en `docs/adr/README.md`. Verificado por búsqueda de "Aceptado" en los 4 archivos.

## Decisiones de arquitectura (ADR-0004..0007)

| ADR | Decisión | Estado |
|-----|----------|--------|
| [0004](../../../../docs/adr/0004-normalize-before-validate.md) | Orden `Raw → Normalize → Validate → Enqueue → Store`; normalizar antes de validar; la validación sigue siendo la autoridad única de rechazo | ✅ Aceptado |
| [0005](../../../../docs/adr/0005-representation-only-normalization.md) | Solo representación — nunca recortar/redondear magnitudes (TTFB 9000ms es señal de anomalía) | ✅ Aceptado |
| [0006](../../../../docs/adr/0006-error-type-in-code-catalog.md) | Catálogo `error_type` en código, desconocido→`Other`, sin DDL/migración | ✅ Aceptado |
| [0007](../../../../docs/adr/0007-unit-alias-conversion.md) | Alias de unidad → canónica, indexado por la unidad declarada, idempotente | ✅ Aceptado |

## Verificación del archive (Mechanical Copy Contract)

Todas las operaciones de copia/movimiento de bytes se hicieron por shell (nunca Read→Write). Salidas `diff` verbatim:

### 1. Copia mecánica de `ingest-normalization` (delta → spec principal)

Copia con `cp` a un temporal + `diff -r` de readback (delta vs staged) + `mv`:

```
=== MANDATORY diff -r readback (delta vs staged copy) ===
diff_status=0 (empty = byte-identical)
=== VERBATIM diff (delta vs canonical ingest-normalization) ===
diff_exit=0  (0 = byte-identical, no output above = empty)
```

Sin diferencias — byte-idéntico. Única evidencia de aprobación.

### 2. Merge de `architecture` (ADDED apendizado)

El bloque de requisitos apendizado se tomó verbatim del delta (líneas 12-37) y se verificó contra el destino:

```
=== verify appended requirement block is byte-identical to delta lines 12-37 ===
append_diff=0 (empty above = byte-identical)
=== VERBATIM diff: delta requirement block (12-37) vs appended block (87-112) ===
block_diff_exit=0  (empty above = byte-identical)
=== confirm original lines 1-83 unchanged vs git HEAD ===
original_prefix=byte-identical
```

El prefijo original (líneas 1-83) permanece byte-idéntico a `git HEAD`; la única modificación a contenido existente es el metadato `- **Última actualización**: 2026-05-27 → 2026-10-13` (documentado). `git diff HEAD --stat -- openspec/specs/architecture/spec.md`: `1 file changed, 30 insertions(+), 1 deletion(-)`.

### 3. Movimiento del change folder al archive

`git mv openspec/changes/ISS-S3-02 openspec/changes/archive/2026-10-13-ISS-S3-02` (snapshot recursivo pre-move + destino guard sin colisión). Readback obligatorio:

```
=== MANDATORY diff -r readback (snapshot vs destination) ===
=== diff_status=0 ===
```

Sin diferencias (vacío) — byte-idéntico. Ningún byte pasó por el modelo.

### Contenido del archive (9 artefactos + este reporte aditivo)

- `exploration.md`, `research.md`, `preproposal.md`, `proposal.md`, `design.md`, `tasks.md`, `apply-progress.md`, `verify-report.md`, `specs/architecture/spec.md`, `specs/ingest-normalization/spec.md` + `archive-report.md` (aditivo, excluido del `diff -r`).
- `openspec/changes/` ya no contiene el cambio activo (queda `archive/` e `ISS-S2-04`, ajeno a este cambio).
- `tasks.md` archivado: **18/18 `[x]`, 0 `- [ ]`** (verificado por conteo directo).

## Artefactos leídos (trazabilidad)

- `openspec/changes/ISS-S3-02/{exploration.md, research.md, preproposal.md, proposal.md, design.md, tasks.md, apply-progress.md, verify-report.md}` y `specs/{architecture,ingest-normalization}/spec.md` (leídos antes del move).
- `openspec/specs/{architecture/spec.md, openapi.yaml}`, `openspec/config.yaml` (rules.archive), `openspec/changes/archive/2026-09-29-ISS-S3-01/archive-report.md` (convención de formato).
- `docs/adr/0004..0007-*.md` + `docs/adr/README.md`, `CHANGELOG.md`.
- Estado nativo: `gentle-ai sdd-status ISS-S3-02 --json --instructions`.

## Hallazgos y riesgos residuales (no bloqueantes)

1. **W-2 (verify-report) — Imagen `intellops-core` sin `openspec/`+`schemathesis`** (preexistente, sin relación con este cambio): contrato/migraciones no corren dentro de la imagen; falla igual en `develop`. Cubierto por host/CI. Seguir como cambio separado.
2. **W-1 (verify-report) — Paridad Python 3.14 host vs 3.11 CI**: la suite completa no se re-ejecutó en 3.11; resultados consistentes. Recomendación: correr la suite en la imagen/CI py3.11 para paridad exacta.
3. **SUG-1..3 (verify-report)**: guard de no-E/S por AST (no conductual), coverage 93%/91% en ramas defensivas, pylint R0801 preexistente. Aceptadas.
4. **Desviación de convención de archive** (ver arriba): `openspec/specs/ingest-normalization/` creado y `architecture/spec.md` mergeado por instrucción explícita del orquestador; difiere de la convención S2/S3 (sin specs de dominio por capability). Revisable por el mantenedor.
5. **Delivery pendiente**: el cambio NO está pusheado ni tiene PR al cierre. El commit de archive se hace local (convención `docs(openspec): archiva ISS-SX-XX …`); push/PR quedan como decisión humana separada.

## Verdict

**ARCHIVED (intentional-with-warnings)** — El cambio ISS-S3-02 cerró el ciclo SDD completo: explorado, propuesto, especificado, diseñado, implementado (18/18 tareas, strict TDD), verificado (PASS WITH WARNINGS, 9/9 requisitos, 18/18 escenarios con Postgres real + httpx ASGI + schemathesis, 300 passed + 1 xpassed, cobertura 94.12%, `flake8` limpio, `pylint` 9.80/10, build exit 0, 0 CRITICAL, 0 blockers) y archivado con sync de deltas aplicado sobre los specs vigentes (`architecture/spec.md` mergeado con ARCH-5/6; `ingest-normalization/spec.md` creado; `openapi.yaml` ya sincronizado en apply). Los 2 WARNING son de entorno (paridad Python; imagen sin `openspec/`+`schemathesis`, preexistente) y no defectos de implementación. La desviación de convención (specs de dominio por capability) es intencional por instrucción del orquestador y queda registrada. Entrega (push/PR) pendiente de aprobación del usuario.

## Next recommended

**none** — ciclo SDD cerrado para ISS-S3-02. Siguiente acción fuera de SDD: revisión del mantenedor y apertura del single PR con `size:exception`; el follow-up de W-2 (imagen `intellops-core` sin `openspec/`+`schemathesis`) se rastrea como cambio separado.
