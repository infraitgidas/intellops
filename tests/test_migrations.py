"""Tests de la migración 0002 (credentials) — DATA-1..DATA-5.

Escenarios de spec:
- Upgrade a head: columnas/índices/seed presentes (DATA-1, DATA-3).
- Downgrade a 0001: limpieza completa y ordenada (DATA-4).
- Upgrade restaura el estado tras el downgrade.

Autocontenido: corre Alembic contra Postgres real vía la API de Alembic
(env.py lee DATABASE_URL del entorno y normaliza a psycopg sync).
"""

import os
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.engine import Connection

from api.config import get_settings
from api.infrastructure.security.password import PasswordHasher

SEED_USER_ID = "9f8c5a2e-1b2c-4d5e-8f9a-0b1c2d3e4f5a"
SEED_EMAIL = "admin@intellops.local"
REV_0001 = "0001"
REV_0002 = "0002"
REV_0003 = "0003"
REV_0004 = "0004"
REV_0005 = "0005"

DDL_PATH = "openspec/specs/database/ddl_v1.0.sql"


def _sync_url() -> str:
    url = get_settings().database_url
    if url.startswith("postgresql+asyncpg://"):
        return url.replace("postgresql+asyncpg://", "postgresql+psycopg://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


@pytest.fixture(scope="module")
def alembic_cfg() -> Config:
    cfg = Config("alembic.ini")
    os.environ["DATABASE_URL"] = _sync_url()
    return cfg


@pytest.fixture(autouse=True)
def _no_clean_db() -> None:
    """Override de clean_db: este módulo maneja su propio ciclo de
    migraciones y necesita el seed de la migración persistido entre
    upgrade/downgrade (el TRUNCATE de lab_user lo borraría)."""
    yield


@pytest.fixture
def conn() -> Connection:
    """Conexión sync en AUTOCOMMIT: cada statement libera sus locks al
    terminar, evitando bloquear el TRUNCATE de clean_db entre tests."""
    engine = create_engine(_sync_url())
    connection = engine.connect().execution_options(isolation_level="AUTOCOMMIT")
    yield connection
    connection.close()
    engine.dispose()


def _column_names(conn: Connection, table: str) -> set[str]:
    rows = conn.execute(
        text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema = 'public' AND table_name = :table"
        ),
        {"table": table},
    )
    return {row[0] for row in rows}


def _column_nullable(conn: Connection, table: str, column: str) -> bool:
    row = conn.execute(
        text(
            "SELECT is_nullable FROM information_schema.columns "
            "WHERE table_schema = 'public' AND table_name = :table "
            "AND column_name = :column"
        ),
        {"table": table, "column": column},
    ).first()
    return row is not None and row[0] == "YES"


def _index_exists(conn: Connection, index_name: str) -> bool:
    row = conn.execute(
        text(
            "SELECT 1 FROM pg_indexes "
            "WHERE schemaname = 'public' AND indexname = :index"
        ),
        {"index": index_name},
    ).first()
    return row is not None


def _current_revision(conn: Connection) -> str | None:
    row = conn.execute(text("SELECT version_num FROM alembic_version")).first()
    return row[0] if row else None


def _seed_row(conn: Connection):
    """Datos del seed sin password_hash (válido en 0001 y 0002)."""
    return conn.execute(
        text(
            "SELECT lu.user_id, lu.name, lu.email, ur.name AS role_name, "
            "lu.is_active "
            "FROM lab_user lu JOIN user_role ur ON ur.role_id = lu.role_id "
            "WHERE lu.email = :email"
        ),
        {"email": SEED_EMAIL},
    ).first()


def _seed_password_hash(conn: Connection) -> str | None:
    """Hash del seed; solo invocar con la columna presente (revisión 0002)."""
    row = conn.execute(
        text("SELECT password_hash FROM lab_user WHERE email = :email"),
        {"email": SEED_EMAIL},
    ).first()
    return row[0] if row else None


