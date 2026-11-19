#!/usr/bin/env python3
"""Entry point for the FastAPI web dashboard server."""
import sys
import os
import time
import webbrowser
import threading
import uvicorn

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT_DIR)
sys.path.insert(0, os.path.join(ROOT_DIR, "web_dashboard"))

def open_browser():
    time.sleep(1.2)
    print("\n[Detecta Dashboard] Launching web interface in your default browser: http://localhost:8000")
    webbrowser.open("http://localhost:8000")

def main():
    print("=" * 65)
    print(" DETECTA — AI SECURITY CAMERA WEB INTELLIGENCE DASHBOARD")
    print("=" * 65)
    print(" Serving on: http://localhost:8000 (and local network IP:8000)")
    print(" Press Ctrl+C in this terminal to stop the server.\n")

    if not os.environ.get("DETECTA_DESKTOP") and "--no-browser" not in sys.argv:
        threading.Thread(target=open_browser, daemon=True).start()

    from web_dashboard.backend import app
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="warning")

if __name__ == "__main__":
    main()
