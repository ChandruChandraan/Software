"""FastAPI application main entry point with lifespan management."""

import asyncio
from contextlib import asynccontextmanager
import logging
from pathlib import Path
import sys
import time
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.health import router as health_router
from app.api.tracker import router as tracker_router
from app.api.scenarios import router as scenarios_router
from app.config import settings, BASE_DIR
from app.services.scenario_registry import ScenarioRegistry
from app.services.scenario_service import ScenarioService
from app.services.tracker_listener import TrackerUDPListener
from app.services.tracker_process import TrackerProcessManager
from app.services.tracker_state import TrackerState
from app.websocket.manager import ws_manager

# Configure root logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("backend.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI Lifespan:
    1. Initialize app state and services.
    2. Start UDP listener before starting Tracker.
    3. Verify UDP listener is ready.
    4. Auto-launch Tracker process if enabled.
    5. Wait up to timeout for initial telemetry without blocking API readiness.
    6. Gracefully stop Tracker, UDP listener, and background tasks on shutdown.
    """
    logger.info("Initializing FiringSim Backend services...")

    # 1. Initialize services
    active_settings = getattr(app.state, "settings", settings)
    tracker_state = getattr(
        app.state,
        "tracker_state",
        TrackerState(telemetry_timeout=active_settings.TRACKER_TELEMETRY_TIMEOUT),
    )
    tracker_state.reset_shots()

    tracker_dir = BASE_DIR.parent / "Tracker"
    root_venv_python = BASE_DIR.parent / ".venv" / "Scripts" / "python.exe"
    if not root_venv_python.exists():
        root_venv_python = Path(sys.executable)

    from app.services.simulation_services import UnrealService, OverlayService

    if not hasattr(app.state, "unreal_service") or app.state.unreal_service is None:
        unreal_service = UnrealService(
            ws_manager=ws_manager,
            exe_path=active_settings.UNREAL_EXE_PATH,
        )
    else:
        unreal_service = app.state.unreal_service

    if not hasattr(app.state, "overlay_service") or app.state.overlay_service is None:
        overlay_service = OverlayService(
            ws_manager=ws_manager,
            tracker_dir=tracker_dir,
            python_exe=root_venv_python,
        )
    else:
        overlay_service = app.state.overlay_service

    if not hasattr(app.state, "scenario_registry") or app.state.scenario_registry is None:
        scenario_registry = ScenarioRegistry(content_dir=active_settings.get_unreal_content_dir())
    else:
        scenario_registry = app.state.scenario_registry

    if not hasattr(app.state, "scenario_service") or app.state.scenario_service is None:
        scenario_service = ScenarioService(
            settings=active_settings,
            registry=scenario_registry,
            ws_manager=ws_manager,
            unreal_service=unreal_service,
        )
    else:
        scenario_service = app.state.scenario_service

    if not hasattr(app.state, "udp_listener") or app.state.udp_listener is None:
        udp_listener = TrackerUDPListener(
            host=active_settings.UDP_HOST,
            port=active_settings.UDP_PORT,
            state=tracker_state,
            ws_manager=ws_manager,
            scenario_service=scenario_service,
        )
    else:
        udp_listener = app.state.udp_listener

    if not hasattr(app.state, "process_manager") or app.state.process_manager is None:
        process_manager = TrackerProcessManager(
            settings=active_settings,
            ws_manager=ws_manager,
        )
    else:
        process_manager = app.state.process_manager

    # Attach to app.state
    app.state.settings = active_settings
    app.state.tracker_state = tracker_state
    app.state.udp_listener = udp_listener
    app.state.process_manager = process_manager
    app.state.ws_manager = getattr(app.state, "ws_manager", ws_manager)
    app.state.unreal_service = unreal_service
    app.state.overlay_service = overlay_service
    app.state.scenario_registry = scenario_registry
    app.state.scenario_service = scenario_service


    # 2. Start UDP listener
    udp_started = await udp_listener.start()
    if not udp_started:
        logger.error(f"UDP listener failed to bind on {active_settings.UDP_HOST}:{active_settings.UDP_PORT}")
    else:
        logger.info(f"UDP listener active on {active_settings.UDP_HOST}:{active_settings.UDP_PORT}")
        if getattr(scenario_service, "_udp_sender", None) == getattr(scenario_service, "_default_udp_sender", None):
            scenario_service.set_udp_sender(udp_listener.send_to)

    # 3. Autostart Tracker process if configured
    if active_settings.TRACKER_AUTOSTART:
        logger.info("Automatic Tracker launch enabled. Starting Tracker process...")
        started, msg = await process_manager.start_tracker()
        if started:
            logger.info(f"Tracker launched. Waiting up to {active_settings.TRACKER_STARTUP_TIMEOUT}s for initial telemetry...")
            start_wait = time.time()
            # Non-blocking wait for initial telemetry
            while (time.time() - start_wait) < active_settings.TRACKER_STARTUP_TIMEOUT:
                if tracker_state.last_valid_event_time is not None:
                    logger.info("Initial Tracker telemetry packet confirmed received!")
                    break
                await asyncio.sleep(0.2)
            else:
                logger.warning(
                    f"Tracker process is running, but no telemetry packet arrived within "
                    f"{active_settings.TRACKER_STARTUP_TIMEOUT}s. Backend remains operational."
                )
        else:
            logger.warning(f"Tracker autostart did not launch process: {msg}")

    # 4. Autostart Unreal Engine if configured
    if getattr(active_settings, "UNREAL_AUTOSTART", True):
        logger.info("Automatic Unreal Engine launch enabled. Starting Unreal Engine...")
        unreal_started, unreal_msg = await unreal_service.start()
        if unreal_started:
            logger.info(f"Unreal Engine autostart: {unreal_msg}")
        else:
            logger.warning(f"Unreal Engine autostart did not launch: {unreal_msg}")

    logger.info(f"Backend HTTP server ready at http://{settings.BACKEND_HOST}:{settings.BACKEND_PORT}")

    # Yield control to FastAPI request handling
    yield

    # Shutdown sequence
    logger.info("Shutting down FiringSim Backend...")

    # 1. Stop Projector Overlay if running or enabled
    try:
        is_overlay_running, _ = overlay_service.is_running()
        if is_overlay_running:
            logger.info("Stopping Projector Overlay on shutdown...")
            await overlay_service.stop()
    except Exception as e:
        logger.warning(f"Error closing overlay on shutdown: {e}")

    # 2. Stop Unreal Engine if running
    try:
        is_unreal_running, _ = unreal_service.is_running()
        if is_unreal_running:
            logger.info("Stopping Unreal Engine on shutdown...")
            await unreal_service.stop()
    except Exception as e:
        logger.warning(f"Error stopping Unreal Engine on shutdown: {e}")

    # 3. Stop child Tracker process
    if process_manager.is_running():
        logger.info("Stopping managed Tracker process...")
        await process_manager.stop_tracker()

    # 4. Close UDP listener
    await udp_listener.stop()

    # 5. Cancel pending scenario timers
    try:
        await scenario_service.shutdown()
    except Exception as e:
        logger.warning(f"Error shutting down scenario service: {e}")

    # 6. Close remaining WebSocket connections
    for client in list(ws_manager.active_connections):
        try:
            await client.close()
        except Exception:
            pass

    logger.info("Backend shutdown complete.")


# Instantiate FastAPI application
app = FastAPI(
    title="FiringSim Backend",
    description="Marksmanship Firing Simulator Backend and Tracker Process Coordinator",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(health_router)
app.include_router(tracker_router)
app.include_router(scenarios_router)


# WebSocket endpoint
@app.websocket("/ws/backend")
async def websocket_backend_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time dashboard events:
    Broadcasts shot events, gun statuses, process lifecycle, logs, and UDP errors.
    """
    await ws_manager.connect(websocket)
    # Send initial welcome payload
    try:
        await websocket.send_json(
            {
                "topic": "connection_established",
                "data": {
                    "backend_uptime": app.state.tracker_state.get_uptime_seconds(),
                    "server_time": time.time(),
                },
                "timestamp": time.time(),
            }
        )
        while True:
            # Keep connection open, handle client-side ping/messages
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket)
    except Exception as e:
        logger.debug(f"WebSocket client error: {e}")
        await ws_manager.disconnect(websocket)


# Static assets & dashboard
static_dir = BASE_DIR.parent / "Interfaces" / "static"
if not static_dir.exists():
    static_dir = BASE_DIR / "static"

if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/", include_in_schema=False)
async def serve_dashboard():
    """Serves the Backend Dashboard web interface."""
    index_file = static_dir / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"message": "FiringSim Backend API is running. Dashboard assets pending."}

