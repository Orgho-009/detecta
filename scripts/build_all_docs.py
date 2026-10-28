"""
Detecta Master Documentation & Deliverable Builder
Compiles:
1. DETECTA_LAB_REPORT.md (Markdown Academic Report)
2. DETECTA_SMART_AI_CAMERA_LAB_REPORT.pdf (10-Page LaTeX Styled Academic PDF)
3. viva_script_compact.html & DETECTA_PROJECT_VIVA_AND_DEFENSE_SCRIPT.pdf (2-Page Bilingual Defense Sheet)
"""
import os
import sys
import subprocess

def main():
    scripts_dir = os.path.dirname(os.path.abspath(__file__))
    python_exe = sys.executable

    print("=" * 60)
    print(" DETECTA — COMPILING ALL ACADEMIC REPORTS & DEFENSE GUIDES")
    print("=" * 60)

    print("\n[1/3] Generating Academic Lab Report Markdown...")
    subprocess.run([python_exe, os.path.join(scripts_dir, "build_latex_style_markdown.py")], check=True)

    print("\n[2/3] Compiling 10-Page LaTeX-Style Lab Report PDF...")
    subprocess.run([python_exe, os.path.join(scripts_dir, "generate_latex_style_pdf.py")], check=True)

    print("\n[3/3] Generating and Compiling Viva Defense Sheet PDF...")
    subprocess.run([python_exe, os.path.join(scripts_dir, "generate_compact_viva_html.py")], check=True)
    subprocess.run([python_exe, os.path.join(scripts_dir, "compile_compact_pdf.py")], check=True)

    print("\n" + "=" * 60)
    print(" [ALL DELIVERABLES READY IN docs/ AND ROOT]")
    print("=" * 60)

if __name__ == "__main__":
    main()
