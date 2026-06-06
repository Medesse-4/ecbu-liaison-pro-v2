from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models import EcbuRequest, NonConformity, LabResult, Antibiogram, User, Sample

bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")

@bp.route("/")
@login_required
def home():
    if current_user.role == "admin":
        data = {
            "users": User.query.filter_by(deleted_at=None).count(),
            "pending_users": User.query.filter_by(is_admin_approved=False, deleted_at=None).count(),
            "active_users": User.query.filter_by(is_active=True, deleted_at=None).count(),
            "delete_requests": User.query.filter(User.deletion_requested_at.isnot(None), User.deleted_at.is_(None)).count(),
        }
        return render_template("dashboard/home.html", data=data, mode="admin")
    if current_user.role == "prescripteur":
        q = EcbuRequest.query.filter_by(created_by_id=current_user.id, deleted_at=None)
        data = {"my_requests": q.count(), "validated": q.filter_by(status="validated").count(), "pending": q.filter(EcbuRequest.status != "validated").count(), "rejected": q.filter_by(status="rejected").count()}
        return render_template("dashboard/home.html", data=data, mode="prescripteur")
    if current_user.role == "laboratoire":
        data = {"total_requests": EcbuRequest.query.filter_by(deleted_at=None).count(), "samples": Sample.query.count(), "validated": EcbuRequest.query.filter_by(status="validated", deleted_at=None).count(), "rejected": EcbuRequest.query.filter_by(status="rejected", deleted_at=None).count(), "non_conformities": NonConformity.query.count(), "resistant": Antibiogram.query.filter_by(interpretation="R").count()}
        return render_template("dashboard/home.html", data=data, mode="laboratoire")
    data = {"non_conformities": NonConformity.query.count(), "open_nc": NonConformity.query.filter_by(status="open").count()}
    return render_template("dashboard/home.html", data=data, mode="qualite")
