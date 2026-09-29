# Proposal: ISS-S2-03 — Ingesta RUM asíncrona

**Cambio**: ISS-S2-03 (#37). **Base**: develop con ISS-S2-01 + ISS-S2-02 mergeados.

## Intent

Implementar los handlers de ingesta RUM `POST /telemetry/metrics` y `POST /telemetry/exceptions` con `Depends(require_api_key)`, procesamiento asíncrono desacoplado del request (cola en proceso + workers), validación según política ya especificada, backpressure y persistencia a BD. Cierra el wiring de IAUTH-5 y la nomenclatura `/telemetry/*`; cubre los 8 criterios de #37.

## Scope

### In Scope
- Endpoints `/telemetry/metrics` y `/telemetry/exceptions` (guard `apiKey`, 401/403).
- Validación envelope→400 (`schema_validation_error`, D5) y por evento→202 parcial con `rejected[{index, reason}]` según `PipelineIngestaRUM.md` §2.
- Cola `asyncio.Queue` acotada + worker tasks en lifespan, detrás de interfaz abstraída; 503 `queue_full` (backpressure).
- Persistencia del worker a `rum_metric`, `js_exception`, `user_session` (D1).
- Drenado de cola en shutdown con timeout acotado (D6).
- Renombrado de rutas viejas a `/telemetry/*` en OpenAPI, tests, Schemathesis y docs vivas.
- Observabilidad: logs estructurados + contadores en proceso (D4).

### Out of Scope
- Rate limiting (429 solo declarado, D3); `/metrics` OpenMetrics y prometheus-client (D4); analítica/calidad de datos (ISS-S3-01/#40); broker externo; worker separado.

## Capabilities

### New Capabilities
- `rum-ingest`: pipeline completo de ingesta RUM — endpoints con auth, validación por evento (política S1), cola asíncrona con backpressure, persistencia a BD y drenado en shutdown.

### Modified Capabilities
- `openapi`: paths `/telemetry/*`, `security: [apiKey]`, respuestas 401/403/503, descripción del scheme, `application_id` fuera de `required` (D2), 429 sin implementación.
- `ingest-auth`: guard cableado a paths de producción (IAUTH-5); `unknown_application` fuera del flujo (D2).
- `architecture`: `interfaces.md` revierte nomenclatura S1 a `/telemetry/*`; `components.md` y `quality-attributes.md` alinean árbol/mermaid/artefacto.

## Approach

E1 (exploración §4): interfaz `IngestQueue` (enqueue/close/join) + `asyncio.Queue(maxsize)`; validación en request (no en worker); tenant = app de la key, payload sin autoridad (D2); `ServiceUnavailableError` 503 en `exceptions.py`; handler global 422→400 (D5); config `INGEST_QUEUE_MAXSIZE=10000`, `INGEST_WORKERS=2`, chunk 500, retry 3 backoff solo errores transitorios de BD; lifespan crea cola/workers y drena en shutdown (D6); logs con `batch_id`+`index`+`reason` y contadores en proceso (D4). Strict TDD + Schemathesis.

## Affected Areas

| Área | Impacto | Descripción |
|------|--------|-------------|
| `src/api/presentation/routers/telemetry.py` | Nuevo | 2 endpoints con `require_api_key` |
| `src/api/domain/services/ingest_service.py` | Nuevo | validación política, batch_id, encolado |
| `src/api/infrastructure/ingest/queue.py` | Nuevo | interfaz + cola acotada + workers |
| `src/api/domain/{entities,repositories}/` | Nuevo | rum_metric, js_exception, user_session |
| `src/api/presentation/schemas/ingest.py` | Nuevo | Pydantic espejo del contrato |
| `src/api/domain/exceptions.py` | Modificado | subtipo 503 `queue_full` |
| `src/api/config.py`, `src/api/main.py` | Modificado | settings + lifespan |
| `openspec/specs/openapi.yaml` + `architecture/*` | Modificado | nomenclatura, security, descripción |
| `docs/architecture/PipelineIngestaRUM.md`, `ContratoIngestaRUM.md`, `docs/brief-v2.md` | Modificado | rutas nuevas, semántica 202/503 |
| `tests/test_contract.py`, `tests/test_ingest_auth.py` | Modificado | OAS-6/9/10, `_SCOPED_PATH_RE`, wiring |
| `tests/test_ingest_telemetry.py`, `docs/adr/`, `CHANGELOG.md` | Nuevo | tests, ADR pipeline async, registro |

Módulos: seguridad, QA, captura.

## Risks

| Riesgo | Prob. | Mitigación |
|--------|-------|------------|
| Cola sin durabilidad ante reinicios (R5) | Media | Drenado en shutdown (D6) + dead-letter logueada |
| Breaking de contract tests OAS-6/9/10 (R3) | Media | Tests actualizados en el mismo cambio |
| ADR-23 redacción vs nuevos logs | Media | `batch_id`/`index`/`reason`, nunca keys |
| Fragmentación con `--workers>1` (R6) | Baja | Documentar restricción (CMD fijo 1 worker) |
| Registro ADR (R7) | Baja | Nuevo ADR en `docs/adr/` |

## Rollback Plan

- Código: revert del PR (sin migración nueva; DDL de S1 ya existe).
- Contrato: revert diff de openapi.yaml y specs de arquitectura.
- Datos: filas huérfanas de `rum_metric`/`js_exception` no generan deuda (tablas ya en DDL).

## Dependencies

- ISS-S2-01 (DDL, session async) e ISS-S2-02 (guard `require_api_key`, OAS-6).
- Postgres 16 CI; pytest-asyncio; schemathesis.

## Success Criteria

- [ ] Tests TDD: 400 envelope, 202 parcial con `rejected[{index, reason}]` por código, 401/403, 503 `queue_full`, aislamiento IAUTH-2, persistencia verificada en BD.
- [ ] `/telemetry/*` exigen `apiKey` en openapi.yaml; paths viejos ausentes; schemathesis verde.
- [ ] Worker persiste batches (D1); shutdown drena cola (D6); contadores en proceso (D4).
- [ ] Cobertura ≥70%; `pytest` verde; CHANGELOG y ADR actualizados.