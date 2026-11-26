# Proposal: ISS-B-14 — Motor determinístico de reglas de umbral

**Cambio**: B.14 (#74). **Base**: `develop` + ISS-B-03 (`0007`) + ISS-B-13 (sonda).
**Depende de**: B.3 (tabla `alert` y API de lectura), B.13 (`AVAILABILITY` en `metric_type`).
**Lo consumen**: B.10 (despacho de la alerta), C.1 (E2E) y C.5 (release).

## Intent

D1 movió la detección ML a M3, pero M2 exige una alerta real por Telegram. La v1 necesita un
motor determinístico que evalúe umbrales sobre las métricas RUM y la disponibilidad de la sonda,
y cree `ALERT` en estado Pending con severidad y mensaje. Sustituye en la v1 al motor basado en
score ML (B.11), que pasa a M3 con la detección.

Hoy no existe ni la configuración de umbrales ni el motor. `/alerts/config` es un stub del
contrato sin esquema ni router, la tabla `alert_rule` no existe y nada escribe alertas: la tabla
`alert` está vacía en todos los entornos. ADR-0012 §3 y §6 reservan explícitamente para B.14 el
umbral, el valor observado, el id de la regla y `/alerts/config`.

## Scope

### In Scope (RFC 2119)

- MUST: tabla `alert_rule` con umbrales por aplicación y por métrica, y migración `0008` que
  cuelga de la `0007` (`down_revision = "0007"`, sin segundo head).
- MUST: `alert` gana `rule_id`, `threshold` y `observed_value` (nullable: las alertas de ML de
  M3 no tienen regla).
- MUST: motor que evalúa cada regla activa sobre `[now - window_minutes, now)` y crea `ALERT` en
  Pending con severidad, mensaje, umbral y valor observado.
- MUST: comparación inclusiva — `gt` dispara con `observado >= umbral`, `lt` con `observado <= umbral`.
- MUST: datos insuficientes (muestras < `min_samples`) no crean alerta ni fallan el ciclo.
- MUST: cooldown por regla para no repetir alertas.
- MUST: `POST /alerts/config` y `GET /alerts/config` con auth por rol (JWT), validación de
  umbral, ventana, muestras mínimas, cooldown y severidad, con `ErrorResponse`.
- MUST: tests de reglas, de los casos borde de S4, de migración y de contrato con B.10.
- SHOULD: el ciclo registra cuántas reglas evaluó, disparó, omitió por cooldown y por datos
  insuficientes.

### Out of Scope

- Despacho a mail/Telegram y transición a Sent/Failed: es B.10.
- Detección ML y alertas con `anomaly_id`: M3 (B.11).
- `/alerts/{id}/ack`: sin issue en la v1.
- Notificaciones por WhatsApp: fuera del catálogo de canales de la v1.

## Capabilities

- **Nuevas**: `alert-rules` (configuración), `alert-engine` (evaluación periódica).
- **Modificadas**: `database` (tabla `alert_rule` y columnas de regla en `alert`), `contract`
  (paths `/alerts/config` y schemas `AlertRule`/`AlertRuleInput`).

## Approach

Tres piezas con límites claros (ADR-0013):

1. **Configuración**: tabla `alert_rule` + endpoints `POST`/`GET /alerts/config` en
   `intellops-core` con `require_role`, siguiendo el patrón de `/applications`.
2. **Evaluación**: `RulesEngine` en `intellops-ai-engine` (ADR-0010: "lee RUM_METRIC ... escribe
   ALERT en estado Pending"), con un ciclo periódico propio y una sentencia de agregación por
   regla calculada en PostgreSQL (p95 con `percentile_cont`, razón de excepciones y uptime con
   `AVG`), para no traer muestras crudas al proceso.
3. **Contrato**: la alerta creada es la misma fila que consumen `GET /alerts` (B.3) y el
   dispatcher (B.10); el test de contrato fija esa forma.

## Affected Areas

| Área | Impacto | Descripción |
|------|---------|-------------|
| `src/api/infrastructure/db/migrations/versions/0008_alert_rule.py` | Nuevo | `alert_rule` + columnas de regla en `alert` |
| `src/api/domain/entities/alert_rule.py`, `entities/alert.py` | Nuevo / Modificado | Espejo ORM |
| `src/api/domain/repositories/alert_rule_repository.py` | Nuevo | Puerto de configuración |
| `src/api/domain/services/alert_rule_service.py` | Nuevo | Validación de la regla |
| `src/api/infrastructure/db/repositories/sqlalchemy_alert_rule_repository.py` | Nuevo | CRUD acotado por tenant |
| `src/api/presentation/{schemas,routers}/alert_rule.py`, `main.py` | Nuevo / Modificado | Endpoints |
| `src/ml/rules/{engine,aggregates,scheduler,config}.py` | Nuevo | Motor y ciclo |
| `openspec/specs/openapi.yaml`, `openspec/specs/database/ddl_v1.0.sql` | Modificado | Contrato y DDL |
| `tests/` | Nuevo / Modificado | Unit, integración, migración y contrato |
| `docs/adr/0013-*.md`, `CHANGELOG.md`, `docs/business/brief-v1.md` | Docs | Decisión y trazabilidad |

## Vínculo con la investigación

Es el eslabón que convierte la telemetría en una acción observable y medible: habilita la alerta
por Telegram de M2 y el cálculo de falsos positivos de C.4 con datos reales del piloto.

## Recursos

Sin dependencias nuevas. Una consulta de agregación por regla activa por ciclo; `percentile_cont`
sobre el índice `(application_id, metric_type_id, timestamp)` ya existente.

## Rollback

Revertir el PR y bajar la migración a `0007`. El downgrade de la `0008` solo corre si `alert` no
tiene filas con `rule_id` (las alertas de umbral), porque sus `rule_id`/`threshold`/
`observed_value` no se pueden derivar.
