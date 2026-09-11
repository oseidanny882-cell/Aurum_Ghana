import os
import uuid
from flask import request, jsonify
from werkzeug.utils import secure_filename
try:
    from PIL import Image
except ImportError:
    Image = None  # Image processing is optional
from backend.api import api_bp
from backend.extensions import db
from backend.models import Product, Category, Supplier, Order, OrderItem, User
from backend.services.audit import log_audit
from backend.utils.security import get_request_meta, role_required

ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
IMAGE_UPLOAD_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "frontend", "images"
)
# Images are resized proportionally so no dimension exceeds this. Keeps the
# site fast without making the modal preview look stretched or blurry.
MAX_IMAGE_DIMENSION = 1200   # max width or height in pixels
IMAGE_QUALITY = 85           # JPEG quality (0-100)
MAX_FILE_SIZE_MB = 5
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

def allowed_image(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS

def resize_and_save_image(file, dest_path, max_dim=MAX_IMAGE_DIMENSION, quality=IMAGE_QUALITY, crop_square=True):
    """Open the uploaded file, resize to a uniform 1:1 square, and save optimized.

    Algorithm for crop_square=True:
      1. Normalize mode to RGB.
      2. Scale proportionally so the shorter side = max_dim (upscaling small images too).
      3. Center-crop to a max_dim x max_dim square.
      4. Save with JPEG compression.

    Result: every saved image is exactly max_dim x max_dim pixels (default 1200x1200),
    regardless of the original aspect ratio. PNGs are preserved.

        Falls back to raw byte copy if Pillow fails.
    """
    if Image is None:
        # PIL not available — just write the raw file
        try:
            if hasattr(file, "stream"):
                file.stream.seek(0)
                data = file.stream.read()
            else:
                file.seek(0)
                data = file.read()
            with open(dest_path, "wb") as out:
                out.write(data)
        except Exception:
            pass
        return

    try:
        img = Image.open(file.stream if hasattr(file, "stream") else file)

        # Normalize mode for JPEG compatibility
        if img.mode in ("RGBA", "P", "LA", "PA"):
            background = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            mask = img.split()[-1] if img.mode in ("RGBA", "PA") else None
            background.paste(img, mask=mask)
            img = background
        elif img.mode != "RGB":
            img = img.convert("RGB")

        if crop_square:
            w, h = img.size
            # Scale up or down so the shorter side equals max_dim
            if w < h:
                new_w = max_dim
                new_h = int(h * (max_dim / w))
            else:
                new_h = max_dim
                new_w = int(w * (max_dim / h))
            img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

            # Now center-crop to a perfect square
            w2, h2 = img.size
            side = min(w2, h2)
            left = (w2 - side) // 2
            top = (h2 - side) // 2
            img = img.crop((left, top, left + side, top + side))

        else:
            # Proportional resize only (no crop)
            w, h = img.size
            if w > max_dim or h > max_dim:
                ratio = min(max_dim / w, max_dim / h)
                img = img.resize((int(w * ratio), int(h * ratio)), Image.Resampling.LANCZOS)

        ext = os.path.splitext(dest_path)[1].lower()
        if ext in (".jpg", ".jpeg"):
            img.save(dest_path, quality=quality, optimize=True)
        elif ext == ".png":
            img.save(dest_path, optimize=True)
        else:
            img.save(dest_path, quality=quality, optimize=True)

    except Exception:
        if hasattr(file, "stream"):
            file.stream.seek(0)
            data = file.stream.read()
        else:
            file.seek(0)
            data = file.read()
        with open(dest_path, "wb") as out:
            out.write(data)


### Admin Dashboard Stats

@api_bp.route("/admin/dashboard", methods=["GET"])
@role_required("admin")
def admin_dashboard():
    """Return aggregate stats for the admin dashboard."""
    from sqlalchemy import func
    from datetime import datetime, timezone, timedelta

    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_month_start = (month_start - timedelta(days=1)).replace(day=1)

    # Revenue: orders with confirmed payment (payment_status = "paid")
    curr_revenue = db.session.query(func.coalesce(func.sum(Order.total), 0)).filter(
        Order.payment_status == "paid",
        Order.created_at >= month_start,
    ).scalar() or 0
    prev_revenue = db.session.query(func.coalesce(func.sum(Order.total), 0)).filter(
        Order.payment_status == "paid",
        Order.created_at >= last_month_start,
        Order.created_at < month_start,
    ).scalar() or 0
    revenue_change = round(((float(curr_revenue) - float(prev_revenue)) / float(prev_revenue) * 100), 1) if prev_revenue else (100 if curr_revenue else 0)

    # Orders
    curr_orders = Order.query.filter(Order.created_at >= month_start).count()
    prev_orders = Order.query.filter(
        Order.created_at >= last_month_start,
        Order.created_at < month_start,
    ).count()
    orders_change = round(((curr_orders - prev_orders) / prev_orders * 100), 1) if prev_orders else (100 if curr_orders else 0)

    # Customers
    curr_customers = User.query.filter(
        User.created_at >= month_start, User.is_active == True,
    ).count()
    prev_customers = User.query.filter(
        User.created_at >= last_month_start, User.created_at < month_start,
        User.is_active == True,
    ).count()
    customers_change = round(((curr_customers - prev_customers) / prev_customers * 100), 1) if prev_customers else (100 if curr_customers else 0)

    # Conversion: orders this month / new users this month
    conversion_rate = round((curr_orders / curr_customers * 100), 1) if curr_customers else 0
    prev_conversion = round((prev_orders / prev_customers * 100), 1) if prev_customers else 0
    conversion_change = round(conversion_rate - prev_conversion, 1)

    return jsonify({
        "revenue": float(curr_revenue),
        "revenue_change": revenue_change,
        "orders": curr_orders,
        "orders_change": orders_change,
        "customers": curr_customers,
        "customers_change": customers_change,
        "conversion_rate": conversion_rate,
        "conversion_change": conversion_change,
    }), 200


### Image Upload

@api_bp.route("/admin/upload/image", methods=["POST"])
@role_required("admin")
def admin_upload_image():
    """Upload a product image. Returns the public URL of the saved image.

    The image is resized to a maximum dimension of MAX_IMAGE_DIMENSION
    (default 1200px) and saved with 85% JPEG quality to keep file sizes
    manageable while staying sharp on retina displays.
    """
    if "file" not in request.files:
        return jsonify({"detail": "No file part in request"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"detail": "No file selected"}), 400
    if not allowed_image(file.filename):
        return jsonify({"detail": "Allowed types: PNG, JPG, JPEG, GIF, WEBP"}), 400

    # Check file size before loading the whole thing into memory
    file.stream.seek(0, 2)  # seek to end
    file_size = file.stream.tell()
    file.stream.seek(0)     # reset to start
    if file_size > MAX_FILE_SIZE_BYTES:
        return jsonify({
            "detail": f"File too large. Maximum size is {MAX_FILE_SIZE_MB} MB."
        }), 413

    os.makedirs(IMAGE_UPLOAD_DIR, exist_ok=True)
    ext = file.filename.rsplit(".", 1)[1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    dest_path = os.path.join(IMAGE_UPLOAD_DIR, filename)

    # Resize and save with Pillow for a fast, nicely-sized image
    resize_and_save_image(file, dest_path)

    return jsonify({"url": f"/images/{filename}", "filename": filename}), 200


### Suppliers

@api_bp.route("/admin/suppliers", methods=["GET"])
@role_required("admin")
def admin_list_suppliers():
    page = max(1, int(request.args.get("page", 1)))
    per_page = min(100, max(1, int(request.args.get("per_page", 20))))
    p = Supplier.query.order_by(Supplier.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({"items": [s.to_dict() for s in p.items], "total": p.total,
                    "page": p.page, "per_page": p.per_page, "pages": p.pages}), 200


@api_bp.route("/admin/suppliers", methods=["POST"])
@role_required("admin")
def admin_create_supplier():
    data = request.get_json(silent=True) or {}
    if not data.get("name"):
        return jsonify({"detail": "name is required", "code": "missing_field"}), 400
    s = Supplier(
        name=str(data["name"]).strip(),
        country=data.get("country") or None,
        contact_name=data.get("contact_name") or None,
        contact_email=data.get("contact_email") or None,
        contact_phone=data.get("contact_phone") or None,
        address=data.get("address") or None,
        api_endpoint=data.get("api_endpoint") or None,
        api_key=data.get("api_key") or None,
        notes=data.get("notes") or None,
        lead_time_days=int(data.get("lead_time_days", 7)),
        is_active=bool(data.get("is_active", True)),
    )
    db.session.add(s)
    db.session.commit()
    log_audit(user_id=request.current_user.id, action="admin.supplier_created",
              resource_type="supplier", resource_id=s.id, details=f"name={s.name}", meta=get_request_meta())
    return jsonify(s.to_dict()), 201


@api_bp.route("/admin/suppliers/<supplier_id>", methods=["GET"])
@role_required("admin")
def admin_get_supplier(supplier_id):
    s = Supplier.query.get(supplier_id)
    if not s:
        return jsonify({"detail": "Supplier not found", "code": "not_found"}), 404
    return jsonify(s.to_dict()), 200


@api_bp.route("/admin/suppliers/<supplier_id>", methods=["PUT"])
@role_required("admin")
def admin_update_supplier(supplier_id):
    s = Supplier.query.get(supplier_id)
    if not s:
        return jsonify({"detail": "Supplier not found", "code": "not_found"}), 404
    data = request.get_json(silent=True) or {}
    if "name" in data: s.name = str(data["name"]).strip()
    if "country" in data: s.country = data["country"] or None
    if "contact_name" in data: s.contact_name = data["contact_name"] or None
    if "contact_email" in data: s.contact_email = data["contact_email"] or None
    if "contact_phone" in data: s.contact_phone = data["contact_phone"] or None
    if "address" in data: s.address = data["address"] or None
    if "api_endpoint" in data: s.api_endpoint = data["api_endpoint"] or None
    if "api_key" in data: s.api_key = data["api_key"] or None
    if "notes" in data: s.notes = data["notes"] or None
    if "lead_time_days" in data: s.lead_time_days = int(data["lead_time_days"])
    if "is_active" in data: s.is_active = bool(data["is_active"])
    db.session.commit()
    log_audit(user_id=request.current_user.id, action="admin.supplier_updated",
              resource_type="supplier", resource_id=s.id, meta=get_request_meta())
    return jsonify(s.to_dict()), 200


@api_bp.route("/admin/suppliers/<supplier_id>", methods=["DELETE"])
@role_required("admin")
def admin_delete_supplier(supplier_id):
    s = Supplier.query.get(supplier_id)
    if not s:
        return jsonify({"detail": "Supplier not found", "code": "not_found"}), 404
    s.is_active = False
    db.session.commit()
    log_audit(user_id=request.current_user.id, action="admin.supplier_deleted",
              resource_type="supplier", resource_id=supplier_id, meta=get_request_meta())
    return jsonify({"message": "Supplier deactivated"}), 200

### Dropship

@api_bp.route("/admin/dropship/send-to-supplier/<order_id>", methods=["POST"])
@role_required("admin")
def admin_send_to_supplier(order_id):
    order = Order.query.get(order_id)
    if not order:
        return jsonify({"detail": "Order not found", "code": "not_found"}), 404
    data = request.get_json(silent=True) or {}
    if data.get("supplier_order_id"):
        order.supplier_order_id = data["supplier_order_id"]
    if data.get("notes"):
        order.supplier_notes = data["notes"]
    order.fulfillment_status = Order.FulfillmentStatus.SENT_TO_SUPPLIER
    db.session.commit()
    log_audit(user_id=request.current_user.id, action="admin.order_sent_to_supplier",
              resource_type="order", resource_id=order_id,
              details=f"supplier_order_id={order.supplier_order_id}", meta=get_request_meta())
    return jsonify(order.to_dict(include_items=True)), 200


@api_bp.route("/admin/dropship/dashboard", methods=["GET"])
@role_required("admin")
def admin_dropship_dashboard():
    from sqlalchemy import func
    results = db.session.query(
        Supplier.name,
        Supplier.id,
        func.count(Order.id).label("total_orders"),
        func.sum(func.cast(Order.total, db.Numeric(10, 2))).label("total_revenue"),
    ).join(Order, Order.supplier_id == Supplier.id).filter(
        Order.fulfillment_status != "n/a"
    ).group_by(Supplier.id, Supplier.name).all()
    pending = Order.query.filter(
        Order.fulfillment_status.in_([Order.FulfillmentStatus.NEW,
                                       Order.FulfillmentStatus.SENT_TO_SUPPLIER])
    ).count()
    return jsonify({
        "suppliers": [{"name": r.name, "id": r.id, "total_orders": r.total_orders,
                       "total_revenue": float(r.total_revenue or 0)} for r in results],
        "pending_dropship_orders": pending,
    }), 200

### Categories

@api_bp.route("/admin/categories", methods=["GET"])
@role_required("admin")
def admin_list_categories():
    cats = Category.query.order_by(Category.display_order.asc()).all()
    return jsonify({"items": [c.to_dict() for c in cats]}), 200


### Products

@api_bp.route("/admin/products", methods=["GET"])
@role_required("admin")
def admin_list_products():
    page = max(1, int(request.args.get("page", 1)))
    per_page = min(100, max(1, int(request.args.get("per_page", 20))))
    q = Product.query
    sq = request.args.get("q")
    if sq:
        pat = f"%{sq}%"
        q = q.filter(db.or_(Product.name.ilike(pat), Product.sku.ilike(pat), Product.description.ilike(pat)))
    cs = request.args.get("category")
    if cs:
        cat = Category.query.filter_by(slug=cs).first()
        if cat:
            q = q.filter(Product.category_id == cat.id)
    ia = request.args.get("is_active")
    if ia == "false":
        q = q.filter(Product.is_active.is_(False))
    elif ia != "all":
        q = q.filter(Product.is_active.is_(True))
    sr = request.args.get("sort", "newest")
    if sr == "price_asc":
        q = q.order_by(Product.price.asc())
    elif sr == "price_desc":
        q = q.order_by(Product.price.desc())
    elif sr == "name":
        q = q.order_by(Product.name.asc())
    else:
        q = q.order_by(Product.created_at.desc())
    pp = q.paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        "items": [s.to_dict() for s in pp.items],
        "total": pp.total, "page": pp.page, "per_page": pp.per_page, "pages": pp.pages,
    }), 200
@api_bp.route("/admin/products", methods=["POST"])
@role_required("admin")
def admin_create_product():
    data = request.get_json(silent=True) or {}
    for f in ["name", "sku", "price"]:
        if not data.get(f):
            return jsonify({"detail": f + " is required", "code": "missing_field"}), 400
    if Product.query.filter_by(sku=data["sku"]).first():
        return jsonify({"detail": "SKU already exists", "code": "duplicate_sku"}), 409
    cat = None
    if data.get("category"):
        cat = Category.query.filter_by(slug=data["category"]).first()
        if not cat:
            return jsonify({"detail": "Invalid category", "code": "invalid_category"}), 400
    sid = data.get("supplier_id")
    if sid and not Supplier.query.get(sid):
        return jsonify({"detail": "Supplier not found", "code": "invalid_supplier"}), 400
    tags = data.get("tags", [])
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",") if t.strip()]
    slug = str(data.get("slug", data["name"]).lower().replace(" ", "-").replace("&", "and")[:255])
    p2 = Product(
        id=str(data.get("id", data["sku"])),
        sku=str(data["sku"]).strip(),
        slug=slug,
        name=str(data["name"]).strip(),
        description=data.get("description"),
        category_id=cat.id if cat else None,
        price=float(data["price"]),
        discount_price=float(data["discount_price"]) if data.get("discount_price") else None,
        currency=data.get("currency", "GHS"),
        stock=int(data.get("stock", 0)),
        image=data.get("image"),
        images=data.get("images") or [data.get("image")] if data.get("image") else [],
        material=data.get("material"),
        color=data.get("color"),
        weight_grams=float(data["weight_grams"]) if data.get("weight_grams") else None,
        dimensions=data.get("dimensions"),
        variants=data.get("variants", []),
        is_new=bool(data.get("is_new", False)),
        is_best=bool(data.get("is_best", False)),
        is_featured=bool(data.get("is_featured", False)),
        is_active=bool(data.get("is_active", True)),
        tags=tags,
        fulfillment_mode=data.get("fulfillment_mode", "in_stock"),
        supplier_id=sid,
        cost_price=float(data["cost_price"]) if data.get("cost_price") else None,
    )
    db.session.add(p2)
    db.session.commit()
    log_audit(user_id=request.current_user.id, action="admin.product_created",
              resource_type="product", resource_id=p2.id, details=f"name={p2.name}", meta=get_request_meta())
    return jsonify(p2.to_dict(include_cost=True)), 201


