"""TDD: lectura de anomalías — GET /anomalies y GET /anomalies/{anomaly_id}
(ISS-B-03, #68; ADR-0012).

Capas: unit (AnomalyService con repos dobles: límites antes del repo,
delegación y 404; forma de AnomalyOut) e integration (httpx ASGI + Postgres
real: aislamiento por key, orden, ventana sobre detected_at, filtro por tipo,
limit, 401/403/404/422).
"""

from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest
from sqlalchemy import text

from api.domain.exceptions import NotFoundError, QueryRangeError
from api.domain.repositories.anomaly_repository import AnomalyRecord
from api.domain.services.anomaly_service import AnomalyService

ANOMALY_FIELDS = {
    "anomaly_id",
    "application_id",
    "metric_type_id",
    "metric_name",
    "model_id",
    "bucket_start",
    "bucket_seconds",
    "expected_value",
    "actual_value",
    "severity_score",
    "confidence_score",
    "detected_at",
}
# Campos del borrador inicial del contrato que la tabla no guarda.
DRAFT_FIELDS = {"id", "score", "severity", "detector", "description", "metrics_snapshot"}


def _ts(dt: datetime) -> str:
    """ISO 8601 UTC con zona explícita (contrato date-time)."""
    return dt.isoformat()


def _record(**overrides) -> AnomalyRecord:
    values = {
        "anomaly_id": uuid4(),
        "application_id": uuid4(),
        "metric_type_id": 1,
        "metric_name": "TTFB",
        "model_id": uuid4(),
        "bucket_start": datetime(2026, 11, 1, 12, 0, tzinfo=timezone.utc),
        "bucket_seconds": 60,
        "expected_value": 120.0,
        "actual_value": 480.0,
        "severity_score": 0.9,
        "confidence_score": 0.8,
        "detected_at": datetime(2026, 11, 1, 12, 1, tzinfo=timezone.utc),
    }
    values.update(overrides)
    return AnomalyRecord(**values)


# -- Unit: AnomalyService ------------------------------------------------------

class _BoomRepo:
    """Repo que falla si se lo llama: prueba que la guarda corre antes."""

    called = False

    async def list_anomalies(self, *args, **kwargs):
        self.called = True
        raise AssertionError("el repo no debe llamarse con parámetros inválidos")

    async def get_anomaly(self, *args, **kwargs):
        self.called = True
        raise AssertionError("no aplica")


class _CaptureRepo:
    """Repo que registra los argumentos y devuelve un resultado fijo."""

    def __init__(self, result=None) -> None:
        self.kwargs = None
        self.result = result

    async def list_anomalies(self, app_id, start, end, limit, metric_type_id=None):
        self.kwargs = {
            "app_id": app_id,
            "start": start,
            "end": end,
            "limit": limit,
            "metric_type_id": metric_type_id,
        }
        return self.result or []

    async def get_anomaly(self, app_id, anomaly_id):
        self.kwargs = {"app_id": app_id, "anomaly_id": anomaly_id}
        return self.result


@pytest.mark.parametrize(
    "kwargs",
    [
        {"start": datetime(2026, 11, 1, tzinfo=timezone.utc),
         "end": datetime(2026, 11, 1, tzinfo=timezone.utc)},
        {"start": datetime(2026, 10, 1, tzinfo=timezone.utc),
         "end": datetime(2026, 11, 1, tzinfo=timezone.utc)},
        {"limit": 0},
        {"limit": 501},
    ],
)
async def test_service_rejects_invalid_params_without_calling_repo(kwargs):
    """Ventana inválida o limit fuera de 1..500 DEBEN dar 422 sin consultar."""
    repo = _BoomRepo()
    with pytest.raises(QueryRangeError) as excinfo:
        await AnomalyService(repo).list_anomalies(app_id=uuid4(), **kwargs)
    assert excinfo.value.code == "invalid_query_range"
    assert repo.called is False


async def test_service_delegates_defaults_and_filter():
    """Sin ventana ni limit, el servicio DEBE pedir 24 h y limit 50, y pasar
    el filtro por tipo y el tenant tal cual."""
    expected = [_record()]
    repo = _CaptureRepo(result=expected)
    app_id = uuid4()

    result = await AnomalyService(repo).list_anomalies(app_id=app_id, metric_type_id=2)

    assert result == expected
    assert repo.kwargs["app_id"] == app_id
    assert repo.kwargs["limit"] == 50
    assert repo.kwargs["metric_type_id"] == 2
    assert repo.kwargs["end"] - repo.kwargs["start"] == timedelta(hours=24)


async def test_service_get_anomaly_returns_record():
    """Si el repo encuentra la anomalía del tenant, el servicio la devuelve."""
    record = _record()
    repo = _CaptureRepo(result=record)

    found = await AnomalyService(repo).get_anomaly(
        app_id=record.application_id, anomaly_id=record.anomaly_id
    )

    assert found is record
    assert repo.kwargs == {
        "app_id": record.application_id,
        "anomaly_id": record.anomaly_id,
    }


