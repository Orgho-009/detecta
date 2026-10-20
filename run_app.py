import os
import sys
import time
import subprocess
import threading
import webview

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
PYTHON_EXE = os.path.join(ROOT_DIR, ".venv", "Scripts", "python.exe")
BACKEND_SCRIPT = os.path.join(ROOT_DIR, "run_dashboard.py")
ICON_PATH = os.path.join(ROOT_DIR, "logo.ico")

backend_proc = None

def is_server_running():
    import urllib.request
    try:
        req = urllib.request.Request("http://127.0.0.1:8000/api/status")
        with urllib.request.urlopen(req, timeout=1.0) as res:
            return res.status == 200
    except Exception:
        return False

def ensure_backend():
    global backend_proc
    if is_server_running():
        return
    
    # Launch backend server hidden in background using virtualenv python
    startupinfo = None
    if sys.platform == "win32":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 0 # SW_HIDE

    backend_proc = subprocess.Popen(
        [PYTHON_EXE, BACKEND_SCRIPT],
        cwd=ROOT_DIR,
        startupinfo=startupinfo,
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    )

    # Wait up to 25s for server to initialize CUDA and models
    for _ in range(50):
        if is_server_running():
            break
        time.sleep(0.5)

def on_closed():
    global backend_proc
    if backend_proc is not None:
        try:
            backend_proc.terminate()
        except Exception:
            pass
    os._exit(0)

def main():
    ensure_backend()
    
    # Create Native Windows Application Window (with custom icon & Chromium WebView2)
    window = webview.create_window(
        title="Detecta — AI Security Intelligence",
        url="http://127.0.0.1:8000",
        width=1340,
        height=860,
        min_size=(960, 600),
        background_color="#060913"
    )
    window.events.closed += on_closed
    
    # Start WebView2 engine with custom window icon
    webview.start(icon=ICON_PATH if os.path.exists(ICON_PATH) else None)

if __name__ == "__main__":
    main()
