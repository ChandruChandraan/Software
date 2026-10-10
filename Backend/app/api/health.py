"""Health and system diagnostics endpoints."""

from datetime import datetime, timezone
from fastapi import APIRouter, Request

from app import __version__
from app.schemas import HealthResponse, HealthDetailsResponse

router = APIRouter(prefix="/api/health", tags=["Health"])


@router.get("", response_model=HealthResponse)
async def get_health(request: Request):
    """Returns basic backend health and uptime."""
    state = request.app.state.tracker_state
    return HealthResponse(
        status="ok",
        uptime_seconds=state.get_uptime_seconds(),
        version=__version__,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@router.get("/details", response_model=HealthDetailsResponse)
async def get_health_details(request: Request):
    """Returns detailed operational status of listener, process manager, and telemetry."""
    state = request.app.state.tracker_state
    listener = request.app.state.udp_listener
    proc_mgr = request.app.state.process_manager
    cfg = request.app.state.settings

    return HealthDetailsResponse(
        status="ok",
        uptime_seconds=state.get_uptime_seconds(),
        backend_host=cfg.BACKEND_HOST,
        backend_port=cfg.BACKEND_PORT,
        udp_listener=listener.get_status(),
        tracker_process=proc_mgr.get_status(),
        tracker_telemetry=state.get_telemetry_status(),
    )
