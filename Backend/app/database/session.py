"""Database engine, session management, and schema initialization."""

import logging
from pathlib import Path
from typing import Generator
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker, Session
from .base import Base
from ..config import get_config

logger = logging.getLogger("backend.database")

_engine = None
_SessionLocal = None


def get_engine():
    """Lazily initialize and return SQLAlchemy database engine."""
    global _engine
    if _engine is None:
        cfg = get_config()
        db_url = cfg.database_url

        # Ensure parent directory exists for SQLite database files
        if db_url.startswith("sqlite:///"):
            raw_path = db_url.replace("sqlite:///", "")
            db_file = Path(raw_path)
            db_file.parent.mkdir(parents=True, exist_ok=True)

        connect_args = {"check_same_thread": False} if "sqlite" in db_url else {}
        _engine = create_engine(
            db_url,
            connect_args=connect_args,
            echo=False,
        )
        logger.info(f"Database engine initialized for {db_url}")
    return _engine


def __getattr__(name: str):
    if name == "engine":
        return get_engine()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def get_session_factory():
    """Lazily initialize and return SQLAlchemy session factory."""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
    return _SessionLocal


def SessionLocal() -> Session:
    """Instantiate a new database session."""
    factory = get_session_factory()
    return factory()


def get_db() -> Generator[Session, None, None]:
    """FastAPI Dependency for obtaining a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Initialize all database tables and seed baseline reference entities."""
    from ..models import entities  # noqa: F401
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    logger.info("Database schema initialized.")

    # Seed initial baseline data if database is empty
    with SessionLocal() as db:
        _seed_initial_data(db)


def _seed_initial_data(db: Session) -> None:
    """Seed default system user, standard targets, and weapon types if none exist."""
    from ..models.entities import User, Target, Weapon, ScoringPattern

    # 1. Default Admin / Instructor User
    existing_user = db.query(User).first()
    if not existing_user:
        admin_user = User(
            username="instructor",
            email="instructor@simulator.local",
            hashed_password="placeholder_hash_change_in_prod",
            role="instructor",
            is_active=True,
        )
        db.add(admin_user)
        logger.info("Seeded default instructor user.")

    # 2. Default Target
    existing_target = db.query(Target).first()
    if not existing_target:
        std_target = Target(
            name="ISSF 25m Precision",
            target_type="bullseye",
            width_mm=500.0,
            height_mm=500.0,
            rings_json='{"rings": [{"val": 10, "r_mm": 25}, {"val": 9, "r_mm": 50}, {"val": 8, "r_mm": 75}]}',
        )
        db.add(std_target)
        logger.info("Seeded default ISSF 25m target.")

    # 3. Default Weapon
    existing_weapon = db.query(Weapon).first()
    if not existing_weapon:
        std_weapon = Weapon(
            model_name="Glock 17 Gen5",
            caliber="9x19mm Parabellum",
            weapon_type="pistol",
            description="Standard service sidearm",
        )
        db.add(std_weapon)
        logger.info("Seeded default Glock 17 weapon platform.")

    # 4. Default Scoring Pattern
    existing_pattern = db.query(ScoringPattern).first()
    if not existing_pattern:
        std_pattern = ScoringPattern(
            name="Standard Bullseye 10-Ring",
            description="Standard qualification points with 10-ring bullseye",
            rules_json='{"max_score_per_shot": 10, "pass_percentage": 70.0}',
        )
        db.add(std_pattern)
        logger.info("Seeded default scoring pattern.")

    db.commit()


if __name__ == "__main__":
    init_db()
    print("Database tables initialized successfully.")
