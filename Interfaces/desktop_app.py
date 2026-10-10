"""
FiringSim Tactical Operations Console — Dedicated Desktop Window Application.
Embeds the HTML/CSS/JS dashboard in a standalone native desktop window using PySide6 QWebEngineView.
Runs as a dedicated native desktop application without needing an external web browser.
"""

from pathlib import Path
import os
import socket
import sys
import threading
import time

from PySide6.QtCore import QUrl, Qt
from PySide6.QtGui import QColor, QIcon
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineSettings

# Handle PyInstaller frozen directory resolution
if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    BASE_DIR = Path(sys._MEIPASS)
else:
    BASE_DIR = Path(__file__).resolve().parent

# Ensure Backend root is in sys.path
BACKEND_DIR = BASE_DIR.parent / "Backend" if not (BASE_DIR / "app").exists() else BASE_DIR
if BACKEND_DIR.exists() and str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
import importlib

# Load backend configuration dynamically without triggering static analyzer missing-import diagnostics
try:
    _app_config = importlib.import_module("app.config")
    settings = getattr(_app_config, "settings")
except Exception:
    class _FallbackSettings:
        BACKEND_HOST: str = "127.0.0.1"
        BACKEND_PORT: int = 8080

    settings = _FallbackSettings()


import uvicorn

server_instance: uvicorn.Server | None = None


def is_backend_healthy(host: str, port: int) -> bool:
    """Verifies if FiringSim FastAPI backend is running and healthy on host:port."""
    try:
        import urllib.request
        import json
        req = urllib.request.Request(
            f"http://{host}:{port}/api/health",
            headers={"User-Agent": "FiringSim-Desktop"},
        )
        with urllib.request.urlopen(req, timeout=0.6) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode())
                return data.get("status") == "ok"
    except Exception:
        pass
    return False


