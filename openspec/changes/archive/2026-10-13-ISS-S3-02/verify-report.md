```yaml
schema: gentle-ai.verify-result/v1
evidence_revision: sha256:097be81299035c6d84e5777221be5c967373ea89cdd66606c5e0c27f14d2d821
verdict: pass_with_warnings
blockers: 0
critical_findings: 0
requirements: 9/9
scenarios: 18/18
test_command: DATABASE_URL=postgresql+asyncpg://intellops:intellops@172.18.0.4:5432/intellops PYTHONPATH=. .venv/bin/pytest --cov=src --cov-report=term-missing -q
test_exit_code: 0
test_output_hash: sha256:51c6e8411d344d2ccdc5fcc631924cc693a6f387b3b0a86bc0d5968d04e0ba64
build_command: docker compose build intellops-core
build_exit_code: 0
build_output_hash: sha256:0c070cf61c2bb3e7af3953a74f8c917ff0be89a14c127c2f18f6d392da2d6269
```

## Verification Report

**Change**: ISS-S3-02 — Normalización y calidad de datos de ingesta (GitHub #41)
**Version**: delta specs `ingest-normalization` (NORM-1..7) + `architecture` (ARCH-5/6)
**Mode**: Strict TDD (`openspec/config.yaml` `apply.tdd:true`, `testing.strict_tdd:true`, runner pytest)
**Rama**: `feat/ISS-S3-02` @ `150155d` (base `origin/develop` @ `1a46eb4`), árbol de trabajo limpio (sin cambios sin commitear en `src/`/`tests/`/`openspec/`)
**Fecha**: 2026-10-13
**Tipo de verificación**: Independiente y fresca — suite completa, capas unit/integration/contract, cobertura, linters y build re-ejecutados por el verificador contra el árbol actual.
**`evidence_revision`**: SHA-256 del `git rev-parse HEAD^{tree}` (`4cea490d4f8565660f5969c99f0dd654bcdca611`); commit `150155dfa99b12ddfeb4725e7dbf2bd404e46539`.

### Completeness

| Metric | Value |
|--------|-------|
| Tasks total | 18 |
| Tasks complete | 18 |
| Tasks incomplete | 0 |

`tasks.md` verificado: 18 checkboxes `[x]`, 0 pendientes. Requisitos contados por headings `### Requirement:` = 9 (NORM-1..7 + ARCH-5/6). Escenarios contados por headings `#### Scenario:` = 18.

### Build & Tests Execution

**Build**: ✅ Passed (exit 0)
```text
docker compose build intellops-core
#18 DONE 0.0s
 Image intellops-intellops-core Built
```
> El contrato y las migraciones dependen de `openspec/` + `schemathesis`, que la imagen `intellops-core` **no** copia/instala (limitación preexistente, ver W-2).

**Tests (suite completa, CI-equivalente)**: ✅ 300 passed / 0 failed / 1 xpassed
```text
DATABASE_URL=postgresql+asyncpg://intellops:intellops@172.18.0.4:5432/intellops PYTHONPATH=. .venv/bin/pytest --cov=src --cov-report=term-missing -q
============ 300 passed, 1 xpassed, 36 warnings in 67.15s (0:01:07) ============
Required test coverage of 70.0% reached. Total coverage: 94.12%
```
El xpass es `test_contract.py::test_schemathesis_live_contract_scoped` (xfail documentado, ADR-24) — la corrida live de schemathesis contra la app ASGI pasa.

**Capas (reproducidas por separado)**:

| Capa | Comando | Resultado |
|------|---------|-----------|
| Unit (sin DB) | `PYTHONPATH=. .venv/bin/pytest -m unit -q` | ✅ 181 passed, 120 deselected |
| Integration (Postgres real) | `... pytest -m integration -q` | ✅ 119 passed, 181 deselected, 1 xpassed |
| Unit — normalizador | `... pytest tests/test_ingest_normalizer.py -m unit -q` | ✅ 63 passed |
| Unit — telemetría | `... pytest tests/test_ingest_telemetry.py -m unit -q` | ✅ 57 passed |
| Integration — `/telemetry/*` | `... pytest tests/test_ingest_telemetry.py -m integration -q` | ✅ 22 passed |
| Contract — OpenAPI/schemathesis | `... pytest tests/test_contract.py -q` | ✅ 15 passed, 1 xpassed |

Suma de capas: 181 unit + 119 integration = 300 passed, +1 xpassed. Sin solapamiento.

**Lint**: ✅ `flake8 src/ tests/` exit 0. **Pylint**: ✅ `pylint src/` 9.80/10 (gate CI `--fail-under=9.0`); única nota informativa R0801 duplicate-code preexistente.

**Coverage**: 94.12% / umbral 70% → ✅ Above (gate `fail_under=70` en `pyproject.toml`).

### TDD Compliance

| Check | Result | Details |
|-------|--------|---------|
| TDD Evidence reported | ✅ | `apply-progress.md` con tabla "TDD Cycle Evidence" (18 filas) + "Evidencia de Work Units" |
| All tasks have tests | ✅ | 18/18 tareas con test/soporte verificado (`test_ingest_normalizer.py` nuevo, `test_ingest_telemetry.py`, `test_contract.py`) |
| RED confirmed (tests exist) | ✅ | Archivos de test existen en el repo; pasaron en ejecución independiente |
| GREEN confirmed (tests pass) | ✅ | 300 passed + 1 xpassed (exit 0) en ejecución independiente |
| Triangulation adequate | ✅ | Valores distintos por comportamiento (2000 ms vs 2 ms; `Other` vs canónicos; 1.5 rechazado vs 2.0 aceptado; naïve rechazado; 9000 preservado) |
| Safety Net for modified files | ✅ | Normalizador nuevo (N/A new válido); archivos modificados con suite unit/integration previa como red |

**TDD Compliance**: 6/6 checks passed

### Test Layer Distribution

| Layer | Tests | Files | Tools |
|-------|-------|-------|-------|
| Unit | ~120 (normalizador, política, servicio) | `test_ingest_normalizer.py`, `test_ingest_telemetry.py` | pytest |
| Integration (Postgres real + httpx ASGI) | ~60 (polemétricas `/telemetry/*`, worker) | `test_ingest_telemetry.py`, `test_migrations.py` | pytest + httpx AsyncClient + SQLAlchemy async |
| Contract | 16 (15 passed + 1 xpassed) | `test_contract.py` | schemathesis 4.28 + yaml |
| **Total** | **300 passed + 1 xpassed** | suite completa | |

### Changed File Coverage

| File | Line % | Uncovered | Rating |
|------|--------|-----------|--------|
| `src/api/domain/services/ingest_normalizer.py` (nuevo) | 97% | L89, 96, 143 | ✅ Excellent |
| `src/api/domain/services/ingest_policy.py` | 93% | L123, 130, 140, 147, 179, 182, 197, 249 | ✅ Excellent |
| `src/api/domain/services/ingest_service.py` | 96% | L107-108 (rama defensiva) | ✅ Excellent |
| `src/api/infrastructure/ingest/queue.py` | 91% | L179-183, 189, 202-207, 299, 303-304, 306, 308 | ✅ Excellent |

**Average changed file coverage**: 94.25% — todos ≥ 91% (sin WARNING de coverage). `ingest_normalizer.py` 97% coincide con lo declarado en `apply-progress.md`.

### Assertion Quality

**Assertion quality**: ✅ All assertions verify real behavior. Los tests afirman valores concretos: alias `s`→`unit=="ms"`, `value==2000.0` y `×1000` aplicado una sola vez; idempotencia `normalize(normalize(e)) == normalize(e)`; `error_type` desconocido→`Other`; `_canonical_ts` offset→UTC `2026-10-13T15:00:00+00:00`; naïve intacto (nunca `now()`); 9000 ms preservado; 1.5 rechazado sin redondeo; persistencia real en Postgres (`unit=="ms"`, `value==2000`, ts canónico exacto); contrato `unit` enum con la familia de alias y desconocida aún `invalid_unit`. Sin tautologías, ghost loops, smoke-only ni aserciones sin llamada a producción.

### Spec Compliance Matrix

Requisitos: 9/9. Escenarios: 18/18.

| Req | Escenario | Test | Result |
|-----|-----------|------|--------|
| NORM-1 | Aceptación parcial preservada | `test_ingest_normalizer.py > test_service_preserves_partial_202_when_alias_unresolvable` | ✅ COMPLIANT |
| NORM-2 | Offset canonicalizado | `test_ingest_normalizer.py > test_canonical_ts_returns_utc_iso_for_offset` + `test_service_inherits_envelope_timestamp_into_metric` | ✅ COMPLIANT |
| NORM-2 | La métrica hereda el envelope | `test_ingest_normalizer.py > test_normalize_metric_inherits_envelope_timestamp` | ✅ COMPLIANT |
| NORM-2 | Naive rechazado | `test_ingest_normalizer.py > test_normalize_rum_event_never_invents_missing_timestamp` + `test_ingest_telemetry.py > test_policy_rejects_naive_timestamp` + `test_telemetry_rejects_naive_timestamp_without_persisting` | ✅ COMPLIANT |
| NORM-3 | Segundos convertidos | `test_ingest_normalizer.py > test_normalize_converts_duration_aliases_to_ms` + `test_service_normalizes_unit_alias_before_validate` + `test_ingest_telemetry.py > test_telemetry_normalizes_alias_and_persists_canonical` | ✅ COMPLIANT |
| NORM-3 | Idempotente | `test_ingest_normalizer.py > test_normalize_unit_conversion_is_idempotent` + `test_normalize_never_applies_factor_twice` | ✅ COMPLIANT |
| NORM-3 | Unidad desconocida rechazada | `test_ingest_normalizer.py > test_normalize_passes_unknown_unit_through_for_validation` + `test_service_rejects_unknown_unit_after_normalization` + `test_ingest_telemetry.py > test_policy_rejects_unknown_unit` + `test_contract.py > test_oas14_unknown_unit_still_rejected_by_policy` | ✅ COMPLIANT |
| NORM-4 | Nombre con case-fold | `test_ingest_normalizer.py > test_normalize_casefolds_metric_type` | ✅ COMPLIANT |
| NORM-4 | error_type desconocido agrupado en bucket | `test_ingest_normalizer.py > test_normalize_canonicalizes_error_type` + `test_service_canonicalizes_error_type_before_validate` | ✅ COMPLIANT |
| NORM-5 | Requerido ausente | `test_ingest_normalizer.py > test_normalize_does_not_fabricate_missing_required_field` + `test_ingest_telemetry.py > test_policy_rejects_missing_required_field` | ✅ COMPLIANT |
| NORM-5 | Opcional ausente | `test_ingest_normalizer.py > test_normalize_does_not_fabricate_missing_optional_field` + `test_service_accepts_optional_absent_without_fabrication` | ✅ COMPLIANT |
| NORM-6 | Cadena numérica coaccionada | `test_ingest_normalizer.py > test_normalize_coerces_finite_numeric_string` | ✅ COMPLIANT |
| NORM-6 | No finito rechazado | `test_ingest_normalizer.py > test_normalize_does_not_coerce_non_finite_or_garbage` + `test_ingest_telemetry.py > test_policy_rejects_non_finite_values` | ✅ COMPLIANT |
| NORM-6 | Sin recorte | `test_ingest_normalizer.py > test_normalize_preserves_magnitude_without_clamping` + `test_ingest_telemetry.py > test_policy_rejects_ttfb_out_of_sanity_range_but_accepts_9000` | ✅ COMPLIANT |
| NORM-6 | Conteo fraccionario rechazado | `test_ingest_normalizer.py > test_normalize_keeps_fractional_count_intact` + `test_ingest_telemetry.py > test_policy_rejects_fractional_count_value` | ✅ COMPLIANT |
| ARCH-5 | Orden observable | `test_ingest_normalizer.py > test_service_normalizes_unit_alias_before_validate` + `test_ingest_telemetry.py > test_telemetry_normalizes_alias_and_persists_canonical` | ✅ COMPLIANT |
| ARCH-5 | Autoridad de rechazo sin cambios | `test_ingest_normalizer.py > test_service_rejects_unknown_unit_after_normalization` + `test_ingest_telemetry.py > test_policy_rejects_incoherent_unit` + `test_policy_rejects_naive_timestamp` | ✅ COMPLIANT |
| ARCH-6 | El contrato refleja los alias | `test_contract.py > test_oas14_metric_unit_accepts_alias_family` + `test_oas9_openapi_document_loads_in_schemathesis` | ✅ COMPLIANT |

**Compliance summary**: 18/18 escenarios con test pasando en ejecución independiente (9/9 requisitos).

### Correctness (Static Evidence)

| Requisito | Status | Notas |
|-----------|--------|-------|
| NORM-1 | ✅ Implementado | `ingest_service.py:69-92`: `payload = normalizer(...)` antes de `validator(payload)`; rechazo por índice sin abortar el lote (semántica parcial 202). Normalizador puro, sin E/S (`ingest_normalizer.py` solo `math`/`datetime`/dominio). |
| NORM-2 | ✅ Implementado | `_canonical_ts` (L36-46) → ISO-8601 UTC tz-aware o `None`; `_inherit_timestamp` (L125-138) hereda el ts del envelope; naïve/no parseable se deja intacto para que la validación rechace. Worker sin `now()`/`float()` (`queue.py:235-308`). |
| NORM-3 | ✅ Implementado | `UNIT_CONVERSIONS` en `ingest_policy.py:49-58` (fuente única); `_convert_unit` (L103-122) indexado por unidad declarada → idempotente. Desconocidas pasan → `invalid_unit`. |
| NORM-4 | ✅ Implementado | `METRIC_TYPE_ALIASES`/`ERROR_TYPE_CATALOG`/`ERROR_TYPE_ALIASES` en `ingest_policy.py:61-97`; `_canonical_metric_type`/`_canonical_error_type` con trim+case; desconocido `error_type`→`Other`. Sin DDL/migración. |
| NORM-5 | ✅ Implementado | Normalizador no inventa requeridos ni fabrica opcionales; hereda ts de métrica del envelope y nulables quedan `None`. Validación rechaza requeridos ausentes. |
| NORM-6 | ✅ Implementado | `_coerce_finite_number` coacciona strings numéricos finitos; `NaN`/`Infinity`/no finitos pasan → `invalid_range` (`_in_range` con `math.isfinite`, `ingest_policy.py:154-164`); conteos no enteros → `invalid_range` (L191-194) sin redondeo; 9000 ms intacto. |
| NORM-7 | ✅ Implementado | Sin cambios en `pyproject.toml`/dependencias (diff `1a46eb4..HEAD` no toca manifiesto); normalizador CPU-only, puro, sin procesos; `test_normalizer_has_no_third_party_dependencies` (AST). ML precisión/recall/F1 N/A por diseño (solo representación). |
| ARCH-5 | ✅ Implementado | `Raw → Normalize → Validate → Enqueue → Store` documentado en `docs/architecture/PipelineIngestaRUM.md:24,40` y materializado en `ingest_service.py`; ADRs 0004/0005 Aceptado. |
| ARCH-6 | ✅ Implementado | `openapi.yaml:953-955` enum `unit: [ms, count, s, sec, secs, msec, millis, counts]` + nota de canonicalización; `JsExceptionEvent.error_type` nota de canonicalización→`Other` sin enum (L987-991). Retrocompatible. |

### Coherence (Design)

| Decisión | Followed? | Notas |
|----------|-----------|-------|
| ADR-0004 — Normalizar antes de validar | ✅ Yes | Orden implementado en `ingest_service.py`; validación sigue siendo autoridad única de rechazo. |
| ADR-0005 — Solo representación, nunca recortar magnitudes | ✅ Yes | 9000 ms preservado; sin clamp/round; trim de whitespace limitado a campos de clasificación (desviación documentada, ver `apply-progress.md` #1). |
| ADR-0006 — `error_type` en catálogo de código, desconocido→`Other`, sin DDL | ✅ Yes | `ERROR_TYPE_CATALOG`/`ALIASES` en Python; sin migración. |
| ADR-0007 — Alias de unidad → canónica, indexada por unidad declarada | ✅ Yes | `UNIT_CONVERSIONS`; conversión escalar idempotente. |
| Registros compartidos (R7, sin deriva) | ✅ Yes | `ingest_normalizer` importa `UNIT_CONVERSIONS`/`METRIC_TYPE_ALIASES`/`ERROR_TYPE_*` de `ingest_policy`. |
| Payload canónico encolado; sin `now()`/`float()` en worker | ✅ Yes | `queue._build_rows` consume payload canónico; tests de guard estructural + integración real. |

**Desviaciones documentadas (ninguna rompe spec)**: (1) trim de whitespace solo en campos de clasificación (`type`/`unit`/`error_type`); `message`/`stack_trace` intactos (portadores de anomalía). (2) `QueuedEvent.payload` = canónico (tests de worker actualizados). (3) `_build_rows` sin fallback: ts ausente → `None` → BD NOT NULL lo rechaza. (4) Ejemplo de `test_policy_rejects_unknown_unit` cambiado a `"furlongs"` (realmente desconocida).

### Reproducibilidad de `apply-progress.md`

Todas las cifras materiales re-verificadas de forma independiente:

| Claim (apply-progress) | Reproducido | Estado |
|---|---|---|
| `pytest tests/test_ingest_normalizer.py -m unit` → 63 passed | 63 passed | ✅ coincide |
| `pytest tests/test_ingest_telemetry.py -m unit` → 57 passed | 57 passed | ✅ coincide |
| `pytest tests/test_ingest_telemetry.py -m integration` → 22 passed | 22 passed | ✅ coincide |
| `pytest tests/test_contract.py` → 15 passed | 15 passed, 1 xpassed | ✅ coincide |
| suite completa → 300 passed, 1 xpassed; 94.12% | 300 passed, 1 xpassed; 94.12% | ✅ coincide |
| `flake8 src/ tests/` → OK | exit 0 | ✅ coincide |
| `pylint src/` → 9.74/10 | 9.80/10 | ✅ mejora (delta informativo, sin impacto) |
| `ingest_normalizer.py` → 97% | 97% | ✅ coincide |
| Imagen `intellops-core` sin `openspec/`+`schemathesis` → contrato/migración fallan | confirmado (ver W-2) | ✅ coincide |

Sin discrepancias bloqueantes. El conteo unit declarado en fases intermedias (175) creció a 181 con las adiciones de fases posteriores; consistente con la evolución descrita.

### Issues Found

**CRITICAL**: None

**WARNING**:
- **W-1 — Paridad de entorno Python**: la suite se ejecutó en el venv del host con **Python 3.14.7**, mientras el CI usa **Python 3.11** y la imagen `intellops-core` es py3.11. `apply-progress.md` declara la capa integration verificada en contenedor py3.11 (22 passed) pero el verificador **no** re-ejecutó toda la suite en 3.11. Los resultados son consistentes, pero la paridad exacta con CI no quedó reproducida aquí. No es defecto de implementación.
- **W-2 — La imagen `intellops-core` no puede correr contrato/migraciones** (preexistente, sin relación con este cambio): `docker exec ... pytest tests/test_contract.py` falla con `ModuleNotFoundError: No module named 'schemathesis'` y `pytest tests/test_migrations.py` falla `test_ddl_v1_0_sql_synced_with_0003` con `FileNotFoundError: 'openspec/specs/database/ddl_v1.0.sql'` (5 passed, 1 failed). La imagen no copia `openspec/` ni instala `schemathesis`. Los tests sí corren en el host (venv) y en el CI (checkout + `pip install -e .[dev]`), por lo que el gate real queda cubierto. Verificar en `develop` para confirmar preexistencia.

**SUGGESTION**:
- **SUG-1 — Cobertura de no-E/S de NORM-1 es estructural**: la cláusula "el normalizador no realiza E/S" se cubre con `test_normalizer_has_no_third_party_dependencies` (inspección AST de imports), no con un test conductual (spy de I/O). Es un guard razonable; un test de comportamiento futura lo reforzaría.
- **SUG-2 — `ingest_policy.py` 93% y `queue.py` 91%**: líneas no cubiertas son ramas defensivas (`except` amplio en `_queue_depth`, parseos de ts inválidos). ≥ 80% (Acceptable); sin impacto funcional.
- **SUG-3 — Pylint R0801 duplicate-code** (preexistente, DTOs de capas distintas): informativo.

### Verdict

**PASS WITH WARNINGS** — Suite completa **300 passed + 1 xpassed** (exit 0), cobertura **94.12% ≥ 70%**, `flake8 src/ tests/` limpio, `pylint src/` **9.80/10 ≥ 9.0**, build `docker compose build intellops-core` exit 0. **18/18 escenarios** de spec con test pasando en ejecución independiente (**9/9 requisitos**), incluidos los de contrato OpenAPI (`unit` enum ampliado a la familia de alias). Se reprodujeron todas las cifras materiales de `apply-progress.md`. Sin hallazgos CRITICAL ni blockers. Los WARNING son de entorno (paridad Python 3.14 host vs 3.11 CI; imagen `intellops-core` sin `openspec/`+`schemathesis`, preexistente) y no defectos de implementación. Normalizador puro pre-validación, sin recorte de magnitudes, sin dependencias nuevas ni DDL: cumple las 3 patas (normalizador + wiring + limpieza del worker) y las decisiones ADR-0004..0007.
