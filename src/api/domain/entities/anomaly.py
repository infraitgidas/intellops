"""Entity Anomaly — mirror de anomaly (DDL 0001 + 0004).

Solo tipa la tabla para la capa de repositorios; las migraciones se
escriben a mano (env.py target_metadata=None).
"""

# pylint: disable=too-few-public-methods

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, SmallInteger
from sqlalchemy.dialects.postgresql import DOUBLE_PRECISION
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Anomaly(Base):
    """Anomalía detectada sobre una serie agregada (ADR-0008, migración 0004).

    Se ancla a la serie (`application_id`, `metric_type_id`) y al bucket
    (`bucket_start`, `bucket_seconds`), no a una métrica individual.
    `application_id` es el TENANT; `timestamp` es el instante de detección.
    En la v1 no hay detector que la escriba (la detección ML es M3, D1).
    """

    __tablename__ = "anomaly"

    anomaly_id: Mapped[UUID] = mapped_column(primary_key=True)
    application_id: Mapped[UUID] = mapped_column(
        ForeignKey("application.app_id", ondelete="RESTRICT"), nullable=False
    )
    metric_type_id: Mapped[int] = mapped_column(
        SmallInteger,
        ForeignKey("metric_type.metric_type_id", ondelete="RESTRICT"),
        nullable=False,
    )
    bucket_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    bucket_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    model_id: Mapped[UUID] = mapped_column(
        ForeignKey("ml_model.model_id", ondelete="RESTRICT"), nullable=False
    )
    expected_value: Mapped[float] = mapped_column(DOUBLE_PRECISION, nullable=False)
    actual_value: Mapped[float] = mapped_column(DOUBLE_PRECISION, nullable=False)
    severity_score: Mapped[float] = mapped_column(DOUBLE_PRECISION, nullable=False)
    confidence_score: Mapped[float] = mapped_column(DOUBLE_PRECISION, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
