@echo off
title Detecta Web Intelligence Dashboard
cd /d %~dp0
echo ===================================================
echo  Starting Detecta Web Intelligence Dashboard
echo  Serving on: http://localhost:8000
echo ===================================================
call .venv\Scripts\activate.bat
python run_dashboard.py
pause
