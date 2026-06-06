from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy import or_
from extensions import db
from app.forms import InternalMessageForm
from app.models import InternalMessage, EcbuRequest
from app.utils import audit, notify

bp = Blueprint("chat", __name__, url_prefix="/messages")

def visible_messages_query():
    q = InternalMessage.query
    if current_user.role == "admin":
        return q.filter(or_(InternalMessage.sender_id == current_user.id, InternalMessage.recipient_role == "admin", InternalMessage.recipient_user_id == current_user.id))
    if current_user.role == "laboratoire" or current_user.role == "laboratoire":
        return q.filter(or_(InternalMessage.sender_id == current_user.id, InternalMessage.recipient_role.in_(["laboratoire"]), InternalMessage.recipient_user_id == current_user.id))
    return q.filter(or_(InternalMessage.sender_id == current_user.id, InternalMessage.recipient_user_id == current_user.id))

def build_ai_response(request_number):
    if not request_number:
        return None
    req = EcbuRequest.query.filter_by(request_number=request_number.strip()).first()
    if not req:
        return "Aucune demande ne correspond à ce numéro. Vérifiez le numéro de demande."
    if current_user.role == "prescripteur" and req.created_by_id != current_user.id:
        return "Ce numéro de demande n’est pas accessible depuis votre espace."
    sample = req.samples[0] if req.samples else None
    result = req.result[0] if isinstance(req.result, list) and req.result else req.result if req.result else None
    status_map = {
        "submitted": "Demande transmise au laboratoire",
        "received": "Échantillon réceptionné",
        "non_conforming": "Échantillon signalé non conforme à la réception",
        "pending_validation": "Résultat saisi, en attente de validation",
        "validated": "Résultat validé et disponible",
        "rejected": "Prélèvement rejeté",
        "result_deleted": "Résultat retiré de la consultation",
    }
    parts = [f"État de la demande {req.request_number} : {status_map.get(req.status, req.status)}."]
    if sample:
        parts.append(f"Échantillon : {sample.sample_number}.")
    if req.conformity and req.conformity != "not_evaluated":
        parts.append(f"Conformité pré-analytique : {req.conformity}.")
    if result and result.culture_status:
        parts.append(f"Culture : {result.culture_status}.")
    return " ".join(parts)

@bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    form = InternalMessageForm()
    if current_user.role == "admin":
        form.recipient_role.choices = [("laboratoire", "Laboratoire"), ("prescripteur", "Prescripteur")]
    elif current_user.role == "laboratoire":
        form.recipient_role.choices = [("prescripteur", "Prescripteur"), ("admin", "Administrateur")]
    else:
        form.recipient_role.choices = [("laboratoire", "Laboratoire"), ("admin", "Administrateur")]
    if form.validate_on_submit():
        req = EcbuRequest.query.filter_by(request_number=form.request_number.data.strip()).first() if form.request_number.data else None
        if current_user.role == "prescripteur" and req and req.created_by_id != current_user.id:
            flash("Cette demande n’est pas accessible depuis votre espace.", "danger")
            return redirect(url_for("chat.index"))
        msg = InternalMessage(request_id=req.id if req else None, sender_id=current_user.id, recipient_role=form.recipient_role.data, subject=form.subject.data, body=form.body.data, ai_response=build_ai_response(form.request_number.data))
        db.session.add(msg)
        db.session.commit()
        audit("message_interne", "internal_message", msg.id)
        notify("Nouveau message", form.subject.data, role_target=form.recipient_role.data)
        flash("Message envoyé.", "success")
        return redirect(url_for("chat.index"))
    messages = visible_messages_query().order_by(InternalMessage.id.desc()).limit(80).all()
    return render_template("chat/index.html", form=form, messages=messages)