@api_bp.route("/admin/products/<product_id>", methods=["GET"])
@role_required("admin")
def admin_get_product(product_id):
    p2 = Product.query.get(product_id)
    if not p2:
        return jsonify({"detail": "Product not found", "code": "not_found"}), 404
    return jsonify(p2.to_dict(include_cost=True)), 200
@api_bp.route("/admin/products/<product_id>", methods=["PUT"])
@role_required("admin")
def admin_update_product(product_id):
    p2 = Product.query.get(product_id)
    if not p2:
        return jsonify({"detail": "Product not found", "code": "not_found"}), 404
    d = request.get_json(silent=True) or {}
    if "name" in d:
        p2.name = str(d["name"]).strip()
    if "sku" in d:
        if Product.query.filter(Product.sku == d["sku"], Product.id != product_id).first():
            return jsonify({"detail": "SKU already in use", "code": "duplicate_sku"}), 409
        p2.sku = str(d["sku"]).strip()
    if "slug" in d:
        p2.slug = str(d["slug"]).strip()[:255]
    if "description" in d:
        p2.description = d["description"]
    if "category" in d:
        cat = Category.query.filter_by(slug=d["category"]).first()
        p2.category_id = cat.id if cat else None
    if "price" in d:
        p2.price = float(d["price"])
    if "discount_price" in d:
        p2.discount_price = float(d["discount_price"]) if d["discount_price"] else None
    if "currency" in d:
        p2.currency = d["currency"]
    if "stock" in d:
        p2.stock = int(d["stock"])
    if "image" in d:
        p2.image = d["image"]
    if "images" in d:
        p2.images = d["images"]
    if "material" in d:
        p2.material = d["material"]
    if "color" in d:
        p2.color = d["color"]
    if "weight_grams" in d:
        p2.weight_grams = float(d["weight_grams"]) if d["weight_grams"] else None
    if "dimensions" in d:
        p2.dimensions = d["dimensions"]
    if "variants" in d:
        p2.variants = d["variants"]
    if "tags" in d:
        tags = d["tags"]
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(",") if t.strip()]
        p2.tags = tags
    if "is_new" in d:
        p2.is_new = bool(d["is_new"])
    if "is_best" in d:
        p2.is_best = bool(d["is_best"])
    if "is_featured" in d:
        p2.is_featured = bool(d["is_featured"])
    if "is_active" in d:
        p2.is_active = bool(d["is_active"])
    if "fulfillment_mode" in d:
        p2.fulfillment_mode = d["fulfillment_mode"]
    if "supplier_id" in d:
        if d["supplier_id"] and not Supplier.query.get(d["supplier_id"]):
            return jsonify({"detail": "Supplier not found", "code": "invalid_supplier"}), 400
        p2.supplier_id = d["supplier_id"]
    if "cost_price" in d:
        p2.cost_price = float(d["cost_price"]) if d["cost_price"] else None
    db.session.commit()
    log_audit(user_id=request.current_user.id, action="admin.product_updated",
              resource_type="product", resource_id=p2.id, meta=get_request_meta())
    return jsonify(p2.to_dict(include_cost=True)), 200


