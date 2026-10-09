"""System diagnostic and configuration endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database.session import get_db
from ..health import get_full_health
from ..config import get_config
from ..schemas.common import HealthResponse, LicenceResponse, SettingsResponse

router = APIRouter(prefix="/system", tags=["System"])


@router.get("/health", response_model=HealthResponse)
def get_health():
    """Retrieve operational health status of backend and database."""
    return get_full_health()


@router.get("/health/details")
def get_health_details():
    """Retrieve extended diagnostics including database and UDP listener."""
    from ..services.tracker_listener import tracker_listener
    health = get_full_health()
    health["udp_listener"] = tracker_listener.get_status()
    health["guns"] = tracker_listener.get_gun_states()
    return health


@router.get("/licence", response_model=LicenceResponse)
def get_licence():
    """Retrieve current software licence status (placeholder)."""
    return LicenceResponse(
        status="active",
        licence_type="Enterprise-Training",
        expiry_date="2099-12-31",
        seats=16,
    )


@router.get("/settings", response_model=SettingsResponse)
def get_settings():
    """Retrieve runtime settings and network parameters."""
    cfg = get_config()
    return SettingsResponse(
        app_name=cfg.app_name,
        version=cfg.version,
        udp_listen_port=cfg.udp_listen_port,
        camera_fps=120,
    )
