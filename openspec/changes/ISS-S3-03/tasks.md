# Tasks: ISS-S3-03 — Gestión de sesiones (lectura app-scoped de `user_session`)

## Review Workload Forecast

Changed lines (medido): ≈ 1580, de las cuales ≈ 425 son código de producción en `src/` (casi todo docstrings), ≈ 555 tests y ≈ 600 contrato OpenAPI y docs. Delivery strategy: single-pr. Supera el presupuesto de 400 líneas, pero el código revisable de producción queda en el orden de ese presupuesto; el resto son tests y documentación que acompañan el cambio.

Decision needed before apply: No (alcance acordado con Federico; ver ADR-0011)
Chained PRs recommended: No
400-line budget risk: Medium

Dependencias: ISS-S2-01 (auth y aplicaciones) e ISS-S2-03 (la ingesta crea `user_session`). Sin dependencias con ML.

## Fase 1 — Infraestructura (dominio)

- [x] 1.1 Crear `src/api/domain/repositories/session_repository.py`: interfaz `SessionRepository` y DTO `SessionSummary` sin campos muertos (SES-4).
- [x] 1.2 RED `tests/test_sessions.py` (unit): límites, defaults, 404 del servicio y forma de `SessionOut` (SES-2, SES-3, SES-4).
- [x] 1.3 Crear `src/api/domain/services/session_service.py`: ventana default 24 h y máximo 7 días, `limit` 1..500 sin recorte silencioso y `NotFoundError(session_not_found)` (SES-2, SES-3).

## Fase 2 — Implementación (persistencia y API)

- [x] 2.1 RED `tests/test_sessions.py` (integration): aislamiento, conteos, `last_activity_at`, ventana, limit, 404 entre tenants, 401/403/422 y sesión creada por la ingesta con columnas NULL (SES-1..SES-6).
- [x] 2.2 Crear `src/api/infrastructure/db/repositories/sqlalchemy_session_repository.py`: subconsulta acotada por tenant más conteos `LATERAL` (DS-5).
- [x] 2.3 Crear `src/api/presentation/schemas/session.py` (`SessionOut`) y `src/api/presentation/routers/sessions.py` (`listSessions` y `getSession` con `require_api_key`).
- [x] 2.4 Registrar el router en `src/api/main.py`.

## Fase 3 — Testing (contrato)

- [x] 3.1 `openspec/specs/openapi.yaml`: paths `/sessions` y `/sessions/{session_id}`, schema `Session` y descripción del scheme `apiKey` (OAS-S303).
- [x] 3.2 `tests/test_contract.py`: contrato de paths, sin escritura, schema sin campos muertos, y `/sessions` dentro del subconjunto de schemathesis.
- [x] 3.3 Suite unitaria y lint en verde: `pytest -m unit`, `flake8 src/ tests/` y `pylint src/ --fail-under=9.0`.
- [x] 3.4 Suite completa en el entorno reproducible (`make test`, Postgres efímero): todo en verde, incluidos los 11 tests de integración de `tests/test_sessions.py`, más 1 xpassed. El xpassed es `test_schemathesis_live_contract_scoped`, un xfail no estricto (OAS-9/ADR-24) que ya pasaba en todas las issues anteriores y ahora también recorre `/sessions*`.

## Fase 4 — Documentación

- [x] 4.1 `docs/adr/0011-sesiones-rum-solo-lectura.md` y su entrada en `docs/adr/README.md`.
- [x] 4.2 `docs/architecture/ContratoAgenteRUM.md` §2.1 y `docs/architecture/PipelineIngestaRUM.md` §3.2: política de campos y lectura.
- [x] 4.3 `docs/business/EDT intellops.md` §3.1: nota de redefinición. `docs/business/issues-s2-s3.md`: criterios de #42. `docs/business/brief-v1.md`: estado de #42.
- [x] 4.4 `CHANGELOG.md`: entrada en Added.
- [ ] 4.5 Actualizar el body de la issue #42 en GitHub con los criterios redefinidos (texto en `docs/business/issues-s2-s3.md`).

## Fase 5 — Review de la PR

- [x] 5.1 Corregir la diferencia que marcó la review (no bloqueante): para `limit` fuera de 1..500, el 422 lo emitía `Query(ge=1, le=500)` de FastAPI con el body `{"detail": [...]}`, y no el `ErrorResponse` con `invalid_query_range` que prometen SES-2, `openapi.yaml` y el CHANGELOG. Se quitó `ge`/`le` del router y el rango lo valida `SessionService`, igual que `bucket_seconds` en `/metrics/query`. El test de integración ahora fija `error.code` y que el mensaje incluya el valor rechazado.
- [ ] 5.2 Volver a correr la suite completa (`make test`) sobre el fix.

## Seguimiento (fuera de alcance)

- `/metrics/probes` conserva el patrón `Query(ge, le)`, con el mismo desfasaje entre lo documentado y la respuesta para `limit`. Conviene alinearlo en una issue aparte.
- Algunos errores de tipo (un `limit` que no es entero, un `start` que no es fecha o un `session_id` que no es UUID) los sigue rechazando FastAPI con `{"detail": [...]}`, aunque los 422 de `openapi.yaml` declaran `ErrorResponse` en todo el documento. Es un desfasaje general del contrato, no de esta issue.

- Issue nueva: cierre de sesiones por inactividad del lado del servidor (completar `end_timestamp` y `duration_ms` y agregarlos al schema `Session` cuando tengan datos).
- Evaluar el índice `(app_id, start_timestamp DESC)` si el volumen del piloto lo justifica.
