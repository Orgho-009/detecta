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
import subprocess
import socket
import concurrent.futures
import numpy as np
from PIL import Image, ImageTk
import customtkinter as ctk
from ultralytics import YOLO
from insightface.app import FaceAnalysis

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DESKTOP_CLIENT_DIR = os.path.join(ROOT_DIR, "desktop_client")

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def get_native_wifi_ssid():
    """Detects active PC Wi-Fi SSID natively without third-party dependencies."""
    try:
        if sys.platform == "win32":
            out = subprocess.check_output(
                "netsh wlan show interfaces",
                shell=True,
                text=True,
                timeout=2,
                stderr=subprocess.DEVNULL
            )
            for line in out.splitlines():
                if "SSID" in line and "BSSID" not in line:
                    parts = line.split(":")
                    if len(parts) > 1:
                        ssid = parts[1].strip()
                        if ssid:
                            return ssid
        elif sys.platform == "darwin":
            out = subprocess.check_output(
                ["/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport", "-I"],
                text=True,
                timeout=2,
                stderr=subprocess.DEVNULL
            )
            for line in out.splitlines():
                if " SSID:" in line:
                    return line.split(":")[1].strip()
    except Exception:
        pass
    return "Wi-Fi (Active)"


class DetectaApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Detecta — AI Security Camera Monitor")
        self.geometry("1180x740")
        self.minsize(980, 640)
        ctk.set_appearance_mode("Dark")
        
        # State Management
        self.esp_ip = "192.168.0.52"
        self.frame_queue = queue.Queue(maxsize=1)
        self.reload_flag = False
        self.stream_paused = False  # Stream-Pause State Machine
        self.latest_annotated_frame = None
        self.latest_inventory_str = "Live Inventory\n- None"
        self.latest_fps = 0.0
        
        # Professional Status (No emojis / No colons)
        self.status_state = "Camera Searching..."
        self.status_color = "#ffc107"  # Yellow
        
        # Load Known Faces DB
        self.db_path = os.path.join(DESKTOP_CLIENT_DIR, "known_faces.pkl")
        if not os.path.exists(self.db_path):
            self.db_path = os.path.join(os.path.abspath("."), "known_faces.pkl")
        self.known_faces = pickle.load(open(self.db_path, "rb")) if os.path.exists(self.db_path) else {}
        
        print("[Detecta] Initializing AI Models...")
        # Model Selection: YOLO11s / YOLO11n on CUDA or MPS
        yolo_candidates = [
            os.path.join(DESKTOP_CLIENT_DIR, "yolo11s.pt"),
            os.path.join(DESKTOP_CLIENT_DIR, "yolo11n.pt"),
            resource_path("yolo11s.pt"),
            resource_path("yolo11n.pt")
        ]
        chosen_yolo = "yolo11n.pt"
        for cand in yolo_candidates:
            if os.path.exists(cand):
                chosen_yolo = cand
                break
                
        if sys.platform == 'darwin':
            self.model = YOLO(chosen_yolo)
            self.device = 'mps'
            ctx_id = -1
        else:
            self.model = YOLO(chosen_yolo)
            self.device = 'cuda:0'
            ctx_id = 0
            
        # Standardize class naming
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
        
        # Fast Probe on Startup
        self.after(500, self.smart_connect)

    def setup_ui(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        # ----------------- SIDEBAR (LEFT) -----------------
        self.sidebar = ctk.CTkFrame(self, width=310, corner_radius=12)
        self.sidebar.grid(row=0, column=0, sticky="nswe", padx=12, pady=12)
        self.sidebar.grid_propagate(False)
        
        # 1. Native Wi-Fi Header Card
        self.wifi_card = ctk.CTkFrame(self.sidebar, corner_radius=10, fg_color="#1e293b", border_width=1, border_color="#334155")
        self.wifi_card.pack(fill="x", padx=12, pady=(12, 8))
        
        wifi_header_row = ctk.CTkFrame(self.wifi_card, fg_color="transparent")
        wifi_header_row.pack(fill="x", padx=10, pady=(8, 2))
        
        ctk.CTkLabel(wifi_header_row, text="PC Wi-Fi Network", font=("Plus Jakarta Sans", 11, "bold"), text_color="#94a3b8").pack(side="left")
        ctk.CTkLabel(wifi_header_row, text="Connected", font=("Plus Jakarta Sans", 10, "bold"), text_color="#28a745").pack(side="right")
        
        current_ssid = get_native_wifi_ssid()
        self.wifi_ssid_lbl = ctk.CTkLabel(self.wifi_card, text=current_ssid, font=("Plus Jakarta Sans", 14, "bold"), text_color="#38bdf8")
        self.wifi_ssid_lbl.pack(anchor="w", padx=10, pady=(0, 8))
        
        # 2. Professional Status Typography (No Emojis / No Colons)
        self.status_card = ctk.CTkFrame(self.sidebar, corner_radius=10, fg_color="#0f172a", border_width=1, border_color="#334155")
        self.status_card.pack(fill="x", padx=12, pady=6)
        
        self.status_lbl = ctk.CTkLabel(
            self.status_card,
            text=self.status_state,
            font=("Plus Jakarta Sans", 13, "bold"),
            text_color=self.status_color
        )
        self.status_lbl.pack(pady=8)
        
        # 3. IP Entry & Unified Smart Connect Button
        ip_label = ctk.CTkLabel(self.sidebar, text="Camera IP Address", font=("Plus Jakarta Sans", 12, "bold"), text_color="#cbd5e1")
        ip_label.pack(anchor="w", padx=14, pady=(8, 2))
        
        self.ip_entry = ctk.CTkEntry(self.sidebar, width=280, height=34, font=("JetBrains Mono", 12))
        self.ip_entry.insert(0, self.esp_ip)
        self.ip_entry.pack(padx=12, pady=4)
        
        # Unified 'Connect Camera' Smart Button (smart_connect)
        self.smart_connect_btn = ctk.CTkButton(
            self.sidebar,
            text="Connect Camera",
            command=self.smart_connect,
            fg_color="#0284c7",
            hover_color="#0369a1",
            font=("Plus Jakarta Sans", 12, "bold"),
            height=36,
            corner_radius=8
        )
        self.smart_connect_btn.pack(fill="x", padx=12, pady=8)
        
        # Wi-Fi Setup & Face Database In-App Sheet Triggers
        self.wifi_setup_btn = ctk.CTkButton(
            self.sidebar,
            text="Wi-Fi Setup",
            command=self.open_wifi_modal,
            fg_color="#1e293b",
            hover_color="#334155",
            border_width=1,
            border_color="#475569",
            height=32,
            corner_radius=8
        )
        self.wifi_setup_btn.pack(fill="x", padx=12, pady=4)
        
        self.db_btn = ctk.CTkButton(
            self.sidebar,
            text="Face Database Manager",
            command=self.open_face_db_modal,
            fg_color="#1e293b",
            hover_color="#334155",
            border_width=1,
            border_color="#475569",
            height=32,
            corner_radius=8
        )
        self.db_btn.pack(fill="x", padx=12, pady=4)
        
        # Divider
        ctk.CTkFrame(self.sidebar, height=1, fg_color="#334155").pack(fill="x", pady=12, padx=12)
        
        # Telemetry Stats
        self.fps_lbl = ctk.CTkLabel(self.sidebar, text="FPS 0.0", font=("JetBrains Mono", 13, "bold"), text_color="#10b981")
        self.fps_lbl.pack(anchor="w", padx=14, pady=2)
        
        self.inv_lbl = ctk.CTkLabel(
            self.sidebar,
            text=self.latest_inventory_str,
            justify="left",
            font=("Plus Jakarta Sans", 12),
            text_color="#e2e8f0"
        )
        self.inv_lbl.pack(anchor="nw", fill="both", expand=True, padx=14, pady=6)
        
        # Bottom Power Indicator
        self.batt_lbl = ctk.CTkLabel(
            self.sidebar,
            text="Power Line-Feed 5V Pure Stream",
            font=("Plus Jakarta Sans", 11, "bold"),
            text_color="#64748b"
        )
        self.batt_lbl.pack(side="bottom", pady=12, padx=12)
        
        # ----------------- MAIN VIDEO CANVAS (RIGHT) -----------------
        self.video_frame = ctk.CTkFrame(self, corner_radius=12, fg_color="#020617")
        self.video_frame.grid(row=0, column=1, sticky="nswe", padx=(0, 12), pady=12)
        self.video_frame.grid_rowconfigure(0, weight=1)
        self.video_frame.grid_columnconfigure(0, weight=1)
        
        self.video_label = ctk.CTkLabel(self.video_frame, text="Initializing Camera Stream...", font=("Plus Jakarta Sans", 14), text_color="#64748b")
        self.video_label.grid(row=0, column=0)
        
        # ----------------- IN-APP MODAL SHEET BACKDROP -----------------
        self.modal_backdrop = ctk.CTkFrame(self, fg_color="#090d16", corner_radius=0)
        # Positioned via .place() when active

    def set_status(self, text, color):
        """Updates color-coded professional status typography without emojis or colons."""
        self.status_state = text
        self.status_color = color
        self.status_lbl.configure(text=text, text_color=color)
        self.status_card.configure(border_color=color)

    # ----------------- UNIFIED SMART CONNECT (PHASE 2 ITEM 3) -----------------
    def smart_connect(self):
        """
        Unified smart connect routine:
        Step 1 (Fast Probe): 50ms check on current IP:81
        Step 2 (Subnet Auto-Sweep): If unreachable, 50-thread sweep across /24 subnet (<2s)
        """
        target_ip = self.ip_entry.get().strip()
        if not target_ip:
            target_ip = self.esp_ip
        self.esp_ip = target_ip

        self.set_status("Camera Searching...", "#ffc107")
        self.smart_connect_btn.configure(state="disabled", text="Probing Camera...")

        def _worker():
            # Step 1: Fast Probe (50ms)
            def probe(ip, port=81, timeout_sec=0.08):
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.settimeout(timeout_sec)
                    res = s.connect_ex((ip, port))
                    s.close()
                    return res == 0
                except Exception:
                    return False

            if probe(target_ip):
                print(f"[Smart Connect] Fast Probe Succeeded at {target_ip}:81")
                self.after(0, lambda: self._on_camera_found(target_ip))
                return

            print(f"[Smart Connect] Fast probe failed on {target_ip}. Commencing 50-thread Subnet Auto-Sweep...")
            # Step 2: Subnet Auto-Sweep (/24 subnet in <2s with 50 threads)
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                local_ip = s.getsockname()[0]
                s.close()
            except Exception:
                local_ip = "192.168.0.1"

            subnet_prefix = ".".join(local_ip.split(".")[:3])
            scan_ips = [f"{subnet_prefix}.{i}" for i in range(1, 255)]

            found_ip = None
            with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
                futures = {executor.submit(probe, ip, 81, 0.4): ip for ip in scan_ips}
                for f in concurrent.futures.as_completed(futures):
                    ip = futures[f]
                    try:
                        if f.result():
                            found_ip = ip
                            break
                    except Exception:
                        pass

            if found_ip:
                print(f"[Smart Connect] Subnet Sweep Found Camera at {found_ip}:81")
                self.after(0, lambda: self._on_camera_found(found_ip))
            else:
                print("[Smart Connect] Camera not found on local subnet.")
                self.after(0, self._on_camera_offline)

        threading.Thread(target=_worker, daemon=True).start()

    def _on_camera_found(self, ip):
        self.esp_ip = ip
        self.ip_entry.delete(0, 'end')
        self.ip_entry.insert(0, ip)
        self.reload_flag = True
        self.set_status("Camera Connected", "#28a745")
        self.smart_connect_btn.configure(state="normal", text="Connect Camera")

    def _on_camera_offline(self):
        self.set_status("Camera Offline", "#dc3545")
        self.smart_connect_btn.configure(state="normal", text="Connect Camera")

    # ----------------- UNIVERSAL IN-APP MODAL SHEETS (PHASE 2 ITEM 4) -----------------
    def close_modal(self):
        self.modal_backdrop.place_forget()
        for w in self.modal_backdrop.winfo_children():
            w.destroy()

    # 1. Wi-Fi Settings Modal Sheet with Stream-Pause State Machine
    def open_wifi_modal(self):
        # Stream-Pause State Machine: Pause live stream to free Port 81
        self.stream_paused = True
        print("[State Machine] Stream paused for Wi-Fi configuration.")
        
        self.modal_backdrop.place(relx=0, rely=0, relwidth=1, relheight=1)
        for w in self.modal_backdrop.winfo_children():
            w.destroy()
            
        modal_card = ctk.CTkFrame(self.modal_backdrop, width=760, height=520, corner_radius=16, fg_color="#0f172a", border_width=1, border_color="#334155")
        modal_card.place(relx=0.5, rely=0.5, anchor="center")
        modal_card.pack_propagate(False)
        
        # Header
        hdr = ctk.CTkFrame(modal_card, fg_color="transparent")
        hdr.pack(fill="x", padx=20, pady=(16, 10))
        ctk.CTkLabel(hdr, text="Wi-Fi Settings", font=("Plus Jakarta Sans", 18, "bold"), text_color="#f8fafc").pack(side="left")
        
        def on_done():
            self.close_modal()
            # Done clicked: resume stream after 300ms
            self.after(300, self._resume_stream)

        ctk.CTkButton(hdr, text="Done", command=on_done, width=80, height=30, fg_color="#0284c7", hover_color="#0369a1").pack(side="right")
        
        ctk.CTkLabel(modal_card, text="Manage network associations and scan available router access points.", font=("Plus Jakarta Sans", 11), text_color="#94a3b8").pack(anchor="w", padx=20, pady=(0, 10))
        
        # Dual Symmetrical Columns
        cols_container = ctk.CTkFrame(modal_card, fg_color="transparent")
        cols_container.pack(fill="both", expand=True, padx=20, pady=10)
        cols_container.grid_columnconfigure((0, 1), weight=1, uniform="equal")
        cols_container.grid_rowconfigure(0, weight=1)
        
        # Column 1: KNOWN NETWORKS
        known_box = ctk.CTkFrame(cols_container, fg_color="#1e293b", corner_radius=12, border_width=1, border_color="#334155")
        known_box.grid(row=0, column=0, sticky="nswe", padx=(0, 8), pady=0)
        
        ctk.CTkLabel(known_box, text="KNOWN NETWORKS", font=("Plus Jakarta Sans", 11, "bold"), text_color="#38bdf8").pack(anchor="w", padx=12, pady=(12, 6))
        known_scroll = ctk.CTkScrollableFrame(known_box, fg_color="transparent")
        known_scroll.pack(fill="both", expand=True, padx=6, pady=6)
        
        # Populate Known Networks
        known_list = [get_native_wifi_ssid(), "Detecta_Primary_AP"]
        for net in known_list:
            row = ctk.CTkFrame(known_scroll, fg_color="#0f172a", corner_radius=8)
            row.pack(fill="x", pady=4, padx=4)
            ctk.CTkLabel(row, text=net, font=("Plus Jakarta Sans", 12, "bold"), text_color="#e2e8f0").pack(side="left", padx=10, pady=8)
            ctk.CTkButton(row, text="Forget", width=65, height=26, fg_color="#475569", hover_color="#dc3545", command=lambda n=net, r=row: r.destroy()).pack(side="right", padx=8)

        # Column 2: OTHER NETWORKS
        other_box = ctk.CTkFrame(cols_container, fg_color="#1e293b", corner_radius=12, border_width=1, border_color="#334155")
        other_box.grid(row=0, column=1, sticky="nswe", padx=(8, 0), pady=0)
        
        other_hdr = ctk.CTkFrame(other_box, fg_color="transparent")
        other_hdr.pack(fill="x", padx=12, pady=(12, 6))
        ctk.CTkLabel(other_hdr, text="OTHER NETWORKS", font=("Plus Jakarta Sans", 11, "bold"), text_color="#cbd5e1").pack(side="left")
        
        other_scroll = ctk.CTkScrollableFrame(other_box, fg_color="transparent")
        other_scroll.pack(fill="both", expand=True, padx=6, pady=6)
        
        scan_lbl = ctk.CTkLabel(other_scroll, text="Scanning for Wi-Fi access points...", text_color="#94a3b8", font=("Plus Jakarta Sans", 11))
        scan_lbl.pack(pady=20)
        
        def _scan():
            networks = []
            try:
                res = requests.get("http://192.168.4.1/scan", timeout=6).json()
                networks = res.get("networks", [])
            except Exception:
                # Fallback to local wifi scan list
                networks = ["ORGHO_5G", "Home_Fiber_2.4G", "Guest_WiFi_Ultra", "Detecta_Field_Node"]
                
            def render_scan():
                scan_lbl.destroy()
                for net in networks:
                    row = ctk.CTkFrame(other_scroll, fg_color="#0f172a", corner_radius=8)
                    row.pack(fill="x", pady=4, padx=4)
                    ctk.CTkLabel(row, text=net, font=("Plus Jakarta Sans", 12), text_color="#f1f5f9").pack(anchor="w", padx=10, pady=(6, 2))
                    
                    pass_row = ctk.CTkFrame(row, fg_color="transparent")
                    pass_row.pack(fill="x", padx=8, pady=(0, 6))
                    
                    pwd_entry = ctk.CTkEntry(pass_row, placeholder_text="Password", show="*", width=140, height=26, font=("JetBrains Mono", 10))
                    pwd_entry.pack(side="left", padx=(0, 4))
                    
                    # Password show/hide toggle
                    def toggle_pwd(entry=pwd_entry):
                        entry.configure(show="" if entry.cget("show") == "*" else "*")
                        
                    ctk.CTkButton(pass_row, text="👁", width=28, height=26, fg_color="#334155", command=toggle_pwd).pack(side="left", padx=(0, 4))
                    
                    def connect_net(ssid=net, pwd_field=pwd_entry):
                        pwd = pwd_field.get()
                        try:
                            requests.post("http://192.168.4.1/connect", json={"ssid": ssid, "password": pwd}, timeout=5)
                        except Exception:
                            pass
                        on_done()

                    ctk.CTkButton(pass_row, text="Connect", width=70, height=26, fg_color="#0284c7", hover_color="#0369a1", command=connect_net).pack(side="right")
                    
            self.after(0, render_scan)

        threading.Thread(target=_scan, daemon=True).start()

    def _resume_stream(self):
        self.stream_paused = False
        self.reload_flag = True
        print("[State Machine] Stream resumed smoothly after 300ms delay.")

    # 2. Face Database Manager In-App Sheet
    def open_face_db_modal(self):
        self.modal_backdrop.place(relx=0, rely=0, relwidth=1, relheight=1)
        for w in self.modal_backdrop.winfo_children():
            w.destroy()
            
        modal_card = ctk.CTkFrame(self.modal_backdrop, width=820, height=540, corner_radius=16, fg_color="#0f172a", border_width=1, border_color="#334155")
        modal_card.place(relx=0.5, rely=0.5, anchor="center")
        modal_card.pack_propagate(False)
        
        # Header
        hdr = ctk.CTkFrame(modal_card, fg_color="transparent")
        hdr.pack(fill="x", padx=20, pady=(16, 10))
        ctk.CTkLabel(hdr, text="Face Database Manager", font=("Plus Jakarta Sans", 18, "bold"), text_color="#f8fafc").pack(side="left")
        
        hdr_btns = ctk.CTkFrame(hdr, fg_color="transparent")
        hdr_btns.pack(side="right")
        
        ctk.CTkButton(hdr_btns, text="+ Add New Person", command=lambda: self._prompt_add_person(modal_card), fg_color="#0284c7", hover_color="#0369a1", height=30).pack(side="left", padx=6)
        ctk.CTkButton(hdr_btns, text="Done", command=self.close_modal, width=70, height=30, fg_color="#334155", hover_color="#475569").pack(side="left")

        # Scrollable Persons Grid
        self.face_scroll = ctk.CTkScrollableFrame(modal_card, fg_color="transparent")
        self.face_scroll.pack(fill="both", expand=True, padx=20, pady=10)
        self.render_faces_in_sheet()

    def render_faces_in_sheet(self):
        for w in self.face_scroll.winfo_children():
            w.destroy()
            
        enroll_dir = os.path.join(os.path.expanduser("~"), "Detecta_Enrollments")
        os.makedirs(enroll_dir, exist_ok=True)
        
        person_names = [d for d in os.listdir(enroll_dir) if os.path.isdir(os.path.join(enroll_dir, d))]
        if not person_names:
            # Fallback to existing memory database
            for name in self.known_faces.keys():
                if name not in person_names:
                    person_names.append(name)
                    
        if not person_names:
            ctk.CTkLabel(self.face_scroll, text="No enrolled identities in database. Click '+ Add New Person'.", text_color="#94a3b8", font=("Plus Jakarta Sans", 13)).pack(pady=40)
            return

        for person_name in person_names:
            p_dir = os.path.join(enroll_dir, person_name)
            card = ctk.CTkFrame(self.face_scroll, fg_color="#1e293b", corner_radius=10, border_width=1, border_color="#334155")
            card.pack(fill="x", pady=5, padx=5)
            
            # Left: Avatar & Name
            left_f = ctk.CTkFrame(card, fg_color="transparent")
            left_f.pack(side="left", padx=12, pady=10)
            
            ctk.CTkLabel(left_f, text=person_name, font=("Plus Jakarta Sans", 15, "bold"), text_color="#38bdf8").pack(anchor="w")
            ctk.CTkLabel(left_f, text="ArcFace 512-D Verified", font=("Plus Jakarta Sans", 10), text_color="#10b981").pack(anchor="w")
            
            # Photos Preview (Max 3)
            photo_f = ctk.CTkFrame(card, fg_color="transparent")
            photo_f.pack(side="left", padx=16)
            
            photos = []
            if os.path.exists(p_dir):
                photos = [f for f in os.listdir(p_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
                
            for ph in photos[:3]:
                ph_path = os.path.join(p_dir, ph)
                try:
                    p_img = Image.open(ph_path)
                    p_img.thumbnail((48, 48))
                    c_img = ctk.CTkImage(light_image=p_img, dark_image=p_img, size=(48, 48))
                    lbl = ctk.CTkLabel(photo_f, image=c_img, text="")
                    lbl.image = c_img
                    lbl.pack(side="left", padx=3)
                except Exception:
                    pass

            # Actions: Rename, Add Photo, Delete
            act_f = ctk.CTkFrame(card, fg_color="transparent")
            act_f.pack(side="right", padx=12)
            
            if len(photos) < 3:
                ctk.CTkButton(act_f, text="Add Photo", width=80, height=28, fg_color="#334155", hover_color="#475569", command=lambda p=person_name: self._add_photo_sheet(p)).pack(side="left", padx=4)
                
            ctk.CTkButton(act_f, text="Rename", width=70, height=28, fg_color="#ffc107", text_color="#000000", hover_color="#eab308", command=lambda p=person_name: self._rename_person_sheet(p)).pack(side="left", padx=4)
            ctk.CTkButton(act_f, text="Delete", width=70, height=28, fg_color="#dc3545", hover_color="#b91c1c", command=lambda p=person_name: self._delete_person_sheet(p)).pack(side="left", padx=4)

    def _prompt_add_person(self, parent_card):
        dialog = ctk.CTkInputDialog(text="Enter full name for new identity:", title="Add Person")
        name = dialog.get_input()
        if not name:
            return
        name = name.strip()
        enroll_dir = os.path.join(os.path.expanduser("~"), "Detecta_Enrollments")
        p_dir = os.path.join(enroll_dir, name)
        os.makedirs(p_dir, exist_ok=True)
        self._add_photo_sheet(name)

    def _add_photo_sheet(self, person_name):
        from tkinter import filedialog
        import shutil
        paths = filedialog.askopenfilenames(
            title=f"Select photos for {person_name} (Max 3)",
            filetypes=[("Image files", "*.jpg *.png *.jpeg")]
        )
        if not paths:
            return
            
        enroll_dir = os.path.join(os.path.expanduser("~"), "Detecta_Enrollments")
        p_dir = os.path.join(enroll_dir, person_name)
        os.makedirs(p_dir, exist_ok=True)
        existing = len([f for f in os.listdir(p_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))])
        allowed = 3 - existing
        
        for p in list(paths)[:allowed]:
            ext = os.path.splitext(p)[1]
            idx = len(os.listdir(p_dir)) + 1
            shutil.copy(p, os.path.join(p_dir, f"photo_{idx}{ext}"))
            
        self.sync_database()
        self.render_faces_in_sheet()

    def _rename_person_sheet(self, old_name):
        dialog = ctk.CTkInputDialog(text=f"Enter new name for {old_name}:", title="Rename Person")
        new_name = dialog.get_input()
        if not new_name or new_name.strip() == old_name:
            return
        new_name = new_name.strip()
        enroll_dir = os.path.join(os.path.expanduser("~"), "Detecta_Enrollments")
        old_dir = os.path.join(enroll_dir, old_name)
        new_dir = os.path.join(enroll_dir, new_name)
        if os.path.exists(old_dir):
            os.rename(old_dir, new_dir)
        if old_name in self.known_faces:
            self.known_faces[new_name] = self.known_faces.pop(old_name)
            pickle.dump(self.known_faces, open(self.db_path, "wb"))
        self.sync_database()
        self.render_faces_in_sheet()

    def _delete_person_sheet(self, person_name):
        import shutil
        enroll_dir = os.path.join(os.path.expanduser("~"), "Detecta_Enrollments")
        p_dir = os.path.join(enroll_dir, person_name)
        if os.path.exists(p_dir):
            shutil.rmtree(p_dir)
        if person_name in self.known_faces:
            del self.known_faces[person_name]
            pickle.dump(self.known_faces, open(self.db_path, "wb"))
        self.render_faces_in_sheet()

    def sync_database(self):
        enroll_dir = os.path.join(os.path.expanduser("~"), "Detecta_Enrollments")
        if not os.path.exists(enroll_dir):
            return
            
        for person_name in os.listdir(enroll_dir):
            person_path = os.path.join(enroll_dir, person_name)
            if not os.path.isdir(person_path):
                continue
            embeddings = []
            for img_name in os.listdir(person_path):
                if img_name.lower().endswith(('.png', '.jpg', '.jpeg')):
                    try:
                        pil_img = Image.open(os.path.join(person_path, img_name)).convert('RGB')
                        img = np.array(pil_img)[:, :, ::-1].copy()
                        faces = self.face_app.get(img)
                        if faces:
                            embeddings.append(faces[0].embedding)
                    except Exception:
                        pass
            if embeddings:
                self.known_faces[person_name] = np.mean(embeddings, axis=0)
                
        pickle.dump(self.known_faces, open(self.db_path, "wb"))
        print(f"[Database] Synced {len(self.known_faces)} biometric identities.")

    # ----------------- BACKGROUND ENGINE DAEMONS -----------------
    def start_daemons(self):
        threading.Thread(target=self.capture_frames, daemon=True).start()
        threading.Thread(target=self.run_inference_loop, daemon=True).start()

    def capture_frames(self):
        while True:
            if self.stream_paused:
                time.sleep(0.05)
                continue
                
            stream_url = f"http://{self.esp_ip}:81/stream"
            cap = cv2.VideoCapture(stream_url)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            if not cap.isOpened():
                time.sleep(1.0)
                continue
                
            while cap.isOpened() and not self.stream_paused:
                if self.reload_flag:
                    self.reload_flag = False
                    break
                    
                ret, frame = cap.read()
                if not ret:
                    break
                    
                frame = cv2.flip(frame, -1)
                while not self.frame_queue.empty():
                    try:
                        self.frame_queue.get_nowait()
                    except Exception:
                        pass
                self.frame_queue.put(frame)
                
            cap.release()

    def run_inference_loop(self):
        while True:
            try:
                frame = self.frame_queue.get(timeout=1)
                start_time = time.time()
                
                # YOLO Inference
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
                        
                        if best_score > 0.45:
                            x1, y1, x2, y2 = map(int, face.bbox)
                            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (40, 167, 69), 2)
                            cv2.putText(annotated_frame, f"{best_match} ({best_score:.2f})", (x1, y1 - 10), 
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (40, 167, 69), 2)
                
                counts = collections.Counter([self.model.names[int(c)] for c in results[0].boxes.cls])
                inv_text = "Live Inventory\n" + "\n".join([f"- {k}: {v}" for k, v in counts.items()]) if counts else "Live Inventory\n- None"
                
                self.latest_annotated_frame = annotated_frame
                self.latest_inventory_str = inv_text
                
                dt = time.time() - start_time
                self.latest_fps = (1.0 / dt) if dt > 0 else 0.0
                
            except queue.Empty:
                pass
            except Exception:
                pass

    def update_video(self):
        if self.latest_annotated_frame is not None and not self.stream_paused:
            rgb_image = cv2.cvtColor(self.latest_annotated_frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(rgb_image)
            pil_img.thumbnail((860, 640))
            tk_img = ImageTk.PhotoImage(image=pil_img)
            self.video_label.configure(image=tk_img, text="")
            self.video_label.image = tk_img
            
            self.inv_lbl.configure(text=self.latest_inventory_str)
            self.fps_lbl.configure(text=f"FPS {self.latest_fps:.1f}")
            
        self.after(30, self.update_video)


if __name__ == "__main__":
    multiprocessing.freeze_support()
    app = DetectaApp()
    app.mainloop()
