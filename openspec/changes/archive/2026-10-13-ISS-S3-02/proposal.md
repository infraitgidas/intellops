# Proposal: ISS-S3-02 — Normalización de datos de ingesta

**Cambio**: ISS-S3-02 (#41) · base `feat/ISS-S3-02` @ `1a46eb4` · store openspec · r1.

## Intent

El issue #41 pide `Raw → Validation → Normalization → Storage`; hoy la normalización es implícita, sin nombre y mal ubicada en el worker (`queue.py`, post-`202`), sin canonicalización de unidad/nombre. El orden literal está **invertido**: la validación rechaza las inconsistencias de unidad/nombre antes de que la normalización pueda resolverlas, por lo que los criterios 2–3 son inalcanzables. Arreglo: una etapa de normalización pura y con nombre corre **antes** de la validación; la validación sigue siendo la autoridad única de rechazo. La normalización resuelve **solo representaciones** (D4) — las magnitudes son la señal de anomalía, nunca se recortan.

## Scope

**In**: `ingest_normalizer` puro por evento pre-validación; timestamp → UTC con tz (ts de métrica ← ts de envelope, rechazar naïve/no parseable); alias de unidad `s|sec|secs|msec|millis`→`ms`, `counts`→`count` (idempotente); canonicalización de nombre de métrica/`error_type` (desconocido→`Other`); defaults opcionales del contrato; coerción de cadenas numéricas finitas; conteos no enteros rechazados (`invalid_range`); eliminar el fallback `now()` del worker.

**Out**: recorte de magnitudes (d); DDL/migración de `error_type` (c); backfill de eventos rechazados; cambios de envelope/`202`/backpressure.

## Capabilities

**New**: `ingest-normalization`. **Modified**: `architecture` (orden del pipeline + flexibilidad del contrato).

## Approach

Normalizador de dominio puro (exploration Enfoque 1) insertado en `IngestService` antes de `ingest_policy`; se reutilizan los registros de la policy para evitar deriva (R7).

## Affected Areas

Área | Impacto
---- | ------
`src/api/domain/services/ingest_normalizer.py` | Nuevo — normalización pura
`src/api/domain/services/ingest_service.py` | Modificado — paso de normalización (`:59-83`)
`src/api/domain/services/ingest_policy.py` | Modificado — registros compartidos (`:30-48`)
`src/api/infrastructure/ingest/queue.py` | Modificado — quitar coerción/`now()` (`:235-301`)
`openspec/specs/openapi.yaml` | Modificado — ampliar alias (`:953-956`)
`tests/test_ingest_normalizer.py` (nuevo), `tests/test_ingest_telemetry.py` | Nuevo/Modificado — tests
`ContratoIngestaRUM.md`, `PipelineIngestaRUM.md`, `CHANGELOG.md`, nuevo ADR | Modificado — docs

**Impacto en el contrato**: los alias pasan a aceptarse (retrocompatible); OpenAPI ampliado; unidades/nombres desconocidos aún rechazados.

## Risks

Riesgo | Prob. | Mitigación
---- | - | ----------
R1 ampliación del contrato (acepta antes rechazado) | Alta | decisiones a/e; actualizar OpenAPI
R2 destruye la señal de anomalía del ML | Alta | regla de solo representación (d)
R4 conversión no idempotente | Media | indexar por unidad declarada; tests de idempotencia
R5 ambigüedad de orden | Media | ADR registra normalizar-antes-de-validar
R6 reescritura silenciosa con `now()` | Media | eliminar el fallback; rechazar en su lugar
R3/R7/R9 catálogo, deriva, estricto-vs-flexible | Baja–Media | en código; registros compartidos; documentar

## Rollback Plan

Revertir el único PR: el normalizador es aditivo/aislado — restaurar el camino de validación directa de `IngestService` y la coerción del worker, eliminar el módulo y los tests. Sin cambio de DDL/esquema → sin rollback de datos. La ampliación de OpenAPI se revierte en el mismo commit. Las filas canónicas ya aceptadas siguen siendo válidas.

## Dependencies & Footprint

`ContratoIngestaRUM.md:30`; ADR-0002; `research.md` r1 (`obs-7a8aedcf0ba7123a`). Transformaciones puras en memoria, sin nueva dependencia/proceso/RAM — se mantiene <2GB RAM, CPU-only, $0/mes. Las magnitudes preservadas alimentan el objetivo de anomalías del ML; los campos canónicos mantienen consistente la exportación de S3-04.

## Success Criteria

- [ ] Unidades/nombres/`error_type` canonicalizados pre-validación; desconocidos rechazados.
- [ ] Sin recorte de magnitudes; TTFB de `9000ms` aceptado sin cambios.
- [ ] Normalizador puro, testeado por unidad; señal de anomalía intacta.
- [ ] Contrato/docs/ADR actualizados; sin DDL; cobertura ≥ 70%.
