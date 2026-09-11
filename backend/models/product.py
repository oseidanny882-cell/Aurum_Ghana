"""
Aurum Ghana - Product and Category models
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import JSON
from backend.extensions import db


def generate_uuid():
    return str(uuid.uuid4())


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    slug = db.Column(db.String(100), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    image = db.Column(db.String(500), nullable=True)
    display_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    products = db.relationship("Product", back_populates="category", lazy="dynamic")

    def to_dict(self):
        return {
            "id": self.id,
            "slug": self.slug,
            "name": self.name,
            "description": self.description,
            "image": self.image,
            "display_order": self.display_order,
            "is_active": self.is_active,
        }


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.String(50), primary_key=True)  # SKU-style id e.g. "sku-rings-1"
    sku = db.Column(db.String(50), unique=True, nullable=False, index=True)
    slug = db.Column(db.String(255), unique=True, nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category_id = db.Column(db.String(36), db.ForeignKey("categories.id"), nullable=True)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    discount_price = db.Column(db.Numeric(10, 2), nullable=True)
    currency = db.Column(db.String(3), default="GHS")
    stock = db.Column(db.Integer, default=0)
    image = db.Column(db.String(500), nullable=True)
    images = db.Column(JSON, default=list)  # array of image URLs
    material = db.Column(db.String(100), nullable=True)
    color = db.Column(db.String(50), nullable=True)
    weight_grams = db.Column(db.Numeric(8, 2), nullable=True)
    dimensions = db.Column(db.String(100), nullable=True)
    variants = db.Column(JSON, default=list)  # [{id, name, price, stock}]
    is_new = db.Column(db.Boolean, default=False)
    is_best = db.Column(db.Boolean, default=False)
    is_featured = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    tags = db.Column(JSON, default=list)
    rating_avg = db.Column(db.Numeric(3, 2), default=0)
    review_count = db.Column(db.Integer, default=0)
    view_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    category = db.relationship("Category", back_populates="products")
    order_items = db.relationship("OrderItem", back_populates="product", lazy="dynamic")
    reviews = db.relationship("Review", back_populates="product", lazy="dynamic")
    supplier = db.relationship("Supplier", back_populates="products")

    # Dropshipping fields
    fulfillment_mode = db.Column(db.String(20), default="in_stock")   # "in_stock" | "dropship"
    supplier_id = db.Column(db.String(36), db.ForeignKey("suppliers.id"), nullable=True)
    cost_price = db.Column(db.Numeric(10, 2), nullable=True)          # what we pay the supplier

    def to_dict(self, include_category=True, include_cost=False):
        base = {
            "id": self.id,
            "sku": self.sku,
            "slug": self.slug,
            "name": self.name,
            "description": self.description,
            "price": float(self.price),
            "discount_price": float(self.discount_price) if self.discount_price else None,
            "currency": self.currency,
            "stock": self.stock,
            "image": self.image,
            "images": self.images or [self.image] if self.image else [],
            "material": self.material,
            "color": self.color,
            "variants": self.variants or [],
            "is_new": self.is_new,
            "is_best": self.is_best,
            "is_active": self.is_active,
            "is_featured": self.is_featured,
            "rating_avg": float(self.rating_avg) if self.rating_avg else 0,
            "review_count": self.review_count,
            "in_stock": self.stock > 0,
            # Dropshipping fields
            "fulfillment_mode": self.fulfillment_mode,
            "supplier_id": self.supplier_id,
            "supplier_name": self.supplier.name if self.supplier else None,
            "is_dropship": self.fulfillment_mode == "dropship",
        }
        if include_cost:
            base["cost_price"] = float(self.cost_price) if self.cost_price else None
        if include_category:
            base["category"] = self.category.slug if self.category else None
            base["category_name"] = self.category.name if self.category else None
        return base
