"""
Aurum Ghana - Webhooks
POST /webhooks/paystack  - Paystack webhook for payment confirmation
"""
import hmac, hashlib, json
from datetime import datetime, timezone
from flask import request, jsonify, current_app
from backend.api import api_bp
from backend.extensions import db
from backend.models import Order, Payment
from backend.services.audit import log_audit
from backend.utils.security import get_request_meta


@api_bp.route("/webhooks/paystack", methods=["POST"])
def paystack_webhook():
    """Paystack webhook -- verifies HMAC and updates order status."""
    payload = request.get_data(as_text=True)
    sig = request.headers.get("x-paystack-signature", "")

    secret = current_app.config.get("PAYSTACK_WEBHOOK_SECRET", "")
    if not secret:
        return jsonify({"detail": "Webhook not configured"}), 500

    expected = hmac.new(secret.encode(), payload.encode(), hashlib.sha512).hexdigest()
    if not hmac.compare_digest(expected, sig):
        return jsonify({"detail": "Invalid signature"}), 401

    event = json.loads(payload or "{}")
    event_type = event.get("event")
    data = event.get("data", {})
    reference = data.get("reference")

    if not reference:
        return jsonify({"detail": "No reference"}), 400

    order = Order.query.filter_by(paystack_reference=reference).first()
    if not order:
        return jsonify({"detail": "Order not found"}), 404

    if event_type == "charge.success":
        order.payment_status = Order.PaymentStatus.PAID
        order.status = Order.Status.CONFIRMED
        order.confirmed_at = datetime.now(timezone.utc)
        # Reduce stock
        from backend.models import Product
        for oi in order.items:
            p = Product.query.get(oi.product_id)
            if p:
                p.stock = max(0, p.stock - oi.quantity)

        payment = order.payment or Payment(order_id=order.id, amount=order.total, currency=order.currency)
        payment.status = Payment.Status.SUCCESS
        payment.provider_reference = reference
        payment.provider_response = json.dumps(data)[:10000]
        if not order.payment:
            order.payment = payment

        log_audit(user_id=order.user_id, action="order.paid", resource_type="order",
                  resource_id=order.id, details=f"order_number={order.order_number}",
                  meta=get_request_meta())

    elif event_type in ("charge.failed", "payment.failed"):
        order.payment_status = Order.PaymentStatus.FAILED
        log_audit(user_id=order.user_id, action="order.payment_failed", resource_type="order",
                  resource_id=order.id, details=f"event={event_type}", meta=get_request_meta())

    db.session.commit()
    return jsonify({"received": True}), 200
