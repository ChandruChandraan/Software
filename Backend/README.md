# FiringSim — Python FastAPI Backend & Tracker Coordinator

First-starting component of the Firing Simulator software suite. Coordinates background headless Tracker processes, ingests real-time UDP marksmanship telemetry, maintains in-memory gun state, broadcasts WebSocket events, and serves an operations dashboard for process lifecycle monitoring.

---

## 1. Architecture & Telemetry Flow

```
Hardware Microcontrollers (COMx) / Virtual Guns (SIM-1..4)
                       │
                       ▼
          Headless Tracker Service (Tracker/main.py)
           ├── Port 47000 (UDP) ──► Unreal Engine 5.8 (Direct Shot Delivery)
           └── Port 47001 (UDP) ──► FastAPI Backend (Port 8000)
                                      ├── In-Memory Gun Fleet State
                                      ├── Process Lifecycle Watchdog
                                      ├── REST API (/api/health, /api/tracker)
                                      ├── WebSocket (/ws/backend)
                                      └── Operations Dashboard (/)
```

### Telemetry Contracts (UDP Port 47001)

1. **Shot Event (`type: "shot"`)**:
```json
{
  "v": 1,
  "type": "shot",
  "gun": 1,
  "lane": 1,
  "x": 960.0,
  "y": 540.0,
  "display_width": 1920,
  "display_height": 1080,
  "round": 1,
  "cross_lane": false,
  "time_us": 1728471234567890
}
```

2. **Gun Status Event (`type: "gun_status"`)**:
```json
{
  "v": 1,
  "type": "gun_status",
  "gun": 1,
  "lane": 1,
  "port": "COM4",
  "connected": true,
  "shot_count": 4,
  "time_us": 1728471234567890
}
```

---

## 2. Directory Structure

```
Backend/
├── app/
│   ├── __init__.py            # Application package metadata
│   ├── main.py                # FastAPI app & lifespan coordinator
│   ├── config.py              # Configuration & path resolver
│   ├── schemas.py             # Pydantic schemas for UDP & REST
│   ├── api/
│   │   ├── __init__.py
│   │   ├── health.py          # /api/health and /api/health/details
│   │   └── tracker.py         # /api/tracker status, guns, process control
│   ├── services/
│   │   ├── __init__.py
│   │   ├── tracker_state.py   # In-memory gun fleet & freshness tracking
│   │   ├── tracker_listener.py# Asyncio UDP datagram server (47001)
│   │   └── tracker_process.py # Subprocess management, logs & crash recovery
│   └── websocket/
│       ├── __init__.py
│       └── manager.py         # Multi-client WebSocket connection manager
├── static/
│   ├── index.html             # Operations Dashboard web interface
│   ├── styles.css             # Dark charcoal & neon telemetry theme
│   └── app.js                 # WebSocket client & real-time telemetry renderer
├── tests/
│   ├── conftest.py            # Test fixtures & test client
│   ├── test_health.py         # Health endpoints
│   ├── test_udp_listener.py   # Datagram parsing, schemas & validation
│   ├── test_tracker_state.py  # Gun state & freshness timeouts
│   ├── test_process_manager.py# Process lifecycle & crash recovery
│   ├── test_websocket.py      # Real-time WebSocket broadcasts
│   └── test_api_tracker.py    # Process control REST endpoints
├── .env.example               # Template environment configuration
├── requirements.txt           # Backend Python dependencies
├── start_backend.py           # Single-process Uvicorn launcher
├── start_backend.bat          # Windows one-click launcher
└── README.md                  # This file
```

---

## 3. Quick Start & Launching

### A. One-Click Windows Launcher (Recommended)
Double-click `start_backend.bat` or run from terminal:
```cmd
.\start_backend.bat
```
This batch script will:
1. Detect Python or the root suite `.venv`.
2. Automatically create a dedicated `Backend\.venv` without touching or modifying the root `.venv`.
3. Install required dependencies on first run.
4. Launch the Backend HTTP server and UDP listener.
5. Automatically spawn the headless Tracker daemon.
6. Serve the dashboard at `http://127.0.0.1:8000/`.

### B. Launching from Python Terminal
```powershell
# Using the dedicated virtual environment
.\.venv\Scripts\python.exe start_backend.py
```

Optional CLI flags:
- `--open-browser`: Automatically opens the dashboard in your default browser.
- `--no-tracker`: Disables automatic Tracker subprocess launching.
- `--host <ip>`: Bind host (default: `127.0.0.1`).
- `--port <port>`: Bind port (default: `8000`).

---

