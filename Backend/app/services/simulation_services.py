"""
Simulation Services for Unreal Engine, Projector Overlay, and Display Management.
Provides process supervisor and display detection for the FiringSim tactical suite.
"""

import asyncio
import ctypes
from ctypes import wintypes
import logging
import os
from pathlib import Path
import subprocess
import threading
import time
from typing import Dict, List, Optional, Tuple

from app.config import Settings
from app.schemas import DisplayInfoModel, UnrealStatusModel, OverlayStatusModel
from app.websocket.manager import ConnectionManager

logger = logging.getLogger("backend.sim_services")

user32 = ctypes.windll.user32
WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)


class DisplayService:
    """Detects active physical monitors and projectors using Windows API."""

    @staticmethod
    def get_displays() -> List[DisplayInfoModel]:
        displays: List[DisplayInfoModel] = []

        try:
            monitors = []

            def enum_cb(h_monitor, hdc, lprc_monitor, dw_data):
                r = lprc_monitor.contents
                monitors.append((r.left, r.top, r.right - r.left, r.bottom - r.top))
                return True

            MONITORENUMPROC = ctypes.WINFUNCTYPE(
                wintypes.BOOL,
                wintypes.HMONITOR,
                wintypes.HDC,
                ctypes.POINTER(wintypes.RECT),
                wintypes.LPARAM,
            )
            user32.EnumDisplayMonitors(0, 0, MONITORENUMPROC(enum_cb), 0)

            for idx, (x, y, w, h) in enumerate(monitors):
                is_primary = (x == 0 and y == 0)
                name = f"Display {idx + 1}" + (" (Primary)" if is_primary else " (Projector/Secondary)")
                displays.append(
                    DisplayInfoModel(
                        index=idx + 1,
                        name=name,
                        x=x,
                        y=y,
                        width=w,
                        height=h,
                        is_primary=is_primary,
                    )
                )
        except Exception as e:
            logger.error(f"Error enumerating displays: {e}")
            # Fallback 1080p
            displays.append(
                DisplayInfoModel(
                    index=1,
                    name="Display 1 (Primary)",
                    x=0,
                    y=0,
                    width=1920,
                    height=1080,
                    is_primary=True,
                )
            )

        return displays

    @staticmethod
    def get_projector_or_secondary() -> DisplayInfoModel:
        displays = DisplayService.get_displays()
        secondary = next((d for d in displays if not d.is_primary), None)
        return secondary or displays[0]


