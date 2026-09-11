"""
Aurum Ghana - Newsletter API routes
"""
from flask import current_app, request, jsonify
from backend.api import api_bp
from backend.extensions import db, limiter
from backend.extensions import db
from backend.models import NewsletterSubscriber
from backend.utils.security import validate_email, get_request_meta
from backend.services.audit import log_audit


@api_bp.route("/newsletter", methods=["POST"])
@limiter.limit("10 per hour")
def newsletter_subscribe():
    """Subscribe an email to the newsletter. Idempotent: re-subscribing an
    existing (even previously unsubscribed) email re-activates it without
    leaking whether the address was already on the list."""
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()

    if not email or not validate_email(email):
        return jsonify({"detail": "A valid email address is required", "code": "invalid_email"}), 400

    sub = NewsletterSubscriber.query.filter_by(email=email).first()
    if sub is None:
        sub = NewsletterSubscriber(email=email, is_active=True)
        db.session.add(sub)
    elif not sub.is_active:
        sub.is_active = True
    db.session.commit()

    log_audit(action="newsletter.subscribed", resource_type="newsletter_subscriber",
              details=f"email={email}", meta=get_request_meta())

    return jsonify({"message": "Subscribed successfully. Welcome to the list!"}), 201


@api_bp.route("/newsletter/unsubscribe", methods=["POST"])
def newsletter_unsubscribe():
    """Opt an email out of the newsletter. No body/no email -> generic OK so
    the endpoint can't be used to probe which addresses are subscribed."""
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()

    if email and validate_email(email):
        sub = NewsletterSubscriber.query.filter_by(email=email).first()
        if sub:
            sub.is_active = False
            db.session.commit()
            log_audit(action="newsletter.unsubscribed", resource_type="newsletter_subscriber",
                      details=f"email={email}", meta=get_request_meta())

    return jsonify({"message": "You have been unsubscribed."}), 200
