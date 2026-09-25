"""Configuración de la aplicación vía variables de entorno."""

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Variables de entorno consumidas por intellops-core."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    intellops_env: str = "development"
    database_url: str = "postgresql+asyncpg://intellops:intellops@localhost:5432/intellops"
    db_pool_size: int = 20
    db_max_overflow: int = 10

    # JWT (ISS-S2-01, AUTH-6). El default es SOLO dev/CI; en producción
    # se override con JWT_SECRET desde el entorno.
    jwt_secret: str = "dev-only-jwt-secret-change-me-0123456789abcdef"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    api_key_prefix: str = "ilp_"

    # Password dev del seed Admin (migración 0002) — solo dev/CI.
    admin_bootstrap_password: str = "admin-dev-password"

    # Ingesta RUM asíncrona (ISS-S2-03, RUM-5/DD-6): cola en proceso acotada
    # con N workers y drenado en shutdown con timeout. Env: INGEST_*.
    ingest_queue_maxsize: int = 10000
    ingest_workers: int = 2
    ingest_shutdown_timeout: float = 10.0

    @field_validator("jwt_secret")
    @classmethod
    def _validate_jwt_secret_length(cls, value: str) -> str:
        if len(value) < 32:
            raise ValueError("jwt_secret must be at least 32 characters")
        return value

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
