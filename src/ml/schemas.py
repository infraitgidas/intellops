"""Módulo de esquemas y contratos de datos para el módulo IA."""
from pydantic import (
    UUID4,
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)


class MetricBatchInput(BaseModel):
    """Registro de entrada M4: un agregado por serie y bucket."""
    model_config = ConfigDict(extra="forbid", frozen=True)

    application_id: UUID4
    metric_type_id: int = Field(ge=1)
    timestamp: AwareDatetime  # bucket_start, alineado a epoch UTC
    bucket_seconds: int = Field(ge=60)
    value: float
    session_count: int = Field(ge=0)

    @model_validator(mode="after")
    def _check_bucket_alignment(self) -> "MetricBatchInput":
        if int(self.timestamp.timestamp()) % self.bucket_seconds != 0:
            raise ValueError("timestamp must be aligned to bucket_seconds (epoch UTC)")
        return self
