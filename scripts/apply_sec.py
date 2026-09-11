"""Security upgrade generator. Run: python scripts/apply_sec.py"""
import pathlib, json, base64, textwrap
R = pathlib.Path(__file__).parent.parent

# Each file: relative path -> list of base64-encoded line-group strings
MANIFEST = {}

# Write files
for path_str, groups in MANIFEST.items():
    p = R / path_str
    p.parent.mkdir(parents=True, exist_ok=True)
    raw = b"".join(base64.b64decode(g) for g in groups)
    p.write_bytes(raw)
    print(f"  WROTE {p.relative_to(R)}")
print("All done.")
""",
    insert_line: 1
)

