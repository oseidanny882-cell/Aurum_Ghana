"""
Aurum Ghana - Auth API routes
"""
from datetime import datetime, timezone
from flask import current_app, request, jsonify
from flask_jwt_extended import (
    create_access_token, create_refresh_token, get_jwt_identity,
    jwt_required, set_access_cookies, set_refresh_cookies, unset_jwt_cookies,
    get_csrf_token
)
import os
import secrets
from backend.api import api_bp
from backend.extensions import db, limiter
from backend.models import User, VerificationToken
from backend.utils.security import (
    validate_email,
    validate_ghana_phone,
    validate_password_strength,
    normalize_ghana_phone,
    get_request_meta,
    verify_totp,
)
from backend.services.email import send_email
from backend.services.audit import log_audit


def _build_tokens(user_id: str, mfa_verified=False) -> dict:
    """Build JWT tokens. Admin tokens include mfa_verified claim."""
    from flask_jwt_extended import create_access_token, create_refresh_token
    access_token = create_access_token(
        identity=user_id,
        additional_claims={"mfa_verified": mfa_verified}
    )
    refresh_token = create_refresh_token(identity=user_id)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
    }


@api_bp.route("/auth/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    first_name = (data.get("first_name") or "").strip()
    last_name = (data.get("last_name") or "").strip()
    phone = (data.get("phone") or "").strip()

    if not validate_email(email):
        return jsonify({"detail": "Valid email required", "code": "invalid_email"}), 400
    ok, msg = validate_password_strength(password)
    if not ok:
        return jsonify({"detail": msg, "code": "weak_password"}), 400
    if not first_name or not last_name:
        return jsonify({"detail": "First and last name required", "code": "missing_name"}), 400
    if phone and not validate_ghana_phone(phone):
        return jsonify({"detail": "Invalid Ghana phone number", "code": "invalid_phone"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"detail": "Email already registered", "code": "email_exists"}), 409

    from backend.extensions import bcrypt
    pw_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    user = User(
        email=email, password_hash=pw_hash,
        first_name=first_name, last_name=last_name,
        phone=normalize_ghana_phone(phone) if phone else None,
        is_verified=False,
    )
    db.session.add(user)
    db.session.flush()

    vtoken = VerificationToken.generate_token("email_verification", user.id, ttl_hours=48)
    db.session.add(vtoken)
    db.session.commit()

    frontend_url = current_app.config.get("FRONTEND_URL", "https://oseidanny882-cell.github.io/Aurum_Ghana").rstrip("/")
    verify_url = f"{frontend_url}/verify-email.html?token={vtoken.token}"
    sent = send_email(to=email, subject="Verify your AUTUM LUXE account",
                      body=f"Click to verify: {verify_url}")

    if not sent:
        return jsonify({
            "detail": "Failed to send verification email. Please try again.",
            "code": "email_failed"
        }), 503

    log_audit(user_id=user.id, action="user.registered", resource_type="user",
              details=f"email={email}", meta=get_request_meta())
    return jsonify({"message": "Registration successful. Please check your email to verify your account."}), 201


_LOGIN_LIMIT  = os.getenv("RATE_LIMIT_AUTH",  "10 per 5 minutes")
_FORGOT_LIMIT = os.getenv("RATE_LIMIT_FORGOT", "10 per 5 minutes")

# Per-account lockout (brute-force protection beyond IP rate limiting)
_MAX_FAILED_ATTEMPTS = 5
_LOCKOUT_DURATION_MINUTES = 15


@api_bp.route("/auth/login", methods=["POST"])
@limiter.limit(_LOGIN_LIMIT)
def login():
    """Authenticate user with rate limiting, account lockout, and audit logging."""
    now = datetime.now(timezone.utc)
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"detail": "Email and password required", "code": "missing_credentials"}), 400

    user = User.query.filter_by(email=email).first()

    # Check per-account lockout BEFORE revealing whether the account exists
    if user and user.locked_until and user.locked_until > now:
        remaining = int((user.locked_until - now).total_seconds() // 60) + 1
        return jsonify({
            "detail": f"Account temporarily locked due to too many failed attempts. Try again in {remaining} minute(s).",
            "code": "account_locked",
        }), 429

    from backend.extensions import bcrypt
    if not user:
        # Constant-time dummy hash: prevents timing attacks that detect valid emails
        bcrypt.check_password_hash(
            "$2b$12$CwTycUXWue0Thq9StjUM0uJ8.6G2KGFhZpQ1uMqQrn8uWSbW9xYHm", password)
        return jsonify({"detail": "Invalid credentials", "code": "invalid_credentials"}), 401

    if not bcrypt.check_password_hash(user.password_hash, password):
        user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
        if user.failed_login_attempts >= _MAX_FAILED_ATTEMPTS:
            from datetime import timedelta
            user.locked_until = now + timedelta(minutes=_LOCKOUT_DURATION_MINUTES)
            log_audit(user_id=user.id, action="user.account_locked", resource_type="user",
                      details=f"locked_after_{user.failed_login_attempts}_attempts",
                      meta=get_request_meta())
        db.session.commit()
        return jsonify({"detail": "Invalid credentials", "code": "invalid_credentials"}), 401

    if not user.is_active:
        return jsonify({"detail": "Account is disabled", "code": "account_disabled"}), 403

    # Success: reset failed attempts counter and update last login
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login = now

    # Admin second factor: EMAIL OTP. A random 6-digit code is generated,
    # stored server-side with a 5-minute expiry, and emailed to the admin.
    # No tokens are issued until the code is verified via /auth/mfa-email-verify.
    admin_otp_required = (
        user.role in ("admin", "super_admin")
        and current_app.config.get("ADMIN_MFA_REQUIRED", True)
    )
    if admin_otp_required:
        code = f"{secrets.randbelow(1000000):06d}"
        from datetime import timedelta
        user.email_otp_code = code
        user.email_otp_expires_at = now + timedelta(minutes=10)
        db.session.commit()

        sent = send_email(
            to=user.email,
            subject="Your AUTUM LUXE admin login code",
            body=(
                f"Hello {user.first_name},\n\n"
                f"Your admin login verification code is: {code}\n\n"
                f"This code expires in 10 minutes.\n"
                f"If you did not attempt to log in, someone knows your "
                f"password - please change it immediately."
            ),
        )
        if not sent:
            user.email_otp_code = None
            user.email_otp_expires_at = None
            db.session.commit()
            log_audit(user_id=user.id, action="user.login_otp_failed",
                      resource_type="user", details="email_otp_send_failed",
                      meta=get_request_meta())
            return jsonify({
                "detail": "Failed to send the verification code email. Please try again.",
                "code": "email_failed",
            }), 503

        log_audit(user_id=user.id, action="user.login_otp_sent", resource_type="user",
                  details="email_otp_sent", meta=get_request_meta())
        csrf_token = get_csrf_token(
            create_access_token(identity=user.id, additional_claims={"mfa_verified": False})
        )
        return jsonify({
            "mfa_required": True,
            "mfa_method": "email",
            "message": "A 6-digit code has been sent to your email address.",
            "user": user.to_dict(),
            "csrf_token": csrf_token,
        }), 200

    # Non-admin (or MFA disabled) login: issue tokens directly.
    db.session.commit()
    tokens = _build_tokens(user.id, mfa_verified=False)
    log_audit(user_id=user.id, action="user.login", resource_type="user",
              details="login_success", meta=get_request_meta())

    resp = jsonify({
        "user": user.to_dict(),
        "csrf_token": get_csrf_token(tokens["access_token"]),
    })
    set_access_cookies(resp, tokens["access_token"])
    set_refresh_cookies(resp, tokens["refresh_token"])
    return resp, 200

@api_bp.route("/auth/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token using the refresh token cookie."""
    from flask_jwt_extended import get_jwt_identity
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user or not user.is_active:
        return jsonify({"detail": "Unauthorized"}), 401
    access = create_access_token(identity=user_id)
    resp = jsonify({
        "message": "Token refreshed",
        "csrf_token": get_csrf_token(access),
    })
    set_access_cookies(resp, access)
    return resp, 200

@api_bp.route("/auth/logout", methods=["POST"])
def logout():
    resp = jsonify({"message": "Logged out"})
    unset_jwt_cookies(resp)
    return resp, 200


@api_bp.route("/auth/mfa-email-verify", methods=["POST"])
def mfa_email_verify():
    """Second step of admin login: verify the 6-digit code that was emailed.
    Called right after /auth/login when the response included
    mfa_required=True (mfa_method='email'). The code is single-use and
    expires 5 minutes after it was sent."""
    now = datetime.now(timezone.utc)
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    code = (data.get("code") or data.get("token") or "").strip()

    if not email or not code:
        return jsonify({
            "detail": "Email and code are required",
            "code": "missing_fields",
        }), 400

    user = User.query.filter_by(email=email).first()
    # Uniform error for unknown email / no pending OTP / wrong code / expired
    # code so an attacker cannot probe which case failed.
    generic_err = ({"detail": "Invalid or expired code", "code": "invalid_code"}, 401)

    if (not user or not user.email_otp_code
            or not user.email_otp_expires_at
            or user.email_otp_expires_at < now
            or not secrets.compare_digest(user.email_otp_code, code)):
        log_audit(user_id=user.id if user else None,
                  action="user.mfa_email_verify_failed",
                  resource_type="user", details="invalid_or_expired_otp",
                  meta=get_request_meta())
        return jsonify(generic_err[0]), generic_err[1]

    # Success: single-use - clear the code, issue an mfa_verified token.
    user.email_otp_code = None
    user.email_otp_expires_at = None
    user.last_login = now
    db.session.commit()

    access_token = create_access_token(
        identity=user.id, additional_claims={"mfa_verified": True})
    refresh_token = create_refresh_token(identity=user.id)

    log_audit(user_id=user.id, action="user.mfa_email_verified",
              resource_type="user", details="mfa_email_login_success",
              meta=get_request_meta())

    resp = jsonify({
        "user": user.to_dict(),
        "message": "Verified successfully",
        "csrf_token": get_csrf_token(access_token),
    })
    set_access_cookies(resp, access_token)
    set_refresh_cookies(resp, refresh_token)
    return resp, 200



@api_bp.route("/auth/forgot-password", methods=["POST"])
@limiter.limit(_FORGOT_LIMIT)
def forgot_password():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()

    if not validate_email(email):
        return jsonify({"detail": "Valid email required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"message": "If the email exists, a reset link has been sent."}), 200

    VerificationToken.query.filter_by(user_id=user.id, token_type="password_reset").update(
        {"used_at": datetime.now(timezone.utc)}
    )

    vtoken = VerificationToken.generate_token("password_reset", user.id, ttl_hours=1/12)  # 5 minutes
    db.session.add(vtoken)
    db.session.commit()

    frontend_url = current_app.config.get("FRONTEND_URL", "https://oseidanny882-cell.github.io/Aurum_Ghana").rstrip("/")
    reset_url = f"{frontend_url}/reset-password.html?token={vtoken.token}"
    sent = send_email(
        to=email,
        subject="Reset your AUTUM LUXE password",
        body=(
            f"Click to reset: {reset_url}\n\n"
            f"This link expires in 5 minutes.\n\n"
            f"If you did not request this, ignore this email."
        )
    )

    if not sent:
        return jsonify({
            "detail": "Failed to send reset email. Please try again.",
            "code": "email_failed"
        }), 503

    return jsonify({"message": "Reset link sent to your email."}), 200


@api_bp.route("/auth/reset-password", methods=["POST"])
def reset_password():
    data = request.get_json(silent=True) or {}
    token = (data.get("token") or "").strip()
    new_password = data.get("new_password") or ""

    if not token or not new_password:
        return jsonify({"detail": "Token and new_password required", "code": "missing_fields"}), 400

    ok, msg = validate_password_strength(new_password)
    if not ok:
        return jsonify({"detail": msg, "code": "weak_password"}), 400

    vtoken = VerificationToken.query.filter_by(
        token=token, token_type="password_reset", used_at=None
    ).first()

    if not vtoken or vtoken.expires_at < datetime.now(timezone.utc):
        return jsonify({"detail": "Invalid or expired token", "code": "invalid_token"}), 400

    user = User.query.get(vtoken.user_id)
    if not user:
        return jsonify({"detail": "User not found", "code": "user_not_found"}), 404

    from backend.extensions import bcrypt
    user.password_hash = bcrypt.generate_password_hash(new_password).decode("utf-8")
    vtoken.used_at = datetime.now(timezone.utc)
    db.session.commit()

    log_audit(user_id=user.id, action="user.password_reset", resource_type="user",
              details="password_changed", meta=get_request_meta())

    return jsonify({"message": "Password reset successful. Please log in."}), 200


@api_bp.route("/auth/verify-email", methods=["POST"])
def verify_email():
    data = request.get_json(silent=True) or {}
    token = (data.get("token") or "").strip()

    if not token:
        return jsonify({"detail": "Token required", "code": "missing_token"}), 400

    vtoken = VerificationToken.query.filter_by(
        token=token, token_type="email_verification", used_at=None
    ).first()

    if not vtoken or vtoken.expires_at < datetime.now(timezone.utc):
        return jsonify({"detail": "Invalid or expired token", "code": "invalid_token"}), 400

    user = User.query.get(vtoken.user_id)
    if not user:
        return jsonify({"detail": "User not found", "code": "user_not_found"}), 404

    user.is_verified = True
    vtoken.used_at = datetime.now(timezone.utc)
    db.session.commit()

    log_audit(user_id=user.id, action="user.email_verified", resource_type="user",
              details="email_verified", meta=get_request_meta())

    return jsonify({"message": "Email verified successfully"}), 200


@api_bp.route("/auth/profile", methods=["GET"])
@jwt_required()
def get_auth_profile():
    user_id = get_jwt_identity()
    user = User.query.filter_by(id=user_id).first()
    if not user:
        return jsonify({"detail": "User not found", "code": "user_not_found"}), 404
    return jsonify(user.to_dict()), 200
