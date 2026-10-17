# FiringSim — Interfaces Module (React + TypeScript + Shadcn Black & White Edition)

This folder contains the tactical client interface and frontend presentation layer for the FiringSim marksmanship simulation platform.

Built with **React 19**, **TypeScript**, **Tailwind CSS**, and **Shadcn UI** adhering to an ultra-clean **Full Black and White (Monochrome Noir)** aesthetic.

---

## Folder Structure

```
Software/Interfaces/
├── src/
│   ├── components/
│   │   ├── ui/                    # Shadcn UI primitives (Button, Card, Badge, Table, Dialog, Tabs)
│   │   ├── Sidebar.tsx            # Tactical sidebar, cockpit clock & live telemetry
│   │   ├── ScenarioSelector.tsx   # 3D simulator level coordinator & selector
│   │   ├── GunsTable.tsx          # Real-time hardware weapon fleet matrix
│   │   ├── LiveShotFeed.tsx       # Live ballistic shot stream & telemetry
│   │   ├── SubsystemManager.tsx   # Tracker, Unreal 3D & Screen overlay process orchestrator
│   │   ├── DiagnosticsPanel.tsx   # Stdout/Stderr logs and raw UDP error telemetry
│   │   ├── SplashScreen.tsx       # Black & White radar ring initialization screen
│   │   └── ShutdownScreen.tsx     # Clean shutdown sequence screen
│   ├── lib/
│   │   └── utils.ts               # Shadcn styling utilities (cn, formatters)
│   ├── types/
│   │   └── simulator.ts           # TypeScript interfaces for guns, events, telemetry
│   ├── App.tsx                    # Main operations console application
│   ├── main.tsx                   # React DOM entry point
│   └── index.css                  # Tailwind & Shadcn Monochrome design tokens
├── static/                        # Production build output (served by FastAPI & PySide6)
├── legacy_static/                 # Preserved backup of original legacy assets
├── desktop_app.py                 # Standalone native desktop window app (PySide6 QWebEngineView)
├── start_interface.bat            # Launcher to run the desktop application
├── build_desktop_exe.py           # PyInstaller build script to compile to standalone .exe
├── build_desktop_exe.bat          # One-click batch build script for .exe
├── package.json                   # Node dependencies and build scripts
├── vite.config.ts                 # Vite bundler configuration (proxies /api and /ws)
├── tailwind.config.js             # Black & White theme styling configuration
└── tsconfig.json                  # TypeScript compiler settings
```

---

## Development & Building

### 1. Run React Vite Development Server (Hot Reload)
```bash
cd Software/Interfaces
npm run dev
```
Runs at `http://localhost:5173` with automatic reverse proxy to Backend API and WebSocket at `http://127.0.0.1:8080`.

### 2. Compile Production Bundle
```bash
cd Software/Interfaces
npm run build
```
Compiles and bundles React + TypeScript into `Interfaces/static/`.

---

## Desktop Application

### 1. Launch the Desktop UI Window Directly
Double-click `start_interface.bat` (or `Software/start_desktop_ui.bat` from the root).
- Embeds the full Black & White interface inside a native desktop frame using PySide6 WebEngine.
- Automatically coordinates with the Backend and Tracker.
- Supports fullscreen toggle with **F11**.

### 2. Compile to Standalone Executable (.exe)
Double-click `build_desktop_exe.bat`.
- Compiles the interface and WebEngine runtime into `dist/FiringSim_UI/FiringSim_UI.exe`.
