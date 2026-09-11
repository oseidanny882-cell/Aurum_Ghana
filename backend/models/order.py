"""
Aurum Ghana - Order models
"""
import uuid, time, secrets
from datetime import datetime, timezone
from backend.extensions import db


def generate_uuid():
    return str(uuid.uuid4())


class Order(db.Model):
    __tablename__ = "orders"

    class Status:
        PENDING = "pending"
        CONFIRMED = "confirmed"
        PROCESSING = "processing"
        SHIPPED = "shipped"
        DELIVERED = "delivered"
        CANCELLED = "cancelled"
        REFUNDED = "refunded"
        CHOICES = [PENDING, CONFIRMED, PROCESSING, SHIPPED, DELIVERED, CANCELLED, REFUNDED]

    class PaymentStatus:
        PENDING = "pending"
        PAID = "paid"
        FAILED = "failed"
        REFUNDED = "refunded"

    class FulfillmentStatus:
        NEW = "new"                          # paid but not yet sent to supplier
        SENT_TO_SUPPLIER = "sent_to_supplier"
        SUPPLIER_CONFIRMED = "supplier_confirmed"
        SUPPLIER_SHIPPED = "supplier_shipped"
        DELIVERED = "delivered"
        FAILED = "failed"
        NOT_APPLICABLE = "n/a"               # for in-stock orders
        CHOICES = [NEW, SENT_TO_SUPPLIER, SUPPLIER_CONFIRMED, SUPPLIER_SHIPPED, DELIVERED, FAILED, NOT_APPLICABLE]

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    order_number = db.Column(db.String(20), unique=True, nullable=False, index=True)
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=True)
    status = db.Column(db.String(20), default=Status.PENDING)
    payment_status = db.Column(db.String(20), default=PaymentStatus.PENDING)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    delivery_fee = db.Column(db.Numeric(10, 2), default=0)
    discount = db.Column(db.Numeric(10, 2), default=0)
    total = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(3), default="GHS")
    payment_method = db.Column(db.String(20), nullable=True)
    payment_reference = db.Column(db.String(255), nullable=True)
    paystack_reference = db.Column(db.String(255), nullable=True, index=True)
    shipping_first_name = db.Column(db.String(100), nullable=False)
    shipping_last_name = db.Column(db.String(100), nullable=False)
    shipping_phone = db.Column(db.String(20), nullable=False)
    shipping_email = db.Column(db.String(255), nullable=True)
    shipping_street = db.Column(db.String(255), nullable=False)
    shipping_city = db.Column(db.String(100), nullable=False)
    shipping_region = db.Column(db.String(100), nullable=False)
    shipping_postal_code = db.Column(db.String(20), nullable=True)
    shipping_country = db.Column(db.String(100), default="Ghana")
    delivery_notes = db.Column(db.Text, nullable=True)
    billing_first_name = db.Column(db.String(100), nullable=True)
    billing_last_name = db.Column(db.String(100), nullable=True)
    billing_phone = db.Column(db.String(20), nullable=True)
    billing_street = db.Column(db.String(255), nullable=True)
    billing_city = db.Column(db.String(100), nullable=True)
    billing_region = db.Column(db.String(100), nullable=True)
    billing_postal_code = db.Column(db.String(20), nullable=True)
    tracking_number = db.Column(db.String(100), nullable=True)
    estimated_delivery = db.Column(db.Date, nullable=True)
    # Dropshipping fields
    supplier_id = db.Column(db.String(36), db.ForeignKey("suppliers.id"), nullable=True)
    fulfillment_status = db.Column(db.String(40), default="n/a")
    supplier_order_id = db.Column(db.String(100), nullable=True)  # supplier's reference for this order
    supplier_notes = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    confirmed_at = db.Column(db.DateTime(timezone=True), nullable=True)
    shipped_at = db.Column(db.DateTime(timezone=True), nullable=True)
    delivered_at = db.Column(db.DateTime(timezone=True), nullable=True)

    user = db.relationship("User", back_populates="orders")
    items = db.relationship("OrderItem", back_populates="order", lazy="dynamic", cascade="all, delete-orphan")
    payment = db.relationship("Payment", back_populates="order", uselist=False)
    supplier = db.relationship("Supplier", backref="orders")

    @staticmethod
    def generate_order_number():
        return f"AUR-{int(time.time())}{secrets.token_hex(2).upper()}"

    def to_dict(self, include_items=False, include_user=False):
        d = {
            "id": self.id, "order_number": self.order_number, "status": self.status,
            "payment_status": self.payment_status, "subtotal": float(self.subtotal),
            "delivery_fee": float(self.delivery_fee), "discount": float(self.discount),
            "total": float(self.total), "currency": self.currency,
            "payment_method": self.payment_method, "paystack_reference": self.paystack_reference,
            "shipping": {
                "first_name": self.shipping_first_name, "last_name": self.shipping_last_name,
                "phone": self.shipping_phone, "email": self.shipping_email,
                "street": self.shipping_street, "city": self.shipping_city,
                "region": self.shipping_region, "postal_code": self.shipping_postal_code,
                "country": self.shipping_country, "notes": self.delivery_notes,
            },
            "tracking_number": self.tracking_number,
            "estimated_delivery": self.estimated_delivery.isoformat() if self.estimated_delivery else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            # Dropshipping fields
            "fulfillment_status": self.fulfillment_status,
            "supplier_id": self.supplier_id,
            "supplier_name": self.supplier.name if self.supplier else None,
            "supplier_order_id": self.supplier_order_id,
            "supplier_notes": self.supplier_notes,
        }
        if include_items:
            d["items"] = [i.to_dict() for i in self.items]
        if include_user and self.user:
            d["user"] = self.user.to_dict()
        return d


class OrderItem(db.Model):
    __tablename__ = "order_items"
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    order_id = db.Column(db.String(36), db.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    product_id = db.Column(db.String(50), db.ForeignKey("products.id"), nullable=False)
    variant_id = db.Column(db.String(50), nullable=True)
    sku = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    image = db.Column(db.String(500), nullable=True)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    line_total = db.Column(db.Numeric(10, 2), nullable=False)
    cost_price = db.Column(db.Numeric(10, 2), nullable=True)  # snapshot of supplier cost
    order = db.relationship("Order", back_populates="items")
    product = db.relationship("Product", back_populates="order_items")
    review_id = db.Column(db.String(36), db.ForeignKey("reviews.id"), nullable=True, unique=True)
    review = db.relationship("Review", back_populates="order_item", uselist=False, foreign_keys=[review_id])

    def to_dict(self):
        return {
            "id": self.id, "product_id": self.product_id, "variant_id": self.variant_id,
            "sku": self.sku, "name": self.name, "image": self.image,
            "quantity": self.quantity, "unit_price": float(self.unit_price),
            "line_total": float(self.line_total),
            "cost_price": float(self.cost_price) if self.cost_price else None,
        }
