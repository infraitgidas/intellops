"""Entidad LabUser — usuarios del laboratorio (credenciales en 0002)."""
# pylint: disable=too-few-public-methods,unsubscriptable-object,not-callable

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, SmallInteger, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .user_role import UserRole


class LabUser(Base):
    """Usuario del laboratorio.

    `email` es único vía el índice `idx_lab_user_email` de la migración
    0002 (el DDL no declara UNIQUE constraint, solo índice — se respeta
    esa forma en el modelo). `password_hash` es nullable en DDL (ADR-06);
    el enforcement de login sin hash vive en el servicio.
    """

    __tablename__ = "lab_user"

    user_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    email: Mapped[str] = mapped_column(Text, nullable=False)
    password_hash: Mapped[str | None] = mapped_column(String(255))
    role_id: Mapped[int] = mapped_column(
        SmallInteger,
        ForeignKey("user_role.role_id", ondelete="RESTRICT"),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.current_timestamp()
    )

    role: Mapped[UserRole] = relationship()
