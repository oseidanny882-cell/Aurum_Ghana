"""
Generator script: writes all upgraded security files.
Run:  python scripts/gen_security.py
"""
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
B = ROOT / "backend"
F = ROOT / "frontend"

def w(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"  WROTE {path.relative_to(ROOT)}")

# ── 1. backend/utils/security.py ──────────────────────────────────────────────
w(B / "utils" / "security.py", R"""'''
Aurum Ghana - Security utilities
'''
import hashlib
import os
import re
import secrets
import urllib.request
from functools import wraps
from flask import request, jsonify, current_app
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from backend.models import User


# ─── Password Policy ────────────────────────────────────────────────────────────

MIN_PASSWORD_LENGTH = int(os.getenv("MIN_PASSWORD_LENGTH", "12"))
MAX_PASSWORD_LENGTH = 128

# HIBP k-anonymity in-process cache  (key = SHA-1 prefix, val = set of suffixes)
_hibp_cache: dict[str, set[str]] = {}


def validate_email(email: str) -> bool:
    if not email or len(email) > 255:
        return False
    pattern = r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def validate_ghana_phone(phone: str) -> bool:
    if not phone:
        return False
    cleaned = re.sub(r"[\s\-]", "", phone)
    pattern = r"^(\+233|0)\d{9}$"
    return bool(re.match(pattern, cleaned))


def normalize_ghana_phone(phone: str) -> str:
    cleaned = re.sub(r"[\s\-]", "", phone)
    if cleaned.startswith("+233"):
        return "0" + cleaned[4:]
    return cleaned


def _check_hibp_k_anonymity(password: str) -> bool:
    sha1 = hashlib.sha1(password.encode("utf-8")).hexdigest().upper()
    prefix, suffix = sha1[:5], sha1[5:]
    if prefix in _hibp_cache:
        return suffix in _hibp_cache[prefix]
    try:
        url = f"https://api.pwnedpasswords.com/range/{prefix}"
        req = urllib.request.Request(
            url, headers={"User-Agent": "AurumGhana-SecurityCheck/1.0"}
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = resp.read().decode("utf-8", errors="ignore")
        suffixes = set(
            line.split(":")[0]
            for line in data.strip().split("\n")
            if line
        )
        _hibp_cache[prefix] = suffixes
        return suffix in suffixes
    except Exception:
        current_app.logger.warning("HIBP API unavailable; skipping breach check")
        return False


def validate_password_strength(
    password: str,
    check_breach: bool = True,
    previous_hashes: list[str] | None = None,
) -> tuple[bool, str]:
    if not password:
        return False, "Password is required"
    if len(password) < MIN_PASSWORD_LENGTH:
        return False, f"Password must be at least {MIN_PASSWORD_LENGTH} characters"
    if len(password) > MAX_PASSWORD_LENGTH:
        return False, "Password too long"
    if not re.search(r"[A-Za-z]", password):
        return False, "Password must contain at least one letter"
    if not re.search(r"\d", password):
        return False, "Password must contain at least one number"
    if (
        check_breach
        and os.getenv("CHECK_HIBP", "true").lower() not in ("0", "false", "no")
    ):
        if _check_hibp_k_anonymity(password):
            return False, (
                "This password appeared in a known data breach. "
                "Please choose a different one."
            )
    if previous_hashes:
        from backend.extensions import bcrypt
        for old_hash in previous_hashes[-5:]:
            if bcrypt.check_password_hash(old_hash, password):
                return False, "You cannot reuse a recently used password."
    return True, ""


def generate_csrf_token() -> str:
    return secrets.token_urlsafe(32)


def role_required(*roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            user_id = get_jwt_identity()
            user = User.query.get(user_id)
            if not user or not user.is_active:
                return jsonify({"detail": "Unauthorized"}), 401
            if roles and user.role not in roles:
                return jsonify({"detail": "Forbidden", "code": "insufficient_role"}), 403
            request.current_user = user
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def get_request_meta() -> dict:
    return {
        "ip": request.headers.get("X-Forwarded-For", request.remote_addr) or "",
        "user_agent": request.headers.get("User-Agent", "")[:500],
    }
""")

print("Done.")
""",
    insert_line: 1
)

