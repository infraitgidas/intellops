"""Configuración de la sonda por variables de entorno (S1, S2, S4).

Reusa `pydantic-settings` igual que `api.config.Settings`: los campos son
`PROBE_*` (pydantic-settings deriva el env var del nombre del campo) y la
ingesta apunta a la API con `INGEST_BASE_URL`.

Un intervalo no positivo es configuración inválida: la sonda nunca debe
entrar en un bucle sin pausa (S1). Se valida al construir, no en la primera
corrida.
"""

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Destino por defecto de la ingesta: la API local del stack de desarrollo. En
# producción se override con `INGEST_BASE_URL` (nunca se asume un host de test).
DEFAULT_INGEST_BASE_URL = "http://localhost:8000"


class ProbeSettings(BaseSettings):
    """Variables de entorno consumidas por `python -m probe`."""

    model_config = SettingsConfigDict(extra="ignore")

    # Origen único medido por la sonda y API key del tenant que reporta (S1).
    probe_target_url: str
    probe_api_key: str
    ingest_base_url: str = DEFAULT_INGEST_BASE_URL

    # Cadencia y timeout de la corrida (S1, S4). `gt=0` rechaza un intervalo
    # no positivo con ValidationError (subclase de ValueError).
    probe_interval_seconds: float = Field(default=60.0, gt=0)
    probe_timeout_seconds: float = Field(default=5.0, gt=0)

    # Aplicación RUM a la que pertenece la sesión sintética (D4). Opcional:
    # `application_id` nunca es autoridad de tenant (IAUTH-2).
    probe_application_id: str | None = None

    @field_validator("probe_target_url", "ingest_base_url")
    @classmethod
    def _validate_url(cls, value: str) -> str:
        """Un target sin esquema no es una URL medible: se rechaza al construir."""
        if not value.startswith(("http://", "https://")):
            raise ValueError("url must start with http:// or https://")
        return value


@lru_cache
def get_probe_settings() -> ProbeSettings:
    """Settings de la sonda cacheadas como singleton para todo el proceso."""
    return ProbeSettings()
