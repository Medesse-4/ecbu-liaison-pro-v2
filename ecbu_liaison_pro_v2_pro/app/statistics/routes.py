from flask import Blueprint, render_template, jsonify
from flask_login import login_required
from sqlalchemy import func
from app.utils import role_required
from app.models import EcbuRequest, NonConformity, Antibiogram, LabResult

bp = Blueprint("statistics", __name__, url_prefix="/statistics")

@bp.route("/")
@login_required
@role_required("laboratoire", "chef_labo")
def index():
    total = EcbuRequest.query.count()
    validated = EcbuRequest.query.filter_by(status="validated").count()
    rejected = EcbuRequest.query.filter_by(status="rejected").count()
    nc = NonConformity.query.count()
    return render_template("statistics/index.html", total=total, validated=validated, rejected=rejected, nc=nc)

@bp.route("/api/overview")
@login_required
@role_required("laboratoire", "chef_labo")
def overview():
    by_nc = NonConformity.query.with_entities(NonConformity.type_nc, func.count(NonConformity.id)).group_by(NonConformity.type_nc).all()
    resistance = Antibiogram.query.with_entities(Antibiogram.interpretation, func.count(Antibiogram.id)).group_by(Antibiogram.interpretation).all()
    return jsonify({"non_conformities": by_nc, "resistance": resistance})
