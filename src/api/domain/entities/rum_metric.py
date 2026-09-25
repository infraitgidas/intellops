"""Entity RumMetric — mirror de rum_metric (DDL 0001).

Solo tipa la tabla para la capa de repositorios; las migraciones se
escriben a mano (env.py target_metadata=None).
"""

# pylint: disable=too-few-public-methods,not-callable

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, SmallInteger, Text, text
from sqlalchemy.dialects.postgresql import DOUBLE_PRECISION, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class RumMetric(Base):
    """Métrica RUM persistida por el worker de ingesta.

    `metric_type_id` (FK al catálogo metric_type) se resuelve contra el
    catálogo cacheado en el repositorio; `value` DOUBLE PRECISION.
    """

    __tablename__ = "rum_metric"

    metric_id: Mapped[UUID] = mapped_column(primary_key=True)
    session_id: Mapped[UUID] = mapped_column(
        ForeignKey("user_session.session_id", ondelete="RESTRICT"), nullable=False
    )
    metric_type_id: Mapped[int] = mapped_column(
        SmallInteger,
        ForeignKey("metric_type.metric_type_id", ondelete="RESTRICT"),
        nullable=False,
    )
    value: Mapped[float] = mapped_column(DOUBLE_PRECISION, nullable=False)
    unit: Mapped[str] = mapped_column(Text, nullable=False)
    page_url: Mapped[str | None] = mapped_column(Text)
    # "metadata" es atributo reservado en la Declarative API: el atributo se
    # llama metadata_json pero la columna física sigue siendo "metadata".
    metadata_json: Mapped[dict | None] = mapped_column("metadata", JSONB)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
