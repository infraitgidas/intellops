"""Entity Alert — mirror de alert (DDL 0001 + 0007).

Solo tipa la tabla para la capa de repositorios; las migraciones se
escriben a mano (env.py target_metadata=None).
"""

# pylint: disable=too-few-public-methods

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, SmallInteger, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Alert(Base):
    """Alerta de una aplicación, independiente de la anomalía (ADR-0012).

    `application_id` es el TENANT. `anomaly_id` es NULL para las alertas de
    reglas de umbral (B.14, v1) y apunta a la anomalía cuando la dispara la
    detección ML (M3). `recipient` y `channel_id` los completa el dispatcher
    (B.10) al despachar; mientras la alerta está Pending pueden ser NULL.
    """

    __tablename__ = "alert"

    alert_id: Mapped[UUID] = mapped_column(primary_key=True)
    application_id: Mapped[UUID] = mapped_column(
        ForeignKey("application.app_id", ondelete="RESTRICT"), nullable=False
    )
    anomaly_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("anomaly.anomaly_id", ondelete="RESTRICT")
    )
    severity: Mapped[str] = mapped_column(Text, nullable=False)
    recipient: Mapped[str | None] = mapped_column(Text)
    channel_id: Mapped[int | None] = mapped_column(
        SmallInteger, ForeignKey("alert_channel.channel_id", ondelete="RESTRICT")
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    status_id: Mapped[int] = mapped_column(
        SmallInteger,
        ForeignKey("alert_status.status_id", ondelete="RESTRICT"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
