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
        flash("Ce résultat a été retiré de la consultation.", "warning")
        return redirect(url_for("results.index"))
    form = ResultForm(obj=result)
    if form.validate_on_submit():
        old = {"status": req.status, "conclusion": result.conclusion}
        form.populate_obj(result)
        if result.culture_status != "positive":
            result.isolated_germ = None
        result.deleted_at = None
        if result.id is None:
            db.session.add(result)
        if result.culture_status == "rejected":
            req.status = "rejected"
            reason = result.rejection_reason or result.conclusion or "Motif non précisé"
            notify("Prélèvement rejeté", f"Le prélèvement {req.request_number} est rejeté pour raison de : {reason}", user_id=req.created_by_id, level="warning")
        else:
            req.status = "pending_validation"
            notify("Résultat à valider", req.request_number, role_target="chef_labo", level="warning")
        db.session.commit()
        audit("saisie_resultat", "lab_result", result.id, old, {"status": req.status, "conclusion": result.conclusion})
        flash("Données enregistrées.", "success")
        return redirect(url_for("results.index"))
    return render_template("results/form.html", form=form, req=req)

@bp.route("/validate/<int:result_id>", methods=["POST"])
@login_required
@role_required("chef_labo")
def validate(result_id):
    result = db.session.get(LabResult, result_id)
    if result and not result.deleted_at and result.request and not result.request.deleted_at:
        if result.culture_status == "rejected":
            result.request.status = "rejected"
            reason = result.rejection_reason or result.conclusion or "Motif non précisé"
            notify("Prélèvement rejeté", f"Le prélèvement {result.request.request_number} est rejeté pour raison de : {reason}", user_id=result.request.created_by_id, level="warning")
        else:
            result.validated_by_id = current_user.id
            result.validated_at = utcnow()
            result.electronic_signature = f"VAL-{current_user.id}-{int(result.validated_at.timestamp())}"
            result.request.status = "validated"
            result.request.archived_at = utcnow()
            for sample in result.request.samples:
                sample.archived_at = utcnow()
            notify("Résultat disponible", result.request.request_number, user_id=result.request.created_by_id, level="success")
        db.session.commit()
        audit("validation_resultat", "lab_result", result.id)
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
    result.delete_reason = request.form.get("reason", "Retrait laboratoire")
    if result.request:
        result.request.status = "result_deleted"
    db.session.commit()
    audit("retrait_resultat_par_laboratoire", "lab_result", result.id, old, {"deleted_at": result.deleted_at, "reason": result.delete_reason})
    if result.request:
        notify("Résultat retiré", f"Le résultat de la demande {result.request.request_number} a été retiré par le laboratoire.", user_id=result.request.created_by_id, level="warning")
    flash("Résultat retiré de la consultation.", "success")
    return redirect(url_for("results.index"))

@bp.route("/report/<int:result_id>")
@login_required
def report(result_id):
    result = db.session.get(LabResult, result_id)
    if not result or result.deleted_at or result.culture_status == "rejected":
        return render_template("errors/404.html"), 404
    if not clinical_access_for_request(result.request):
        return render_template("errors/403.html"), 403
    if current_user.role == "prescripteur" and result.request.status != "validated":
        return render_template("errors/403.html"), 403
    groups = {"S": [], "I": [], "R": []}
    if result.culture_status == "positive":
        for row in result.antibiograms:
            if row.display_on_report and row.interpretation in groups:
                groups[row.interpretation].append(row)
    return render_template("results/report.html", result=result, req=result.request, groups=groups)

@bp.route("/export.csv")
@login_required
@role_required("laboratoire", "chef_labo")
def export_csv():
    out = io.StringIO(); w = csv.writer(out, delimiter=';')
    w.writerow(["N° demande", "N° échantillon", "Patient", "Sexe", "Âge", "Hôpital", "Service", "Commune", "Sous sonde", "ATB", "Hospitalisé", "Conformité", "Culture", "Germe isolé", "Conclusion", "Validation"])
    rows = LabResult.query.join(EcbuRequest).filter(EcbuRequest.deleted_at.is_(None)).order_by(LabResult.id.desc()).all()
    for r in rows:
        req = r.request
        sample_no = req.samples[0].sample_number if req.samples else ""
        w.writerow([req.request_number, sample_no, f"{req.patient_name} {req.patient_firstname or ''}", req.patient_sex, f"{req.patient_age or ''} {req.patient_age_unit or ''}", req.hospital_name or "", req.requesting_service or "", req.origin_commune or "", req.patient_probe or "", req.antibiotic_treatment or "", req.currently_hospitalized or "", req.conformity or "", r.culture_status or "", r.isolated_germ or "", r.conclusion or "", r.validated_at or ""])
    return Response(out.getvalue().encode('utf-8-sig'), mimetype='text/csv', headers={'Content-Disposition':'attachment; filename=base_laboratoire_ecbu.csv'})
