"""Entidad UserRole — catálogo de roles (seed de la migración 0001)."""
# pylint: disable=too-few-public-methods,unsubscriptable-object

from sqlalchemy import Boolean, Identity, SmallInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class UserRole(Base):
    """Rol de usuario del laboratorio (Admin, Researcher)."""

    __tablename__ = "user_role"

    role_id: Mapped[int] = mapped_column(
        SmallInteger, Identity(always=True), primary_key=True
    )
    name: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
