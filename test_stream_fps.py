"""
Detecta — Low-Level Stream Throughput & Latency Benchmark Script
Used to isolate network transmission issues from AI inference load.
"""
import cv2
import threading
import time

STREAM_URL = "http://192.168.0.216:81/stream"

class CameraStream:
    def __init__(self, src=0):
        self.stream = cv2.VideoCapture(src)
        self.stream.set(cv2.CAP_PROP_BUFFERSIZE, 2)
        (self.grabbed, self.frame) = self.stream.read()
        self.stopped = False
        self.new_frames = 0
        self.fps = 0.0

    def start(self):
        threading.Thread(target=self.update, args=(), daemon=True).start()
        return self

    def update(self):
        last_calc = time.time()
        count = 0
        while not self.stopped:
            if not self.grabbed:
                self.stop()
            else:
                (self.grabbed, self.frame) = self.stream.read()
                if self.grabbed:
                    self.new_frames += 1
                    count += 1
            now = time.time()
            if now - last_calc >= 1.0:
                self.fps = count / (now - last_calc)
                count = 0
                last_calc = now

    def read(self):
        return self.frame

    def stop(self):
        self.stopped = True

print(f"[Detecta] Starting Home-Intelligent CameraStream on {STREAM_URL}...")
cam = CameraStream(STREAM_URL).start()

t_wait = time.time()
while cam.read() is None and time.time() - t_wait < 5.0:
    time.sleep(0.1)

if cam.read() is None:
    print("[Detecta] Failed to connect to camera stream.")
    exit(1)

print("[Detecta] Connected successfully! Opening live display window. Press 'q' to quit.")

cv2.namedWindow("Home-Intelligent ESP32-CAM Stream", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Home-Intelligent ESP32-CAM Stream", 640, 480)

try:
    while True:
        frame = cam.read()
        if frame is None:
            time.sleep(0.01)
            continue

        h, w = frame.shape[:2]
        display = frame.copy()

        # High-contrast HUD FPS Badge overlay
        cv2.rectangle(display, (12, 12), (360, 68), (15, 23, 42), -1)
        cv2.rectangle(display, (12, 12), (360, 68), (56, 189, 248), 2)
        cv2.circle(display, (28, 40), 6, (0, 255, 0), -1)
        cv2.putText(
            display,
            f"FPS: {cam.fps:4.1f}",
            (44, 46),
            cv2.FONT_HERSHEY_DUPLEX,
            0.8,
            (0, 255, 0),
            2,
            cv2.LINE_AA,
        )
        cv2.putText(
            display,
            f"| {w}x{h} VGA | Frame #{cam.new_frames}",
            (170, 44),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (203, 213, 225),
            1,
            cv2.LINE_AA,
        )

        cv2.imshow("Home-Intelligent ESP32-CAM Stream", display)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
finally:
    cam.stop()
    cv2.destroyAllWindows()
