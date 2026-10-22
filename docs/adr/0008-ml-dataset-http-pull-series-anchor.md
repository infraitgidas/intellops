# ADR 0008: Dataset operativo para ML — pull HTTP del read path y anomalía anclada a la serie

- **Estado**: Aceptado
- **Fecha**: 2026-10-14
- **Autores**: Equipo InfraIT — GIDAS UTN FrLP
- **Decisión relacionada**: Issue #43 (ISS-S3-04), ADR-0003, `openspec/changes/ISS-S3-04/`

## Contexto

`containers.md` declara que `intellops-ai-engine` lee `RUM_METRIC` directo de la base, mientras que ADR-0003 expone el read path `GET /metrics/query` (app-scoped, agregado). Además, el read path devuelve filas agregadas sin `metric_id`, pero `anomaly.metric_id` es `NOT NULL` con FK a `rum_metric`: una anomalía detectada sobre un bucket no tiene fila física a la cual apuntar.

## Decisión

1. **El AI engine consume el dataset por HTTP** (`GET /metrics/query`, key por app, pull bajo demanda). Prevalece sobre la lectura directa de `RUM_METRIC` de `containers.md`; se mantiene la regla §5.1 (sin cross-imports entre `intellops-core` e `intellops-ai-engine`). La escritura de `ANOMALY`/`ALERT` sigue siendo contra la base.
2. **La anomalía se ancla a la serie/bucket** `(application_id, metric_type_id, bucket_start, bucket_seconds)` en lugar de a `metric_id`. `MetricBatchInput` pierde `metric_id`; `anomaly.timestamp` se mantiene como instante de detección. Migración `0004`; índice único con `model_id` para reproceso idempotente.
3. **Granularidad por defecto 60 s**, configurable y persistida; la ventana se alinea a múltiplos de `bucket_seconds` en época UTC para que la identidad de la serie sea estable.

## Consecuencias

- Sin cambios en `src/api`; el contrato entre módulos es el read path público.
- Cambio breaking en `MetricBatchInput` y `ANOMALY`; seguro hoy porque nadie escribe en `anomaly`.
- La trazabilidad por fila física de `rum_metric` se pierde a propósito; el Health Score por sesión necesitará otra fuente.
- `containers.md` e `interfaces.md` quedan por actualizar como seguimiento.
