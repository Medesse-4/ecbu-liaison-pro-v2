from flask import Blueprint, render_template, redirect, url_for, flash, Response, request
from flask_login import login_required, current_user
from extensions import db
from app.forms import ResultForm
from app.models import EcbuRequest, LabResult, Sample
from app.utils import audit, notify, utcnow, role_required, clinical_access_for_request
import io, csv

bp = Blueprint("results", __name__, url_prefix="/results")

@bp.route("/")
@login_required
@role_required("prescripteur", "laboratoire", "chef_labo")
def index():
    query = LabResult.query.join(EcbuRequest).filter(LabResult.deleted_at.is_(None), EcbuRequest.deleted_at.is_(None))
    if current_user.role == "prescripteur":
        query = query.filter(EcbuRequest.created_by_id == current_user.id, EcbuRequest.status == "validated")
    results = query.order_by(LabResult.id.desc()).limit(200).all()
    return render_template("results/index.html", results=results)

@bp.route("/edit/<int:request_id>", methods=["GET", "POST"])
@login_required
@role_required("laboratoire", "chef_labo")
def edit(request_id):
    req = db.session.get(EcbuRequest, request_id)
    if not req or req.deleted_at:
        return render_template("errors/404.html"), 404
    result = LabResult.query.filter_by(request_id=req.id).first() or LabResult(request_id=req.id)
    if result.deleted_at:
        flash("Ce résultat a été supprimé. Créez un nouveau résultat uniquement après décision interne documentée.", "warning")
        return redirect(url_for("results.index"))
    if req.status == "validated" and current_user.role not in ("laboratoire", "chef_labo"):
        return render_template("errors/403.html"), 403
    form = ResultForm(obj=result)
    if form.validate_on_submit():
        old = {"status": req.status, "conclusion": result.conclusion}
        form.populate_obj(result)
        result.deleted_at = None
        if result.id is None:
            db.session.add(result)
        req.status = "pending_validation"
        db.session.commit()
        audit("saisie_resultat", "lab_result", result.id, old, {"status": req.status, "conclusion": result.conclusion})
        notify("Résultat à valider", req.request_number, role_target="chef_labo", level="warning")
        flash("Résultat enregistré.", "success")
        return redirect(url_for("results.index"))
    return render_template("results/form.html", form=form, req=req)

@bp.route("/validate/<int:result_id>", methods=["POST"])
@login_required
@role_required("chef_labo")
def validate(result_id):
    result = db.session.get(LabResult, result_id)
    if result and not result.deleted_at and result.request and not result.request.deleted_at:
        result.validated_by_id = current_user.id
        result.validated_at = utcnow()
        result.electronic_signature = f"VAL-{current_user.id}-{int(result.validated_at.timestamp())}"
        result.request.status = "validated"
        result.request.archived_at = utcnow()
        for sample in result.request.samples:
            sample.archived_at = utcnow()
        db.session.commit()
        audit("validation_resultat", "lab_result", result.id)
        notify("Résultat disponible", result.request.request_number, user_id=result.request.created_by_id, level="success")
    return redirect(url_for("results.index"))

@bp.route("/delete/<int:result_id>", methods=["POST"])
@login_required
@role_required("laboratoire", "chef_labo")
def delete_result(result_id):
    result = db.session.get(LabResult, result_id)
    if not result or result.deleted_at:
        return render_template("errors/404.html"), 404
    old = {"validated_at": result.validated_at, "request_status": result.request.status if result.request else None}
    result.deleted_at = utcnow()
    result.deleted_by_id = current_user.id
    result.delete_reason = request.form.get("reason", "Suppression par le laboratoire")
    if result.request:
        result.request.status = "result_deleted"
    db.session.commit()
    audit("suppression_resultat_valide_ou_envoye_par_laboratoire", "lab_result", result.id, old, {"deleted_at": result.deleted_at, "reason": result.delete_reason})
    if result.request:
        notify("Résultat retiré", f"Le résultat de la demande {result.request.request_number} a été retiré par le laboratoire.", user_id=result.request.created_by_id, level="warning")
    flash("Résultat supprimé de l’espace de consultation. La trace d’audit est conservée.", "success")
    return redirect(url_for("results.index"))

@bp.route("/report/<int:result_id>")
@login_required
def report(result_id):
    result = db.session.get(LabResult, result_id)
    if not result or result.deleted_at:
        return render_template("errors/404.html"), 404
    if not clinical_access_for_request(result.request):
        return render_template("errors/403.html"), 403
    if current_user.role == "prescripteur" and result.request.status != "validated":
        return render_template("errors/403.html"), 403
    groups = {"S": [], "I": [], "R": []}
    for row in result.antibiograms:
        if row.display_on_report and row.interpretation in groups:
            groups[row.interpretation].append(row)
    return render_template("results/report.html", result=result, req=result.request, groups=groups)

@bp.route("/export.csv")
@login_required
@role_required("laboratoire", "chef_labo")
def export_csv():
    out = io.StringIO(); w = csv.writer(out, delimiter=';')
    w.writerow(["Demande", "Culture", "Conclusion", "Validation"])
    for r in LabResult.query.filter(LabResult.deleted_at.is_(None)).order_by(LabResult.id.desc()).all():
        w.writerow([r.request.request_number, r.culture_status, r.conclusion, r.validated_at])
    return Response(out.getvalue().encode('utf-8-sig'), mimetype='text/csv', headers={'Content-Disposition':'attachment; filename=resultats_ecbu.csv'})
