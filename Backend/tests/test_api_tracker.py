"""Tests for Tracker process management and gun endpoints."""

import sys
from app.config import Settings
from app.services.tracker_process import TrackerProcessManager


def test_get_tracker_status_and_guns(client, tracker_state):
    """Verify tracker status and guns endpoints return structured data."""
    res_status = client.get("/api/tracker/status")
    assert res_status.status_code == 200
    data = res_status.json()
    assert "process" in data
    assert "telemetry" in data
    assert "guns" in data

    res_guns = client.get("/api/tracker/guns")
    assert res_guns.status_code == 200
    assert isinstance(res_guns.json(), list)


def test_stop_not_running(client):
    """Calling stop on an idle Tracker returns 400."""
    res = client.post("/api/tracker/stop")
    assert res.status_code == 400
    data = res.json()
    assert "not currently running" in str(data)


def test_start_missing_file(client, app_with_state, tmp_path):
    """Calling start when file is missing returns 400."""
    bad_settings = Settings(
        TRACKER_MODE="script",
        TRACKER_SCRIPT_PATH=str(tmp_path / "nonexistent.py"),
        TRACKER_AUTOSTART=False,
    )
    app_with_state.state.process_manager = TrackerProcessManager(
        settings=bad_settings,
        ws_manager=app_with_state.state.ws_manager,
    )

    res = client.post("/api/tracker/start")
    assert res.status_code == 400
    data = res.json()
    assert "not found" in str(data)


def test_start_stop_restart_workflow(client, app_with_state, tmp_path):
    """Verify full start, stop, restart workflow via REST endpoints."""
    dummy_script = tmp_path / "dummy_tracker.py"
    dummy_script.write_text("import time\ntime.sleep(10)\n")

    settings = Settings(
        TRACKER_MODE="script",
        TRACKER_SCRIPT_PATH=str(dummy_script),
        TRACKER_AUTOSTART=False,
        TRACKER_PYTHON_PATH=sys.executable,
    )
    app_with_state.state.process_manager = TrackerProcessManager(
        settings=settings,
        ws_manager=app_with_state.state.ws_manager,
    )

    # 1. Start
    res_start = client.post("/api/tracker/start")
    assert res_start.status_code == 200
    assert res_start.json()["success"] is True

    # 2. Restart
    res_restart = client.post("/api/tracker/restart")
    assert res_restart.status_code == 200
    assert res_restart.json()["success"] is True

    # 3. Stop
    res_stop = client.post("/api/tracker/stop")
    assert res_stop.status_code == 200
    assert res_stop.json()["success"] is True
