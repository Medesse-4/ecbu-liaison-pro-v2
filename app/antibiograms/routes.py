from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from extensions import db
from app.models import LabResult, Antibiogram
from app.utils import audit, role_required

bp = Blueprint("antibiograms", __name__, url_prefix="/antibiograms")

ANTIBIOTICS = [
    "Ampicilline (AMP10)", "Amoxicilline (AMX25)", "Amoxicilline + acide clavulanique (AMC30)",
    "Ticarcilline (TIC75)", "Ticarcilline + acide clavulanique (TCC75)", "Pipéracilline (PIP30)", "Pipéracilline/Tazobactam (TZP)",
    "Céfalotine (KF30)", "Céfazoline (KZ30)", "Céfuroxime (CXM30)", "Céfixime (CFM5)", "Céfotaxime (CTX30)",
    "Ceftriaxone (CRO30)", "Ceftazidime (CAZ30)", "Céfépime (FEP30)", "Céfoxitine (FOX30)",
    "Imipénème (IPM10)", "Méropénème (MEM10)", "Ertapénème (ETP10)", "Doripénème (DOR10)", "Aztréonam (ATM30)",
    "Gentamicine (GEN10)", "Amikacine (AK30)", "Tobramycine (TOB10)", "Netilmicine (NET30)", "Streptomycine (S10)",
    "Ciprofloxacine (CIP5)", "Norfloxacine (NOR10)", "Ofloxacine (OFX5)", "Lévofloxacine (LEV5)", "Moxifloxacine (MXF5)",
    "Acide nalidixique (NA30)", "Cotrimoxazole / TMP-SMX (SXT25)", "Triméthoprime (W5)",
    "Nitrofurantoïne (F/M300)", "Fosfomycine (FOS200)", "Pivmécillinam (MEL10)",
    "Doxycycline (DO30)", "Tétracycline (TE30)", "Minocycline (MH30)",
    "Azithromycine (AZM15)", "Clarithromycine (CLR15)", "Erythromycine (E15)", "Clindamycine (DA2)",
    "Vancomycine (VA30)", "Teicoplanine (TEC30)", "Linézolide (LZD10)", "Daptomycine (DAP30)",
    "Chloramphénicol (C30)", "Rifampicine (RA5)", "Pristinamycine (PT15)", "Fusidique acide (FA10)",
    "Colistine (CT10)", "Tigécycline (TGC15)", "Ceftazidime/Avibactam (CZA)", "Ceftolozane/Tazobactam (C/T)",
]

@bp.route("/")
@login_required
@role_required("laboratoire")
def index():
    rows = Antibiogram.query.order_by(Antibiogram.id.desc()).limit(300).all()
    return render_template("antibiograms/index.html", rows=rows)

@bp.route("/edit/<int:result_id>", methods=["GET", "POST"])
@login_required
@role_required("laboratoire")
def edit(result_id):
    result = db.session.get(LabResult, result_id)
    if not result:
        return render_template("errors/404.html"), 404
    if request.method == "POST":
        Antibiogram.query.filter_by(result_id=result.id).delete()
        for i, ab in enumerate(ANTIBIOTICS):
            interp = request.form.get(f"interp_{i}")
            diam = request.form.get(f"diam_{i}")
            if interp:
                db.session.add(Antibiogram(result_id=result.id, bacteria=request.form.get("bacteria", ""), antibiotic=ab, diameter=diam, interpretation=interp, resistance_profile=request.form.get("profile", ""), display_on_report=bool(request.form.get(f"show_{i}"))))
        db.session.commit()
        audit("saisie_antibiogramme", "lab_result", result.id)
        flash("Antibiogramme enregistré.", "success")
        return redirect(url_for("antibiograms.index"))
    return render_template("antibiograms/form.html", result=result, antibiotics=ANTIBIOTICS)
