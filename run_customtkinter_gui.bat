@echo off
title Detecta CustomTkinter GUI Client
cd /d %~dp0
echo ===================================================
echo  Starting Detecta CustomTkinter GUI Client
echo ===================================================
call .venv\Scripts\activate.bat
python desktop_client_v1_stable/app.py
pause
