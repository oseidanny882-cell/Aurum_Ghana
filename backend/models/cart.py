"""
Aurum Ghana - Cart models
Server-side cart persistence for logged-in users.
The frontend uses localStorage for guest carts; the backend syncs when the user logs in.
"""
import uuid
from datetime import datetime, timezone
from backend.extensions import db


def generate_uuid():
    return str(uuid.uuid4())


class CartItem(db.Model):
    __tablename__ = "cart_items"

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    user_id = db.Column(db.String(36), db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = db.Column(db.String(50), db.ForeignKey("products.id"), nullable=False)
    variant_id = db.Column(db.String(50), nullable=True)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user = db.relationship("User", back_populates="cart_items")
    product = db.relationship("Product")

    def to_dict(self):
        p = self.product
        unit_price = float(p.discount_price) if p.discount_price else float(p.price)
        line_total = unit_price * self.quantity
        return {
            "id": self.id,
            "key": f"{p.id}_{self.variant_id or 'default'}",
            "product_id": p.id,
            "slug": p.slug,
            "variant_id": self.variant_id,
            "name": p.name,
            "image": p.image,
            "price": float(p.price),
            "discount_price": float(p.discount_price) if p.discount_price else None,
            "quantity": self.quantity,
            "stock": p.stock,
            "in_stock": p.stock >= self.quantity,
            "line_total": line_total,
            "unit_price": unit_price,
        }


class Cart:
    """In-memory aggregation helper, not a model. Used by service layer."""
    def __init__(self, items):
        self.items = items
        self.subtotal = sum(i.line_total for i in items)
        self.item_count = sum(i.quantity for i in items)
        self.delivery_fee = 0 if self.subtotal >= 500 or self.subtotal == 0 else 35
        self.discount = 0
        self.total = self.subtotal + self.delivery_fee - self.discount
