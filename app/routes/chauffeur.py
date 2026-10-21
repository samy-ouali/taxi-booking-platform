"""
Routes côté chauffeur : notifications reçues, accepter/refuser, terminer une course.
"""
from datetime import datetime
from functools import wraps

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    abort,
)
from flask_login import login_required, current_user

from app import db
from app.models import Course, NotificationDemande, Chauffeur, Taxi
from app.services.matching import attribuer_course

bp = Blueprint("chauffeur", __name__)


def chauffeur_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "CHAUFFEUR":
            abort(403)
        return view(*args, **kwargs)

    return wrapper


@bp.route("/dashboard")
@login_required
@chauffeur_required
def dashboard():
    notifs = (
        NotificationDemande.query.filter_by(
            id_chauffeur=current_user.id_utilisateur, reponse="EN_ATTENTE"
        )
        .order_by(NotificationDemande.date_envoi.desc())
        .all()
    )
    courses_en_cours = Course.query.filter_by(
        id_chauffeur=current_user.id_utilisateur, statut="ATTRIBUEE"
    ).all() + Course.query.filter_by(
        id_chauffeur=current_user.id_utilisateur, statut="EN_COURS"
    ).all()
    return render_template(
        "chauffeur/dashboard.html",
        notifications=notifs,
        courses_en_cours=courses_en_cours,
    )


@bp.route("/notification/<int:id_notification>/accepter", methods=["POST"])
@login_required
@chauffeur_required
def accepter(id_notification: int):
    notif = NotificationDemande.query.get_or_404(id_notification)
    if notif.id_chauffeur != current_user.id_utilisateur:
        abort(403)
    course = db.session.get(Course, notif.id_course)
    if course.statut != "EN_RECHERCHE":
        flash("Cette course n'est plus disponible.", "warning")
        return redirect(url_for("chauffeur.dashboard"))

    ok = attribuer_course(course, current_user.id_utilisateur)
    if ok:
        flash(f"Course #{course.id_course} acceptée.", "success")
    else:
        flash("Impossible d'accepter cette course.", "danger")
    return redirect(url_for("chauffeur.dashboard"))


@bp.route("/notification/<int:id_notification>/refuser", methods=["POST"])
@login_required
@chauffeur_required
def refuser(id_notification: int):
    notif = NotificationDemande.query.get_or_404(id_notification)
    if notif.id_chauffeur != current_user.id_utilisateur:
        abort(403)
    notif.reponse = "REFUSEE"
    notif.date_reponse = datetime.utcnow()
    db.session.commit()
    flash("Course refusée.", "info")
    return redirect(url_for("chauffeur.dashboard"))


@bp.route("/course/<int:id_course>/demarrer", methods=["POST"])
@login_required
@chauffeur_required
def demarrer(id_course: int):
    course = Course.query.get_or_404(id_course)
    if course.id_chauffeur != current_user.id_utilisateur:
        abort(403)
    if course.statut != "ATTRIBUEE":
        flash("La course ne peut pas être démarrée.", "warning")
        return redirect(url_for("chauffeur.dashboard"))
    course.statut = "EN_COURS"
    db.session.commit()
    flash("Course démarrée.", "success")
    return redirect(url_for("chauffeur.dashboard"))


@bp.route("/course/<int:id_course>/terminer", methods=["POST"])
@login_required
@chauffeur_required
def terminer(id_course: int):
    course = Course.query.get_or_404(id_course)
    if course.id_chauffeur != current_user.id_utilisateur:
        abort(403)
    if course.statut != "EN_COURS":
        flash("La course n'est pas en cours.", "warning")
        return redirect(url_for("chauffeur.dashboard"))

    course.statut = "TERMINEE"
    course.prix_final = course.prix_estime  # simple : prix final = estimé

    chauffeur = db.session.get(Chauffeur, current_user.id_utilisateur)
    chauffeur.statut = "DISPONIBLE"

    if course.id_taxi:
        taxi = db.session.get(Taxi, course.id_taxi)
        if taxi:
            taxi.statut_disponibilite = "DISPONIBLE"

    db.session.commit()
    flash("Course terminée. Bonne continuation !", "success")
    return redirect(url_for("chauffeur.dashboard"))
