"""
Tests unitaires qui ne dépendent PAS de la BDD :
    - géographie (euclidienne)
    - normalisation note / proximité
    - calcul de prix (tarif)
    - calcul de score final

Lancer :
    python -m unittest tests/test_matching_math.py
"""
import os
import sys
import unittest
from datetime import datetime, time
from decimal import Decimal
from types import SimpleNamespace

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from app.services.geo import distance_euclidienne_km
from app.services.matching import _normalise_note, _normalise_proximite
from app.services.tarif import tranche_active, calculer_prix_estime


class TestGeo(unittest.TestCase):
    def test_distance_paris_orly(self):
        # Paris (Notre-Dame) -> Aéroport Orly, environ 13 km
        d = distance_euclidienne_km(48.8530, 2.3499, 48.7262, 2.3652)
        self.assertAlmostEqual(d, 14, delta=2)

    def test_distance_same_point(self):
        self.assertAlmostEqual(distance_euclidienne_km(48.8566, 2.3522, 48.8566, 2.3522), 0.0)


class TestNormalisation(unittest.TestCase):
    def test_note(self):
        self.assertEqual(_normalise_note(None), 0.0)
        self.assertEqual(_normalise_note(0), 0.0)
        self.assertEqual(_normalise_note(5), 1.0)
        self.assertAlmostEqual(_normalise_note(4.5), 0.9)

    def test_proximite(self):
        # dist = 0 -> score max, dist = rayon -> 0
        self.assertAlmostEqual(_normalise_proximite(0, 5), 1.0)
        self.assertAlmostEqual(_normalise_proximite(5, 5), 0.0)
        self.assertAlmostEqual(_normalise_proximite(2.5, 5), 0.5)


class TestTarif(unittest.TestCase):
    def _tranches(self):
        return [
            SimpleNamespace(libelle="Jour", heure_debut=time(6, 0),
                            heure_fin=time(20, 0), coefficient=Decimal("1.00")),
            SimpleNamespace(libelle="Nuit", heure_debut=time(20, 0),
                            heure_fin=time(6, 0), coefficient=Decimal("1.25")),
        ]

    def test_tranche_jour(self):
        tr = tranche_active(datetime(2026, 4, 21, 14, 0), self._tranches())
        self.assertEqual(tr.libelle, "Jour")

    def test_tranche_nuit_avant_minuit(self):
        tr = tranche_active(datetime(2026, 4, 21, 23, 0), self._tranches())
        self.assertEqual(tr.libelle, "Nuit")

    def test_tranche_nuit_apres_minuit(self):
        tr = tranche_active(datetime(2026, 4, 21, 3, 0), self._tranches())
        self.assertEqual(tr.libelle, "Nuit")

    def test_prix_jour(self):
        cat = SimpleNamespace(
            prix_base=Decimal("3.50"), tarif_km=Decimal("1.80"),
            supplement_personne=Decimal("0.00"), supplement_bagage=Decimal("0.50"),
        )
        # 10 km, 2 pers, 1 bagage, jour
        prix, tr = calculer_prix_estime(
            cat, 10, 2, 1, datetime(2026, 4, 21, 10, 0), self._tranches()
        )
        # 3.50 + 1.80*10 + 0 + 0.50*1 = 22.00 * 1.00 = 22.00
        self.assertEqual(prix, Decimal("22.00"))
        self.assertEqual(tr.libelle, "Jour")

    def test_prix_nuit(self):
        cat = SimpleNamespace(
            prix_base=Decimal("3.50"), tarif_km=Decimal("1.80"),
            supplement_personne=Decimal("0.00"), supplement_bagage=Decimal("0.50"),
        )
        prix, tr = calculer_prix_estime(
            cat, 10, 2, 1, datetime(2026, 4, 21, 23, 30), self._tranches()
        )
        # 22.00 * 1.25 = 27.50
        self.assertEqual(prix, Decimal("27.50"))
        self.assertEqual(tr.libelle, "Nuit")


class TestScoreFormula(unittest.TestCase):
    """Vérifie le cœur de la formule de score."""

    def test_score_parfait(self):
        # note = 5, distance = 0, fiabilité = 1 -> score = 1.0
        note = _normalise_note(5)
        prox = _normalise_proximite(0, 5)
        fiab = 1.0
        score = 0.50 * note + 0.30 * prox + 0.20 * fiab
        self.assertAlmostEqual(score, 1.0)

    def test_score_minimal(self):
        # note = 0, hors rayon, fiabilité = 0 -> score = 0
        note = _normalise_note(0)
        prox = _normalise_proximite(5, 5)
        fiab = 0.0
        score = 0.50 * note + 0.30 * prox + 0.20 * fiab
        self.assertAlmostEqual(score, 0.0)

    def test_poids_correct(self):
        # vérifie que les poids somment à 1
        self.assertAlmostEqual(0.50 + 0.30 + 0.20, 1.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
