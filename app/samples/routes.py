from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from extensions import db
from app.forms import SampleForm
from app.models import EcbuRequest, Sample
from app.security import generate_token
from app.utils import audit, role_required

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
        sample = Sample(request_id=req.id, sample_number=form.sample_number.data, qr_code=generate_token(), sample_type=form.sample_type.data, sampling_date=form.sampling_date.data, sampling_time=form.sampling_time.data, reception_date=form.reception_date.data, reception_time=form.reception_time.data, transport_condition=form.transport_condition.data, storage_temperature=form.storage_temperature.data)
        db.session.add(sample)
        req.status = "received"
        db.session.commit()
        audit("reception_echantillon", "sample", sample.id)
        flash("Échantillon enregistré.", "success")
        return redirect(url_for("samples.index"))
    return render_template("samples/form.html", form=form, req=req)
