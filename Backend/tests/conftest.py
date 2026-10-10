"""Pytest test fixtures and configuration."""

import asyncio
from pathlib import Path
import sys
import pytest
from starlette.testclient import TestClient

# Ensure Backend root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.config import Settings
from app.main import app
from app.services.tracker_listener import TrackerUDPListener
from app.services.tracker_process import TrackerProcessManager
from app.services.tracker_state import TrackerState
from app.websocket.manager import ConnectionManager


@pytest.fixture
def test_settings():
    """Returns isolated test settings with autostart disabled."""
    return Settings(
        BACKEND_HOST="127.0.0.1",
        BACKEND_PORT=8000,
        UDP_HOST="127.0.0.1",
        UDP_PORT=47099,  # Use test port
        TRACKER_AUTOSTART=False,
        TRACKER_MODE="script",
        TRACKER_SCRIPT_PATH="../Tracker/main.py",
        TRACKER_STARTUP_TIMEOUT=1.0,
        TRACKER_TELEMETRY_TIMEOUT=1.0,
        LOCAL_ONLY_MANAGEMENT=True,
    )


@pytest.fixture
def tracker_state(test_settings):
    """Returns a fresh TrackerState instance."""
    return TrackerState(telemetry_timeout=test_settings.TRACKER_TELEMETRY_TIMEOUT)


@pytest.fixture
def ws_manager():
    """Returns a fresh ConnectionManager instance."""
    return ConnectionManager()


@pytest.fixture
def process_manager(test_settings, ws_manager):
    """Returns a TrackerProcessManager instance with test settings."""
    return TrackerProcessManager(settings=test_settings, ws_manager=ws_manager)


@pytest.fixture
def udp_listener(test_settings, tracker_state, ws_manager):
    """Returns a TrackerUDPListener instance."""
    return TrackerUDPListener(
        host=test_settings.UDP_HOST,
        port=test_settings.UDP_PORT,
        state=tracker_state,
        ws_manager=ws_manager,
    )


@pytest.fixture
def app_with_state(test_settings, tracker_state, udp_listener, process_manager, ws_manager):
    """Configures the main FastAPI application state for unit and integration testing."""
    app.state.settings = test_settings
    app.state.tracker_state = tracker_state
    app.state.udp_listener = udp_listener
    app.state.process_manager = process_manager
    app.state.ws_manager = ws_manager
    return app


@pytest.fixture
def client(app_with_state):
    """Synchronous Starlette TestClient."""
    return TestClient(app_with_state)
