from flask import Blueprint, jsonify
from flask_login import login_required
from app.models import EcbuRequest, NonConformity, Antibiogram

bp = Blueprint("api", __name__, url_prefix="/api")

@bp.route("/health")
def health():
    return jsonify({"status": "ok", "service": "ECBU Liaison Pro V2"})

@bp.route("/metrics")
@login_required
def metrics():
    return jsonify({"requests": EcbuRequest.query.count(), "non_conformities": NonConformity.query.count(), "antibiograms": Antibiogram.query.count()})
