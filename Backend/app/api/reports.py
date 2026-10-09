"""Report templates and session performance report generation endpoints."""

from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database.session import get_db
from ..models.entities import ReportTemplate

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/")
def list_reports(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    templates = db.query(ReportTemplate).all()
    return [
        {
            "id": t.id,
            "title": t.title,
            "template_type": t.template_type,
        }
        for t in templates
    ]
