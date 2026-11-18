"""Configuración por entorno de `intellops-comms` (ISS-B-10, design §2/§4/§6).

Sigue el estilo de `src/ml/rules/config.py`: `pydantic-settings` con alias
explícito por variable `INTELLOPS_COMMS_*`, validación al construir y un
singleton cacheado. Los secretos (token del bot, contraseña SMTP) se leen SOLO
del entorno: nunca hay un valor por defecto en el código y nunca se loguean
(OAS-B10-4).

Un canal fuera del catálogo de la v1 (Telegram y Email; no hay WhatsApp) es
configuración inválida y falla al arrancar, no en el primer despacho. Un canal
sin destino configurado NO es un error: el stack arranca sin secretos y el
dispatcher deja esas alertas en Pending (OAS-B10-2).
"""

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from comms.dispatcher import RetryPolicy

DEFAULT_DATABASE_URL = (
    "postgresql+asyncpg://intellops:intellops@localhost:5432/intellops"
)

TELEGRAM = "telegram"
EMAIL = "email"
# Catálogo de canales de la v1: no hay WhatsApp (design §2).
SUPPORTED_CHANNELS = frozenset({TELEGRAM, EMAIL})
# Orden de evaluación de severidades (el mismo del catálogo `alert.severity`).
SEVERITIES = ("critical", "high", "medium", "low")

# Remitente de los mails cuando el operador no lo configura.
DEFAULT_SMTP_SENDER = "intellops@localhost"


