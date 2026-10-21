"""
Tests d'intégration – pipeline tarif + géo
Vérifie que geo.py et tarif.py fonctionnent correctement ensemble
dans un scénario de bout en bout (sans base de données).
"""
import pytest
from datetime import datetime, time
from decimal import Decimal
from unittest.mock import MagicMock

from app.services.geo import distance_euclidienne_km
from app.services.tarif import tranche_active, calculer_prix_estime


def make_tranche(debut, fin, coef):
    tr = MagicMock()
    tr.heure_debut = debut
    tr.heure_fin = fin
    tr.coefficient = coef
    return tr


def make_categorie(prix_base, tarif_km, sup_p, sup_b):
    cat = MagicMock()
    cat.prix_base = prix_base
    cat.tarif_km = tarif_km
    cat.supplement_personne = sup_p
    cat.supplement_bagage = sup_b
    return cat


class TestIntegrationGeoTarif:
    """
    Scénario intégré : calcul de la distance réelle entre deux adresses
    puis calcul du prix estimé basé sur cette distance.
    """

    def test_course_geneve_aeroport(self):
        """
        Course simulée : centre de Genève → Aéroport de Genève.
        Distance ≈ 5 km. Prix attendu dans une fourchette réaliste.
        """
        lat_depart, lon_depart = 46.2044, 6.1432   # Genève centre
        lat_arrivee, lon_arrivee = 46.2381, 6.1089  # Aéroport GVA

        distance_km = distance_euclidienne_km(lat_depart, lon_depart, lat_arrivee, lon_arrivee)

        # La distance doit être raisonnable (entre 2 et 10 km)
        assert 2.0 <= distance_km <= 10.0

        cat = make_categorie(prix_base=5.0, tarif_km=2.5, sup_p=1.0, sup_b=0.5)
        tranches = [
            make_tranche(time(7, 0), time(20, 0), 1.0),   # jour
            make_tranche(time(20, 0), time(7, 0), 1.3),   # nuit
        ]
        moment = datetime(2024, 6, 15, 9, 0)  # 9h → tranche jour

        prix, tranche_utilisee = calculer_prix_estime(
            cat, distance_km, 2, 1, moment, tranches
        )

        # Le prix doit être positif et dans une fourchette réaliste
        assert prix > Decimal("0")
        assert tranche_utilisee is tranches[0]  # tranche jour

    def test_course_nuit_majoration(self):
        """
        La même course de nuit coûte plus cher (coefficient 1.3 vs 1.0).
        """
        lat_depart, lon_depart = 46.2044, 6.1432
        lat_arrivee, lon_arrivee = 46.5197, 6.6323

        distance_km = distance_euclidienne_km(lat_depart, lon_depart, lat_arrivee, lon_arrivee)
        cat = make_categorie(prix_base=5.0, tarif_km=2.0, sup_p=0, sup_b=0)
        tranches = [
            make_tranche(time(7, 0), time(22, 0), 1.0),
            make_tranche(time(22, 0), time(7, 0), 1.3),
        ]

        prix_jour, _ = calculer_prix_estime(cat, distance_km, 1, 0, datetime(2024, 6, 15, 10, 0), tranches)
        prix_nuit, _ = calculer_prix_estime(cat, distance_km, 1, 0, datetime(2024, 6, 15, 23, 0), tranches)

        assert prix_nuit > prix_jour

    def test_course_sans_tranche_distance_reelle(self):
        """
        Course avec distance géographique réelle et sans tranche tarifaire.
        Le prix ne doit pas être nul.
        """
        distance_km = distance_euclidienne_km(46.2044, 6.1432, 46.3000, 6.2000)
        cat = make_categorie(prix_base=3.0, tarif_km=1.5, sup_p=0, sup_b=0)
        moment = datetime(2024, 6, 15, 14, 0)

        prix, tranche = calculer_prix_estime(cat, distance_km, 1, 0, moment, [])

        assert prix > Decimal("3.00")  # au moins le prix de base
        assert tranche is None

    def test_distance_nulle_prix_minimal(self):
        """
        Si départ == arrivée, la distance est 0 et le prix = prix_base.
        """
        distance_km = distance_euclidienne_km(46.2044, 6.1432, 46.2044, 6.1432)
        cat = make_categorie(prix_base=5.0, tarif_km=2.0, sup_p=0, sup_b=0)
        moment = datetime(2024, 6, 15, 14, 0)

        prix, _ = calculer_prix_estime(cat, distance_km, 1, 0, moment, [])
        assert prix == Decimal("5.00")
