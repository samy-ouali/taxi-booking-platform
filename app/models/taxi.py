"""
Modèles liés aux taxis, catégories et tranches tarifaires
"""
from app import db


class CategorieTaxi(db.Model):
    __tablename__ = "categorie_taxi"

    id_categorie = db.Column(db.Integer, primary_key=True)
    libelle = db.Column(db.String(50), nullable=False, unique=True)
    capacite_personnes = db.Column(db.Integer, nullable=False)
    capacite_bagages = db.Column(db.Integer, nullable=False)
    prix_base = db.Column(db.Numeric(6, 2), nullable=False)
    tarif_km = db.Column(db.Numeric(5, 2), nullable=False)
    supplement_personne = db.Column(db.Numeric(5, 2), default=0.00)
    supplement_bagage = db.Column(db.Numeric(5, 2), default=0.00)
    taxis = db.relationship("Taxi", back_populates="categorie")

    def __repr__(self) -> str:
        return f"<Categorie {self.libelle}>"


class Taxi(db.Model):
    __tablename__ = "taxi"

    id_taxi = db.Column(db.Integer, primary_key=True)
    immatriculation = db.Column(db.String(15), nullable=False, unique=True)
    marque_modele = db.Column(db.String(80), nullable=False)
    id_categorie = db.Column(
        db.Integer, db.ForeignKey("categorie_taxi.id_categorie"), nullable=False
    )
    id_chauffeur = db.Column(
        db.Integer, db.ForeignKey("chauffeur.id_chauffeur"), nullable=False
    )
    statut_disponibilite = db.Column(
        db.Enum("DISPONIBLE", "OCCUPE", "HORS_SERVICE"), default="DISPONIBLE"
    )
    latitude = db.Column(db.Numeric(10, 7))
    longitude = db.Column(db.Numeric(10, 7))

    categorie = db.relationship("CategorieTaxi", back_populates="taxis")
    chauffeur = db.relationship("Chauffeur", back_populates="taxis")

    def __repr__(self) -> str:
        return f"<Taxi {self.immatriculation} ({self.marque_modele})>"


class TrancheTarif(db.Model):
    __tablename__ = "tranche_tarif"

    id_tranche = db.Column(db.Integer, primary_key=True)
    libelle = db.Column(db.String(50), nullable=False)
    heure_debut = db.Column(db.Time, nullable=False)
    heure_fin = db.Column(db.Time, nullable=False)
    coefficient = db.Column(db.Numeric(4, 2), nullable=False, default=1.00)
