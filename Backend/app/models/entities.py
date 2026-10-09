"""Database models for Firing Training Simulator."""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import (
    Integer,
    String,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database.base import Base


class User(Base):
    """System operator, instructor, or administrator."""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(256), nullable=False)
    role: Mapped[str] = mapped_column(String(32), default="instructor")  # admin, instructor, viewer
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


class Group(Base):
    """Organizational squadron, squad, or trainee batch."""
    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    trainees: Mapped[list["Trainee"]] = relationship("Trainee", back_populates="group")


class Trainee(Base):
    """Individual undergoing marksmanship training."""
    __tablename__ = "trainees"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    service_number: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    first_name: Mapped[str] = mapped_column(String(64), nullable=False)
    last_name: Mapped[str] = mapped_column(String(64), nullable=False)
    rank: Mapped[str] = mapped_column(String(32), default="Private")
    group_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("groups.id"), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    group: Mapped[Optional["Group"]] = relationship("Group", back_populates="trainees")


class Weapon(Base):
    """Weapon model specifications (e.g. Glock 17, AK-47, M4A1)."""
    __tablename__ = "weapons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    model_name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    caliber: Mapped[str] = mapped_column(String(32), nullable=False)
    weapon_type: Mapped[str] = mapped_column(String(32), default="pistol")  # pistol, rifle, carbine
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    guns: Mapped[list["Gun"]] = relationship("Gun", back_populates="weapon")


class Gun(Base):
    """Physical laser/recoil training weapon unit assigned to a lane."""
    __tablename__ = "guns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    serial_number: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    weapon_id: Mapped[int] = mapped_column(Integer, ForeignKey("weapons.id"), nullable=False)
    hardware_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="ready")  # ready, in_use, offline, maintenance
    battery_level: Mapped[float] = mapped_column(Float, default=100.0)
    last_calibrated: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    weapon: Mapped["Weapon"] = relationship("Weapon", back_populates="guns")


class Target(Base):
    """Target configuration (dimensions, rings, scoring zones)."""
    __tablename__ = "targets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    target_type: Mapped[str] = mapped_column(String(32), default="bullseye")  # bullseye, silhouette, steel, popper
    width_mm: Mapped[float] = mapped_column(Float, default=500.0)
    height_mm: Mapped[float] = mapped_column(Float, default=500.0)
    rings_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    texture_path: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)


class ScoringPattern(Base):
    """Scoring pattern rules and point valuations."""
    __tablename__ = "scoring_patterns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rules_json: Mapped[str] = mapped_column(Text, default="{}")


class Exercise(Base):
    """Individual firing exercise definition."""
    __tablename__ = "exercises"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    time_limit_sec: Mapped[int] = mapped_column(Integer, default=60)
    target_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("targets.id"), nullable=True)
    scoring_pattern_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("scoring_patterns.id"), nullable=True)
    distance_m: Mapped[float] = mapped_column(Float, default=25.0)
    shots_allowed: Mapped[int] = mapped_column(Integer, default=10)


class RangeCourse(Base):
    """Composite qualification course consisting of multiple exercises."""
    __tablename__ = "range_courses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    exercise_ids_json: Mapped[str] = mapped_column(Text, default="[]")
    stage_count: Mapped[int] = mapped_column(Integer, default=1)


class Scenario3D(Base):
    """Unreal Engine 3D virtual firing range or tactical environment."""
    __tablename__ = "scenarios_3d"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    map_name: Mapped[str] = mapped_column(String(128), nullable=False)
    time_of_day: Mapped[str] = mapped_column(String(32), default="day")  # day, dusk, night
    weather: Mapped[str] = mapped_column(String(32), default="clear")  # clear, rain, fog
    target_count: Mapped[int] = mapped_column(Integer, default=5)
    difficulty: Mapped[str] = mapped_column(String(32), default="standard")


class VideoScenario(Base):
    """Branching video-based judgmental shoot/don't shoot scenario."""
    __tablename__ = "video_scenarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    video_file_path: Mapped[str] = mapped_column(String(256), nullable=False)
    duration_sec: Mapped[float] = mapped_column(Float, default=0.0)
    branch_points_json: Mapped[str] = mapped_column(Text, default="[]")


class Calibration(Base):
    """Display screen homography and weapon optical calibration presets."""
    __tablename__ = "calibrations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    calibration_type: Mapped[str] = mapped_column(String(32), default="screen")  # screen, weapon
    screen_matrix_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    weapon_offset_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


class Session(Base):
    """Active or archived marksmanship training session."""
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_code: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    course_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("range_courses.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="pending")  # pending, active, paused, completed
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    instructor_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)


class LaneAssignment(Base):
    """Binding between firing lane, trainee, and weapon in a session."""
    __tablename__ = "lane_assignments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(Integer, ForeignKey("sessions.id"), nullable=False)
    lane_number: Mapped[int] = mapped_column(Integer, nullable=False)
    trainee_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("trainees.id"), nullable=True)
    gun_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("guns.id"), nullable=True)


class Shot(Base):
    """Discrete shot placement record with coordinates, time, and score."""
    __tablename__ = "shots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(Integer, ForeignKey("sessions.id"), nullable=False)
    lane_number: Mapped[int] = mapped_column(Integer, nullable=False)
    trainee_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("trainees.id"), nullable=True)
    x: Mapped[float] = mapped_column(Float, nullable=False)
    y: Mapped[float] = mapped_column(Float, nullable=False)
    timestamp_us: Mapped[int] = mapped_column(Integer, nullable=False)
    score: Mapped[float] = mapped_column(Float, default=0.0)
    is_hit: Mapped[bool] = mapped_column(Boolean, default=False)
    ring_value: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)


class AimTrace(Base):
    """Serialized high-rate aim point trajectory segment for shot review/replay."""
    __tablename__ = "aim_traces"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(Integer, ForeignKey("sessions.id"), nullable=False)
    lane_number: Mapped[int] = mapped_column(Integer, nullable=False)
    points_json: Mapped[str] = mapped_column(Text, nullable=False)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    start_time_us: Mapped[int] = mapped_column(Integer, default=0)


class ReportTemplate(Base):
    """Printable or exportable performance report template configuration."""
    __tablename__ = "report_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    template_type: Mapped[str] = mapped_column(String(32), default="standard_qualification")
    layout_json: Mapped[str] = mapped_column(Text, default="{}")
