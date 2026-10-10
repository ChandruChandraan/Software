"""Tracker process control and gun telemetry endpoints."""

from typing import List, Dict, Any
from fastapi import APIRouter, Request, HTTPException, status

from app.schemas import (
    TrackerStatusResponse,
    GunStateModel,
    TrackerActionResponse,
)

router = APIRouter(prefix="/api/tracker", tags=["Tracker"])


def verify_local_access(request: Request):
    """Enforces localhost-only access for process control when configured."""
    settings = request.app.state.settings
    if settings.LOCAL_ONLY_MANAGEMENT:
        client_host = request.client.host if request.client else ""
        # Accept localhost IPv4, IPv6, and Starlette TestClient
        if client_host not in ("127.0.0.1", "::1", "localhost", "testclient"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tracker process management is restricted to localhost.",
            )


@router.get("/status", response_model=TrackerStatusResponse)
async def get_tracker_status(request: Request):
    """Returns combined status of the Tracker process and incoming telemetry."""
    state = request.app.state.tracker_state
    proc_mgr = request.app.state.process_manager

    return TrackerStatusResponse(
        process=proc_mgr.get_status(),
        telemetry=state.get_telemetry_status(),
        guns=state.get_all_guns(),
    )


@router.get("/guns", response_model=List[GunStateModel])
async def get_tracker_guns(request: Request):
    """Returns list of currently registered simulator guns and their latest state."""
    state = request.app.state.tracker_state
    return state.get_all_guns()


@router.get("/events")
async def get_recent_events(request: Request):
    """Returns recent valid telemetry events (shots and gun status)."""
    state = request.app.state.tracker_state
    return list(state.recent_events)


@router.post("/clear-events")
async def clear_events(request: Request):
    """Clears the live event log buffer."""
    state = request.app.state.tracker_state
    state.clear_recent_events()
    return {"status": "ok", "message": "Event history cleared"}


@router.get("/logs")
async def get_tracker_logs(request: Request, limit: int = 100):
    """Returns recent stdout/stderr lines from the managed Tracker process."""
    proc_mgr = request.app.state.process_manager
    return proc_mgr.get_recent_logs(limit)


@router.post("/start", response_model=TrackerActionResponse)
async def start_tracker_process(request: Request):
    """Starts the configured Tracker process if not already running."""
    verify_local_access(request)
    proc_mgr = request.app.state.process_manager

    success, message = await proc_mgr.start_tracker()
    status_data = proc_mgr.get_status()

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"success": False, "message": message, "status": status_data.model_dump()},
        )

    return TrackerActionResponse(
        success=True,
        message=message,
        status=status_data,
    )


@router.post("/stop", response_model=TrackerActionResponse)
async def stop_tracker_process(request: Request):
    """Gracefully terminates only the Tracker process owned by this backend."""
    verify_local_access(request)
    proc_mgr = request.app.state.process_manager

    success, message = await proc_mgr.stop_tracker()
    status_data = proc_mgr.get_status()

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"success": False, "message": message, "status": status_data.model_dump()},
        )

    return TrackerActionResponse(
        success=True,
        message=message,
        status=status_data,
    )


@router.post("/restart", response_model=TrackerActionResponse)
async def restart_tracker_process(request: Request):
    """Restarts the configured Tracker process."""
    verify_local_access(request)
    proc_mgr = request.app.state.process_manager

    success, message = await proc_mgr.restart_tracker()
    status_data = proc_mgr.get_status()

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"success": False, "message": message, "status": status_data.model_dump()},
        )

    return TrackerActionResponse(
        success=True,
        message=message,
        status=status_data,
    )
