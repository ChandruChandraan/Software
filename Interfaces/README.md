# FiringSim — Interfaces Module

This folder contains the standalone client interfaces and frontend UI presentation layer for the FiringSim platform.

## Folder Structure

```
Software/Interfaces/
├── static/
│   ├── index.html        # HTML structure of the Tactical Operations Console
│   ├── styles.css        # Modern glowing dark theme, layout, responsive cards
│   └── app.js            # WebSocket client, gun telemetry handling, event feed
├── desktop_app.py        # Native desktop window app (PySide6 QWebEngineView)
├── start_interface.bat   # Launcher to run the desktop application
├── build_desktop_exe.py  # PyInstaller build script to compile to standalone .exe
└── build_desktop_exe.bat # One-click batch build script for .exe
```

## How to Run

### 1. Launch the Desktop UI Window Directly
Double-click `start_interface.bat` (or `Software/start_desktop_ui.bat` from the root).
- Embeds the HTML/CSS interface inside a native desktop frame.
- Automatically coordinates with the Backend and Tracker.
- Does not open in a standard web browser.

### 2. Compile to Standalone Executable (.exe)
Double-click `build_desktop_exe.bat`.
- Compiles the interface and WebEngine runtime into `dist/FiringSim_UI/FiringSim_UI.exe`.
