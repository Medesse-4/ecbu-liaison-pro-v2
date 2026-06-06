from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy import or_
from extensions import db
from app.models import CommunicationThread, CommunicationMessage, EcbuRequest
from app.utils import audit, notify, role_required, clinical_access_for_request

bp = Blueprint("chat", __name__, url_prefix="/messagerie")


def thread_query():
    q = CommunicationThread.query
    if current_user.role == "prescripteur":
        q = q.filter(CommunicationThread.prescriber_id == current_user.id)
    elif current_user.role in ("laboratoire", "chef_labo"):
        q = q.filter(CommunicationThread.admin_thread.is_(False))
    elif current_user.role == "admin":
        q = q.filter(CommunicationThread.admin_thread.is_(True))
    else:
        q = q.filter(False)
    return q


def request_status_text(req):
    sample = req.samples[0] if req.samples else None
    result = getattr(req, "result", None)
    if isinstance(result, list):
        result = result[0] if result else None
    lines = [f"Demande {req.request_number}"]
    lines.append(f"Statut : {req.status or 'enregistrée'}")
    lines.append(f"Conformité : {req.conformity or 'non évaluée'}")
    if sample:
        lines.append(f"Échantillon : {sample.sample_number} — décision préanalytique : {sample.preanalytical_decision or 'non évaluée'}")
    if result and not result.deleted_at:
        if result.culture_status == "rejected":
            reason = result.rejection_reason or result.conclusion or "motif non renseigné"
            lines.append(f"Prélèvement rejeté : {reason}")
        elif result.culture_status:
            lines.append(f"Culture : {result.culture_status}")
            if result.culture_status == "positive" and result.culture_details:
                lines.append(f"Germe isolé : {result.culture_details}")
    return "\n".join(lines)


@bp.route("/", methods=["GET", "POST"])
@login_required
@role_required("admin", "prescripteur", "laboratoire", "chef_labo")
def index():
    if request.method == "POST":
        request_number = request.form.get("request_number", "").strip()
        subject = request.form.get("subject", "").strip() or "Suivi de demande"
        body = request.form.get("body", "").strip()
        admin_thread = request.form.get("admin_thread") == "1"
        req = None
        prescriber_id = current_user.id if current_user.role == "prescripteur" else None
        if request_number:
            req = EcbuRequest.query.filter_by(request_number=request_number).first()
            if not req:
                flash("Numéro de demande introuvable.", "warning")
                return redirect(url_for("chat.index"))
            if current_user.role == "prescripteur" and req.created_by_id != current_user.id:
                flash("Cette demande n’appartient pas à votre espace.", "danger")
                return redirect(url_for("chat.index"))
            prescriber_id = req.created_by_id
            subject = f"Suivi {req.request_number}"
        if current_user.role == "admin":
            admin_thread = True
        thread = CommunicationThread(
            request_id=req.id if req else None,
            subject=subject,
            prescriber_id=prescriber_id,
            admin_thread=admin_thread,
            created_by_id=current_user.id,
        )
        db.session.add(thread)
        db.session.flush()
        if body:
            db.session.add(CommunicationMessage(thread_id=thread.id, sender_id=current_user.id, sender_role=current_user.role, body=body))
        if req:
            db.session.add(CommunicationMessage(thread_id=thread.id, sender_role="assistant", body=request_status_text(req), is_assistant=True))
        db.session.commit()
        audit("creation_fil_discussion", "communication_thread", thread.id)
        flash("Discussion créée.", "success")
        return redirect(url_for("chat.thread", thread_id=thread.id))
    threads = thread_query().order_by(CommunicationThread.updated_at.desc()).limit(80).all()
    return render_template("chat/index.html", threads=threads)


@bp.route("/<int:thread_id>", methods=["GET", "POST"])
@login_required
@role_required("admin", "prescripteur", "laboratoire", "chef_labo")
def thread(thread_id):
    thread = thread_query().filter(CommunicationThread.id == thread_id).first()
    if not thread:
        return render_template("errors/403.html"), 403
    if request.method == "POST":
        body = request.form.get("body", "").strip()
        if body:
            db.session.add(CommunicationMessage(thread_id=thread.id, sender_id=current_user.id, sender_role=current_user.role, body=body))
            if thread.request and ("etat" in body.lower() or "avancement" in body.lower() or "statut" in body.lower() or thread.request.request_number.lower() in body.lower()):
                db.session.add(CommunicationMessage(thread_id=thread.id, sender_role="assistant", body=request_status_text(thread.request), is_assistant=True))
            db.session.commit()
            audit("message_discussion", "communication_thread", thread.id)
        return redirect(url_for("chat.thread", thread_id=thread.id))
    return render_template("chat/thread.html", thread=thread)
