from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from extensions import db
from app.forms import NonConformityForm
from app.models import NonConformity, EcbuRequest, CapaAction
from app.utils import audit, notify, role_required

bp = Blueprint("quality", __name__, url_prefix="/quality")

@bp.route("/non-conformities", methods=["GET", "POST"])
@login_required
@role_required("responsable_qualite", "laboratoire", "chef_labo")
def non_conformities():
    form = NonConformityForm()
    req_id = request.args.get("request_id", type=int)
    if form.validate_on_submit():
        nc = NonConformity(request_id=req_id, type_nc=form.type_nc.data, severity=form.severity.data, impact=form.impact.data, consequence=form.consequence.data, decision=form.decision.data, responsible=form.responsible.data, declared_by_id=current_user.id)
        db.session.add(nc)
        if req_id:
            req = db.session.get(EcbuRequest, req_id)
            if req:
                req.conformity = "non_compliant"
        db.session.commit()
        audit("declaration_non_conformite", "non_conformity", nc.id)
        notify("Non-conformité déclarée", nc.type_nc, role_target="responsable_qualite", level="danger")
        flash("Non-conformité déclarée.", "success")
        return redirect(url_for("quality.non_conformities"))
    rows = NonConformity.query.order_by(NonConformity.id.desc()).limit(300).all()
    return render_template("quality/non_conformities.html", form=form, rows=rows)

@bp.route("/capa")
@login_required
@role_required("responsable_qualite", "laboratoire", "chef_labo")
def capa():
    actions = CapaAction.query.order_by(CapaAction.id.desc()).limit(200).all()
    return render_template("quality/capa.html", actions=actions)
