"""Entity AlertRule — mirror de alert_rule (migración 0008, ISS-B-14).

Solo tipa la tabla para la capa de repositorios; las migraciones se
escriben a mano (env.py target_metadata=None).
"""

# pylint: disable=too-few-public-methods,unsubscriptable-object

from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Integer, Text, text
from sqlalchemy.dialects.postgresql import DOUBLE_PRECISION
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class AlertRule(Base):
    """Override de una regla de umbral por aplicación (ISS-B-14).

    Una fila reemplaza por completo al default del código para su
    (`application_id`, `rule_id`); sin fila rige el default. `rule_id` es
    `latency`, `error_rate` o `availability`.
    """

    __tablename__ = "alert_rule"

    application_id: Mapped[UUID] = mapped_column(
        ForeignKey("application.app_id", ondelete="CASCADE"), primary_key=True
    )
    rule_id: Mapped[str] = mapped_column(Text, primary_key=True)
    threshold: Mapped[float] = mapped_column(DOUBLE_PRECISION, nullable=False)
    severity: Mapped[str] = mapped_column(Text, nullable=False)
    window_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    min_samples: Mapped[int] = mapped_column(Integer, nullable=False)
    cooldown_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )
