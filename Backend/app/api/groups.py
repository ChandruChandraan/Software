"""Group / squad management endpoints."""

from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database.session import get_db
from ..models.entities import Group
from ..schemas.common import GroupCreate

router = APIRouter(prefix="/groups", tags=["Groups"])


@router.get("/")
def list_groups(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    groups = db.query(Group).all()
    return [{"id": g.id, "name": g.name, "description": g.description} for g in groups]


@router.post("/")
def create_group(payload: GroupCreate, db: Session = Depends(get_db)) -> Dict[str, Any]:
    grp = Group(name=payload.name, description=payload.description)
    db.add(grp)
    db.commit()
    db.refresh(grp)
    return {"id": grp.id, "name": grp.name}
