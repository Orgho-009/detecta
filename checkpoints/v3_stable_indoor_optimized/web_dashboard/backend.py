import os
import sys
import time
import json
import asyncio
import threading
from datetime import datetime
import cv2
import numpy as np
import requests
from pydantic import BaseModel
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse, HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT_DIR, "desktop_client"))

from camera_stream import CameraStream
from ai_engine import AIEngine

CONFIG_PATH = os.path.join(ROOT_DIR, "web_dashboard", "config.json")
DATABASE_DIR = os.path.join(ROOT_DIR, "database")
BACKUP_DIR = os.path.join(ROOT_DIR, "backups")
TEMPLATES_DIR = os.path.join(ROOT_DIR, "web_dashboard", "templates")
STATIC_DIR = os.path.join(ROOT_DIR, "web_dashboard", "static")

os.makedirs(DATABASE_DIR, exist_ok=True)
os.makedirs(BACKUP_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "camera_ip": "192.168.0.52",
        "telegram_token": "8630270967:AAEpNahDspEU2wG2yTcOb305oTE2RKxEfx0",
        "telegram_chat_id": "-1004297425384",
        "conf_threshold": 0.3,
        "face_tolerance": 0.45
    }

def save_config(cfg):
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2)

config = load_config()

app = FastAPI(title="Detecta AI Security Camera Dashboard")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

yolo_weights = os.path.join(ROOT_DIR, "desktop_client", "yolo11s.pt")
if not os.path.exists(yolo_weights):
    yolo_weights = os.path.join(ROOT_DIR, "desktop_client", "yolo11n.pt")
db_pickle = os.path.join(ROOT_DIR, "desktop_client", "known_faces.pkl")

ai_engine = AIEngine(yolo_path=yolo_weights, db_path=db_pickle)
camera = None
stream_lock = threading.Lock()
latest_processed_frame = None
latest_inventory = {}
last_alert_time = 0
server_start_time = time.time()

def init_camera(ip):
    global camera, latest_processed_frame
    with stream_lock:
        if camera is not None:
            camera.stop()
            camera = None
        latest_processed_frame = None
        ip_str = str(ip).strip()
        if ip_str == "0" or (ip_str.isdigit() and len(ip_str) <= 2):
            stream_src = int(ip_str)
            print(f"[Dashboard Backend] Connecting CameraStream to local camera {stream_src}...")
        else:
            stream_src = f"http://{ip_str}:81/stream"
            print(f"[Dashboard Backend] Connecting CameraStream to {stream_src}...")
        camera = CameraStream(stream_src, buffer_size=1).start()

init_camera(config.get("camera_ip", "192.168.0.52"))

def processing_worker():
    global latest_processed_frame, latest_inventory, last_alert_time
    print("[Dashboard Backend] AI Processing Worker Thread started.")
    last_frame_id = -1
    while True:
        try:
            if camera is None:
                time.sleep(0.05)
                continue

            current_frame_id = camera.new_frames
            if current_frame_id == last_frame_id:
                time.sleep(0.005)
                continue

            raw = camera.read()
            if raw is None:
                with stream_lock:
                    latest_processed_frame = None
                time.sleep(0.02)
                continue

            last_frame_id = current_frame_id
            annotated, inventory = ai_engine.process(raw)
            with stream_lock:
                latest_processed_frame = annotated
                latest_inventory = inventory

            # Telegram Alert Trigger
            human_detected = inventory.get("Human", 0) > 0
            now = time.time()
            if human_detected and (now - last_alert_time > 30):
                last_alert_time = now
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                snap_path = os.path.join(BACKUP_DIR, f"alert_{ts}.jpg")
                cv2.imwrite(snap_path, annotated)
                threading.Thread(target=send_telegram_alert, args=(snap_path, "Human Intrusion Detected!"), daemon=True).start()

            time.sleep(0.005)
        except Exception as e:
            print(f"[Processing Worker Exception] {e}")
            time.sleep(0.05)

threading.Thread(target=processing_worker, daemon=True).start()

def send_telegram_alert(image_path, caption):
    tok = config.get("telegram_token", "")
    chat = config.get("telegram_chat_id", "")
    if not tok or not chat:
        return
    url = f"https://api.telegram.org/bot{tok}/sendPhoto"
    try:
        with open(image_path, "rb") as f:
            requests.post(url, data={"chat_id": chat, "caption": caption}, files={"photo": f}, timeout=10)
        print(f"[Dashboard Backend] Telegram alert sent: {image_path}")
    except Exception as e:
        print(f"[Dashboard Backend] Failed to send Telegram alert: {e}")

@app.get("/", response_class=HTMLResponse)
def index_page():
    index_file = os.path.join(TEMPLATES_DIR, "index.html")
    with open(index_file, "r") as f:
        return f.read()