@api_bp.route("/admin/products/<product_id>", methods=["DELETE"])
@role_required("admin")
def admin_delete_product(product_id):
    p2 = Product.query.get(product_id)
    if not p2:
        return jsonify({"detail": "Product not found", "code": "not_found"}), 404
    p2.is_active = False
    db.session.commit()
    log_audit(user_id=request.current_user.id, action="admin.product_deleted",
              resource_type="product", resource_id=product_id, meta=get_request_meta())
    return jsonify({"message": "Product deactivated"}), 200


### Orders / Users (lightweight listings for admin UI)

@api_bp.route("/admin/orders", methods=["GET"])
@role_required("admin")
def admin_list_orders():
    """Return a paginated list of orders for the admin Orders page."""
    from backend.models import User
    page = max(1, int(request.args.get("page", 1)))
    per_page = min(100, max(1, int(request.args.get("per_page", 20))))
    q = Order.query.order_by(Order.created_at.desc())
    total = q.count()
    rows = q.offset((page - 1) * per_page).limit(per_page).all()
    out = []
    for o in rows:
        try:
            user = User.query.get(o.user_id) if o.user_id else None
            user_name = user.name if user and hasattr(user, "name") else (getattr(user, "email", "") if user else "")
        except Exception:
            user_name = ""
        out.append({
            "id": o.id,
            "order_number": getattr(o, "order_number", None) or o.id[:8],
            "user_id": o.user_id,
            "user_name": user_name,
            "user_email": getattr(user, "email", "") if user else "",
            "status": o.status,
            "total": float(getattr(o, "total", 0) or 0),
            "created_at": o.created_at.isoformat() if o.created_at else None,
        })
    return jsonify({"items": out, "total": total, "page": page, "per_page": per_page}), 200


