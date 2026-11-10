# Detecta Documentation and Academic Deliverables

> [!TIP]
> Looking for the standalone executable? You can run or download **[`Detecta.exe`](../Detecta.exe)** directly from the project root for 1-click Windows 10/11 desktop surveillance without setting up Python.

This directory contains the formal academic documentation, lab report, circuit schematics, and presentation defense materials for the **Detecta** Intelligent AI Surveillance Camera system.

---

## Documents Index

| Document | Format | Description |
| :--- | :--- | :--- |
| **[Academic Lab Report (PDF)](DETECTA_SMART_AI_CAMERA_LAB_REPORT.pdf)** | PDF (10 Pages) | Formal IEEE/LaTeX-styled academic lab report covering complete hardware architecture, Port 81 streaming pipeline, multi-modal AI engine (YOLO11s, ArcFace 512-D, MediaPipe), and experimental benchmarks. |
| **[Academic Lab Report (Markdown)](DETECTA_LAB_REPORT.md)** | Markdown | Full GitHub-flavored markdown source of the lab report including comprehensive mathematical formulas and code walkthroughs. |
| **Viva & Defense Quick Guide (PDF)** | PDF (2 Pages) | *(Private / Local Exam Deliverable)* Compact bilingual defense script preserved in local `docs/` for viva preparation. |
| **[Hardware Circuit Diagram](assets/detecta_circuit_diagram.jpg)** | Image (JPG) | High-resolution unified schematic showing 18650 Li-ion battery, IP2312 3A Type-C buck charger, SPST power switch, XL6009 4A boost converter, Pin 4 resistor divider network, and AI-Thinker ESP32-CAM wiring. |

---

## Rebuilding Documentation

All deliverables can be automatically compiled and refreshed using the build scripts located in `scripts/`:

```powershell
# Activate Python environment
.\.venv\Scripts\activate.ps1

# Run the master builder script
python scripts/build_all_docs.py
```

This single command will:
1. Re-render the Markdown lab report.
2. Compile the 10-page LaTeX-style academic PDF (`ReportLab` engine).
3. Generate the bilingual HTML layout and compile the 2-page viva cheat sheet via headless Chromium (`msedge`).
