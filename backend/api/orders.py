"""
Aurum Ghana - Orders API
GET /orders       - List user's orders
GET /orders/<id> - Get order detail
"""
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.api import api_bp
from backend.models import Order


@api_bp.route("/orders", methods=["GET"])
@jwt_required()
def list_orders():
    user_id = get_jwt_identity()
    page = max(1, int(request.args.get("page", 1)))
    per_page = min(100, max(1, int(request.args.get("per_page", 10))))

    pagination = Order.query.filter_by(user_id=user_id).order_by(
        Order.created_at.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "items": [o.to_dict() for o in pagination.items],
        "total": pagination.total,
        "page": pagination.page,
        "per_page": pagination.per_page,
        "pages": pagination.pages,
    }), 200


@api_bp.route("/orders/<order_id>", methods=["GET"])
@jwt_required()
def get_order(order_id):
    user_id = get_jwt_identity()
    order = Order.query.filter_by(id=order_id, user_id=user_id).first()
    if not order:
        return jsonify({"detail": "Order not found", "code": "not_found"}), 404
    return jsonify(order.to_dict(include_items=True)), 200
