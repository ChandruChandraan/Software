"""Application Configuration."""

from pathlib import Path
import sys
from typing import Literal, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    BASE_DIR = Path(sys._MEIPASS)
else:
    BASE_DIR = Path(__file__).resolve().parent.parent


def resolve_path(path_str: str, relative_to: Path = BASE_DIR) -> Path:
    """Resolve a relative or absolute path reliably."""
    p = Path(path_str)
    if p.is_absolute():
        return p
    return (relative_to / p).resolve()


class Settings(BaseSettings):
    """Backend server and tracker configuration settings."""

    # Server settings
    BACKEND_HOST: str = Field(default="127.0.0.1", description="FastAPI bind host")
    BACKEND_PORT: int = Field(default=8000, description="FastAPI HTTP port")

    # UDP Listener settings
    UDP_HOST: str = Field(default="127.0.0.1", description="UDP listener bind host")
    UDP_PORT: int = Field(default=47001, description="UDP listener port for Tracker telemetry")

    # Tracker Process Management
    TRACKER_AUTOSTART: bool = Field(default=True, description="Whether to launch Tracker automatically on startup")
    TRACKER_MODE: Literal["script", "exe"] = Field(
        default="script", description="Launch mode: 'script' for Python main.py, or 'exe' for Tracker.exe"
    )
    TRACKER_SCRIPT_PATH: str = Field(default="../Tracker/main.py", description="Path to Tracker script")
    TRACKER_EXE_PATH: str = Field(default="../Tracker/dist/Tracker.exe", description="Path to Tracker.exe")
    TRACKER_PYTHON_PATH: Optional[str] = Field(
        default=None, description="Custom Python interpreter executable (None = current sys.executable)"
    )

    TRACKER_NO_SIM: bool = Field(
        default=True, description="Disable virtual simulated guns (enforce physical hardware only)"
    )

    TRACKER_STARTUP_TIMEOUT: float = Field(
        default=5.0, description="Seconds to wait after launch for first telemetry packet"
    )
    TRACKER_TELEMETRY_TIMEOUT: float = Field(
        default=5.0, description="Seconds before telemetry is marked stale/disconnected"
    )

    TRACKER_RESTART_ON_CRASH: bool = Field(default=True, description="Automatically restart Tracker on unexpected exit")
    TRACKER_MAX_CRASH_RESTARTS: int = Field(default=3, description="Maximum crash restart attempts within window")
    TRACKER_CRASH_RESET_WINDOW: float = Field(
        default=30.0, description="Seconds a process must run before crash count resets"
    )

    # Security
    LOCAL_ONLY_MANAGEMENT: bool = Field(
        default=True, description="Restrict process start/stop/restart endpoints to localhost"
    )

    # Logging
    LOG_LEVEL: str = Field(default="INFO", description="Backend log level")

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def get_resolved_script_path(self) -> Path:
        """Get the absolute path to Tracker script."""
        return resolve_path(self.TRACKER_SCRIPT_PATH)

    def get_resolved_exe_path(self) -> Path:
        """Get the absolute path to Tracker executable."""
        return resolve_path(self.TRACKER_EXE_PATH)

    def get_resolved_python_path(self) -> str:
        """Get the executable path for Python interpreter."""
        if self.TRACKER_PYTHON_PATH and self.TRACKER_PYTHON_PATH.strip():
            resolved = resolve_path(self.TRACKER_PYTHON_PATH)
            return str(resolved)
        # Prefer parent suite virtual environment where PySide6/Tracker dependencies reside
        parent_venv_python = (BASE_DIR.parent / ".venv" / "Scripts" / "python.exe").resolve()
        if parent_venv_python.exists():
            return str(parent_venv_python)
        return sys.executable


# Default settings singleton
settings = Settings()