@app.get("/api/stream")
def video_feed():
    def frame_generator():
        while True:
            with stream_lock:
                frame = latest_processed_frame
            if frame is None:
                # Render clean offline slate placeholder
                placeholder = np.zeros((320, 480, 3), dtype=np.uint8)
                cv2.rectangle(placeholder, (5, 5), (475, 315), (30, 41, 59), 2)
                cv2.putText(placeholder, "DETECTA AI SURVEILLANCE", (70, 130), cv2.FONT_HERSHEY_DUPLEX, 0.65, (56, 189, 248), 2)
                cam_label = config.get("camera_ip", "192.168.0.52")
                cv2.putText(placeholder, f"Target: http://{cam_label}:81/stream", (80, 165), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (203, 213, 225), 1)
                cv2.putText(placeholder, "Connecting / Waiting for camera stream...", (70, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (239, 68, 68), 1)
                frame_to_send = placeholder
            else:
                frame_to_send = frame
            ret, jpeg = cv2.imencode('.jpg', frame_to_send, [cv2.IMWRITE_JPEG_QUALITY, 80])
            if ret:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
            time.sleep(0.033)
    return StreamingResponse(frame_generator(), media_type="multipart/x-mixed-replace; boundary=frame")

@app.get("/api/status")
def get_status():
    fps = camera.fps if camera else 0.0
    connected = (camera is not None and camera.read() is not None)
    return {
        "status": "connected" if connected else "offline",
        "fps": round(fps, 1),
        "ip": config.get("camera_ip", "192.168.0.52"),
        "inventory": latest_inventory if connected else {},
        "uptime": int(time.time() - server_start_time),
        "total_faces": len(ai_engine.known_faces)
    }

@app.post("/api/camera/ip")
def set_camera_ip(ip: str = Form(...)):
    ip = ip.strip()
    if not ip:
        raise HTTPException(status_code=400, detail="Invalid IP")
    config["camera_ip"] = ip
    save_config(config)
    init_camera(ip)
    return {"status": "ok", "camera_ip": ip, "message": f"Connected to camera at {ip}"}

@app.post("/api/snapshot")
def take_snapshot():
    with stream_lock:
        frame = latest_processed_frame
    if frame is None and camera:
        frame = camera.read()
    if frame is None:
        raise HTTPException(status_code=400, detail="No active camera frame to capture")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"snapshot_{ts}.jpg"
    filepath = os.path.join(BACKUP_DIR, filename)
    cv2.imwrite(filepath, frame)
    return {"status": "ok", "filename": filename, "message": f"Snapshot saved as {filename}"}

@app.get("/api/config")
def get_settings():
    return config

@app.post("/api/config")
def update_settings(
    camera_ip: str = Form(...),
    telegram_token: str = Form(""),
    telegram_chat_id: str = Form("")
):
    config["camera_ip"] = camera_ip.strip()
    config["telegram_token"] = telegram_token.strip()
    config["telegram_chat_id"] = telegram_chat_id.strip()
    save_config(config)
    init_camera(config["camera_ip"])
    return {"status": "ok", "config": config, "message": "Settings saved successfully!"}

@app.get("/api/faces")
def list_faces():
    return [{"name": name} for name in ai_engine.known_faces.keys()]

@app.post("/api/faces/enroll_live")
def enroll_from_live(name: str = Form(...)):
    name = name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Name cannot be empty")
    raw = camera.read() if camera else None
    if raw is None:
        raise HTTPException(status_code=400, detail="Camera stream unavailable")
    ok, msg = ai_engine.enroll_face_from_frame(raw, name)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {"status": "ok", "message": msg}

@app.delete("/api/faces/{name}")
def delete_face(name: str):
    if name in ai_engine.known_faces:
        del ai_engine.known_faces[name]
        ai_engine.save_database()
        return {"status": "ok", "message": f"Deleted {name}"}
    raise HTTPException(status_code=404, detail="Face not found")

@app.get("/api/alerts")
def list_alerts():
    files = sorted([f for f in os.listdir(BACKUP_DIR) if f.endswith(".jpg")], reverse=True)
    return [{"filename": f, "timestamp": os.path.getmtime(os.path.join(BACKUP_DIR, f))} for f in files[:200]]

@app.get("/api/alerts/{filename}")
def get_alert_image(filename: str):
    clean_name = os.path.basename(filename)
    path = os.path.join(BACKUP_DIR, clean_name)
    if os.path.exists(path):
        return FileResponse(path, media_type="image/jpeg")
    raise HTTPException(status_code=404, detail="Image not found")

@app.delete("/api/alerts/{filename}")
def delete_alert(filename: str):
    clean_name = os.path.basename(filename)
    path = os.path.join(BACKUP_DIR, clean_name)
    if os.path.exists(path):
        try:
            os.remove(path)
            return {"status": "ok", "message": f"Deleted {clean_name}"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    raise HTTPException(status_code=404, detail="Image not found")

class BatchDeleteRequest(BaseModel):
    filenames: list[str]

@app.post("/api/alerts/delete_batch")
def delete_batch_alerts(req: BatchDeleteRequest):
    deleted = 0
    for fn in req.filenames:
        clean_name = os.path.basename(fn)
        path = os.path.join(BACKUP_DIR, clean_name)
        if os.path.exists(path):
            try:
                os.remove(path)
                deleted += 1
            except Exception:
                pass
    return {"status": "ok", "deleted_count": deleted, "message": f"Successfully deleted {deleted} alert images"}

@app.post("/api/alerts/clear_all")
def clear_all_alerts():
    deleted = 0
    for f in os.listdir(BACKUP_DIR):
        if f.endswith(".jpg"):
            try:
                os.remove(os.path.join(BACKUP_DIR, f))
                deleted += 1
            except Exception:
                pass
    return {"status": "ok", "deleted_count": deleted, "message": f"Cleared {deleted} alert images"}

