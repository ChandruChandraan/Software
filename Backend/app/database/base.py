"""SQLAlchemy declarative base and metadata configuration."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base model for all database entities."""
    pass