## 4. Configuration Reference

Settings can be overridden in a `.env` file placed in `Backend/` (see `.env.example`):

| Variable | Default | Description |
|---|---|---|
| `BACKEND_HOST` | `127.0.0.1` | FastAPI HTTP bind IP |
| `BACKEND_PORT` | `8000` | FastAPI HTTP port |
| `UDP_HOST` | `127.0.0.1` | UDP listener bind host |
| `UDP_PORT` | `47001` | UDP listener port for Tracker telemetry |
| `TRACKER_AUTOSTART` | `true` | Launch Tracker automatically on startup |
| `TRACKER_MODE` | `script` | `script` (runs Python) or `exe` (runs binary) |
| `TRACKER_SCRIPT_PATH` | `../Tracker/main.py` | Path to Tracker script |
| `TRACKER_EXE_PATH` | `../Tracker/dist/Tracker.exe`| Path to compiled Tracker.exe |
| `TRACKER_PYTHON_PATH`| `../.venv/Scripts/python.exe` | Interpreter with PySide6/Tracker libraries |
| `TRACKER_STARTUP_TIMEOUT` | `5.0` | Seconds to wait for initial telemetry packet |
| `TRACKER_TELEMETRY_TIMEOUT` | `5.0` | Seconds before telemetry marks stale |
| `TRACKER_RESTART_ON_CRASH` | `true` | Automatically restart Tracker if it exits unexpectedly |
| `TRACKER_MAX_CRASH_RESTARTS` | `3` | Maximum automatic restart attempts |
| `LOCAL_ONLY_MANAGEMENT` | `true` | Restrict process start/stop/restart to localhost |
| `LOG_LEVEL` | `INFO` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |

---

## 5. REST & WebSocket API Reference

### Health Diagnostics
- `GET /api/health`: Basic uptime and server status.
- `GET /api/health/details`: Complete diagnostic snapshot (UDP listener metrics, Tracker PID, uptime, telemetry freshness, active guns).

### Tracker Telemetry & Process Management
- `GET /api/tracker/status`: Combined state of child Tracker process and incoming telemetry.
- `GET /api/tracker/guns`: List of registered guns, lanes, ports, connection status, and shot counts.
- `GET /api/tracker/events`: Buffer of recent shot and connection events.
- `POST /api/tracker/clear-events`: Clears the live event log buffer.
- `GET /api/tracker/logs`: Recent stdout/stderr lines from the child Tracker process.
- `POST /api/tracker/start`: Starts the configured Tracker process.
- `POST /api/tracker/stop`: Gracefully terminates only the Tracker process owned by this backend.
- `POST /api/tracker/restart`: Restarts the configured Tracker process.

### Live WebSocket Stream
- `WS /ws/backend`: Real-time bi-directional connection.
  - Broadcasts envelope: `{"topic": "<topic>", "data": <payload>, "timestamp": <epoch>}`
  - Topics: `shot`, `gun_status`, `tracker_started`, `tracker_stopped`, `tracker_crashed`, `tracker_log`, `udp_error`.

---

## 6. How to Confirm Tracker Connectivity

1. Open `http://127.0.0.1:8000/` in your browser.
2. Verify the top header status pills:
   - **Backend**: Green (Uptime running)
   - **Tracker Process**: Green (e.g. `Running (PID 4748)`)
   - **Telemetry**: Green (`Live Telemetry`)
   - **WebSocket**: Green (`Connected`)
3. Check the **Simulator Gun Controller Fleet** table:
   - Four virtual simulation guns (`SIM-1` to `SIM-4`) are displayed with `CONNECTED` badges and periodic keepalives.
4. Test shot delivery via terminal:
   ```powershell
   f:\Shooter\FiringSimulator\Software\.venv\Scripts\python.exe f:\Shooter\FiringSimulator\Software\Tracker\test_udp_stream.py
   ```
   The dashboard will instantly reflect the shot event in the **Live Telemetry Events** feed and increment the shot counter.

---

## 7. Troubleshooting

### Port Conflicts (WinError 10048)
If port 8000 or 47001 is already in use by another running instance:
```powershell
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | Select-Object OwningProcess
Stop-Process -Id <OwningProcess> -Force
```

### Tracker Fails to Start
- Verify that `TRACKER_PYTHON_PATH` points to the virtual environment containing `PySide6` (by default, `Software\.venv`).
- Check the **System Diagnostics & Output** tab on the dashboard to view real-time stderr logs.
- If running in executable mode (`TRACKER_MODE=exe`), ensure `Tracker.exe` exists at the configured path.
