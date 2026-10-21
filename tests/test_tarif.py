"""
Tests unitaires – tarif.py
Fonctions testées : tranche_active, calculer_prix_estime
"""
import pytest
from datetime import datetime, time
from decimal import Decimal
from unittest.mock import MagicMock

from app.services.tarif import tranche_active, calculer_prix_estime


# ── Helpers : objets mock ──────────────────────────────────────────────────────

def make_tranche(debut: time, fin: time, coefficient: float) -> MagicMock:
    tr = MagicMock()
    tr.heure_debut = debut
    tr.heure_fin = fin
    tr.coefficient = coefficient
    return tr


def make_categorie(
    prix_base=5.0,
    tarif_km=2.0,
    supplement_personne=1.0,
    supplement_bagage=0.50,
) -> MagicMock:
    cat = MagicMock()
    cat.prix_base = prix_base
    cat.tarif_km = tarif_km
    cat.supplement_personne = supplement_personne
    cat.supplement_bagage = supplement_bagage
    return cat


# ── tranche_active ─────────────────────────────────────────────────────────────

class TestTrancheActive:

    def test_heure_dans_tranche_normale(self):
        """Heure dans une tranche qui ne traverse pas minuit."""
        tr = make_tranche(time(8, 0), time(20, 0), 1.0)
        moment = datetime(2024, 1, 15, 10, 0)
        assert tranche_active(moment, [tr]) is tr

    def test_heure_hors_tranche_normale(self):
        """Heure en dehors de la tranche → None."""
        tr = make_tranche(time(8, 0), time(20, 0), 1.0)
        moment = datetime(2024, 1, 15, 22, 0)
        assert tranche_active(moment, [tr]) is None

    def test_tranche_traverse_minuit_avant_minuit(self):
        """Tranche nocturne (22h → 06h) : heure 23h00 est couverte."""
        tr = make_tranche(time(22, 0), time(6, 0), 1.5)
        moment = datetime(2024, 1, 15, 23, 0)
        assert tranche_active(moment, [tr]) is tr

    def test_tranche_traverse_minuit_apres_minuit(self):
        """Tranche nocturne (22h → 06h) : heure 03h00 est couverte."""
        tr = make_tranche(time(22, 0), time(6, 0), 1.5)
        moment = datetime(2024, 1, 15, 3, 0)
        assert tranche_active(moment, [tr]) is tr

    def test_tranche_traverse_minuit_hors_plage(self):
        """Tranche nocturne (22h → 06h) : heure 12h00 n'est pas couverte."""
        tr = make_tranche(time(22, 0), time(6, 0), 1.5)
        moment = datetime(2024, 1, 15, 12, 0)
        assert tranche_active(moment, [tr]) is None

    def test_liste_vide_retourne_none(self):
        """Aucune tranche disponible → None."""
        moment = datetime(2024, 1, 15, 10, 0)
        assert tranche_active(moment, []) is None

    def test_premiere_tranche_correspondante_retournee(self):
        """En cas de chevauchement, la première tranche correspondante est retournée."""
        tr1 = make_tranche(time(8, 0), time(20, 0), 1.0)
        tr2 = make_tranche(time(6, 0), time(22, 0), 1.2)
        moment = datetime(2024, 1, 15, 10, 0)
        result = tranche_active(moment, [tr1, tr2])
        assert result is tr1

    def test_heure_exactement_au_debut(self):
        """Heure exactement à heure_debut est incluse."""
        tr = make_tranche(time(8, 0), time(20, 0), 1.0)
        moment = datetime(2024, 1, 15, 8, 0)
        assert tranche_active(moment, [tr]) is tr

    def test_heure_exactement_a_la_fin(self):
        """Heure exactement à heure_fin est incluse."""
        tr = make_tranche(time(8, 0), time(20, 0), 1.0)
        moment = datetime(2024, 1, 15, 20, 0)
        assert tranche_active(moment, [tr]) is tr


# ── calculer_prix_estime ───────────────────────────────────────────────────────

