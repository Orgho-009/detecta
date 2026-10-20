"""
Detecta ESP32-CAM Serial Auto-Discovery & Hot-Plug Assistant
Listens on COM6 for ESP32 boot/Wi-Fi logs.
When the ESP32 connects and prints its IP, this script automatically updates
the Detecta Web Dashboard to switch to that stream!
"""
import re
import time
import serial
import requests

SERIAL_PORT = "COM6"
BAUD_RATE = 115200
DASHBOARD_URL = "http://127.0.0.1:8000/api/camera/ip"

def run_serial_watcher():
    print(f"[Auto-Detector] Monitoring {SERIAL_PORT} for ESP32-CAM IP assignment...")
    while True:
        try:
            with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1) as ser:
                # Ensure DTR is False so ESP32 runs in normal execution mode
                ser.setDTR(False)
                while True:
                    line = ser.readline()
                    if not line:
                        continue
                    text = line.decode('utf-8', errors='replace').strip()
                    if text:
                        print(f"[ESP32 COM6] {text}")
                    
                    # Match: Live Stream Ready! URL: http://192.168.X.X:81/stream
                    # Or IP: 192.168.X.X
                    match = re.search(r"http://(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):81", text)
                    if match:
                        cam_ip = match.group(1)
                        print("=" * 60)
                        print(f"[Auto-Detector] Found ESP32-CAM IP: {cam_ip}")
                        print(f"[Auto-Detector] Updating Web Dashboard at {DASHBOARD_URL}...")
                        try:
                            res = requests.post(DASHBOARD_URL, data={"ip": cam_ip}, timeout=5)
                            print(f"[Auto-Detector] Dashboard response: {res.json()}")
                        except Exception as e:
                            print(f"[Auto-Detector] Could not update dashboard: {e}")
                        print("=" * 60)
        except serial.SerialException:
            # Device might be unplugged or restarting
            time.sleep(2)
        except Exception as e:
            time.sleep(2)

if __name__ == "__main__":
    run_serial_watcher()
