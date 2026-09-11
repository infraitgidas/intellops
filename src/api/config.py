"""Configuración de la aplicación vía variables de entorno."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Variables de entorno consumidas por intellops-core."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    intellops_env: str = "development"
    database_url: str = "postgresql+asyncpg://intellops:intellops@localhost:5432/intellops"
    db_pool_size: int = 20
    db_max_overflow: int = 10

    @property
    def async_database_url(self) -> str:
        """DATABASE_URL normalizada al driver async (asyncpg)."""
        if self.database_url.startswith("postgresql://"):
            return self.database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return self.database_url


@lru_cache
def get_settings() -> Settings:
    """Settings cacheada como singleton para todo el proceso."""
    return Settings()
