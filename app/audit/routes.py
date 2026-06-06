from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from app.utils import role_required
from app.models import AuditLog

bp = Blueprint("audit", __name__, url_prefix="/audit")

@bp.route("/")
@login_required
@role_required("admin")
def index():
    page = request.args.get("page", 1, type=int)
    pagination = AuditLog.query.order_by(AuditLog.id.desc()).paginate(page=page, per_page=50, error_out=False)
    return render_template("audit/index.html", pagination=pagination)
