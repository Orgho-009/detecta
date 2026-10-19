import os
import re

source_md = r"c:\Users\rumon\Downloads\DETECTA_ALL_IN_ONE_MASTER_SOURCE.md"
dest_root = r"c:\detecta"

with open(source_md, "r", encoding="utf-8") as f:
    text = f.read()

# Pattern matches:
# ### Source: `path/to/file` ...
# ```lang
# <code>
# ```
pattern = re.compile(r"### Source:\s*`([^`]+)`[^\n]*\r?\n+```[a-zA-Z0-9_\-]*\r?\n(.*?)\r?\n```", re.DOTALL)
matches = pattern.findall(text)

print(f"Total matching source files found: {len(matches)}")
for rel_path, code in matches:
    clean_path = rel_path.strip().replace("/", os.sep)
    full_path = os.path.join(dest_root, clean_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f_out:
        f_out.write(code + "\n")
    print(f"Extracted: {clean_path} ({len(code.splitlines())} lines)")

print("Extraction finished.")
