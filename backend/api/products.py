"""
Aurum Ghana - Products API
GET  /products          - List with filters (category, q, featured, is_new, is_best, filter=new|best|sale, page, per_page)
GET  /products/<slug>   - Product detail
GET  /categories        - List categories
"""
from flask import request, jsonify, g
from backend.api import api_bp
from backend.models import Product, Category, Review, OrderItem, User
from backend.extensions import db
from datetime import datetime, timezone


def _paginate(query, default=24, max_size=100):
    try:
        page = max(1, int(request.args.get("page", 1)))
        per_page = min(max_size, max(1, int(request.args.get("per_page", default))))
    except (TypeError, ValueError):
        page, per_page = 1, default
    return query.paginate(page=page, per_page=per_page, error_out=False)


@api_bp.route("/products", methods=["GET"])
def list_products():
    q = Product.query.filter(Product.is_active.is_(True))

    category = request.args.get("category")
    if category:
        cat = Category.query.filter_by(slug=category).first()
        if cat:
            q = q.filter(Product.category_id == cat.id)
        else:
            return jsonify({"items": [], "total": 0, "page": 1, "per_page": 0, "pages": 0})

    # Accept both "q" (API convention) and "search" (user-friendly URL)
    search = request.args.get("q") or request.args.get("search")
    if search:
        pattern = f"%{search}%"
        q = q.filter(db.or_(
            Product.name.ilike(pattern),
            Product.description.ilike(pattern),
            Product.sku.ilike(pattern),
        ))

    if request.args.get("featured") in ("1", "true", "yes"):
        q = q.filter(Product.is_featured.is_(True))
    if request.args.get("is_new") in ("1", "true", "yes"):
        q = q.filter(Product.is_new.is_(True))
    if request.args.get("is_best") in ("1", "true", "yes"):
        q = q.filter(Product.is_best.is_(True))
    if request.args.get("filter") == "new":
        q = q.filter(Product.is_new.is_(True)).order_by(Product.created_at.desc())
    elif request.args.get("filter") == "best":
        q = q.filter(Product.is_best.is_(True)).order_by(Product.rating_avg.desc())
    elif request.args.get("filter") == "sale":
        q = q.filter(Product.discount_price.isnot(None), Product.discount_price > 0).order_by(Product.discount_price.asc())

    min_price = request.args.get("min_price")
    max_price = request.args.get("max_price")
    if min_price:
        try: q = q.filter(Product.price >= float(min_price))
        except ValueError: pass
    if max_price:
        try: q = q.filter(Product.price <= float(max_price))
        except ValueError: pass

    sort = request.args.get("sort", "newest")
    if sort == "price_asc": q = q.order_by(Product.price.asc())
    elif sort == "price_desc": q = q.order_by(Product.price.desc())
    elif sort == "rating": q = q.order_by(Product.rating_avg.desc())
    else: q = q.order_by(Product.created_at.desc())

    result = _paginate(q)
    return jsonify({
        "items": [p.to_dict() for p in result.items],
        "total": result.total,
        "page": result.page,
        "per_page": result.per_page,
        "pages": result.pages,
    }), 200


@api_bp.route("/products/<slug_or_id>", methods=["GET"])
def get_product(slug_or_id):
    product = Product.query.filter(
        db.or_(Product.slug == slug_or_id, Product.sku == slug_or_id, Product.id == slug_or_id)
    ).first()
    if not product or not product.is_active:
        return jsonify({"detail": "Product not found", "code": "not_found"}), 404
    # increment view count
    product.view_count = (product.view_count or 0) + 1
    db.session.commit()
    return jsonify(product.to_dict(include_category=True)), 200


@api_bp.route("/categories", methods=["GET"])
def list_categories():
    cats = Category.query.filter_by(is_active=True).order_by(Category.display_order.asc()).all()
    return jsonify({"items": [c.to_dict() for c in cats]}), 200


# ==================== REVIEW ENDPOINTS ====================

@api_bp.route('/products/<product_id>/reviews', methods=['POST'])
def submit_review(product_id):
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    for field in ['title', 'content', 'rating', 'order_item_id']:
        if not data.get(field):
            return jsonify({'error': f'Missing required field: {field}'}), 400
    if not (1 <= data.get('rating', 0) <= 5):
        return jsonify({'error': 'Rating must be between 1 and 5'}), 400
    order_item = OrderItem.query.filter_by(id=data.get('order_item_id'), product_id=product_id).first()
    if not order_item:
        return jsonify({'error': 'Invalid order item or product'}), 403
    if order_item.review:
        return jsonify({'error': 'Review already submitted for this order item'}), 409
    user_id = getattr(g, 'current_user_id', None)
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    review = Review(product_id=product_id, user_id=user_id, title=data['title'], content=data['content'], rating=data['rating'], verified_purchase=True, reviewer_name=user.name, reviewer_email=user.email, status='pending')
    order_item.review = review
    db.session.add(review)
    db.session.commit()
    product = Product.query.get(product_id)
    if product:
        product.review_count = Review.query.filter_by(product_id=product_id, is_approved=True).count()
        approved = Review.query.filter_by(product_id=product_id, is_approved=True).all()
        product.rating_avg = sum(r.rating for r in approved) / len(approved) if approved else 0
        db.session.commit()
    return jsonify(review.to_dict(include_user=True)), 201


@api_bp.route('/products/<product_id>/reviews', methods=['GET'])
def get_product_reviews(product_id):
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 50)
    reviews = Review.query.filter_by(product_id=product_id, is_approved=True, status='approved').order_by(Review.published_at.desc())
    total = reviews.count()
    reviews = reviews.offset((page - 1) * per_page).limit(per_page).all()
    return jsonify({'items': [r.to_dict() for r in reviews], 'total': total, 'page': page, 'per_page': per_page, 'has_more': (page * per_page) < total}), 200


@api_bp.route('/admin/reviews', methods=['GET'])
def admin_get_reviews():
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    status_filter = request.args.get('status', 'all')
    query = Review.query
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    reviews = query.order_by(Review.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({'items': [r.to_dict(include_user=True) for r in reviews.items], 'total': reviews.total, 'page': reviews.page, 'per_page': reviews.per_page, 'pages': reviews.pages}), 200


@api_bp.route('/admin/reviews/<review_id>', methods=['PATCH'])
def admin_update_review(review_id):
    review = Review.query.get_or_404(review_id)
    data = request.get_json()
    if not data or 'status' not in data:
        return jsonify({'error': 'Status is required'}), 400
    if data['status'] not in ['pending', 'approved', 'rejected', 'archived']:
        return jsonify({'error': 'Invalid status'}), 400
    review.status = data['status']
    if data['status'] == 'approved':
        review.is_approved = True
        review.published_at = datetime.now(timezone.utc)
    elif data['status'] == 'rejected':
        review.is_approved = False
    db.session.commit()
    return jsonify(review.to_dict(include_user=True)), 200
