#!/usr/bin/env python3
"""
Detecta — Intelligent Security Camera Monitor
Architecture strictly aligned with Home-Intelligent:
- Pure single-endpoint Port 81 MJPEG ingestion (http://<IP>:81/stream)
- Dedicated CameraStream reader thread with line-speed socket draining
- Ultralytics YOLO11 Human Detection (MPS / CUDA / Neural Engine accelerated)
- Synchronous 3-frame strided Face Recognition on 0.5x downscaled frame
- Hardware-accelerated native display window (cv2.imshow) with real-time HUD
- Zero background polling (no port 80 requests, no battery queries, no subprocess freezes)
"""
import sys
import os
import time
from datetime import datetime
import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from camera_stream import CameraStream
from ai_engine import AIEngine

DEFAULT_IP = "192.168.0.216"
BACKUP_DIR = "backups"
os.makedirs(BACKUP_DIR, exist_ok=True)

def draw_hud(display, fps, ip, inventory, total_frames):
    """Draws a clean, modern HUD overlay onto the frame."""
    h, w = display.shape[:2]

    # Top Status Bar
    cv2.rectangle(display, (10, 10), (380, 70), (15, 23, 42), -1)
    cv2.rectangle(display, (10, 10), (380, 70), (56, 189, 248), 1)

    # Active indicator dot
    cv2.circle(display, (26, 40), 6, (0, 255, 0), -1)

    # FPS Metric
    fps_color = (0, 255, 0) if fps >= 10 else (0, 200, 255) if fps >= 5 else (0, 0, 255)
    cv2.putText(display, f"FPS: {fps:4.1f}", (40, 47), cv2.FONT_HERSHEY_DUPLEX, 0.75, fps_color, 2, cv2.LINE_AA)

    # Resolution & IP
    cv2.putText(display, f"| {w}x{h} VGA | {ip}", (165, 36), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (203, 213, 225), 1, cv2.LINE_AA)

    # Target indicator
    hum_count = inventory.get("Human", 0)
    hum_text = f"Human Detected: {hum_count}" if hum_count > 0 else "Area Secure (No humans)"
    hum_col = (0, 200, 255) if hum_count > 0 else (148, 163, 184)
    cv2.putText(display, hum_text, (165, 56), cv2.FONT_HERSHEY_SIMPLEX, 0.45, hum_col, 1, cv2.LINE_AA)

    # Bottom Helper Bar
    cv2.rectangle(display, (10, h - 36), (420, h - 10), (15, 23, 42), -1)
    cv2.rectangle(display, (10, h - 36), (420, h - 10), (71, 85, 105), 1)
    cv2.putText(display, "[S] Snapshot  [E] Enroll Face  [R] Change IP  [Q] Quit", 
                (20, h - 18), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (226, 232, 240), 1, cv2.LINE_AA)

def main():
    cam_ip = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_IP
    stream_url = f"http://{cam_ip}:81/stream"

    print("=" * 60)
    print(" DETECTA — High-Performance AI Security Monitor")
    print(f" Target Camera: {stream_url}")
    print(" Architecture: 100% Home-Intelligent Parity")
    print("=" * 60)

    # 1. Initialize AI Engine
    yolo_model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "yolo11n.pt")
    if not os.path.exists(yolo_model_path):
        yolo_model_path = "yolo11n.pt"

    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "known_faces.pkl")
    ai = AIEngine(yolo_path=yolo_model_path, db_path=db_path)

    # 2. Connect to Camera
    print(f"\n[Detecta] Connecting CameraStream to {stream_url}...")
    cam = CameraStream(stream_url, buffer_size=2).start()

    t_wait = time.time()
    while cam.read() is None and time.time() - t_wait < 5.0:
        time.sleep(0.05)

    if cam.read() is None:
        print(f"[Detecta] Notice: Unable to connect to {stream_url}.")
        print("[Detecta] Checking local camera (device 0) as fallback...")
        cam.stop()
        cam = CameraStream(0, buffer_size=2).start()
        t_wait = time.time()
        while cam.read() is None and time.time() - t_wait < 3.0:
            time.sleep(0.05)
        if cam.read() is None:
            print("[Detecta] Error: Neither ESP32-CAM nor local webcam could be opened.")
            cam.stop()
            sys.exit(1)
        cam_ip = "Local-Webcam (0)"

    print("[Detecta] Connected successfully! Live window active.")
    window_name = "Detecta — Live AI Surveillance Monitor"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, 640, 480)

    total_frames = 0
    t_start = time.time()
    rolling_fps = 0.0

    try:
        while True:
            raw_frame = cam.read()
            if raw_frame is None:
                time.sleep(0.01)
                continue

            total_frames += 1

            # Run AI Pipeline
            annotated_frame, inventory = ai.process(raw_frame)

            # Compute FPS
            elapsed = time.time() - t_start
            if elapsed >= 0.5:
                rolling_fps = total_frames / elapsed
                total_frames = 0
                t_start = time.time()

            # Render HUD
            draw_hud(annotated_frame, rolling_fps, cam_ip, inventory, total_frames)

            # Render Window
            cv2.imshow(window_name, annotated_frame)
            key = cv2.waitKey(1) & 0xFF

            if key == ord('q') or key == ord('Q'):
                print("[Detecta] Exiting by user command.")
                break
            elif key == ord('s') or key == ord('S'):
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                snap_path = os.path.join(BACKUP_DIR, f"snapshot_{ts}.jpg")
                cv2.imwrite(snap_path, raw_frame)
                print(f"[Detecta] High-res Snapshot saved: {snap_path}")
            elif key == ord('e') or key == ord('E'):
                print("\n" + "-" * 50)
                name = input("[Detecta Enrollment] Enter person's name: ").strip()
                if name:
                    ok, msg = ai.enroll_face_from_frame(raw_frame, name)
                    print(f"[Detecta Enrollment] {msg}")
                print("-" * 50 + "\n")
            elif key == ord('r') or key == ord('R'):
                new_ip = input("[Detecta] Enter new camera IP: ").strip()
                if new_ip:
                    cam_ip = new_ip
                    stream_url = f"http://{cam_ip}:81/stream"
                    cam.stop()
                    cam = CameraStream(stream_url, buffer_size=2).start()
                    print(f"[Detecta] Reconnected to {stream_url}")

    finally:
        cam.stop()
        cv2.destroyAllWindows()
        print("[Detecta] Shutdown complete.")

if __name__ == "__main__":
    main()
