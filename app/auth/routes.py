from datetime import timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, current_user, login_required
from extensions import db, limiter
from app.forms import LoginForm, RegisterForm
from app.models import User
from app.security import verify_password, hash_password, password_is_strong
from app.utils import utcnow, audit, notify

bp = Blueprint("auth", __name__)

def is_professional_email(email):
    """Validation simple : adresse structurée, non fictive côté formulaire.
    La validation définitive est réalisée par l’administrateur du site.
    """
    return bool(email and "@" in email and "." in email.rsplit("@", 1)[-1])

@bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.home"))
    return redirect(url_for("auth.login"))

@bp.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower().strip()).first()
        if not user or not verify_password(user.password_hash, form.password.data):
            if user:
                user.failed_login_count += 1
                if user.failed_login_count >= 5:
                    user.locked_until = utcnow() + timedelta(minutes=20)
                db.session.commit()
            flash("Identifiants invalides.", "danger")
            return render_template("auth/login.html", form=form), 401
        if user.locked_until and user.locked_until > utcnow():
            flash("Compte temporairement verrouillé.", "danger")
            return render_template("auth/login.html", form=form), 403
        if not user.is_admin_approved or not user.is_active:
            flash("Compte en attente de validation administrateur.", "warning")
            return render_template("auth/login.html", form=form), 403
        user.failed_login_count = 0
        user.locked_until = None
        user.last_login_at = utcnow()
        db.session.commit()
        login_user(user, remember=False, fresh=True)
        audit("connexion")
        return redirect(url_for("dashboard.home"))
    return render_template("auth/login.html", form=form)

@bp.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        email = form.email.data.lower().strip()
        if not password_is_strong(form.password.data):
            flash("Mot de passe insuffisant : 10 caractères minimum avec majuscule, minuscule et chiffre.", "danger")
        elif not is_professional_email(email):
            flash("Utilisez une adresse email professionnelle réelle, pas une adresse personnelle publique.", "danger")
        elif User.query.filter_by(email=email).first():
            flash("Cette adresse email existe déjà.", "danger")
        else:
            user = User(name=form.name.data.strip(), email=email, password_hash=hash_password(form.password.data), role=form.role.data, service=form.service.data.strip(), email_token=None, is_active=False, is_email_verified=True, is_admin_approved=False)
            db.session.add(user)
            db.session.commit()
            notify("Nouveau compte à valider", f"Compte en attente : {user.email}", role_target="admin", level="warning")
            audit("creation_compte", "user", user.id)
            flash("Compte créé. Votre accès sera disponible après validation par l’administrateur.", "success")
            return redirect(url_for("auth.login"))
    return render_template("auth/register.html", form=form)

@bp.route("/verify-email/<token>")
def verify_email(token):
    user = User.query.filter_by(email_token=token).first()
    if not user:
        flash("Lien de vérification invalide ou expiré.", "danger")
        return redirect(url_for("auth.login"))
    user.is_email_verified = True
    user.email_token = None
    db.session.commit()
    audit("verification_email", "user", user.id)
    notify("Compte vérifié en attente de validation", user.email, role_target="admin", level="warning")
    flash("Adresse email vérifiée. Votre compte attend maintenant la validation administrateur.", "success")
    return redirect(url_for("auth.login"))

@bp.route("/logout")
def logout():
    audit("deconnexion")
    logout_user()
    return redirect(url_for("auth.login"))


@bp.route("/account/delete-request", methods=["GET", "POST"])
@login_required
def request_delete_account():
    if request.method == "POST":
        current_user.deletion_requested_at = utcnow()
        current_user.deletion_reason = request.form.get("reason", "").strip()
        db.session.commit()
        audit("demande_suppression_compte", "user", current_user.id, new_value={"reason": current_user.deletion_reason})
        notify("Demande de suppression de compte", f"{current_user.email} demande la suppression de son compte.", role_target="admin", level="warning")
        flash("Votre demande de suppression a été transmise à l’administrateur.", "success")
        return redirect(url_for("dashboard.home"))
    return render_template("auth/delete_request.html")
