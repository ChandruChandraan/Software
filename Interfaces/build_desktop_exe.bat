@echo off
setlocal

REM Resolve directory of this script and parent repository directory
set "INTERFACE_DIR=%~dp0"
for %%I in ("%INTERFACE_DIR%..") do set "ROOT_DIR=%%~fI"

cd /d "%INTERFACE_DIR%"

echo =====================================================================
echo  FiringSim - Build Standalone Desktop Executable (.exe)
echo =====================================================================
echo.

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
    echo [ERROR] Python environment was not found.
    pause
    exit /b 1
)

echo Using Python: %TARGET_PYTHON%
"%TARGET_PYTHON%" "%INTERFACE_DIR%build_desktop_exe.py"

if errorlevel 1 (
    echo.
    echo [Build failed with error code %errorlevel%]
    pause
    exit /b %errorlevel%
)

echo.
echo Build complete. The executable is located at:
echo %INTERFACE_DIR%dist\FiringSim_UI\FiringSim_UI.exe
echo.
pause
