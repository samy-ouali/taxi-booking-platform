"""
Algorithme de matching chauffeur-course.

Principe :
    1. Filtrage : chauffeur disponible, taxi compatible (capacité >= besoin), distance <= rayon.
    2. Scoring : score = 0.50 * note_normalisée + 0.30 * proximité_normaliéee + 0.20 * fiabilité
    3. Sélection : ordre décroissant des scores, notification, premier qui accepte = chauffeur retenu.
"""
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Iterable
from app import db
from app.models import (
    Chauffeur,
    Taxi,
    Course,
    NotificationDemande,
    CategorieTaxi,
    Utilisateur,
)
from app.services.geo import distance_euclidienne_km


@dataclass
class Candidat:
    chauffeur: Chauffeur
    taxi: Taxi
    distance_km: float
    score: float


def _normalise_note(note: Decimal | float | None) -> float:
    """Note sur 5 -> valeur [0,1]."""
    if note is None:
        return 0.0
    return max(0.0, min(1.0, float(note) / 5.0))


def _normalise_proximite(distance_km: float, rayon_km: float) -> float:
    """Plus la distance est petite, plus le score est élevé."""
    if rayon_km <= 0:
        return 0.0
    return max(0.0, 1 - (distance_km / rayon_km))


def chercher_candidats(
    course: Course,
    rayon_km: float = 5.0,
    poids_note: float = 0.50,
    poids_proximite: float = 0.30,
    poids_fiabilite: float = 0.20,
) -> list[Candidat]:
    """
    Retourne la liste triée (score décroissant) des candidats
    pouvant prendre la course donnée.
    """
    # Jointure : chauffeurs disponibles + taxi + catégorie compatible
    query = (
        db.session.query(Chauffeur, Taxi, CategorieTaxi, Utilisateur)
        .join(Taxi, Taxi.id_chauffeur == Chauffeur.id_chauffeur)
        .join(CategorieTaxi, CategorieTaxi.id_categorie == Taxi.id_categorie)
        .join(Utilisateur, Utilisateur.id_utilisateur == Chauffeur.id_chauffeur)
        .filter(
            Chauffeur.statut == "DISPONIBLE",
            Taxi.statut_disponibilite == "DISPONIBLE",
            CategorieTaxi.capacite_personnes >= course.nb_personnes,
            CategorieTaxi.capacite_bagages >= course.nb_bagages,
            Utilisateur.actif.is_(True),
        )
    )

    candidats: list[Candidat] = []
    for chauffeur, taxi, _cat, user in query.all():
        if taxi.latitude is None or taxi.longitude is None:
            continue
        if course.depart_lat is None or course.depart_lon is None:
            continue

        dist = distance_euclidienne_km(
            float(taxi.latitude),
            float(taxi.longitude),
            float(course.depart_lat),
            float(course.depart_lon),
        )
        if dist > rayon_km:
            continue

        score = (
            poids_note * _normalise_note(user.note_moyenne)
            + poids_proximite * _normalise_proximite(dist, rayon_km)
            + poids_fiabilite * chauffeur.fiabilite
        )
        candidats.append(
            Candidat(chauffeur=chauffeur, taxi=taxi, distance_km=dist, score=score)
        )

    candidats.sort(key=lambda c: c.score, reverse=True)
    return candidats


def notifier_candidats(course: Course, candidats: Iterable[Candidat]) -> None:
    """
    Crée des notifications EN_ATTENTE pour chaque candidat.
    """
    for cand in candidats:
        notif = NotificationDemande(
            id_course=course.id_course,
            id_chauffeur=cand.chauffeur.id_chauffeur,
            score_selection=round(cand.score * 100, 2),
        )
        db.session.add(notif)
    db.session.commit()


def attribuer_course(course: Course, id_chauffeur_accepteur: int) -> bool:
    """
    Un chauffeur accepte : on lui attribue la course,
    on passe sa notification à ACCEPTEE et on marque les autres EXPIREE.
    """
    notif_accept = NotificationDemande.query.filter_by(
        id_course=course.id_course, id_chauffeur=id_chauffeur_accepteur
    ).first()
    if notif_accept is None or notif_accept.reponse != "EN_ATTENTE":
        return False

    # Chauffeur + taxi lié
    chauffeur = db.session.get(Chauffeur, id_chauffeur_accepteur)
    taxi = (
        Taxi.query.filter_by(
            id_chauffeur=id_chauffeur_accepteur, statut_disponibilite="DISPONIBLE"
        )
        .first()
    )
    if chauffeur is None or taxi is None:
        return False

    # Mise à jour de l'état
    course.id_chauffeur = chauffeur.id_chauffeur
    course.id_taxi = taxi.id_taxi
    course.statut = "ATTRIBUEE"

    chauffeur.statut = "OCCUPE"
    taxi.statut_disponibilite = "OCCUPE"

    notif_accept.reponse = "ACCEPTEE"
    notif_accept.date_reponse = datetime.utcnow()

    # Les autres notifications de la même course expirent
    (
        NotificationDemande.query.filter(
            NotificationDemande.id_course == course.id_course,
            NotificationDemande.id_chauffeur != id_chauffeur_accepteur,
            NotificationDemande.reponse == "EN_ATTENTE",
        ).update({"reponse": "EXPIREE"}, synchronize_session=False)
    )

    db.session.commit()
    return True
