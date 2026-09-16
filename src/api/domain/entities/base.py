"""Base declarativa compartida de los modelos ORM (SQLAlchemy 2.0 typed)."""
# pylint: disable=too-few-public-methods

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base declarativa de los modelos de dominio.

    Las migraciones se escriben a mano (env.py target_metadata=None);
    esta base solo tipa los modelos para la capa de repositorios.
    """
