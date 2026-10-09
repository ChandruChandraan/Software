"""Trainee management endpoints."""

from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database.session import get_db
from ..models.entities import Trainee
from ..schemas.common import TraineeCreate

router = APIRouter(prefix="/trainees", tags=["Trainees"])


@router.get("/")
def list_trainees(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """List registered trainees."""
    trainees = db.query(Trainee).all()
    return [
        {
            "id": t.id,
            "service_number": t.service_number,
            "first_name": t.first_name,
            "last_name": t.last_name,
            "rank": t.rank,
            "group_id": t.group_id,
            "notes": t.notes,
        }
        for t in trainees
    ]


@router.post("/")
def create_trainee(payload: TraineeCreate, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Register a new trainee."""
    trainee = Trainee(
        service_number=payload.service_number,
        first_name=payload.first_name,
        last_name=payload.last_name,
        rank=payload.rank,
        group_id=payload.group_id,
        notes=payload.notes,
    )
    db.add(trainee)
    db.commit()
    db.refresh(trainee)
    return {
        "id": trainee.id,
        "service_number": trainee.service_number,
        "first_name": trainee.first_name,
        "last_name": trainee.last_name,
        "rank": trainee.rank,
    }
