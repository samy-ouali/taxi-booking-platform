"""
Tests de non-régression – tarif.py
Vérifie qu'une amélioration du calcul de prix (ajout d'un plafond)
ne casse pas le comportement existant.
"""
import pytest
from datetime import datetime, time
from decimal import Decimal
from unittest.mock import MagicMock

from app.services.tarif import calculer_prix_estime


def make_tranche(debut, fin, coef):
    tr = MagicMock()
    tr.heure_debut = debut
    tr.heure_fin = fin
    tr.coefficient = coef
    return tr


def make_categorie(prix_base=5.0, tarif_km=2.0, sup_p=1.0, sup_b=0.5):
    cat = MagicMock()
    cat.prix_base = prix_base
    cat.tarif_km = tarif_km
    cat.supplement_personne = sup_p
    cat.supplement_bagage = sup_b
    return cat


# ── Baseline : résultats de référence avant extension ─────────────────────────

BASELINE = {
    "course_standard": Decimal("25.00"),    # base=5, km=10*2, 1p, 0b, coef=1
    "course_nuit":     Decimal("32.50"),    # même + coef=1.3
    "course_bagages":  Decimal("27.00"),    # base=5, km=10*2, 1p, 2b*1, coef=1
}


class TestNonRegression:
    """
    Ces tests capturent le comportement attendu AVANT toute modification.
    Si un refactoring casse un de ces tests, c'est une régression.
    """

    def setup_method(self):
        self.cat = make_categorie(prix_base=5.0, tarif_km=2.0, sup_p=1.0, sup_b=1.0)
        self.tranche_jour = make_tranche(time(6, 0), time(22, 0), 1.0)
        self.tranche_nuit = make_tranche(time(22, 0), time(6, 0), 1.3)
        self.tranches = [self.tranche_jour, self.tranche_nuit]

    def test_course_standard_non_regressee(self):
        """Course de base (jour, 1p, 0b, 10km) → 25.00 CHF."""
        prix, _ = calculer_prix_estime(
            self.cat, 10.0, 1, 0, datetime(2024, 6, 15, 10, 0), self.tranches
        )
        assert prix == BASELINE["course_standard"]

    def test_course_nuit_non_regressee(self):
        """Course de nuit (coef 1.3) → 32.50 CHF."""
        prix, _ = calculer_prix_estime(
            self.cat, 10.0, 1, 0, datetime(2024, 6, 15, 23, 0), self.tranches
        )
        assert prix == BASELINE["course_nuit"]

    def test_course_avec_bagages_non_regressee(self):
        """Course jour + 2 bagages → 27.00 CHF."""
        prix, _ = calculer_prix_estime(
            self.cat, 10.0, 1, 2, datetime(2024, 6, 15, 10, 0), self.tranches
        )
        assert prix == BASELINE["course_bagages"]

    def test_supplement_personne_non_regressee(self):
        """
        Vérification que le supplément personne ne s'applique qu'à partir de la 2e.
        3 personnes → 2 suppléments.
        """
        prix, _ = calculer_prix_estime(
            self.cat, 10.0, 3, 0, datetime(2024, 6, 15, 10, 0), self.tranches
        )
        # 5 + 20 + 2*1 = 27.00
        assert prix == Decimal("27.00")

    def test_type_retour_non_regressee(self):
        """Le type de retour reste toujours un tuple (Decimal, tranche)."""
        result = calculer_prix_estime(
            self.cat, 5.0, 1, 0, datetime(2024, 6, 15, 10, 0), self.tranches
        )
        assert isinstance(result, tuple)
        assert isinstance(result[0], Decimal)
