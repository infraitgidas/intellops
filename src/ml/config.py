"""Configuración por entorno del reader del dataset operativo (ISS-S3-04)."""
from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class MLDatasetSettings(BaseSettings):
    """Variables `INTELLOPS_*` del pull contra `GET /metrics/query`."""
    model_config = SettingsConfigDict(extra="ignore", populate_by_name=True)

    api_base_url: str = Field(min_length=1, validation_alias="INTELLOPS_API_BASE_URL")
    api_key: SecretStr = Field(min_length=1, validation_alias="INTELLOPS_ML_API_KEY")
    bucket_seconds: int = Field(
        default=60, ge=60, validation_alias="INTELLOPS_ML_BUCKET_SECONDS"
    )
    window_minutes: int = Field(
        default=60, ge=1, le=10080, validation_alias="INTELLOPS_ML_WINDOW_MINUTES"
    )
    http_timeout_seconds: float = Field(
        default=10, gt=0, allow_inf_nan=False, validation_alias="INTELLOPS_ML_HTTP_TIMEOUT_SECONDS"
    )
    http_retries: int = Field(
        default=2, ge=0, validation_alias="INTELLOPS_ML_HTTP_RETRIES"
    )

    @model_validator(mode="after")
    def _window_covers_one_bucket(self) -> "MLDatasetSettings":
        if self.window_minutes * 60 < self.bucket_seconds:
            raise ValueError("window_minutes must cover at least one bucket")
        return self
