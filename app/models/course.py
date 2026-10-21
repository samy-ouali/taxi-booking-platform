"""
Modèles : Course, NotificationDemande, Evaluation
"""
from datetime import datetime
from app import db


class Course(db.Model):
    __tablename__ = "course"

    id_course = db.Column(db.Integer, primary_key=True)
    id_client = db.Column(
        db.Integer, db.ForeignKey("client.id_client"), nullable=False
    )
    id_chauffeur = db.Column(
        db.Integer, db.ForeignKey("chauffeur.id_chauffeur")
    )
    id_taxi = db.Column(db.Integer, db.ForeignKey("taxi.id_taxi"))
    id_tranche = db.Column(
        db.Integer, db.ForeignKey("tranche_tarif.id_tranche")
    )

    depart_adresse = db.Column(db.String(160), nullable=False)
    arrivee_adresse = db.Column(db.String(160), nullable=False)
    depart_lat = db.Column(db.Numeric(10, 7))
    depart_lon = db.Column(db.Numeric(10, 7))
    arrivee_lat = db.Column(db.Numeric(10, 7))
    arrivee_lon = db.Column(db.Numeric(10, 7))

    distance_estimee_km = db.Column(db.Numeric(6, 2), nullable=False)
    nb_personnes = db.Column(db.Integer, nullable=False)
    nb_bagages = db.Column(db.Integer, nullable=False, default=0)

    date_demande = db.Column(db.DateTime, default=datetime.utcnow)
    date_depart_souhaitee = db.Column(db.DateTime, nullable=False)

    statut = db.Column(
        db.Enum(
            "EN_RECHERCHE",
            "ATTRIBUEE",
            "EN_COURS",
            "TERMINEE",
            "ANNULEE",
            "ECHEC",
        ),
        default="EN_RECHERCHE",
    )
    prix_estime = db.Column(db.Numeric(8, 2))
    prix_final = db.Column(db.Numeric(8, 2))

    notifications = db.relationship(
        "NotificationDemande", backref="course", cascade="all, delete-orphan"
    )
    evaluations = db.relationship(
        "Evaluation", backref="course", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Course #{self.id_course} {self.statut}>"


class NotificationDemande(db.Model):
    __tablename__ = "notification_demande"

    id_notification = db.Column(db.Integer, primary_key=True)
    id_course = db.Column(
        db.Integer, db.ForeignKey("course.id_course"), nullable=False
    )
    id_chauffeur = db.Column(
        db.Integer, db.ForeignKey("chauffeur.id_chauffeur"), nullable=False
    )
    date_envoi = db.Column(db.DateTime, default=datetime.utcnow)
    reponse = db.Column(
        db.Enum("EN_ATTENTE", "ACCEPTEE", "REFUSEE", "EXPIREE"),
        default="EN_ATTENTE",
    )
    date_reponse = db.Column(db.DateTime)
    score_selection = db.Column(db.Numeric(5, 2))


class Evaluation(db.Model):
    __tablename__ = "evaluation"

    id_evaluation = db.Column(db.Integer, primary_key=True)
    id_course = db.Column(
        db.Integer, db.ForeignKey("course.id_course"), nullable=False
    )
    auteur_id = db.Column(
        db.Integer, db.ForeignKey("utilisateur.id_utilisateur"), nullable=False
    )
    cible_id = db.Column(
        db.Integer, db.ForeignKey("utilisateur.id_utilisateur"), nullable=False
    )
    note = db.Column(db.Integer, nullable=False)
    commentaire = db.Column(db.String(500))
    date_eval = db.Column(db.DateTime, default=datetime.utcnow)
