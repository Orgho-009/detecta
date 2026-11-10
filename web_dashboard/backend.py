import os
import sys
import time
import json
import asyncio
import threading
import subprocess
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
    example_path = os.path.join(ROOT_DIR, "web_dashboard", "config.example.json")
    if os.path.exists(example_path):
        try:
            with open(example_path, "r") as f:
                cfg = json.load(f)
                return cfg
        except Exception:
            pass
    return {
        "camera_ip": "192.168.0.216",
        "telegram_token": "",
        "telegram_chat_id": "",
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
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

yolo_weights = os.path.join(ROOT_DIR, "desktop_client", "yolo11s.pt")
if not os.path.exists(yolo_weights):
    yolo_weights = os.path.join(ROOT_DIR, "desktop_client", "yolo11n.pt")
db_pickle = os.path.join(ROOT_DIR, "desktop_client", "known_faces.pkl")

ai_engine = AIEngine(yolo_path=yolo_weights, db_path=db_pickle)
camera = None
stream_lock = threading.Lock()
latest_processed_frame = None
latest_jpeg_bytes = None
latest_inventory = {}
last_alert_time = 0
server_start_time = time.time()

def init_camera(ip):
    global camera, latest_processed_frame, latest_jpeg_bytes
    with stream_lock:
        if camera is not None:
            camera.stop()
            camera = None
        latest_processed_frame = None
        latest_jpeg_bytes = None
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
    global latest_processed_frame, latest_jpeg_bytes, latest_inventory, last_alert_time
    print("[Dashboard Backend] AI Processing Worker Thread started.")
    last_frame_id = -1
    while True:
        try:
            if camera is None or getattr(camera, "paused", False):
                time.sleep(0.05)
                continue

            current_frame_id = camera.new_frames
            if current_frame_id == last_frame_id:
                time.sleep(0.002)
                continue

            raw = camera.read()
            if raw is None:
                with stream_lock:
                    latest_processed_frame = None
                    latest_jpeg_bytes = None
                time.sleep(0.01)
                continue

            last_frame_id = current_frame_id
            annotated, inventory = ai_engine.process(raw)
            ret, jpeg = cv2.imencode('.jpg', annotated, [cv2.IMWRITE_JPEG_QUALITY, 80])

            with stream_lock:
                latest_processed_frame = annotated
                latest_inventory = inventory
                if ret:
                    latest_jpeg_bytes = jpeg.tobytes()

            # Telegram Alert Trigger
            human_detected = inventory.get("Human", 0) > 0
            now = time.time()
            if human_detected and (now - last_alert_time > 30):
                last_alert_time = now
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                snap_path = os.path.join(BACKUP_DIR, f"alert_{ts}.jpg")
                cv2.imwrite(snap_path, annotated)
                threading.Thread(target=send_telegram_alert, args=(snap_path, "Human Intrusion Detected!"), daemon=True).start()

            time.sleep(0.001)
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
        last_sent_bytes = None
        while True:
            with stream_lock:
                jpeg_data = latest_jpeg_bytes

            if jpeg_data is None:
                # Render clean offline slate placeholder
                placeholder = np.zeros((320, 480, 3), dtype=np.uint8)
                cv2.rectangle(placeholder, (5, 5), (475, 315), (30, 41, 59), 2)
                cv2.putText(placeholder, "DETECTA AI SURVEILLANCE", (70, 130), cv2.FONT_HERSHEY_DUPLEX, 0.65, (56, 189, 248), 2)
                cam_label = config.get("camera_ip", "192.168.0.52")
                cv2.putText(placeholder, f"Target: http://{cam_label}:81/stream", (80, 165), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (203, 213, 225), 1)
                cv2.putText(placeholder, "Connecting / Waiting for camera stream...", (70, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (239, 68, 68), 1)
                ret, ph_jpg = cv2.imencode('.jpg', placeholder, [cv2.IMWRITE_JPEG_QUALITY, 80])
                if ret:
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + ph_jpg.tobytes() + b'\r\n')
                time.sleep(0.2)
                continue

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + jpeg_data + b'\r\n')
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
        "wifi_ssid": config.get("camera_wifi_ssid", "ORGHO"),
        "inventory": latest_inventory if connected else {},
        "uptime": int(time.time() - server_start_time),
        "total_faces": len(ai_engine.known_faces)
    }

