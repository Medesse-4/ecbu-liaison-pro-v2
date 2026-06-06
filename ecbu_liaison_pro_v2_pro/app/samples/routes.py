from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from extensions import db
from app.forms import SampleForm
from app.models import EcbuRequest, Sample, QualityChecklist
from app.security import generate_token
from app.utils import audit, role_required, notify

bp = Blueprint("samples", __name__, url_prefix="/samples")

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
        checklist_values = {
            "patient_informed": form.patient_informed.data,
            "technique_mastered": form.technique_mastered.data,
            "intimate_toilet": form.intimate_toilet.data,
            "sterile_container": form.sterile_container.data,
            "identified_container": form.identified_container.data,
            "sufficient_volume": form.sufficient_volume.data,
            "no_leakage": form.no_leakage.data,
            "delay_compliant": form.delay_compliant.data,
            "temperature_compliant": form.temperature_compliant.data,
            "transport_compliant": form.transport_compliant.data,
            "sample_nature_compliant": form.sample_nature_compliant.data,
            "acceptable_container": form.acceptable_container.data,
            "patient_identity_match": form.patient_identity_match.data,
            "request_form_complete": form.request_form_complete.data,
            "collection_instructions_given": form.collection_instructions_given.data,
        }
        decision = "conforme" if all(checklist_values.values()) else "non_conforme"
        sample = Sample(
            request_id=req.id,
            sample_number=form.sample_number.data,
            qr_code=generate_token(),
            sample_type=form.sample_type.data,
            sampling_date=form.sampling_date.data,
            sampling_time=form.sampling_time.data,
            reception_date=form.reception_date.data,
            reception_time=form.reception_time.data,
            transport_condition=form.transport_condition.data,
            storage_temperature=form.storage_temperature.data,
            preanalytical_decision=decision,
            preanalytical_comment=form.preanalytical_comment.data,
        )
        db.session.add(sample)
        checklist = QualityChecklist.query.filter_by(request_id=req.id).first() or QualityChecklist(request_id=req.id)
        for key, value in checklist_values.items():
            setattr(checklist, key, value)
        checklist.decision = decision
        db.session.add(checklist)
        req.status = "received"
        req.conformity = "Conforme" if decision == "conforme" else "Non conforme"
        db.session.commit()
        audit("reception_et_controle_conformite", "sample", sample.id, new_value={"decision": decision})
        if decision == "conforme":
            flash("Réception enregistrée. Échantillon conforme.", "success")
        else:
            notify(
                "Prélèvement non conforme",
                f"La demande {req.request_number} présente une non-conformité à la réception. Observation : {form.preanalytical_comment.data or 'contrôle qualité requis'}",
                user_id=req.created_by_id,
                level="warning",
            )
            flash("Réception enregistrée. Échantillon non conforme : le prescripteur est notifié et la décision est tracée.", "warning")
        return redirect(url_for("samples.index"))
    return render_template("samples/form.html", form=form, req=req)
