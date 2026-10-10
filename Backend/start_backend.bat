@echo off
setlocal

REM Resolve directory of this script and parent repository directory
set "BACKEND_DIR=%~dp0"
for %%I in ("%BACKEND_DIR%..") do set "ROOT_DIR=%%~fI"

cd /d "%BACKEND_DIR%"

echo [1/4] Checking Python environment...

REM Check if root .venv exists or system python exists
set "BASE_PYTHON="
if exist "%ROOT_DIR%\.venv\Scripts\python.exe" set "BASE_PYTHON=%ROOT_DIR%\.venv\Scripts\python.exe"
if "%BASE_PYTHON%"=="" (
    for /f "delims=" %%I in ('where python 2^>nul') do (
        if "%BASE_PYTHON%"=="" set "BASE_PYTHON=%%I"
    )
)

if "%BASE_PYTHON%"=="" (
    echo [ERROR] Python was not found on PATH or in root .venv
    pause
    exit /b 1
)

REM Use dedicated backend virtual environment
if not exist "%BACKEND_DIR%.venv\Scripts\python.exe" (
    echo [2/4] Initializing dedicated Backend virtual environment: .venv
    "%BASE_PYTHON%" -m venv "%BACKEND_DIR%.venv"
    if errorlevel 1 (
        echo [ERROR] Failed to create dedicated virtual environment.
        pause
        exit /b 1
    )
    echo [3/4] Installing Backend dependencies from requirements.txt...
    "%BACKEND_DIR%.venv\Scripts\pip.exe" install --upgrade pip
    "%BACKEND_DIR%.venv\Scripts\pip.exe" install -r "%BACKEND_DIR%requirements.txt"
) else (
    echo [2/4] Dedicated Backend virtual environment found: .venv
    echo [3/4] Ready.
)

echo [4/4] Starting FiringSim Backend Application...
echo.
echo Dashboard URL: http://127.0.0.1:8000/
echo UDP Listener : 127.0.0.1:47001
echo.

"%BACKEND_DIR%.venv\Scripts\python.exe" "%BACKEND_DIR%start_backend.py" %*

if errorlevel 1 (
    echo.
    echo [Backend exited with error code %errorlevel%]
    pause
)