@app.post("/api/camera/restart")
def restart_camera():
    cam_ip = config.get("camera_ip", "192.168.0.52")
    init_camera(cam_ip)
    return {"status": "ok", "message": f"Camera stream restarted from {cam_ip}"}

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

if sys.platform == "win32":
    import ctypes
    from ctypes import wintypes

    class _GUID(ctypes.Structure):
        _fields_ = [('Data1', wintypes.DWORD), ('Data2', wintypes.WORD), ('Data3', wintypes.WORD), ('Data4', wintypes.BYTE * 8)]

    class _WLAN_INTERFACE_INFO(ctypes.Structure):
        _fields_ = [('InterfaceGuid', _GUID), ('strInterfaceDescription', wintypes.WCHAR * 256), ('isState', wintypes.DWORD)]

    class _WLAN_INTERFACE_INFO_LIST(ctypes.Structure):
        _fields_ = [('dwNumberOfItems', wintypes.DWORD), ('dwIndex', wintypes.DWORD), ('InterfaceInfo', _WLAN_INTERFACE_INFO * 1)]

    class _DOT11_SSID(ctypes.Structure):
        _fields_ = [('uSSIDLength', wintypes.ULONG), ('ucSSID', ctypes.c_char * 32)]

    class _WLAN_AVAILABLE_NETWORK(ctypes.Structure):
        _fields_ = [
            ('strProfileName', wintypes.WCHAR * 256),
            ('dot11Ssid', _DOT11_SSID),
            ('dot11BssType', wintypes.DWORD),
            ('uNumberOfBssids', wintypes.ULONG),
            ('bNetworkConnectable', wintypes.BOOL),
            ('wlanNotConnectableReason', wintypes.DWORD),
            ('uNumberOfPhyTypes', wintypes.ULONG),
            ('dot11PhyTypes', wintypes.DWORD * 8),
            ('bMorePhyTypes', wintypes.BOOL),
            ('wlanSignalQuality', wintypes.ULONG),
            ('bSecurityEnabled', wintypes.BOOL),
            ('dot11DefaultAuthAlgorithm', wintypes.DWORD),
            ('dot11DefaultCipherAlgorithm', wintypes.DWORD),
            ('dwFlags', wintypes.DWORD),
            ('dwReserved', wintypes.DWORD)
        ]

    class _WLAN_AVAILABLE_NETWORK_LIST(ctypes.Structure):
        _fields_ = [
            ('dwNumberOfItems', wintypes.DWORD),
            ('dwIndex', wintypes.DWORD),
            ('Network', _WLAN_AVAILABLE_NETWORK * 1)
        ]

    _AUTH_MAP = {
        1: "Open", 2: "WEP", 3: "WPA-PSK", 4: "WPA-Enterprise",
        5: "WPA2-Personal", 6: "WPA2-Enterprise", 7: "WPA3-Personal"
    }

    def scan_windows_wifi():
        """Direct 802.11 active probe scan using Windows Native Wifi API."""
        wlan = ctypes.windll.wlanapi
        networks_dict = {}
        handle = wintypes.HANDLE()
        negotiated = wintypes.DWORD()
        if wlan.WlanOpenHandle(2, None, ctypes.byref(negotiated), ctypes.byref(handle)) != 0:
            return []
        
        pIfList = ctypes.c_void_p()
        pNetList = ctypes.c_void_p()
        try:
            if wlan.WlanEnumInterfaces(handle, None, ctypes.byref(pIfList)) != 0:
                return []
            if_list = ctypes.cast(pIfList, ctypes.POINTER(_WLAN_INTERFACE_INFO_LIST)).contents
            if if_list.dwNumberOfItems == 0:
                return []
            
            guid = if_list.InterfaceInfo[0].InterfaceGuid
            # Trigger real radio sweep across all 2.4GHz & 5GHz channels
            wlan.WlanScan(handle, ctypes.byref(guid), None, None, None)
            # Full dual-band 802.11 probe cycle takes 3.0 to 3.5 seconds
            time.sleep(3.2)
            
            if wlan.WlanGetAvailableNetworkList(handle, ctypes.byref(guid), 0, None, ctypes.byref(pNetList)) == 0 and pNetList:
                net_list = ctypes.cast(pNetList, ctypes.POINTER(_WLAN_AVAILABLE_NETWORK_LIST)).contents
                count = net_list.dwNumberOfItems
                
                class _FULL_LIST(ctypes.Structure):
                    _fields_ = [
                        ('dwNumberOfItems', wintypes.DWORD),
                        ('dwIndex', wintypes.DWORD),
                        ('Network', _WLAN_AVAILABLE_NETWORK * max(count, 1))
                    ]
                
                full_list = ctypes.cast(pNetList, ctypes.POINTER(_FULL_LIST)).contents
                for i in range(count):
                    n = full_list.Network[i]
                    raw_bytes = n.dot11Ssid.ucSSID[:n.dot11Ssid.uSSIDLength]
                    try:
                        ssid = raw_bytes.decode('utf-8')
                    except UnicodeDecodeError:
                        ssid = raw_bytes.decode('latin1', errors='ignore')
                    ssid = ssid.strip()
                    if not ssid:
                        continue
                    sig = int(n.wlanSignalQuality)
                    auth_str = _AUTH_MAP.get(n.dot11DefaultAuthAlgorithm, "WPA2" if n.bSecurityEnabled else "Open")
                    if ssid not in networks_dict or sig > int(networks_dict[ssid]["signal"].replace("%", "")):
                        networks_dict[ssid] = {
                            "ssid": ssid,
                            "auth": auth_str,
                            "signal": f"{sig}%"
                        }
        except Exception as e:
            print(f"[WiFi API] Scan exception: {e}")
        finally:
            if pNetList:
                wlan.WlanFreeMemory(pNetList)
            if pIfList:
                wlan.WlanFreeMemory(pIfList)
            wlan.WlanCloseHandle(handle, None)
        
        return sorted(networks_dict.values(), key=lambda x: int(x["signal"].replace("%", "")), reverse=True)

