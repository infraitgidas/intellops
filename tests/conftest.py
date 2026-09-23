"""Fixtures async de la suite (Postgres real, pytest-asyncio) — design §7.

- `_migrated_database` (session): corre `alembic upgrade head` una vez.
- `db_session` (session): sesión async reutilizando el engine global.
- `clean_db` (autouse): TRUNCATE de tablas de datos por test; catálogos intactos.
- `seed_admin`: re-inserta el seed Admin de 0002 (mismo UUID fijo y password dev).
- `client`: httpx AsyncClient con override de get_session.
- `make_admin` / `make_researcher`: crean usuario vía repositorio + hasher + JWT.
"""

import os
from collections.abc import AsyncIterator, Callable
from uuid import UUID, uuid4

import pytest
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from api.config import get_settings
from api.domain.entities.lab_user import LabUser
from api.domain.entities.user_role import UserRole
from api.infrastructure.db.repositories.sqlalchemy_user_repository import (
    SQLAlchemyUserRepository,
)
from api.infrastructure.db.session import get_session
from api.infrastructure.security.jwt import create_access_token
from api.infrastructure.security.password import PasswordHasher
from api.main import app
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    async_sessionmaker,
    create_async_engine,
)

# Tablas de datos (no catálogos) que clean_db trunca por test (design §7).
DATA_TABLES = (
    "rum_metric",
    "js_exception",
    "anomaly",
    "alert",
    "ml_model",
    "user_session",
    "user_favorite_metric",
    "lab_user",
    "application",
)

SEED_USER_ID = UUID("9f8c5a2e-1b2c-4d5e-8f9a-0b1c2d3e4f5a")
SEED_EMAIL = "admin@intellops.local"


def _alembic_config() -> Config:
    cfg = Config("alembic.ini")
    os.environ["DATABASE_URL"] = get_settings().database_url
    return cfg


@pytest.fixture(scope="session", autouse=True)
def _migrated_database() -> None:
    """Asegura el esquema en head antes de la suite (Postgres real)."""
    command.upgrade(_alembic_config(), "head")
    yield


@pytest.fixture(scope="session")
async def test_engine() -> AsyncIterator[AsyncEngine]:
    """Engine async PROPIO del conftest (loop de pytest-asyncio).

    No usa el engine global de session.py: test_health lo crea en el
    loop del TestClient (sync) y mezclar loops rompe check_connection
    con "Future attached to a different loop".
    """
    engine = create_async_engine(get_settings().async_database_url, pool_pre_ping=True)
    yield engine
    await engine.dispose()


@pytest.fixture(scope="session")
async def db_session(test_engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    """Sesión async compartida por la suite (engine del conftest)."""
    factory = async_sessionmaker(test_engine, expire_on_commit=False)
    async with factory() as session:
        yield session


@pytest.fixture(autouse=True)
async def clean_db(db_session: AsyncSession) -> AsyncIterator[None]:
    """Trunca las tablas de datos por test; catálogos (user_role, ...) intactos."""
    await db_session.execute(
        text(f"TRUNCATE {', '.join(DATA_TABLES)} RESTART IDENTITY CASCADE")
    )
    await db_session.commit()
    yield


async def _create_user_with_token(
    session: AsyncSession,
    *,
    name: str,
    email: str,
    role_name: str,
    password: str = "dev-password-123",
) -> tuple[LabUser, str]:
    """Crea un lab_user con rol y devuelve (usuario, token JWT)."""
    settings = get_settings()
    hasher = PasswordHasher()
    repo = SQLAlchemyUserRepository(session)
    role = (
        await session.execute(select(UserRole).where(UserRole.name == role_name))
    ).scalar_one()
    user = LabUser(
        user_id=uuid4(),
        name=name,
        email=email,
        role_id=role.role_id,
        is_active=True,
        password_hash=hasher.hash_password(password),
    )
    await repo.create(user)
    await session.commit()
    await session.refresh(user)
    token = create_access_token(
        user.user_id,
        role.name,
        secret=settings.jwt_secret,
        expire_minutes=settings.jwt_access_token_expire_minutes,
    )
    return user, token


@pytest.fixture
async def seed_admin(db_session: AsyncSession) -> LabUser:
    """Re-inserta el seed Admin de 0002 (UUID fijo + password dev)."""
    settings = get_settings()
    hasher = PasswordHasher()
    role_id = (
        await db_session.execute(
            select(UserRole.role_id).where(UserRole.name == "Admin")
        )
    ).scalar_one()
    admin = LabUser(
        user_id=SEED_USER_ID,
        name="Admin",
        email=SEED_EMAIL,
        role_id=role_id,
        is_active=True,
        password_hash=hasher.hash_password(settings.admin_bootstrap_password),
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)
    return admin


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncIterator[AsyncClient]:
    """httpx AsyncClient contra la app con get_session overridden."""

    async def _override_get_session() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_session] = _override_get_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as test_client:
        yield test_client
    app.dependency_overrides.pop(get_session, None)


