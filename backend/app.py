"""
Aurum Ghana - Flask application factory
"""
import os
import logging
from datetime import timedelta
from flask import Flask, jsonify, request
from backend.config import config
from backend.extensions import db, jwt, bcrypt, migrate, limiter


def create_app(config_name=None):
    config_name = config_name or os.getenv("FLASK_ENV", "development")
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Refuse to boot with insecure default signing keys in production.
    _cfg = config[config_name]
    _cfg.validate_secrets()

    # Init extensions
    db.init_app(app)
    jwt.init_app(app)
    bcrypt.init_app(app)
    migrate.init_app(app, db)
    limiter.init_app(app)

    # CORS
    from flask_cors import CORS
    CORS(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}},
         supports_credentials=True, allow_headers=["Content-Type", "Authorization", "X-CSRF-Token", "X-Request-ID"],
         methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])

    # JWT setup
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = app.config["JWT_ACCESS_TOKEN_TTL"]
    app.config["JWT_REFRESH_TOKEN_EXPIRES"] = app.config["JWT_REFRESH_TOKEN_TTL"]
    app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
    app.config["JWT_COOKIE_SECURE"] = app.config.get("JWT_COOKIE_SECURE", False)
    app.config["JWT_COOKIE_SAMESITE"] = app.config.get("JWT_COOKIE_SAMESITE", "Lax")
    app.config["JWT_COOKIE_CSRF_PROTECT"] = app.config.get("JWT_COOKIE_CSRF_PROTECT", True)
    app.config["JWT_CSRF_IN_COOKIES"] = True

    # Register blueprints
    from backend.api import api_bp
    from backend.api.webhooks import api_bp as webhooks_bp  # already in api_bp
    app.register_blueprint(api_bp)

    # Health check
    @app.route("/health")
    def health():
        return jsonify({"status": "ok", "service": "autum-luxe-api"}), 200

    # Root
    @app.route("/")
    def index():
        return jsonify({
            "name": "AUTUM LUXE API",
            "version": "1.0.0",
            "docs": "/api/v1",
        }), 200

    # Global error handlers
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"detail": "Not found", "code": "not_found"}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"detail": "Method not allowed", "code": "method_not_allowed"}), 405

    @app.errorhandler(500)
    def server_error(e):
        app.logger.error(f"Server error: {e}")
        return jsonify({"detail": "Internal server error", "code": "server_error"}), 500

    @app.errorhandler(429)
    def rate_limited(e):
        return jsonify({"detail": "Too many requests. Please try again later.", "code": "rate_limited"}), 429

    # Request logging
    @app.before_request
    def log_request():
        if not request.path.startswith("/static") and not request.path.startswith("/health"):
            app.logger.debug(f"{request.method} {request.path} from {request.remote_addr}")


    # Security headers: protect against common attacks (XSS, clickjacking,
    # MIME sniffing, referrer leakage).
    @app.after_request
    def _security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        # HSTS only when serving over HTTPS
        if request.is_secure:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        # Don't expose tokens via referrer if linked from external sites
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
        return response

    # HTTPS enforcement: in production, redirect HTTP to HTTPS
    @app.before_request
    def _enforce_https():
        if app.config.get("FLASK_ENV") == "production":
            if not request.is_secure and not request.headers.get("X-Forwarded-Proto") == "https":
                url = request.url.replace("http://", "https://", 1)
                return jsonify({"detail": "HTTPS required", "code": "https_required", "url": url}), 301

    # JWT error handlers
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({"detail": "Token expired", "code": "token_expired"}), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(reason):
        return jsonify({"detail": "Invalid token", "code": "invalid_token", "reason": reason}), 401

    @jwt.unauthorized_loader
    def missing_token_callback(reason):
        return jsonify({"detail": "Authorization required", "code": "missing_token", "reason": reason}), 401

    # Configure logging
    if not app.debug:
        logging.basicConfig(level=app.config.get("LOG_LEVEL", "INFO"))

    return app


# WSGI entry point
if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=app.config.get("DEBUG", False))
