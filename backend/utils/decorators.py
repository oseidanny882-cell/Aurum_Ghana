"""
Aurum Ghana - Decorators
"""
from functools import wraps
from flask import request, jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from backend.models import User
from backend.extensions import limiter


def jwt_or_anonymous(fn):
    """Allow both authenticated and anonymous users. If JWT present, attach user."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request(optional=True)
            user_id = get_jwt_identity()
            if user_id:
                user = User.query.get(user_id)
                if user and user.is_active:
                    request.current_user = user
                else:
                    request.current_user = None
            else:
                request.current_user = None
        except Exception:
            request.current_user = None
        return fn(*args, **kwargs)
    return wrapper
