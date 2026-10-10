"""
Build script to compile FiringSim desktop app into a standalone Windows .exe using PyInstaller.
"""

from pathlib import Path
import subprocess
import sys

INTERFACE_DIR = Path(__file__).resolve().parent
ROOT_DIR = INTERFACE_DIR.parent
BACKEND_DIR = ROOT_DIR / "Backend"

# Locate PyInstaller in root or backend venv
PYINSTALLER_EXE = ROOT_DIR / ".venv" / "Scripts" / "pyinstaller.exe"
if not PYINSTALLER_EXE.exists():
    PYINSTALLER_EXE = BACKEND_DIR / ".venv" / "Scripts" / "pyinstaller.exe"
if not PYINSTALLER_EXE.exists():
    PYINSTALLER_EXE = Path(sys.executable).parent / "pyinstaller.exe"


def build():
    print("==================================================================")
    print(" Compiling FiringSim Desktop UI (HTML/CSS Framework) to .exe")
    print("==================================================================")

    static_dir = INTERFACE_DIR / "static"
    app_dir = BACKEND_DIR / "app"

    cmd = [
        str(PYINSTALLER_EXE),
        "--name=FiringSim_UI",
        "--onedir",
        "--noconfirm",
        "--clean",
        "--windowed",
        f"--add-data={static_dir};static",
        f"--add-data={app_dir};app",
        f"--paths={BACKEND_DIR}",
        "--hidden-import=uvicorn.logging",
        "--hidden-import=uvicorn.loops",
        "--hidden-import=uvicorn.loops.auto",
        "--hidden-import=uvicorn.protocols",
        "--hidden-import=uvicorn.protocols.http",
        "--hidden-import=uvicorn.protocols.http.auto",
        "--hidden-import=uvicorn.protocols.websockets",
        "--hidden-import=uvicorn.protocols.websockets.auto",
        "--hidden-import=uvicorn.lifespan",
        "--hidden-import=uvicorn.lifespan.on",
        "--hidden-import=websockets",
        "--hidden-import=fastapi",
        "--hidden-import=pydantic_settings",
        "--hidden-import=PySide6.QtWebEngineWidgets",
        "--hidden-import=PySide6.QtWebEngineCore",
        str(INTERFACE_DIR / "desktop_app.py"),
    ]

    print(f"\n[Command] {' '.join(cmd)}\n")
    result = subprocess.run(cmd, cwd=str(INTERFACE_DIR))

    if result.returncode == 0:
        exe_path = INTERFACE_DIR / "dist" / "FiringSim_UI" / "FiringSim_UI.exe"
        print("\n==================================================================")
        print(" [SUCCESS] Standalone Desktop Executable Built Successfully!")
        print(f" Executable: {exe_path}")
        print("==================================================================")
    else:
        print(f"\n[ERROR] PyInstaller failed with exit code: {result.returncode}")
        sys.exit(result.returncode)


if __name__ == "__main__":
    build()
