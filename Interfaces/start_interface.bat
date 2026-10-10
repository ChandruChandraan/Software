@echo off
setlocal

REM Resolve directory of this script and parent repository directory
set "INTERFACE_DIR=%~dp0"
for %%I in ("%INTERFACE_DIR%..") do set "ROOT_DIR=%%~fI"

cd /d "%INTERFACE_DIR%"

echo =====================================================================
echo  FiringSim - Dedicated Desktop UI Application (HTML/CSS Framework)
echo =====================================================================
echo.

REM 1. If compiled standalone EXE exists, launch it directly
if exist "%INTERFACE_DIR%dist\FiringSim_UI\FiringSim_UI.exe" (
    echo [Launching compiled standalone EXE]
    start "" "%INTERFACE_DIR%dist\FiringSim_UI\FiringSim_UI.exe" %*
    exit /b 0
)

REM 2. Determine Python interpreter
set "TARGET_PYTHON="
if exist "%ROOT_DIR%\.venv\Scripts\python.exe" set "TARGET_PYTHON=%ROOT_DIR%\.venv\Scripts\python.exe"
if "%TARGET_PYTHON%"=="" (
    if exist "%ROOT_DIR%\Backend\.venv\Scripts\python.exe" set "TARGET_PYTHON=%ROOT_DIR%\Backend\.venv\Scripts\python.exe"
)
if "%TARGET_PYTHON%"=="" (
    for /f "delims=" %%I in ('where python 2^>nul') do (
        if "%TARGET_PYTHON%"=="" set "TARGET_PYTHON=%%I"
    )
)

if "%TARGET_PYTHON%"=="" (
    echo [ERROR] No suitable Python interpreter found.
    pause
    exit /b 1
)

echo [1/2] Using Python: %TARGET_PYTHON%
echo [2/2] Launching FiringSim Desktop UI Window...
echo.

"%TARGET_PYTHON%" "%INTERFACE_DIR%desktop_app.py" %*

if errorlevel 1 (
    echo.
    echo [Desktop App exited with status %errorlevel%]
    pause
)
