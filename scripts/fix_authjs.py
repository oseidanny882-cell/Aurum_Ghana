"""Fix auth-forms.js password length check + reset-password.html placeholder."""
import pathlib

# Fix auth-forms.js
f = pathlib.Path(r"c:\Users\Codewithme\jewelry-gh\frontend\auth-forms.js")
js = f.read_text(encoding="utf-8")
n1 = js.count("if (raw.password.length < 8)")
js = js.replace("if (raw.password.length < 8)", "if (raw.password.length < 12)")
n2 = js.count("'Password must be at least 8 characters.'")
js = js.replace("'Password must be at least 8 characters.'", "'Password must be at least 12 characters.'")
f.write_text(js, encoding="utf-8")
print(f"auth-forms.js: {n1} length checks, {n2} error messages updated.")

# Fix reset-password.html placeholder
f2 = pathlib.Path(r"c:\Users\Codewithme\jewelry-gh\frontend\reset-password.html")
reg = f2.read_text(encoding="utf-8")
n3 = reg.count('placeholder="Min. 8 characters"')
reg = reg.replace('placeholder="Min. 8 characters"', 'placeholder="Min. 12 characters"')
f2.write_text(reg, encoding="utf-8")
print(f"reset-password.html: {n3} placeholder(s) updated.")
print("Done.")

"""Fix auth-forms.js password length check."""
import pathlib
f = pathlib.Path(r"c:\Users\Codewithme\jewelry-gh\frontend\auth-forms.js")
js = f.read_text(encoding="utf-8")
count = 0
count += js.count("if (raw.password.length < 8)")
js = js.replace("if (raw.password.length < 8)", "if (raw.password.length < 12)")
count2 = js.count("'Password must be at least 8 characters.'")
js = js.replace("'Password must be at least 8 characters.'", "'Password must be at least 12 characters.'")
f.write_text(js, encoding="utf-8")
print(f"Fixed {count} length checks and {count2} error messages in auth-forms.js")
