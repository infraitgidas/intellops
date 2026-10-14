# Tasks: ISS-S3-04 — Dataset operativo para ML (M4)

> Fuentes: `proposal.md`, `design.md`, `specs/{ml-operational-dataset,database,architecture}/spec.md`.
> Modo: strict TDD (RED -> GREEN -> REFACTOR por tarea). Runner: `pytest` (markers `unit` / `integration`, gate de cobertura >= 70%).

## Review Workload Forecast

| Campo | Valor |
|---|---|
| Líneas cambiadas estimadas | ~750 |
| Estrategia de entrega | `single-pr` con label `size:exception` (decisión del usuario) |
| Chained PRs recommended | No (excepción explícita) |
| 400-line budget risk | High (aceptado vía `size:exception`) |
| Decision needed before apply | No (resuelta) |
| Commits | 3 work units atómicos, ordenados, cada uno con su verificación y rollback por `git revert` |

Reparto: commit 1 ~120, commit 2 ~250, commit 3 ~380.

## Reglas transversales

- Conventional commits, sin co-author ni atribución IA. Scope estilo repo: `feat(ml): ... (ISS-S3-04)`.
- Python 3.11 compatible (CI usa 3.11): sin sintaxis 3.12+ (`type` statements, f-strings anidadas con comillas iguales, `typing.override`).
- Vedados (PR #59): `CHANGELOG.md`, `openapi.yaml`, `src/api/.../queue.py`, ADR 0004-0007. Único archivo nuevo bajo `src/api`: la migración `0004` (DB-SCOPE-1).
- Sin cross-imports `src/ml` <-> `src/api` (MLD-3.2, ARCH-AI-3.2).
- No regenerar `ml/data/rum_mock.json` (dominio #44).

---

## Commit 1 — `feat(ml): contrato M4 sin metric_id y con bucket_seconds (ISS-S3-04)`

Specs: MLD-1.1, MLD-1.2, MLD-1.3.

- [x] **1.1 RED**: en `tests/test_ml_worker.py` (marker `unit`) agregar tests: registro válido sin `metric_id` (MLD-1.1); falta `bucket_seconds` falla (MLD-1.2); `metric_id` presente falla por `extra="forbid"`; `timestamp` naive falla; `epoch(timestamp) % bucket_seconds != 0` falla; `bucket_seconds < 60` falla; `mock_data.json` y salida del generador validan sin `metric_id` (MLD-1.3). Ajustar los tests existentes que usan `metric_id`.
- [x] **1.2 GREEN** `src/ml/schemas.py`: `MetricBatchInput` con `ConfigDict(extra="forbid", frozen=True)`, sin `metric_id`, con `bucket_seconds: int = Field(ge=60)`, `timestamp: AwareDatetime`, `model_validator` de alineación a epoch.
- [x] **1.3 GREEN** `src/ml/mock_data.json`: quitar `metric_id`, agregar `bucket_seconds: 60`, 2.º registro a `21:15:00Z` (alineado).
- [x] **1.4 GREEN** `ml/data/generate_mock_dataset.py`: `metric_id` -> `bucket_seconds: 60`; actualizar docstring; quitar `import uuid` si queda sin uso (flake8 F401 no corre en `ml/`, pero mantenerlo limpio).
- [x] **1.5** `docs/architecture/IsolationForest/ContratoEntradaSalida.md`: entrada/salida M4 (sin `metric_id`, con `bucket_seconds`, identidad de serie).
- [x] **1.6 REFACTOR**: revisar que `mock_reader.py` y `src/ml/main.py` no referencien `metric_id` (`rg metric_id src/ml ml/data`).

Archivos: `src/ml/schemas.py`, `src/ml/mock_data.json`, `ml/data/generate_mock_dataset.py`, `docs/architecture/IsolationForest/ContratoEntradaSalida.md`, `tests/test_ml_worker.py`.

Verificación:
```
PYTHONPATH=. pytest tests/test_ml_worker.py -m unit
flake8 src/ tests/
```

---

## Commit 2 — `feat(db): migración 0004 ancla ANOMALY a la serie/bucket (ISS-S3-04)`

Specs: DB-ANOM-1, DB-ANOM-2, DB-ANOM-3, DB-MIG-1, DB-DDL-1, DB-SCOPE-1.

- [x] **2.1 RED** `tests/test_migrations.py` (marker `integration`): actualizar asserts de "head" `REV_0003` -> `REV_0004` (revisar todos: head, `down_revision`, downgrade-to-base). Agregar tests: columnas nuevas y ausencia de `metric_id`/`fk_anomaly_metric` (DB-ANOM-2.1, DB-MIG-1.1); CHECK `bucket_seconds >= 60` (DB-ANOM-1.2); `ck_anomaly_bucket_aligned`; FK app inexistente (DB-ANOM-1.3); `timestamp` independiente de `bucket_start` (DB-ANOM-1.4); unique rechaza duplicado y permite otro `model_id` / otro `bucket_seconds` (DB-ANOM-3.1-3.3); downgrade con tabla vacía restaura `metric_id` + FK (DB-MIG-1.2); downgrade con fila falla explícito y queda en `0004` (DB-MIG-1.3); upgrade sin datos (DB-MIG-1.4); equivalencia con `ddl_v1.0.sql` (DB-DDL-1.1, mismo patrón que el test de sync de `0003`).
- [x] **2.2 GREEN** `src/api/infrastructure/db/migrations/versions/0004_anomaly_series_anchor.py`: `down_revision = "0003"`; upgrade con guard (filas -> `RuntimeError`) y SQL del design; downgrade con el mismo guard, drop índice/constraints/columnas, `ADD COLUMN metric_id UUID NOT NULL` + `fk_anomaly_metric ON DELETE RESTRICT`. Pylint ignora `migrations/`, pero flake8 sí aplica.
- [x] **2.3 GREEN** `openspec/specs/database/ddl_v1.0.sql` §9: estado final de `anomaly` con comentario de trazabilidad `0004` (patrón de `0003`).
- [x] **2.4 REFACTOR**: verificar que ningún otro test/seed referencie `anomaly.metric_id` (`rg "anomaly" tests/ src/api`).

Archivos: `src/api/infrastructure/db/migrations/versions/0004_anomaly_series_anchor.py`, `openspec/specs/database/ddl_v1.0.sql`, `tests/test_migrations.py`.

Verificación (requiere Postgres 16 local, `DATABASE_URL` como en CI):
```
alembic upgrade head
PYTHONPATH=. pytest tests/test_migrations.py
alembic downgrade 0003 && alembic upgrade head
```

---

## Commit 3 — `feat(ml): reader HTTP del read path, config y mapper (ISS-S3-04)`

Specs: MLD-2 a MLD-10, ARCH-AI-1.2, ARCH-AI-3.2.

- [ ] **3.1 RED** `tests/test_ml_dataset_reader.py` (marker `unit`, sin Postgres): 
  - `align_window`: parametrizado (`s%b==0`, `e%b==0`, `e<=now`), MLD-4.1, 4.2, 4.3; errores naive tz, `s>=e`, ventana > 7 d tras alinear; 7 d exactos OK (MLD-6.1, 6.2).
  - `to_batch`: mapeo y propagación de `bucket_seconds` (MLD-2.1), vacío (MLD-2.2), campo faltante, extra ignorado, app mixta (MLD-7.2), duplicado `(metric_type_id, ts)`, fuera de `[start, end)`.
  - config: defaults (MLD-5.1), `bucket_seconds=30` falla sin request (MLD-5.2), falta API key / base URL nombra la variable (MLD-10.1), ventana 1..10080 y >= bucket, key como `SecretStr` ausente en `repr`/logs (MLD-10.2).
  - reader con `httpx.MockTransport`: URL, header `X-API-Key`, params `start/end/bucket_seconds` (MLD-3.1); 200 ok; 401/403 (MLD-9.1); 422 con status y código (MLD-6.3); 5xx y timeout (MLD-9.2); cuerpo no lista (MLD-9.3); sin fallback silencioso al mock.
  - aislamiento: test que escanea `src/ml/**/*.py` y falla si importa `src.api` (MLD-3.2, ARCH-AI-3.2).
- [ ] **3.2 GREEN** `src/ml/config.py`: `MLDatasetSettings` (pydantic-settings) con las 6 variables `INTELLOPS_*` del design.
- [ ] **3.3 GREEN** `src/ml/pipeline/mapper.py`: `DatasetReadError`, `to_batch(rows, bucket_seconds, start, end)` puro.
- [ ] **3.4 GREEN** `src/ml/pipeline/api_reader.py`: `align_window` + `read_dataset(settings, client=None)`; `httpx.Client` sync inyectable, `HTTPTransport(retries=N)`, mapeo de status a `DatasetReadError`, sin loguear la key.
- [ ] **3.5 GREEN** `pyproject.toml`: mover `httpx>=0.28.0` de `[project.optional-dependencies].dev` a `dependencies` (BSD-3, compatible con `pip-licenses --fail-on="SSPL;AGPL"`). Sin otras dependencias nuevas. No tocar `Dockerfile`/`docker-compose.yml`.
- [ ] **3.6 REFACTOR**: eliminar duplicación entre reader y mapper; verificar pylint >= 9.0 sobre `src/ml`.

Archivos: `src/ml/config.py`, `src/ml/pipeline/mapper.py`, `src/ml/pipeline/api_reader.py`, `pyproject.toml`, `tests/test_ml_dataset_reader.py`.

Verificación:
```
PYTHONPATH=. pytest tests/test_ml_dataset_reader.py -m unit
flake8 src/ tests/
pylint src/ --fail-under=9.0
```

---

## Bloque final de verificación (previo al PR)

Replicar CI (`.github/workflows/ci.yml`) en este orden, desde un venv Python 3.11:

- [ ] V1 `pip install -e ".[dev]"`
- [ ] V2 Lint: `flake8 src/ tests/` (0 warnings) y `pylint src/ --fail-under=9.0`
- [ ] V3 Unit (sin DB): `PYTHONPATH=. pytest -m unit`
- [ ] V4 DB limpia (Postgres 16, `DATABASE_URL=postgresql+asyncpg://intellops:intellops@localhost:5432/intellops`): `alembic upgrade head` -> `alembic downgrade 0003` -> `alembic upgrade head`
- [ ] V5 Suite completa + cobertura: `PYTHONPATH=. pytest --cov --cov-report=term-missing --cov-report=xml --cov-report=html --junitxml=reports/junit.xml` (gate `fail_under = 70`)
- [ ] V6 Contract: `PYTHONPATH=. pytest tests/test_contract.py -q` (esperado sin cambios: `openapi.yaml` y read path intactos)
- [ ] V7 Licencias: `pip install pip-licenses && pip-licenses --fail-on="SSPL;AGPL"`; confirmar que `httpx` (BSD-3) es la única dependencia movida a runtime
- [ ] V8 Docker: `docker compose build` (Dockerfile sin cambios; solo cambió `pyproject.toml`)
- [ ] V9 Diff acotado: `src/api` solo contiene `0004_anomaly_series_anchor.py`; sin cambios en `CHANGELOG.md`, `openapi.yaml`, `queue.py`, ADR 0004-0007 (DB-SCOPE-1.1)
- [ ] V10 `rg "metric_id" src/ml ml/data/generate_mock_dataset.py docs/architecture/IsolationForest/ContratoEntradaSalida.md` sin resultados salvo notas históricas

## Checklist del PR

- [ ] Título: `feat(ml): dataset operativo para ML con contrato M4 y migración 0004 (ISS-S3-04)`
- [ ] Label `size:exception` con justificación: ~750 líneas; tres commits atómicos (contrato, migración, reader) revisables por separado; contrato y migración son acoplados por el breaking change M4; sin chained PRs por decisión explícita del usuario.
- [ ] Descripción: enlazar `Closes #43`; listar los 3 commits y su verificación.
- [ ] Notificar a Santiago (owner DB) sobre la migración `0004` antes del merge (criterio de aceptación de database spec).
- [ ] Flaggear para #44: `ml/data/rum_mock.json` y el notebook EDA siguen con `metric_id` y quedan rotos hasta regenerarse; el generador ya emite M4.
- [ ] Notar: coordinar con PR #59 (no tocamos `CHANGELOG.md`/`openapi.yaml`/`queue.py`; ADR >= 0008; CHANGELOG como follow-up post-merge).
- [ ] Breaking change documentado: `MetricBatchInput` sin `metric_id`; downgrade `0004` solo con `anomaly` vacía.

## Follow-ups / decisiones abiertas

- **ADR-0008 + `containers.md` §2.3/C4 + `interfaces.md` §2.1** (ARCH-AI-1, ARCH-AI-3): el design lo deja como outline sin archivo (KISS), pero `architecture/spec.md` ARCH-AI-3.1 exige `docs/adr/0008-*.md`. No está en los 3 commits pedidos; decidir antes del PR si se agrega como commit 4 docs (~100-200 líneas, sin impacto en CI) o se mueve a follow-up. Hasta decidir, la spec de architecture queda sin cubrir.
- **Discrepancia MLD-8 vs design**: la spec dice omitir fila malformada y contarla; el design decidió fail-fast del batch. Las tareas 3.1/3.4 siguen el design (fail-fast). Reconciliar la spec (o el design) antes de `sdd-verify`.
- `application_id: UUID4` rechaza UUID no-v4: confirmar que `app_id` siempre se genera v4 (open question del design).
- Wiring en `Dockerfile`/`docker-compose.yml` y scheduler: se cablean con #44.
