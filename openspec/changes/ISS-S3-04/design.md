# Design: ISS-S3-04 — Dataset operativo para ML (M4)

> **Enfoque (KISS)**: tres piezas en `src/ml` (config + reader HTTP + mapper), contrato `MetricBatchInput` sin `metric_id` y con `bucket_seconds`, y migración `0004` que ancla `ANOMALY` a la serie/bucket. Cero cambios en `src/api` salvo `0004`. Fuente: `proposal.md` (incl. question round) y `decisiones-metric-id-y-frontera.md` §6.

## Technical Approach

`config` → `align_window` (epoch UTC) → `GET /metrics/query` (`httpx`, `X-API-Key`) → `to_batch` (validación fail-fast) → `list[MetricBatchInput]`. Sin capa de puertos/protocolos: el reader es una función con un `httpx.Client` inyectable (los tests pasan `MockTransport`). Sin cross-imports con `src/api` (`containers.md` §5.1): el shape `MetricAggregate` se mapea desde JSON, no desde la dataclass.

## Architecture Decisions

| Tema | Opciones | Tradeoff | Decisión |
|---|---|---|---|
| Cliente HTTP | `httpx` / `urllib` stdlib / `requests` | `httpx` ya instalado (dev, BSD-3, viene con FastAPI TestClient) y trae `MockTransport`; `urllib` es 0-dep pero testeo vía monkeypatch; `requests` = dep nueva | **`httpx` sync**, se mueve de `dev` a `dependencies` en `pyproject.toml` (sin paquete nuevo; ~1 MB) |
| Sync vs async | async (estilo `src/api`) / sync | El consumidor (scikit-learn, worker loop) es sync; async agrega event loop sin beneficio | **sync** |
| Capas | puerto+adaptador+DTO / reader+mapper+config | Puerto sin 2.º adaptador real = abstracción especulativa | **reader + mapper + config**; `mock_reader` sigue como fuente alternativa |
| Malformed rows | skip-and-count / fail-fast | Saltear filas sesga el dataset en silencio | **fail-fast** del batch, con índice de fila en el error |
| Reintentos | loop con backoff / transporte | Pull bajo demanda: el caller re-ejecuta | **`HTTPTransport(retries=N)`** (solo errores de conexión); sin reintento por status |
| Alineación | ancla del read path (`start`) / epoch UTC | Ancla a `start` ⇒ identidad inestable entre pulls | **epoch UTC** alineando `start`/`end` antes de pedir (question round #2) |
| Contenedor | instalar deps en `src/ml/Dockerfile` ahora / después | Nadie invoca el reader en el contenedor todavía (sin scheduler) | **sin cambios** en `Dockerfile`/`docker-compose.yml`; se cablea con #44 |

## Data Flow

```
env ──> MLDatasetSettings ──> align_window(now|start,end, b)
                                   │ [start,end) múltiplos de b
                                   v
        httpx.Client ──GET /metrics/query?start&end&bucket_seconds=b──> intellops-core
                                   │ JSON list[MetricAggregate]
                                   v
                     to_batch(rows, b, start, end) ──> list[MetricBatchInput]
```

## Ventana: algoritmo de alineación

```python
def align_window(start: datetime, end: datetime, b: int) -> tuple[datetime, datetime]:
    s = floor(start.timestamp() / b) * b   # epoch UTC
    e = floor(end.timestamp() / b) * b     # descarta bucket abierto
    # errores: naive tz, s >= e, e - s > 7 d  -> DatasetReadError (antes de llamar)
```

- **Default**: `end = now`, `start = end - window_minutes`.
- **Bucket parcial final**: `end` se redondea hacia abajo y el SQL usa `< end` ⇒ solo buckets cerrados (latencia máx. `b`).
- **Bucket inicial**: `start` hacia abajo ⇒ el primer bucket es completo.
- **> 7 d tras alinear** (por el floor de `start`): error local, nunca 422.
- **Resultado vacío**: `[]` (no es error). **Paginación**: el read path no pagina; cota = 10080 buckets × N tipos (pocos MB).
- **Datos tardíos**: un re-pull puede cambiar `value` del mismo bucket; la identidad no cambia y el índice único de `0004` hace idempotente el reproceso.

## Interfaces / Contracts

```python
class MetricBatchInput(BaseModel):          # src/ml/schemas.py (BREAKING)
    model_config = ConfigDict(extra="forbid", frozen=True)
    application_id: UUID4
    metric_type_id: int = Field(ge=1)
    timestamp: AwareDatetime                # bucket_start
    bucket_seconds: int = Field(ge=60)
    value: float
    session_count: int = Field(ge=0)
    # model_validator: epoch(timestamp) % bucket_seconds == 0
```

| Env var | Default | Regla |
|---|---|---|
| `INTELLOPS_API_BASE_URL` | — (requerida) | URL |
| `INTELLOPS_ML_API_KEY` | — (requerida) | `SecretStr`, una app por ejecución |
| `INTELLOPS_ML_BUCKET_SECONDS` | 60 | ≥ 60 |
| `INTELLOPS_ML_WINDOW_MINUTES` | 60 | 1..10080, ≥ bucket |
| `INTELLOPS_ML_HTTP_TIMEOUT_SECONDS` | 10 | > 0 |
| `INTELLOPS_ML_HTTP_RETRIES` | 2 | ≥ 0 (solo conexión) |

`pydantic-settings` (ya dependencia). **Errores**: una sola `DatasetReadError` (en `mapper.py`). Mapeo: 200 → parse; 401/403 → error "key inválida / app inactiva"; 422 → error "bug de alineación"; 5xx, timeout, conexión → error "read path no disponible". **Validación del batch**: JSON lista; campos tomados explícitamente (extras de la respuesta se ignoran); `start ≤ ts < end`; un único `application_id`; sin duplicados `(metric_type_id, ts)`.

## Migración `0004_anomaly_series_anchor.py`

Upgrade (guard: si `anomaly` tiene filas → `RuntimeError`, no hay backfill posible):

```sql
ALTER TABLE anomaly DROP CONSTRAINT fk_anomaly_metric;
ALTER TABLE anomaly DROP COLUMN metric_id;
ALTER TABLE anomaly
  ADD COLUMN application_id UUID NOT NULL,
  ADD COLUMN metric_type_id SMALLINT NOT NULL,
  ADD COLUMN bucket_start TIMESTAMPTZ NOT NULL,
  ADD COLUMN bucket_seconds INTEGER NOT NULL,
  ADD CONSTRAINT ck_anomaly_bucket_seconds CHECK (bucket_seconds >= 60),
  ADD CONSTRAINT ck_anomaly_bucket_aligned
      CHECK ((EXTRACT(EPOCH FROM bucket_start)::bigint % bucket_seconds) = 0),
  ADD CONSTRAINT fk_anomaly_application FOREIGN KEY (application_id)
      REFERENCES application(app_id) ON DELETE RESTRICT,
  ADD CONSTRAINT fk_anomaly_metric_type FOREIGN KEY (metric_type_id)
      REFERENCES metric_type(metric_type_id) ON DELETE RESTRICT;
CREATE UNIQUE INDEX idx_anomaly_series_bucket_model
  ON anomaly(application_id, metric_type_id, bucket_start, bucket_seconds, model_id);
```

`timestamp` queda como instante de detección. Downgrade: mismo guard (tabla no vacía → `RuntimeError`; `ALERT` también la referencia), luego drop índice/constraints/columnas, `ADD COLUMN metric_id UUID NOT NULL` + `fk_anomaly_metric`. `ddl_v1.0.sql` §9 refleja el estado final con comentario de trazabilidad `0004` (patrón de `0003`).

## File Changes

| Archivo | Acción |
|---|---|
| `src/ml/schemas.py` | Modify — contrato M4 |
| `src/ml/mock_data.json` | Modify — sin `metric_id`, `bucket_seconds: 60`, 2.º registro a `21:15:00Z` |
| `ml/data/generate_mock_dataset.py` | Modify — `metric_id` → `bucket_seconds: 60`; docstring; quitar `import uuid` si queda sin uso. **No** se regenera `rum_mock.json` (#44) |
| `docs/architecture/IsolationForest/ContratoEntradaSalida.md` | Modify — entrada/salida M4 |
| `src/api/infrastructure/db/migrations/versions/0004_anomaly_series_anchor.py` | Create |
| `openspec/specs/database/ddl_v1.0.sql` | Modify — §9 |
| `src/ml/config.py`, `src/ml/pipeline/mapper.py`, `src/ml/pipeline/api_reader.py` | Create |
| `pyproject.toml` | Modify — `httpx` a runtime |
| `tests/test_ml_worker.py`, `tests/test_migrations.py` | Modify |
| `tests/test_ml_dataset_reader.py` | Create |

Vedados (PR #59): `CHANGELOG.md`, `openapi.yaml`, `queue.py`, ADR 0004–0007.

## Testing Strategy (strict TDD, RED primero)

| Capa | Qué | Cómo |
|---|---|---|
| Unit | `MetricBatchInput` (extra forbid, alineación, tz) y mocks | `pytest -m unit` |
| Unit | `align_window` | Parametrizado (sin dep nueva): para muchos `now`×`b`: `s%b==0`, `e%b==0`, `e≤now`; dos pulls solapados ⇒ mismas claves; errores (naive, `s≥e`, >7 d) |
| Unit | `to_batch` | Filas válidas, campo faltante, extra ignorado, app mixta, duplicado, fuera de rango, vacío |
| Unit | reader | `httpx.MockTransport`: query params/header, 200/401/403/422/500, timeout |
| Integration | `0004` | `tests/test_migrations.py`: columnas/índice/FKs, guard de downgrade con fila, unique rechaza duplicado, `ck_anomaly_bucket_aligned`, sync DDL. **Actualizar** asserts `REV_0003` de "head" a `REV_0004` |

## Slicing (chained, work-unit commits)

| # | Contenido | Est. |
|---|---|---|
| 1 | `feat(ml)`: contrato M4 — `schemas.py`, `mock_data.json`, generador, `ContratoEntradaSalida.md`, `test_ml_worker.py` | ~120 |
| 2 | `feat(db)`: `0004` + `ddl_v1.0.sql` + `test_migrations.py` | ~250 |
| 3 | `feat(ml)`: config + mapper + reader + `pyproject.toml` + tests | ~380 |

Rollback por slice: revert; `0004` vía `alembic downgrade 0003` (tabla vacía).

## ADR-0008 (outline — sin archivo)

- **Contexto**: `containers.md` §2.3/C4 dice "AI engine lee `RUM_METRIC` de DB"; ADR-0003 dice "consume `/metrics/query`".
- **Decisión**: lectura de telemetría vía HTTP read path (app-scoped por key); escritura de `ANOMALY`/`ALERT` en DB se mantiene.
- **Consecuencias**: dataset = contrato público agregado; dependencia de disponibilidad de `intellops-core`; multi-app = N keys.
- **Afecta**: `containers.md` §2.3/C4, `interfaces.md` §2.1.

## Open Questions

- [ ] ¿Se materializa ADR-0008 + ajuste de `containers.md`/`interfaces.md` en apply (criterio de éxito del proposal) o queda solo este outline? Hoy: solo outline (guía KISS).
- [ ] `application_id: UUID4` rechaza apps con UUID no-v4: confirmar que `app_id` siempre se genera v4.
