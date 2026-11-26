# Changelog — IntellOps

Todas las modificaciones notables de IntellOps se documentan en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es/1.1.0/),
y el proyecto sigue [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-11-18

Primera versión completa del MVP v1 sobre la rama local `MVP1`: agente RUM, ingesta asíncrona,
lectura de métricas y sesiones, sonda de disponibilidad, motor determinístico de umbrales,
despacho por Telegram y mail, SPA de latencias y heatmap, gates de calidad bloqueantes, smoke E2E
reproducible y carga con k6. Detalle funcional y limitaciones conocidas en
`docs/release-notes-v1.0.md`; despliegue y rollback en `docs/operations/deploy-v1.0.md`.

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
  `JsExceptionEvent` (OpenAPI 0..1 y Pydantic), enviado por el agente,
  validado por evento (`invalid_range` si no es finito o sale de 0..1) y
  persistido en `js_exception` (migración 0005 y espejo en `ddl_v1.0.sql`)
  para ponderar el análisis por `1 / sample_rate`.
- Pruebas unitarias de módulos críticos (ISS-S3-06, #45): tests sin Postgres
  para la lógica de negocio (`application_service`, `user_service`,
  `auth_service`) con `FakeSession` y repositorios en memoria, los guards de
  acceso (`get_current_user`, `require_role`, `require_api_key`) y los
  handlers de error, los casos límite de `ingest_policy`,
  `ingest_normalizer` y `query_service`, y la transformación `_build_rows`.
  Cada módulo crítico queda en ≥ 95 % de cobertura unitaria (antes, 24-97 %)
  y el total unitario pasa de 80 % a 89 %. Sin cambios de producción; el bug
  de `is_active` ignorado al crear aplicaciones queda fijado con un test
  `xfail` estricto para corregirlo aparte.
- Lectura de sesiones RUM (ISS-S3-03, #42): endpoints `GET /sessions`
  (`listSessions`) y `GET /sessions/{session_id}` (`getSession`) con
  `require_api_key`. El tenant sale solo de la key y el detalle filtra por
  `session_id` AND `app_id`: una sesión de otra aplicación responde 404
  `session_not_found`, igual que una inexistente. El listado filtra por
  `start_timestamp` en `[start, end)` (default 24 h, máximo 7 días), ordena de
  la más nueva a la más vieja y acota con `limit` 1..500 (default 50). Fuera de
  rango → 422 `invalid_query_range`. Cada sesión trae `metric_count`,
  `exception_count` y `last_activity_at`, calculados en SQL. Sin POST: la
  sesión la sigue creando la ingesta. `user_id`, `ip_address`, `os_version`,
  `end_timestamp` y `duration_ms` quedan NULL y fuera de la respuesta.
  ADR-0011 registra la decisión; sin migración.
- API de lectura de anomalías y alertas (B.3, ISS-B-03, #68): `GET /anomalies`,
  `GET /anomalies/{anomaly_id}` y `GET /alerts` con `Depends(require_api_key)`
  (tenant solo de la key). Ventana `[start, end)` con default de 24 h y máximo
  de 7 días, `limit` 1..500 (default 50) y filtros opcionales `metric_type` y
  `status`; un valor fuera de esos límites responde 422
  `invalid_query_range` con `ErrorResponse` (los errores de tipo, como
  `limit=abc`, siguen con el 422 `{"detail"}` de FastAPI, igual que en
  `/sessions`). El detalle de otra aplicación responde 404
  `anomaly_not_found`, igual que uno inexistente. Las respuestas exponen las
  columnas reales, sin campos muertos y sin `recipient`.
- Migración 0007 (ISS-B-03, ADR-0012): la alerta pasa a ser independiente de
  la anomalía para las reglas de umbral de B.14. Agrega `application_id`,
  `severity` (`ck_alert_severity`) y `created_at`; `anomaly_id`, `recipient` y
  `channel_id` pasan a nullable; índices `idx_alert_app_created` e
  `idx_anomaly_app_timestamp`. Aborta si `alert` tiene filas. Espejo en
  `ddl_v1.0.sql`.
- Motor determinístico de reglas de umbral (ISS-B-14, #74, ADR-0013): la v1
  crea alertas sin detección ML (D1). Migración 0008: tabla `alert_rule`
  (umbral por aplicación y por métrica, comparación `gt`/`lt`, ventana,
  muestras mínimas, cooldown y severidad) y columnas `rule_id`, `threshold`
  y `observed_value` en `alert`. Motor en `intellops-ai-engine`
  (`src/ml/rules/`): agregación en PostgreSQL (p95 para latencias y rage
  clicks, `AVG` para `AVAILABILITY`, razón de excepciones sobre sesiones),
  comparación inclusiva, datos insuficientes sin alerta y cooldown contra
  `alert`. `POST`/`GET /alerts/config` con auth por rol (422
  `invalid_alert_rule`, 404 `application_not_found` y
  `metric_type_not_found`). La imagen del worker pasa a copiar `src/`
  completo: antes arrancaba con `ModuleNotFoundError: ml.rules`.
- Despacho de alertas por Telegram y Email (B.10, ISS-B-10, #72, ADR-0010):
  `intellops-comms` deja de ser un placeholder y pasa a ser el worker que
  consume las alertas `Pending` del motor de reglas. Ciclo propio cada
  `INTELLOPS_COMMS_INTERVAL_SECONDS` (default 30 s) con lote acotado
  (default 20) reclamado con `SELECT ... WHERE status = Pending ORDER BY
  created_at FOR UPDATE SKIP LOCKED LIMIT :batch`; routing por severidad
  configurable por entorno (`critical`/`high` → Telegram, `medium`/`low` →
  Email por defecto, sin WhatsApp en la v1); un destino por canal desde el
  entorno (`INTELLOPS_COMMS_TELEGRAM_CHAT_ID`, `INTELLOPS_COMMS_SMTP_TO`)
  persistido en `alert.recipient`; retry con backoff exponencial (4 intentos,
  1/2/4 s, presupuesto total acotado) donde Telegram 400/403 y SMTP 5xx van a
  `Failed` sin reintento; éxito → `Sent` con `sent_at`, canal y destinatario,
  intentos agotados → `Failed` con `sent_at` NULL. Un canal sin credenciales
  no es un fallo: la alerta queda `Pending`, el canal se loguea una vez y el
  stack levanta sin secretos. Sin dependencias nuevas (`httpx` para Telegram,
  `smtplib`/`email.message` para el correo). La imagen pasa a copiar `src/`
  completo y arranca con `python -m comms.entrypoint` (antes solo empaquetaba
  el `entrypoint.py` del placeholder); `docker-compose.yml` pasa las
  variables con default vacío.

### Changed

- Release v1.0.0 (C.5, ISS-C-05, #80): tag local `v1.0.0` sobre `MVP1` con la verificación de
  despliegue en máquina limpia (`docker compose down -v` + `up -d --build` → `/health` 200 y los
  cuatro servicios arriba), el smoke post-deploy en verde sobre la base recién migrada, la guía de
  despliegue y rollback (`docs/operations/deploy-v1.0.md`) y las notas de release
  (`docs/release-notes-v1.0.md`). `docker-compose.yml` pasa `JWT_SECRET` al core (antes el
  contenedor usaba el default del código y el `.env` del operador no tenía efecto).

- Suite E2E en CI y carga con k6 (C.3, ISS-C-03, #78): job `e2e` bloqueante
  (`needs: lint`, 25 min) que levanta la stack con el perfil `smoke`, intervalos
  de los workers en 5 s, y corre el smoke de C.1 — es el único gate que ve
  build + migraciones + colas + ciclos de los workers, y sube el smoke y los
  logs como artefacto cuando falla. Escenario k6 versionado (`load/ingest.js`)
  con `setup()` que se provisiona solo (login admin → aplicación → API key) y
  los umbrales de la v1: `p(95) ≤ 500 ms` en la ingesta, `http_req_failed <
  1 %` y 100 % de checks (`accepted > 0`), medidos con la imagen oficial
  `grafana/k6` pinneada en la red del compose (`make load`,
  `reports/k6-summary.json`). Carga estándar: 10 VUs, 1 min, lotes de 10
  eventos. Medición local: p95 10.39 ms, 0 % de fallos, 600 iteraciones, los
  tres umbrales en verde. El job `load` del CI corre sólo por
  `workflow_dispatch` (la latencia de un runner compartido no es comparable
  entre corridas) y el runbook aclara qué prueba y qué no el número.

- Integración de punta a punta (C.1, ISS-C-01, #76): `make smoke` recorre el
  flujo completo sobre la stack real en ~10 s — health → login del admin del
  seed → alta de aplicación + API key → ingesta → lectura en
  `/metrics/query` → regla de umbral → alerta → notificación — y falla
  nombrando la etapa, el status y el cuerpo de la respuesta
  (`scripts/smoke.py`, sólo stdlib). La notificación se verifica contra
  `scripts/telegram_stub.py`, un servicio opcional del compose
  (`profiles: ["smoke"]`) que imita `POST /bot<token>/sendMessage` y expone
  `/_messages`: el despacho apunta ahí con
  `INTELLOPS_COMMS_TELEGRAM_API_BASE`, settings nuevo y aditivo (sin la
  variable, la URL es la de siempre). Un stub en el host no servía: el
  firewall de esta máquina dropea el tráfico contenedor→host. Se documenta el
  runbook (`docs/operations/smoke-e2e.md`, con el chequeo de mergeabilidad
  contra `origin/develop`) y el guion de la demo de punta a punta
  (`docs/operations/demo-mvp1.md`). Evidencia: 10/10 etapas verdes, alerta
  `sent` y mensaje `[CRITICAL] TTFB p95 1500,0 ms supera el umbral de 500,0
  ms` en el stub.

- SPA de operación (B.5, ISS-B-05, #69): `src/frontend/` deja de ser
  placeholders y pasa a una app React 19 + TypeScript + Vite con las dos
  vistas de la v1. **Latencias**: selector de métrica (`/metrics/list`),
  ventanas 15 min/1 h/6 h/24 h con bucket 60/60/300/900 s, serie SVG del AVG
  por bucket con `session_count`, resumen y tabla de corridas de la sonda
  (`/metrics/probes`). **Heatmap UX**: grilla tiempo × métrica con una sola
  llamada a `/metrics/query` sin filtro, color normalizado por fila, celda sin
  dato neutra, tooltip y tabla accesible (la API pública no expone `page_url`
  ni `metadata`, así que no es una grilla página × posición). La API key la
  pega el operador y vive sólo en `sessionStorage` (401/403 la descarta): el
  JWT no está cableado a `/metrics/*` y hacerlo es backend nuevo, fuera de
  B.5. Build estático reproducible (`npm ci` + lock, Node ≥ 22) con
  presupuesto de bundle verificado por script: ~243 kB raw / ~75 kB gzip.
  50 tests de componentes (Vitest + Testing Library) y 5 de smoke E2E
  (Playwright sobre el build con un stub de API). Sin librería de gráficos:
  D3 queda para cuando haga falta interacción (desvío de ADR-0009
  documentado).

- Gates de calidad bloqueantes en CI (B.9, ISS-B-09, #71): la suite declara
  `--cov-fail-under=70` en el job (además de `fail_under = 70` en
  `pyproject.toml`), pylint pasa a `--fail-under=9.0 --fail-on=W,E` sin ningún
  `--disable`, el job `contract` corre `tests/test_contract.py` como `needs` de
  `Docker Build` y `make lint` usa el mismo comando que el CI. El árbol quedó
  con 0 warnings y 0 errores de lint sin mensajes desactivados: se corrigió el
  `W0613` real de `GET /metrics/list` (`_application`, catálogo global) en vez
  de desactivar `unused-argument`. `tests/test_ci_gates.py` fija umbral, orden
  de `needs`, `--fail-on`, la paridad de `make lint` y la ausencia de
  `continue-on-error`; `CONTRIBUTING.md` documenta cada gate y cómo
  reproducir su fallo localmente.
- CI (ISS-B-05, #69): job `frontend` bloqueante (`npm ci` → eslint → Vitest →
  build → `check-size` < 1 MB → Chromium + smoke E2E), fijado por
  `tests/test_ci_gates.py`; `make fe-install/fe-lint/fe-test/fe-build/fe-e2e`
  para correr lo mismo en local.
- Imports `src.ml.*` → `ml.*` (ISS-B-09, #71): `src/ml/` y los tests cargaban
  el mismo archivo como dos módulos distintos (`src.ml.schemas` y
  `ml.schemas` → dos clases `MetricBatchInput`), lo que rompía `isinstance`
  entre el loader del dataset y sus tests y no resolvía con el
  `PYTHONPATH=/app/src` de las imágenes.

- Contrato OpenAPI de `Anomaly` y `Alert` (ISS-B-03, #68): se reemplazan los
  campos del borrador (`score`, `detector`, `description`,
  `metrics_snapshot`) por las columnas reales de las tablas, y el path
  `/anomalies/{id}` pasa a `/anomalies/{anomaly_id}`.
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
- Las filas de la sonda HTTP (`metadata` con `probe_target`) dejan de mezclarse
  con la latencia real de usuarios (ISS-B-14, ISS-B-05): el p95 del motor de
  reglas (`src/ml/rules/aggregates.py`) y `GET /metrics/query` las excluyen en
  todos los tipos de métrica salvo `AVAILABILITY`, que proviene únicamente de
  la sonda. El contrato de `/metrics/query` (parámetros, shape y orden) no
  cambia; una fila sin `metadata` sigue contando como RUM.

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

[Unreleased]: https://github.com/gidas/intellops/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/gidas/intellops/releases/tag/v1.0.0
[0.0.0]: https://github.com/gidas/intellops/releases/tag/v0.0.0
