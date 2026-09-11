"""
Aurum Ghana - User API
GET   /user/profile
PATCH /user/profile
POST  /user/change-password
"""
from datetime import datetime, timezone
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.api import api_bp
from backend.extensions import db
from backend.models import User
from backend.utils.security import validate_password_strength, validate_ghana_phone, normalize_ghana_phone
from backend.services.audit import log_audit
from backend.utils.security import get_request_meta


@api_bp.route("/user/profile", methods=["GET"])
@jwt_required()
def get_profile():
    user = User.query.get(get_jwt_identity())
    if not user:
        return jsonify({"detail": "User not found", "code": "not_found"}), 404
    return jsonify(user.to_dict(include_sensitive=True)), 200


@api_bp.route("/user/profile", methods=["PATCH"])
@jwt_required()
def update_profile():
    user = User.query.get(get_jwt_identity())
    if not user:
        return jsonify({"detail": "User not found", "code": "not_found"}), 404

    data = request.get_json(silent=True) or {}
    if "first_name" in data:
        user.first_name = (data["first_name"] or "").strip() or user.first_name
    if "last_name" in data:
        user.last_name = (data["last_name"] or "").strip() or user.last_name
    if "email" in data and data["email"]:
        user.email = data["email"].strip().lower()
    if "phone" in data and data["phone"]:
        phone = normalize_ghana_phone(data["phone"])
        if not validate_ghana_phone(phone):
            return jsonify({"detail": "Invalid phone", "code": "invalid_phone"}), 400
        user.phone = phone
    db.session.commit()
    return jsonify(user.to_dict()), 200


@api_bp.route("/user/change-password", methods=["POST"])
@jwt_required()
def change_password():
    user = User.query.get(get_jwt_identity())
    if not user:
        return jsonify({"detail": "User not found", "code": "not_found"}), 404

    data = request.get_json(silent=True) or {}
    current_password = data.get("current_password") or ""
    new_password = data.get("new_password") or ""

    from backend.extensions import bcrypt
    if not bcrypt.check_password_hash(user.password_hash, current_password):
        return jsonify({"detail": "Current password incorrect", "code": "invalid_password"}), 401

    ok, msg = validate_password_strength(new_password)
    if not ok:
        return jsonify({"detail": msg, "code": "weak_password"}), 400

    user.password_hash = bcrypt.generate_password_hash(new_password).decode("utf-8")
    db.session.commit()

    log_audit(user_id=user.id, action="user.password_changed", resource_type="user",
              details="password_changed", meta=get_request_meta())

    return jsonify({"message": "Password changed successfully"}), 200
