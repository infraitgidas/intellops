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

### Changed

- Migración de GitLab a GitHub como plataforma principal de control de versiones (#1)
- Reemplazo de ELK Stack por Grafana + Loki + Prometheus en Módulo de Seguridad y stack general (#2)
  - Ver ADR-0001 para justificación completa (licencias SSPL, footprint de recursos, unificación de stack)
- ADR-16 materializado (ISS-S2-02, #36): `api_token_hash` se retira de
  `ApplicationRead` (Pydantic + OpenAPI) — el hash es dato interno y no viaja
  en respuestas; `ApplicationRead` ahora expone `is_active`.
- Contract testing con schemathesis (OpenAPI 3.1) como gate de CI (OAS-9).

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
