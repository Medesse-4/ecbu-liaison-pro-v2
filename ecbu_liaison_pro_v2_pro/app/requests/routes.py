from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from sqlalchemy import or_
from extensions import db
from app.forms import RequestForm
from app.models import EcbuRequest
from app.utils import audit, notify, role_required, utcnow
from datetime import datetime

bp = Blueprint("requests", __name__, url_prefix="/requests")

def next_request_number():
    year = datetime.utcnow().year
    count = EcbuRequest.query.filter(EcbuRequest.request_number.like(f"DEM-{year}-%")).count() + 1
    return f"DEM-{year}-{count:06d}"

@bp.route("/")
@login_required
@role_required("prescripteur", "laboratoire", "chef_labo")
def index():
    q = request.args.get("q", "").strip()
    page = request.args.get("page", 1, type=int)
    query = EcbuRequest.query.filter(EcbuRequest.deleted_at.is_(None))
    if current_user.role == "prescripteur":
        query = query.filter(EcbuRequest.created_by_id == current_user.id)
    if q:
        like = f"%{q}%"
        query = query.filter(or_(EcbuRequest.request_number.ilike(like), EcbuRequest.patient_name.ilike(like), EcbuRequest.patient_firstname.ilike(like), EcbuRequest.requesting_service.ilike(like)))
    pagination = query.order_by(EcbuRequest.id.desc()).paginate(page=page, per_page=20, error_out=False)
    return render_template("requests/index.html", pagination=pagination, q=q)

@bp.route("/new", methods=["GET", "POST"])
@login_required
@role_required("prescripteur")
def create():
    form = RequestForm()
    if form.validate_on_submit():
        obj = EcbuRequest(
            request_number=next_request_number(),
            patient_name=form.patient_name.data,
            patient_firstname=form.patient_firstname.data,
            patient_age=form.patient_age.data,
            patient_age_unit=form.patient_age_unit.data,
            patient_sex=form.patient_sex.data,
            hospital_origin=form.hospital_origin.data,
            origin_commune=form.origin_commune.data,
            requesting_service=form.requesting_service.data,
            prescriber_name=form.prescriber_name.data,
            sample_nature=form.sample_nature.data,
            patient_under_catheter=form.patient_under_catheter.data,
            consultation_reason=form.consultation_reason.data,
            general_signs=form.general_signs.data,
            recent_hospitalization_before_admission=form.recent_hospitalization_before_admission.data,
            recent_hospitalization_duration=form.recent_hospitalization_duration.data,
            currently_hospitalized=form.currently_hospitalized.data,
            current_hospitalization_duration=form.current_hospitalization_duration.data,
            antibiotic_treatment=form.antibiotic_treatment.data,
            current_atb_duration=form.current_atb_duration.data,
            chronic_disease=form.chronic_disease.data,
            primary_diagnosis=form.primary_diagnosis.data,
            sampling_date=form.sampling_date.data,
            urgent=form.urgent.data,
            created_by_id=current_user.id,
            status="submitted",
        )
        db.session.add(obj)
        db.session.commit()
        audit("creation_demande", "ecbu_request", obj.id)
        notify("Nouvelle demande ECBU", obj.request_number, role_target="laboratoire")
        flash("Demande envoyée au laboratoire.", "success")
        return redirect(url_for("requests.index"))
    return render_template("requests/form.html", form=form)

@bp.route("/<int:request_id>/delete", methods=["POST"])
@login_required
@role_required("prescripteur")
def delete(request_id):
    obj = db.session.get(EcbuRequest, request_id)
    if not obj or obj.created_by_id != current_user.id or obj.deleted_at is not None:
        return render_template("errors/403.html"), 403
    if obj.status == "validated":
        flash("Un résultat déjà validé ne peut pas être supprimé depuis l’espace prescripteur.", "warning")
        return redirect(url_for("requests.index"))
    old = {"status": obj.status, "deleted_at": obj.deleted_at}
    obj.deleted_at = utcnow()
    obj.deleted_by_id = current_user.id
    obj.delete_reason = request.form.get("reason", "Retrait de la demande par le prescripteur")
    db.session.commit()
    audit("suppression_logique_demande_par_prescripteur", "ecbu_request", obj.id, old, {"deleted_at": obj.deleted_at, "reason": obj.delete_reason})
    flash("Demande retirée de votre espace.", "success")
    return redirect(url_for("requests.index"))
