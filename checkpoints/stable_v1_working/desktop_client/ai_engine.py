"""
High-Performance Vision & AI Engine
Directly aligned with Home-Intelligent architecture:
- Ultralytics YOLO11 on Apple Silicon MPS (or CUDA/CPU on Windows)
- Human Detection (class 0: person)
- Fast Face Recognition using InsightFace on 0.5x downscaled frame
- 3-frame temporal striding to prevent CPU starvation
- Live Inventory and object counts
"""
import os
import cv2
import time
import pickle
import numpy as np
import torch
from ultralytics import YOLO
from insightface.app import FaceAnalysis

class AIEngine:
    def __init__(self, yolo_path="desktop_client/yolo11n.pt", db_path="desktop_client/known_faces.pkl"):
        # Select device (CUDA on Windows -> MPS on Apple Silicon -> CPU fallback)
        if torch.cuda.is_available():
            self.device = "cuda"
        elif torch.backends.mps.is_available():
            self.device = "mps"
        else:
            self.device = "cpu"

        print(f"[AI Engine] Loading YOLO11 model ({yolo_path}) on {self.device}...")
        self.model = YOLO(yolo_path)

        print("[AI Engine] Initializing Face Analysis with 0.5x downscaled engine...")
        providers = ['CUDAExecutionProvider', 'CPUExecutionProvider'] if self.device == "cuda" else ['CPUExecutionProvider']
        self.face_app = FaceAnalysis(name='buffalo_l', providers=providers)
        self.face_app.prepare(ctx_id=0 if self.device == "cuda" else -1, det_size=(320, 320))

        self.db_path = db_path
        self.known_faces = {}
        self.load_database()

        self.frame_count = 0
        self.cached_faces = []
        self.cached_boxes = []
        self.latest_inventory = {}

    def load_database(self):
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, "rb") as f:
                    data = pickle.load(f)
                    if isinstance(data, dict):
                        self.known_faces = data
                        print(f"[AI Engine] Loaded {len(self.known_faces)} enrolled faces from {self.db_path}")
            except Exception as e:
                print(f"[AI Engine] Could not load {self.db_path}: {e}")
                self.known_faces = {}

    def save_database(self):
        try:
            with open(self.db_path, "wb") as f:
                pickle.dump(self.known_faces, f)
            print(f"[AI Engine] Saved {len(self.known_faces)} faces to {self.db_path}")
        except Exception as e:
            print(f"[AI Engine] Failed to save {self.db_path}: {e}")

    def enroll_face_from_frame(self, frame, name):
        """Enroll the largest face visible in the given frame."""
        small = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
        faces = self.face_app.get(small)
        if not faces:
            return False, "No face detected in frame."

        faces.sort(key=lambda x: (x.bbox[2]-x.bbox[0]) * (x.bbox[3]-x.bbox[1]), reverse=True)
        self.known_faces[name] = faces[0].embedding
        self.save_database()
        return True, f"Successfully enrolled '{name}'!"

    def process(self, frame):
        """
        High-Performance Human & Biometric Vision Engine:
        1. YOLO Person Detection (classes=[0], conf=0.35)
        2. InsightFace identification on 0.5x downsampled frame every 3rd frame (specifically for human faces)
        3. Returns annotated frame with clean bounding boxes and real-time inventory
        """
        self.frame_count += 1
        h, w = frame.shape[:2]
        annotated = frame.copy()

        # 1. Run YOLO person detection (classes=[0], confidence threshold 0.35)
        results = self.model(frame, classes=[0], conf=0.35, device=self.device, verbose=False)
        person_detected = False
        human_boxes = []
        inventory = {}

        if len(results) > 0 and len(results[0].boxes) > 0:
            for b in results[0].boxes:
                cls_id = int(b.cls[0])
                if cls_id == 0:
                    person_detected = True
                    score = float(b.conf[0])
                    x1, y1, x2, y2 = map(int, b.xyxy[0].tolist())
                    human_boxes.append((x1, y1, x2, y2, score))

        if person_detected:
            inventory["Human"] = len(human_boxes)

        # 2. Face Recognition with 3-frame Temporal Striding (only if a person is in the frame)
        if person_detected and len(self.known_faces) > 0:
            if self.frame_count % 3 == 0 or len(self.cached_faces) == 0:
                small = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
                detected_faces = self.face_app.get(small)

                self.cached_faces = []
                for f in detected_faces:
                    fx1, fy1, fx2, fy2 = [int(v * 2.0) for v in f.bbox]
                    emb = f.embedding

                    best_name, best_dist = "Unknown", 1.0
                    for name, known_emb in self.known_faces.items():
                        sim = np.dot(emb, known_emb) / (np.linalg.norm(emb) * np.linalg.norm(known_emb))
                        dist = 1.0 - sim
                        if dist < best_dist:
                            best_dist = dist
                            best_name = name

                    if best_dist <= 0.45: # Strict biometric threshold
                        label = f"{best_name} ({best_dist:.2f})"
                    else:
                        label = "Unknown"

                    self.cached_faces.append((fx1, fy1, fx2, fy2, label))

        elif not person_detected:
            self.cached_faces = []

        # 3. Draw Annotations
        # A. Draw Human boxes (Orange)
        for (x1, y1, x2, y2, score) in human_boxes:
            cv2.rectangle(annotated, (x1, y1), (x2, y2), (255, 140, 0), 2)
            badge_text = f"Human {score:.2f}"
            (tw, th), _ = cv2.getTextSize(badge_text, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
            cv2.rectangle(annotated, (x1, max(0, y1 - 18)), (x1 + tw + 6, max(18, y1)), (255, 140, 0), -1)
            cv2.putText(annotated, badge_text, (x1 + 3, max(14, y1 - 4)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)

        # B. Draw Biometric Face boxes (Green for recognized, Red for Unknown)
        for (fx1, fy1, fx2, fy2, label) in self.cached_faces:
            color = (0, 255, 0) if not label.startswith("Unknown") else (0, 0, 255)
            cv2.rectangle(annotated, (fx1, fy1), (fx2, fy2), color, 2)
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(annotated, (fx1, max(0, fy1 - 20)), (fx1 + tw + 6, max(20, fy1)), color, -1)
            text_color = (0, 0, 0) if not label.startswith("Unknown") else (255, 255, 255)
            cv2.putText(annotated, label, (fx1 + 3, max(15, fy1 - 5)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, text_color, 1, cv2.LINE_AA)

        self.latest_inventory = inventory
        return annotated, inventory
