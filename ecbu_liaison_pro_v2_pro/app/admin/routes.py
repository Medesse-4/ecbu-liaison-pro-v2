from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from extensions import db
from app.models import User, EcbuRequest, Sample, QualityChecklist, LabResult, Antibiogram, NonConformity, CapaAction, Notification, Ticket
from app.utils import audit, role_required, utcnow

bp = Blueprint("admin", __name__, url_prefix="/admin")

@bp.route("/users")
@login_required
@role_required("admin")
def users():
    rows = User.query.order_by(User.is_admin_approved, User.role, User.name).all()
    return render_template("admin/users.html", users=rows)

@bp.route("/users/<int:user_id>/approve", methods=["POST"])
@login_required
@role_required("admin")
def approve(user_id):
    user = db.session.get(User, user_id)
    if user and user.role != "admin" and not user.deleted_at:
        old = {"active": user.is_active, "approved": user.is_admin_approved}
        user.is_admin_approved = True
        user.is_active = True
        db.session.commit()
        audit("validation_compte", "user", user.id, old, {"active": True, "approved": True})
        flash("Compte validé.", "success")
    return redirect(url_for("admin.users"))

@bp.route("/users/<int:user_id>/toggle", methods=["POST"])
@login_required
@role_required("admin")
def toggle(user_id):
    user = db.session.get(User, user_id)
    if user and user.role != "admin" and not user.deleted_at:
        old = {"active": user.is_active}
        user.is_active = not user.is_active
        db.session.commit()
        audit("activation_suspension_compte", "user", user.id, old, {"active": user.is_active})
        flash("Statut du compte mis à jour.", "success")
    return redirect(url_for("admin.users"))

@bp.route("/users/<int:user_id>/delete", methods=["POST"])
@login_required
@role_required("admin")
def delete_user(user_id):
    user = db.session.get(User, user_id)
    if user and user.role != "admin":
        user.is_active = False
        user.deleted_at = utcnow()
        user.deletion_confirmed_by_id = current_user.id
        user.deletion_confirmed_at = utcnow()
        db.session.commit()
        audit("suppression_logique_compte", "user", user.id)
        flash("Compte supprimé. Les traces de sécurité restent conservées.", "success")
    return redirect(url_for("admin.users"))

@bp.route("/users/<int:user_id>/confirm-delete-request", methods=["POST"])
@login_required
@role_required("admin")
def confirm_delete_request(user_id):
    return delete_user(user_id)

@bp.route("/reset-site", methods=["GET", "POST"])
@login_required
@role_required("admin")
def reset_site():
    """Réinitialisation opérationnelle sans affichage des données médicales."""
    if request.method == "POST":
        phrase = request.form.get("confirmation", "").strip()
        if phrase != "REINITIALISER":
            flash("Confirmation incorrecte. Tapez exactement REINITIALISER.", "danger")
            return redirect(url_for("admin.reset_site"))
        # Ordre volontaire pour respecter les contraintes de clés étrangères.
        for model in [Antibiogram, LabResult, QualityChecklist, Sample, CapaAction, NonConformity, EcbuRequest, Notification, Ticket]:
            db.session.query(model).delete(synchronize_session=False)
        db.session.commit()
        audit("reinitialisation_site_sans_consultation_donnees", "system", "clinical_operational_data")
        flash("Le site a été réinitialisé. Les utilisateurs et l’audit de sécurité sont conservés.", "success")
        return redirect(url_for("dashboard.home"))
    return render_template("admin/reset_site.html")
