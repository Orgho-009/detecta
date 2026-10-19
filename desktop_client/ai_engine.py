"""
High-Precision Multi-Modal Vision & Biometric AI Engine:
- Ultralytics YOLO11s (RTX 4050 CUDA Acceleration)
- InsightFace 512-d ArcFace Biometrics with [Verified] status
- MediaPipe Hand Sign & Gesture Recognition (Thumbs Up, Palm, Victory, Fist, Pointing, Rock)
- Temporal Persistence Tracking (eliminates flickering & keeps detections rock-solid)
- Smart Handheld Peripheral Disambiguation (Mouse vs Cell Phone vs Keyboard)
- Uncluttered HUD: Suppresses giant full-body box when Face is Verified
- Live multi-object inventory & layered visual annotations
"""
import os
import cv2
import time
import pickle
import numpy as np
import torch
from ultralytics import YOLO
from insightface.app import FaceAnalysis

try:
    import mediapipe as mp
    GestureRecognizer = mp.tasks.vision.GestureRecognizer
    GestureRecognizer.__del__ = lambda self: None # Prevent exit shutdown error
    HAS_MEDIAPIPE = True
except Exception:
    HAS_MEDIAPIPE = False

INDOOR_TARGET_CLASSES = {
    0: "Human",
    24: "Backpack / Bag",
    26: "Handbag",
    39: "Bottle / Spray",
    41: "Cup / Mug",
    46: "Banana",
    47: "Apple",
    49: "Orange / Fruit",
    58: "Flowers / Plant",
    62: "TV/Monitor",
    63: "Laptop",
    64: "Mouse",
    65: "Remote",
    66: "Keyboard",
    67: "Cell Phone",
    73: "Book",
    74: "Watch / Clock",
    75: "Vase / Flowers",
    77: "Doll / Teddy Bear"
}
ALLOWED_CLASS_IDS = list(INDOOR_TARGET_CLASSES.keys())

GESTURE_EMOJIS = {
    "Thumb_Up": "👍 Thumbs Up",
    "Thumb_Down": "👎 Thumbs Down",
    "Open_Palm": "✋ Open Palm",
    "Closed_Fist": "👊 Fist",
    "Victory": "✌️ Victory",
    "Pointing_Up": "☝️ Pointing",
    "ILoveYou": "🤟 Rock / Love"
}

def calc_iou(b1, b2):
    x1, y1 = max(b1[0], b2[0]), max(b1[1], b2[1])
    x2, y2 = min(b1[2], b2[2]), min(b1[3], b2[3])
    inter = max(0, x2 - x1) * max(0, y2 - y1)
    a1 = (b1[2] - b1[0]) * (b1[3] - b1[1])
    a2 = (b2[2] - b2[0]) * (b2[3] - b2[1])
    union = a1 + a2 - inter
    return inter / union if union > 0 else 0

class TrackedBox:
    def __init__(self, cls_name, box, score, ttl=6):
        self.cls_name = cls_name
        self.box = list(box)
        self.score = score
        self.ttl = ttl

    def update(self, box, score, ttl=6):
        # Smooth coordinates with exponential moving average
        alpha = 0.65
        self.box = [
            int(alpha * n + (1.0 - alpha) * o)
            for n, o in zip(box, self.box)
        ]
        self.score = max(self.score, score)
        self.ttl = ttl