# -- App de prueba /_probe (IAUTH-5: guard desacoplado, prod sin wiring) -----
#
# La app de producción NO cablea `require_api_key` a ningún path en S2-02
# (wiring a /telemetry/* en #37). Para ejercitar el guard aisladamente, esta
# app de TEST expone GET /_probe protegido por la MISMA dependencia.

from fastapi import Depends, FastAPI  # noqa: E402
from typing import Annotated  # noqa: E402

from api.domain.entities.application import Application  # noqa: E402
from api.domain.exceptions import DomainError  # noqa: E402
from api.presentation.dependencies import require_api_key  # noqa: E402
from api.presentation.errors import domain_error_handler  # noqa: E402

probe_app = FastAPI(title="intellops-probe-test")
# Mismo contrato de errores que producción (ADR-09).
probe_app.add_exception_handler(DomainError, domain_error_handler)


@probe_app.get("/_probe")
async def probe(
    application: Annotated[Application, Depends(require_api_key)],
    claimed_app_id: str | None = None,
) -> dict:
    """Devuelve la Application inyectada por el guard + el app_id reclamado
    en el payload/query (el guard DEBE ignorarlo: binding 1:1, IAUTH-2)."""
    return {
        "app_id": str(application.app_id),
        "name": application.name,
        "claimed_app_id": claimed_app_id,
    }


@pytest.fixture
async def probe_client(db_session: AsyncSession) -> AsyncIterator[AsyncClient]:
    """httpx AsyncClient contra la app de prueba /_probe (mismo override)."""

    async def _override_get_session() -> AsyncIterator[AsyncSession]:
        yield db_session

    probe_app.dependency_overrides[get_session] = _override_get_session
    transport = ASGITransport(app=probe_app)
    async with AsyncClient(transport=transport, base_url="http://test") as test_client:
        yield test_client
    probe_app.dependency_overrides.pop(get_session, None)


@pytest.fixture
async def make_admin(
    db_session: AsyncSession,
) -> Callable[..., AsyncIterator[tuple[LabUser, str]]]:
    """Factory de usuario Admin + token."""

    async def _make(
        name: str = "Admin Test",
        email: str = "admin-test@intellops.local",
        password: str = "dev-password-123",
    ) -> tuple[LabUser, str]:
        return await _create_user_with_token(
            db_session, name=name, email=email, role_name="Admin", password=password
        )

    return _make


@pytest.fixture
async def make_researcher(
    db_session: AsyncSession,
) -> Callable[..., AsyncIterator[tuple[LabUser, str]]]:
    """Factory de usuario Researcher + token."""

    async def _make(
        name: str = "Researcher Test",
        email: str = "researcher-test@intellops.local",
        password: str = "dev-password-123",
    ) -> tuple[LabUser, str]:
        return await _create_user_with_token(
            db_session,
            name=name,
            email=email,
            role_name="Researcher",
            password=password,
        )

    return _make