def test_upgrade_head_adds_columns_indexes_and_seed(alembic_cfg, conn):
    """DATA-1/DATA-3: desde 0001, upgrade head agrega columnas, índices y seed."""
    # Estado de partida explícito (escenario: "una DB en revisión 0001").
    command.downgrade(alembic_cfg, REV_0001)
    assert _current_revision(conn) == REV_0001

    command.upgrade(alembic_cfg, "head")

    assert _current_revision(conn) == REV_0005

    lab_user_columns = _column_names(conn, "lab_user")
    assert "password_hash" in lab_user_columns
    assert _column_nullable(conn, "lab_user", "password_hash") is True  # DATA-2

    application_columns = _column_names(conn, "application")
    assert "api_token_hash" in application_columns
    assert "is_active" in application_columns  # DATA-6: 0003 aplicada

    assert _index_exists(conn, "idx_lab_user_email") is True
    assert _index_exists(conn, "idx_application_api_token_hash") is True

    # OD-03: 0005 deja sample_rate nullable en js_exception.
    assert "sample_rate" in _column_names(conn, "js_exception")
    assert _column_nullable(conn, "js_exception", "sample_rate") is True

    seed = _seed_row(conn)
    assert seed is not None
    assert str(seed.user_id) == SEED_USER_ID
    assert seed.name == "Admin"
    assert seed.role_name == "Admin"
    assert seed.is_active is True
    # El hash del seed debe verificar contra la password dev (DATA-3).
    hasher = PasswordHasher()
    assert hasher.verify_password(
        get_settings().admin_bootstrap_password, _seed_password_hash(conn)
    )


def test_downgrade_0001_removes_credentials_and_seed(alembic_cfg, conn):
    """DATA-4: downgrade 0001 elimina columnas, índices y seed; 0001 intacto."""
    command.upgrade(alembic_cfg, "head")
    # Precondición: head (0005) aplicada (evita falso verde).
    assert _current_revision(conn) == REV_0005

    command.downgrade(alembic_cfg, REV_0001)

    assert _current_revision(conn) == REV_0001
    lab_user_columns = _column_names(conn, "lab_user")
    assert "password_hash" not in lab_user_columns
    assert _index_exists(conn, "idx_lab_user_email") is False
    application_columns = _column_names(conn, "application")
    assert "api_token_hash" not in application_columns
    assert _index_exists(conn, "idx_application_api_token_hash") is False
    assert _seed_row(conn) is None
    # Esquema de 0001 intacto.
    assert "user_id" in lab_user_columns
    assert _index_exists(conn, "idx_lab_user_role_id") is True


def test_upgrade_restores_state_after_downgrade(alembic_cfg, conn):
    """Upgrade tras downgrade restaura columnas, índices y seed."""
    command.downgrade(alembic_cfg, REV_0001)
    assert _current_revision(conn) == REV_0001

    command.upgrade(alembic_cfg, "head")

    assert _current_revision(conn) == REV_0005
    assert "password_hash" in _column_names(conn, "lab_user")
    application_columns = _column_names(conn, "application")
    assert "api_token_hash" in application_columns
    assert "is_active" in application_columns  # DATA-6
    assert _index_exists(conn, "idx_lab_user_email") is True
    assert _index_exists(conn, "idx_application_api_token_hash") is True
    seed = _seed_row(conn)
    assert seed is not None
    assert seed.email == SEED_EMAIL
    assert seed.role_name == "Admin"


# -- DATA-6..DATA-9: migración 0003 (is_active) -----------------------------

