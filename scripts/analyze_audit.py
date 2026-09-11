#!/usr/bin/env python3
"""Check which innerHTML usages actually inject user-controlled data."""
import pathlib, re

base = pathlib.Path("c:/Users/Codewithme/jewelry-gh/frontend")

# Look specifically for innerHTML that uses API response data
files_to_check = [
    "admin-products.js", "admin-orders.js", "admin-users.js",
    "supplier.js", "admin.js"
]

for fname in files_to_check:
    p = base / fname
    if not p.exists():
        continue
    
    text = p.read_text(encoding="utf-8")
    lines = text.split('\n')
    
    print(f"\n=== {fname} ===")
    for i, line in enumerate(lines, 1):
        # Look for innerHTML with template literals or string concatenation
        if 'innerHTML' in line and ('${' in line or ' + ' in line or 'e.message' in line or 'err.message' in line):
            print(f"  Line {i}: {line.strip()[:120]}")
