"""
Aurum Ghana - Cart API
GET    /cart           - Get current cart
POST   /cart/items     - Add item
PATCH  /cart/items/<id> - Update quantity
DELETE /cart/items/<id> - Remove item
DELETE /cart/clear     - Clear cart
"""
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.api import api_bp
from backend.extensions import db
from backend.models import CartItem, Product


def _get_cart(user_id):
    return CartItem.query.filter_by(user_id=user_id).all()


def _build_response(items):
    def _unit_price(item):
        p = item.product
        if not p:
            return 0.0
        return float(p.discount_price) if p.discount_price else float(p.price)

    subtotal = sum(_unit_price(i) * i.quantity for i in items)
    delivery_fee = 0 if subtotal >= 500 or subtotal == 0 else 35
    return {
        "items": [i.to_dict() for i in items],
        "subtotal": subtotal,
        "delivery_fee": delivery_fee,
        "discount": 0,
        "total": subtotal + delivery_fee,
        "item_count": sum(i.quantity for i in items),
    }


@api_bp.route("/cart", methods=["GET"])
@jwt_required()
def get_cart():
    user_id = get_jwt_identity()
    items = _get_cart(user_id)
    return jsonify(_build_response(items)), 200


@api_bp.route("/cart/items", methods=["POST"])
@jwt_required()
def add_cart_item():
    user_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}
    product_id = str(data.get("product_id") or "")
    quantity = max(1, int(data.get("quantity", 1)))
    variant_id = str(data.get("variant_id")) if data.get("variant_id") else None

    product = Product.query.get(product_id)
    if not product or not product.is_active:
        return jsonify({"detail": "Product not found", "code": "not_found"}), 404

    is_dropship = getattr(product, "fulfillment_mode", "in_stock") == "dropship"
    max_qty = 99 if is_dropship else product.stock
    if quantity > max_qty:
        msg = "Maximum 99 allowed for dropship items" if is_dropship else "Not enough stock"
        return jsonify({"detail": msg, "code": "insufficient_stock"}), 400

    existing = CartItem.query.filter_by(
        user_id=user_id, product_id=product_id, variant_id=variant_id
    ).first()

    if existing:
        new_qty = existing.quantity + quantity
        if new_qty > max_qty:
            msg = "Maximum 99 allowed for dropship items" if is_dropship else "Not enough stock"
            return jsonify({"detail": msg, "code": "insufficient_stock"}), 400
        existing.quantity = new_qty
    else:
        existing = CartItem(user_id=user_id, product_id=product_id, variant_id=variant_id, quantity=quantity)
        db.session.add(existing)

    db.session.commit()
    items = _get_cart(user_id)
    return jsonify(_build_response(items)), 200


@api_bp.route("/cart/items/<item_id>", methods=["PATCH"])
@jwt_required()
def update_cart_item(item_id):
    user_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}
    quantity = int(data.get("quantity", 1))

    item = CartItem.query.filter_by(id=item_id, user_id=user_id).first()
    if not item:
        return jsonify({"detail": "Item not found", "code": "not_found"}), 404

    if quantity <= 0:
        db.session.delete(item)
    else:
        is_dropship = getattr(item.product, "fulfillment_mode", "in_stock") == "dropship"
        max_qty = 99 if is_dropship else item.product.stock
        if quantity > max_qty:
            msg = "Maximum 99 allowed for dropship items" if is_dropship else "Not enough stock"
            return jsonify({"detail": msg, "code": "insufficient_stock"}), 400
        item.quantity = quantity

    db.session.commit()
    items = _get_cart(user_id)
    return jsonify(_build_response(items)), 200


@api_bp.route("/cart/items/<item_id>", methods=["DELETE"])
@jwt_required()
def remove_cart_item(item_id):
    user_id = get_jwt_identity()
    item = CartItem.query.filter_by(id=item_id, user_id=user_id).first()
    if not item:
        return jsonify({"detail": "Item not found", "code": "not_found"}), 404
    db.session.delete(item)
    db.session.commit()
    items = _get_cart(user_id)
    return jsonify(_build_response(items)), 200


@api_bp.route("/cart/clear", methods=["DELETE"])
@jwt_required()
def clear_cart():
    user_id = get_jwt_identity()
    CartItem.query.filter_by(user_id=user_id).delete()
    db.session.commit()
    return jsonify(_build_response([])), 200
