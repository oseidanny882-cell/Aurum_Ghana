"""
Aurum Ghana - API Blueprint
"""
from flask import Blueprint

api_bp = Blueprint("api", __name__, url_prefix="/api/v1")

from backend.api import auth, products, cart, checkout, payments, orders, user, admin, mfa, webhooks, newsletter  # noqa: F401, E402
