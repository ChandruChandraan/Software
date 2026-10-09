"""Screen homography and weapon offset calibration endpoints."""

from typing import Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database.session import get_db
from ..models.entities import Calibration
from ..schemas.common import CalibrationScreenUpdate, CalibrationWeaponUpdate

router = APIRouter(prefix="/calibration", tags=["Calibration"])


@router.get("/screen")
def get_screen_calibration(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Retrieve latest screen 4-point homography calibration."""
    cal = db.query(Calibration).filter(Calibration.calibration_type == "screen").order_by(Calibration.id.desc()).first()
    if cal:
        return {"status": "calibrated", "screen_matrix": cal.screen_matrix_json}
    return {
        "status": "uncalibrated",
        "screen_matrix": "[[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]",
    }


@router.post("/screen")
def update_screen_calibration(payload: CalibrationScreenUpdate, db: Session = Depends(get_db)) -> Dict[str, Any]:
    cal = Calibration(
        calibration_type="screen",
        screen_matrix_json=payload.screen_matrix_json,
    )
    db.add(cal)
    db.commit()
    db.refresh(cal)
    return {"status": "saved", "id": cal.id}


@router.get("/weapon")
def get_weapon_calibration(db: Session = Depends(get_db)) -> Dict[str, Any]:
    cal = db.query(Calibration).filter(Calibration.calibration_type == "weapon").order_by(Calibration.id.desc()).first()
    return {
        "status": "calibrated" if cal else "default",
        "weapon_offset": cal.weapon_offset_json if cal else "{\"x_offset\": 0.0, \"y_offset\": 0.0}",
    }


@router.post("/weapon")
def update_weapon_calibration(payload: CalibrationWeaponUpdate, db: Session = Depends(get_db)) -> Dict[str, Any]:
    cal = Calibration(
        calibration_type="weapon",
        weapon_offset_json=payload.offset_json,
    )
    db.add(cal)
    db.commit()
    db.refresh(cal)
    return {"status": "saved", "id": cal.id}
