"""
Routes côté client : créer une réservation, suivre ses courses, noter un chauffeur.
"""
from datetime import datetime
from functools import wraps
import requests
from app.services.geo import distance_euclidienne_km

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
from app.models import (
    Course,
    CategorieTaxi,
    TrancheTarif,
    Evaluation,
    Client,
)
from app.services.matching import chercher_candidats, notifier_candidats
from app.services.tarif import calculer_prix_estime
from config import Config

bp = Blueprint("client", __name__)


def client_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "CLIENT":
            abort(403)
        return view(*args, **kwargs)

    return wrapper


@bp.route("/dashboard")
@login_required
@client_required
def dashboard():
    courses = (
        Course.query.filter_by(id_client=current_user.id_utilisateur)
        .order_by(Course.date_demande.desc())
        .all()
    )
    return render_template("client/dashboard.html", courses=courses)


@bp.route("/reserver", methods=["GET", "POST"])
@login_required
@client_required
def reserver():
    categories = CategorieTaxi.query.all()
    if request.method == "POST":
        try:
            depart_adresse = request.form["depart_adresse"]
            arrivee_adresse = request.form["arrivee_adresse"]
            nb_p = int(request.form["nb_personnes"])
            nb_b = int(request.form.get("nb_bagages", 0))
            categorie_id = int(request.form["id_categorie"])
            depart_souhaite = datetime.fromisoformat(
                request.form["date_depart_souhaitee"]
            )

            def geocode(addr):
                r = requests.get(
                    "https://nominatim.openstreetmap.org/search",
                    params={"q": addr, "format": "json", "limit": 1},
                    headers={"User-Agent": "TaxiResApp/1.0 (samy.ouali@etu.unige.ch)"},
                    timeout=5,
                )
                data = r.json()
                if not data:
                    return None, None
                return float(data[0]["lat"]), float(data[0]["lon"])

            depart_lat, depart_lon = geocode(depart_adresse)
            arrivee_lat, arrivee_lon = geocode(arrivee_adresse)
            if None in (depart_lat, depart_lon, arrivee_lat, arrivee_lon):
                flash("Adresse introuvable. Vérifiez l'orthographe.", "danger")
                return redirect(url_for("client.reserver"))

            distance = distance_euclidienne_km(
                depart_lat, depart_lon, arrivee_lat, arrivee_lon
            )
        except (KeyError, ValueError):
            flash("Formulaire invalide.", "danger")
            return redirect(url_for("client.reserver"))

        categorie = db.session.get(CategorieTaxi, categorie_id)
        tranches = TrancheTarif.query.all()
        prix, tranche = calculer_prix_estime(
            categorie, distance, nb_p, nb_b, depart_souhaite, tranches
        )

        course = Course(
            id_client=current_user.id_utilisateur,
            depart_adresse=request.form["depart_adresse"],
            arrivee_adresse=request.form["arrivee_adresse"],
            depart_lat=depart_lat,
            depart_lon=depart_lon,
            arrivee_lat=arrivee_lat,
            arrivee_lon=arrivee_lon,
            distance_estimee_km=distance,
            nb_personnes=nb_p,
            nb_bagages=nb_b,
            date_depart_souhaitee=depart_souhaite,
            prix_estime=prix,
            id_tranche=tranche.id_tranche if tranche else None,
        )
        db.session.add(course)
        db.session.commit()

        # Recherche des chauffeurs + envoi de notifications
        candidats = chercher_candidats(
            course,
            rayon_km=Config.RAYON_RECHERCHE_KM,
            poids_note=Config.POIDS_NOTE,
            poids_proximite=Config.POIDS_PROXIMITE,
            poids_fiabilite=Config.POIDS_FIABILITE,
        )
        if not candidats:
            course.statut = "ECHEC"
            db.session.commit()
            flash(
                "Aucun chauffeur disponible pour le moment. Réessayez plus tard.",
                "warning",
            )
            return redirect(url_for("client.dashboard"))

        notifier_candidats(course, candidats)
        flash(
            f"Course #{course.id_course} créée. "
            f"{len(candidats)} chauffeur(s) notifié(s). Prix estimé : {prix} €.",
            "success",
        )
        return redirect(url_for("client.suivi", id_course=course.id_course))

    return render_template("client/reserver.html", categories=categories)


@bp.route("/course/<int:id_course>")
@login_required
@client_required
def suivi(id_course: int):
    course = Course.query.get_or_404(id_course)
    if course.id_client != current_user.id_utilisateur:
        abort(403)
    return render_template("client/suivi.html", course=course)


@bp.route("/course/<int:id_course>/noter", methods=["POST"])
@login_required
@client_required
def noter(id_course: int):
    course = Course.query.get_or_404(id_course)
    if course.id_client != current_user.id_utilisateur:
        abort(403)
    if course.statut != "TERMINEE":
        flash("Vous ne pouvez noter qu'une course terminée.", "warning")
        return redirect(url_for("client.suivi", id_course=id_course))

    note = int(request.form.get("note", 0))
    if not 1 <= note <= 5:
        flash("Note invalide.", "danger")
        return redirect(url_for("client.suivi", id_course=id_course))

    evaluation = Evaluation(
        id_course=id_course,
        auteur_id=current_user.id_utilisateur,
        cible_id=course.id_chauffeur,
        note=note,
        commentaire=request.form.get("commentaire", "")[:500],
    )
    db.session.add(evaluation)
    db.session.commit()
    flash("Merci pour votre évaluation !", "success")
    return redirect(url_for("client.suivi", id_course=id_course))
