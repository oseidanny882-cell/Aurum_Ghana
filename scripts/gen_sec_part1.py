"""
Part 1 of security generator.
"""
import pathlib, base64
R = pathlib.Path(__file__).parent.parent
def w(path, lines):
    p = R / path
    p.parent.mkdir(parents=True, exist_ok=True)
    content = "\n".join(lines) + "\n"
    p.write_text(content, encoding="utf-8")
    print(f"  WROTE {p.relative_to(R)}")

# backend/utils/security.py
w("backend/utils/security.py", [
    "'''",
    "Aurum Ghana - Security utilities",
    "'''",
    "import hashlib, os, re, secrets, urllib.request",
    "from functools import wraps",
    "from flask import request, jsonify, current_app",
    "from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity",
    "from backend.models import User",
    "",
    "# Password policy: 12+ chars minimum",
    'MIN_PASSWORD_LENGTH = int(os.getenv("MIN_PASSWORD_LENGTH", "12"))',
    "MAX_PASSWORD_LENGTH = 128",
    "",
    "# HIBP k-anonymity in-process cache (key=SHA1-prefix, val=set of suffixes)",
    "_hibp_cache = {}",
    "",
    "",
    "def validate_email(email):",
    "    if not email or len(email) > 255: return False",
    '    return bool(re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$", email))',
    "",
    "",
    "def validate_ghana_phone(phone):",
    "    if not phone: return False",
    '    cleaned = re.sub(r"[\\s-]", "", phone)',
    '    return bool(re.match(r"^(\\+233|0)\\d{9}$", cleaned))',
    "",
    "",
    "def normalize_ghana_phone(phone):",
    '    cleaned = re.sub(r"[\\s-]", "", phone)',
    '    if cleaned.startswith("+233"): return "0" + cleaned[4:]',
    "    return cleaned",
    "",
    "",
    "def _check_hibp(password):",
    '    sha1 = hashlib.sha1(password.encode("utf-8")).hexdigest().upper()',
    "    prefix, suffix = sha1[:5], sha1[5:]",
    "    if prefix in _hibp_cache:",
    "        return suffix in _hibp_cache[prefix]",
    "    try:",
    '        url = f"https://api.pwnedpasswords.com/range/{prefix}"',
    '        req = urllib.request.Request(url, headers={"User-Agent": "AurumGhana-SecurityCheck/1.0"})',
    "        with urllib.request.urlopen(req, timeout=5) as resp:",
    '            data = resp.read().decode("utf-8", errors="ignore")',
    '        _hibp_cache[prefix] = set(line.split(":")[0] for line in data.strip().split("\\n") if line)',
    "        return suffix in _hibp_cache[prefix]",
    "    except Exception:",
    '        current_app.logger.warning("HIBP API unavailable; skipping breach check")',
    "        return False",
])

print("Part 1 done.")
""",
    insert_line: 1
)

