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

    # Server settings (Port 8080 avoids verified conflict with Unreal Engine 5.8 HTTPServer on port 8000)
    BACKEND_HOST: str = Field(default="127.0.0.1", description="FastAPI bind host")
    BACKEND_PORT: int = Field(default=8080, description="FastAPI HTTP port")

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

    # Dynamic defaults relative to Software/
    _DEFAULT_UNREAL_EXE = str((BASE_DIR.parent / "PackagedUE" / "Windows" / "FiringSim.exe").resolve())
    _DEFAULT_UNREAL_CONTENT = str((BASE_DIR.parent / "PackagedUE" / "Windows" / "FiringSim" / "Content").resolve())

    # Unreal Engine Management
    UNREAL_AUTOSTART: bool = Field(
        default=True, description="Whether to launch Unreal Engine automatically on startup"
    )
    UNREAL_EXE_PATH: str = Field(
        default=_DEFAULT_UNREAL_EXE,
        description="Path to packaged Unreal Engine executable (configured in Software/config.json)"
    )
    UNREAL_UDP_HOST: str = Field(
        default="127.0.0.1", description="Unreal Engine UDP command destination host"
    )
    UNREAL_UDP_PORT: int = Field(
        default=47000, description="Unreal Engine UDP command destination port"
    )
    SCENARIO_COMMAND_TIMEOUT: float = Field(
        default=5.0, description="Timeout in seconds awaiting Unreal scenario acknowledgement"
    )
    SCENARIO_DEBOUNCE_SECONDS: float = Field(
        default=2.0, description="Minimum seconds between duplicate scenario change requests"
    )
    UNREAL_CONTENT_DIR: Optional[str] = Field(
        default=_DEFAULT_UNREAL_CONTENT,
        description="Path to Unreal Engine Content directory (configured in Software/config.json)",
    )
    SCENARIOS_JSON_PATH: Optional[str] = Field(
        default=str(BASE_DIR / "scenarios.json"),
        description="Path to JSON file for scenario catalog definitions",
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

    def __init__(self, **values):
        central_config = BASE_DIR.parent / "config.json"
        if central_config.exists():
            try:
                import json
                with open(central_config, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    if "unreal_exe_path" in cfg and "UNREAL_EXE_PATH" not in values:
                        values["UNREAL_EXE_PATH"] = cfg["unreal_exe_path"]
                    if "unreal_content_dir" in cfg and "UNREAL_CONTENT_DIR" not in values:
                        values["UNREAL_CONTENT_DIR"] = cfg["unreal_content_dir"]
                    if "unreal_autostart" in cfg and "UNREAL_AUTOSTART" not in values:
                        values["UNREAL_AUTOSTART"] = bool(cfg["unreal_autostart"])
                    if "unreal_udp_host" in cfg and "UNREAL_UDP_HOST" not in values:
                        values["UNREAL_UDP_HOST"] = cfg["unreal_udp_host"]
                    if "unreal_udp_port" in cfg and "UNREAL_UDP_PORT" not in values:
                        values["UNREAL_UDP_PORT"] = int(cfg["unreal_udp_port"])
                    if "backend_host" in cfg and "BACKEND_HOST" not in values:
                        values["BACKEND_HOST"] = cfg["backend_host"]
                    if "backend_port" in cfg and "BACKEND_PORT" not in values:
                        values["BACKEND_PORT"] = int(cfg["backend_port"])
                    if "tracker_udp_port" in cfg and "UDP_PORT" not in values:
                        values["UDP_PORT"] = int(cfg["tracker_udp_port"])
            except Exception as e:
                print(f"[Backend Config] Error loading {central_config}: {e}")
        super().__init__(**values)

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

    def get_unreal_content_dir(self) -> Optional[Path]:
        """Get the absolute path to Unreal Content directory if it exists."""
        if self.UNREAL_CONTENT_DIR:
            p = resolve_path(self.UNREAL_CONTENT_DIR)
            if p.exists():
                return p
        # Check PackagedUE Content
        pkg_content = (BASE_DIR.parent / "PackagedUE" / "Windows" / "FiringSim" / "Content").resolve()
        if pkg_content.exists():
            return pkg_content
        # Fallback relative to project root
        candidate = (BASE_DIR.parent.parent / "Unreal" / "FiringSim" / "Content").resolve()
        if candidate.exists():
            return candidate
        return None

    def get_scenarios_json_path(self) -> Optional[Path]:
        """Get the resolved path to scenarios.json if configured or present."""
        if self.SCENARIOS_JSON_PATH:
            p = resolve_path(self.SCENARIOS_JSON_PATH)
            return p
        candidate = (BASE_DIR / "scenarios.json").resolve()
        return candidate if candidate.exists() else None


# Default settings singleton
settings = Settings()
