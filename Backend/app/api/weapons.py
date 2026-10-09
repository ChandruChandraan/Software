"""Weapon model and physical gun registry endpoints."""

from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database.session import get_db
from ..models.entities import Weapon, Gun
from ..schemas.common import WeaponCreate, GunCreate

router = APIRouter(tags=["Weapons & Guns"])


@router.get("/weapons")
def list_weapons(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    weapons = db.query(Weapon).all()
    return [
        {
            "id": w.id,
            "model_name": w.model_name,
            "caliber": w.caliber,
            "weapon_type": w.weapon_type,
            "description": w.description,
        }
        for w in weapons
    ]


@router.post("/weapons")
def create_weapon(payload: WeaponCreate, db: Session = Depends(get_db)) -> Dict[str, Any]:
    w = Weapon(
        model_name=payload.model_name,
        caliber=payload.caliber,
        weapon_type=payload.weapon_type,
        description=payload.description,
    )
    db.add(w)
    db.commit()
    db.refresh(w)
    return {"id": w.id, "model_name": w.model_name}


@router.get("/guns")
def list_guns(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    guns = db.query(Gun).all()
    return [
        {
            "id": g.id,
            "serial_number": g.serial_number,
            "weapon_id": g.weapon_id,
            "hardware_id": g.hardware_id,
            "status": g.status,
            "battery_level": g.battery_level,
        }
        for g in guns
    ]


@router.post("/guns")
def create_gun(payload: GunCreate, db: Session = Depends(get_db)) -> Dict[str, Any]:
    gun = Gun(
        serial_number=payload.serial_number,
        weapon_id=payload.weapon_id,
        hardware_id=payload.hardware_id,
    )
    db.add(gun)
    db.commit()
    db.refresh(gun)
    return {"id": gun.id, "serial_number": gun.serial_number}
