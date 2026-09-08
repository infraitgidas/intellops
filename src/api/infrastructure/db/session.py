"""Motor y sesiones async de SQLAlchemy hacia PostgreSQL (asyncpg)."""

from collections.abc import AsyncIterator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from ...config import get_settings

# pylint: disable=invalid-name
_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    """Crea (una única vez) el engine async con el pool configurado."""
    global _engine  # pylint: disable=global-statement
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(
            settings.async_database_url,
            pool_size=settings.db_pool_size,
            max_overflow=settings.db_max_overflow,
            pool_pre_ping=True,
        )
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Crea (una única vez) el sessionmaker ligado al engine async."""
    global _session_factory  # pylint: disable=global-statement
    if _session_factory is None:
        _session_factory = async_sessionmaker(get_engine(), expire_on_commit=False)
    return _session_factory


async def get_session() -> AsyncIterator[AsyncSession]:
    """Dependencia de FastAPI para inyectar una sesión por request."""
    async with get_session_factory()() as session:
        yield session


async def check_connection() -> bool:
    """Usado por /health para verificar que la DB responde."""
    try:
        async with get_engine().connect() as connection:
            await connection.execute(text("SELECT 1"))
        return True
    except Exception:  # pylint: disable=broad-exception-caught
        return False


async def dispose_engine() -> None:
    """Libera el pool de conexiones al apagar la app."""
    global _engine  # pylint: disable=global-statement
    if _engine is not None:
        await _engine.dispose()
        _engine = None