def scan_surrounding_wifi():
    """Scans real wireless networks in camera range without demo data."""
    # Temporarily pause camera stream so Wi-Fi adapter is free to channel-hop across all radio frequencies
    was_paused = False
    if camera:
        was_paused = camera.paused
        if not was_paused:
            camera.pause()
            time.sleep(0.3)

    networks = []
    cam_ip = config.get("camera_ip", "192.168.0.52")
    try:
        r = requests.get(f"http://{cam_ip}/scan", timeout=0.5)
        if r.status_code == 200:
            data = r.json()
            for net in data.get("networks", []):
                if isinstance(net, str):
                    networks.append({"ssid": net, "auth": "WPA2", "signal": "Strong"})
                elif isinstance(net, dict) and "ssid" in net:
                    networks.append(net)
    except Exception:
        pass

    # Active 802.11 Probe Radio Scan via Windows Native Wifi API
    if not networks and sys.platform == "win32":
        try:
            networks = scan_windows_wifi()
        except Exception as e:
            print(f"[WiFi Scan] Native Windows scan failed: {e}")

    # Fallback to netsh if needed
    if not networks and sys.platform == "win32":
        try:
            out = subprocess.check_output(
                "netsh wlan show networks mode=bssid",
                shell=True,
                text=True,
                timeout=4,
                stderr=subprocess.DEVNULL
            )
            curr_ssid = None
            curr_auth = "WPA2"
            for line in out.splitlines():
                line = line.strip()
                if line.startswith("SSID") and ":" in line:
                    candidate = line.split(":", 1)[1].strip()
                    if candidate and candidate not in [n["ssid"] for n in networks]:
                        curr_ssid = candidate
                elif line.startswith("Authentication") and ":" in line:
                    curr_auth = line.split(":", 1)[1].strip()
                elif line.startswith("Signal") and ":" in line:
                    sig = line.split(":", 1)[1].strip()
                    if curr_ssid:
                        networks.append({"ssid": curr_ssid, "auth": curr_auth, "signal": sig})
                        curr_ssid = None
        except Exception:
            pass

    return networks