class UnrealService:
    """Manages lifecycle and positioning of the packaged Unreal Engine application."""

    def __init__(self, ws_manager: ConnectionManager, exe_path: Optional[str] = None):
        self.ws_manager = ws_manager
        if exe_path:
            self.exe_path = exe_path
        else:
            from app.config import settings
            self.exe_path = settings.UNREAL_EXE_PATH
        self._proc: Optional[subprocess.Popen] = None
        self._pid: Optional[int] = None
        self._lock = threading.Lock()

    def get_status(self) -> UnrealStatusModel:
        is_alive, pid = self.is_running()
        return UnrealStatusModel(
            is_running=is_alive,
            pid=pid,
            exe_path=self.exe_path,
            exe_exists=Path(self.exe_path).exists(),
        )

    def is_running(self) -> Tuple[bool, Optional[int]]:
        with self._lock:
            if self._proc is not None and self._proc.poll() is None:
                return True, self._proc.pid

        # Check by tasklist for bound FiringSim instances
        try:
            res = subprocess.run(
                ["tasklist", "/FO", "CSV", "/NH"],
                capture_output=True,
                text=True,
                timeout=2.0,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            for line in res.stdout.splitlines():
                parts = [p.strip().strip('"') for p in line.split('","')]
                if len(parts) >= 2:
                    proc_name = parts[0].lower()
                    if proc_name in ("firingsim.exe", "firingsim-win64-shipping.exe"):
                        try:
                            pid = int(parts[1])
                            return True, pid
                        except (ValueError, TypeError):
                            pass
        except Exception:
            pass

        return False, None

    async def start(self, display_index: Optional[int] = None) -> Tuple[bool, str]:
        exe_file = Path(self.exe_path)
        if not exe_file.exists():
            return False, f"Unreal executable not found at: {self.exe_path}"

        running, pid = self.is_running()
        if running:
            return True, f"Unreal Engine is already running (PID: {pid})"

        # Select target display
        displays = DisplayService.get_displays()
        target_display = None
        if display_index is not None:
            target_display = next((d for d in displays if d.index == display_index), None)
        if target_display is None:
            target_display = DisplayService.get_projector_or_secondary()

        args = [
            str(exe_file),
            f"-WinX={target_display.x}",
            f"-WinY={target_display.y}",
            f"-ResX={target_display.width}",
            f"-ResY={target_display.height}",
            "-fullscreen",
            "-borderless",
            "-forceres",
            "-NoVSync",
        ]

        logger.info(f"Launching Unreal Engine on Display {target_display.index} (Fullscreen): {' '.join(args)}")
        try:
            self._proc = subprocess.Popen(
                args,
                cwd=str(exe_file.parent),
                shell=False,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            self._pid = self._proc.pid

            # Thread to ensure window placement and strip window borders
            threading.Thread(
                target=self._snap_window_placement,
                args=(target_display,),
                daemon=True,
            ).start()

            await self.ws_manager.broadcast("unreal_status", self.get_status().model_dump())
            return True, f"Unreal Engine launched successfully on Display {target_display.index} in fullscreen mode (PID: {self._pid})"
        except Exception as e:
            logger.error(f"Failed to launch Unreal Engine: {e}")
            return False, f"Launch failed: {e}"

    def _find_all_unreal_pids(self) -> List[int]:
        """Discovers all running FiringSim executable process IDs."""
        pids: List[int] = []
        try:
            res = subprocess.run(
                ["tasklist", "/FO", "CSV", "/NH"],
                capture_output=True,
                text=True,
                timeout=2.0,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            for line in res.stdout.splitlines():
                parts = [p.strip().strip('"') for p in line.split('","')]
                if len(parts) >= 2:
                    proc_name = parts[0].lower()
                    if proc_name in ("firingsim.exe", "firingsim-win64-shipping.exe"):
                        try:
                            pids.append(int(parts[1]))
                        except (ValueError, TypeError):
                            pass
        except Exception:
            pass
        return pids

    async def stop(self) -> Tuple[bool, str]:
        running, pid = self.is_running()

        logger.info(f"Terminating Unreal Engine (PID: {pid})...")

        # 1. Post WM_CLOSE to window HWNDs
        try:
            hwnds = self._find_unreal_hwnds(pid)
            for hwnd in hwnds:
                user32.PostMessageW(hwnd, 0x0010, 0, 0)
        except Exception:
            pass

        # 2. Kill managed process directly
        with self._lock:
            if self._proc is not None:
                try:
                    self._proc.kill()
                except Exception:
                    pass
                self._proc = None

        # 3. Kill all FiringSim process instances
        all_pids = self._find_all_unreal_pids()
        if pid and pid not in all_pids:
            all_pids.append(pid)

        for p in all_pids:
            try:
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(p)],
                    capture_output=True,
                    timeout=2.0,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )
            except Exception:
                pass

        # 4. Fallback image-name taskkill
        try:
            subprocess.run(
                ["taskkill", "/F", "/IM", "FiringSim.exe"],
                capture_output=True,
                timeout=1.5,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            subprocess.run(
                ["taskkill", "/F", "/IM", "FiringSim-Win64-Shipping.exe"],
                capture_output=True,
                timeout=1.5,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
        except Exception:
            pass

        await self.ws_manager.broadcast("unreal_status", self.get_status().model_dump())
        return True, "Unreal Engine stopped successfully"

    def _snap_window_placement(self, display: DisplayInfoModel, duration_seconds: float = 12.0):
        """Monitors for Unreal window, strips window borders, and snaps borderless fullscreen."""
        target_x, target_y, target_w, target_h = display.x, display.y, display.width, display.height
        GWL_STYLE = -16
        WS_CAPTION = 0x00C00000
        WS_THICKFRAME = 0x00040000
        WS_POPUP = 0x80000000
        SWP_FRAMECHANGED = 0x0020
        SWP_SHOWWINDOW = 0x0040

        start_time = time.time()
        while time.time() - start_time < duration_seconds:
            time.sleep(0.4)
            is_alive, pid = self.is_running()
            if not is_alive or not pid:
                break
            hwnds = self._find_unreal_hwnds(pid)
            for hwnd in hwnds:
                try:
                    current_style = user32.GetWindowLongW(hwnd, GWL_STYLE)
                    new_style = (current_style & ~(WS_CAPTION | WS_THICKFRAME)) | WS_POPUP
                    user32.SetWindowLongW(hwnd, GWL_STYLE, new_style)
                    user32.SetWindowPos(
                        hwnd, 0, target_x, target_y, target_w, target_h,
                        SWP_FRAMECHANGED | SWP_SHOWWINDOW
                    )
                except Exception:
                    pass

    def _find_unreal_hwnds(self, target_pid: Optional[int]) -> List[int]:
        found_hwnds = []
        if not target_pid:
            return found_hwnds

        def enum_cb(hwnd, lparam):
            if user32.IsWindowVisible(hwnd):
                pid = wintypes.DWORD()
                user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                if pid.value == target_pid:
                    found_hwnds.append(hwnd)
            return True

        cb = WNDENUMPROC(enum_cb)
        user32.EnumWindows(cb, 0)
        return found_hwnds


class OverlayService:
    """Manages the Projector Overlay process (overlay.py)."""

    def __init__(self, ws_manager: ConnectionManager, tracker_dir: Path, python_exe: Path):
        self.ws_manager = ws_manager
        self.tracker_dir = tracker_dir
        self.python_exe = python_exe
        self._proc: Optional[subprocess.Popen] = None
        self._pid: Optional[int] = None
        self._target_display: Optional[DisplayInfoModel] = None
        self._lock = threading.Lock()

    def get_status(self) -> OverlayStatusModel:
        is_alive, pid = self.is_running()
        target = self._target_display
        if target is None:
            target = DisplayService.get_projector_or_secondary()

        active_ident = None
        if is_alive and target:
            active_ident = f"Display {target.index} ({target.width}x{target.height}) [Secondary Projector]"

        return OverlayStatusModel(
            is_running=is_alive,
            pid=pid,
            target_display=target.index if target else None,
            target_resolution=f"{target.width}x{target.height}" if target else None,
            active_identity=active_ident,
        )

    def _find_overlay_pids(self) -> List[int]:
        """Discovers any running python processes executing overlay.py."""
        pids: List[int] = []
        try:
            cmd = [
                "powershell",
                "-NoProfile",
                "-Command",
                "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*overlay.py*' } | Select-Object -ExpandProperty ProcessId",
            ]
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=2.0,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            for line in res.stdout.splitlines():
                line = line.strip()
                if line.isdigit():
                    pids.append(int(line))
        except Exception:
            pass
        return pids

    def _find_overlay_hwnds(self) -> List[int]:
        """Finds any top-level window handles matching Projector Overlay."""
        found: List[int] = []
        def enum_cb(hwnd, lparam):
            if user32.IsWindowVisible(hwnd):
                length = user32.GetWindowTextLengthW(hwnd)
                if length > 0:
                    buf = ctypes.create_unicode_buffer(length + 1)
                    user32.GetWindowTextW(hwnd, buf, length + 1)
                    title = buf.value.lower()
                    if "projector overlay" in title:
                        found.append(hwnd)
            return True

        cb = WNDENUMPROC(enum_cb)
        user32.EnumWindows(cb, 0)
        return found

    def is_running(self) -> Tuple[bool, Optional[int]]:
        with self._lock:
            if self._proc is not None and self._proc.poll() is None:
                return True, self._proc.pid

        # Check discovered active overlay.py processes
        active_pids = self._find_overlay_pids()
        if active_pids:
            return True, active_pids[0]
        return False, None

    async def start(self, display_index: Optional[int] = None) -> Tuple[bool, str]:
        running, pid = self.is_running()
        if running:
            return True, f"Projector Overlay is already running (PID: {pid})"

        overlay_script = self.tracker_dir / "overlay.py"
        if not overlay_script.exists():
            return False, f"Overlay script not found at: {overlay_script}"

        # Resolve the projector / secondary display matching Unreal Engine
        displays = DisplayService.get_displays()
        target_display = None
        if display_index is not None:
            target_display = next((d for d in displays if d.index == display_index), None)
        if target_display is None:
            target_display = DisplayService.get_projector_or_secondary()

        cmd = [
            str(self.python_exe),
            str(overlay_script),
            f"--display={target_display.index}",
            f"--x={target_display.x}",
            f"--y={target_display.y}",
            f"--w={target_display.width}",
            f"--h={target_display.height}",
        ]
        logger.info(f"Launching Projector Overlay on Display {target_display.index} ({target_display.width}x{target_display.height}): {' '.join(cmd)}")

        try:
            self._proc = subprocess.Popen(
                cmd,
                cwd=str(self.tracker_dir),
                shell=False,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            self._pid = self._proc.pid
            self._target_display = target_display
            await self.ws_manager.broadcast("overlay_status", self.get_status().model_dump())
            return True, f"Projector Overlay launched on Display {target_display.index} (PID: {self._pid})"
        except Exception as e:
            logger.error(f"Failed to launch Projector Overlay: {e}")
            return False, f"Overlay launch failed: {e}"

    async def stop(self) -> Tuple[bool, str]:
        running, pid = self.is_running()

        logger.info(f"Stopping Projector Overlay (PID: {pid})...")

        # 1. Post WM_CLOSE to any overlay window
        try:
            hwnds = self._find_overlay_hwnds()
            for hwnd in hwnds:
                user32.PostMessageW(hwnd, 0x0010, 0, 0)
        except Exception:
            pass

        # 2. Terminate managed process
        with self._lock:
            if self._proc is not None:
                try:
                    self._proc.terminate()
                    self._proc.kill()
                except Exception:
                    pass
                self._proc = None

        # 3. Kill all active overlay.py process IDs
        active_pids = self._find_overlay_pids()
        if pid and pid not in active_pids:
            active_pids.append(pid)

        for opid in active_pids:
            try:
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(opid)],
                    capture_output=True,
                    timeout=2.0,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )
            except Exception:
                pass

        await self.ws_manager.broadcast("overlay_status", self.get_status().model_dump())
        return True, "Projector Overlay stopped"