@api_bp.route("/admin/orders/<order_id>/status", methods=["PUT"])
@role_required("admin")
def admin_update_order_status(order_id):
    """Update an order's status (e.g., pending -> paid -> shipped -> delivered)."""
    o = Order.query.get(order_id)
    if not o:
        return jsonify({"detail": "Order not found", "code": "not_found"}), 404
    d = request.get_json(silent=True) or {}
    new_status = (d.get("status") or "").strip()
    if not new_status:
        return jsonify({"detail": "status is required"}), 400
    o.status = new_status
    db.session.commit()
    log_audit(user_id=request.current_user.id, action="admin.order_status_updated",
              resource_type="order", resource_id=order_id,
              meta={**get_request_meta(), "new_status": new_status})
    return jsonify({"id": o.id, "status": o.status}), 200


@api_bp.route("/admin/users", methods=["GET"])
@role_required("admin")
def admin_list_users():
    """Return a paginated list of users for the admin Users page."""
    from backend.models import User
    page = max(1, int(request.args.get("page", 1)))
    per_page = min(100, max(1, int(request.args.get("per_page", 20))))
    q = User.query.order_by(User.created_at.desc())
    total = q.count()
    rows = q.offset((page - 1) * per_page).limit(per_page).all()
    out = []
    for u in rows:
        out.append({
            "id": u.id,
            "name": getattr(u, "name", "") or (u.email.split("@")[0] if u.email else ""),
            "email": u.email,
            "role": getattr(u, "role", "user"),
            "is_active": getattr(u, "is_active", True),
            "is_verified": getattr(u, "is_verified", False),
            "created_at": u.created_at.isoformat() if getattr(u, "created_at", None) else None,
        })
    return jsonify({"items": out, "total": total, "page": page, "per_page": per_page}), 200

