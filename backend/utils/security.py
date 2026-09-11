'''
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

# Password Policy (12+ chars, configurable via MIN_PASSWORD_LENGTH env var)
MIN_PASSWORD_LENGTH = int(os.getenv("MIN_PASSWORD_LENGTH", "12"))
MAX_PASSWORD_LENGTH = 128

# HIBP k-anonymity in-process cache
_hibp_cache = {}

# MFA/TOTP
import pyotp


def generate_mfa_secret():
    """Generate a new base32 TOTP secret."""
    return pyotp.random_base32()


def get_totp_uri(secret, email, issuer="AUTUM LUXE"):
    """Return otpauth:// URI for TOTP enrollment."""
    return pyotp.totp.TOTP(secret).provisioning_uri(name=email, issuer_name=issuer)


def verify_totp(secret, token, valid_window=1):
    """Verify a TOTP token. valid_window=1 allows ±30s clock drift."""
    totp = pyotp.TOTP(secret)
    return totp.verify(token, valid_window=valid_window)



def validate_email(email):
    if not email or len(email) > 255:
        return False
    return bool(re.match(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$", email))


def validate_ghana_phone(phone):
    """Accept Ghana phone formats: +233XXXXXXXXX, 0XXXXXXXXX, XXX-XXX-XXXX."""
    if not phone:
        return False
    cleaned = re.sub(r"[\s\-]", "", phone)
    return bool(re.match(r"^(\+233|0)\d{9}$", cleaned))


def normalize_ghana_phone(phone):
    """Normalize to 0XXXXXXXXX (10 digits)."""
    cleaned = re.sub(r"[\s\-]", "", phone)
    if cleaned.startswith("+233"):
        return "0" + cleaned[4:]
    return cleaned


def _check_hibp_k_anonymity(password):
    """Check Have I Been Pwned via k-anonymity (only SHA-1 prefix sent to HIBP)."""
    sha1 = hashlib.sha1(password.encode("utf-8")).hexdigest().upper()
    prefix, suffix = sha1[:5], sha1[5:]
    if prefix in _hibp_cache:
        return suffix in _hibp_cache[prefix]
    try:
        url = f"https://api.pwnedpasswords.com/range/{prefix}"
        req = urllib.request.Request(url, headers={"User-Agent": "AurumGhana-SecurityCheck/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = resp.read().decode("utf-8", errors="ignore")
        _hibp_cache[prefix] = set(line.split(":")[0] for line in data.strip().split("\n") if line)
        return suffix in _hibp_cache[prefix]
    except Exception:
        current_app.logger.warning("HIBP API unavailable; skipping breach check")
        return False


def validate_password_strength(password, check_breach=True, previous_hashes=None):
    """Modern password policy: 12+ chars, 1 letter, 1 number. Optional HIBP + reuse check."""
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
    if check_breach and os.getenv("CHECK_HIBP", "true").lower() not in ("0", "false", "no"):
        if _check_hibp_k_anonymity(password):
            return False, "This password appeared in a known data breach. Please choose a different one."
    if previous_hashes:
        from backend.extensions import bcrypt
        for old_hash in previous_hashes[-5:]:
            if bcrypt.check_password_hash(old_hash, password):
                return False, "You cannot reuse a recently used password."
    return True, ""


def generate_csrf_token():
    return secrets.token_urlsafe(32)


def role_required(*roles):
    """Decorator: require JWT identity + active-user + role check.
    For admin users, also enforces MFA when ADMIN_MFA_REQUIRED is set."""
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
            # Enforce MFA for admin users who have it ENABLED (bootstrap-only:
            # an admin that has never set up MFA is allowed through so they can
            # complete enrollment via /mfa/setup; once mfa_enabled is True the
            # login-time TOTP check is mandatory for every admin request).
            if ("admin" in roles and current_app.config.get("ADMIN_MFA_REQUIRED", True)
                    and user.role == "admin" and user.mfa_enabled):
                from flask_jwt_extended import get_jwt
                jwt_data = get_jwt()
                if not jwt_data.get("mfa_verified"):
                    return jsonify({
                        "detail": "MFA verification required for admin access",
                        "code": "mfa_required",
                        "mfa_required": True
                    }), 403
            request.current_user = user
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def get_request_meta():
    """IP address and User-Agent for audit logging."""
    return {
        "ip": request.headers.get("X-Forwarded-For", request.remote_addr) or "",
        "user_agent": request.headers.get("User-Agent", "")[:500],
    }


# Re-exports for convenience
__all__ = [
    "validate_email", "validate_ghana_phone", "normalize_ghana_phone",
    "validate_password_strength", "generate_csrf_token", "role_required",
    "get_request_meta", "generate_mfa_secret", "get_totp_uri", "verify_totp",
]
