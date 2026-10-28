import subprocess
import os
import shutil
import tempfile

edge = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
if not os.path.exists(edge):
    edge = r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"

script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(script_dir) if os.path.basename(script_dir) == "scripts" else script_dir
docs_dir = os.path.join(root_dir, "docs")
assets_dir = os.path.join(docs_dir, "assets")

html = os.path.join(assets_dir, "viva_script_compact.html")
if not os.path.exists(html):
    html = os.path.join(root_dir, "viva_script_compact.html")

pdf_dest = os.path.join(docs_dir, "DETECTA_PROJECT_VIVA_AND_DEFENSE_SCRIPT.pdf")
root_pdf_dest = os.path.join(root_dir, "DETECTA_PROJECT_VIVA_AND_DEFENSE_SCRIPT.pdf")
downloads_dest = os.path.expanduser(r"~\Downloads\DETECTA_PROJECT_VIVA_AND_DEFENSE_SCRIPT.pdf")

temp_profile = tempfile.mkdtemp(prefix="detecta_edge_")

cmd = [
    edge,
    "--headless",
    "--disable-gpu",
    f"--user-data-dir={temp_profile}",
    f"--print-to-pdf={pdf_dest}",
    html
]

try:
    res = subprocess.run(cmd, capture_output=True, text=True)
    print("Edge returncode:", res.returncode)
    if os.path.exists(pdf_dest):
        print(f"Compiled PDF size: {os.path.getsize(pdf_dest)} bytes at {pdf_dest}")
        try:
            shutil.copyfile(pdf_dest, root_pdf_dest)
            shutil.copyfile(pdf_dest, downloads_dest)
            print("Copied to Downloads and root successfully!")
        except Exception as e:
            print("Copy note:", e)
finally:
    shutil.rmtree(temp_profile, ignore_errors=True)
