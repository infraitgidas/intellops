# Tasks: ISS-B-03 — API de lectura de series, anomalías y alertas

## Review Workload Forecast

Changed lines (medido): ≈ 2700, de las cuales ≈ 1110 son tests, ≈ 960 código de producción con docstrings (migración, dominio, repositorios, routers) y el resto contrato, DDL y documentos. Delivery strategy: single-pr, un commit por archivo.

Decision needed before apply: No (esquema de `alert` acordado con el equipo; ver ADR-0012).
Chained PRs recommended: No.
400-line budget risk: Medium (los endpoints son simétricos y cada archivo se revisa por separado).

Dependencias: ISS-S3-01 (read path) y A.2. Lo consumen B.5, B.10 y B.14.

## Fase 0 — Documentos del cambio

- [x] 0.1 `proposal.md`, `spec.md` (RD-1..RD-5, DB-ALERT-1..3, OAS-B3-1), `design.md` y este `tasks.md`.
- [x] 0.2 ADR-0012 e índice de ADRs.

## Fase 1 — Esquema

- [x] 1.1 Migración `0007_alert_standalone.py` con la guarda de tabla vacía (DB-ALERT-1, DB-ALERT-2).
- [x] 1.2 `ddl_v1.0.sql` sincronizado (DB-ALERT-3).
- [x] 1.3 Entidades `Anomaly` y `Alert`.

## Fase 2 — Dominio

- [x] 2.1 Puertos y DTOs `anomaly_repository.py` y `alert_repository.py`.
- [x] 2.2 `read_window.py`: ventana y `limit` compartidos (RD-4).
- [x] 2.3 `AnomalyService` (RD-1, RD-2) y `AlertService` (RD-3, RD-4).

## Fase 3 — Infraestructura y presentación

- [x] 3.1 Repositorios SQLAlchemy de anomalías y alertas.
- [x] 3.2 Schemas `AnomalyOut` y `AlertOut`.
- [x] 3.3 Routers `anomalies.py` y `alerts.py` y su registro en `main.py` (RD-5).

## Fase 4 — Contrato

- [x] 4.1 `openapi.yaml`: paths, parámetros, respuestas y schemas `Anomaly` y `Alert` (OAS-B3-1).

## Fase 5 — Tests

- [x] 5.1 `test_read_window.py`, `test_anomalies.py` y `test_alerts.py`.
- [x] 5.2 `test_migrations.py`: tests de la `0007` y `REV_HEAD`.
- [x] 5.3 `test_contract.py`: tests de B.3 y `_SCOPED_PATH_RE`.
- [x] 5.4 `pytest -m unit`, `flake8 src/ tests/` y `pylint src/` en verde.
- [ ] 5.5 Suite completa en el entorno reproducible (`make test-cov`, Postgres efímero): integración, migraciones y schemathesis. Pendiente de correrla en una máquina con Docker.

## Fase 6 — Documentación

- [x] 6.1 `CHANGELOG.md`, `brief-v1.md` y `Trazabilidad HU-DER.md`.

## Seguimiento (fuera de alcance)

- **B.14**: su migración cuelga de la `0007` (`down_revision = "0007"`) y agrega las columnas de las reglas.
- **B.10**: completa `recipient`, `channel_id`, `status_id` y `sent_at` al despachar. Si hace falta registrar cada envío por separado, la tabla es `alert_delivery` (M3).
- **ISS-S3-03**: cuando se mergee, `session_service` puede usar `read_window` en lugar de sus límites propios. Al hacer rebase, `_SCOPED_PATH_RE`, `main.py`, el OpenAPI y el índice de ADRs (0011 y 0012) se combinan a mano.
- `GET /alerts/{id}` y `/alerts/{id}/ack`: cuando la SPA o B.10 los necesiten.
