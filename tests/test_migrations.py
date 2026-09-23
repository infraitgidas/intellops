"""Tests de la migración 0002 (credentials) — DATA-1..DATA-5.

Escenarios de spec:
- Upgrade a head: columnas/índices/seed presentes (DATA-1, DATA-3).
- Downgrade a 0001: limpieza completa y ordenada (DATA-4).
- Upgrade restaura el estado tras el downgrade.

Autocontenido: corre Alembic contra Postgres real vía la API de Alembic
(env.py lee DATABASE_URL del entorno y normaliza a psycopg sync).
"""

import os

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection

from api.config import get_settings
from api.infrastructure.security.password import PasswordHasher

SEED_USER_ID = "9f8c5a2e-1b2c-4d5e-8f9a-0b1c2d3e4f5a"
SEED_EMAIL = "admin@intellops.local"
REV_0001 = "0001"
REV_0002 = "0002"
REV_0003 = "0003"

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

    assert _current_revision(conn) == REV_0003

    lab_user_columns = _column_names(conn, "lab_user")
    assert "password_hash" in lab_user_columns
    assert _column_nullable(conn, "lab_user", "password_hash") is True  # DATA-2

    application_columns = _column_names(conn, "application")
    assert "api_token_hash" in application_columns
    assert "is_active" in application_columns  # DATA-6: 0003 aplicada

    assert _index_exists(conn, "idx_lab_user_email") is True
    assert _index_exists(conn, "idx_application_api_token_hash") is True

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
    # Precondición: 0003 aplicada (evita falso verde).
    assert _current_revision(conn) == REV_0003

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

    assert _current_revision(conn) == REV_0003
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
    assert _current_revision(conn) == REV_0003

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
    assert _current_revision(conn) == REV_0003
    assert "is_active" in _column_names(conn, "application")

    command.downgrade(alembic_cfg, REV_0002)

    assert _current_revision(conn) == REV_0002
    application_columns = _column_names(conn, "application")
    assert "is_active" not in application_columns
    assert "api_token_hash" in application_columns
    assert _index_exists(conn, "idx_application_api_token_hash") is True

    # Dejar la DB en head para no contaminar el resto de la suite.
    command.upgrade(alembic_cfg, "head")
    assert _current_revision(conn) == REV_0003


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
