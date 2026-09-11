"""
Aurum Ghana - User model
"""
import uuid
import secrets
from datetime import datetime, timezone
from backend.extensions import db


def generate_uuid():
    return str(uuid.uuid4())


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    role = db.Column(db.String(20), nullable=False, default="customer")  # customer | admin
    is_verified = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    mfa_enabled = db.Column(db.Boolean, default=False)
    mfa_secret = db.Column(db.String(32), nullable=True)
    last_login = db.Column(db.DateTime(timezone=True), nullable=True)
    # Account lockout: per-account brute-force protection
    failed_login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime(timezone=True), nullable=True)
    # Email OTP (admin second factor): random 6-digit code emailed at login
    email_otp_code = db.Column(db.String(6), nullable=True)
    email_otp_expires_at = db.Column(db.DateTime(timezone=True), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    addresses = db.relationship("Address", back_populates="user", lazy="dynamic", cascade="all, delete-orphan")
    orders = db.relationship("Order", back_populates="user", lazy="dynamic", cascade="all, delete-orphan")
    cart_items = db.relationship("CartItem", back_populates="user", lazy="dynamic", cascade="all, delete-orphan")
    verification_tokens = db.relationship("VerificationToken", back_populates="user", lazy="dynamic", cascade="all, delete-orphan")
    reviews = db.relationship("Review", foreign_keys="Review.user_id", back_populates="user", lazy="dynamic", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.email}>"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def to_dict(self, include_sensitive=False):
        d = {
            "id": self.id,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": self.full_name,
            "phone": self.phone,
            "role": self.role,
            "is_verified": self.is_verified,
            "mfa_enabled": self.mfa_enabled,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_sensitive:
            d["last_login"] = self.last_login.isoformat() if self.last_login else None
        return d


class Address(db.Model):
    __tablename__ = "addresses"

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    user_id = db.Column(db.String(36), db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    label = db.Column(db.String(50), default="Home")  # Home | Work | Other
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    street = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    region = db.Column(db.String(100), nullable=False)  # Greater Accra, Ashanti, etc.
    postal_code = db.Column(db.String(20), nullable=True)
    country = db.Column(db.String(100), default="Ghana")
    is_default = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = db.relationship("User", back_populates="addresses")

    def to_dict(self):
        return {
            "id": self.id,
            "label": self.label,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": f"{self.first_name} {self.last_name}",
            "phone": self.phone,
            "street": self.street,
            "city": self.city,
            "region": self.region,
            "postal_code": self.postal_code,
            "country": self.country,
            "is_default": self.is_default,
        }


class VerificationToken(db.Model):
    __tablename__ = "verification_tokens"

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    user_id = db.Column(db.String(36), db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token = db.Column(db.String(255), unique=True, nullable=False, index=True)
    token_type = db.Column(db.String(20), nullable=False)  # email_verification | password_reset
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    used_at = db.Column(db.DateTime(timezone=True), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = db.relationship("User", back_populates="verification_tokens")

    @staticmethod
    def generate_token(token_type: str, user_id: str, ttl_hours: int = 24) -> "VerificationToken":
        from datetime import timedelta
        token_str = secrets.token_urlsafe(32)
        return VerificationToken(
            token=token_str,
            user_id=user_id,
            token_type=token_type,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=ttl_hours),
        )


class MfaSecret(db.Model):
    __tablename__ = "mfa_secrets"

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    user_id = db.Column(db.String(36), db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    secret = db.Column(db.String(32), nullable=False)
    backup_codes = db.Column(db.JSON, nullable=True)  # list of hashed backup codes
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
