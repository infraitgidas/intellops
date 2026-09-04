from pydantic import BaseModel, UUID4
from datetime import datetime


class MetricBatchInput(BaseModel):
    application_id: UUID4
    metric_id: UUID4
    metric_type_id: int
    timestamp: datetime
    value: float
    session_count: int