async def test_service_get_anomaly_missing_raises_404():
    """Inexistente o de otro tenant → 404 anomaly_not_found (ADR-0003)."""
    with pytest.raises(NotFoundError) as excinfo:
        await AnomalyService(_CaptureRepo(result=None)).get_anomaly(
            app_id=uuid4(), anomaly_id=uuid4()
        )
    assert excinfo.value.http_code == 404
    assert excinfo.value.code == "anomaly_not_found"


def test_anomaly_out_matches_table_columns_not_draft():
    """AnomalyOut DEBE exponer las columnas reales, no el borrador del
    contrato (sin campos muertos, ADR-0012)."""
    from api.presentation.schemas.anomaly import AnomalyOut

    assert set(AnomalyOut.model_fields) == ANOMALY_FIELDS
    assert not DRAFT_FIELDS & set(AnomalyOut.model_fields)


# -- Integration: helpers ------------------------------------------------------

async def _make_app_with_key(client, make_admin, name: str):
    """Crea una aplicación + API key vía HTTP; devuelve (app_id, key, token)."""
    _, token = await make_admin(email=f"admin-{uuid4().hex[:12]}@intellops.local")
    created = await client.post(
        "/applications",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": name},
    )
    assert created.status_code == 201, created.text
    app_id = created.json()["app_id"]
    key_resp = await client.post(
        f"/applications/{app_id}/api-key",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert key_resp.status_code == 201, key_resp.text
    return app_id, key_resp.json()["api_key"], token


async def _metric_type_id(db_session, name: str) -> int:
    return (
        await db_session.execute(
            text("SELECT metric_type_id FROM metric_type WHERE name = :n"), {"n": name}
        )
    ).scalar_one()


async def _seed_model(db_session) -> UUID:
    """Seed de un ml_model (anomaly.model_id es NOT NULL con FK)."""
    model_id = uuid4()
    await db_session.execute(
        text(
            "INSERT INTO ml_model (model_id, name, target_metric_id, version, "
            "status_id) VALUES (:id, 'iforest', 1, 'v1', 1)"
        ),
        {"id": str(model_id)},
    )
    await db_session.commit()
    return model_id


async def _seed_anomaly(
    db_session, app_id, model_id, *, detected_at, metric_type="TTFB", actual=480.0
) -> UUID:
    """Seed SQL directo de una anomalía con bucket alineado a 60 s."""
    anomaly_id = uuid4()
    bucket_start = detected_at.replace(second=0, microsecond=0) - timedelta(minutes=1)
    await db_session.execute(
        text(
            "INSERT INTO anomaly (anomaly_id, application_id, metric_type_id, "
            "bucket_start, bucket_seconds, model_id, expected_value, "
            "actual_value, severity_score, confidence_score, timestamp) "
            "VALUES (:id, :app, :tid, :bucket, 60, :model, 120.0, :actual, "
            "0.9, 0.75, :ts)"
        ),
        {
            "id": str(anomaly_id),
            "app": str(app_id),
            "tid": await _metric_type_id(db_session, metric_type),
            "bucket": bucket_start,
            "model": str(model_id),
            "actual": actual,
            "ts": detected_at,
        },
    )
    await db_session.commit()
    return anomaly_id


# -- Integration: GET /anomalies -----------------------------------------------

async def test_list_anomalies_is_app_scoped_newest_first(client, make_admin, db_session):
    """GET /anomalies con la key de A DEBE devolver solo las anomalías de A,
    la más nueva primero, con las columnas reales y el nombre de la métrica."""
    app_a, key_a, _ = await _make_app_with_key(client, make_admin, "anom-a")
    app_b, _, _ = await _make_app_with_key(client, make_admin, "anom-b")
    model = await _seed_model(db_session)
    now = datetime.now(timezone.utc).replace(microsecond=0)

    older = await _seed_anomaly(db_session, app_a, model, detected_at=now - timedelta(hours=3))
    newer = await _seed_anomaly(
        db_session, app_a, model, detected_at=now - timedelta(hours=1), metric_type="FCP"
    )
    await _seed_anomaly(db_session, app_b, model, detected_at=now - timedelta(hours=2))

    resp = await client.get("/anomalies", headers={"X-API-Key": key_a})

    assert resp.status_code == 200, resp.text
    rows = resp.json()
    assert [row["anomaly_id"] for row in rows] == [str(newer), str(older)]
    for row in rows:
        assert set(row) == ANOMALY_FIELDS
        assert row["application_id"] == app_a
        assert row["model_id"] == str(model)
    newest = rows[0]
    assert newest["metric_name"] == "FCP"
    assert newest["bucket_seconds"] == 60
    assert newest["expected_value"] == 120.0
    assert newest["actual_value"] == 480.0
    assert newest["severity_score"] == 0.9
    assert newest["confidence_score"] == 0.75
    assert datetime.fromisoformat(newest["detected_at"]) == now - timedelta(hours=1)


async def test_list_anomalies_empty_when_nothing_detected(client, make_admin):
    """Sin anomalías (caso normal de la v1) la respuesta DEBE ser 200 []."""
    _, key, _ = await _make_app_with_key(client, make_admin, "anom-empty")
    resp = await client.get("/anomalies", headers={"X-API-Key": key})
    assert resp.status_code == 200
    assert resp.json() == []


async def test_list_anomalies_window_and_metric_type_filter(client, make_admin, db_session):
    """La ventana filtra por detected_at en [start, end) (default 24 h) y
    metric_type deja solo ese tipo."""
    app_id, key, _ = await _make_app_with_key(client, make_admin, "anom-window")
    model = await _seed_model(db_session)
    now = datetime.now(timezone.utc).replace(microsecond=0)
    old = await _seed_anomaly(db_session, app_id, model, detected_at=now - timedelta(days=2))
    ttfb = await _seed_anomaly(db_session, app_id, model, detected_at=now - timedelta(hours=2))
    fcp = await _seed_anomaly(
        db_session, app_id, model, detected_at=now - timedelta(hours=1), metric_type="FCP"
    )

    default = await client.get("/anomalies", headers={"X-API-Key": key})
    assert [row["anomaly_id"] for row in default.json()] == [str(fcp), str(ttfb)]

    explicit = await client.get(
        "/anomalies",
        headers={"X-API-Key": key},
        params={
            "start": _ts(now - timedelta(days=3)),
            "end": _ts(now - timedelta(hours=2)),  # exclusivo: deja afuera `ttfb`
        },
    )
    assert [row["anomaly_id"] for row in explicit.json()] == [str(old)]

    fcp_type = await _metric_type_id(db_session, "FCP")
    only_fcp = await client.get(
        "/anomalies", headers={"X-API-Key": key}, params={"metric_type": fcp_type}
    )
    assert [row["anomaly_id"] for row in only_fcp.json()] == [str(fcp)]


async def test_list_anomalies_limit_and_422_contract(client, make_admin, db_session):
    """limit=1 DEBE devolver solo la más nueva; limit fuera de rango y
    ventana inválida DEBEN responder 422 invalid_query_range con
    ErrorResponse (no el {"detail"} de FastAPI)."""
    app_id, key, _ = await _make_app_with_key(client, make_admin, "anom-limit")
    model = await _seed_model(db_session)
    now = datetime.now(timezone.utc).replace(microsecond=0)
    for hours in (3, 2, 1):
        newest = await _seed_anomaly(
            db_session, app_id, model, detected_at=now - timedelta(hours=hours)
        )

    one = await client.get("/anomalies", headers={"X-API-Key": key}, params={"limit": 1})
    assert [row["anomaly_id"] for row in one.json()] == [str(newest)]

    for params in (
        {"limit": 0},
        {"limit": 501},
        {"start": _ts(now), "end": _ts(now)},
        {"start": _ts(now - timedelta(days=8)), "end": _ts(now)},
    ):
        resp = await client.get("/anomalies", headers={"X-API-Key": key}, params=params)
        assert resp.status_code == 422, params
        assert resp.json()["error"]["code"] == "invalid_query_range"


# -- Integration: GET /anomalies/{anomaly_id} ----------------------------------

async def test_get_anomaly_own_and_other_tenant(client, make_admin, db_session):
    """El detalle propio DEBE dar 200; el de otra app DEBE dar el mismo 404
    anomaly_not_found que uno inexistente (ADR-0003)."""
    app_a, key_a, _ = await _make_app_with_key(client, make_admin, "anom-owner")
    _, key_b, _ = await _make_app_with_key(client, make_admin, "anom-other")
    model = await _seed_model(db_session)
    anomaly_id = await _seed_anomaly(
        db_session, app_a, model, detected_at=datetime.now(timezone.utc) - timedelta(hours=1)
    )

    own = await client.get(f"/anomalies/{anomaly_id}", headers={"X-API-Key": key_a})
    assert own.status_code == 200, own.text
    assert set(own.json()) == ANOMALY_FIELDS
    assert own.json()["anomaly_id"] == str(anomaly_id)
    assert own.json()["application_id"] == app_a

    cross = await client.get(f"/anomalies/{anomaly_id}", headers={"X-API-Key": key_b})
    missing = await client.get(f"/anomalies/{uuid4()}", headers={"X-API-Key": key_b})
    for resp in (cross, missing):
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "anomaly_not_found"
    assert cross.json() == missing.json()


# -- Integration: autenticación ------------------------------------------------

async def test_anomalies_401_without_key(client):
    """Sin X-API-Key ambos paths DEBEN responder 401 con WWW-Authenticate."""
    for path in ("/anomalies", f"/anomalies/{uuid4()}"):
        resp = await client.get(path)
        assert resp.status_code == 401
        assert resp.json()["error"]["code"] == "invalid_api_key"
        assert resp.headers.get("www-authenticate") == "ApiKey"


async def test_anomalies_403_app_inactive(client, make_admin):
    """Key válida de una aplicación inactiva DEBE responder 403 app_inactive."""
    app_id, key, token = await _make_app_with_key(client, make_admin, "anom-inactive")
    deactivated = await client.put(
        f"/applications/{app_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"is_active": False},
    )
    assert deactivated.status_code == 200

    resp = await client.get("/anomalies", headers={"X-API-Key": key})
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "app_inactive"
