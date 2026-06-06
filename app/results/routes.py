from flask import Blueprint, render_template, redirect, url_for, flash, Response, request
from flask_login import login_required, current_user
from extensions import db
from app.forms import ResultForm, LabProfileForm
from app.models import EcbuRequest, LabResult, LabProfile
from app.utils import audit, notify, utcnow, role_required, clinical_access_for_request
import io, csv

bp = Blueprint("results", __name__, url_prefix="/results")


def current_lab_profile():
    if not getattr(current_user, "is_authenticated", False) or current_user.role != "laboratoire":
        return None
    return LabProfile.query.filter_by(user_id=current_user.id).first()


@bp.route("/lab/profile", methods=["GET", "POST"])
@login_required
@role_required("laboratoire")
def lab_profile():
    profile = current_lab_profile() or LabProfile(user_id=current_user.id)
    form = LabProfileForm(obj=profile)
    if form.validate_on_submit():
        form.populate_obj(profile)
        if profile.id is None:
            db.session.add(profile)
        db.session.commit()
        audit("configuration_bon_laboratoire", "lab_profile", profile.id)
        flash("Paramètres permanents du bon enregistrés.", "success")
        return redirect(url_for("dashboard.home"))
    return render_template("results/lab_profile.html", form=form, profile=profile)


@bp.route("/")
@login_required
@role_required("prescripteur", "laboratoire")
def index():
    query = LabResult.query.join(EcbuRequest).filter(LabResult.deleted_at.is_(None), EcbuRequest.deleted_at.is_(None))
    if current_user.role == "prescripteur":
        query = query.filter(EcbuRequest.created_by_id == current_user.id, EcbuRequest.status == "validated")
    results = query.order_by(LabResult.id.desc()).limit(200).all()
    return render_template("results/index.html", results=results)


@bp.route("/edit/<int:request_id>", methods=["GET", "POST"])
@login_required
@role_required("laboratoire")
def edit(request_id):
    req = db.session.get(EcbuRequest, request_id)
    if not req or req.deleted_at:
        return render_template("errors/404.html"), 404
    profile = current_lab_profile()
    result = LabResult.query.filter_by(request_id=req.id).first() or LabResult(request_id=req.id)
    if result.deleted_at:
        flash("Ce résultat a été retiré de la consultation.", "warning")
        return redirect(url_for("results.index"))
    form = ResultForm(obj=result)
    if request.method == "GET" and profile and not result.laboratory_name:
        form.laboratory_name.data = profile.laboratory_name
    if form.validate_on_submit():
        old = {"status": req.status, "conclusion": result.conclusion, "validated_at": result.validated_at}
        form.populate_obj(result)
        if profile:
            result.laboratory_name = result.laboratory_name or profile.laboratory_name
            result.hospital_name_on_report = profile.hospital_name
        result.manipulated_by_id = current_user.id
        result.manipulated_by_name = current_user.name
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
            notify("Résultat à valider", f"Résultat en attente de validation pour {req.request_number}", role_target="laboratoire", level="warning")
        db.session.commit()
        audit("saisie_resultat", "lab_result", result.id, old, {"status": req.status, "conclusion": result.conclusion, "manipule_par": current_user.name})
        flash("Résultat enregistré. La validation finale peut maintenant être réalisée par le laboratoire.", "success")
        return redirect(url_for("results.index"))
    return render_template("results/form.html", form=form, req=req)


@bp.route("/validate/<int:result_id>", methods=["POST"])
@login_required
@role_required("laboratoire")
def validate(result_id):
    result = db.session.get(LabResult, result_id)
    if result and not result.deleted_at and result.request and not result.request.deleted_at:
        if result.culture_status == "rejected":
            result.request.status = "rejected"
            reason = result.rejection_reason or result.conclusion or "Motif non précisé"
            notify("Prélèvement rejeté", f"Le prélèvement {result.request.request_number} est rejeté pour raison de : {reason}", user_id=result.request.created_by_id, level="warning")
        else:
            profile = current_lab_profile()
            if profile:
                result.laboratory_name = result.laboratory_name or profile.laboratory_name
                result.hospital_name_on_report = profile.hospital_name
                result.electronic_signature = profile.signature_text or f"Validation électronique — {current_user.name}"
            else:
                result.electronic_signature = f"Validation électronique — {current_user.name}"
            result.validated_by_id = current_user.id
            result.validated_at = utcnow()
            result.request.status = "validated"
            result.request.archived_at = utcnow()
            for sample in result.request.samples:
                sample.archived_at = utcnow()
            notify("Résultat disponible", result.request.request_number, user_id=result.request.created_by_id, level="success")
        db.session.commit()
        audit("validation_resultat_laboratoire", "lab_result", result.id, new_value={"validateur": current_user.name})
    return redirect(url_for("results.index"))


@bp.route("/delete/<int:result_id>", methods=["POST"])
@login_required
@role_required("laboratoire")
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
    return render_template("results/report.html", result=result, req=result.request, groups=groups, validator=result.validated_by)


@bp.route("/export.csv")
@login_required
@role_required("laboratoire")
def export_csv():
    out = io.StringIO(); w = csv.writer(out, delimiter=';')
    w.writerow(["N° demande", "N° échantillon", "Patient", "Sexe", "Âge", "Hôpital", "Service", "Commune", "Sous sonde", "ATB", "Hospitalisé", "Conformité", "Culture", "Germe isolé", "Conclusion", "Manipulé par", "Validé par", "Date validation"])
    rows = LabResult.query.join(EcbuRequest).filter(EcbuRequest.deleted_at.is_(None)).order_by(LabResult.id.desc()).all()
    for r in rows:
        req = r.request
        sample_no = req.samples[0].sample_number if req.samples else ""
        validator_name = r.validated_by.name if r.validated_by else ""
        w.writerow([req.request_number, sample_no, f"{req.patient_name} {req.patient_firstname or ''}", req.patient_sex, f"{req.patient_age or ''} {req.patient_age_unit or ''}", req.hospital_name or "", req.requesting_service or "", req.origin_commune or "", req.patient_probe or "", req.antibiotic_treatment or "", req.currently_hospitalized or "", req.conformity or "", r.culture_status or "", r.isolated_germ or "", r.conclusion or "", r.manipulated_by_name or "", validator_name, r.validated_at or ""])
    return Response(out.getvalue().encode('utf-8-sig'), mimetype='text/csv', headers={'Content-Disposition':'attachment; filename=base_laboratoire_ecbu.csv'})
