"""Entidades ORM de dominio (SQLAlchemy 2.0 typed)."""

from .application import Application
from .base import Base
from .lab_user import LabUser
from .user_role import UserRole

__all__ = ["Application", "Base", "LabUser", "UserRole"]
