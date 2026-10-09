"""3D Unreal environments and branching video scenarios endpoints."""

from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database.session import get_db
from ..models.entities import Scenario3D, VideoScenario
from ..schemas.common import Scenario3DCreate, VideoScenarioCreate

router = APIRouter(prefix="/scenarios", tags=["Scenarios"])


@router.get("/3d")
def list_3d_scenarios(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    scenarios = db.query(Scenario3D).all()
    return [
        {
            "id": s.id,
            "title": s.title,
            "map_name": s.map_name,
            "time_of_day": s.time_of_day,
            "weather": s.weather,
            "target_count": s.target_count,
            "difficulty": s.difficulty,
        }
        for s in scenarios
    ]


@router.post("/3d")
def create_3d_scenario(payload: Scenario3DCreate, db: Session = Depends(get_db)) -> Dict[str, Any]:
    s = Scenario3D(
        title=payload.title,
        map_name=payload.map_name,
        time_of_day=payload.time_of_day,
        weather=payload.weather,
        target_count=payload.target_count,
        difficulty=payload.difficulty,
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return {"id": s.id, "title": s.title}


@router.get("/video")
def list_video_scenarios(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    scenarios = db.query(VideoScenario).all()
    return [
        {
            "id": v.id,
            "title": v.title,
            "video_file_path": v.video_file_path,
            "duration_sec": v.duration_sec,
        }
        for v in scenarios
    ]


@router.post("/video")
def create_video_scenario(payload: VideoScenarioCreate, db: Session = Depends(get_db)) -> Dict[str, Any]:
    v = VideoScenario(
        title=payload.title,
        video_file_path=payload.video_file_path,
        duration_sec=payload.duration_sec,
        branch_points_json=payload.branch_points_json,
    )
    db.add(v)
    db.commit()
    db.refresh(v)
    return {"id": v.id, "title": v.title}
