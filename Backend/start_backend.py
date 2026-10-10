"""
FiringSim Backend Launcher Script.
Starts Uvicorn server in production-like mode (no reload) to ensure clean child process management.
"""

import argparse
import os
from pathlib import Path
import sys
import threading
import time
import webbrowser
import uvicorn

# Ensure Backend directory is in sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.config import settings


def main():
    parser = argparse.ArgumentParser(description="FiringSim Backend Service Launcher")
    parser.add_argument("--host", default=settings.BACKEND_HOST, help="Host to bind HTTP server")
    parser.add_argument("--port", type=int, default=settings.BACKEND_PORT, help="Port to bind HTTP server")
    parser.add_argument("--open-browser", action="store_true", help="Automatically open dashboard in browser")
    parser.add_argument("--no-tracker", action="store_true", help="Disable automatic Tracker process launch")
    args = parser.parse_args()

    if args.no_tracker:
        os.environ["TRACKER_AUTOSTART"] = "false"

    dashboard_url = f"http://{args.host}:{args.port}/"

    print("=" * 70)
    print(" FIRINGSIM — BACKEND OPERATIONS DAEMON")
    print("=" * 70)
    print(f" Dashboard URL : {dashboard_url}")
    print(f" UDP Listener  : {settings.UDP_HOST}:{settings.UDP_PORT} (Marksmanship Telemetry)")
    print(f" Tracker Mode  : {settings.TRACKER_MODE.upper()}")
    target_path = settings.get_resolved_exe_path() if settings.TRACKER_MODE == "exe" else settings.get_resolved_script_path()
    print(f" Target Path   : {target_path}")
    print(f" Auto-Launch   : {'ENABLED' if settings.TRACKER_AUTOSTART and not args.no_tracker else 'DISABLED'}")
    print("=" * 70)
    print("Starting Uvicorn server (single process, reload disabled)...")

    if args.open_browser:
        def _open():
            time.sleep(1.2)
            try:
                webbrowser.open(dashboard_url)
            except Exception:
                pass
        threading.Thread(target=_open, daemon=True).start()

    # NOTE: reload is explicitly False to avoid duplicate process hierarchies
    try:
        uvicorn.run(
            "app.main:app",
            host=args.host,
            port=args.port,
            reload=False,
            log_level=settings.LOG_LEVEL.lower(),
        )
    finally:
        # Guarantee no orphaned tracker or overlay processes linger on shutdown
        if sys.platform == "win32":
            try:
                import subprocess
                ps_script = (
                    "Get-CimInstance Win32_Process | "
                    "Where-Object { ($_.Name -like 'python*' -or $_.Name -like 'FiringSim*') -and "
                    "($_.CommandLine -like '*headless_tracker*' -or $_.CommandLine -like '*Tracker*main.py*' "
                    "-or $_.CommandLine -like '*overlay.py*') } | "
                    "ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"
                )
                subprocess.run(
                    ["powershell", "-NoProfile", "-Command", ps_script],
                    capture_output=True,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    timeout=3.0,
                )
            except Exception:
                pass


if __name__ == "__main__":
    main()
