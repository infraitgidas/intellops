# Tasks: ISS-B-14 — Motor determinístico de reglas de umbral

## Review Workload Forecast

Changed lines (estimado): ≈ 1250, de las cuales ≈ 520 son tests, ≈ 520 código de producción con
docstrings (migración, dominio, repositorios, router, motor y scheduler) y el resto contrato, DDL
y documentos. Delivery strategy: work-unit commits por preocupación (esquema → configuración →
motor → contrato), cada uno con sus tests.

Decision needed before apply: No (ADR-0013 resuelve la ubicación del motor y la forma de la regla).
Chained PRs recommended: No.
400-line budget risk: Medium (cuatro slices naturales; el motor y los tests de integración son los
más grandes).

Dependencias: ISS-B-03 (`alert` y read path), ISS-B-13 (`AVAILABILITY`). Lo consumen B.10, C.1 y C.5.

## Fase 0 — Documentos del cambio

- [x] 0.1 `proposal.md`, `spec.md` (DB-RULE-1..2, OAS-B14-1..2, AR-1..6, CT-B14-B10),
      `design.md` y este `tasks.md`.
- [x] 0.2 ADR-0013 e índice de ADRs.

## Fase 1 — Esquema

- [x] 1.1 Migración `0008_alert_rule.py`: tabla `alert_rule`, columnas `rule_id`/`threshold`/
      `observed_value` en `alert`, índices y guarda de downgrade (DB-RULE-1, DB-RULE-2).
- [x] 1.2 Espejo ORM `AlertRule` y columnas nuevas en el espejo `Alert`.
- [x] 1.3 Sincronizar `openspec/specs/database/ddl_v1.0.sql`.
- [x] 1.4 Tests de migración: upgrade, columnas, índices y downgrade con guarda.

## Fase 2 — Configuración de umbrales

- [x] 2.1 Puerto `AlertRuleRepository` y DTOs de dominio.
- [x] 2.2 `AlertRuleService` con la validación semántica y el upsert idempotente.
- [x] 2.3 Repositorio SQLAlchemy.
- [x] 2.4 Schemas y router `POST`/`GET /alerts/config` con `require_role`, registrado en `main.py`.
- [x] 2.5 Contrato OpenAPI: paths y schemas `AlertRule`/`AlertRuleInput`.
- [x] 2.6 Tests unitarios del servicio y de integración del endpoint.

## Fase 3 — Motor de evaluación

- [x] 3.1 `aggregates.py`: agregación por tipo de métrica (AR-2).
- [x] 3.2 `engine.py`: ventana, muestras, comparación inclusiva, cooldown y creación de `ALERT`
      Pending (AR-1, AR-3, AR-4, AR-5, AR-6).
- [x] 3.3 `config.py` y `scheduler.py`, y arranque del worker.
- [x] 3.4 Tests unitarios de las decisiones y de integración de la agregación SQL.

## Fase 4 — Contrato y cierre

- [x] 4.1 Test de contrato CT-B14-B10: la alerta del motor es despachable y visible por `GET /alerts`.
- [x] 4.2 `CHANGELOG.md`, `docs/business/brief-v1.md` y estado de B.14 en el catálogo.
- [x] 4.3 Suite completa, lint y cobertura.
