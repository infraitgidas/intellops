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
- [ ] 5.4 `pytest -m unit`, `flake8 src/ tests/` y `pylint src/ --fail-under=9.0`. La marca anterior era incorrecta: en el CI de la PR, pylint dio **8.95/10** (el gate es 9.0 y develop está en 9.36). Los espejos nuevos `alert.py` y `anomaly.py` solo desactivaban `too-few-public-methods` y sumaban 21 `E1136 unsubscriptable-object`, más un `R0801` entre `AnomalyRecord` y `AnomalyOut`. Corregido en 7.1. Salida local después del fix (Python 3.11.18, `requirements/dev.lock`): `pytest -m unit` 425 passed, `flake8` sin warnings, pylint 9.81/10. Localmente no se reproducen los E1136 ni antes del fix, así que la casilla se marca cuando el job Lint & Format quede en verde en CI.
- [ ] 5.5 Suite completa en el entorno reproducible (`make ci`, Postgres efímero): integración, migraciones, schemathesis y cobertura. En CI quedaron skipped porque el lint falló primero. Pendiente de correrla en una máquina con Docker.

## Fase 6 — Documentación

- [x] 6.1 `CHANGELOG.md`, `brief-v1.md` y `Trazabilidad HU-DER.md`.

## Fase 7 — Review de la PR

- [x] 7.1 Lint: `alert.py` y `anomaly.py` desactivan también `unsubscriptable-object`, como los espejos existentes (`application.py`, `lab_user.py`, `user_role.py`).
- [x] 7.2 DB-ALERT-2: test de la guarda en upgrade. Baja a `0006`, inserta una alerta con forma de 0001 y espera el `RuntimeError` en `upgrade head`, con la DB en `0006`.
- [x] 7.3 RD-1 y RD-3: tests de desempate con tres eventos en el mismo instante (orden por `anomaly_id` / `alert_id` descendente, también con `limit=1`).
- [x] 7.4 RD-4: la spec, el ADR-0012 y el CHANGELOG dejan escrita la excepción de los errores de tipo (`limit=abc`, fecha o UUID mal formados → 422 `{"detail"}` de FastAPI), igual que en `/sessions` y `/metrics/*`. Unificarlo es el follow-up general abierto en ISS-S3-03.
- [x] 7.5 `AlertOut.status` y `channel` pasan a `str` (y sin `enum` en el OpenAPI): sus catálogos no tienen CHECK, y un canal nuevo dejaba `GET /alerts` en 500. `severity` sigue cerrado por `ck_alert_severity`. Test de integración con un canal agregado al catálogo.
- [x] 7.6 OAS-B3-1: test unitario que afirma qué paths incluye y excluye el subset de schemathesis.
- [x] 7.7 Se quita `ALERT_SEVERITIES`: solo lo usaba un test que lo comparaba consigo mismo. El dominio lo cubren `ck_alert_severity` y el `Literal` de `AlertOut`.
- [x] 7.8 Nits: el filtro opcional (`metric_type_id` / `status`) se aplica antes de `order_by`/`limit` en los dos repositorios. `brief-v1.md` marca B.3 como "En revisión" hasta el merge.
- [ ] 7.9 `make ci` en verde sobre estos cambios (ver 5.5).

## Seguimiento (fuera de alcance)

- **B.14**: su migración cuelga de la `0007` (`down_revision = "0007"`) y agrega las columnas de las reglas.
- **B.10**: completa `recipient`, `channel_id`, `status_id` y `sent_at` al despachar. Si hace falta registrar cada envío por separado, la tabla es `alert_delivery` (M3).
- **ISS-S3-03**: cuando se mergee, `session_service` puede usar `read_window` en lugar de sus límites propios. Al hacer rebase, `_SCOPED_PATH_RE`, `main.py`, el OpenAPI y el índice de ADRs (0011 y 0012) se combinan a mano.
- `GET /alerts/{id}` y `/alerts/{id}/ack`: cuando la SPA o B.10 los necesiten.
