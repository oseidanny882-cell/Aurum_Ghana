"""
Aurum Ghana - Payments API
POST /payments/initialize/<order_id>  - Initialize Paystack payment
GET  /payments/verify/<reference>     - Verify a payment (used by callback page)
GET  /payments/callback              - Paystack redirect callback
GET  /payments/config                - Public config (public key, env, mock mode)
"""
import hmac, hashlib, time
from datetime import datetime, timezone
from flask import request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.api import api_bp
from backend.extensions import db
from backend.models import Order, Payment
from backend.services.paystack import initialize_payment, verify_payment
from backend.services.audit import log_audit
from backend.utils.security import get_request_meta


@api_bp.route("/payments/config", methods=["GET"])
def payment_config():
    """Public endpoint - serves the Paystack public key and tells the frontend
    whether it's in mock/demo mode. Safe to expose (public key only)."""
    secret = current_app.config.get("PAYSTACK_SECRET_KEY", "")
    public = current_app.config.get("PAYSTACK_PUBLIC_KEY", "")
    is_mock = not secret
    env = "demo"
    if secret:
        env = "live" if secret.startswith("sk_live_") else "test"
    return jsonify({
        "publicKey": public,
        "env": env,
        "mock": is_mock,
        "currency": "GHS",
    }), 200


@api_bp.route("/payments/initialize/<order_id>", methods=["POST"])
@jwt_required()
def initialize(order_id):
    user_id = get_jwt_identity()
    order = Order.query.filter_by(id=order_id, user_id=user_id).first()
    if not order:
        return jsonify({"detail": "Order not found", "code": "not_found"}), 404
    if order.payment_status == Order.PaymentStatus.PAID:
        return jsonify({"detail": "Order already paid", "code": "already_paid"}), 400

    result = initialize_payment(order)
    if not result.get("authorization_url"):
        return jsonify({"detail": "Payment provider error", "code": "provider_error"}), 502

    # Store Paystack reference
    order.paystack_reference = result.get("reference")
    db.session.commit()

    return jsonify({
        "authorization_url": result["authorization_url"],
        "reference": result["reference"],
    }), 200


@api_bp.route("/payments/verify/<reference>", methods=["GET"])
@jwt_required()
def verify(reference):
    """Verify a payment by reference. Called by the callback page after
    Paystack redirects back. Updates order status if successful."""
    user_id = get_jwt_identity()
    order = Order.query.filter_by(paystack_reference=reference, user_id=user_id).first()
    if not order:
        return jsonify({"detail": "Order not found", "code": "not_found"}), 404

    if order.payment_status == Order.PaymentStatus.PAID:
        return jsonify({
            "status": "success",
            "message": "Payment already verified",
            "order_number": order.order_number,
        }), 200

    try:
        result = verify_payment(reference)
    except Exception as e:
        return jsonify({
            "status": "failed",
            "message": str(e) or "Verification failed",
            "order_number": order.order_number,
        }), 502

    paystack_status = (result.get("status") or "").lower()
    if paystack_status == "success":
        order.payment_status = Order.PaymentStatus.PAID
        order.status = Order.Status.CONFIRMED
        order.confirmed_at = datetime.now(timezone.utc)
        # Decrement stock - only for in-stock orders, not dropship
        for item in order.items.all():
            if item.product and getattr(item.product, 'fulfillment_mode', 'in_stock') != 'dropship':
                item.product.stock = max(0, item.product.stock - item.quantity)
        # Set fulfillment_status for dropship orders
        if getattr(order, 'fulfillment_status', 'n/a') == 'n/a' or order.fulfillment_status == 'n/a':
            order.fulfillment_status = order.FulfillmentStatus.NEW
        db.session.commit()
        log_audit(user_id=user_id, action="payment.verified", resource_type="order",
                  resource_id=order.id, details=f"ref={reference}",
                  meta=get_request_meta())
        return jsonify({
            "status": "success",
            "message": "Payment confirmed",
            "order_number": order.order_number,
            "amount": float(order.total),
            "currency": order.currency,
        }), 200
    else:
        order.payment_status = Order.PaymentStatus.FAILED
        db.session.commit()
        return jsonify({
            "status": "failed",
            "message": f"Payment status: {paystack_status or 'unknown'}",
            "order_number": order.order_number,
        }), 200


@api_bp.route("/payments/callback", methods=["GET"])
def payment_callback():
    """Paystack redirect callback. Just acknowledges the reference so the
    frontend can poll /payments/verify/<ref> for the actual status."""
    ref = request.args.get("reference") or request.args.get("trxref") or ""
    return jsonify({
        "reference": ref,
        "message": "Payment callback received. Please wait for confirmation.",
    }), 200
