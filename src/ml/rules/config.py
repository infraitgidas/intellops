"""Configuración por entorno del motor de reglas (ISS-B-14, design §10).

Sigue el estilo de `src/ml/config.py` (`pydantic-settings`, alias explícito
por variable `INTELLOPS_*`) y normaliza `DATABASE_URL` al driver async igual
que `api.config.Settings`, porque el compose entrega la URL con
`postgresql://` y el motor usa asyncpg.
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_DATABASE_URL = (
    "postgresql+asyncpg://intellops:intellops@localhost:5432/intellops"
)


class RulesSettings(BaseSettings):
    """Variables de entorno consumidas por el worker de reglas."""

    model_config = SettingsConfigDict(extra="ignore", populate_by_name=True)

    database_url: str = Field(
        default=DEFAULT_DATABASE_URL,
        min_length=1,
        validation_alias="DATABASE_URL",
    )
    # Design §10: el ciclo corre cada 60 s por defecto. `gt=0` rechaza un
    # intervalo no positivo al construir: el scheduler nunca debe entrar en un
    # bucle sin pausa.
    interval_seconds: float = Field(
        default=60.0,
        gt=0,
        allow_inf_nan=False,
        validation_alias="INTELLOPS_RULES_INTERVAL_SECONDS",
    )

    @property
    def async_database_url(self) -> str:
        """`DATABASE_URL` normalizada al driver async (asyncpg)."""
        if self.database_url.startswith("postgresql://"):
            return self.database_url.replace(
                "postgresql://", "postgresql+asyncpg://", 1
            )
        return self.database_url


@lru_cache
def get_rules_settings() -> RulesSettings:
    """Settings del motor cacheadas como singleton para todo el proceso."""
    return RulesSettings()
