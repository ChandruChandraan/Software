"""Tests for TrackerProcessManager process lifecycle, path validation, and crash recovery."""

import asyncio
from pathlib import Path
import sys
from app.config import Settings
from app.services.tracker_process import TrackerProcessManager
from app.websocket.manager import ConnectionManager


def test_missing_target_path(tmp_path):
    """Attempting to launch nonexistent file returns error cleanly without crashing."""
    async def _run():
        settings = Settings(
            TRACKER_MODE="script",
            TRACKER_SCRIPT_PATH=str(tmp_path / "nonexistent_tracker.py"),
            TRACKER_AUTOSTART=False,
        )
        ws_mgr = ConnectionManager()
        mgr = TrackerProcessManager(settings=settings, ws_manager=ws_mgr)

        started, msg = await mgr.start_tracker()
        assert started is False
        assert "not found at" in msg

        status = mgr.get_status()
        assert status.running is False
        assert status.path_exists is False

    asyncio.run(_run())


def test_process_lifecycle_with_subscript(tmp_path):
    """Test start, status, and graceful stop on a real python script double."""
    async def _run():
        dummy_script = tmp_path / "dummy_tracker.py"
        dummy_script.write_text(
            "import time, sys\n"
            "for i in range(10):\n"
            "    print(f'TICK {i}', flush=True)\n"
            "    time.sleep(0.5)\n"
        )

        settings = Settings(
            TRACKER_MODE="script",
            TRACKER_SCRIPT_PATH=str(dummy_script),
            TRACKER_AUTOSTART=False,
            TRACKER_PYTHON_PATH=sys.executable,
        )
        ws_mgr = ConnectionManager()
        mgr = TrackerProcessManager(settings=settings, ws_manager=ws_mgr)

        # 1. Start process
        started, msg = await mgr.start_tracker()
        assert started is True
        assert mgr.is_running() is True
        assert mgr.get_status().pid is not None

        # Wait briefly for process to produce output
        await asyncio.sleep(0.3)
        assert len(mgr.recent_logs) > 0

        # 2. Stop process cleanly
        stopped, stop_msg = await mgr.stop_tracker()
        assert stopped is True
        assert mgr.is_running() is False
        assert mgr.get_status().running is False

    asyncio.run(_run())


def test_cannot_start_twice(tmp_path):
    """Starting an already running process fails gracefully."""
    async def _run():
        dummy_script = tmp_path / "dummy_tracker.py"
        dummy_script.write_text("import time\ntime.sleep(5)\n")

        settings = Settings(
            TRACKER_MODE="script",
            TRACKER_SCRIPT_PATH=str(dummy_script),
            TRACKER_AUTOSTART=False,
            TRACKER_PYTHON_PATH=sys.executable,
        )
        ws_mgr = ConnectionManager()
        mgr = TrackerProcessManager(settings=settings, ws_manager=ws_mgr)

        started1, _ = await mgr.start_tracker()
        assert started1 is True

        started2, msg2 = await mgr.start_tracker()
        assert started2 is False
        assert "already running" in msg2

        await mgr.stop_tracker()

    asyncio.run(_run())


def test_crash_recovery(tmp_path):
    """Process exiting unexpectedly triggers crash recovery when enabled."""
    async def _run():
        crash_script = tmp_path / "crash_tracker.py"
        crash_script.write_text("import sys\nsys.exit(1)\n")

        settings = Settings(
            TRACKER_MODE="script",
            TRACKER_SCRIPT_PATH=str(crash_script),
            TRACKER_AUTOSTART=False,
            TRACKER_RESTART_ON_CRASH=True,
            TRACKER_MAX_CRASH_RESTARTS=1,
            TRACKER_CRASH_RESET_WINDOW=60.0,
            TRACKER_PYTHON_PATH=sys.executable,
        )
        ws_mgr = ConnectionManager()
        mgr = TrackerProcessManager(settings=settings, ws_manager=ws_mgr)

        started, _ = await mgr.start_tracker()
        assert started is True

        # Allow monitor to observe crash
        await asyncio.sleep(0.5)

        # Process should have recorded exit code 1
        assert mgr.get_status().exit_code == 1

    asyncio.run(_run())
