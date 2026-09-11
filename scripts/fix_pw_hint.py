"""Fix stale password hint + JS check in account.html."""
import pathlib
f = pathlib.Path(r"c:\Users\Codewithme\jewelry-gh\frontend\account.html")
html = f.read_text(encoding="utf-8")

# Fix 1: update the hint text (line 92 area)
old_hint = '<p class="form-hint">Minimum 8 characters. Include uppercase, lowercase, number, and special character.</p>'
new_hint = '<p class="form-hint">Minimum 12 characters. Include at least one letter and one number.</p>'
if old_hint in html:
    html = html.replace(old_hint, new_hint, 1)
    print("Fixed hint text in account.html.")
else:
    print("Hint text not found (may already be fixed or different).")

# Fix 2: update the JS length check (8 -> 12)
old_js = "if (npw.length < 8) { al.textContent = 'New password must be at least 8 characters.'"
new_js = "if (npw.length < 12) { al.textContent = 'New password must be at least 12 characters.'"
if old_js in html:
    html = html.replace(old_js, new_js, 1)
    print("Fixed JS length check in account.html.")
else:
    print("JS length check not found.")

f.write_text(html, encoding="utf-8")
print("Saved account.html")

# Fix 3: auth-forms.js registration password validation
f2 = pathlib.Path(r"c:\Users\Codewithme\jewelry-gh\frontend\auth-forms.js")
js = f2.read_text(encoding="utf-8")
old_auth = "if (raw.password.length < 8) {\n\n                if (alertEl) { alertEl.textContent = 'Password must be at least 8 characters.'; alertEl.className = 'alert alert-error'; alertEl.classList.add('show'); }"
new_auth = "if (raw.password.length < 12) {\n\n                if (alertEl) { alertEl.textContent = 'Password must be at least 12 characters.'; alertEl.className = 'alert alert-error'; alertEl.classList.add('show'); }"
if old_auth in js:
    js = js.replace(old_auth, new_auth, 1)
    print("Fixed length check in auth-forms.js.")
else:
    print("auth-forms.js length check not found.")
f2.write_text(js, encoding="utf-8")
print("Saved auth-forms.js")

# Fix 4: register.html hint + placeholder
f3 = pathlib.Path(r"c:\Users\Codewithme\jewelry-gh\frontend\register.html")
reg = f3.read_text(encoding="utf-8")
old_hint2 = '<p class="form-hint">At least 8 characters with uppercase, lowercase, number, and special character.</p>'
new_hint2 = '<p class="form-hint">At least 12 characters with at least one letter and one number.</p>'
if old_hint2 in reg:
    reg = reg.replace(old_hint2, new_hint2, 1)
    print("Fixed hint text in register.html.")
else:
    print("register.html hint not found.")
old_ph = 'placeholder="Min. 8 characters"'
new_ph = 'placeholder="Min. 12 characters"'
if old_ph in reg:
    reg = reg.replace(old_ph, new_ph, 1)
    print("Fixed placeholder in register.html.")
else:
    print("register.html placeholder not found.")
f3.write_text(reg, encoding="utf-8")
print("Saved register.html")
print("All done.")

"""Fix stale password hint + JS check in account.html."""
import pathlib
f = pathlib.Path(r"c:\Users\Codewithme\jewelry-gh\frontend\account.html")
html = f.read_text(encoding="utf-8")

# Fix 1: update the hint text (line 92 area)
old_hint = '<p class="form-hint">Minimum 8 characters. Include uppercase, lowercase, number, and special character.</p>'
new_hint = '<p class="form-hint">Minimum 12 characters. Include at least one letter and one number.</p>'
if old_hint in html:
    html = html.replace(old_hint, new_hint, 1)
    print("Fixed hint text.")
else:
    print("Hint text not found (may already be fixed or different).")

# Fix 2: update the JS length check (8 -> 12)
old_js = "if (npw.length < 8) { al.textContent = 'New password must be at least 8 characters.'"
new_js = "if (npw.length < 12) { al.textContent = 'New password must be at least 12 characters.'"
if old_js in html:
    html = html.replace(old_js, new_js, 1)
    print("Fixed JS length check.")
else:
    print("JS length check not found.")

f.write_text(html, encoding="utf-8")
print("Saved account.html")
