# Proposal: ISS-S3-01 — Persistencia de telemetría (verificación + hardening + read path)

**Cambio**: ISS-S3-01 (#40). **Base**: develop con ISS-S2-03 mergeado (PR #55).

## Intent

Los 4 criterios de #40 ya los cumple ISS-S2-03. ISS-S3-01 se re-encuadra para aportar valor
nuevo: (1) verificar con tests la persistencia existente, (2) cerrar el gap CRITICAL de
aislamiento multi-tenant (colisión cross-tenant de session_id), (3) habilitar el read path de
ISS-S3-04 (#43): query repository + `GET /metrics/query` + `GET /metrics/list` (openapi.yaml:124-137).

## Scope

### In Scope (RFC 2119)
- MUST: ownership en upsert de `user_session` — predicado de tenant en el path ON CONFLICT;
  session_id de otra app → descartar filas del lote + contador `session_foreign_total`.
- MUST: correlación `metric_id` de excepciones con scope de ownership; si no → NULL + contador.
- MUST: query repository app-scoped (`user_session.app_id = tenant`), agregación por bucket,
  relación de sesión preservada; shape ML `(application_id, metric_type_id, timestamp, value, session_count)`.
- MUST: endpoints `GET /metrics/query` + `GET /metrics/list` alineados a openapi.yaml (sin romper contrato).
- MUST: tests de collision/replay (app B reutilizando session_id de app A) — el test faltante (C5).
- SHALL: rollback plan + estimación de recursos (<2GB RAM, CPU-only).
- SHOULD: contadores de observabilidad para descartes por ownership.
- MAY: nota en asyncapi.yaml sobre MetricBatchEvent obsoleto (follow-up).

### Out of Scope
- Rewiring del worker ML (ISS-S3-04, #43); rework AsyncAPI.
- Migración de esquema: NO requerida — fix de ownership es lógica de upsert/repo, sin DDL nuevo.
- Desnormalizar app_id en rum_metric/js_exception (rechazado en investigación, C8).
- Normalización de error_type a catálogo (ISS-S3-02, #41).

## Capabilities

### New Capabilities
- `telemetry-query`: read path app-scoped — query repository, agregación temporal, endpoints
  `GET /metrics/query` + `GET /metrics/list`, shape ML listo para S3-04.

### Modified Capabilities
- `rum-ingest`: ownership de sesión en upsert + correlación metric_id scoped por tenant.
- `openapi`: completar `/metrics/query` y `/metrics/list` (parámetros, respuestas, security).

## Approach

Ownership check EN EL REPOSITORIO, no en service layer: la propiedad de sesión es un hecho de BD
que el service no conoce en encolado; validar ahí introduce TOCTOU. En
`SQLAlchemyIngestRepository._upsert_sessions`, antes del insert, resolver los session_id existentes
del chunk (SELECT app_id WHERE session_id IN) — los de otra app se descartan (contador), los
nuevos van a ON CONFLICT DO NOTHING. En `_bulk_exceptions`, el SELECT de correlación filtra por
session_id del lote. Query repo nuevo: JOIN user_session→rum_metric con app_id=tenant, GROUP BY
metric_type_id + bucket, AVG(value)+COUNT(DISTINCT session_id). Router `metrics.py` con
`require_api_key`. TDD + Schemathesis.

## Affected Areas

| Área | Impacto | Descripción |
|------|---------|-------------|
| `sqlalchemy_ingest_repository.py` | Modificado | ownership upsert + correlación scoped |
| `ingest/queue.py` | Modificado | descartes de sesión extranjera + contadores |
| `query_repository.py` + `sqlalchemy_query_repository.py` | Nuevo | query app-scoped time-bucketed |
| `routers/metrics.py` + schemas | Nuevo | GET /metrics/query, /metrics/list |
| `openspec/specs/openapi.yaml` | Modificado | endpoints 124-137 |
| `tests/test_ingest_telemetry.py`, `tests/test_metrics_query.py` | Nuevo/Mod | collision/replay + read path |

Módulos: seguridad (ownership), ML (shape), QA (tests/contract), captura (sin cambios).

## Risks

| Riesgo | Prob. | Mitigación |
|--------|-------|------------|
| Fix descarta sesiones legítimas | Media | Resolución por PK + test replay |
| Read path N+1 / escaneo amplio | Media | Índices existentes (idx_user_session_app_id, idx_rum_metric_*); agregación en SQL |
| Romper contrato OpenAPI | Media | Schemathesis sobre 124-137; no cambiar operationIds |

## Rollback Plan

- Código: revert del PR (sin migración nueva → sin rollback de DDL).
- Datos: filas descartadas no se insertan → sin deuda residual.

## Dependencies

- ISS-S2-03 (#37) mergeado en develop (PR #55) — base.
- Investigación obs #216 (S1/S8/S9/S12/S20/S22-S24): C2-C4 gaps, C6 shape ML, C7 asyncapi stale.
- Cadena: #40 (S3-01) → #43 (S3-04) → #41 (S3-02).

## Success Criteria

- [ ] Collision/replay: sesión de A reutilizada por B → filas NO se persisten bajo A; contador incrementa.
- [ ] Correlación metric_id cross-app → NULL + contador; query repo devuelve shape ML exacto.
- [ ] GET /metrics/query + /metrics/list responden 200 con apiKey, app-scoped; openapi 124-137 intacto; Schemathesis verde.
- [ ] pytest verde, cobertura ≥70%, CHANGELOG + ADR actualizados.