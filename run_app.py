import os
import sys
import time
import subprocess
import threading
import shutil
import webview

def show_native_message(title, message):
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, message, title, 0x10)  # 0x10 = MB_ICONERROR
    except Exception:
        print(f"[{title}] {message}")

def ask_yes_no(title, message):
    try:
        import ctypes
        # 0x04 = MB_YESNO, 0x20 = MB_ICONQUESTION, 0x1000 = MB_SYSTEMMODAL
        res = ctypes.windll.user32.MessageBoxW(0, message, title, 0x04 | 0x20 | 0x1000)
        return res == 6  # IDYES = 6
    except Exception:
        return False

def auto_setup_environment():
    setup_bat = os.path.join(ROOT_DIR, "Setup.bat")
    if not os.path.exists(setup_bat):
        show_native_message(
            "Detecta Setup",
            f"Setup.bat not found at:\n{setup_bat}\nPlease ensure all project files are present."
        )
        return False

    choice = ask_yes_no(
        "Detecta — Automatic Environment Setup",
        "The Python AI environment (.venv) is not yet configured on this PC.\n\n"
        "Would you like Detecta to automatically configure the environment and install all dependencies now?\n\n"
        "Click 'Yes' to start automatic 1-click setup."
    )
    if not choice:
        return False

    # Launch Setup.bat in a visible console window so the user sees progress
    ret = subprocess.call(["cmd.exe", "/c", setup_bat], cwd=ROOT_DIR)
    return ret == 0

def get_base_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))

BASE_DIR = get_base_dir()

# Locate project directory where run_dashboard.py exists
candidates = [
    BASE_DIR,
    r"c:\detecta",
    os.path.abspath(os.path.join(BASE_DIR, "..")),
    os.getcwd()
]

ROOT_DIR = BASE_DIR
for c in candidates:
    if c and os.path.exists(os.path.join(c, "run_dashboard.py")):
        ROOT_DIR = c
        break

# Find Python executable
PYTHON_EXE = None
py_candidates = [
    os.path.join(ROOT_DIR, ".venv", "Scripts", "python.exe"),
    r"c:\detecta\.venv\Scripts\python.exe",
    os.path.join(BASE_DIR, ".venv", "Scripts", "python.exe"),
    sys.executable if not getattr(sys, "frozen", False) else None
]

for p in py_candidates:
    if p and os.path.exists(p):
        PYTHON_EXE = p
        break

if not PYTHON_EXE:
    system_py = shutil.which("python")
    if system_py and os.path.exists(system_py):
        PYTHON_EXE = system_py

BACKEND_SCRIPT = os.path.join(ROOT_DIR, "run_dashboard.py")
ICON_PATH = os.path.join(ROOT_DIR, "logo.ico")
if not os.path.exists(ICON_PATH):
    ICON_PATH = os.path.join(BASE_DIR, "logo.ico")

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
    global backend_proc, PYTHON_EXE
    if is_server_running():
        return True

    if not PYTHON_EXE or not os.path.exists(PYTHON_EXE):
        if auto_setup_environment():
            candidate_venv_py = os.path.join(ROOT_DIR, ".venv", "Scripts", "python.exe")
            if os.path.exists(candidate_venv_py):
                PYTHON_EXE = candidate_venv_py

        if not PYTHON_EXE or not os.path.exists(PYTHON_EXE):
            show_native_message(
                "Detecta - Setup Incomplete",
                "Python environment setup was cancelled or failed.\n\n"
                f"Searched in: {os.path.join(ROOT_DIR, '.venv')}\n"
                "Please run Setup.bat manually."
            )
            return False

    if not os.path.exists(BACKEND_SCRIPT):
        show_native_message(
            "Detecta - Backend Script Missing",
            f"Could not find run_dashboard.py at:\n{BACKEND_SCRIPT}\n\n"
            f"Please ensure Detecta.exe is placed in the Detecta project directory."
        )
        return False

    startupinfo = None
    if sys.platform == "win32":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 0  # SW_HIDE

    env = os.environ.copy()
    env["DETECTA_DESKTOP"] = "1"

    try:
        backend_proc = subprocess.Popen(
            [PYTHON_EXE, BACKEND_SCRIPT, "--no-browser"],
            cwd=ROOT_DIR,
            env=env,
            startupinfo=startupinfo,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        )
    except Exception as e:
        show_native_message("Detecta Startup Error", f"Failed to start backend server:\n{e}")
        return False

    # Wait up to 30s for server to initialize CUDA and models
    for _ in range(60):
        if is_server_running():
            return True
        time.sleep(0.5)

    return is_server_running()

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

    window = webview.create_window(
        title="Detecta — AI Security Intelligence",
        url="http://127.0.0.1:8000",
        width=1340,
        height=860,
        min_size=(960, 600),
        background_color="#060913"
    )
    window.events.closed += on_closed

    webview.start(icon=ICON_PATH if os.path.exists(ICON_PATH) else None)

if __name__ == "__main__":
    main()