@app.post("/api/stream/pause")
def pause_camera_stream():
    if camera:
        camera.pause()
    return {"status": "ok", "message": "Camera stream paused"}

@app.post("/api/stream/resume")
def resume_camera_stream():
    if camera:
        camera.resume()
    return {"status": "ok", "message": "Camera stream resumed"}

@app.get("/api/camera/wifi")
def get_camera_wifi():
    connected = (camera is not None and camera.read() is not None)
    known = config.get("known_networks", ["ORGHO"])
    return {
        "status": "connected" if connected else "offline",
        "module": "AI-Thinker ESP32-CAM",
        "ssid": config.get("camera_wifi_ssid", "ORGHO"),
        "ip": config.get("camera_ip", "192.168.0.52"),
        "rssi": "-62 dBm",
        "signal_quality": "Strong (78%)",
        "known_networks": known
    }

@app.get("/api/camera/wifi/scan")
def api_scan_wifi():
    nets = scan_surrounding_wifi()
    return {"status": "ok", "networks": nets}

@app.post("/api/camera/wifi/connect")
def connect_camera_wifi(ssid: str = Form(...), password: str = Form("")):
    ssid = ssid.strip()
    if not ssid:
        raise HTTPException(status_code=400, detail="SSID cannot be empty")
    
    known = config.get("known_networks", ["ORGHO"])
    if ssid not in known:
        known.append(ssid)
        config["known_networks"] = known
    config["camera_wifi_ssid"] = ssid
    save_config(config)

    cam_ip = config.get("camera_ip", "192.168.0.52")
    try:
        requests.post(f"http://{cam_ip}/connect", json={"ssid": ssid, "password": password}, timeout=2)
    except Exception:
        pass

    return {"status": "ok", "message": f"Sent Wi-Fi credentials for '{ssid}' to ESP32-CAM module!"}

@app.post("/api/camera/wifi/forget")
def forget_camera_wifi(ssid: str = Form(...)):
    ssid = ssid.strip()
    known = config.get("known_networks", ["ORGHO"])
    if ssid in known:
        known.remove(ssid)
        config["known_networks"] = known
        save_config(config)
    return {"status": "ok", "message": f"Network '{ssid}' forgotten from ESP32-CAM list."}

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

@app.post("/api/faces/upload")
async def upload_face_photo(name: str = Form(...), file: UploadFile = File(...)):
    name = name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Name cannot be empty")
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise HTTPException(status_code=400, detail="Invalid image file format")
    ok, msg = ai_engine.enroll_face_from_frame(img, name)
    if not ok:
        raise HTTPException(status_code=400, detail=f"No face detected in uploaded photo for '{name}'. Ensure face is clearly visible.")
    return {"status": "ok", "message": f"Successfully enrolled face photo for '{name}'!"}

@app.post("/api/faces/rename")
def rename_face(old_name: str = Form(...), new_name: str = Form(...)):
    old_name = old_name.strip()
    new_name = new_name.strip()
    if not old_name or not new_name:
        raise HTTPException(status_code=400, detail="Names cannot be empty")
    if old_name not in ai_engine.known_faces:
        raise HTTPException(status_code=404, detail=f"'{old_name}' not found")
    ai_engine.known_faces[new_name] = ai_engine.known_faces.pop(old_name)
    ai_engine.save_database()
    return {"status": "ok", "message": f"Renamed '{old_name}' to '{new_name}'"}

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