def test_upgrade_head_adds_is_active_default_true_for_existing_rows(
    alembic_cfg, conn
):
    """DATA-6/DATA-7: upgrade head agrega is_active NOT NULL DEFAULT TRUE y las
    filas preexistentes (revisión 0002) quedan activas."""
    command.upgrade(alembic_cfg, "head")
    command.downgrade(alembic_cfg, REV_0002)
    assert _current_revision(conn) == REV_0002
    assert "is_active" not in _column_names(conn, "application")

    # Fila preexistente tal como existía en 0002 (sin is_active).
    conn.execute(
        text(
            "INSERT INTO application (app_id, name, description, api_token_hash) "
            "VALUES (:app_id, :name, :description, NULL)"
        ),
        {
            "app_id": "11111111-2222-3333-4444-555555555555",
            "name": "legacy-app",
            "description": "creada antes de 0003",
        },
    )

    command.upgrade(alembic_cfg, "head")
    assert _current_revision(conn) == REV_0005

    application_columns = _column_names(conn, "application")
    assert "is_active" in application_columns
    assert _column_nullable(conn, "application", "is_active") is False

    row = conn.execute(
        text(
            "SELECT is_active FROM application "
            "WHERE app_id = '11111111-2222-3333-4444-555555555555'"
        )
    ).first()
    assert row is not None
    assert row[0] is True  # DATA-7: fila previa queda activa (default TRUE)

    # DATA-7: api_token_hash y su índice único parcial NO se tocan.
    assert "api_token_hash" in application_columns
    assert _index_exists(conn, "idx_application_api_token_hash") is True


def test_downgrade_0002_removes_is_active_only(alembic_cfg, conn):
    """DATA-8: downgrade 0002 elimina solo is_active; api_token_hash y el
    índice único parcial quedan intactos (rollback plan)."""
    command.upgrade(alembic_cfg, "head")
    assert _current_revision(conn) == REV_0005
    assert "is_active" in _column_names(conn, "application")

    command.downgrade(alembic_cfg, REV_0002)

    assert _current_revision(conn) == REV_0002
    application_columns = _column_names(conn, "application")
    assert "is_active" not in application_columns
    assert "api_token_hash" in application_columns
    assert _index_exists(conn, "idx_application_api_token_hash") is True

    # Dejar la DB en head para no contaminar el resto de la suite.
    command.upgrade(alembic_cfg, "head")
    assert _current_revision(conn) == REV_0005


def test_ddl_v1_0_sql_synced_with_0003(alembic_cfg, conn):
    """DATA-9: ddl_v1.0.sql declara is_active en application con comentario
    de trazabilidad de la migración 0003; api_token_hash intacto."""
    command.upgrade(alembic_cfg, "head")
    with open(DDL_PATH, encoding="utf-8") as handle:
        ddl = handle.read()

    # Bloque real de CREATE TABLE application: desde el nombre hasta la
    # primera línea que cierra con ");" (los comentarios pueden contener ");").
    application_block_lines = ddl.split("CREATE TABLE application", 1)[1].splitlines()
    application_block: list[str] = []
    for line in application_block_lines:
        application_block.append(line)
        if line.rstrip().endswith(");"):
            break
    application_block = "\n".join(application_block)
    assert "is_active" in application_block
    assert "0003" in application_block
    assert "api_token_hash" in application_block
    # La columna sigue siendo dormida hasta S2-02: nullable en el DDL.
    assert "is_active BOOLEAN NOT NULL DEFAULT TRUE" in application_block


# -- DB-ANOM / DB-MIG / DB-DDL: migración 0004 (ISS-S3-04) -------------------

ANOMALY_INSERT = text(
    "INSERT INTO anomaly (anomaly_id, application_id, metric_type_id, "
    "bucket_start, bucket_seconds, model_id, expected_value, actual_value, "
    "severity_score, confidence_score, timestamp) "
    "VALUES (:anomaly_id, :app_id, :metric_type_id, :bucket_start, "
    ":bucket_seconds, :model_id, 1, 2, 0.5, 0.5, :ts)"
)


def _constraint_exists(conn: Connection, name: str) -> bool:
    row = conn.execute(
        text("SELECT 1 FROM pg_constraint WHERE conname = :name"), {"name": name}
    ).first()
    return row is not None


def _seed_app_and_models(conn: Connection) -> tuple[str, str, str]:
    app_id, model_a, model_b = str(uuid4()), str(uuid4()), str(uuid4())
    conn.execute(
        text(
            "INSERT INTO application (app_id, name, description) "
            "VALUES (:id, :name, 'test 0004')"
        ),
        {"id": app_id, "name": f"app-{app_id}"},
    )
    for model_id in (model_a, model_b):
        conn.execute(
            text(
                "INSERT INTO ml_model (model_id, name, target_metric_id, "
                "version, status_id) VALUES (:id, 'iforest', 1, 'v1', 1)"
            ),
            {"id": model_id},
        )
    return app_id, model_a, model_b


