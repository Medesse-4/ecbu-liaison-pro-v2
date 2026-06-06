from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
from app.forms import TicketForm
from app.models import Ticket
from app.utils import audit, notify

bp = Blueprint("tickets", __name__, url_prefix="/tickets")

@bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    form = TicketForm()
    if form.validate_on_submit():
        t = Ticket(title=form.title.data, category=form.category.data, description=form.description.data, created_by_id=current_user.id)
        db.session.add(t); db.session.commit()
        audit("creation_ticket", "ticket", t.id)
        notify("Nouveau ticket", t.title, role_target="admin", level="warning")
        flash("Ticket envoyé.", "success")
        return redirect(url_for("tickets.index"))
    query = Ticket.query
    if current_user.role != "admin":
        query = query.filter_by(created_by_id=current_user.id)
    rows = query.order_by(Ticket.id.desc()).limit(200).all()
    return render_template("tickets/index.html", form=form, rows=rows)
