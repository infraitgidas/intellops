# Proposal: ISS-S3-04 — Dataset operativo para ML (GitHub #43)

> **Decisión en una línea**: el AI engine consume `GET /metrics/query` por HTTP (API key por app), mapea `MetricAggregate` → `MetricBatchInput` sin `metric_id`, y `ANOMALY` se ancla a la serie/bucket `(application_id, metric_type_id, bucket_start, bucket_seconds)` vía migración `0004`.
>
> **Fuentes**: `exploration.md`, `research.md`, `decisiones-metric-id-y-frontera.md` §6 (D2 = M4, D4 = (a), implementador único: Romeo).

## Intent

El motor ML lee hoy un mock estático (`src/ml/mock_data.json`) y su contrato exige `metric_id`, que no existe en una fila agregada. #43 pide exponer el dataset **sin acoplar el ML a los internos de la ingesta**. Resultado esperado: un reader real, validado y configurable que consume el contrato público del read path, más una entidad `ANOMALY` coherente con datos agregados.

## Scope

### In Scope
1. **Contrato M4**: quitar `metric_id` de `MetricBatchInput`; agregar `bucket_seconds` a la identidad de la serie.
2. **Migración Alembic `0004`**: `ANOMALY` elimina `metric_id` + `fk_anomaly_metric`; agrega columnas de serie. Actualizar `ddl_v1.0.sql`.
3. **Reader/adaptador en `src/ml`**: cliente HTTP (`httpx`) a `GET /metrics/query`, API key por app, ventana `start/end` configurable (≤ 7 d), `bucket_seconds` configurable (default 60) y propagado a cada registro.
4. **Config** por env (`INTELLOPS_API_BASE_URL`, API key, `bucket_seconds`, ventana).
5. **Mocks alineados**: `mock_data.json`, `mock_reader.py`, `ml/data/generate_mock_dataset.py`.
6. **Docs**: `ContratoEntradaSalida.md`, contrato de dataset operativo, **ADR-0008** (reconcilia `containers.md` "lee `RUM_METRIC` de DB" vs ADR-0003 HTTP).
7. Tests (strict TDD): adaptador puro, reader con `httpx.MockTransport`, migración up/down.

