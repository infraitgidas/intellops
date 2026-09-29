# ADR 0003: Ownership de tenant en la persistencia de telemetría y read path app-scoped

- **Estado**: Aceptado
- **Fecha**: 2026-09-29
- **Autores**: Equipo InfraIT — GIDAS UTN FrLP
- **Decisión relacionada**: Issue #40 (ISS-S3-01), `openspec/specs/openapi.yaml:124-137` (`GET /metrics/query` `queryMetrics`, `GET /metrics/list` `listMetrics`), investigación obs #216 (gaps C2-C4/C6), `src/ml/schemas.py` (`MetricBatchInput`)

## Contexto

La ingesta RUM (ISS-S2-03, PR #55) persistía `user_session` con `ON CONFLICT (session_id) DO NOTHING` y correlacionaba `js_exception.metric_id` contra cualquier métrica existente, sin validar propiedad. Tres gaps:

- **C2 (CRITICAL, aislamiento multi-tenant)**: una aplicación B podía reutilizar el `session_id` de una sesión ya persistida bajo la aplicación A. El upsert era no-op (la sesión seguía siendo de A), pero las métricas y excepciones de B referenciando ese `session_id` se insertaban igual: quedaban **atadas a una sesión de otro tenant** (C3).
- **C4 (correlación cross-app)**: una excepción de B podía reivindicar `metric_id` de una métrica de A y persistir la referencia, filtrando ownership.
- **C6 (read path ausente)**: no existía forma app-scoped de consultar métricas agregadas; el futuro worker ML (S3-04, #43) necesita el shape `(application_id, metric_type_id, timestamp, value, session_count)`.

Restricciones vigentes: CPU-only, < 2GB RAM, $0/mes, **sin DDL nuevo** (sin migración), contratos OpenAPI 3.1 intactos (no romper operationIds/paths de `openapi.yaml:124-137`).

## Decisión

**DD-8 — Ownership resuelto en el repositorio, antes del insert.** `_upsert_sessions` ejecuta un `SELECT session_id, app_id FROM user_session WHERE session_id IN (chunk)` previo al insert (una sentencia, O(chunk), índice PK) y devuelve el `set[UUID]` de **sesiones extranjeras** (existen bajo otra app). `persist_chunk` descarta las métricas/excepciones que las referencian y las cuenta en `PersistStats.session_foreign` → `ingest.session_foreign_total`. La propiedad de la sesión es un hecho transaccional de BD que el worker observa en el mismo `AsyncSession` del chunk: sin ventana TOCTOU entre check y write.

**DD-9 — Agregación del read path EN SQL.** `SQLAlchemyQueryRepository.query_metrics` ejecuta una sola sentencia `SELECT ... JOIN user_session us ON us.session_id = rm.session_id WHERE us.app_id = :tenant ... GROUP BY metric_type_id + bucket`, con bucket de epoch **anclado a `:start`** (determinista, alineado a la ventana del request), `AVG(value)::float8` y `COUNT(DISTINCT session_id)::int`. PostgreSQL agrega sin copiar filas al proceso (footprint ~0); el plan usa los índices existentes (`idx_user_session_app_id`, `idx_rum_metric_*`). El shape devuelto es el ML C6 (base de `MetricBatchInput` sin `metric_id`): `(application_id, metric_type_id, timestamp, value, session_count)`.

**DD-10 — Contadores de descartes por ownership en el mecanismo existente.** `IngestCounters` (D4/RUM-8, sin prometheus-client) gana `session_foreign(n)`/`metric_id_foreign(n)` con keys `ingest.session_foreign_total` e `ingest.metric_id_foreign_total` en `snapshot()`; `PersistStats` gana los campos `session_foreign`/`metric_id_foreign` (defaults a 0 → compat con mocks). El worker de `queue.py` incrementa desde `PersistStats` con wiring mínimo.

**Correlación metric_id scoped (RUM-10)**: `_bulk_exceptions` solo reivindica un `metric_id` si la métrica existe Y su sesión pertenece al mismo tenant del lote; inexistente → `NULL` + `metric_id_unknown_total` (RUM-6 vigente); existente cross-app → `NULL` + `metric_id_foreign_total`.

**Read path expuesto** vía `GET /metrics/query` (`queryMetrics`) y `GET /metrics/list` (`listMetrics`) con `Depends(require_api_key)`: el tenant se deriva EXCLUSIVAMENTE de la key (OAS-14). `QueryService` acota antes de tocar el repo: ventana default 15 min, máximo 7 días, bucket mínimo 60 s, `start < end` → `QueryRangeError` 422 `invalid_query_range` (ADR-09).

## Consecuencias

### Positivas

- **Cierra el gap CRITICAL C2-C4**: el replay cross-tenant (C5) deja los datos del dueño intactos y las filas intrusas nunca se insertan (sin deuda residual en rollback).
- **Sin DDL**: el fix es lógica de upsert/repo; el read path solo SELECT. Rollback = revert del PR.
- **Read path listo para S3-04**: shape ML exacto agregado en SQL, app-scoped, < 2 s en ventana default por plan indexado.
- **Observabilidad**: los descartes por ownership son visibles en `snapshot()` bajo el naming contract `ingest.` + `_total`.
- **Contrato intacto**: operationIds `queryMetrics`/`listMetrics` y paths sin cambios; Schemathesis scoped verde.

### Negativas / Trade-offs

- **Una consulta extra por chunk** (SELECT por PK ≤ 500 ids) en la ingesta: costo O(chunk) despreciable frente al INSERT batch, a cambio de la garantía de aislamiento.
- **El read path devuelve el shape agregado sin `metric_id`**: S3-04 deberá mapear `MetricAggregate` → `MetricBatchInput` (contrato explícito de TQ-1).
- **Collisión same-chunk de primera vez** (dos tenants envían el mismo `session_id` NUEVO en el mismo chunk): el SELECT pre-insert no la detecta (ninguno existe aún); ON CONFLICT DO NOTHING conserva una de las filas y las métricas del otro tenant quedan bajo esa sesión. Caso límite no cubierto por la spec C5; mitigación futura: índice único `(session_id, app_id)` (DDL) o dedup intra-chunk.

### Riesgos

- **Fix descarta sesiones legítimas**: mitigado por resolución por PK (`session_id` + `app_id` del tenant) y test de replay C5 (reenvío del mismo tenant → no-op sin contador).
- **Read path con escaneo amplio**: mitigado por índices existentes y ventana acotada (default 15 min); peor caso 7 días acotado por el rango.

## Alternativas Consideradas

| Alternativa | Descripción | Razón de descarte |
|-------------|-------------|-------------------|
| Ownership en service layer | Validar la sesión al encolar | TOCTOU: la sesión puede crearse entre encolado y persistencia; el service no tiene sesión de BD |
| `WHERE app_id = tenant` en el conflict | Filtro de tenant en el ON CONFLICT | No soportado: `ON CONFLICT DO NOTHING` no admite filtro (el target es la constraint) |
| Índice único `(session_id, app_id)` | DDL nuevo que impide la colisión en BD | Fuera de scope: sin migración; el fix debe ser lógica de upsert |
| Agregación en memoria | Materializar el rango y agrupar en Python | Viola < 2GB RAM en ventanas grandes; RAM y CPU Python |
| Vista materializada pre-agregada | Read path sobre agregados pre-calculados | DDL nuevo + latencia de refresco; fuera de scope |
| Endpoint `/metrics` Prometheus para contadores | Observabilidad estándar | Fuera de scope (D4): el mecanismo `snapshot()` ya existe y el worker lo consume |

## Recursos

- Implementación: `src/api/infrastructure/db/repositories/sqlalchemy_ingest_repository.py`, `src/api/infrastructure/ingest/counters.py`, `src/api/infrastructure/ingest/queue.py`, `src/api/domain/repositories/query_repository.py`, `src/api/infrastructure/db/repositories/sqlalchemy_query_repository.py`, `src/api/domain/services/query_service.py`, `src/api/presentation/routers/metrics.py`, `src/api/presentation/schemas/metrics.py`.
- Config: sin cambios (límites TQ-2 constantes en `query_service.py`).
- DDL: sin migración (tablas `user_session`, `rum_metric`, `js_exception`, `metric_type` existen desde S1).

## Referencias

- Issue #40 (`docs/business/issues-s2-s3.md`)
- Investigación obs #216: C2/C3 (aislamiento), C4 (correlación), C5 (test faltante), C6 (shape ML), C8 (sin denormalizar app_id)
- `openspec/specs/openapi.yaml:124-137` (OAS-13: contrato de consulta completado)
- `src/ml/schemas.py` (`MetricBatchInput` — base del shape C6)
- [ADR Template](0000-template.md), ADR-0002 (pipeline de ingesta, base de este cambio)