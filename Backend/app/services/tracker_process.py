"""Tracker subprocess management (start, stop, restart, crash recovery, logs)."""

import asyncio
from collections import deque
import logging
import os
from pathlib import Path
import sys
import time
from typing import Dict, List, Optional, Tuple, Any

from app.config import Settings
from app.schemas import TrackerProcessStatus
from app.websocket.manager import ConnectionManager

logger = logging.getLogger("backend.tracker_process")


class TrackerProcessManager:
    """Manages the child Tracker process lifecycle."""

    def __init__(self, settings: Settings, ws_manager: ConnectionManager):
        self.settings = settings
        self.ws_manager = ws_manager

        self._process: Optional[asyncio.subprocess.Process] = None
        self._pid: Optional[int] = None
        self._started_at: Optional[float] = None
        self._exit_code: Optional[int] = None
        self._last_error: Optional[str] = None
        self._restart_count: int = 0
        self._stopping_intentionally: bool = False

        self._stdout_task: Optional[asyncio.Task] = None
        self._stderr_task: Optional[asyncio.Task] = None
        self._monitor_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()

        # Buffered recent output lines
        self.recent_logs: deque = deque(maxlen=200)

    def is_running(self) -> bool:
        """Returns True if the managed child process is currently alive."""
        return self._process is not None and self._process.returncode is None

    def get_target_path(self) -> Path:
        """Returns the configured script or executable path based on TRACKER_MODE."""
        if self.settings.TRACKER_MODE == "exe":
            return self.settings.get_resolved_exe_path()
        return self.settings.get_resolved_script_path()

    async def start_tracker(self) -> Tuple[bool, str]:
        """
        Launches the configured Tracker process.
        Validates target file existence beforehand.
        """
        async with self._lock:
            if self.is_running():
                return False, f"Tracker is already running (PID: {self._pid})"

            target_path = self.get_target_path()
            if not target_path.exists():
                err_msg = (
                    f"Configured Tracker {self.settings.TRACKER_MODE} not found at: {target_path}. "
                    f"Please verify path in configuration."
                )
                self._last_error = err_msg
                logger.error(err_msg)
                self.record_log_line("system", err_msg)
                return False, err_msg

            # Build command line arguments
            if self.settings.TRACKER_MODE == "exe":
                cmd = [
                    str(target_path),
                    "--backend-host",
                    self.settings.UDP_HOST,
                    "--backend-port",
                    str(self.settings.UDP_PORT),
                ]
                if self.settings.TRACKER_NO_SIM:
                    cmd.append("--no-sim")
                working_dir = str(target_path.parent)
            else:
                python_exe = self.settings.get_resolved_python_path()
                cmd = [
                    python_exe,
                    str(target_path),
                    "--backend-host",
                    self.settings.UDP_HOST,
                    "--backend-port",
                    str(self.settings.UDP_PORT),
                ]
                if self.settings.TRACKER_NO_SIM:
                    cmd.append("--no-sim")
                working_dir = str(target_path.parent)

            logger.info(f"Starting Tracker process in {working_dir}: {' '.join(cmd)}")
            self.record_log_line("system", f"Launching: {' '.join(cmd)}")

            try:
                self._stopping_intentionally = False
                self._process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=working_dir,
                )
                self._pid = self._process.pid
                self._started_at = time.time()
                self._exit_code = None
                self._last_error = None

                logger.info(f"Tracker process spawned successfully with PID: {self._pid}")
                self.record_log_line("system", f"Tracker process started with PID {self._pid}")

                # Start streaming readers
                self._stdout_task = asyncio.create_task(self._read_stream(self._process.stdout, "stdout"))
                self._stderr_task = asyncio.create_task(self._read_stream(self._process.stderr, "stderr"))
                self._monitor_task = asyncio.create_task(self._monitor_process())

                # Broadcast process start event
                status_dict = self.get_status().model_dump()
                await self.ws_manager.broadcast("tracker_started", status_dict)
                return True, f"Tracker started successfully (PID: {self._pid})"

            except Exception as e:
                self._last_error = str(e)
                logger.exception(f"Failed to launch Tracker process: {e}")
                self.record_log_line("system", f"Launch error: {e}")
                return False, f"Failed to launch Tracker: {e}"

    async def stop_tracker(self) -> Tuple[bool, str]:
        """Gracefully terminates only the Tracker process owned by this backend."""
        async with self._lock:
            if not self.is_running() or self._process is None:
                return False, "Tracker is not currently running"

            self._stopping_intentionally = True
            pid = self._pid
            logger.info(f"Stopping Tracker process (PID: {pid})...")
            self.record_log_line("system", f"Stopping Tracker process (PID: {pid})...")

            try:
                if sys.platform == "win32" and pid:
                    import subprocess
                    subprocess.run(
                        ["taskkill", "/F", "/T", "/PID", str(pid)],
                        capture_output=True,
                        creationflags=subprocess.CREATE_NO_WINDOW,
                    )
                else:
                    self._process.terminate()

                try:
                    await asyncio.wait_for(self._process.wait(), timeout=1.5)
                except asyncio.TimeoutError:
                    if self._process:
                        self._process.kill()
                        await self._process.wait()
            except ProcessLookupError:
                pass
            except Exception as e:
                logger.error(f"Error while terminating Tracker: {e}")

            # Cancel readers
            if self._stdout_task and not self._stdout_task.done():
                self._stdout_task.cancel()
            if self._stderr_task and not self._stderr_task.done():
                self._stderr_task.cancel()
            if self._monitor_task and not self._monitor_task.done():
                self._monitor_task.cancel()

            self._exit_code = self._process.returncode if self._process else 0
            self._process = None
            self._pid = None
            self._stopping_intentionally = False

            logger.info(f"Tracker (PID: {pid}) stopped.")
            self.record_log_line("system", f"Tracker process (PID {pid}) stopped.")

            status_dict = self.get_status().model_dump()
            await self.ws_manager.broadcast("tracker_stopped", status_dict)
            return True, f"Tracker process (PID {pid}) stopped successfully"

    async def restart_tracker(self) -> Tuple[bool, str]:
        """Safely stops and restarts the Tracker process."""
        if self.is_running():
            stop_ok, stop_msg = await self.stop_tracker()
            if not stop_ok:
                return False, f"Restart failed during stop: {stop_msg}"
            # Small pause to ensure ports and serial handles release cleanly
            await asyncio.sleep(0.5)

        start_ok, start_msg = await self.start_tracker()
        return start_ok, start_msg

    async def _read_stream(self, reader: Optional[asyncio.StreamReader], stream_name: str):
        """Reads output stream line by line without blocking."""
        if reader is None:
            return
        try:
            while True:
                line = await reader.readline()
                if not line:
                    break
                text = line.decode("utf-8", errors="replace").rstrip()
                if text:
                    self.record_log_line(stream_name, text)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.debug(f"Stream reader {stream_name} closed: {e}")

    def record_log_line(self, stream_name: str, text: str):
        """Buffers a log line and broadcasts to WebSocket."""
        entry = {
            "timestamp": time.time(),
            "stream": stream_name,
            "text": text,
        }
        self.recent_logs.append(entry)
        asyncio.create_task(self.ws_manager.broadcast("tracker_log", entry))

    async def _monitor_process(self):
        """Monitors child process exit and triggers crash recovery if needed."""
        if not self._process:
            return
        try:
            exit_code = await self._process.wait()
            self._exit_code = exit_code
            was_intentional = self._stopping_intentionally
            run_duration = (time.time() - self._started_at) if self._started_at else 0.0

            # Reset internal references
            self._process = None
            self._pid = None

            if was_intentional:
                logger.info(f"Tracker exited cleanly with code {exit_code}")
                return

            # Unexpected exit / crash
            logger.warning(f"Tracker process exited unexpectedly with code {exit_code}")
            self._last_error = f"Process terminated unexpectedly with exit code {exit_code}"
            self.record_log_line("system", self._last_error)

            status_dict = self.get_status().model_dump()
            await self.ws_manager.broadcast("tracker_crashed", status_dict)

            # Crash restart logic
            if self.settings.TRACKER_RESTART_ON_CRASH:
                if run_duration > self.settings.TRACKER_CRASH_RESET_WINDOW:
                    self._restart_count = 0

                if self._restart_count < self.settings.TRACKER_MAX_CRASH_RESTARTS:
                    self._restart_count += 1
                    msg = (
                        f"Crash recovery: restarting Tracker in 2.0s "
                        f"(attempt {self._restart_count}/{self.settings.TRACKER_MAX_CRASH_RESTARTS})..."
                    )
                    logger.info(msg)
                    self.record_log_line("system", msg)
                    await asyncio.sleep(2.0)
                    await self.start_tracker()
                else:
                    msg = (
                        f"Tracker crashed repeatedly. Exceeded maximum "
                        f"{self.settings.TRACKER_MAX_CRASH_RESTARTS} automatic restarts."
                    )
                    logger.error(msg)
                    self.record_log_line("system", msg)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.exception(f"Error in process monitor: {e}")

    def get_status(self) -> TrackerProcessStatus:
        """Returns structured status information for REST API and dashboard."""
        target_path = self.get_target_path()
        running = self.is_running()
        uptime = round(time.time() - self._started_at, 2) if (running and self._started_at) else None

        return TrackerProcessStatus(
            running=running,
            pid=self._pid,
            mode=self.settings.TRACKER_MODE,
            target_path=str(target_path),
            path_exists=target_path.exists(),
            uptime_seconds=uptime,
            exit_code=self._exit_code,
            restart_count=self._restart_count,
            last_error=self._last_error,
        )

    def get_recent_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Returns recent buffered logs."""
        logs = list(self.recent_logs)
        return logs[-limit:]
