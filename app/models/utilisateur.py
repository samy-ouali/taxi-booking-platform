"""
Modèles des utilisateurs : héritage (Utilisateur -> Client, Chauffeur)
"""
from datetime import datetime
import bcrypt
from flask_login import UserMixin
from app import db, login_manager


class Utilisateur(db.Model, UserMixin):
    __tablename__ = "utilisateur"

    id_utilisateur = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(80), nullable=False)
    prenom = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True)
    telephone = db.Column(db.String(20), nullable=False)
    mot_de_passe_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum("CLIENT", "CHAUFFEUR", "ADMIN"), nullable=False)
    note_moyenne = db.Column(db.Numeric(3, 2), default=0.00)
    actif = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # ------------------------------------------------------------------
    # Authentification (bcrypt)
    # ------------------------------------------------------------------
    def set_password(self, plain_password: str) -> None:
        self.mot_de_passe_hash = bcrypt.hashpw(
            plain_password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

    def check_password(self, plain_password: str) -> bool:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            self.mot_de_passe_hash.encode("utf-8"),
        )

    # Requis par Flask-Login
    def get_id(self) -> str:
        return str(self.id_utilisateur)

    def __repr__(self) -> str:
        return f"<Utilisateur {self.email} ({self.role})>"


class Client(db.Model):
    __tablename__ = "client"

    id_client = db.Column(
        db.Integer,
        db.ForeignKey("utilisateur.id_utilisateur", ondelete="CASCADE"),
        primary_key=True,
    )
    preferences_paiement = db.Column(
        db.Enum("CARTE", "ESPECES", "APPLICATION"), default="CARTE"
    )

    utilisateur = db.relationship(
        "Utilisateur", backref=db.backref("client", uselist=False)
    )


class Chauffeur(db.Model):
    __tablename__ = "chauffeur"

    id_chauffeur = db.Column(
        db.Integer,
        db.ForeignKey("utilisateur.id_utilisateur", ondelete="CASCADE"),
        primary_key=True,
    )
    numero_permis = db.Column(db.String(30), nullable=False, unique=True)
    statut = db.Column(
        db.Enum("DISPONIBLE", "OCCUPE", "HORS_SERVICE"), default="DISPONIBLE"
    )
    zone_service = db.Column(db.String(80))
    taux_acceptation = db.Column(db.Numeric(5, 2), default=100.00)
    taux_annulation = db.Column(db.Numeric(5, 2), default=0.00)

    utilisateur = db.relationship(
        "Utilisateur", backref=db.backref("chauffeur", uselist=False)
    )
    taxis = db.relationship("Taxi", back_populates="chauffeur")

    # ------------------------------------------------------------------
    # Indicateur de fiabilité (utilisé par l'algo de matching)
    # ------------------------------------------------------------------
    @property
    def fiabilite(self) -> float:
        """
        Fiabilité = combinaison du taux d'acceptation et de non-annulation.
        Plage [0,1].
        """
        acc = float(self.taux_acceptation or 0) / 100.0
        ann = float(self.taux_annulation or 0) / 100.0
        return max(0.0, min(1.0, 0.7 * acc + 0.3 * (1 - ann)))


@login_manager.user_loader
def load_user(user_id: str):
    return db.session.get(Utilisateur, int(user_id))
