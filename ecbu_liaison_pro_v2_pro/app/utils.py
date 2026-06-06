from datetime import datetime, timezone
from flask import request
from flask_login import current_user
from extensions import db
from app.models import AuditLog, Notification
import hashlib, json


def utcnow():
    return datetime.now(timezone.utc)


def client_ip():
    forwarded = request.headers.get("X-Forwarded-For", "") if request else ""
    return (forwarded.split(",")[0].strip() or request.remote_addr or "") if request else ""


def audit(action, entity_type=None, entity_id=None, old_value=None, new_value=None):
    previous = AuditLog.query.order_by(AuditLog.id.desc()).first()
    payload = json.dumps({"action": action, "entity_type": entity_type, "entity_id": entity_id, "old": old_value, "new": new_value}, ensure_ascii=False, sort_keys=True, default=str)
    base = f"{previous.hash_chain if previous else ''}|{payload}|{utcnow().isoformat()}"
    log = AuditLog(user_id=getattr(current_user, 'id', None) if current_user else None, user_name=getattr(current_user, 'name', ''), action=action, entity_type=entity_type, entity_id=str(entity_id or ''), old_value=json.dumps(old_value, ensure_ascii=False, default=str) if old_value is not None else None, new_value=json.dumps(new_value, ensure_ascii=False, default=str) if new_value is not None else None, ip_address=client_ip(), hash_chain=hashlib.sha256(base.encode()).hexdigest())
    db.session.add(log)
    db.session.commit()


def notify(title, message, user_id=None, role_target=None, level="info"):
    db.session.add(Notification(title=title, message=message, user_id=user_id, role_target=role_target, level=level))
    db.session.commit()


ROLE_LABELS = {
    "admin": "Administrateur du site",
    "prescripteur": "Prescripteur",
    "laboratoire": "Laboratoire",
    "chef_labo": "Chef laboratoire",
}

CLINICAL_ROLES = {"prescripteur", "laboratoire", "chef_labo"}
LAB_ROLES = {"laboratoire", "chef_labo"}
QUALITY_ROLES = {"laboratoire", "chef_labo"}

def has_role(*roles):
    return getattr(current_user, "is_authenticated", False) and getattr(current_user, "role", None) in roles

def role_required(*roles):
    from functools import wraps
    from flask import render_template
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not has_role(*roles):
                audit("acces_refuse", new_value={"route": request.path, "roles_autorises": roles})
                return render_template("errors/403.html"), 403
            return func(*args, **kwargs)
        return wrapper
    return decorator

def clinical_access_for_request(req):
    if not getattr(current_user, "is_authenticated", False):
        return False
    if current_user.role == "prescripteur":
        return req.created_by_id == current_user.id
    if current_user.role in {"laboratoire", "chef_labo"}:
        return True
    return False
