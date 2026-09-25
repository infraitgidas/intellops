"""Entity JsException — mirror de js_exception (DDL 0001).

Solo tipa la tabla para la capa de repositorios; las migraciones se
escriben a mano (env.py target_metadata=None).
"""

# pylint: disable=too-few-public-methods,not-callable

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class JsException(Base):
    """Excepción JavaScript no manejada persistida por el worker.

    `metric_id` (FK nullable a rum_metric, ON DELETE SET NULL) es
    correlación blanda: se persiste solo si la métrica existe; si no,
    NULL + contador `ingest.metric_id_unknown_total`.
    """

    __tablename__ = "js_exception"

    error_id: Mapped[UUID] = mapped_column(primary_key=True)
    session_id: Mapped[UUID] = mapped_column(
        ForeignKey("user_session.session_id", ondelete="RESTRICT"), nullable=False
    )
    metric_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("rum_metric.metric_id", ondelete="SET NULL")
    )
    error_type: Mapped[str] = mapped_column(Text, nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    stack_trace: Mapped[str | None] = mapped_column(Text)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )