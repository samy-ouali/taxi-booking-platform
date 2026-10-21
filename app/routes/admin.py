"""
Routes côté admin : vue globale + recalcul des notes moyennes.
"""
from functools import wraps
from decimal import Decimal

from flask import Blueprint, render_template, abort, redirect, url_for, flash
from flask_login import login_required, current_user

from app import db
from app.models import Utilisateur, Course, Chauffeur, Evaluation

bp = Blueprint("admin", __name__)


def admin_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "ADMIN":
            abort(403)
        return view(*args, **kwargs)

    return wrapper


@bp.route("/dashboard")
@login_required
@admin_required
def dashboard():
    stats = {
        "nb_clients": Utilisateur.query.filter_by(role="CLIENT").count(),
        "nb_chauffeurs": Utilisateur.query.filter_by(role="CHAUFFEUR").count(),
        "nb_courses_total": Course.query.count(),
        "nb_courses_terminees": Course.query.filter_by(statut="TERMINEE").count(),
        "nb_chauffeurs_dispo": Chauffeur.query.filter_by(statut="DISPONIBLE").count(),
    }
    dernieres_courses = (
        Course.query.order_by(Course.date_demande.desc()).limit(10).all()
    )
    return render_template(
        "admin/dashboard.html", stats=stats, dernieres_courses=dernieres_courses
    )


@bp.route("/recalculer-notes", methods=["POST"])
@login_required
@admin_required
def recalculer_notes():
    """Recalcule la note_moyenne de tous les utilisateurs."""
    users = Utilisateur.query.all()
    for user in users:
        evals = Evaluation.query.filter_by(cible_id=user.id_utilisateur).all()
        if evals:
            moy = sum(e.note for e in evals) / len(evals)
            user.note_moyenne = Decimal(str(round(moy, 2)))
        else:
            user.note_moyenne = Decimal("0.00")
    db.session.commit()
    flash("Notes moyennes recalculées.", "success")
    return redirect(url_for("admin.dashboard"))
