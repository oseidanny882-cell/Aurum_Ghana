"""
Generator: writes all security-upgrade files.
Usage: python scripts/gen_sec.py
"""
import pathlib
R = pathlib.Path(__file__).parent.parent

def w(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    print(f"  WROTE {path}")

# ─────────────────────────────────────────────────────────────────
# 1. backend/utils/security.py
# ─────────────────────────────────────────────────────────────────
SEC = R / "backend" / "utils" / "security.py"
w(SEC, """'''\nAurum Ghana - Security utilities\n'''\nimport hashlib\nimport os\nimport re\nimport secrets\nimport urllib.request\nfrom functools import wraps\nfrom flask import request, jsonify, current_app\nfrom flask_jwt_extended import verify_jwt_in_request, get_jwt_identity\nfrom backend.models import User\n\n# Password policy\nMIN_PASSWORD_LENGTH = int(os.getenv("MIN_PASSWORD_LENGTH", "12"))\nMAX_PASSWORD_LENGTH = 128\n\n# HIBP k-anonymity in-process cache\n_hibp_cache = {}\n\n\ndef validate_email(email):\n    if not email or len(email) > 255: return False\n    return bool(re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$", email))\n\n\ndef validate_ghana_phone(phone):\n    if not phone: return False\n    cleaned = re.sub(r"[\\s-]", "", phone)\n    return bool(re.match(r"^(\\+233|0)\\d{9}$", cleaned))\n\n\ndef normalize_ghana_phone(phone):\n    cleaned = re.sub(r"[\\s-]", "", phone)\n    if cleaned.startswith("+233"): return "0" + cleaned[4:]\n    return cleaned\n\n\ndef _check_hibp(password):\n    sha1 = hashlib.sha1(password.encode("utf-8")).hexdigest().upper()\n    prefix, suffix = sha1[:5], sha1[5:]\n    if prefix in _hibp_cache:\n        return suffix in _hibp_cache[prefix]\n    try:\n        url = f"https://api.pwnedpasswords.com/range/{prefix}"\n        req = urllib.request.Request(url, headers={"User-Agent": "AurumGhana-SecurityCheck/1.0"})\n        with urllib.request.urlopen(req, timeout=5) as resp:\n            data = resp.read().decode("utf-8", errors="ignore")\n        _hibp_cache[prefix] = set(line.split(":")[0] for line in data.strip().split("\\n") if line)\n        return suffix in _hibp_cache[prefix]\n    except Exception:\n        current_app.logger.warning("HIBP API unavailable; skipping breach check")\n        return False\n\n\ndef validate_password_strength(password, check_breach=True, previous_hashes=None):\n    if not password: return False, "Password is required"\n    if len(password) < MIN_PASSWORD_LENGTH: return False, f"Password must be at least {MIN_PASSWORD_LENGTH} characters"\n    if len(password) > MAX_PASSWORD_LENGTH: return False, "Password too long"\n    if not re.search(r"[A-Za-z]", password): return False, "Password must contain at least one letter"\n    if not re.search(r"\\d", password): return False, "Password must contain at least one number"\n    if check_breach and os.getenv("CHECK_HIBP", "true").lower() not in ("0", "false", "no"):\n        if _check_hibp(password):\n            return False, "This password appeared in a known data breach. Please choose a different one."\n    if previous_hashes:\n        from backend.extensions import bcrypt\n        for old_hash in previous_hashes[-5:]:\n            if bcrypt.check_password_hash(old_hash, password):\n                return False, "You cannot reuse a recently used password."\n    return True, ""\n\n\ndef generate_csrf_token():\n    return secrets.token_urlsafe(32)\n\n\ndef role_required(*roles):\n    def decorator(fn):\n        @wraps(fn)\n        def wrapper(*args, **kwargs):\n            verify_jwt_in_request()\n            user_id = get_jwt_identity()\n            user = User.query.get(user_id)\n            if not user or not user.is_active:\n                return jsonify({"detail": "Unauthorized"}), 401\n            if roles and user.role not in roles:\n                return jsonify({"detail": "Forbidden", "code": "insufficient_role"}), 403\n            request.current_user = user\n            return fn(*args, **kwargs)\n        return wrapper\n    return decorator\n\n\ndef get_request_meta():\n    return {\n        "ip": request.headers.get("X-Forwarded-For", request.remote_addr) or "",\n        "user_agent": request.headers.get("User-Agent", "")[:500],\n    }\n""")

print("Done.")
""",
    insert_line: 1
)

