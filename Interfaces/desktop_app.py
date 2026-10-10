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
        BACKEND_PORT: int = 8000

    settings = _FallbackSettings()


import uvicorn

server_instance: uvicorn.Server | None = None



def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    """Checks if a TCP port is actively listening."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.3)
        return s.connect_ex((host, port)) == 0


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

    def __init__(self, target_url: str):
        super().__init__()
        self.target_url = target_url

        self.setWindowTitle("FiringSim — Tactical Operations Console")
        self.resize(1380, 880)
        self.setMinimumSize(1024, 680)

        # Sleek dark window background matching dashboard theme
        self.setStyleSheet("background-color: #0a0c10;")

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Configure WebEngine
        self.web_view = QWebEngineView(self)
        self.web_view.setStyleSheet("background-color: #0a0c10;")
        self.web_view.page().setBackgroundColor(QColor("#0a0c10"))

        settings_view = self.web_view.settings()
        settings_view.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        settings_view.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
        settings_view.setAttribute(QWebEngineSettings.WebAttribute.WebGLEnabled, True)

        layout.addWidget(self.web_view)

        # Load dashboard URL
        self.web_view.load(QUrl(self.target_url))

    def closeEvent(self, event):
        """Cleanly close window, release web engine resources, and signal backend shutdown."""
        try:
            self.web_view.load(QUrl("about:blank"))
            self.web_view.stop()
            self.web_view.setParent(None)
        except Exception:
            pass

        global server_instance
        if server_instance is not None:
            server_instance.should_exit = True
        event.accept()



def main():
    app = QApplication(sys.argv)
    app.setApplicationName("FiringSim Tactical Console")

    host = settings.BACKEND_HOST
    port = settings.BACKEND_PORT
    dashboard_url = f"http://{host}:{port}/"

    # Start backend server if not already running
    if not is_port_in_use(port, host):
        print(f"[Desktop App] Starting backend server on {host}:{port}...")
        backend_thread = threading.Thread(
            target=start_backend_in_thread, args=(host, port), daemon=True
        )
        backend_thread.start()

        # Wait briefly for server to bind
        retries = 30
        while retries > 0 and not is_port_in_use(port, host):
            time.sleep(0.1)
            retries -= 1

    window = DashboardWindow(dashboard_url)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
