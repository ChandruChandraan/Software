"""Exercise definition and course management endpoints."""

from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database.session import get_db
from ..models.entities import Exercise, RangeCourse
from ..schemas.common import ExerciseCreate, CourseCreate

router = APIRouter(tags=["Exercises & Courses"])


@router.get("/exercises")
def list_exercises(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    exercises = db.query(Exercise).all()
    return [
        {
            "id": ex.id,
            "title": ex.title,
            "description": ex.description,
            "time_limit_sec": ex.time_limit_sec,
            "distance_m": ex.distance_m,
            "shots_allowed": ex.shots_allowed,
        }
        for ex in exercises
    ]


@router.post("/exercises")
def create_exercise(payload: ExerciseCreate, db: Session = Depends(get_db)) -> Dict[str, Any]:
    ex = Exercise(
        title=payload.title,
        description=payload.description,
        time_limit_sec=payload.time_limit_sec,
        target_id=payload.target_id,
        scoring_pattern_id=payload.scoring_pattern_id,
        distance_m=payload.distance_m,
        shots_allowed=payload.shots_allowed,
    )
    db.add(ex)
    db.commit()
    db.refresh(ex)
    return {"id": ex.id, "title": ex.title}


@router.get("/courses")
def list_courses(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    courses = db.query(RangeCourse).all()
    return [
        {
            "id": c.id,
            "title": c.title,
            "description": c.description,
            "stage_count": c.stage_count,
        }
        for c in courses
    ]


@router.post("/courses")
def create_course(payload: CourseCreate, db: Session = Depends(get_db)) -> Dict[str, Any]:
    c = RangeCourse(
        title=payload.title,
        description=payload.description,
        exercise_ids_json=payload.exercise_ids_json,
        stage_count=payload.stage_count,
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return {"id": c.id, "title": c.title}
