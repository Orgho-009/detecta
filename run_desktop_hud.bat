@echo off
title Detecta OpenCV HUD Client
cd /d %~dp0
echo ===================================================
echo  Starting Detecta OpenCV HUD Client (DirectShow)
echo  Default IP: 192.168.0.216 (or local webcam fallback)
echo  Controls: [S] Snapshot  [E] Enroll Face  [R] Change IP  [Q] Quit
echo ===================================================
call .venv\Scripts\activate.bat
python desktop_client/app.py %1
pause
