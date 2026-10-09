from app.database.session import init_db, SessionLocal, get_engine
from app.models.entities import User, Trainee, Weapon, Target, Session as DbSession
from sqlalchemy import text


def test_db_initialization():
    init_db()
    with SessionLocal() as db:
        result = db.execute(text("SELECT 1")).scalar()
        assert result == 1


def test_db_create_and_query_trainee():
    init_db()
    with SessionLocal() as db:
        # Check creating a trainee record
        test_sn = "SN-TEST-9999"
        existing = db.query(Trainee).filter(Trainee.service_number == test_sn).first()
        if not existing:
            trainee = Trainee(
                service_number=test_sn,
                first_name="John",
                last_name="Doe",
                rank="Corporal",
            )
            db.add(trainee)
            db.commit()

        retrieved = db.query(Trainee).filter(Trainee.service_number == test_sn).first()
        assert retrieved is not None
        assert retrieved.first_name == "John"
        assert retrieved.rank == "Corporal"


def test_seeded_baseline_data():
    init_db()
    with SessionLocal() as db:
        user = db.query(User).filter(User.username == "instructor").first()
        assert user is not None
        assert user.role == "instructor"

        target = db.query(Target).first()
        assert target is not None
        assert target.target_type == "bullseye"

        weapon = db.query(Weapon).first()
        assert weapon is not None
        assert weapon.model_name == "Glock 17 Gen5"


def test_all_17_models_tables_exist():
    """Verify that all 17 database model tables exist in SQLite metadata."""
    from app.models.entities import (
        User, Trainee, Group, Weapon, Gun, Target, ScoringPattern,
        Exercise, RangeCourse, Scenario3D, VideoScenario, Calibration,
        Session, LaneAssignment, Shot, AimTrace, ReportTemplate,
    )
    init_db()
    with SessionLocal() as db:
        models = [
            User, Trainee, Group, Weapon, Gun, Target, ScoringPattern,
            Exercise, RangeCourse, Scenario3D, VideoScenario, Calibration,
            Session, LaneAssignment, Shot, AimTrace, ReportTemplate,
        ]
        assert len(models) == 17
        for m in models:
            # Query each table to verify it exists and is queryable without error
            _ = db.query(m).limit(1).all()
