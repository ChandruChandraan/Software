"""Firing session lifecycle and lane assignment endpoints."""

from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database.session import get_db
from ..models.entities import Session as DbSession, LaneAssignment
from ..schemas.common import SessionCreate

router = APIRouter(prefix="/sessions", tags=["Sessions"])


@router.get("/")
def list_sessions(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    sessions = db.query(DbSession).all()
    return [
        {
            "id": s.id,
            "session_code": s.session_code,
            "course_id": s.course_id,
            "status": s.status,
            "started_at": s.started_at.isoformat() if s.started_at else None,
            "ended_at": s.ended_at.isoformat() if s.ended_at else None,
        }
        for s in sessions
    ]


@router.post("/")
def create_session(payload: SessionCreate, db: Session = Depends(get_db)) -> Dict[str, Any]:
    session = DbSession(
        session_code=payload.session_code,
        course_id=payload.course_id,
        status="pending",
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return {"id": session.id, "session_code": session.session_code, "status": session.status}


@router.get("/{session_id}")
def get_session(session_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    session = db.query(DbSession).filter(DbSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {
        "id": session.id,
        "session_code": session.session_code,
        "course_id": session.course_id,
        "status": session.status,
    }
