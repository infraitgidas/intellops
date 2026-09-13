"""Repositorios de dominio — contratos (Protocols)."""

from .application_repository import ApplicationRepository
from .user_repository import UserRepository

__all__ = ["ApplicationRepository", "UserRepository"]
