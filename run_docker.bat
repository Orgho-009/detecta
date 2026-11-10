@echo off
title Detecta — Docker Container Launcher
cd /d %~dp0
echo ===================================================
echo  DETECTA — 1-Click Docker Container Launcher
echo ===================================================
echo.

where docker >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Docker is not installed or Docker Desktop is not running.
    echo Please install Docker Desktop from https://www.docker.com/ and start it.
    pause
    exit /b 1
)

echo [*] Building and launching Detecta AI container...
docker compose up --build -d

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ===================================================
    echo  Detecta is running successfully!
    echo  Access the Dashboard at: http://localhost:8000
    echo ===================================================
    echo.
    echo [*] Opening dashboard in your default browser...
    start http://localhost:8000
    echo.
    echo Press any key to view live container logs (Ctrl+C to exit logs)...
    pause >nul
    docker compose logs -f
) else (
    echo [ERROR] Docker build/startup failed.
    pause
)
