import multiprocessing
import sys
import os
import cv2
import queue
import time
import pickle
import requests
import threading
import collections
import numpy as np
from PIL import Image, ImageTk
import customtkinter as ctk
from customtkinter import filedialog as fd
from ultralytics import YOLO
from insightface.app import FaceAnalysis

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class DetectaApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Detecta")
        self.geometry("1100x700")
        ctk.set_appearance_mode("System")
        
        # IP Configuration
        self.esp_ip = "192.168.137.20" # Default Windows Hotspot subnet IP
        
        # Data Queues & State
        self.frame_queue = queue.Queue(maxsize=1)
        self.reload_flag = False
        self.latest_annotated_frame = None

        self.latest_inventory_str = "Live Inventory:\n- None"
        self.latest_fps = 0.0

        self.battery_text = ctk.StringVar(value="Battery: Checking...")
        self.inventory_text = ctk.StringVar(value="Inventory:\nWaiting for stream...")
        self.fps_text = ctk.StringVar(value="FPS: 0")
        
        # Load Known Faces DB
        self.db_path = "known_faces.pkl"
        self.known_faces = pickle.load(open(self.db_path, "rb")) if os.path.exists(self.db_path) else {}
        
        print("Loading AI Models...")
        if sys.platform == 'darwin':
            self.model = YOLO(resource_path('yolov10n.pt'))
            self.device = 'mps'
            ctx_id = -1
        else:
            try:
                self.model = YOLO(resource_path('yolov10n.engine'), task='detect')
            except:
                self.model = YOLO(resource_path('yolov10n.pt'))
            self.device = 'cuda:0'
            ctx_id = 0
            
        # Change person to Human
        if hasattr(self.model, 'model') and 0 in self.model.model.names:
            self.model.model.names[0] = "Human"
        for k, v in list(self.model.names.items()):
            if v == "person":
                self.model.model.names[k] = "Human"

        # InsightFace Initialization
        self.face_app = FaceAnalysis(name='buffalo_l', root=resource_path(''), providers=['CPUExecutionProvider'])
        self.face_app.prepare(ctx_id=ctx_id, det_size=(640, 640))
        
        self.setup_ui()
        self.start_daemons()
        self.update_video()

    def setup_ui(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        # Sidebar (Left)
        self.sidebar = ctk.CTkFrame(self, width=280)
        self.sidebar.grid(row=0, column=0, sticky="nswe", padx=10, pady=10)
        
        # IP Entry & Connectivity
        ctk.CTkLabel(self.sidebar, text="Camera IP:", font=("Arial", 14, "bold")).pack(pady=(15, 5), padx=10, anchor="w")
        self.ip_entry = ctk.CTkEntry(self.sidebar, width=220)
        self.ip_entry.insert(0, "192.168.137.20")
        self.ip_entry.pack(pady=5, padx=10)
        
        # Action Buttons in Sidebar
        self.update_ip_btn = ctk.CTkButton(self.sidebar, text="Reload / Connect", command=self.trigger_reload, width=220)
        self.update_ip_btn.pack(pady=10, padx=10)
        
        self.auto_discover_btn = ctk.CTkButton(self.sidebar, text="Auto-Discover", command=self.auto_discover_ip, fg_color="#17a2b8", hover_color="#138496", width=220)
        self.auto_discover_btn.pack(pady=10, padx=10)
        
        self.wifi_setup_btn = ctk.CTkButton(self.sidebar, text="Wi-Fi Setup", command=self.setup_wifi_dialog, fg_color="#28a745", hover_color="#218838", width=220)
        self.wifi_setup_btn.pack(pady=10, padx=10)
        
        self.db_btn = ctk.CTkButton(self.sidebar, text="Database", command=self.show_database, fg_color="#6c757d", hover_color="#5a6268", width=220)
        self.db_btn.pack(pady=10, padx=10)
        
        # Stats
        ctk.CTkFrame(self.sidebar, height=2, fg_color="gray").pack(fill="x", pady=20, padx=10)
        
        self.lbl_fps = ctk.CTkLabel(self.sidebar, textvariable=self.fps_text, font=("Arial", 14))
        self.lbl_fps.pack(pady=10, padx=10, anchor="w")
        
        self.lbl_inventory = ctk.CTkLabel(self.sidebar, textvariable=self.inventory_text, justify="left", font=("Arial", 14))
        self.lbl_inventory.pack(pady=10, padx=10, anchor="nw")
        
        # Battery (Bottom of Sidebar)
        self.batt_label = ctk.CTkLabel(self.sidebar, textvariable=self.battery_text, font=("Arial", 13, "bold"), text_color="#ffc107", wraplength=250)
        self.batt_label.pack(side="bottom", pady=20, padx=10)
        
        # Main Video Canvas (Right)
        self.video_frame = ctk.CTkFrame(self)
        self.video_frame.grid(row=0, column=1, sticky="nswe", padx=(0, 10), pady=10)
        self.video_frame.grid_rowconfigure(0, weight=1)
        self.video_frame.grid_columnconfigure(0, weight=1)
        
        self.video_label = ctk.CTkLabel(self.video_frame, text="Waiting for connection...")
        self.video_label.grid(row=0, column=0)

    def setup_wifi_dialog(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Camera Wi-Fi Setup")
        dialog.geometry("400x350")
        dialog.attributes("-topmost", True)
        
        lbl = ctk.CTkLabel(dialog, text="Make sure you are connected to 'Detecta_Setup' Wi-Fi before scanning.", wraplength=350, font=("Arial", 14))
        lbl.pack(pady=15)
        
        networks_dropdown = ctk.CTkComboBox(dialog, values=["Scanning..."], width=250)
        networks_dropdown.pack(pady=10)
        
        def scan_networks():
            try:
                res = requests.get("http://192.168.4.1/scan", timeout=15).json()
                networks = res.get("networks", [])
                self.after(0, lambda: [networks_dropdown.configure(values=networks), networks_dropdown.set(networks[0] if networks else "No networks")])
            except Exception as e:
                self.after(0, lambda: networks_dropdown.set("Error: Camera not found"))
                print(e)
                
        threading.Thread(target=scan_networks, daemon=True).start()
        
        pass_entry = ctk.CTkEntry(dialog, placeholder_text="Wi-Fi Password", show="*", width=250)
        pass_entry.pack(pady=10)
        
        status_lbl = ctk.CTkLabel(dialog, text="", text_color="green", wraplength=350)
        status_lbl.pack(pady=5)
        
        def submit():
            ssid = networks_dropdown.get()
            pwd = pass_entry.get()
            try:
                res = requests.post("http://192.168.4.1/connect", json={"ssid": ssid, "password": pwd}, timeout=10)
                status_lbl.configure(text="Success! Camera is restarting and connecting to your router.")
            except Exception as e:
                status_lbl.configure(text="Failed to send. Are you still connected to Detecta_Setup?", text_color="red")
                
        submit_btn = ctk.CTkButton(dialog, text="Connect Camera to Wi-Fi", command=submit)
        submit_btn.pack(pady=15)

    def trigger_reload(self):
        self.esp_ip = self.ip_entry.get()
        self.reload_flag = True
        print(f"Reload triggered for IP: {self.esp_ip}")
        self.inventory_text.set("Inventory:\nReloading stream...")

    def update_ip(self):
        self.esp_ip = self.ip_entry.get()
        print(f"IP updated to: {self.esp_ip}")

    def auto_discover_ip(self):
        self.ip_entry.delete(0, 'end')
        self.ip_entry.insert(0, "Scanning...")
        
        def scan_subnet():
            import socket
            import concurrent.futures
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                local_ip = s.getsockname()[0]
                s.close()
            except:
                local_ip = "192.168.0.1"
                
            subnet = ".".join(local_ip.split(".")[:3])
            ips = [f"{subnet}.{i}" for i in range(1, 255)]
            
            def check_port(ip):
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                        sock.settimeout(0.5)
                        if sock.connect_ex((ip, 81)) == 0:
                            return ip
                except:
                    pass
                return None
            
            found_ip = None
            with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
                for result in executor.map(check_port, ips):
                    if result:
                        found_ip = result
                        break
            
            if found_ip:
                self.after(0, lambda: [self.ip_entry.delete(0, 'end'), self.ip_entry.insert(0, found_ip), self.update_ip()])
            else:
                self.after(0, lambda: [self.ip_entry.delete(0, 'end'), self.ip_entry.insert(0, "Not Found")])
                
        threading.Thread(target=scan_subnet, daemon=True).start()

    def sync_database(self):
        self.known_faces = {}
        enroll_dir = os.path.join(os.path.expanduser("~"), "Detecta_Enrollments")
        if not os.path.exists(enroll_dir): return
        
        for person_name in os.listdir(enroll_dir):
            person_path = os.path.join(enroll_dir, person_name)
            if not os.path.isdir(person_path): continue
            
            embeddings = []
            for img_name in os.listdir(person_path):
                if img_name.lower().endswith(('.png', '.jpg', '.jpeg')):
                    try:
                        pil_img = Image.open(os.path.join(person_path, img_name)).convert('RGB')
                        img = np.array(pil_img)
                        img = img[:, :, ::-1].copy()
                        faces = self.face_app.get(img)
                        if faces: embeddings.append(faces[0].embedding)
                    except Exception as e:
                        print("Error syncing image:", e)
            
            if embeddings:
                self.known_faces[person_name] = np.mean(embeddings, axis=0)
        
        pickle.dump(self.known_faces, open(self.db_path, "wb"))
        print(f"[Database] Synced {len(self.known_faces)} persons.")

    def show_database(self):
        if hasattr(self, 'db_win') and self.db_win.winfo_exists():
            self.db_win.focus()
            return
            
        self.db_win = ctk.CTkToplevel(self)
        self.db_win.title("Face Database Manager")
        self.db_win.geometry("800x550")
        
        header = ctk.CTkFrame(self.db_win)
        header.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(header, text="Manage Enrolled Faces", font=("Arial", 20, "bold")).pack(side="left")
        ctk.CTkButton(header, text="+ Add New Person", command=self.add_person_ui).pack(side="right")
        
        self.db_scroll = ctk.CTkScrollableFrame(self.db_win)
        self.db_scroll.pack(fill="both", expand=True, padx=20, pady=10)
        self.refresh_db_ui()

    def refresh_db_ui(self):
        for widget in self.db_scroll.winfo_children():
            widget.destroy()
            
        enroll_dir = os.path.join(os.path.expanduser("~"), "Detecta_Enrollments")
        if not os.path.exists(enroll_dir) or not os.listdir(enroll_dir):
            ctk.CTkLabel(self.db_scroll, text="No faces enrolled. Click '+ Add New Person'.", font=("Arial", 14)).pack(pady=20)
            return
            
        for person_name in os.listdir(enroll_dir):
            person_path = os.path.join(enroll_dir, person_name)
            if not os.path.isdir(person_path): continue
            
            row = ctk.CTkFrame(self.db_scroll)
            row.pack(fill="x", pady=5, padx=5)
            
            lbl = ctk.CTkLabel(row, text=person_name, font=("Arial", 16, "bold"), width=120)
            lbl.pack(side="left", padx=10, pady=10)
            
            images = [f for f in os.listdir(person_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            for img_name in images[:3]:
                img_path = os.path.join(person_path, img_name)
                try:
                    pil_img = Image.open(img_path)
                    min_dim = min(pil_img.size)
                    left = (pil_img.width - min_dim)/2
                    top = (pil_img.height - min_dim)/2
                    pil_img = pil_img.crop((left, top, left+min_dim, top+min_dim))
                    pil_img.thumbnail((70, 70))
                    ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(70, 70))
                    img_lbl = ctk.CTkLabel(row, image=ctk_img, text="")
                    img_lbl.image = ctk_img
                    img_lbl.pack(side="left", padx=5, pady=5)
                except: pass
                
            btn_frame = ctk.CTkFrame(row, fg_color="transparent")
            btn_frame.pack(side="right", padx=10)
            
            if len(images) < 3:
                ctk.CTkButton(btn_frame, text="Add Photo", width=80, command=lambda p=person_name: self.add_photo_ui(p)).pack(side="left", padx=5)
            ctk.CTkButton(btn_frame, text="Rename", width=70, fg_color="#ffc107", text_color="black", hover_color="#e0a800", command=lambda p=person_name: self.rename_person_ui(p)).pack(side="left", padx=5)
            ctk.CTkButton(btn_frame, text="Delete", width=70, fg_color="#dc3545", hover_color="#c82333", command=lambda p=person_name: self.delete_person_ui(p)).pack(side="left", padx=5)

    def add_person_ui(self):
        from tkinter import messagebox
        dialog = ctk.CTkInputDialog(text="Enter name for this new person:", title="New Person")
        name = dialog.get_input()
        if not name: return
        
        enroll_dir = os.path.join(os.path.expanduser("~"), "Detecta_Enrollments")
        person_dir = os.path.join(enroll_dir, name)
        if os.path.exists(person_dir):
            messagebox.showerror("Error", "A person with this name already exists!", parent=self.db_win)
            return
            
        os.makedirs(person_dir, exist_ok=True)
        self.add_photo_ui(name)

    def add_photo_ui(self, person_name):
        from tkinter import messagebox, filedialog
        import shutil
        paths = filedialog.askopenfilenames(parent=self.db_win, title=f"Select photos for {person_name} (Max 3 total)", filetypes=[("Image files", "*.jpg *.png *.jpeg")])
        if not paths: return
        
        person_dir = os.path.join(os.path.expanduser("~"), "Detecta_Enrollments", person_name)
        existing = len([f for f in os.listdir(person_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))])
        allowed = 3 - existing
        
        for path in list(paths)[:allowed]:
            img = cv2.imread(path)
            if img is None: continue
            
            faces = self.face_app.get(img)
            if not faces:
                messagebox.showwarning("No Face", f"No face detected in {os.path.basename(path)}. Skipping.", parent=self.db_win)
                continue
                
            ext = os.path.splitext(path)[1]
            idx = len(os.listdir(person_dir)) + 1
            shutil.copy(path, os.path.join(person_dir, f"photo_{idx}{ext}"))
            
        if not os.listdir(person_dir):
            shutil.rmtree(person_dir)
            
        self.sync_database()
        self.refresh_db_ui()

    def rename_person_ui(self, old_name):
        from tkinter import messagebox
        dialog = ctk.CTkInputDialog(text=f"Enter new name for {old_name}:", title="Rename")
        new_name = dialog.get_input()
        if not new_name or new_name == old_name: return
        
        enroll_dir = os.path.join(os.path.expanduser("~"), "Detecta_Enrollments")
        old_dir = os.path.join(enroll_dir, old_name)
        new_dir = os.path.join(enroll_dir, new_name)
        
        if os.path.exists(new_dir):
            messagebox.showerror("Error", "Name already exists!")
            return
            
        os.rename(old_dir, new_dir)
        self.sync_database()
        self.refresh_db_ui()

    def delete_person_ui(self, person_name):
        from tkinter import messagebox
        import shutil
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete {person_name}?", parent=self.db_win):
            person_dir = os.path.join(os.path.expanduser("~"), "Detecta_Enrollments", person_name)
            if os.path.exists(person_dir):
                shutil.rmtree(person_dir)
            self.sync_database()
            self.refresh_db_ui()

    def start_daemons(self):
        threading.Thread(target=self.capture_frames, daemon=True).start()
        threading.Thread(target=self.poll_battery, daemon=True).start()
        threading.Thread(target=self.run_inference_loop, daemon=True).start()

    def capture_frames(self):
        print(f"[Video Thread] Started. Initial IP: {self.esp_ip}")
        while True:
            stream_url = f"http://{self.esp_ip}:81/stream"
            print(f"[Video Thread] Attempting to connect to: {stream_url}")
            cap = cv2.VideoCapture(stream_url)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 2)
            
            if not cap.isOpened():
                print(f"[Video Thread] Failed to open {stream_url}. Retrying in 2s...")
                time.sleep(2)
                continue
                
            print(f"[Video Thread] Successfully connected to {stream_url}!")
            
            while cap.isOpened():
                if self.reload_flag:
                    print("[Video Thread] Reload flag detected! Breaking loop to reconnect...")
                    self.reload_flag = False
                    break 
                    
                ret, frame = cap.read()
                if not ret:
                    print("[Video Thread] cap.read() returned False. Stream dropped.")
                    break
                
                frame = cv2.flip(frame, -1)
                
                while not self.frame_queue.empty():
                    try: self.frame_queue.get_nowait()
                    except: pass
                self.frame_queue.put(frame)
                
            print("[Video Thread] Releasing capture object.")
            cap.release()

    def poll_battery(self):
        while True:
            self.battery_text.set("Battery: Standalone (Port 81 Stream Pure)")
            time.sleep(3600)

    def run_inference_loop(self):
        while True:
            try:
                frame = self.frame_queue.get(timeout=1)
                start_time = time.time()
                
                # AI Inference
                results = self.model(frame, device=self.device, verbose=False)
                annotated_frame = results[0].plot()
                
                # Face Recognition
                classes = [self.model.names[int(c)] for c in results[0].boxes.cls]
                if "Human" in classes or "person" in classes:
                    faces = self.face_app.get(frame)
                    for face in faces:
                        best_match, best_score = "Unknown", 0.0
                        for name, emb in self.known_faces.items():
                            score = np.dot(face.embedding, emb) / (np.linalg.norm(face.embedding) * np.linalg.norm(emb))
                            if score > best_score:
                                best_score, best_match = score, name
                        
                        if best_score > 0.4:  # Threshold
                            x1, y1, x2, y2 = map(int, face.bbox)
                            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                            cv2.putText(annotated_frame, f"{best_match} ({best_score:.2f})", (x1, y1-10), 
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
                
                counts = collections.Counter([self.model.names[int(c)] for c in results[0].boxes.cls])
                inventory_str = "Live Inventory:\n" + "\n".join([f"- {k}: {v}" for k, v in counts.items()])
                
                self.latest_annotated_frame = annotated_frame
                self.latest_inventory_str = inventory_str
                
                fps = 1.0 / (time.time() - start_time) if (time.time() - start_time) > 0 else 0
                self.latest_fps = fps
                
            except queue.Empty:
                pass
            except Exception as e:
                print("Inference error:", e)

    def update_video(self):
        if self.latest_annotated_frame is not None:
            rgb_image = cv2.cvtColor(self.latest_annotated_frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(rgb_image)
            pil_img.thumbnail((800, 600))
            tk_img = ImageTk.PhotoImage(image=pil_img)
            self.video_label.configure(image=tk_img, text="")
            self.video_label.image = tk_img
            
            self.inventory_text.set(self.latest_inventory_str)
            self.fps_text.set(f"FPS: {self.latest_fps:.1f}")
            
        self.after(30, self.update_video)

if __name__ == "__main__":
    multiprocessing.freeze_support()
    app = DetectaApp()
    app.mainloop()