class AIEngine:
    def __init__(self, yolo_path=None, db_path="desktop_client/known_faces.pkl"):
        # Select device (CUDA on Windows -> MPS on Apple Silicon -> CPU fallback)
        if torch.cuda.is_available():
            self.device = "cuda"
        elif torch.backends.mps.is_available():
            self.device = "mps"
        else:
            self.device = "cpu"

        if yolo_path is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            s_path = os.path.join(base_dir, "yolo11s.pt")
            n_path = os.path.join(base_dir, "yolo11n.pt")
            yolo_path = s_path if os.path.exists(s_path) else n_path

        print(f"[AI Engine] Loading YOLO model ({yolo_path}) on {self.device}...")
        self.model = YOLO(yolo_path)

        print("[AI Engine] Initializing Face Analysis with 0.5x downscaled engine...")
        providers = ['CUDAExecutionProvider', 'CPUExecutionProvider'] if self.device == "cuda" else ['CPUExecutionProvider']
        self.face_app = FaceAnalysis(name='buffalo_l', providers=providers)
        self.face_app.prepare(ctx_id=0 if self.device == "cuda" else -1, det_size=(320, 320))

        # MediaPipe Hand Gesture Recognizer
        self.gesture_recognizer = None
        if HAS_MEDIAPIPE:
            try:
                base_dir = os.path.dirname(os.path.abspath(__file__))
                task_path = os.path.join(base_dir, "gesture_recognizer.task")
                if os.path.exists(task_path):
                    options = mp.tasks.vision.GestureRecognizerOptions(
                        base_options=mp.tasks.BaseOptions(model_asset_path=task_path),
                        running_mode=mp.tasks.vision.RunningMode.IMAGE,
                        num_hands=2,
                        min_hand_detection_confidence=0.35,
                        min_hand_presence_confidence=0.35
                    )
                    self.gesture_recognizer = GestureRecognizer.create_from_options(options)
                    print("[AI Engine] MediaPipe Hand Gesture Recognizer initialized successfully!")
            except Exception as e:
                print(f"[AI Engine] Could not initialize Gesture Recognizer: {e}")

        self.db_path = db_path
        self.known_faces = {}
        self.load_database()

        self.frame_count = 0
        self.cached_faces = []
        self.cached_gestures = []
        self.tracked_objects = [] # Temporal persistence for objects
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
        Multi-Modal AI Pipeline with Temporal Smoothing:
        1. YOLO Object & Person Detection on curated target classes (conf=0.18)
        2. InsightFace 512-d Facial Biometrics with [Verified] status
        3. MediaPipe Hand Sign & Gesture Recognition
        4. Temporal Tracking & Persistence (Zero Flickering)
        5. Smart Handheld Disambiguation (Mouse vs Cell Phone vs Keyboard)
        6. Clean HUD: Suppresses giant body rectangle when Face is Verified
        7. Real-Time Telemetry & Inventory
        """
        self.frame_count += 1
        h, w = frame.shape[:2]
        annotated = frame.copy()

        # 1. Run YOLO inference strictly on indoor/everyday curated classes (conf=0.28)
        results = self.model(
            frame,
            classes=ALLOWED_CLASS_IDS,
            conf=0.28,
            device=self.device,
            verbose=False
        )

        raw_human_boxes = []
        candidates = []

        if len(results) > 0 and len(results[0].boxes) > 0:
            for b in results[0].boxes:
                cls_id = int(b.cls[0])
                score = float(b.conf[0])
                x1, y1, x2, y2 = map(int, b.xyxy[0].tolist())
                bw = x2 - x1
                bh = y2 - y1
                aspect = max(bw, bh) / max(1, min(bw, bh))

                if cls_id == 0:
                    if score >= 0.35:
                        raw_human_boxes.append((x1, y1, x2, y2, score))
                    continue

                cls_name = INDOOR_TARGET_CLASSES.get(cls_id, f"obj_{cls_id}")

                # Universal Sanity Filters:
                # 1. Reject optical slivers / curtain pleats (minimum box dimension >= 25px)
                if min(bw, bh) < 25:
                    continue
                # 2. Reject full camera frame background boxes (e.g. whole screen TV hallucination)
                if (bw * bh) > 0.75 * (w * h):
                    continue
                # 3. Book / Paper (reject high-aspect curtain folds)
                if cls_name == "Book" and (aspect > 2.5 or min(bw, bh) < 40):
                    continue
                # 4. TV/Monitor (reject desktop/wall false positives)
                if cls_name == "TV/Monitor" and (score < 0.50 or bw < 120 or bh < 90):
                    continue

                candidates.append((score, cls_name, [x1, y1, x2, y2], aspect, bw, bh))

        # Cross-class NMS: sort by confidence descending so higher-scoring class wins overlapping regions
        candidates.sort(key=lambda x: x[0], reverse=True)
        new_detections = []
        for score, name, box, aspect, bw, bh in candidates:
            overlap = False
            for _, fbox, _ in new_detections:
                if calc_iou(box, fbox) > 0.40:
                    overlap = True
                    break
            if not overlap:
                # Disambiguate handheld objects AFTER cross-class NMS:
                # A compact dark peripheral held or on desk is a Mouse
                if name == "Cell Phone" and aspect < 1.55 and max(bw, bh) < 190:
                    name = "Mouse"
                elif name == "Remote" and max(bw, bh) < 190:
                    name = "Mouse"
                new_detections.append((name, box, score))

        # 2. Biometric Face Recognition (Staggered on frame_count % 4 == 2 to avoid coinciding with gestures)
        should_check_face = (
            len(raw_human_boxes) > 0 or 
            len(self.cached_faces) > 0 or 
            (self.frame_count % 8 == 2)
        )

        if should_check_face and len(self.known_faces) > 0:
            if self.frame_count % 4 == 2 or len(self.cached_faces) == 0:
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

                    if best_dist <= 0.45:
                        label = f"{best_name} [Verified]"
                    else:
                        label = "Unknown"

                    self.cached_faces.append((fx1, fy1, fx2, fy2, label))
        elif len(raw_human_boxes) == 0 and len(self.cached_faces) > 0:
            if self.frame_count % 4 == 2:
                self.cached_faces = []

        # 3. MediaPipe Hand Sign & Gesture Recognition (Staggered on frame_count % 4 == 0 on downsampled frame)
        current_gestures = []
        if self.gesture_recognizer is not None:
            if self.frame_count % 4 == 0 or len(self.cached_gestures) == 0:
                try:
                    small_rgb = cv2.resize(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), (320, 240))
                    mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=small_rgb)
                    gesture_result = self.gesture_recognizer.recognize(mp_img)

                    if gesture_result and gesture_result.hand_landmarks:
                        for idx, landmarks in enumerate(gesture_result.hand_landmarks):
                            xs = [int(pt.x * w) for pt in landmarks]
                            ys = [int(pt.y * h) for pt in landmarks]
                            gx1, gy1 = max(0, min(xs) - 10), max(0, min(ys) - 10)
                            gx2, gy2 = min(w, max(xs) + 10), min(h, max(ys) + 10)

                            g_name = "Hand"
                            g_score = 0.5
                            if gesture_result.gestures and len(gesture_result.gestures) > idx and gesture_result.gestures[idx]:
                                top_g = gesture_result.gestures[idx][0]
                                raw_g = top_g.category_name
                                g_score = top_g.score
                                if raw_g in GESTURE_EMOJIS and g_score >= 0.4:
                                    g_name = GESTURE_EMOJIS[raw_g]

                            current_gestures.append((gx1, gy1, gx2, gy2, g_name, g_score))
                        self.cached_gestures = current_gestures
                    else:
                        if self.frame_count % 4 == 0:
                            self.cached_gestures = []
                except Exception:
                    pass
            current_gestures = self.cached_gestures

        # 4. Temporal Persistence Tracker Update (Zero Flickering)
        # Match new detections with existing tracked objects
        for cls_name, box, score in new_detections:
            matched = False
            for t in self.tracked_objects:
                if calc_iou(t.box, box) > 0.35:
                    t.cls_name = cls_name
                    ttl_val = 8 if cls_name == "Doll / Teddy Bear" else 5
                    t.update(box, score, ttl=ttl_val)
                    matched = True
                    break
            if not matched:
                ttl_val = 8 if cls_name == "Doll / Teddy Bear" else 5
                self.tracked_objects.append(TrackedBox(cls_name, box, score, ttl=ttl_val))

        # Decay and remove expired tracks
        active_objects = []
        for t in self.tracked_objects:
            was_updated = any(calc_iou(t.box, b) > 0.35 for _, b, _ in new_detections)
            if not was_updated:
                t.ttl -= 1
            if t.ttl > 0:
                active_objects.append(t)
        self.tracked_objects = active_objects

        # 5. Suppress Gesture Boxes if Hand is Holding an Object
        filtered_gestures = []
        for (gx1, gy1, gx2, gy2, g_name, g_score) in current_gestures:
            if g_name == "Hand":
                continue # Do not draw plain hand box
            hand_box = [gx1, gy1, gx2, gy2]
            holding_object = any(
                calc_iou(hand_box, t.box) > 0.15 or
                (max(0, min(gx2, t.box[2]) - max(gx1, t.box[0])) * max(0, min(gy2, t.box[3]) - max(gy1, t.box[1])) > 0.2 * (gx2 - gx1) * (gy2 - gy1))
                for t in self.tracked_objects
            )
            if not holding_object:
                filtered_gestures.append((gx1, gy1, gx2, gy2, g_name, g_score))

        # 6. Human Presence & Clean HUD Filtering
        # If face is verified (e.g. ORGHO), user is 100% confirmed present!
        # We do NOT draw the giant body rectangle over the user's chest/hands when face is verified!
        # Only draw body rectangle if an un-faced intruder is detected.
        has_verified_face = any("[Verified]" in label for (_, _, _, _, label) in self.cached_faces)
        human_count = 0
        unfaced_human_boxes = []

        if len(self.cached_faces) > 0:
            human_count = len(self.cached_faces)
        else:
            # Check if any genuine un-faced body is present (vertically oriented, tall)
            for (hx1, hy1, hx2, hy2, score) in raw_human_boxes:
                hw = hx2 - hx1
                hh = hy2 - hy1
                # Must be vertically oriented human body
                if hh >= 170 and (hh > hw * 1.1) and score >= 0.60:
                    unfaced_human_boxes.append((hx1, hy1, hx2, hy2, score))
            human_count = len(unfaced_human_boxes)

        # 7. Build Live Inventory
        inventory = {}
        if human_count > 0:
            inventory["Human"] = human_count
        for t in self.tracked_objects:
            inventory[t.cls_name] = inventory.get(t.cls_name, 0) + 1
        for (_, _, _, _, g_name, _) in filtered_gestures:
            inventory[g_name] = inventory.get(g_name, 0) + 1

        # 8. Layered Visual Annotations Rendering

        # Layer 1: General Objects (Cyan: BGR (248, 189, 56)) - Persistent & Smooth
        for t in self.tracked_objects:
            x1, y1, x2, y2 = t.box
            cv2.rectangle(annotated, (x1, y1), (x2, y2), (248, 189, 56), 2)
            badge_text = f"{t.cls_name} {t.score:.2f}"
            (tw, th), _ = cv2.getTextSize(badge_text, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
            cv2.rectangle(annotated, (x1, max(0, y1 - 18)), (x1 + tw + 6, max(18, y1)), (248, 189, 56), -1)
            cv2.putText(annotated, badge_text, (x1 + 3, max(14, y1 - 4)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (15, 23, 42), 1, cv2.LINE_AA)

        # Layer 2: Hand Signs & Gestures (Magenta: BGR (255, 105, 180)) - Only on empty gesturing hands
        for (gx1, gy1, gx2, gy2, g_name, g_score) in filtered_gestures:
            cv2.rectangle(annotated, (gx1, gy1), (gx2, gy2), (255, 105, 180), 2)
            badge_text = f"{g_name} {g_score:.2f}"
            (tw, th), _ = cv2.getTextSize(badge_text, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
            cv2.rectangle(annotated, (gx1, max(0, gy1 - 18)), (gx1 + tw + 6, max(18, gy1)), (255, 105, 180), -1)
            cv2.putText(annotated, badge_text, (gx1 + 3, max(14, gy1 - 4)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (15, 23, 42), 1, cv2.LINE_AA)

        # Layer 3: Un-faced Human Intruder (Subtle Orange: BGR (0, 140, 255))
        # Only drawn if no face was detected!
        if not has_verified_face and len(self.cached_faces) == 0:
            for (x1, y1, x2, y2, score) in unfaced_human_boxes:
                cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 140, 255), 2)
                badge_text = f"Human {score:.2f}"
                (tw, th), _ = cv2.getTextSize(badge_text, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
                cv2.rectangle(annotated, (x1, max(0, y1 - 18)), (x1 + tw + 6, max(18, y1)), (0, 140, 255), -1)
                cv2.putText(annotated, badge_text, (x1 + 3, max(14, y1 - 4)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)

        # Layer 4: Biometric Face (Emerald Green for Verified, Red for Unknown) - Highest Priority
        for (fx1, fy1, fx2, fy2, label) in self.cached_faces:
            color = (0, 255, 0) if "[Verified]" in label else (0, 0, 255)
            cv2.rectangle(annotated, (fx1, fy1), (fx2, fy2), color, 2)
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(annotated, (fx1, max(0, fy1 - 20)), (fx1 + tw + 6, max(20, fy1)), color, -1)
            text_color = (0, 0, 0) if "[Verified]" in label else (255, 255, 255)
            cv2.putText(annotated, label, (fx1 + 3, max(15, fy1 - 5)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, text_color, 1, cv2.LINE_AA)

        self.latest_inventory = inventory
        return annotated, inventory