class TestCalculerPrixEstime:

    def test_calcul_de_base(self):
        """Prix = (base + km*tarif_km) * coef, sans suppléments."""
        cat = make_categorie(prix_base=5.0, tarif_km=2.0, supplement_personne=0, supplement_bagage=0)
        tr = make_tranche(time(8, 0), time(20, 0), 1.0)
        moment = datetime(2024, 1, 15, 10, 0)

        prix, tranche = calculer_prix_estime(cat, 10.0, 1, 0, moment, [tr])

        # 5 + 2*10 = 25, coef=1 → 25.00
        assert prix == Decimal("25.00")
        assert tranche is tr

    def test_supplement_bagage(self):
        """Supplément bagage appliqué correctement."""
        cat = make_categorie(prix_base=5.0, tarif_km=2.0, supplement_personne=0, supplement_bagage=1.0)
        tr = make_tranche(time(8, 0), time(20, 0), 1.0)
        moment = datetime(2024, 1, 15, 10, 0)

        prix, _ = calculer_prix_estime(cat, 10.0, 1, 3, moment, [tr])
        # 5 + 20 + 3*1 = 28 → 28.00
        assert prix == Decimal("28.00")

    def test_supplement_personne(self):
        """Supplément personne : pas de supplément pour la 1ère personne."""
        cat = make_categorie(prix_base=5.0, tarif_km=2.0, supplement_personne=2.0, supplement_bagage=0)
        tr = make_tranche(time(8, 0), time(20, 0), 1.0)
        moment = datetime(2024, 1, 15, 10, 0)

        prix_1p, _ = calculer_prix_estime(cat, 10.0, 1, 0, moment, [tr])
        prix_3p, _ = calculer_prix_estime(cat, 10.0, 3, 0, moment, [tr])

        assert prix_1p == Decimal("25.00")       # pas de supplément
        assert prix_3p == Decimal("29.00")        # 25 + 2*(3-1) = 29

    def test_coefficient_tranche_applique(self):
        """Coefficient de tranche multiplie bien le total."""
        cat = make_categorie(prix_base=10.0, tarif_km=2.0, supplement_personne=0, supplement_bagage=0)
        tr = make_tranche(time(22, 0), time(6, 0), 1.5)
        moment = datetime(2024, 1, 15, 23, 0)

        prix, _ = calculer_prix_estime(cat, 5.0, 1, 0, moment, [tr])
        # (10 + 10) * 1.5 = 30.00
        assert prix == Decimal("30.00")

    def test_sans_tranche_coefficient_un(self):
        """Sans tranche active, coefficient = 1.00."""
        cat = make_categorie(prix_base=10.0, tarif_km=2.0, supplement_personne=0, supplement_bagage=0)
        moment = datetime(2024, 1, 15, 12, 0)

        prix, tranche = calculer_prix_estime(cat, 5.0, 1, 0, moment, [])
        assert prix == Decimal("20.00")
        assert tranche is None

    def test_prix_arrondi_au_centime(self):
        """Le prix est arrondi à 2 décimales."""
        cat = make_categorie(prix_base=1.0, tarif_km=1.0, supplement_personne=0, supplement_bagage=0)
        tr = make_tranche(time(8, 0), time(20, 0), 1.3)
        moment = datetime(2024, 1, 15, 10, 0)

        prix, _ = calculer_prix_estime(cat, 1.0, 1, 0, moment, [tr])
        # (1 + 1) * 1.3 = 2.6 → 2.60
        assert prix == Decimal("2.60")
        assert prix == prix.quantize(Decimal("0.01"))

    # ── Valeurs limites ────────────────────────────────────────────────────────

    def test_distance_zero(self):
        """Distance = 0 km : seul le prix de base est appliqué."""
        cat = make_categorie(prix_base=5.0, tarif_km=2.0, supplement_personne=0, supplement_bagage=0)
        moment = datetime(2024, 1, 15, 10, 0)

        prix, _ = calculer_prix_estime(cat, 0.0, 1, 0, moment, [])
        assert prix == Decimal("5.00")

    def test_zero_personne(self):
        """nb_personnes = 0 : max(0, -1) = 0 supplément, pas d'erreur."""
        cat = make_categorie(prix_base=5.0, tarif_km=2.0, supplement_personne=2.0, supplement_bagage=0)
        moment = datetime(2024, 1, 15, 10, 0)

        prix, _ = calculer_prix_estime(cat, 0.0, 0, 0, moment, [])
        assert prix == Decimal("5.00")  # pas de supplément négatif

    def test_supplement_none_traite_comme_zero(self):
        """supplement_personne=None ne lève pas d'erreur."""
        cat = make_categorie(prix_base=5.0, tarif_km=2.0, supplement_personne=None, supplement_bagage=None)
        moment = datetime(2024, 1, 15, 10, 0)

        prix, _ = calculer_prix_estime(cat, 5.0, 3, 2, moment, [])
        # (5 + 10 + 0 + 0) * 1 = 15.00
        assert prix == Decimal("15.00")

    def test_retourne_tuple_decimal_et_tranche(self):
        """Le retour est bien un tuple (Decimal, TrancheTarif|None)."""
        cat = make_categorie()
        moment = datetime(2024, 1, 15, 10, 0)
        result = calculer_prix_estime(cat, 5.0, 1, 0, moment, [])
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], Decimal)
