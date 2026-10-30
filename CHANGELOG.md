# Changelog — IntellOps

Todas las modificaciones notables de IntellOps se documentan en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es/1.1.0/),
y el proyecto sigue [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Estructura SDD: `openspec/config.yaml`, `openspec/specs/`, `openspec/changes/` (#1)
- Team Charter: valores, roles, acuerdos de trabajo (#1)
- Guía de contribución (`CONTRIBUTING.md`) con flujo SDD (#1)
- Código de Conducta (`CODE_OF_CONDUCT.md`) (#1)
- Onboarding guide (`onboarding/README.md`) (#1)
- Brief v2.0 del proyecto (`docs/brief-v2.md`) (#1)
- Architecture Decision Records structure (`docs/adr/`) (#1)
- Research notes structure (`docs/research/`) (#1)
- Divulgation notes structure (`docs/divulgation/`) (#1)
- Governance directory (`governance/`) (#1)
- `.gitignore` base para Python + Node + Docker (#1)
- Credenciales de ingesta por aplicación (ISS-S2-02, #36): emisión/revocación
  de API key `ilp_` (show-once, hash SHA-256 persistido), guard reutilizable
  `require_api_key` (401 `invalid_api_key` + `WWW-Authenticate`, 403
  `app_inactive`), `is_active` en aplicaciones (migración 0003) y redacción
  global de API keys en logs (ApiKeyRedactionFilter).
- Ingesta RUM asíncrona (ISS-S2-03, #37): endpoints `POST /telemetry/metrics`
  y `POST /telemetry/exceptions` con `Depends(require_api_key)` (IAUTH-5),
  validación de dos niveles (envelope→400 `schema_validation_error` por
  handler 422→400 scoped a `/telemetry/*`; evento→202 parcial con
  `rejected[{index, reason}]`), cola en proceso acotada (`asyncio.Queue`
  maxsize 10000) con workers que persisten en chunks de 500 a
  `rum_metric`/`js_exception`/`user_session` (retry transitorio 3 con
  backoff 0.5/1/2s y dead-letter logueada), backpressure 503 `queue_full`,
  drenado en shutdown con timeout, contadores en proceso `ingest.*` (D4) y
  tenant fijado desde la key (`application_id` fuera de required, D2/IAUTH-2).
  Nomenclatura definitiva `/telemetry/*` (reemplaza `/metrics/ingest` y
  `/logs/ingest`); ADR-0002 registra la decisión.
- Pipeline de QA inicial (ISS-S2-04, #38): capas de test `unit` (sin DB) e
  `integration` (Postgres) con markers asignados automáticamente en
  `tests/conftest.py`; job `Unit Tests` sin Postgres entre lint y la suite
  completa; reporte de cobertura publicado en el Job Summary y como artefacto
  `coverage-report` (xml, html, junit); targets `make test-unit` y
  `make test-integration`.
- Entorno reproducible de testing (ISS-S2-05, #39): `requirements/dev.lock`
  (dependencias runtime + dev fijadas con hashes, generado con `make lock`),
  imagen `Dockerfile.test` y `docker-compose.test.yml` con Postgres efímero
  aislado del stack de dev; `scripts/ci-tests.sh` reproduce el pipeline del CI
  (`make ci`); `make test-contract` y `make test-down`; job de CI
  `Reproducible Test Env (Docker)` que corre `make ci` y verifica que el lock
  esté al día con `pyproject.toml`; `.dockerignore` para el contexto de build.
- Hardening de aislamiento multi-tenant + read path (ISS-S3-01, #40):
  ownership de sesión en el upsert (`_upsert_sessions` resuelve por PK antes
  del insert; sesión de OTRA app → filas del lote descartadas +
  `ingest.session_foreign_total`), correlación `metric_id` scoped por tenant
  (cross-app → `NULL` + `ingest.metric_id_foreign_total`; inexistente →
  `metric_id_unknown_total`), endpoints `GET /metrics/query` (`queryMetrics`)
  y `GET /metrics/list` (`listMetrics`) con `require_api_key` (tenant solo de
  la key), query repository app-scoped con agregación temporal EN SQL
  (shape ML `(application_id, metric_type_id, timestamp, value,
  session_count)`, ventana default 15 min / ≤ 7 d / bucket ≥ 60 s → 422
  `invalid_query_range`), contrato OpenAPI 124-137 completado sin romper
  operationIds, y tests de collision/replay cross-tenant (C5). ADR-0003
  registra la decisión (DD-8/DD-9/DD-10).
- Normalización de datos de ingesta (ISS-S3-02, #41): etapa de normalización
  pura y con nombre (`ingest_normalizer`) que corre por evento **antes** de la
  validación (`Raw → Normalize → Validate → Enqueue → Store`); canonicaliza
  timestamps a UTC con tz (el `timestamp` de la métrica hereda el del envelope),
  convierte alias de unidad (`s`/`sec`/`secs`/`msec`/`millis` → `ms`,
  `counts` → `count`) de forma idempotente, canonicaliza nombres de tipo y
  `error_type` (desconocido → `Other`, sin DDL/migración), coacciona cadenas
  numéricas finitas y **nunca** recorta magnitudes (el TTFB de 9000 ms es la
  señal de anomalía). La validación sigue siendo la autoridad única de rechazo;
  se rechazan conteos no enteros y valores no finitos (`invalid_range`). El
  worker deja de reescribir timestamps con `now()` y de re-coaccionar el valor.
  Registros compartidos en `ingest_policy`; enum `RumMetric.unit` de OpenAPI
  ampliado a la familia de alias (ARCH-6); ADR-0004..0007.
- Validación por evento de `schema_version` (B.15, ISS-B-15, #75): un evento
  con versión distinta de `1.0` se rechaza con el nuevo código
  `invalid_schema_version` (octavo) en `ingest_policy`, sin romper el 202
  parcial ni rechazar el batch completo.
- `sample_rate` en excepciones JS (B.15, ISS-B-15, #75): campo opcional en
  `JsExceptionEvent` (OpenAPI 0..1 y Pydantic), enviado por el agente y
  persistido en `js_exception` (migración 0005 y espejo en `ddl_v1.0.sql`)
  para ponderar el análisis por `1 / sample_rate`.

### Changed
- CI (ISS-S2-04, #38): pylint `--fail-under` sube de 7.0 a 9.0; gate de
  cobertura único (70%) en `pyproject.toml` con `source = ["src"]`; cache de
  pip, `concurrency` con cancelación, timeouts y `workflow_dispatch`.
- Tests (ISS-S2-05, #39): `make test`, `make test-unit`, `make test-integration`,
  `make test-cov` y `make lint` corren en el entorno de testing en vez del
  contenedor de dev (antes truncaban la DB de desarrollo y fallaban por falta
  de `schemathesis` en la imagen); los jobs del CI instalan desde el lock.
- CI (ISS-S2-04, #38): se quita el envío a Codecov (no había `CODECOV_TOKEN`
  configurado y fallaba en silencio); se reincorporará en una issue aparte.
- Migración de GitLab a GitHub como plataforma principal de control de versiones (#1)
- Reemplazo de ELK Stack por Grafana + Loki + Prometheus en Módulo de Seguridad y stack general (#2)
  - Ver ADR-0001 para justificación completa (licencias SSPL, footprint de recursos, unificación de stack)
- ADR-16 materializado (ISS-S2-02, #36): `api_token_hash` se retira de
  `ApplicationRead` (Pydantic + OpenAPI) — el hash es dato interno y no viaja
  en respuestas; `ApplicationRead` ahora expone `is_active`.
- Contract testing con schemathesis (OpenAPI 3.1) como gate de CI (OAS-9).
- Agente RUM de navegador (B.1, ISS-B-01, #67): `src/agent/` implementa el
  contrato A.3 v0.1 — TTFB (`responseStart - requestStart`), FCP
  (`first-contentful-paint`) y excepciones no manejadas (`onerror`,
  `unhandledrejection`) en `POST /telemetry/metrics` y
  `POST /telemetry/exceptions`; sesión opaca en `sessionStorage` con rotación
  30 min/24 h, muestreo determinista por sesión, batching con caps de 400
  eventos y 32 KiB, `fetch` con `keepalive` y `X-API-Key` (sin `sendBeacon`),
  reintentos 1 s/2 s con backoff y circuito abierto ante 401/403; privacidad
  por diseño (URL sin query, redacción de PII, DNT/GPC y opt-out). Bundle
  IIFE minificado de 4.3 KB gzip (tope 30 KB), sin dependencias de runtime.
  78 tests con `node --test`, demo HTML y verificación E2E contra la ingesta.
- Contrato RUM alineado con la implementación (B.15, ISS-B-15, #75): se retiran
  `viewport` y `connection` del OpenAPI de `RumEvent.metadata` y el `429` de
  `/telemetry/*` hasta implementar el rate limit (el de `/assistant/query` se
  mantiene); se corrige la redacción de secretos al inicio del texto
  (`SECRET_PAIR_RE`, `28181c2`).

### Security

- Estructura de compliance y SBOM en `governance/` (#1)
- Rotación de API keys explícita en dos pasos: POST con key activa → 409;
  DELETE revoca fail-closed de inmediato (CRED-3/CRED-4, ISS-S2-02).
- Validación de API keys timing-safe: gate de prefijo `ilp_` → lookup
  indexado SHA-256 → `hmac.compare_digest` (IAUTH-3, ADR-19).

---

## [0.0.0] - 2026-05-27

### Added

- Inicialización del proyecto IntellOps en GitHub
- Brief técnico-científico v1.0 (`docs/brief.md`)
- Documentación de RRHH con planes de trabajo de estudiantes PS
- Definición de módulos: Seguridad (Cavallero), ML (Monfroglio), QA (Montanari)

[Unreleased]: https://github.com/gidas/intellops/compare/v0.0.0...HEAD
[0.0.0]: https://github.com/gidas/intellops/releases/tag/v0.0.0