def _insert_anomaly(conn: Connection, app_id: str, model_id: str, **overrides):
    params = {
        "anomaly_id": str(uuid4()),
        "app_id": app_id,
        "metric_type_id": 1,
        "bucket_start": "2026-08-28T21:15:00Z",
        "bucket_seconds": 60,
        "model_id": model_id,
        "ts": "2026-08-28T21:16:05Z",
    }
    params.update(overrides)
    conn.execute(ANOMALY_INSERT, params)


@pytest.fixture
def seeded(alembic_cfg, conn):
    """DB en head con app + 2 modelos; limpia anomaly/ml_model/application."""
    command.upgrade(alembic_cfg, "head")
    app_id, model_a, model_b = _seed_app_and_models(conn)
    yield app_id, model_a, model_b
    conn.execute(text("DELETE FROM anomaly"))
    conn.execute(
        text("DELETE FROM ml_model WHERE model_id IN (:a, :b)"),
        {"a": model_a, "b": model_b},
    )
    conn.execute(text("DELETE FROM application WHERE app_id = :id"), {"id": app_id})
    command.upgrade(alembic_cfg, "head")


def test_0004_replaces_metric_id_with_series_anchor(alembic_cfg, conn):
    """DB-ANOM-2.1 / DB-MIG-1.1: columnas nuevas, sin metric_id ni su FK."""
    command.upgrade(alembic_cfg, "head")
    assert _current_revision(conn) == REV_0005
    columns = _column_names(conn, "anomaly")
    assert {
        "application_id", "metric_type_id", "bucket_start",
        "bucket_seconds", "timestamp",
    } <= columns
    assert "metric_id" not in columns
    assert _constraint_exists(conn, "fk_anomaly_metric") is False
    assert _constraint_exists(conn, "fk_anomaly_application") is True
    assert _constraint_exists(conn, "fk_anomaly_metric_type") is True
    assert _index_exists(conn, "idx_anomaly_series_bucket_model") is True


def test_anomaly_rejects_bucket_seconds_below_60(seeded, conn):
    """DB-ANOM-1.2."""
    app_id, model_a, _ = seeded
    with pytest.raises(IntegrityError, match="ck_anomaly_bucket_seconds"):
        _insert_anomaly(conn, app_id, model_a, bucket_seconds=30)


def test_anomaly_rejects_unaligned_bucket_start(seeded, conn):
    """DB-ANOM-1: ck_anomaly_bucket_aligned."""
    app_id, model_a, _ = seeded
    with pytest.raises(IntegrityError, match="ck_anomaly_bucket_aligned"):
        _insert_anomaly(conn, app_id, model_a, bucket_start="2026-08-28T21:15:05Z")


def test_anomaly_rejects_unknown_application(seeded, conn):
    """DB-ANOM-1.3."""
    _, model_a, _ = seeded
    with pytest.raises(IntegrityError, match="fk_anomaly_application"):
        _insert_anomaly(conn, str(uuid4()), model_a)


def test_anomaly_timestamp_is_independent_of_bucket_start(seeded, conn):
    """DB-ANOM-1.4: timestamp (detección) != bucket_start."""
    app_id, model_a, _ = seeded
    _insert_anomaly(conn, app_id, model_a, ts="2026-08-29T10:00:00Z")
    row = conn.execute(text("SELECT timestamp <> bucket_start FROM anomaly")).first()
    assert row[0] is True


def test_anomaly_unique_series_bucket_model(seeded, conn):
    """DB-ANOM-3.1-3.3: rechaza duplicado; permite otro modelo o bucket_seconds."""
    app_id, model_a, model_b = seeded
    _insert_anomaly(conn, app_id, model_a)
    with pytest.raises(IntegrityError, match="idx_anomaly_series_bucket_model"):
        _insert_anomaly(conn, app_id, model_a)
    _insert_anomaly(conn, app_id, model_b)  # otro model_id
    _insert_anomaly(conn, app_id, model_a, bucket_seconds=300)  # otro bucket
    count = conn.execute(text("SELECT count(*) FROM anomaly")).scalar()
    assert count == 3