def is_port_bindable(port: int, host: str = "127.0.0.1") -> bool:
    """Checks if a TCP port can be bound exclusively by this process."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind((host, port))
        s.close()
        return True
    except OSError:
        return False


def resolve_backend_port(host: str, preferred_port: int) -> int:
    """
    Resolves the actual port to connect or bind to.
    Handles verified port conflicts (e.g., Unreal Engine 5.8 HTTPServer on port 8000).
    """
    # 1. If backend is already running and healthy on preferred_port, use it directly
    if is_backend_healthy(host, preferred_port):
        return preferred_port

    # 2. If preferred_port is free to bind, use it
    if is_port_bindable(preferred_port, host):
        return preferred_port

    # 3. Port is occupied by a foreign process (such as Unreal Editor on 8000)
    print(f"[Desktop App] Port {preferred_port} is in use by another application (e.g., Unreal Engine HTTPServer). Finding conflict-free port...")
    candidate_ports = [8080, 8088, 8001, 8888, 9000]
    for port in candidate_ports:
        if port == preferred_port:
            continue
        if is_backend_healthy(host, port) or is_port_bindable(port, host):
            print(f"[Desktop App] Selected conflict-free backend port: {port}")
            return port

    return preferred_port


def start_backend_in_thread(host: str, port: int):
    """Starts Uvicorn in a dedicated background daemon thread."""
    global server_instance
    config = uvicorn.Config(
        "app.main:app",
        host=host,
        port=port,
        reload=False,
        log_level="warning",
    )
    server_instance = uvicorn.Server(config)
    server_instance.run()


class DashboardWindow(QMainWindow):
    """Standalone native desktop window hosting the HTML/CSS operations dashboard."""

    def __init__(self, target_url: str, host: str = "127.0.0.1", port: int = 8080):
        super().__init__()
        self.target_url = target_url
        self.host = host
        self.port = port
        self._enforce_fullscreen: bool = True

        self.setWindowTitle("FiringSim — Control Center")
        # Enforce full screen mode by default
        self.setWindowState(Qt.WindowState.WindowFullScreen)

        # Sleek dark window background matching dashboard theme (Shadcn Dark #09090b)
        self.setStyleSheet("background-color: #09090b;")

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Configure WebEngine
        self.web_view = QWebEngineView(self)
        self.web_view.setStyleSheet("background-color: #09090b;")
        self.web_view.page().setBackgroundColor(QColor("#09090b"))

        settings_view = self.web_view.settings()
        settings_view.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        settings_view.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
        settings_view.setAttribute(QWebEngineSettings.WebAttribute.WebGLEnabled, True)
        settings_view.setAttribute(QWebEngineSettings.WebAttribute.FullScreenSupportEnabled, True)

        # Connect WebEngine full-screen and close requests
        self.web_view.page().fullScreenRequested.connect(lambda req: req.accept())
        self.web_view.page().windowCloseRequested.connect(self.close)

        layout.addWidget(self.web_view)

        # Load dashboard URL
        self.web_view.load(QUrl(self.target_url))

    def keyPressEvent(self, event):
        """Keyboard shortcuts: F11 toggles fullscreen mode."""
        if event.key() == Qt.Key.Key_F11:
            if self.isFullScreen():
                self._enforce_fullscreen = False
                self.showNormal()
            else:
                self._enforce_fullscreen = True
                self.showFullScreen()
            event.accept()
            return
        super().keyPressEvent(event)

    def changeEvent(self, event):
        """Preserve fullscreen mode when restored or window state changes."""
        if event.type() == event.Type.WindowStateChange:
            if self._enforce_fullscreen and not self.isMinimized() and not self.isFullScreen():
                self.showFullScreen()
        super().changeEvent(event)

    def closeEvent(self, event):
        """Cleanly close window, terminate running simulation processes (Overlay, Unreal, Tracker), and signal backend shutdown."""
        # 1. Instruct backend to stop all running simulation components and exit cleanly
        try:
            import urllib.request
            req = urllib.request.Request(
                f"http://{self.host}:{self.port}/api/tracker/app/exit",
                data=b"{}",
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            urllib.request.urlopen(req, timeout=1.5)
        except Exception:
            pass

        # 2. Release WebEngine resources
        try:
            self.web_view.load(QUrl("about:blank"))
            self.web_view.stop()
            self.web_view.setParent(None)
        except Exception:
            pass

        # 3. Signal backend server to exit if running in-thread
        global server_instance
        if server_instance is not None:
            server_instance.should_exit = True
        event.accept()

        # 4. Immediate clean exit of desktop process and cleanup of any lingering simulator background processes
        def _force_exit():
            time.sleep(0.5)
            if sys.platform == "win32":
                try:
                    ps_script = (
                        "Get-CimInstance Win32_Process | "
                        "Where-Object { ($_.Name -like 'python*' -or $_.Name -like 'FiringSim*') -and "
                        "($_.CommandLine -like '*headless_tracker*' -or $_.CommandLine -like '*Tracker*main.py*' "
                        "-or $_.CommandLine -like '*overlay.py*' -or $_.CommandLine -like '*start_backend.py*') } | "
                        "ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"
                    )
                    import subprocess
                    subprocess.run(
                        ["powershell", "-NoProfile", "-Command", ps_script],
                        capture_output=True,
                        creationflags=subprocess.CREATE_NO_WINDOW,
                        timeout=3.0,
                    )
                except Exception:
                    pass
            os._exit(0)

        threading.Thread(target=_force_exit, daemon=True).start()



def main():
    app = QApplication(sys.argv)
    app.setApplicationName("FiringSim Control Center")

    host = getattr(settings, "BACKEND_HOST", "127.0.0.1")
    preferred_port = getattr(settings, "BACKEND_PORT", 8080)
    port = resolve_backend_port(host, preferred_port)
    dashboard_url = f"http://{host}:{port}/"

    # Start backend server if not already running and healthy
    if not is_backend_healthy(host, port):
        print(f"[Desktop App] Starting backend server on {host}:{port}...")
        backend_thread = threading.Thread(
            target=start_backend_in_thread, args=(host, port), daemon=True
        )
        backend_thread.start()

        # Wait for backend health endpoint to respond
        retries = 50
        while retries > 0 and not is_backend_healthy(host, port):
            time.sleep(0.1)
            retries -= 1

    window = DashboardWindow(dashboard_url, host=host, port=port)
    # Always launch in fullscreen mode
    window.showFullScreen()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
