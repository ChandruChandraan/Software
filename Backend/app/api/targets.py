"""Target geometry and scoring patterns endpoints."""

from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database.session import get_db
from ..models.entities import Target, ScoringPattern
from ..schemas.common import TargetCreate, ScoringPatternCreate

router = APIRouter(tags=["Targets & Scoring"])


@router.get("/targets")
def list_targets(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    targets = db.query(Target).all()
    return [
        {
            "id": t.id,
            "name": t.name,
            "target_type": t.target_type,
            "width_mm": t.width_mm,
            "height_mm": t.height_mm,
            "rings_json": t.rings_json,
        }
        for t in targets
    ]


@router.post("/targets")
def create_target(payload: TargetCreate, db: Session = Depends(get_db)) -> Dict[str, Any]:
    t = Target(
        name=payload.name,
        target_type=payload.target_type,
        width_mm=payload.width_mm,
        height_mm=payload.height_mm,
        rings_json=payload.rings_json,
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return {"id": t.id, "name": t.name}


@router.get("/scoring-patterns")
def list_scoring_patterns(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    patterns = db.query(ScoringPattern).all()
    return [
        {
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "rules_json": p.rules_json,
        }
        for p in patterns
    ]


@router.post("/scoring-patterns")
def create_scoring_pattern(payload: ScoringPatternCreate, db: Session = Depends(get_db)) -> Dict[str, Any]:
    p = ScoringPattern(
        name=payload.name,
        description=payload.description,
        rules_json=payload.rules_json,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return {"id": p.id, "name": p.name}
