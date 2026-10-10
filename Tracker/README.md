# Firing Simulator — Headless Tracker Service

High-speed headless multi-gun hardware coordinator, USB serial processor, and dual-destination UDP streaming daemon for the Firing Training Simulator.

---

## 1. Architecture Overview

```
Arduino Gun 1 (COMx) ──┐
Arduino Gun 2 (COMy) ──┼──► SerialDeviceManager ──► MultiGunManager ──► UDP Client ──► Unreal Engine 5.8 (Port 47000)
Arduino Gun 3 (COMz) ──┤          (115200 Baud)         │                             └─► FastAPI Backend  (Port 47001)
Arduino Gun 4 (COMw) ──┘                                │
                                                        ▼
                                           Separate Projector Overlay
                                             (`python overlay.py`)
```

- **Tracker Daemon (`Tracker.exe`)**: Completely **headless**. No window or GUI dashboard. Manages USB serial connections, watchdog keepalives, sequence validation, and dual UDP packet transmission.
- **Projector Overlay (`overlay.py`)**: Standalone transparent projector reticle overlay window run separately when physical projector calibration/aim projection is needed.
- **Instructor Console**: The **single unified UI** for simulator monitoring and control.

---

## 2. Directory Structure

```
Tracker/
├── core/
│   ├── config.py              # Network IPs, ports, and hardware parameters
│   └── gun_state.py           # Independent per-gun state and MultiGunManager
├── devices/
│   └── serial_manager.py      # Non-blocking USB serial manager & 4-gun simulation
├── network/
│   └── udp_client.py          # Low-latency UDP client (Unreal: 47000, Backend: 47001)
├── ui/
│   ├── display_manager.py     # Win32 display detection and projector metrics
│   ├── overlay_window.py      # Independent multi-layer projector overlay window
│   └── unreal_process.py      # Unreal Engine process lifecycle manager
├── dist/
│   └── Tracker.exe            # Self-contained headless Windows executable
├── Guns/
│   └── Guns.ino               # Arduino microcontroller firmware
├── config/
│   └── tracker_config.json    # JSON runtime configuration
├── headless_tracker.py        # Core headless daemon runner
├── main.py                    # Root service launcher (runs headless daemon)
├── overlay.py                 # Standalone projector overlay application launcher
├── requirements.txt           # Dependencies
└── README.md                  # This file
```

---

## 3. Running the Tracker

### A. Run Headless Executable
```powershell
.\dist\Tracker.exe
```

### B. Command-Line Options
```powershell
.\dist\Tracker.exe --help

Options:
  --unreal-host <ip>        Unreal UDP host (Default: 127.0.0.1)
  --unreal-port <port>      Unreal UDP port (Default: 47000)
  --backend-host <ip>       Backend UDP host (Default: 127.0.0.1)
  --backend-port <port>     Backend UDP port (Default: 47001)
  --no-backend              Disable telemetry streaming to Backend
  --no-sim                  Disable simulated virtual guns (real hardware only)
  --sim-guns <count>        Number of simulated virtual guns (Default: 4)
  --launch-unreal           Auto-launch Unreal Engine process
  --display-width <px>      Target display viewport width (Default: 1920)
  --display-height <px>     Target display viewport height (Default: 1080)
  --log-level <level>       Logging verbosity: DEBUG, INFO, WARNING, ERROR
```

### C. Running from Source
```powershell
# Using software suite virtual environment:
..\.venv\Scripts\python.exe main.py
```

### D. Launching the Standalone Projector Overlay
```powershell
..\.venv\Scripts\python.exe overlay.py
```

---

## 4. Telemetry Contracts

### Unreal Engine (UDP Port 47000)
Sent once per valid trigger edge pull:
```json
{
  "type": "shot",
  "gun": 1,
  "lane": 1,
  "x": 960,
  "y": 540,
  "cross_lane": false,
  "round": 1,
  "display_width": 1920,
  "display_height": 1080
}
```

### Python Backend (UDP Port 47001)
1. Shot Event:
```json
{
  "v": 1,
  "type": "shot",
  "gun": 1,
  "lane": 1,
  "x": 960,
  "y": 540,
  "display_width": 1920,
  "display_height": 1080,
  "round": 1,
  "cross_lane": false,
  "time_us": 1728471234567890
}
```

2. Gun Status Event:
```json
{
  "v": 1,
  "type": "gun_status",
  "gun": 1,
  "lane": 1,
  "port": "COM4",
  "connected": true,
  "shot_count": 1,
  "time_us": 1728471234567890
}
```
