@echo off
title Detecta AI - Restore Stable Checkpoint (v3.0 - Indoor Optimized + No Hallucinations)
echo ========================================================
echo        DETECTA AI - ONE-CLICK V3 CHECKPOINT RESTORATION
echo ========================================================
echo.
echo Restoring verified working files from:
echo c:\detecta\checkpoints\v3_stable_indoor_optimized
echo.

echo 1. Terminating running dashboard and python processes...
taskkill /F /IM python.exe /T 2>nul
timeout /t 1 /nobreak >nul

echo 2. Copying clean desktop_client files...
copy /Y "c:\detecta\checkpoints\v3_stable_indoor_optimized\desktop_client\ai_engine.py" "c:\detecta\desktop_client\ai_engine.py" >nul
copy /Y "c:\detecta\checkpoints\v3_stable_indoor_optimized\desktop_client\camera_stream.py" "c:\detecta\desktop_client\camera_stream.py" >nul
copy /Y "c:\detecta\checkpoints\v3_stable_indoor_optimized\desktop_client\known_faces.pkl" "c:\detecta\desktop_client\known_faces.pkl" >nul
if exist "c:\detecta\checkpoints\v3_stable_indoor_optimized\desktop_client\gesture_recognizer.task" (
    copy /Y "c:\detecta\checkpoints\v3_stable_indoor_optimized\desktop_client\gesture_recognizer.task" "c:\detecta\desktop_client\gesture_recognizer.task" >nul
)

echo 3. Copying clean web_dashboard files...
copy /Y "c:\detecta\checkpoints\v3_stable_indoor_optimized\web_dashboard\backend.py" "c:\detecta\web_dashboard\backend.py" >nul
copy /Y "c:\detecta\checkpoints\v3_stable_indoor_optimized\web_dashboard\config.json" "c:\detecta\web_dashboard\config.json" >nul
copy /Y "c:\detecta\checkpoints\v3_stable_indoor_optimized\web_dashboard\templates\index.html" "c:\detecta\web_dashboard\templates\index.html" >nul

echo 4. Copying clean firmware files...
copy /Y "c:\detecta\checkpoints\v3_stable_indoor_optimized\firmware\pio_project\src\main.cpp" "c:\detecta\firmware\pio_project\src\main.cpp" >nul
copy /Y "c:\detecta\checkpoints\v3_stable_indoor_optimized\firmware\pio_project\platformio.ini" "c:\detecta\firmware\pio_project\platformio.ini" >nul

echo 5. Copying root runners...
copy /Y "c:\detecta\checkpoints\v3_stable_indoor_optimized\run_dashboard.py" "c:\detecta\run_dashboard.py" >nul
copy /Y "c:\detecta\checkpoints\v3_stable_indoor_optimized\auto_detect_esp32.py" "c:\detecta\auto_detect_esp32.py" >nul

echo.
echo ========================================================
echo SUCCESS: All verified files restored to stable v3 state!
echo ========================================================
echo.
echo To start dashboard:
echo   c:\detecta\.venv\Scripts\python.exe c:\detecta\run_dashboard.py
echo.
pause
