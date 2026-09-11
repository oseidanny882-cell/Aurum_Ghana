"""
Aurum Ghana - Payment model
"""
import uuid
from datetime import datetime, timezone
from backend.extensions import db


def generate_uuid():
    return str(uuid.uuid4())


class Payment(db.Model):
    __tablename__ = "payments"

    class Status:
        PENDING = "pending"
        PROCESSING = "processing"
        SUCCESS = "success"
        FAILED = "failed"
        REFUNDED = "refunded"

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    order_id = db.Column(db.String(36), db.ForeignKey("orders.id", ondelete="SET NULL"), nullable=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(3), default="GHS")
    status = db.Column(db.String(20), default=Status.PENDING)
    provider = db.Column(db.String(20), default="paystack")
    provider_reference = db.Column(db.String(255), nullable=True, index=True)
    provider_response = db.Column(db.Text, nullable=True)
    fees = db.Column(db.Numeric(10, 2), default=0)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    order = db.relationship("Order", back_populates="payment")

    def to_dict(self):
        return {
            "id": self.id,
            "order_id": self.order_id,
            "amount": float(self.amount),
            "currency": self.currency,
            "status": self.status,
            "provider": self.provider,
            "provider_reference": self.provider_reference,
            "fees": float(self.fees),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
