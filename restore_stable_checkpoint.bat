@echo off
title Detecta AI - Restore Stable Checkpoint (v1.0 - 25 FPS)
echo ========================================================
echo        DETECTA AI - ONE-CLICK CHECKPOINT RESTORATION
echo ========================================================
echo.
echo Restoring verified working files from:
echo c:\detecta\checkpoints\stable_v1_working
echo.

echo 1. Terminating running dashboard and python processes...
taskkill /F /IM python.exe /T 2>nul
timeout /t 1 /nobreak >nul

echo 2. Copying clean desktop_client files...
copy /Y "c:\detecta\checkpoints\stable_v1_working\desktop_client\ai_engine.py" "c:\detecta\desktop_client\ai_engine.py" >nul
copy /Y "c:\detecta\checkpoints\stable_v1_working\desktop_client\camera_stream.py" "c:\detecta\desktop_client\camera_stream.py" >nul
copy /Y "c:\detecta\checkpoints\stable_v1_working\desktop_client\known_faces.pkl" "c:\detecta\desktop_client\known_faces.pkl" >nul

echo 3. Copying clean web_dashboard files...
copy /Y "c:\detecta\checkpoints\stable_v1_working\web_dashboard\backend.py" "c:\detecta\web_dashboard\backend.py" >nul
copy /Y "c:\detecta\checkpoints\stable_v1_working\web_dashboard\config.json" "c:\detecta\web_dashboard\config.json" >nul
copy /Y "c:\detecta\checkpoints\stable_v1_working\web_dashboard\templates\index.html" "c:\detecta\web_dashboard\templates\index.html" >nul

echo 4. Copying clean firmware files...
copy /Y "c:\detecta\checkpoints\stable_v1_working\firmware\pio_project\src\main.cpp" "c:\detecta\firmware\pio_project\src\main.cpp" >nul
copy /Y "c:\detecta\checkpoints\stable_v1_working\firmware\pio_project\platformio.ini" "c:\detecta\firmware\pio_project\platformio.ini" >nul

echo 5. Copying root runners...
copy /Y "c:\detecta\checkpoints\stable_v1_working\run_dashboard.py" "c:\detecta\run_dashboard.py" >nul

echo.
echo ========================================================
echo SUCCESS: All verified files restored to stable v1 state!
echo ========================================================
echo.
echo If you modified ESP32 firmware, reflash by running:
echo   c:\detecta\.venv\Scripts\platformio.exe run -d c:\detecta\firmware\pio_project -t upload --upload-port COM6
echo.
echo To start dashboard:
echo   run_web_dashboard.bat
echo.
pause
