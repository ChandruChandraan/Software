"""System diagnostic health routines."""

from typing import Dict, Any
from sqlalchemy import text
from ..database.session import SessionLocal


def check_database() -> str:
    """Verify SQLite database connectivity."""
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        return "ok"
    except Exception:
        return "error"


def get_full_health() -> Dict[str, Any]:
    """Compile comprehensive system health diagnostic dictionary."""
    return {
        "status": "ok",
        "service": "backend",
        "database": check_database(),
    }
