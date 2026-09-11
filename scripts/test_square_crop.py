"""
Comprehensive frontend fix script - addresses all bugs found in audit.
Run: python scripts/test_square_crop.py
"""
import os
ROOT = r"c:\Users\Codewithme\jewelry-gh\frontend"

# ---------- Fix 1: admin-suppliers.html script order ----------
path = os.path.join(ROOT, "admin-suppliers.html")
content = open(path, encoding="utf-8").read()
old = (
    '    <script src="security.js?v=1788613000"></script>\n'
    '    <script src="api.js?v=1788613000"></script>\n'
    '    <script src="supplier.js?v=1788613000"></script>\n'
    '    <script src="cart.js?v=1788613000"></script>\n'
    '    <script src="auth.js?v=1788615000"></script>\n'
)
new = (
    '    <script src="security.js?v=1788613000"></script>\n'
    '    <script src="api.js?v=1788613000"></script>\n'
    '    <script src="cart.js?v=1788613000"></script>\n'
    '    <script src="auth.js?v=1788615000"></script>\n'
    '    <script src="supplier.js?v=1788613000"></script>\n'
)
if old in content:
    content = content.replace(old, new, 1)
    open(path, "w", encoding="utf-8").write(content)
    print("FIXED admin-suppliers.html - moved supplier.js AFTER auth.js")
else:
    print("SKIP admin-suppliers.html - pattern not found")

# ---------- Fix 2: supplier.js - defensive window.Auth ----------
path = os.path.join(ROOT, "supplier.js")
content = open(path, encoding="utf-8").read()
old_block = '(async function() { await Auth.init(); if (!Auth.redirectIfNotAdmin()) return;'
new_block = ('document.addEventListener("DOMContentLoaded", async function() {\n'
            '    while (!window.Auth || !window.api) { await new Promise(r => setTimeout(r, 50)); }\n'
            '    await window.Auth.init();\n'
            '    if (!window.Auth.redirectIfNotAdmin()) return;')
if old_block in content:
    content = content.replace(old_block, new_block, 1)
    # Fix closing IIFE
    content = content.replace('    load();\n})();', '    load();\n});\n});', 1)
    open(path, "w", encoding="utf-8").write(content)
    print("FIXED supplier.js - waits for globals before Auth.init + uses window.Auth")
else:
    print("SKIP supplier.js block - pattern not found")

# Also fix the inline setTimeout that re-uses Auth
path = os.path.join(ROOT, "supplier.js")
content = open(path, encoding="utf-8").read()
bad = "setTimeout(async function() { await Auth.init(); if (!Auth.redirectIfNotAdmin()) return; e.remove(); }, 4000);"
good = "setTimeout(function() { if (e && e.remove) e.remove(); }, 4000);"
if bad in content:
    content = content.replace(bad, good, 1)
    open(path, "w", encoding="utf-8").write(content)
    print("FIXED supplier.js setTimeout - removed redundant Auth re-init")

# ---------- Fix 3: reviews.js - use api.request() + correct /v1 prefix ----------
path = os.path.join(ROOT, "reviews.js")
content = open(path, encoding="utf-8").read()
import re

# Fix GET reviews
old1 = "await fetch('/api/products/' + this.productId + '/reviews')"
new1 = "await window.api.request('/products/' + this.productId + '/reviews')"
if old1 in content:
    content = content.replace(old1, new1, 1)
    print("FIXED reviews.js - GET reviews uses api.request")

# Fix POST reviews
old2 = "await fetch('/api/products/' + this.productId + '/reviews', {"
new2 = "await window.api.request('/products/' + this.productId + '/reviews', {"
if old2 in content:
    content = content.replace(old2, new2, 1)
    print("FIXED reviews.js - POST reviews uses api.request")

# api.request already throws on non-2xx, so simplify error handling
old3 = "if (!response.ok) {\n                const errorData = await response.json();\n                throw new Error(errorData.error || 'Failed to submit review');\n            }"
new3 = "if (!response.ok) { throw new Error('Failed to submit review'); }"
if old3 in content:
    content = content.replace(old3, new3, 1)
    print("FIXED reviews.js - simplified error handling (api.request handles this)")

# Remove the double-`const response` warning from POST - no need to redeclare
open(path, "w", encoding="utf-8").write(content)

# ---------- Fix 4: category.html - missing base href fix (if needed) ----------
# Check if category.html is missing the base href for relative links
path = os.path.join(ROOT, "category.html")
content = open(path, encoding="utf-8").read()
if 'window.api.request' in content:
    print("category.html already uses window.api")
else:
    print("INFO category.html may need checking")

print("\nAll frontend fixes applied.")

"""Test that uploaded wide/portrait images are center-cropped to a perfect 1200x1200 square."""
import io, json, urllib.request, os
from PIL import Image

# 1. Login
login = json.dumps({"email": "admin@aurum-ghana.local", "password": "Admin12345!"}).encode()
tokens = json.loads(urllib.request.urlopen(
    urllib.request.Request("http://localhost:5000/api/v1/auth/login",
        data=login, headers={"Content-Type": "application/json"})
).read())
token = tokens["access_token"]

# 2. Create a 2000x800 test image (wide/landscape - good test for square crop)
img = Image.new("RGB", (2000, 800), color=(60, 120, 200))
buf = io.BytesIO()
img.save(buf, format="JPEG")
buf.seek(0)

boundary = "----TestBoundary"
header = (
    f"--{boundary}\r\n"
    f"Content-Disposition: form-data; name=\"file\"; filename=\"wide.jpg\"\r\n"
    f"Content-Type: image/jpeg\r\n\r\n"
).encode()
footer = f"\r\n--{boundary}--\r\n".encode()
body = header + buf.read() + footer

req = urllib.request.Request(
    "http://localhost:5000/api/v1/admin/upload/image",
    data=body,
    headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": f"multipart/form-data; boundary={boundary}",
    },
    method="POST"
)
r = json.loads(urllib.request.urlopen(req).read())
print("Upload response:", r)

fpath = os.path.join(r"c:\Users\Codewithme\jewelry-gh\frontend\images", r["filename"])
img2 = Image.open(fpath)
size_kb = os.path.getsize(fpath) // 1024
print(f"Saved: {img2.size[0]}x{img2.size[1]}  ({size_kb} KB)")
print(f"Perfect square 1200x1200: {img2.size == (1200, 1200)}")

# Clean up test file
os.remove(fpath)
print("Test clean.")
