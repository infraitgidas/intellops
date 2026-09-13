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

    assert _current_revision(conn) == REV_0002

    lab_user_columns = _column_names(conn, "lab_user")
    assert "password_hash" in lab_user_columns
    assert _column_nullable(conn, "lab_user", "password_hash") is True  # DATA-2

    application_columns = _column_names(conn, "application")
    assert "api_token_hash" in application_columns

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
    # Precondición: 0002 aplicada (evita falso verde).
    assert _current_revision(conn) == REV_0002

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

    assert _current_revision(conn) == REV_0002
    assert "password_hash" in _column_names(conn, "lab_user")
    assert "api_token_hash" in _column_names(conn, "application")
    assert _index_exists(conn, "idx_lab_user_email") is True
    assert _index_exists(conn, "idx_application_api_token_hash") is True
    seed = _seed_row(conn)
    assert seed is not None
    assert seed.email == SEED_EMAIL
    assert seed.role_name == "Admin"
