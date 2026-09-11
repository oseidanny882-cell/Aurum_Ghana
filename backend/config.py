"""
Aurum Ghana - Flask configuration
"""
import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration."""
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-in-production")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "jwt-dev-secret-change-in-production")
    JWT_ACCESS_TOKEN_TTL = timedelta(minutes=int(os.getenv("JWT_ACCESS_TOKEN_TTL_MIN", 15)))
    JWT_REFRESH_TOKEN_TTL = timedelta(days=int(os.getenv("JWT_REFRESH_TOKEN_TTL_DAYS", 7)))

    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "postgresql+psycopg2://aurum:aurum@localhost:5432/aurum_ghana")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    _is_postgres = "postgresql" in (os.getenv("DATABASE_URL") or "").lower()
    SQLALCHEMY_ENGINE_OPTIONS = (
        {"pool_size": 10, "max_overflow": 20, "pool_pre_ping": True} if _is_postgres else {}
    )

    # Default CORS allowlist covers common local dev servers
    _DEFAULT_CORS = "http://localhost:8000,http://127.0.0.1:8000,http://localhost:5500,http://127.0.0.1:5500,http://localhost:8080,http://127.0.0.1:8080,http://localhost:5173,http://127.0.0.1:5173,https://oseidanny882-cell.github.io"
    CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", _DEFAULT_CORS).split(",") if o.strip()]
    FRONTEND_URL = os.getenv("FRONTEND_URL", "https://oseidanny882-cell.github.io/Aurum_Ghana")

    PAYSTACK_PUBLIC_KEY = os.getenv("PAYSTACK_PUBLIC_KEY", "")
    PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY", "")
    PAYSTACK_CALLBACK_URL = os.getenv("PAYSTACK_CALLBACK_URL", "https://oseidanny882-cell.github.io/Aurum_Ghana/payment-callback.html")
    PAYSTACK_WEBHOOK_SECRET = os.getenv("PAYSTACK_WEBHOOK_SECRET", "")

    # Admin MFA enforcement
    ADMIN_MFA_REQUIRED = os.getenv("ADMIN_MFA_REQUIRED", "true").lower() not in ("0", "false", "no")

    SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
    SMTP_USER = os.getenv("SMTP_USER", "")
    SMTP_PASS = os.getenv("SMTP_PASS", "")
    EMAIL_FROM = os.getenv("EMAIL_FROM", "noreply@aurum-ghana.local")

    RATELIMIT_DEFAULT = os.getenv("RATE_LIMIT_DEFAULT", "100 per hour")
    REDIS_URL = os.getenv("REDIS_URL", "")
    RATELIMIT_STORAGE_URL = os.getenv("RATELIMIT_STORAGE_URL", REDIS_URL or "memory://")
    RATELIMIT_STORAGE_URI = RATELIMIT_STORAGE_URL

    BCRYPT_LOG_ROUNDS = 12

    # CSRF
    WTF_CSRF_ENABLED = True

    # Pagination
    DEFAULT_PAGE_SIZE = 24
    MAX_PAGE_SIZE = 100

    # JWT Cookie settings (HttpOnly cookies for XSS protection)
    JWT_TOKEN_COOKIE = "access_token_cookie"
    JWT_REFRESH_COOKIE = "refresh_token_cookie"
    JWT_COOKIE_SECURE = os.getenv("JWT_COOKIE_SECURE", "false").lower() in ("1", "true", "yes")
    JWT_COOKIE_SAMESITE = os.getenv("JWT_COOKIE_SAMESITE", "Lax")
    JWT_COOKIE_CSRF_PROTECT = os.getenv("JWT_COOKIE_CSRF_PROTECT", "true").lower() in ("1", "true", "yes")
    JWT_CSRF_IN_COOKIES = False


    _DEV_DEFAULT_SECRET = "dev-secret-change-in-production"
    _DEV_DEFAULT_JWT = "jwt-dev-secret-change-in-production"

    @classmethod
    def validate_secrets(cls):
        """Refuse to boot with the well-known development signing keys."""
        if getattr(cls, "FLASK_ENV", "") != "production":
            return
        problems = []
        if not cls.SECRET_KEY or cls.SECRET_KEY == cls._DEV_DEFAULT_SECRET:
            problems.append("SECRET_KEY")
        if not cls.JWT_SECRET_KEY or cls.JWT_SECRET_KEY == cls._DEV_DEFAULT_JWT:
            problems.append("JWT_SECRET_KEY")
        if problems:
            raise RuntimeError(
                "Refusing to start in production: insecure default "
                f"signing {', '.join(problems)} detected. "
                "Set a strong, unique value in your .env / environment."
            )


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    FLASK_ENV = "development"
    JWT_COOKIE_SECURE = False


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    FLASK_ENV = "production"
    JWT_COOKIE_SECURE = True
    JWT_COOKIE_SAMESITE = "Strict"


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_ENGINE_OPTIONS = {}
    WTF_CSRF_ENABLED = False


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}
