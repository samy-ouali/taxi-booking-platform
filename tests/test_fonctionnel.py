"""
Tests fonctionnels – scénarios utilisateur complets
Simule des cas d'usage réels du système de réservation taxi.
"""
import pytest
from datetime import datetime, time
from decimal import Decimal
from unittest.mock import MagicMock, patch

from app.services.geo import distance_euclidienne_km
from app.services.tarif import calculer_prix_estime, tranche_active
from app.services.matching import _normalise_note, _normalise_proximite


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


class TestScenarioReservationClient:
    """
    Scénario 1 : Un client réserve un taxi pour aller à l'aéroport.
    Vérifie le calcul de distance et de prix de bout en bout.
    """

    def test_reservation_aeroport_jour(self):
        """
        Client au centre-ville, aéroport à ~5 km.
        Course de jour, 1 personne, 2 bagages.
        Le prix doit être calculé correctement.
        """
        # Étape 1 : calcul de la distance
        dist = distance_euclidienne_km(46.2044, 6.1432, 46.2381, 6.1089)
        assert 2.0 <= dist <= 10.0

        # Étape 2 : sélection de la tranche horaire
        tranches = [make_tranche(time(6, 0), time(22, 0), 1.0)]
        moment = datetime(2024, 6, 15, 8, 30)
        tr = tranche_active(moment, tranches)
        assert tr is not None

        # Étape 3 : calcul du prix
        cat = make_categorie(prix_base=4.0, tarif_km=2.5, sup_p=0, sup_b=1.0)
        prix, _ = calculer_prix_estime(cat, dist, 1, 2, moment, tranches)

        assert prix > Decimal("0")
        assert isinstance(prix, Decimal)

    def test_reservation_nuit_majoration_appliquee(self):
        """
        Même trajet de nuit → prix plus élevé grâce au coefficient nocturne.
        """
        dist = distance_euclidienne_km(46.2044, 6.1432, 46.2381, 6.1089)
        tranches = [
            make_tranche(time(6, 0), time(22, 0), 1.0),
            make_tranche(time(22, 0), time(6, 0), 1.5),
        ]
        cat = make_categorie(prix_base=4.0, tarif_km=2.5, sup_p=0, sup_b=0)

        prix_jour, _ = calculer_prix_estime(cat, dist, 1, 0, datetime(2024, 6, 15, 10, 0), tranches)
        prix_nuit, _ = calculer_prix_estime(cat, dist, 1, 0, datetime(2024, 6, 15, 23, 0), tranches)

        assert prix_nuit > prix_jour
        assert prix_nuit == pytest.approx(prix_jour * Decimal("1.5"), rel=Decimal("0.01"))


class TestScenarioMatchingChauffeur:
    """
    Scénario 2 : Sélection du meilleur chauffeur parmi des candidats.
    Vérifie que le scoring favorise un chauffeur bien noté ET proche.
    """

    def test_chauffeur_bien_note_et_proche_favori(self):
        """
        Chauffeur A : note 5/5, distance 1 km
        Chauffeur B : note 2/5, distance 4 km
        → Score A > Score B
        """
        rayon = 5.0
        poids_note, poids_prox, poids_fiab = 0.50, 0.30, 0.20

        score_a = (
            poids_note * _normalise_note(5.0)
            + poids_prox * _normalise_proximite(1.0, rayon)
            + poids_fiab * 0.9
        )
        score_b = (
            poids_note * _normalise_note(2.0)
            + poids_prox * _normalise_proximite(4.0, rayon)
            + poids_fiab * 0.5
        )

        assert score_a > score_b

    def test_chauffeur_hors_rayon_exclu(self):
        """
        Un chauffeur à 6 km avec rayon = 5 km → proximité = 0 (clampée).
        """
        proximite = _normalise_proximite(6.0, 5.0)
        assert proximite == 0.0

    def test_score_total_dans_intervalle_zero_un(self):
        """
        Quel que soit le chauffeur, son score composite est dans [0, 1].
        """
        for note in [None, 0, 2.5, 5]:
            for dist in [0.0, 2.5, 5.0]:
                score = (
                    0.50 * _normalise_note(note)
                    + 0.30 * _normalise_proximite(dist, 5.0)
                    + 0.20 * 0.8  # fiabilité fixe
                )
                assert 0.0 <= score <= 1.0, f"Score hors bornes pour note={note}, dist={dist}"


class TestScenarioPrixNonNegatif:
    """
    Scénario 3 : Le prix ne doit jamais être négatif, quelle que soit la saisie.
    """

    @pytest.mark.parametrize("distance,nb_p,nb_b", [
        (0.0, 0, 0),
        (0.0, 1, 0),
        (100.0, 1, 0),
        (0.001, 1, 0),
    ])
    def test_prix_toujours_positif_ou_nul(self, distance, nb_p, nb_b):
        cat = make_categorie(prix_base=5.0, tarif_km=2.0, sup_p=1.0, sup_b=0.5)
        moment = datetime(2024, 6, 15, 10, 0)
        prix, _ = calculer_prix_estime(cat, distance, nb_p, nb_b, moment, [])
        assert prix >= Decimal("0")
