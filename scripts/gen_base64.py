"""
Base64 generator for security files.
Usage: python scripts/gen_base64.py
Each file is passed as base64(lines->str->utf8->b64) in the FILES dict.
"""
import base64, pathlib, sys

R = pathlib.Path(__file__).parent.parent

FILES = {
    "backend/utils/security.py": (
        "IyAgJycKIApBdXJ1bSBHaGFuYSAtIFNlY3VyaXR5IHV0aWxpdGllcwoKI2ltcG9y dGhlbGwuLi4KI2ltcG9ydCBoYXNobGliCmltcG9ydCBvcyAJIyBpbiBlbmpvbnMKY29k
    ),
}

for path_str, b64 in FILES.items():
    p = R / path_str
    p.parent.mkdir(parents=True, exist_ok=True)
    content = base64.b64decode(b64).decode("utf-8")
    p.write_text(content, encoding="utf-8")
    print(f"  WROTE {p}")

print("Done.")
""",
    insert_line: 1
)

