"""
Aurum Ghana - Audit logging
"""
import json
from backend.extensions import db
from backend.models import AuditLog


def log_audit(user_id=None, action: str = "", resource_type: str = "",
              resource_id: str = None, details: str = None, meta: dict = None):
    """
    Write an audit log entry. Fails silently to avoid breaking the main flow.
    """
    try:
        entry = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=json.dumps(details) if isinstance(details, (dict, list)) else details,
            ip_address=(meta or {}).get("ip"),
            user_agent=(meta or {}).get("user_agent"),
        )
        db.session.add(entry)
        db.session.commit()
    except Exception:
        db.session.rollback()
