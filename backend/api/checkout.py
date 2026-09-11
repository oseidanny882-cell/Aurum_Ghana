"""
Aurum Ghana - Checkout API
POST /checkout          - Create order from cart
GET  /checkout/session  - Get pending checkout for current user
"""
from datetime import datetime, timezone
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.api import api_bp
from backend.extensions import db
from backend.models import Order, OrderItem, CartItem, Product
from backend.utils.security import validate_ghana_phone, normalize_ghana_phone
from backend.services.audit import log_audit
from backend.utils.security import get_request_meta


@api_bp.route("/checkout", methods=["POST"])
@jwt_required()
def create_checkout():
    user_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}

    # Validate shipping
    required = ["first_name", "last_name", "phone", "street", "city", "region"]
    for f in required:
        if not (data.get(f) or "").strip():
            return jsonify({"detail": f"{f} is required", "code": "missing_field"}), 400
    phone = normalize_ghana_phone(data["phone"])
    if not validate_ghana_phone(phone):
        return jsonify({"detail": "Invalid phone number", "code": "invalid_phone"}), 400

    # Get items - prefer items in body, fall back to server-side cart
    items_data = data.get("items")
    if not items_data:
        # Fall back to server-side cart
        server_items = CartItem.query.filter_by(user_id=user_id).all()
        items_data = [
            {"product_id": ci.product_id, "quantity": ci.quantity, "variant_id": ci.variant_id}
            for ci in server_items
        ]
    if not items_data:
        return jsonify({"detail": "Cart is empty", "code": "empty_cart"}), 400

    cart_items = []
    for it in items_data:
        product_id = str(it.get("product_id") or it.get("id") or "")
        quantity = int(it.get("quantity", 1))
        variant_id = it.get("variant_id")
        product = Product.query.get(product_id)
        if not product or not product.is_active:
            return jsonify({"detail": f"Product {product_id} not found", "code": "not_found"}), 404
        is_dropship = getattr(product, "fulfillment_mode", "in_stock") == "dropship"
        if not is_dropship and product.stock < quantity:
            return jsonify({"detail": f"Not enough stock for {product.name}", "code": "insufficient_stock"}), 400
        unit_price = float(product.discount_price) if product.discount_price else float(product.price)
        cost_price = float(product.cost_price) if product.cost_price else None
        cart_items.append((product, variant_id, quantity, unit_price, cost_price))

    subtotal = sum(p * q for (_, _, q, p, _) in cart_items)
    delivery_fee = 0 if subtotal >= 500 else 35
    total = subtotal + delivery_fee

    order = Order(
        order_number=Order.generate_order_number(),
        user_id=user_id,
        status=Order.Status.PENDING,
        payment_status=Order.PaymentStatus.PENDING,
        subtotal=subtotal, delivery_fee=delivery_fee, total=total,
        shipping_first_name=data["first_name"].strip(),
        shipping_last_name=data["last_name"].strip(),
        shipping_phone=phone,
        shipping_email=(data.get("email") or "").strip() or None,
        shipping_street=data["street"].strip(),
        shipping_city=data["city"].strip(),
        shipping_region=data["region"].strip(),
        shipping_postal_code=(data.get("postal_code") or "").strip() or None,
        shipping_country=data.get("country", "Ghana").strip(),
        delivery_notes=(data.get("delivery_notes") or "").strip() or None,
        payment_method="paystack",
    )
    db.session.add(order)
    db.session.flush()

    for product, variant_id, quantity, unit_price, cost_price in cart_items:
        oi = OrderItem(
            order_id=order.id, product_id=product.id, variant_id=variant_id,
            sku=product.sku, name=product.name, image=product.image,
            quantity=quantity, unit_price=unit_price, line_total=unit_price * quantity,
            cost_price=cost_price,
        )
        db.session.add(oi)

    # Clear cart
    CartItem.query.filter_by(user_id=user_id).delete()
    db.session.commit()

    log_audit(user_id=user_id, action="order.created", resource_type="order",
              resource_id=order.id, details=f"order_number={order.order_number}",
              meta=get_request_meta())

    return jsonify({
        "order_id": order.id,
        "order_number": order.order_number,
        "total": total,
        "currency": order.currency,
        "status": order.status,
    }), 201


@api_bp.route("/checkout/session", methods=["GET"])
@jwt_required()
def get_checkout_session():
    user_id = get_jwt_identity()
    pending = Order.query.filter_by(
        user_id=user_id, status=Order.Status.PENDING, payment_status=Order.PaymentStatus.PENDING
    ).order_by(Order.created_at.desc()).first()
    if not pending:
        return jsonify({"detail": "No pending checkout", "code": "not_found"}), 404
    return jsonify(pending.to_dict(include_items=True)), 200