def test_downgrade_0004_empty_table_restores_metric_id(alembic_cfg, conn):
    """DB-MIG-1.2: downgrade con anomaly vacía restaura metric_id + FK."""
    command.upgrade(alembic_cfg, "head")
    conn.execute(text("DELETE FROM anomaly"))

    command.downgrade(alembic_cfg, REV_0003)

    assert _current_revision(conn) == REV_0003
    columns = _column_names(conn, "anomaly")
    assert "metric_id" in columns
    assert not {
        "application_id", "metric_type_id", "bucket_start", "bucket_seconds",
    } & columns
    assert _constraint_exists(conn, "fk_anomaly_metric") is True
    assert _index_exists(conn, "idx_anomaly_series_bucket_model") is False

    command.upgrade(alembic_cfg, "head")  # DB-MIG-1.4: upgrade sin datos
    assert _current_revision(conn) == REV_0005


def test_downgrade_0004_with_rows_fails_and_stays_at_head(seeded, alembic_cfg, conn):
    """DB-MIG-1.3: guard explícito; la DB queda en la revisión previa (head)."""
    app_id, model_a, _ = seeded
    _insert_anomaly(conn, app_id, model_a)

    with pytest.raises((RuntimeError, DBAPIError)):
        command.downgrade(alembic_cfg, REV_0003)

    assert _current_revision(conn) == REV_0005
    assert "application_id" in _column_names(conn, "anomaly")
    # El rollback también deshace el downgrade de 0005, previo al guard.
    assert "sample_rate" in _column_names(conn, "js_exception")


def test_ddl_v1_0_sql_synced_with_0004():
    """DB-DDL-1.1: ddl_v1.0.sql §9 refleja el estado final de anomaly."""
    with open(DDL_PATH, encoding="utf-8") as handle:
        ddl = handle.read()
    block = ddl.split("CREATE TABLE anomaly", 1)[1].split("-- 10. ALERT", 1)[0]
    assert "0004" in block
    for fragment in (
        "application_id UUID NOT NULL",
        "metric_type_id SMALLINT NOT NULL",
        "bucket_start TIMESTAMPTZ NOT NULL",
        "bucket_seconds INTEGER NOT NULL",
        "ck_anomaly_bucket_seconds",
        "ck_anomaly_bucket_aligned",
        "fk_anomaly_application",
        "fk_anomaly_metric_type",
        "idx_anomaly_series_bucket_model",
    ):
        assert fragment in block
    assert "fk_anomaly_metric\n" not in block


# -- DB-MIG / DB-DDL: migración 0005 (ISS-B-15, OD-03) -----------------------

def test_0005_adds_sample_rate_to_js_exception(alembic_cfg, conn):
    """OD-03/DB-MIG-1.5: 0005 agrega sample_rate DOUBLE PRECISION nullable;
    el downgrade la retira sin tocar el resto de la tabla."""
    command.upgrade(alembic_cfg, "head")
    assert _current_revision(conn) == REV_0005
    assert "sample_rate" in _column_names(conn, "js_exception")
    assert _column_nullable(conn, "js_exception", "sample_rate") is True

    command.downgrade(alembic_cfg, REV_0004)
    assert _current_revision(conn) == REV_0004
    assert "sample_rate" not in _column_names(conn, "js_exception")
    assert {"error_type", "message", "stack_trace"} <= _column_names(
        conn, "js_exception"
    )

    command.upgrade(alembic_cfg, "head")
    assert _current_revision(conn) == REV_0005


def test_ddl_v1_0_sql_synced_with_0005():
    """DB-DDL-1.2: ddl_v1.0.sql §7 refleja sample_rate de js_exception."""
    with open(DDL_PATH, encoding="utf-8") as handle:
        ddl = handle.read()
    block = ddl.split("CREATE TABLE js_exception", 1)[1].split("-- 8. ML_MODEL", 1)[0]
    assert "sample_rate DOUBLE PRECISION" in block
