import uuid
from datetime import datetime, timezone
from backend.extensions import db


class Review(db.Model):
    __tablename__ = "reviews"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    product_id = db.Column(db.String(50), db.ForeignKey("products.id"), nullable=False, index=True)
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, index=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    verified_purchase = db.Column(db.Boolean, default=False, nullable=False)
    is_approved = db.Column(db.Boolean, default=False, nullable=False)
    approved_by_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=True)
    approved_at = db.Column(db.DateTime(timezone=True), nullable=True)
    reviewer_name = db.Column(db.String(255), nullable=False)
    reviewer_email = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(20), default="pending", nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    published_at = db.Column(db.DateTime(timezone=True), nullable=True)

    product = db.relationship("Product", back_populates="reviews")
    user = db.relationship("User", foreign_keys=[user_id], back_populates="reviews")
    approver = db.relationship("User", foreign_keys=[approved_by_id], backref="approved_reviews")
    order_item = db.relationship("OrderItem", back_populates="review", uselist=False)

    def to_dict(self, include_user=False):
        base = {
            "id": self.id, "product_id": self.product_id, "title": self.title,
            "content": self.content, "rating": self.rating,
            "verified_purchase": self.verified_purchase, "is_approved": self.is_approved,
            "status": self.status, "reviewer_name": self.reviewer_name,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "created_at": self.created_at.isoformat(),
        }
        if include_user and self.user:
            base.update({"user_id": self.user.id, "user_name": self.user.name, "user_email": self.user.email})
        return base

    def __repr__(self):
        return f"<Review {self.id} by {self.reviewer_name} - Rating: {self.rating}/5>"