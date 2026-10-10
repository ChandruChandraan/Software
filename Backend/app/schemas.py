"""Pydantic data schemas for UDP packets, REST APIs, and WebSocket payloads."""

from typing import Dict, List, Literal, Optional, Any
from pydantic import BaseModel, Field


# ==============================================================================
# UDP Inbound Telemetry Schemas
# ==============================================================================


class ShotPacket(BaseModel):
    """Shot event telemetry sent by Tracker (UDP Port 47001)."""

    v: int = Field(default=1, description="Protocol version")
    type: Literal["shot"] = Field(default="shot", description="Packet type")
    gun: int = Field(..., ge=1, description="Gun identifier (1-based)")
    lane: int = Field(..., ge=1, description="Target lane identifier (1-based)")
    x: float = Field(..., description="Target aim X coordinate in pixels")
    y: float = Field(..., description="Target aim Y coordinate in pixels")
    display_width: int = Field(default=1920, ge=1, description="Display resolution width")
    display_height: int = Field(default=1080, ge=1, description="Display resolution height")
    round: int = Field(default=1, ge=1, description="Round/shot counter for this gun")
    cross_lane: bool = Field(default=False, description="Whether shot targeted another lane")
    time_us: Optional[int] = Field(default=None, description="Microsecond timestamp")


class GunStatusPacket(BaseModel):
    """Gun status keepalive/state event sent by Tracker (UDP Port 47001)."""

    v: int = Field(default=1, description="Protocol version")
    type: Literal["gun_status"] = Field(default="gun_status", description="Packet type")
    gun: int = Field(..., ge=1, description="Gun identifier (1-based)")
    lane: int = Field(..., ge=1, description="Assigned lane (1-based)")
    port: Optional[str] = Field(default=None, description="Serial COM port or virtual SIM port")
    connected: bool = Field(..., description="Whether gun hardware is currently connected")
    shot_count: int = Field(default=0, ge=0, description="Total shots registered by this gun")
    time_us: Optional[int] = Field(default=None, description="Microsecond timestamp")


# ==============================================================================
# State and API Response Models
# ==============================================================================


class GunStateModel(BaseModel):
    """Complete backend in-memory state of a single gun."""

    gun_id: int
    lane: int
    port: Optional[str] = None
    connected: bool = False
    shot_count: int = 0
    last_seen: Optional[float] = None
    last_shot_time: Optional[float] = None
    last_shot_coords: Optional[Dict[str, float]] = None


class HealthResponse(BaseModel):
    """Basic health status response."""

    status: str = "ok"
    uptime_seconds: float
    version: str
    timestamp: str


class UDPListenerStatus(BaseModel):
    """UDP listener operational status."""

    status: str  # "listening", "stopped", "error"
    host: str
    port: int
    packets_received: int
    invalid_packets: int
    last_packet_time: Optional[float] = None


class TrackerProcessStatus(BaseModel):
    """Tracker OS process management status."""

    running: bool
    pid: Optional[int] = None
    mode: str
    target_path: str
    path_exists: bool
    uptime_seconds: Optional[float] = None
    exit_code: Optional[int] = None
    restart_count: int = 0
    last_error: Optional[str] = None


class TrackerTelemetryStatus(BaseModel):
    """Tracker telemetry freshness and data statistics."""

    freshness: Literal["connected", "stale", "disconnected"]
    last_valid_event_time: Optional[float] = None
    seconds_since_last_event: Optional[float] = None
    connected_guns: int = 0
    total_guns: int = 0
    total_shots: int = 0


class HealthDetailsResponse(BaseModel):
    """Comprehensive system health and state diagnostics."""

    status: str = "ok"
    uptime_seconds: float
    backend_host: str
    backend_port: int
    udp_listener: UDPListenerStatus
    tracker_process: TrackerProcessStatus
    tracker_telemetry: TrackerTelemetryStatus


class TrackerStatusResponse(BaseModel):
    """Tracker full status for dashboard and APIs."""

    process: TrackerProcessStatus
    telemetry: TrackerTelemetryStatus
    guns: List[GunStateModel]


class TrackerActionResponse(BaseModel):
    """Response returned by process start/stop/restart endpoints."""

    success: bool
    message: str
    status: TrackerProcessStatus


class DisplayInfoModel(BaseModel):
    """Physical monitor or projector metadata."""

    index: int
    name: str
    x: int
    y: int
    width: int
    height: int
    is_primary: bool


class UnrealStatusModel(BaseModel):
    """Unreal Engine process state and executable metadata."""

    is_running: bool
    pid: Optional[int] = None
    exe_path: str
    exe_exists: bool


class OverlayStatusModel(BaseModel):
    """Projector reticle overlay window state."""

    is_running: bool
    pid: Optional[int] = None
    target_display: Optional[int] = None
    target_resolution: Optional[str] = None
    active_identity: Optional[str] = None

