#!/usr/bin/env python3
"""Fix remaining XSS vulnerabilities."""
import pathlib

# Fix admin-products.js
p = pathlib.Path("c:/Users/Codewithme/jewelry-gh/frontend/admin-products.js")
text = p.read_text(encoding="utf-8")

# Fix error message XSS
old = "w.innerHTML = '<p style=\"padding:20px;color:red;\">Failed to load: ' + e.message + '</p>'"
new = "w.innerHTML = '<p style=\"padding:20px;color:red;\">Failed to load: ' + Security.escapeHtml(e.message) + '</p>'"
if old in text:
    text = text.replace(old, new)
    print("Fixed admin-products.js error message XSS")
else:
    print("WARNING: admin-products.js error message not found")

p.write_text(text, encoding="utf-8")

# Fix admin-users.js - error message in template literal
p2 = pathlib.Path("c:/Users/Codewithme/jewelry-gh/frontend/admin-users.js")
text2 = p2.read_text(encoding="utf-8")

old2 = 'el.innerHTML = `<p style="padding:20px;color:#c62828;">Failed to load users: ${this.esc(err.message || "Backend not available.")}</p>`;'
new2 = 'el.innerHTML = `<p style="padding:20px;color:#c62828;">Failed to load users: ${window.Security.escapeHtml(err.message || "Backend not available.")}</p>`;'
if old2 in text2:
    text2 = text2.replace(old2, new2)
    print("Fixed admin-users.js error message XSS")
else:
    print("WARNING: admin-users.js error message not found")

p2.write_text(text2, encoding="utf-8")
print("Done")
