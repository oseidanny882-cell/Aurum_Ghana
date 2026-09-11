"""
Aurum Ghana - Paystack service
"""
import requests
from flask import current_app


class PaystackError(Exception):
    def __init__(self, message, code=None):
        super().__init__(message)
        self.code = code


def _get_secret():
    return current_app.config.get("PAYSTACK_SECRET_KEY", "")


def _headers():
    return {
        "Authorization": f"Bearer {_get_secret()}",
        "Content-Type": "application/json",
    }


def initialize_payment(order) -> dict:
    """
    Create a Paystack payment transaction.
    Returns a flat dict with authorization_url, reference, and access_code
    (always unwrapped from Paystack's nested response for consistency).
    """
    secret = _get_secret()
    if not secret:
        # Dev/demo mode: return a mock transaction that points back to our callback
        return {
            "authorization_url": f"{current_app.config.get('FRONTEND_URL', 'http://localhost:8000')}/payment-callback.html?reference=DEMO_{order.id}",
            "reference": f"DEMO_{order.id}",
            "access_code": "demo_access",
        }

    url = "https://api.paystack.co/transaction/initialize"
    payload = {
        "amount": int(float(order.total) * 100),  # kobo
        "email": order.shipping_email or "guest@aurum-ghana.com",
        "currency": order.currency or "GHS",
        "reference": f"ORD_{order.order_number}",
        "callback_url": current_app.config.get("PAYSTACK_CALLBACK_URL", ""),
        "metadata": {
            "order_id": order.id,
            "order_number": order.order_number,
        },
    }

    resp = requests.post(url, json=payload, headers=_headers(), timeout=15)
    data = resp.json()

    if not data.get("status"):
        raise PaystackError(data.get("message", "Paystack error"), code="paystack_init_failed")

    return data["data"]


def verify_payment(reference: str) -> dict:
    """Verify a Paystack transaction by reference.

    Returns a flat dict (same shape as Paystack's /transaction/verify data):
    { "status": "success" | "failed" | ..., "reference": "...", ... }
    Always unwrapped from the Paystack wrapper response.
    """
    secret = _get_secret()
    if not secret or reference.startswith("DEMO_"):
        # Dev/demo mode: auto-approve so the full UI flow can be tested locally
        return {"status": "success", "reference": reference, "amount": 0, "currency": "GHS"}

    url = f"https://api.paystack.co/transaction/verify/{reference}"
    resp = requests.get(url, headers=_headers(), timeout=15)
    data = resp.json()

    if not data.get("status"):
        raise PaystackError(data.get("message", "Verification failed"), code="paystack_verify_failed")

    return data["data"]
