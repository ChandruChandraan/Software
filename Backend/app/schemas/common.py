"""Pydantic schemas for REST API and WebSocket payloads."""

from typing import Optional, Any, Dict, List
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = "backend"
    database: str = "ok"


class LicenceResponse(BaseModel):
    status: str = "active"
    licence_type: str = "Enterprise-Training"
    expiry_date: str = "2099-12-31"
    seats: int = 16


class SettingsResponse(BaseModel):
    app_name: str
    version: str
    udp_listen_port: int
    camera_fps: int = 120


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    role: str


class TraineeCreate(BaseModel):
    service_number: str
    first_name: str
    last_name: str
    rank: str = "Private"
    group_id: Optional[int] = None
    notes: Optional[str] = None


class GroupCreate(BaseModel):
    name: str
    description: Optional[str] = None


class WeaponCreate(BaseModel):
    model_name: str
    caliber: str
    weapon_type: str = "pistol"
    description: Optional[str] = None


class GunCreate(BaseModel):
    serial_number: str
    weapon_id: int
    hardware_id: Optional[str] = None


class TargetCreate(BaseModel):
    name: str
    target_type: str = "bullseye"
    width_mm: float = 500.0
    height_mm: float = 500.0
    rings_json: Optional[str] = None


class ScoringPatternCreate(BaseModel):
    name: str
    description: Optional[str] = None
    rules_json: str = "{}"


class ExerciseCreate(BaseModel):
    title: str
    description: Optional[str] = None
    time_limit_sec: int = 60
    target_id: Optional[int] = None
    scoring_pattern_id: Optional[int] = None
    distance_m: float = 25.0
    shots_allowed: int = 10


class CourseCreate(BaseModel):
    title: str
    description: Optional[str] = None
    exercise_ids_json: str = "[]"
    stage_count: int = 1


class Scenario3DCreate(BaseModel):
    title: str
    map_name: str
    time_of_day: str = "day"
    weather: str = "clear"
    target_count: int = 5
    difficulty: str = "standard"


class VideoScenarioCreate(BaseModel):
    title: str
    video_file_path: str
    duration_sec: float = 0.0
    branch_points_json: str = "[]"


class CalibrationScreenUpdate(BaseModel):
    screen_matrix_json: str


class CalibrationWeaponUpdate(BaseModel):
    weapon_id: int
    offset_json: str


class SessionCreate(BaseModel):
    session_code: str
    course_id: Optional[int] = None
