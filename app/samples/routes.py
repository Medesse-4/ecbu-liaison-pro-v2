from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required
from extensions import db
from app.forms import SampleForm
from app.models import EcbuRequest, Sample, QualityChecklist, NonConformity
from app.security import generate_token
from app.utils import audit, role_required

bp = Blueprint("samples", __name__, url_prefix="/samples")

QUALITY_FIELDS = [
    "patient_informed", "technique_mastered", "intimate_toilet", "sterile_container", "identified_container",
    "sufficient_volume", "no_leakage", "delay_compliant", "temperature_compliant", "transport_compliant", "sample_nature_compliant",
]

@bp.route("/")
@login_required
@role_required("laboratoire", "chef_labo")
def index():
    samples = Sample.query.order_by(Sample.id.desc()).limit(200).all()
    return render_template("samples/index.html", samples=samples)

@bp.route("/new/<int:request_id>", methods=["GET", "POST"])
@login_required
@role_required("laboratoire", "chef_labo")
def create(request_id):
    req = db.session.get(EcbuRequest, request_id)
    if not req:
        return render_template("errors/404.html"), 404
    form = SampleForm()
    if form.validate_on_submit():
        sample = Sample(request_id=req.id, sample_number=form.sample_number.data, qr_code=generate_token(), sample_type=form.sample_type.data, sampling_date=form.sampling_date.data, sampling_time=form.sampling_time.data, reception_date=form.reception_date.data, reception_time=form.reception_time.data, transport_condition=form.transport_condition.data, storage_temperature=form.storage_temperature.data)
        checklist = QualityChecklist.query.filter_by(request_id=req.id).first() or QualityChecklist(request_id=req.id)
        for field in QUALITY_FIELDS:
            setattr(checklist, field, bool(getattr(form, field).data))
        is_conform = all(getattr(checklist, field) for field in QUALITY_FIELDS)
        checklist.decision = "conforme" if is_conform else "non_conforme"
        req.conformity = checklist.decision
        req.status = "received" if is_conform else "non_conforming"
        db.session.add(sample)
        db.session.add(checklist)
        if not is_conform:
            nc = NonConformity(request_id=req.id, type_nc="Non-conformité pré-analytique", severity="moderee", impact="Fiabilité du prélèvement", consequence="Évaluation laboratoire requise", decision="Signalement automatique par grille de réception", responsible="Laboratoire")
            db.session.add(nc)
        db.session.commit()
        audit("reception_echantillon_et_controle_conformite", "sample", sample.id)
        flash("Échantillon enregistré. Conformité : " + ("Conforme" if is_conform else "Non conforme"), "success" if is_conform else "warning")
        return redirect(url_for("samples.index"))
    return render_template("samples/form.html", form=form, req=req)
