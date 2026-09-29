# Contrato de Ingesta RUM

- **Versión del contrato**: 1.0
- **Fecha**: 2026-09-05
- **Issue**: ISS-S1-05
- **Owner**: Federico
- **Estado**: Aprobado para implementación

## Resumen del contrato

La ingesta RUM se compone de dos endpoints, ambos de aceptación asíncrona (202 Accepted) y siempre en modo batch:

| Endpoint | Payload | Propósito |
|----------|---------|-----------|
| `POST /telemetry/metrics` | `RumEventBatch` | Métricas RUM (TTFB, FCP, XHR_LATENCY, JS_EXCEPTION_RATE, RAGE_CLICK) |
| `POST /telemetry/exceptions` | `JsExceptionBatch` | Excepciones JavaScript no manejadas |

Ningún evento se envía suelto: el agente agrupa eventos en lotes de hasta 500 y los envía con `schema_version: "1.0"`. Ambas respuestas son idénticas (202 / 400 / 401 / 403 / 503 / 429) y están definidas en `openspec/specs/openapi.yaml`. El 202 se responde al **encolar** (semántica §3.4 del pipeline); el 503 `queue_full` es backpressure de la cola llena. La nomenclatura `/telemetry/*` es la definitiva (ADR-0002).

## Matriz de validación del evento RUM

| Tipo | Obligatorio | Tipo de dato | Unidad permitida | Rango de cordura (rechazo) | Rating de referencia (no rechazo) |
|------|-------------|--------------|------------------|----------------------------|-----------------------------------|
| TTFB | Sí | number | ms | 0–60000 | ≤800 good / ≤1800 needs-improvement / >1800 poor |
| FCP | Sí | number | ms | 0–120000 | ≤1800 good / ≤3000 needs-improvement / >3000 poor |
| XHR_LATENCY | Sí | number | ms | 0–60000 | Contexto por request en metadata |
| JS_EXCEPTION_RATE | Sí | number (entero) | count | ≥ 0 | Tasa calculada en query-time |
| RAGE_CLICK | Sí | number (entero) | count | ≥ 0 | — |

> **ACLARACIÓN IMPORTANTE**: el rango del contrato es un rango de CORdura, es decir, de rechazo de valores absurdos (ej. TTFB negativo o mayor a 60s). NO es un rango de calidad: un TTFB de 9000ms es un dato legítimo que el sistema acepta — es justamente el valor que el sistema debe detectar como anomalía. Los ratings good/poor son referencia para dashboard y alertas, no criterio de rechazo en el ingest.

## Matriz de validación del evento JS_EXCEPTION

| Campo | Obligatorio | Tipo | Longitud máxima | Notas |
|-------|-------------|------|-----------------|-------|
| `error_type` | Sí | string | 100 | Ej: TypeError, ReferenceError, RangeError, UnhandledRejection, Other |
| `message` | Sí | string | 2000 | Mensaje del error |
| `stack_trace` | No | string | 20000 | Opcional |
| `session_id` | Sí | string (uuid) | — | FK a `user_session` |
| `application_id` | No | string (uuid) | — | Opcional desde ISS-S2-03 (D2): el tenant se deriva EXCLUSIVAMENTE de la API key (IAUTH-2); el payload nunca es autoridad. Si viene, debe ser UUID válido |
| `metric_id` | No | string (uuid) | — | FK nullable a `rum_metric`, ON DELETE SET NULL |
| `timestamp` | Sí | string (date-time) | — | ISO 8601 UTC |

## Reglas de validación generales

- **UUID**: todos los identificadores (`session_id`, `application_id`, `metric_id`) deben ser UUID válidos.
- **Timestamp**: formato ISO 8601 en UTC, con zona horaria explícita.
- **Límites de batch**: máximo 500 eventos por batch y máximo 50 métricas por evento.
- **Versión**: `schema_version` debe ser exactamente `"1.0"`.

## Alineación con el DDL

### RumEvent → `rum_metric`

| Campo del contrato | Columna | Notas |
|--------------------|---------|-------|
| `metrics[].type` | `metric_type_id` | Se resuelve contra el catálogo `metric_type` (TTFB, FCP, XHR_LATENCY, JS_EXCEPTION_RATE, RAGE_CLICK) |
| `session_id` | `session_id` | FK a `user_session` |
| `metrics[].value` | `value` | `DOUBLE PRECISION` |
| `metrics[].unit` | `unit` | `TEXT` |
| `metrics[].page_url` (o `metadata.page_url`) | `page_url` | `TEXT` nullable |
| `metrics[].metadata` | `metadata` | `JSONB` nullable |
| `metrics[].timestamp` (o `timestamp` del envelope) | `timestamp` | `TIMESTAMPTZ` |

### JsExceptionEvent → `js_exception`

| Campo del contrato | Columna | Notas |
|--------------------|---------|-------|
| `error_type` | `error_type` | `TEXT NOT NULL` |
| `message` | `message` | `TEXT NOT NULL` |
| `stack_trace` | `stack_trace` | `TEXT` nullable |
| `session_id` | `session_id` | FK a `user_session` |
| `metric_id` | `metric_id` | FK nullable a `rum_metric`, ON DELETE SET NULL |
| `timestamp` | `timestamp` | `TIMESTAMPTZ NOT NULL` |

> **Nota**: `application_id` no persiste directo en ninguna de las dos tablas. El tenant de la sesión (`user_session.app_id`) se fija desde la aplicación autenticada por la API key al momento del ingest (IAUTH-2/D2), no desde el payload.

## Decisiones registradas

1. **JS_EXCEPTION por `/telemetry/exceptions`**: las excepciones JS usan un endpoint propio, no `/telemetry/metrics`, según la nomenclatura definitiva `/telemetry/*` (ADR-0002).
2. **Wrapper de batch incluido en esta issue**: los esquemas `RumEventBatch` y `JsExceptionBatch` forman parte del contrato de esta issue. El bulk insert asíncrono es del ISS-S2-03.
3. **`application_id` opcional (ISS-S2-03, D2)**: salió de `required` en `RumEvent` y `JsExceptionEvent` porque el tenant se deriva exclusivamente de la API key (IAUTH-2); el payload no es autoridad y el código `unknown_application` fue eliminado del flujo.

## Referencias

- Investigación: `docs/research/rum-agent-deep-dive.md`, `docs/research/frontend-observability.md`
- DDL: `openspec/specs/database/ddl_v1.0.sql`
- OpenAPI: `openspec/specs/openapi.yaml`
- Interfaces: `openspec/specs/architecture/interfaces.md`