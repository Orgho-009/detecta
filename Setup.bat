@echo off
title Detecta — Automated Environment Setup
cd /d %~dp0
echo ===================================================
echo  DETECTA — Environment and Dependency Installer
echo ===================================================
echo.

where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [!] Python is not currently found in your system PATH.
    echo [*] Checking Windows Package Manager (winget)...
    where winget >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        echo [*] Installing Python 3.10 automatically...
        winget install -e --id Python.Python.3.10 --accept-source-agreements --accept-package-agreements
        set "PATH=%LOCALAPPDATA%\Programs\Python\Python310;%LOCALAPPDATA%\Programs\Python\Python310\Scripts;%PATH%"
    ) else (
        echo [ERROR] Please install Python 3.10 from https://www.python.org/downloads/
        echo [ERROR] Make sure to check 'Add python.exe to PATH' during installation.
        pause
        exit /b 1
    )
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

where nvidia-smi >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [*] NVIDIA GPU detected! Configuring CUDA 12.1 hardware acceleration...
    pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
) else (
    echo [*] Standard environment detected (CPU fallback).
)

echo [*] Installing required dependencies from requirements.txt...
pip install -r requirements.txt

echo.
echo ===================================================
echo  Installation completed successfully!
echo  You can now launch the application via Detecta.exe
echo ===================================================
echo.
pause
