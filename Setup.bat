@echo off
title Detecta — Automated Environment Setup
cd /d %~dp0
echo ===================================================
echo  DETECTA — Environment and Dependency Installer
echo ===================================================
echo.

where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python is not installed or not in system PATH.
    echo Please install Python 3.10 or 3.11 from python.org and check 'Add python.exe to PATH'.
    pause
    exit /b 1
)

if not exist ".venv" (
    echo [*] Creating virtual environment (.venv)...
    python -m venv .venv
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
)

echo [*] Activating virtual environment...
call .venv\Scripts\activate.bat

echo [*] Upgrading pip...
python -m pip install --upgrade pip

echo [*] Installing required dependencies from requirements.txt...
pip install -r requirements.txt

echo.
echo ===================================================
echo  Installation completed successfully!
echo  You can now launch the application via Detecta.exe
echo ===================================================
echo.
pause
