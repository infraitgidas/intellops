# Proposal: ISS-B-03 — API de lectura de series, anomalías y alertas

**Cambio**: B.3 (#68). **Owner**: Santiago. **Base**: `develop` (`0faaf1d`). **Depende de**: ISS-S3-01 (read path de métricas), A.2.
**Lo consumen**: B.5 (SPA, contrato), B.10 (dispatcher de notificaciones) y B.14 (reglas de umbral).

## Intent

B.3 pide exponer la API de lectura app-scoped para series de métricas, anomalías y alertas, con contrato OpenAPI y ventanas y paginación acotadas.

Las **series** ya están: `GET /metrics/query`, `/metrics/list` (ISS-S3-01) y `/metrics/probes` (B.13) son app-scoped y tienen la ventana acotada. Lo que falta es `/anomalies` y `/alerts`: en el contrato son stubs que solo declaran el `200`, sin router.

Al definir la lectura de alertas aparece un problema de esquema. En la v1 las alertas las crea el motor de reglas de umbral (B.14), sin detección ML (D1). Pero la tabla `alert` exige `anomaly_id` NOT NULL, y una anomalía exige un `ml_model`. Además, `alert` no tiene tenant, ni severidad, ni momento de creación. B.3 define el contrato de lectura que consumen B.10 y B.14, así que la forma de la tabla se resuelve acá (ADR-0012).

## Scope

### In Scope (RFC 2119)

- MUST: `GET /anomalies`, `GET /anomalies/{anomaly_id}` y `GET /alerts` con `Depends(require_api_key)`. El tenant se deriva exclusivamente de la key (ADR-0003).
- MUST: el detalle filtra por `anomaly_id` AND `application_id`; una anomalía de otro tenant da 404, igual que una inexistente.
- MUST: ventana `[start, end)` (default 24 h, máximo 7 días) y `limit` 1..500 (default 50), validados en el servicio con 422 `invalid_query_range` y contrato `ErrorResponse`.
- MUST: migración `0007` sobre `alert` vacía: `application_id`, `severity` y `created_at`; `anomaly_id`, `recipient` y `channel_id` nullable; índices del read path.
- MUST: schemas `Anomaly` y `Alert` del OpenAPI con las columnas reales, sin campos muertos y sin `recipient`.
- MUST: tests unitarios, de integración, de migración y de contrato.
- SHOULD: filtros opcionales `metric_type` (anomalías) y `status` (alertas).

### Out of Scope

- `/alerts/config`: la configuración de umbrales es de B.14.
- `/alerts/{id}/ack`, `/predictions*` y `/dashboard/*`.
- `GET /alerts/{id}`: el contrato no lo tiene.
- Escritura de anomalías (M3) y de alertas (B.14), y despacho (B.10).
- Columnas propias de las reglas (umbral, valor observado): las agrega B.14 con una migración que cuelga de la `0007`.

## Capabilities

- **Nuevas**: `anomalies-read`, `alerts-read`.
- **Modificadas**: `database` (forma de `alert`), `contract` (paths y schemas de anomalías y alertas).

## Approach

Mismo patrón que `/metrics/*`: router con `require_api_key`, servicio que valida límites antes de tocar la base y repositorio SQLAlchemy con una sola sentencia acotada por tenant, ventana y `limit`. Los límites de ventana y `limit` viven en un helper compartido (`read_window`) para no duplicarlos entre los dos servicios.

## Affected Areas

| Área | Impacto | Descripción |
|------|---------|-------------|
| `src/api/infrastructure/db/migrations/versions/0007_alert_standalone.py` | Nuevo | Forma de `alert` e índices del read path |
| `src/api/domain/entities/{anomaly,alert}.py` | Nuevo | Espejo ORM de las tablas |
| `src/api/domain/repositories/{anomaly,alert}_repository.py` | Nuevo | Puertos de lectura y DTOs |
| `src/api/domain/services/{read_window,anomaly_service,alert_service}.py` | Nuevo | Límites y casos de uso |
| `src/api/infrastructure/db/repositories/sqlalchemy_{anomaly,alert}_repository.py` | Nuevo | Consultas |
| `src/api/presentation/{schemas,routers}/{anomaly,alert}*.py`, `main.py` | Nuevo / Modificado | Endpoints |
| `openspec/specs/openapi.yaml`, `openspec/specs/database/ddl_v1.0.sql` | Modificado | Contrato y DDL |
| `tests/` | Nuevo / Modificado | Unit, integración, migración y contrato |
| `docs/adr/0012-*.md`, docs de negocio, `CHANGELOG.md` | Docs | Decisión y trazabilidad |

## Vínculo con la investigación

La lectura de alertas es el último tramo antes de la alerta por Telegram que exige M2. La de anomalías deja listo el contrato que va a usar la detección ML de M3, anclada a la serie como define ADR-0008.

## Recursos

Sin dependencias nuevas. Consultas acotadas a 500 filas sobre índices compuestos; CPU-only.

## Rollback

Revertir el PR y bajar la migración a `0006`. El downgrade de la `0007` solo corre con `alert` vacía, que es el estado esperado hasta que B.14 escriba alertas.
