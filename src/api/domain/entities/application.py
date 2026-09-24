"""Entidad Application — aplicaciones monitoreadas (api_token_hash activa)."""
# pylint: disable=too-few-public-methods,unsubscriptable-object,not-callable

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, Index, String, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Application(Base):
    """Aplicación registrada para monitoreo.

    `api_token_hash` es la credencial de ingesta (S2-02): nullable, con
    índice único parcial declarado como en la migración 0002
    (`idx_application_api_token_hash WHERE api_token_hash IS NOT NULL`).
    `is_active` (migración 0003, ADR-20) apaga la key de ingesta sin
    revocarla: NOT NULL DEFAULT TRUE.
    """

    __tablename__ = "application"
    __table_args__ = (
        Index(
            "idx_application_api_token_hash",
            "api_token_hash",
            unique=True,
            postgresql_where=text("api_token_hash IS NOT NULL"),
        ),
    )

    app_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    api_token_hash: Mapped[str | None] = mapped_column(String(64))
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("TRUE")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.current_timestamp()
    )
