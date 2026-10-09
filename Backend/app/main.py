"""FastAPI Application entry point for Firing Simulator Backend."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from .config import get_config
from .logging_config import setup_logging
from .database.session import init_db
from .services.tracker_listener import tracker_listener
from .websocket.connection_manager import manager
from .api import api_router

config = get_config()

# Configure structured logging
setup_logging(log_level=config.log_level, log_format=config.log_format)
logger = logging.getLogger("backend")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager for startup and shutdown routines."""
    logger.info(f"Starting {config.app_name} v{config.version}...")
    logger.info(f"Database URL: {config.database_url}")

    # 1. Initialize SQLite database schemas & baseline seed data
    init_db()

    # 2. Start UDP listener for tracker telemetry
    await tracker_listener.start()

    yield

    # Shutdown routines
    logger.info("Initiating Backend graceful shutdown...")
    tracker_listener.stop()
    logger.info("Backend service shutdown complete.")


app = FastAPI(
    title=config.app_name,
    version=config.version,
    description="Central control, telemetry, and session management backend",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount REST API
app.include_router(api_router)


# WebSocket Endpoints
@app.websocket("/ws/console")
async def websocket_console_endpoint(websocket: WebSocket):
    """WebSocket endpoint for Instructor Console live streaming and commands."""
    await manager.connect_console(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            logger.debug(f"Received from console: {data}")
            # Echo or acknowledge message
            await websocket.send_json({"type": "ack", "received": data})
    except WebSocketDisconnect:
        manager.disconnect_console(websocket)
    except Exception as e:
        logger.warning(f"Console WebSocket connection error: {e}")
        manager.disconnect_console(websocket)


@app.websocket("/ws/sim")
async def websocket_sim_endpoint(websocket: WebSocket):
    """WebSocket endpoint for Unreal Engine 3D Simulation synchronization."""
    await manager.connect_sim(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            logger.debug(f"Received from sim: {data}")
            # Echo or acknowledge message
            await websocket.send_json({"type": "ack", "received": data})
    except WebSocketDisconnect:
        manager.disconnect_sim(websocket)
    except Exception as e:
        logger.warning(f"Simulation WebSocket connection error: {e}")
        manager.disconnect_sim(websocket)


@app.get("/")
def root():
    return {
        "app": config.app_name,
        "version": config.version,
        "docs": "/docs",
        "health": "/system/health",
    }
