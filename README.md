# 🛡️ Detecta — High-Performance AI Surveillance System (Windows 11)

Consolidated AI Surveillance and Security Camera Monitor with NVIDIA RTX 4050 CUDA hardware acceleration.

---

## 🚀 Quick Start (Running on Windows)

The project has been extracted, configured, and verified in `c:\detecta`.

### 1. Web Intelligence Dashboard (Modern Glassmorphism UI)
Double-click `run_web_dashboard.bat` or run:
```powershell
.\.venv\Scripts\activate.ps1
python run_dashboard.py
```
Open **[http://localhost:8000](http://localhost:8000)** in your browser:
- Live MJPEG video stream with YOLO11 Human Detection.
- Real-time Threat & Inventory telemetry.
- Face Database Manager (ArcFace 512-d embeddings).
- Dynamic IP switching (type ESP32 IP or `0` for local webcam).

### 2. OpenCV HUD Client (DirectShow Native Window)
Double-click `run_desktop_hud.bat` or run:
```powershell
.\.venv\Scripts\activate.ps1
python desktop_client/app.py 192.168.0.216
```
*(If ESP32 is offline, automatically falls back to local camera `0`).*
- Keybindings: `[S]` Snapshot, `[E]` Enroll Face, `[R]` Change IP, `[Q]` Quit.

### 3. CustomTkinter GUI Client
Double-click `run_customtkinter_gui.bat` or run:
```powershell
.\.venv\Scripts\activate.ps1
python desktop_client_v1_stable/app.py
```

---

## ⚙️ Architecture & Hardware Acceleration

| Component | Target / Technology | Status |
| :--- | :--- | :--- |
| **GPU Acceleration** | NVIDIA GeForce RTX 4050 Laptop GPU (6GB VRAM) | ✅ Active (CUDA 12.1) |
| **Object Detection** | Ultralytics YOLO11n (FP16 Tensor Cores, ~2.5 ms) | ✅ Active |
| **Facial Recognition** | InsightFace ArcFace (`buffalo_l` on `onnxruntime-gpu`) | ✅ Active |
| **Stream Ingest** | OpenCV FFmpeg Low-Latency Non-Buffering (`fflags;nobuffer`) | ✅ Active |
| **Firmware** | ESP32-CAM Dedicated Port 81 (`/stream`) with Dynamic Bitrate Clamp | ✅ Ready in `firmware/` |

---

## 🔧 ESP32-CAM Firmware Upload (PlatformIO / Arduino IDE)
Source files located in:
- `firmware/pio_project/src/main.cpp`
- `firmware/pio_project/src/camera_pins.h`

**Improvements applied:**
- Dynamic JPEG Quality Scaling (keeps packet count < 15 during motion blur to eliminate 2.4GHz buffering).
- Reduced FreeRTOS task delay to 1ms.
- Port 81 purity (strictly dedicated to `/stream`).
