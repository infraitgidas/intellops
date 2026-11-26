"""Entity AlertRule — mirror de alert_rule (migración 0008, ISS-B-14).

Solo tipa la tabla para la capa de repositorios; las migraciones se
escriben a mano (env.py target_metadata=None).
"""

# pylint: disable=too-few-public-methods,unsubscriptable-object

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    SmallInteger,
    Text,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class AlertRule(Base):
    """Umbral de una métrica para una aplicación (ADR-0013).

    `application_id` es el TENANT. La agregación con la que se compara el
    umbral se deriva de `metric_type_id` (latencia → p95, `AVAILABILITY` →
    uptime), no se configura: una regla que pidiera "p95 de la disponibilidad"
    no tendría sentido.

    `threshold` es NUMERIC y no punto flotante: la comparación inclusiva del
    umbral (`>=` para `gt`, `<=` para `lt`) no puede quedar a merced del
    redondeo.
    """

    __tablename__ = "alert_rule"

    rule_id: Mapped[UUID] = mapped_column(primary_key=True)
    application_id: Mapped[UUID] = mapped_column(
        ForeignKey("application.app_id", ondelete="RESTRICT"), nullable=False
    )
    metric_type_id: Mapped[int] = mapped_column(
        SmallInteger,
        ForeignKey("metric_type.metric_type_id", ondelete="RESTRICT"),
        nullable=False,
    )
    comparison: Mapped[str] = mapped_column(Text, nullable=False)
    threshold: Mapped[Decimal] = mapped_column(Numeric, nullable=False)
    window_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    min_samples: Mapped[int] = mapped_column(Integer, nullable=False)
    cooldown_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    severity: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
