"""Tracker process control and gun telemetry endpoints."""

from typing import List, Dict, Any, Optional
from pathlib import Path
import os
import sys
import threading
import time
from fastapi import APIRouter, Request, HTTPException, status

from app.schemas import (
    TrackerStatusResponse,
    GunStateModel,
    TrackerActionResponse,
    DisplayInfoModel,
    UnrealStatusModel,
    OverlayStatusModel,
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


@router.post("/reset-shots")
async def reset_tracker_shots(request: Request):
    """Resets all gun shot counters and total shots to zero, broadcasting update to all clients."""
    state = request.app.state.tracker_state
    state.reset_shots()
    ws_mgr = getattr(request.app.state, "ws_manager", None)
    if ws_mgr:
        await ws_mgr.broadcast(
            topic="shot_counters_reset",
            data={
                "total_shots": 0,
                "guns": [g.model_dump() for g in state.get_all_guns()],
            },
        )
    return {"status": "ok", "message": "Gun Fire Shots and shot counters reset to zero", "total_shots": 0}


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


# ==============================================================================
# Displays & Monitor Detection
# ==============================================================================


@router.get("/displays", response_model=List[DisplayInfoModel])
async def get_displays():
    """Returns detected physical monitors and projectors."""
    from app.services.simulation_services import DisplayService
    return DisplayService.get_displays()


# ==============================================================================
# Unreal Engine Simulation Control
# ==============================================================================


@router.get("/unreal/status", response_model=UnrealStatusModel)
async def get_unreal_status(request: Request):
    """Returns Unreal Engine process running state and executable path."""
    unreal_service = getattr(request.app.state, "unreal_service", None)
    if not unreal_service:
        from app.services.simulation_services import UnrealService
        unreal_service = UnrealService(ws_manager=request.app.state.ws_manager)
    return unreal_service.get_status()


@router.post("/unreal/start")
async def start_unreal(request: Request, display: Optional[int] = None):
    """Launches Unreal Engine on designated display (default: secondary/projector)."""
    verify_local_access(request)
    unreal_service = getattr(request.app.state, "unreal_service", None)
    if not unreal_service:
        from app.services.simulation_services import UnrealService
        unreal_service = UnrealService(ws_manager=request.app.state.ws_manager)

    success, msg = await unreal_service.start(display_index=display)
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)
    return {"success": True, "message": msg, "status": unreal_service.get_status()}


@router.post("/unreal/stop")
async def stop_unreal(request: Request):
    """Terminates project-bound Unreal Engine game instances."""
    verify_local_access(request)
    unreal_service = getattr(request.app.state, "unreal_service", None)
    if not unreal_service:
        from app.services.simulation_services import UnrealService
        unreal_service = UnrealService(ws_manager=request.app.state.ws_manager)

    success, msg = await unreal_service.stop()
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)
    return {"success": True, "message": msg, "status": unreal_service.get_status()}


# ==============================================================================
# Projector Reticle Overlay Control
# ==============================================================================


@router.get("/overlay/status", response_model=OverlayStatusModel)
async def get_overlay_status(request: Request):
    """Returns Projector Overlay window status."""
    overlay_service = getattr(request.app.state, "overlay_service", None)
    if not overlay_service:
        from app.services.simulation_services import OverlayService
        from app.config import BASE_DIR
        overlay_service = OverlayService(
            ws_manager=request.app.state.ws_manager,
            tracker_dir=BASE_DIR.parent / "Tracker",
            python_exe=Path(request.app.state.settings.TRACKER_PYTHON_PATH or sys.executable),
        )
    return overlay_service.get_status()


@router.post("/overlay/start")
async def start_overlay(request: Request):
    """Launches Projector Reticle Overlay on the projector display."""
    verify_local_access(request)
    overlay_service = getattr(request.app.state, "overlay_service", None)
    if not overlay_service:
        from app.services.simulation_services import OverlayService
        from app.config import BASE_DIR
        overlay_service = OverlayService(
            ws_manager=request.app.state.ws_manager,
            tracker_dir=BASE_DIR.parent / "Tracker",
            python_exe=Path(request.app.state.settings.TRACKER_PYTHON_PATH or sys.executable),
        )

    success, msg = await overlay_service.start()
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)
    return {"success": True, "message": msg, "status": overlay_service.get_status()}


@router.post("/overlay/stop")
async def stop_overlay(request: Request):
    """Closes the Projector Reticle Overlay window."""
    verify_local_access(request)
    overlay_service = getattr(request.app.state, "overlay_service", None)
    if not overlay_service:
        from app.services.simulation_services import OverlayService
        from app.config import BASE_DIR
        overlay_service = OverlayService(
            ws_manager=request.app.state.ws_manager,
            tracker_dir=BASE_DIR.parent / "Tracker",
            python_exe=Path(request.app.state.settings.TRACKER_PYTHON_PATH or sys.executable),
        )

    success, msg = await overlay_service.stop()
    return {"success": success, "message": msg, "status": overlay_service.get_status()}


@router.post("/all/stop")
async def stop_all_simulations(request: Request):
    """Closes all active simulation components: Projector Overlay, Unreal Engine, and Tracker."""
    verify_local_access(request)
    results = {}

    # 1. Stop Projector Overlay
    overlay_service = getattr(request.app.state, "overlay_service", None)
    if overlay_service:
        try:
            success, msg = await overlay_service.stop()
            results["overlay"] = {"success": success, "message": msg}
        except Exception as e:
            results["overlay"] = {"success": False, "message": str(e)}

    # 2. Stop Unreal Engine
    unreal_service = getattr(request.app.state, "unreal_service", None)
    if unreal_service:
        try:
            success, msg = await unreal_service.stop()
            results["unreal"] = {"success": success, "message": msg}
        except Exception as e:
            results["unreal"] = {"success": False, "message": str(e)}

    # 3. Stop Tracker process
    proc_mgr = getattr(request.app.state, "process_manager", None)
    if proc_mgr and proc_mgr.is_running():
        try:
            success, msg = await proc_mgr.stop_tracker()
            results["tracker"] = {"success": success, "message": msg}
        except Exception as e:
            results["tracker"] = {"success": False, "message": str(e)}

    return {"success": True, "message": "All simulation components closed", "results": results}


@router.post("/app/exit")
async def exit_application(request: Request):
    """Closes all simulation components and cleanly terminates the desktop application."""
    verify_local_access(request)
    
    # 1. Stop all simulation components
    try:
        await stop_all_simulations(request)
    except Exception:
        pass

    # 2. Schedule clean host process termination
    def _do_exit():
        time.sleep(0.3)
        try:
            sys.stdout.flush()
            sys.stderr.flush()
        except Exception:
            pass
        os._exit(0)

    threading.Thread(target=_do_exit, daemon=True).start()
    return {"success": True, "message": "Application terminating cleanly"}


