"""
High-Performance Camera Stream Reader
Directly optimized for ESP32-CAM and Windows 11.
Bypasses OpenCV's blocking FFmpeg MJPEG socket bugs by using native HTTP chunked streaming (via requests),
while maintaining full cv2.VideoCapture fallback for local USB webcams.
"""
import os
import sys
import time
import threading
import cv2
import numpy as np
import requests

# Windows High-DPI scaling fix
if sys.platform == "win32":
    import ctypes
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

class CameraStream:
    def __init__(self, src=0, buffer_size=1):
        if isinstance(src, str) and src.isdigit():
            self.src = int(src)
            self.is_http = False
        elif isinstance(src, int):
            self.src = src
            self.is_http = False
        else:
            self.src = str(src).strip()
            self.is_http = self.src.startswith("http://") or self.src.startswith("https://")

        self.buffer_size = buffer_size
        self.frame = None
        self.stopped = False
        self.new_frames = 0
        self.fps = 0.0
        self.last_frame_time = 0.0
        self.lock = threading.Lock()
        self.cv_stream = None

    def start(self):
        if self.is_http:
            threading.Thread(target=self._run_http_stream, daemon=True).start()
        else:
            threading.Thread(target=self._run_cv_stream, daemon=True).start()
        return self

    def _run_http_stream(self):
        """Native chunked HTTP stream reader without OpenCV FFmpeg deadlock."""
        while not self.stopped:
            try:
                # Connect with short timeout so reconnections are instant
                with requests.get(self.src, stream=True, timeout=(3.0, 5.0)) as r:
                    if r.status_code != 200:
                        time.sleep(0.5)
                        continue

                    buf = bytearray()
                    last_calc = time.time()
                    count = 0

                    for chunk in r.iter_content(chunk_size=32768):
                        if self.stopped:
                            break
                        if not chunk:
                            continue

                        buf.extend(chunk)

                        while True:
                            # 1. Content-Length parser (standard for ESP32-CAM MJPEG)
                            hdr = buf.find(b'Content-Length:')
                            if hdr != -1:
                                end_hdr = buf.find(b'\r\n\r\n', hdr)
                                if end_hdr == -1:
                                    break
                                try:
                                    clen = int(buf[hdr + 15:end_hdr].strip())
                                    start = end_hdr + 4
                                    if len(buf) < start + clen:
                                        # Wait for remaining frame packets to arrive
                                        break
                                    jpg = bytes(buf[start:start + clen])
                                    del buf[:start + clen]

                                    if len(jpg) > 2000 and jpg[:2] == b'\xff\xd8' and jpg[-2:] == b'\xff\xd9':
                                        raw = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                                        if raw is not None:
                                            processed = cv2.flip(raw, -1)
                                            with self.lock:
                                                self.frame = processed
                                                self.last_frame_time = time.time()
                                            self.new_frames += 1
                                            count += 1
                                except Exception:
                                    del buf[:end_hdr + 4]
                            else:
                                # Fallback: search for SOI and EOI with boundary \xff\xd9\r\n--
                                a = buf.find(b'\xff\xd8')
                                if a == -1:
                                    if len(buf) > 4:
                                        buf = buf[-4:]
                                    break
                                b = buf.find(b'\xff\xd9\r\n--', a + 2)
                                if b == -1:
                                    # Secondary fallback for VGA (size >= 6000)
                                    b_alt = buf.find(b'\xff\xd9', a + 6000)
                                    if b_alt != -1:
                                        b = b_alt
                                    else:
                                        if a > 0:
                                            del buf[:a]
                                        break

                                jpg = bytes(buf[a:b + 2])
                                del buf[:b + 2]

                                if len(jpg) > 2000 and jpg[:2] == b'\xff\xd8' and jpg[-2:] == b'\xff\xd9':
                                    raw = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                                    if raw is not None:
                                        processed = cv2.flip(raw, -1)
                                        with self.lock:
                                            self.frame = processed
                                            self.last_frame_time = time.time()
                                        self.new_frames += 1
                                        count += 1

                            now = time.time()
                            if now - last_calc >= 0.8:
                                calc_fps = count / (now - last_calc)
                                self.fps = round(calc_fps if self.fps == 0.0 else (0.6 * self.fps + 0.4 * calc_fps), 1)
                                count = 0
                                last_calc = now

            except Exception:
                time.sleep(0.3)

            now = time.time()
            if now - self.last_frame_time > 2.5:
                with self.lock:
                    self.frame = None
                self.fps = 0.0

    def _run_cv_stream(self):
        """Standard OpenCV VideoCapture reader for local USB webcams."""
        try:
            self.cv_stream = cv2.VideoCapture(self.src)
            self.cv_stream.set(cv2.CAP_PROP_BUFFERSIZE, self.buffer_size)
        except Exception:
            pass

        last_calc = time.time()
        count = 0

        while not self.stopped:
            if self.cv_stream is None or not self.cv_stream.isOpened():
                time.sleep(0.5)
                try:
                    self.cv_stream = cv2.VideoCapture(self.src)
                except Exception:
                    pass
                continue

            ret, raw = self.cv_stream.read()
            if ret and raw is not None:
                with self.lock:
                    self.frame = raw
                    self.last_frame_time = time.time()
                self.new_frames += 1
                count += 1
            else:
                time.sleep(0.01)

            now = time.time()
            if now - last_calc >= 1.0:
                self.fps = count / (now - last_calc)
                count = 0
                last_calc = now

            if now - self.last_frame_time > 2.0:
                with self.lock:
                    self.frame = None
                self.fps = 0.0

    def read(self):
        with self.lock:
            return self.frame.copy() if self.frame is not None else None

    def stop(self):
        self.stopped = True
        if self.cv_stream is not None:
            try:
                self.cv_stream.release()
            except Exception:
                pass
