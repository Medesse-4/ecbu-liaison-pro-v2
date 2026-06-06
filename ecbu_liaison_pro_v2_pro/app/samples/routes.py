from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
from app.forms import SampleForm
from app.models import EcbuRequest, Sample, QualityChecklist, NonConformity
from app.security import generate_token
from app.utils import audit, role_required

bp = Blueprint("samples", __name__, url_prefix="/samples")

QUALITY_FIELDS = [
    ("patient_informed", "Patient informé"),
    ("technique_mastered", "Technique maîtrisée"),
    ("intimate_toilet", "Toilette intime"),
    ("sterile_container", "Flacon stérile"),
    ("identified_container", "Flacon identifié"),
    ("sufficient_volume", "Volume suffisant"),
    ("no_leakage", "Absence de fuite"),
    ("delay_compliant", "Délai conforme"),
    ("temperature_compliant", "Température conforme"),
    ("transport_compliant", "Transport conforme"),
    ("sample_nature_compliant", "Nature du prélèvement conforme"),
]


def evaluate_quality(form):
    missing = [label for field, label in QUALITY_FIELDS if not getattr(form, field).data]
    return ("conforme" if not missing else "non_conforme", missing)


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
    if not req or req.deleted_at:
        return render_template("errors/404.html"), 404
    form = SampleForm()
    if form.validate_on_submit():
        decision, missing = evaluate_quality(form)
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
            conformity_decision=decision,
            conformity_comment=form.conformity_comment.data,
        )
        db.session.add(sample)
        checklist = QualityChecklist.query.filter_by(request_id=req.id).first() or QualityChecklist(request_id=req.id)
        for field, _label in QUALITY_FIELDS:
            setattr(checklist, field, bool(getattr(form, field).data))
        checklist.decision = decision
        db.session.add(checklist)
        req.status = "received"
        req.conformity = decision
        if decision == "non_conforme":
            nc = NonConformity(
                request_id=req.id,
                type_nc="controle_reception_non_conforme",
                severity="moderee",
                impact="Fiabilité du résultat potentiellement affectée",
                consequence="Critères de réception non entièrement respectés : " + ", ".join(missing),
                decision="Évaluation laboratoire nécessaire avant poursuite de l’analyse.",
                responsible=current_user.name,
                declared_by_id=current_user.id,
            )
            db.session.add(nc)
        db.session.commit()
        audit("reception_echantillon_controle_qualite", "sample", sample.id, new_value={"decision": decision, "criteres_manquants": missing})
        if decision == "non_conforme":
            flash("Échantillon reçu avec non-conformité pré-analytique automatiquement signalée.", "warning")
        else:
            flash("Échantillon conforme enregistré.", "success")
        return redirect(url_for("samples.index"))
    return render_template("samples/form.html", form=form, req=req, quality_fields=QUALITY_FIELDS)
