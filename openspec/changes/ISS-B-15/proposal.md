# Proposal: ISS-B-15 — Alineación del contrato RUM v0.1 con la implementación

**Cambio**: ISS-B-15 / B.15 (#75). **Base**: `feat/ISS-B-15`. **Depende de**: A.3 — Contrato del agente RUM v0.1 (`docs/architecture/ContratoAgenteRUM.md` §13–§14) e ISS-B-01 (#67).

## Intent

Al cerrar A.3 quedaron cuatro correcciones de seguimiento (OD-03, OD-04/D-02, D-03, D-04) que hoy mantienen divergentes el contrato normativo y el código. Esta tarea las ejecuta para que la implementación quede alineada con el contrato v0.1, e incluye la corrección de redacción de secretos detectada en la revisión posterior al merge de B.1.

## Scope

### In Scope

- **OD-03**: `sample_rate` opcional en `JsExceptionEvent`, enviado por el agente y **persistido** en `js_exception` (columna nullable, entidad, repositorio, cola y migración).
- **OD-04/D-02**: validación por evento de `schema_version` con `^1\.0$` en `ingest_policy`, con el nuevo código `invalid_schema_version`; nunca como `Field(pattern=...)` (rompería el 202 parcial).
- **D-03**: quitar `viewport` y `connection` del OpenAPI de `RumEvent.metadata` porque el ingest no los persiste.
- **D-04**: quitar `429` de `/telemetry/metrics` y `/telemetry/exceptions` hasta implementar el rate limit; el `429` de `/assistant/query` se mantiene.
- **Redacción de secretos**: `SECRET_PAIR_RE` con `(^|[?&;,\s])`, ya commiteado en `28181c2`.
- Actualización de tests de contrato, política de ingesta, agente y estado §13/§14 del contrato.

### Out of Scope

- `page_url` y `agent_version` en `JsExceptionEvent` (diferidos por OD-03).
- Rate limit real (OD-06).
- Tests del agente en CI: quedan locales por decisión del owner.
- Cambios en `.github/workflows/ci.yml`.

## Approach

Las correcciones de contrato son cambios acotados en `openapi.yaml`, `interfaces.md` y los documentos de ingesta. La validación de `schema_version` vive en la política pura (`ingest_policy.py`) para conservar el rechazo por evento y la respuesta 202 parcial. `sample_rate` sigue el camino ya usado por `metrics[].metadata`: agente → cola → repositorio → DDL, con columna nullable para no romper filas existentes y mantener opcional el campo.

## Affected Areas

| Área | Impacto | Descripción |
|------|--------|-------------|
| `openspec/specs/openapi.yaml`, `openspec/specs/architecture/interfaces.md` | Modificado | sin `429` de telemetría, sin `viewport`/`connection`, con `sample_rate` |
| `src/api/domain/services/ingest_policy.py` | Modificado | octavo código de rechazo y validación de versión por evento |
| `src/api/` (schemas, entidades, repos, cola, migración) | Modificado | `sample_rate` de extremo a extremo |
| `src/agent/src/index.js` | Modificado | `sample_rate` en el payload de excepciones |
| `docs/architecture/` | Modificado | estado de §13/§14 y códigos de rechazo |
| `CHANGELOG.md` | Modificado | registro del cambio |

## Risks

| Riesgo | Mitigación |
|--------|-----------|
| `Field(pattern=...)` en el modelo de evento convierte un evento inválido en 400 de batch | La validación vive solo en `ingest_policy`; test HTTP de 202 parcial |
| Declarar `sample_rate` sin persistirlo repite el defecto de D-03 | Columna, entidad, repositorio y cola en el mismo cambio |
| Migración sobre filas existentes | Columna nullable, sin backfill ni cambio de `required` |

## Rollback

Revertir el PR es aditivo en su mayoría; la migración `0005` baja con `DROP COLUMN sample_rate`. El `429` y los campos de metadata retirados pueden reincorporarse si se implementa el rate limit o la persistencia correspondiente.
