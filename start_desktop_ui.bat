@echo off
setlocal

REM Resolve directory of this script
set "ROOT_DIR=%~dp0"

cd /d "%ROOT_DIR%"

echo =====================================================================
echo  FiringSim - Tactical Operations Desktop Console (.EXE Launcher)
echo =====================================================================
echo.

REM 1. Prefer compiled standalone executable if available
if exist "%ROOT_DIR%Interfaces\dist\FiringSim_UI\FiringSim_UI.exe" (
    echo [Launching compiled standalone EXE]
    start "" "%ROOT_DIR%Interfaces\dist\FiringSim_UI\FiringSim_UI.exe"
    exit /b 0
)

REM 2. Fall back to Interfaces launcher
echo [Launching Interfaces Desktop Application...]
call "%ROOT_DIR%Interfaces\start_interface.bat"