### Out of Scope
- Entrenamiento / EDA (#44, ISS-S3-05); User Health Score por sesión; alertas.
- Cualquier cambio en `src/api` (ingesta o read path). `bucket_seconds` ya es parámetro del request: el reader lo elige y lo persiste; no hace falta que la respuesta lo exponga (corrige la observación de §6 del brief).
- Scheduler (pull bajo demanda); store de histórico propio.
- Archivos de PR #59: `queue.py`, policy/service de ingesta, `openapi.yaml` (`RumMetric.unit`), ADR 0004–0007, ARCH-5/6, `CHANGELOG.md` (follow-up post-merge de #59).

## Capabilities

### New Capabilities
- `ml-operational-dataset`: reader HTTP del read path, mapeo `MetricAggregate` → `MetricBatchInput`, config, límites de ventana/bucket y alineación de buckets.

### Modified Capabilities
- `database`: `ANOMALY` se ancla a la serie/bucket; sin FK a `rum_metric`.
- `architecture`: el AI engine **lee** telemetría vía HTTP (ADR-0008); sigue **escribiendo** `ANOMALY`/`ALERT` en DB. Ajuste en `containers.md` §2.3/C4 e `interfaces.md` §2.1.

## Approach

- **Adaptador puro** (sin red) + **cliente fino** (I/O), testeables por separado.
- **Alineación de buckets (hallazgo)**: el read path ancla los buckets al `start` de la ventana, no a epoch (`query_repository.py:8-11`). Para que la identidad de serie sea estable entre pulls, el reader **alinea `start`/`end` a múltiplos de `bucket_seconds` en UTC** antes de pedir.
- **Columnas nuevas de `ANOMALY`**: `application_id` (FK `application.app_id`), `metric_type_id SMALLINT` (FK `metric_type`), `bucket_start TIMESTAMPTZ`, `bucket_seconds INT CHECK (>= 60)`. Se mantiene `timestamp` como instante de detección (evita colisión de nombres).
- Sin cross-imports `src/ml` ↔ `src/api` (`containers.md` §5.1). Footprint: solo `httpx`.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `src/ml/schemas.py` | Modified | **Breaking**: sin `metric_id`; con `bucket_seconds` |
| `src/ml/pipeline/` (reader + adaptador nuevos, `mock_reader.py`) | New/Modified | Pull HTTP + mapeo validado |
| `src/ml/config.py`, `src/ml/main.py`, `src/ml/requirements*`/`Dockerfile` | New/Modified | Config env; dep `httpx` |
| `src/ml/mock_data.json`, `ml/data/generate_mock_dataset.py` | Modified | **Breaking**: sin `metric_id` |
| `src/api/infrastructure/db/migrations/versions/0004_*.py` | New | DDL `ANOMALY` (avisar a Santiago) |
| `openspec/specs/database/ddl_v1.0.sql` | Modified | Refleja `0004` |
| `docs/architecture/IsolationForest/ContratoEntradaSalida.md` | Modified | **Breaking**: entrada/salida M4 |
| `docs/adr/0008-*.md`, `containers.md`, `interfaces.md` | New/Modified | Reconciliación HTTP vs DB |
| `tests/` | New/Modified | Adaptador, reader, migración |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Identidad de serie inestable por buckets anclados a la ventana | High | Alinear ventana a múltiplos de `bucket_seconds` (UTC); test dedicado |
| `0004` choca con trabajo de DB (Santiago) | Med | Aviso previo; migración aislada y reversible |
| Downgrade no reversible con datos (`metric_id NOT NULL`) | Low | Hoy nadie escribe `ANOMALY`; downgrade documentado como válido solo con tabla vacía |
| Colisión con PR #59 | Med | Lista de archivos vedados; ADR ≥ 0008; CHANGELOG diferido |
| Key app-scoped limita dataset multi-app | Med | Una key por app en config; multi-app = N pulls |
| `ml/` es dominio de #44 (generador) | Low | Cambio mínimo (quitar campo); avisar en PR |

## Rollback Plan

1. `alembic downgrade 0003` (restaura `metric_id` + FK; requiere `ANOMALY` vacía).
2. Revert de los commits de `src/ml` y docs (cada slice es revertible por separado).
3. El read path no cambia: rollback sin impacto en `intellops-core`.

## Dependencies

- ISS-S3-01 (read path) mergeado. Aviso a Santiago (owner DB) sobre `0004`.
- Merge de PR #59 antes de tocar `CHANGELOG.md`.

## Success Criteria

- [ ] `MetricBatchInput` sin `metric_id`, con `bucket_seconds`; mocks y generador validan.
- [ ] Reader obtiene datos reales de `GET /metrics/query` (default 60 s, ventana ≤ 7 d) y devuelve `list[MetricBatchInput]` validada.
- [ ] Dos pulls solapados producen la misma identidad de bucket.
- [ ] `0004` up/down OK; `ddl_v1.0.sql` alineado.
- [ ] ADR-0008 aprobado; `ContratoEntradaSalida.md` actualizado.
- [ ] Cero cambios en `src/api` (salvo `0004`) y en archivos de #59; sin cross-imports.

## Review Workload Forecast

| Slice (PR) | Contenido | Líneas est. |
|---|---|---|
| 1 | ADR-0008 + contrato de dataset + `containers.md`/`interfaces.md` | ~200 |
| 2 | Contrato M4: `schemas.py`, mocks, generador, `ContratoEntradaSalida.md`, `0004`, DDL + tests | ~330 |
| 3 | Reader/adaptador + config + `httpx` + tests | ~380 |

- Total estimado: **~900 líneas**.
- Decision needed before apply: Yes
- Chained PRs recommended: Yes
- 400-line budget risk: High

## Proposal question round

> No se pudo consultar al usuario desde este sub-agente. Supuestos a revisar (D2/D4 no se reabren):

1. **Nombre de columna**: ¿`bucket_start` para la serie y `timestamp` sigue siendo el instante de detección?
2. **Alineación**: ¿aceptable que el reader alinee la ventana a epoch UTC, aunque difiera del default del read path (`now - 15 min`)?
3. **Multi-app**: ¿el MVP alcanza con una app por ejecución (una key), o se necesitan varias keys en config desde ya?
4. **Unicidad**: ¿puede haber más de una anomalía por `(serie, model_id)`? Define si va un índice único.