class CommsSettings(BaseSettings):
    """Variables de entorno consumidas por el worker de despacho."""

    # `extra="ignore"`: el compose inyecta variables de otros servicios
    # (`INTELLOPS_ENV`). `env_ignore_empty`: el compose pasa las variables del
    # worker con default vacío (`${VAR:-}`) para poder levantar sin secretos;
    # un valor vacío tiene que significar "usá el default", no un error de
    # parseo al arrancar (OAS-B10-2).
    model_config = SettingsConfigDict(
        extra="ignore", populate_by_name=True, env_ignore_empty=True
    )

    database_url: str = Field(
        default=DEFAULT_DATABASE_URL,
        min_length=1,
        validation_alias="DATABASE_URL",
    )
    # El despacho es la latencia que ve una persona: 30 s por defecto, en vez
    # de los 60 s del ciclo de agregación del motor de reglas (design §8).
    interval_seconds: float = Field(
        default=30.0,
        gt=0,
        allow_inf_nan=False,
        validation_alias="INTELLOPS_COMMS_INTERVAL_SECONDS",
    )
    # Lote acotado por ciclo (D1/CD-1): el lock no se sostiene sobre toda la
    # tabla ni sobre un backlog grande.
    batch_size: int = Field(
        default=20,
        ge=1,
        le=100,
        validation_alias="INTELLOPS_COMMS_BATCH_SIZE",
    )

    # Routing por severidad (OAS-B10-1): defaults de la spec.
    channel_critical: str = Field(
        default=TELEGRAM, validation_alias="INTELLOPS_COMMS_CHANNEL_CRITICAL"
    )
    channel_high: str = Field(
        default=TELEGRAM, validation_alias="INTELLOPS_COMMS_CHANNEL_HIGH"
    )
    channel_medium: str = Field(
        default=EMAIL, validation_alias="INTELLOPS_COMMS_CHANNEL_MEDIUM"
    )
    channel_low: str = Field(
        default=EMAIL, validation_alias="INTELLOPS_COMMS_CHANNEL_LOW"
    )

    # Destino y credenciales de Telegram (OAS-B10-2). Sin token Y chat id el
    # canal no está disponible.
    telegram_bot_token: str | None = Field(
        default=None, validation_alias="INTELLOPS_COMMS_TELEGRAM_BOT_TOKEN"
    )
    telegram_chat_id: str | None = Field(
        default=None, validation_alias="INTELLOPS_COMMS_TELEGRAM_CHAT_ID"
    )

    # Destino y credenciales de Email (stdlib `smtplib`, D9).
    smtp_host: str | None = Field(
        default=None, validation_alias="INTELLOPS_COMMS_SMTP_HOST"
    )
    smtp_port: int = Field(
        default=587,
        ge=1,
        le=65535,
        validation_alias="INTELLOPS_COMMS_SMTP_PORT",
    )
    smtp_user: str | None = Field(
        default=None, validation_alias="INTELLOPS_COMMS_SMTP_USER"
    )
    smtp_password: str | None = Field(
        default=None, validation_alias="INTELLOPS_COMMS_SMTP_PASSWORD"
    )
    smtp_from: str | None = Field(
        default=None, validation_alias="INTELLOPS_COMMS_SMTP_FROM"
    )
    smtp_to: str | None = Field(
        default=None, validation_alias="INTELLOPS_COMMS_SMTP_TO"
    )
    smtp_starttls: bool = Field(
        default=True, validation_alias="INTELLOPS_COMMS_SMTP_STARTTLS"
    )

    # Retry y backoff (CD-3, design §4). El presupuesto acota la espera total
    # del proceso: con los defaults, 1 + 2 + 4 = 7 s.
    retry_attempts: int = Field(
        default=4,
        ge=1,
        le=10,
        validation_alias="INTELLOPS_COMMS_RETRY_ATTEMPTS",
    )
    retry_base_seconds: float = Field(
        default=1.0,
        gt=0,
        allow_inf_nan=False,
        validation_alias="INTELLOPS_COMMS_RETRY_BASE_SECONDS",
    )
    retry_factor: float = Field(
        default=2.0,
        ge=1.0,
        allow_inf_nan=False,
        validation_alias="INTELLOPS_COMMS_RETRY_FACTOR",
    )
    retry_budget_seconds: float = Field(
        default=60.0,
        gt=0,
        allow_inf_nan=False,
        validation_alias="INTELLOPS_COMMS_RETRY_BUDGET_SECONDS",
    )
    # Timeout de un envío individual (HTTP y SMTP): sin él un proveedor
    # colgado bloquea el lote entero, que se despacha con el lock tomado.
    delivery_timeout_seconds: float = Field(
        default=10.0,
        gt=0,
        allow_inf_nan=False,
        validation_alias="INTELLOPS_COMMS_DELIVERY_TIMEOUT_SECONDS",
    )

    @field_validator(
        "channel_critical", "channel_high", "channel_medium", "channel_low"
    )
    @classmethod
    def _validate_channel(cls, value: str) -> str:
        """El canal debe estar en el catálogo de la v1, en minúsculas."""
        channel = value.strip().lower()
        if channel not in SUPPORTED_CHANNELS:
            raise ValueError(
                f"unsupported channel {value!r}: "
                f"expected one of {sorted(SUPPORTED_CHANNELS)}"
            )
        return channel

    @property
    def async_database_url(self) -> str:
        """`DATABASE_URL` normalizada al driver async (asyncpg)."""
        if self.database_url.startswith("postgresql://"):
            return self.database_url.replace(
                "postgresql://", "postgresql+asyncpg://", 1
            )
        return self.database_url

    @property
    def routing(self) -> dict[str, str]:
        """Severidad → canal, en el orden de evaluación de la spec."""
        return {
            "critical": self.channel_critical,
            "high": self.channel_high,
            "medium": self.channel_medium,
            "low": self.channel_low,
        }

    @property
    def retry_policy(self) -> RetryPolicy:
        """Política de reintentos del despacho (CD-3)."""
        return RetryPolicy(
            attempts=self.retry_attempts,
            base_seconds=self.retry_base_seconds,
            factor=self.retry_factor,
            budget_seconds=self.retry_budget_seconds,
        )

    @property
    def telegram_configured(self) -> bool:
        """Hay token Y destino: sin alguno de los dos no se puede enviar."""
        return bool(self.telegram_bot_token and self.telegram_chat_id)

    @property
    def email_configured(self) -> bool:
        """Hay servidor SMTP Y destinatario (OAS-B10-2)."""
        return bool(self.smtp_host and self.smtp_to)

    @property
    def smtp_sender(self) -> str:
        """Remitente del mail: explícito, o el usuario SMTP, o un default."""
        return self.smtp_from or self.smtp_user or DEFAULT_SMTP_SENDER

    @property
    def configured_channels(self) -> list[str]:
        """Canales listos para despachar, en orden estable."""
        channels = []
        if self.telegram_configured:
            channels.append(TELEGRAM)
        if self.email_configured:
            channels.append(EMAIL)
        return channels


@lru_cache
def get_comms_settings() -> CommsSettings:
    """Settings del despachador cacheadas como singleton del proceso."""
    return CommsSettings()
