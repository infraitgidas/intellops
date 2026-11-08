# Proposal: ISS-S3-03 — Gestión de sesiones (lectura app-scoped de `user_session`)

**Cambio**: ISS-S3-03 (#42). **Owner**: Santiago. **Base**: `main` con ISS-S2-01, ISS-S2-03, ISS-S3-01 e ISS-B-13 mergeados.

## Intent

#42 pide "la gestión de sesiones necesaria para relacionar actividad RUM con aplicaciones y usuarios cuando corresponda". El EDT la detalla con `POST /sessions`, `POST /sessions/{id}/finish` y `GET /sessions[/{id}]`. La implementación avanzó desde entonces:

- La ingesta ya crea la sesión en el primer evento y fija `app_id` desde la API key (ADR-0002, `queue.py:253-263`).
- El contrato del agente no reporta fin de sesión (`ContratoAgenteRUM.md:31`).
- El agente no envía identidad de usuario ni IP (`ContratoAgenteRUM.md` §9).

El cambio se redefine (acordado con Federico) para entregar lo que falta: **leer** las sesiones por aplicación y **dejar escrita** la política de los campos de `user_session` que nadie escribe.

## Scope

### In Scope (RFC 2119)

- MUST: `GET /sessions`, filtrado por la aplicación de la X-API-Key igual que `GET /metrics/query` (ADR-0003). Ventana sobre `start_timestamp` (default 24 h, máximo 7 días) y `limit` 1..500 (default 50).
- MUST: `GET /sessions/{session_id}` filtrando por `session_id` AND `app_id`. Una sesión de otra aplicación responde 404 `session_not_found`, no 403.
- MUST: la respuesta no expone `user_id`, `ip_address`, `os_version`, `end_timestamp` ni `duration_ms`, que en v1 siempre son NULL.
- MUST: ADR-0011 con la política de campos (NULL en la ingesta, nunca desde el payload), la ausencia de POST y el cierre de sesión pospuesto.
- MUST: OpenAPI (paths y schema `Session`), tests de contrato, aislamiento entre tenants, límites, y un test de regresión de los campos NULL de la ingesta.
- SHOULD: `metric_count`, `exception_count` y `last_activity_at` calculados en SQL, para que la lectura tenga valor operativo sin inventar un cierre.

### Out of Scope

- `POST /sessions` y `POST /sessions/{id}/finish`: duplican la creación de la ingesta y rompen el contrato del agente v0.1.
- Cierre por inactividad del lado del servidor (completar `end_timestamp` y `duration_ms`): va en una issue aparte.
- Asociar `lab_user` a sesiones, guardar IP o sistema operativo.
- Cambios en la ingesta, en el agente o en el DDL. Sin migración.
- El límite de ADR-0003 sobre la colisión del mismo `session_id` nuevo entre tenants dentro de un chunk.

## Capabilities

### New Capabilities

- `session-read`: lectura de sesiones por aplicación, con `GET /sessions` y `GET /sessions/{session_id}`.

### Modified Capabilities

- `openapi`: paths `/sessions` y `/sessions/{session_id}` y schema `Session`. El scheme `apiKey` documenta los read paths.

## Approach

Mismo patrón que el read path de métricas (ISS-S3-01):

- Interfaz `SessionRepository` y DTO `SessionSummary` en el dominio.
- `SessionService` valida la ventana y el `limit` antes de consultar y traduce "no encontrada" a 404.
- `SQLAlchemySessionRepository` resuelve todo en una sentencia: acota las sesiones del tenant y después cuenta su actividad con `LATERAL`.
- El router `sessions.py` usa `Depends(require_api_key)`.
- Desarrollo con TDD: tests unitarios del servicio y del schema, de integración con Postgres y de contrato.

## Affected Areas

| Área | Impacto | Descripción |
|------|---------|-------------|
| `domain/repositories/session_repository.py` | Nuevo | Interfaz y DTO `SessionSummary` |
| `domain/services/session_service.py` | Nuevo | Límites, defaults y 404 |
| `infrastructure/db/repositories/sqlalchemy_session_repository.py` | Nuevo | Consulta por tenant con conteos `LATERAL` |
| `presentation/schemas/session.py`, `presentation/routers/sessions.py` | Nuevo | `SessionOut`, `GET /sessions[/{id}]` |
| `main.py` | Modificado | Registro del router |
| `openspec/specs/openapi.yaml` | Modificado | Paths y schema `Session` |
| `tests/test_sessions.py`, `tests/test_contract.py` | Nuevo / modificado | Unitarios, integración y contrato |
| `docs/adr/0011-*`, `docs/architecture/*`, `docs/business/*`, `CHANGELOG.md` | Docs | Documentación actualizada en el mismo PR |

Módulos: captura (lectura de telemetría) y seguridad (aislamiento entre tenants). No toca ML ni dashboard.

## Vínculo con la investigación

La sesión es la unidad de análisis UX-céntrica del proyecto. Exponerla por aplicación habilita, como trabajo posterior, el Health Score por sesión que ADR-0008 dejó sin fuente.

## Recursos

- Sin dependencias nuevas.
- Cada request ejecuta una sola sentencia SQL sobre índices existentes.
- La respuesta tiene como máximo 500 filas, así que el uso de memoria es despreciable frente al límite de 2 GB. CPU-only.

## Rollback

El cambio es aditivo: no hay migración ni cambios en la ingesta. Para revertir alcanza con revertir el PR, que quita los dos endpoints. Ningún otro componente los consume todavía.
