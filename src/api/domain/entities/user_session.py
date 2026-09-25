"""Entity UserSession — mirror de user_session (DDL 0001).

Solo tipa la tabla para la capa de repositorios; las migraciones se
escriben a mano (env.py target_metadata=None).
"""

# pylint: disable=too-few-public-methods,not-callable

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class UserSession(Base):
    """Sesión de usuario del agente RUM.

    `app_id` (FK a application, ON DELETE RESTRICT) es el TENANT del evento:
    lo fija el worker desde la aplicación autenticada por la key, NUNCA del
    payload (IAUTH-2, D2).
    """

    __tablename__ = "user_session"

    session_id: Mapped[UUID] = mapped_column(primary_key=True)
    app_id: Mapped[UUID] = mapped_column(
        ForeignKey("application.app_id", ondelete="RESTRICT"), nullable=False
    )
    user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("lab_user.user_id", ondelete="SET NULL")
    )
    ip_address: Mapped[str | None] = mapped_column(String)
    user_agent: Mapped[str | None] = mapped_column(Text)
    os_version: Mapped[str | None] = mapped_column(String)
    start_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    end_timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    duration_ms: Mapped[int | None] = mapped_column(Integer)