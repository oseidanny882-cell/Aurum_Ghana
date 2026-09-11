"""
Aurum Ghana - MFA API (TOTP)
POST /mfa/setup    - Generate TOTP secret + otpauth URL
POST /mfa/verify   - Verify code, enable MFA
POST /mfa/disable  - Disable MFA with code
"""
import secrets
import hmac
import hashlib
import base64
import time

try:
    import pyotp as _pyotp
    HAS_PYOTP = True
except ImportError:
    _pyotp = None
    HAS_PYOTP = False

from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.api import api_bp
from backend.extensions import db
from backend.models import User
from backend.services.audit import log_audit
from backend.utils.security import get_request_meta


@api_bp.route("/mfa/setup", methods=["POST"])
@jwt_required()
def mfa_setup():
    if not HAS_PYOTP:
        return jsonify({"detail": "MFA not available", "code": "mfa_unavailable"}), 501
    user = User.query.get(get_jwt_identity())
    if not user:
        return jsonify({"detail": "User not found", "code": "not_found"}), 404
    secret = _pyotp.random_base32()
    user.mfa_secret = secret
    db.session.commit()
    otpauth_url = _pyotp.TOTP(secret).provisioning_uri(
        name=user.email, issuer_name="AUTUM LUXE"
    )
    return jsonify({"secret": secret, "otpauth_url": otpauth_url}), 200


@api_bp.route("/mfa/verify", methods=["POST"])
@jwt_required()
def mfa_verify():
    if not HAS_PYOTP:
        return jsonify({"detail": "MFA not available", "code": "mfa_unavailable"}), 501
    user = User.query.get(get_jwt_identity())
    if not user or not user.mfa_secret:
        return jsonify({"detail": "MFA not set up", "code": "mfa_not_setup"}), 400
    data = request.get_json(silent=True) or {}
    code = (data.get("code") or "").strip()
    if not _pyotp.TOTP(user.mfa_secret).verify(code, valid_window=1):
        return jsonify({"detail": "Invalid code", "code": "invalid_code"}), 401
    user.mfa_enabled = True
    db.session.commit()
    log_audit(user_id=user.id, action="user.mfa_enabled", resource_type="user",
              details="mfa_enabled", meta=get_request_meta())
    return jsonify({"message": "MFA enabled"}), 200


@api_bp.route("/mfa/disable", methods=["POST"])
@jwt_required()
def mfa_disable():
    if not HAS_PYOTP:
        return jsonify({"detail": "MFA not available", "code": "mfa_unavailable"}), 501
    user = User.query.get(get_jwt_identity())
    if not user or not user.mfa_enabled:
        return jsonify({"detail": "MFA not enabled", "code": "not_enabled"}), 400
    data = request.get_json(silent=True) or {}
    code = (data.get("code") or "").strip()
    if user.mfa_secret and not _pyotp.TOTP(user.mfa_secret).verify(code, valid_window=1):
        return jsonify({"detail": "Invalid code", "code": "invalid_code"}), 401
    user.mfa_enabled = False
    user.mfa_secret = None
    db.session.commit()
    log_audit(user_id=user.id, action="user.mfa_disabled", resource_type="user",
              details="mfa_disabled", meta=get_request_meta())
    return jsonify({"message": "MFA disabled"}), 200
