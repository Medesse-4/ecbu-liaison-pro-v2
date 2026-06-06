from flask import Blueprint, render_template
from flask_login import login_required, current_user
from extensions import db
from app.models import Notification
from app.utils import utcnow

bp = Blueprint("notifications", __name__, url_prefix="/notifications")

@bp.route("/")
@login_required
def index():
    rows = Notification.query.filter((Notification.user_id == current_user.id) | (Notification.role_target == current_user.role)).order_by(Notification.id.desc()).limit(100).all()
    for n in rows:
        if not n.seen_at:
            n.seen_at = utcnow()
    db.session.commit()
    return render_template("notifications/index.html", rows=rows)
