"""
AUTUM LUXE - Supplier model for dropshipping
"""
import uuid
from datetime import datetime, timezone
from backend.extensions import db


def generate_uuid():
    return str(uuid.uuid4())


class Supplier(db.Model):
    __tablename__ = "suppliers"

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    name = db.Column(db.String(255), nullable=False)
    country = db.Column(db.String(100), nullable=True)
    contact_name = db.Column(db.String(255), nullable=True)
    contact_email = db.Column(db.String(255), nullable=True)
    contact_phone = db.Column(db.String(50), nullable=True)
    address = db.Column(db.Text, nullable=True)
    api_endpoint = db.Column(db.String(500), nullable=True)   # for future API integration
    api_key = db.Column(db.String(255), nullable=True)        # for future API integration
    notes = db.Column(db.Text, nullable=True)
    lead_time_days = db.Column(db.Integer, default=7)          # typical fulfillment time
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    products = db.relationship("Product", back_populates="supplier", lazy="dynamic")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "country": self.country,
            "contact_name": self.contact_name,
            "contact_email": self.contact_email,
            "contact_phone": self.contact_phone,
            "address": self.address,
            "api_endpoint": self.api_endpoint,
            "lead_time_days": self.lead_time_days,
            "notes": self.notes,
            "is_active": self.is_active,
            "product_count": self.products.count(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
