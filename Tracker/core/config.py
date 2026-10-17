import json
from pathlib import Path

# Unreal Engine UDP Server Settings (127.0.0.1:47000)
UNREAL_IP: str = "127.0.0.1"
UNREAL_PORT: int = 47000

# Python Backend Settings
BACKEND_IP: str = "127.0.0.1"
BACKEND_PORT: int = 47001  # UDP telemetry listener port
BACKEND_HTTP_PORT: int = 8080  # HTTP & WebSocket port
SEND_TO_BACKEND: bool = True

_ROOT_DIR = Path(__file__).resolve().parent.parent.parent
_DEFAULT_EXE = str((_ROOT_DIR / "PackagedUE" / "Windows" / "FiringSim.exe").resolve())

# Unreal Engine Application Launch Settings
UNREAL_EXE_PATH: str = _DEFAULT_EXE
AUTO_LAUNCH_UNREAL: bool = True
AUTO_START_OVERLAY: bool = True

# Load overrides from central config.json at Software root if present
_CENTRAL_CONFIG = _ROOT_DIR / "config.json"
if _CENTRAL_CONFIG.exists():
    try:
        with open(_CENTRAL_CONFIG, "r", encoding="utf-8") as _f:
            _cfg = json.load(_f)
            UNREAL_EXE_PATH = _cfg.get("unreal_exe_path", UNREAL_EXE_PATH)
            UNREAL_IP = _cfg.get("unreal_udp_host", UNREAL_IP)
            UNREAL_PORT = int(_cfg.get("unreal_udp_port", UNREAL_PORT))
            BACKEND_IP = _cfg.get("backend_host", BACKEND_IP)
            BACKEND_PORT = int(_cfg.get("tracker_udp_port", BACKEND_PORT))
            BACKEND_HTTP_PORT = int(_cfg.get("backend_port", BACKEND_HTTP_PORT))
            AUTO_LAUNCH_UNREAL = bool(_cfg.get("unreal_autostart", AUTO_LAUNCH_UNREAL))
    except Exception as _e:
        print(f"[Tracker Config] Error loading {_CENTRAL_CONFIG}: {_e}")

# UDP Connection Monitoring & Handshake
UDP_TIMEOUT: float = 3.0
UDP_HEARTBEAT_INTERVAL: float = 1.0
HELLO_MESSAGE: bytes = b"HELLO_UNREAL"
EXPECTED_RESPONSE: str = "HELLO_PYTHON"

# Overlay Rendering Settings
OVERLAY_FPS: int = 60
# Target Display Defaults: True to default to Primary display, False to default to Secondary/Projector
DEFAULT_TO_PRIMARY_DISPLAY: bool = False
OVERLAY_TRANSPARENT: bool = True
DEBUG_LOGGING: bool = True

# Serial Port & Microcontroller Settings
AUTO_CONNECT_SERIAL: bool = True
SERIAL_BAUD_RATE: int = 115200
SERIAL_TIMEOUT_S: float = 0.2
SERIAL_HEARTBEAT_TIMEOUT_S: float = 3.0
SERIAL_AUTO_SCAN_INTERVAL_MS: int = 1000
SIMULATED_GUN_COUNT: int = 4

# Distinct Color Palette per Gun ID
GUN_COLORS: dict[int, str] = {
    1: "#00ff66",  # Neon Green
    2: "#58a6ff",  # Bright Cyan / Blue
    3: "#ff7b72",  # Coral Red
    4: "#d29922",  # Amber / Gold
    5: "#bc8cff",  # Purple
    6: "#f0883e",  # Orange
    7: "#39d353",  # Mint
    8: "#f778ba",  # Hot Pink
}
