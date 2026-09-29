# ADR 0002: Pipeline de ingesta RUM asíncrono en proceso (cola asyncio + workers) y nomenclatura definitiva `/telemetry/*`

- **Estado**: Aceptado
- **Fecha**: 2026-09-25
- **Autores**: Federico Cavallero (Equipo InfraIT — GIDAS UTN FrLP)
- **Decisión relacionada**: Issue #37 (ISS-S2-03), `docs/architecture/PipelineIngestaRUM.md` §3, `openspec/specs/architecture/interfaces.md` §1 (decisión S1 de nomenclatura, ahora revertida)

## Contexto

La ingesta RUM (`POST /telemetry/metrics` y `POST /telemetry/exceptions`) debe aceptar batches de hasta 500 eventos con procesamiento **desacoplado del request** y backpressure, bajo las restricciones del proyecto: CPU-only, < 2GB RAM, $0/mes operativo y **sin broker externo** (criterio explícito de #37). El pipeline S1 aprobado (`PipelineIngestaRUM.md` §3) ya prescribía una cola en proceso con interfaz abstraída, pero la implementación no existía.

Decisión S1 de nomenclatura previa: `interfaces.md` registró `/metrics/ingest` y `/logs/ingest` como canónicos sobre `/telemetry/*`, con unificación de prefijo `/metrics/`. El criterio 8 de #37 revierte esa decisión: la nomenclatura definitiva es `/telemetry/*` (sin runtime que romper — no existía implementación de ingesta).

## Decisión

**1. Pipeline asíncrono en proceso**: puerto `IngestQueue` (Protocol con `enqueue`/`close`/`join`) implementado con `asyncio.Queue(maxsize=10000)` y worker tasks creados en el lifespan de FastAPI. La validación (envelope→400, evento→202 parcial) y el encolado ocurren en el request; los workers persisten en chunks de 500 filas con retry 3 (backoff 0.5/1/2 s, solo errores transitorios de BD) y dead-letter logueada (nunca pérdida silenciosa). Cola llena → 503 `queue_full` (backpressure). El shutdown drena la cola con timeout acotado antes de `dispose_engine()`. El tenant de cada evento se fija en el encolado desde la aplicación autenticada por la key (IAUTH-2: el `application_id` del payload no es autoridad).

**2. Nomenclatura revertida**: los endpoints de ingesta se documentan e implementan como `POST /telemetry/metrics` y `POST /telemetry/exceptions`, reemplazando `/metrics/ingest` y `/logs/ingest` en OpenAPI, specs de arquitectura y docs vivas. Las referencias históricas (`docs/informe-avance-1/`, `docs/business/issues-s1-s2.md`) se conservan como registros.

## Consecuencias

### Positivas

- **Footprint mínimo**: sin infraestructura nueva (sin Redis/AMQP/Celery), coherente con <2GB RAM, CPU-only y $0/mes.
- **Backpressure real**: `maxsize` + `put_nowait` → 503 sin bloquear el request (criterio 5 de #37).
- **Migrabilidad**: el puerto `IngestQueue` permite reemplazar la cola en proceso por un broker durable sin tocar routers ni servicio (extensión S2+ del pipeline §6).
- **Determinismo de tests**: cola y workers testables con pytest-asyncio y Postgres real; el 202 se responde al encolar (semántica §3.4), no al persistir.
- **Contrato alineado**: `security: [apiKey]` aplicado a los paths de producción cierra IAUTH-5.

### Negativas / Trade-offs

- **Sin durabilidad ante reinicios**: los eventos en cola se pierden si el proceso muere sin drenar (limitación aceptada explícitamente en S1; mitigada con drenado en shutdown + dead-letter logueada).
- **Cola por proceso**: `uvicorn --workers > 1` fragmentaría la cola; el runtime queda restringido a 1 worker (CMD actual, anclado por `test_container_import_path.py`).
- **`batch_id` no persistido**: la correlación entre request y filas en BD es solo por logs (S1).

### Riesgos

- **Pérdida de eventos en cola ante apagado forzoso (SIGKILL)**: aceptado; el drenado de shutdown cubre el apagado graceful.
- **Breaking de contract tests (OAS-6/9/10) por el renombrado**: tests actualizados en el mismo cambio; no había runtime previo que romper.

## Alternativas Consideradas

| Alternativa | Descripción | Razón de descarte |
|-------------|-------------|-------------------|
| `BackgroundTasks` de FastAPI | Tareas triviales post-response | Sin backpressure (acumulación ilimitada), sin batching ni orden; no cumple el criterio de backpressure |
| Broker externo (Redis/AMQP/Celery) | Durabilidad y escala horizontal | Excluido explícitamente por #37; viola $0/mes y <2GB RAM; agrega contenedor y operación |
| Worker en contenedor separado | Aislamiento de OOM | Contradice el pipeline S1 (cola en core); sin broker exigiría DB-polling con tabla staging; overkill para S2 |
| Mantener `/metrics/ingest` | Coherencia con la decisión S1 | El criterio 8 de #37 define `/telemetry/*` como nomenclatura definitiva; la unificación `/metrics/` no prosperó |

## Recursos

- Implementación: `src/api/infrastructure/ingest/queue.py`, `src/api/domain/services/ingest_service.py`, `src/api/presentation/routers/telemetry.py`.
- Config: `INGEST_QUEUE_MAXSIZE=10000`, `INGEST_WORKERS=2`, `INGEST_SHUTDOWN_TIMEOUT` (segundos, acotado).
- DDL: sin migración (tablas `rum_metric`, `js_exception`, `user_session` existen desde S1).

## Referencias

- Issue #37 (`docs/business/issues-s2-s3.md`)
- `docs/architecture/PipelineIngestaRUM.md` §3 (cola en proceso) y §3.4 (semántica 202)
- `docs/architecture/ContratoIngestaRUM.md` (política por evento)
- `openspec/specs/architecture/interfaces.md` §1 (decisión S1 revertida)
- [ADR Template](0000-template.md)