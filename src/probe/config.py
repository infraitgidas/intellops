"""Configuración de la sonda por variables de entorno (S1, S2, S4).

Reusa `pydantic-settings` igual que `api.config.Settings`: los campos son
`PROBE_*` (pydantic-settings deriva el env var del nombre del campo) y la
ingesta apunta a la API con `INGEST_BASE_URL`.

Un intervalo no positivo es configuración inválida: la sonda nunca debe
entrar en un bucle sin pausa (S1). Se valida al construir, no en la primera
corrida.

`PROBE_APPLICATION_ID` se valida como UUID por la misma razón (S2): un valor
que no es UUID hace que la política de ingesta rechace el evento COMPLETO con
`invalid_uuid`, así que la sonda perdería la corrida en silencio cada ciclo.
"""

import os
from functools import lru_cache
from urllib.parse import urlsplit
from uuid import UUID

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Destino por defecto de la ingesta: la API local del stack de desarrollo. En
# producción se override con `INGEST_BASE_URL` (nunca se asume un host de test).
DEFAULT_INGEST_BASE_URL = "http://localhost:8000"

# Prefijos de entorno que la sonda consume. Cualquier otra variable con estos
# prefijos es un typo del operador, no ruido ajeno.
_ENV_PREFIXES = ("PROBE_", "INGEST_")


class ProbeSettings(BaseSettings):
    """Variables de entorno consumidas por `python -m probe`."""

    model_config = SettingsConfigDict(extra="forbid")

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

    @model_validator(mode="after")
    def _reject_unknown_env_vars(self) -> "ProbeSettings":
        """Un `PROBE_*` mal escrito es configuración inválida, no ruido.

        pydantic-settings solo lee los campos declarados, así que `extra` no ve
        un `PROBE_INTERVAL_SECOND` (sin la S final): la sonda arrancaría con el
        intervalo por defecto sin ningún aviso. Se rechaza al construir, que es
        donde se puede corregir.
        """
        known = {name.upper() for name in type(self).model_fields.keys()}
        unknown = sorted(
            key
            for key in os.environ
            if key.upper().startswith(_ENV_PREFIXES) and key.upper() not in known
        )
        if unknown:
            raise ValueError(
                "unknown probe environment variables: " + ", ".join(unknown)
            )
        return self

    @field_validator("probe_target_url", "ingest_base_url")
    @classmethod
    def _validate_url(cls, value: str) -> str:
        """Una URL medible necesita esquema `http(s)` Y host.

        Validar solo el prefijo deja pasar `http://`, que no es una URL
        medible: la sonda arrancaría y perdería cada corrida con
        `connection_error` en vez de fallar al construir, que es donde se puede
        corregir. Un puerto no numérico se rechaza acá por la misma razón.
        """
        try:
            parts = urlsplit(value)
            _ = parts.port  # un puerto inválido lanza acá, no en la corrida.
        except ValueError as exc:
            raise ValueError("url is not a valid http(s) url") from exc
        if parts.scheme not in ("http", "https") or not (parts.hostname or "").strip():
            raise ValueError("url must start with http:// or https:// and have a host")
        return value

    @field_validator("probe_application_id")
    @classmethod
    def _validate_application_id(cls, value: str | None) -> str | None:
        """El `application_id` debe ser UUID o ausente (S2).

        La política de ingesta rechaza el evento completo con `invalid_uuid` si
        el valor no parsea como UUID: sin esta validación la sonda arrancaría
        igual y perdería cada corrida sin dejar rastro (solo un 202 con
        `accepted=0`). Falla al construir, que es donde se puede corregir.
        """
        if value is None:
            return None
        try:
            UUID(value)
        except (ValueError, AttributeError, TypeError) as exc:
            raise ValueError("application_id must be a UUID") from exc
        return value


@lru_cache
def get_probe_settings() -> ProbeSettings:
    """Settings de la sonda cacheadas como singleton para todo el proceso.

    `main()` la usa; construir otro `ProbeSettings` por ciclo releería el
    entorno en cada corrida (una sonda lee su configuración una vez, al
    arrancar).
    """
    return ProbeSettings()
