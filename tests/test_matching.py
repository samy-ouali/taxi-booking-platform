"""
Tests unitaires – matching.py
Fonctions testées : _normalise_note, _normalise_proximite
(fonctions pures, sans dépendance base de données)
"""
import pytest
from decimal import Decimal

from app.services.matching import _normalise_note, _normalise_proximite


class TestNormaliseNote:
    """Tests pour _normalise_note : note/5 → [0, 1]."""

    def test_note_none_retourne_zero(self):
        """Note inconnue → 0.0."""
        assert _normalise_note(None) == 0.0

    def test_note_zero(self):
        """Note 0 → 0.0."""
        assert _normalise_note(0) == 0.0

    def test_note_cinq(self):
        """Note maximale 5 → 1.0."""
        assert _normalise_note(5) == pytest.approx(1.0)

    def test_note_deux_virgule_cinq(self):
        """Note 2.5 → 0.5."""
        assert _normalise_note(2.5) == pytest.approx(0.5)

    def test_note_decimal(self):
        """Accepte un Decimal."""
        assert _normalise_note(Decimal("4.0")) == pytest.approx(0.8)

    def test_note_negative_clampee_a_zero(self):
        """Note négative → clampée à 0.0 (pas de score négatif)."""
        assert _normalise_note(-1) == 0.0

    def test_note_superieure_a_cinq_clampee_a_un(self):
        """Note > 5 → clampée à 1.0."""
        assert _normalise_note(10) == pytest.approx(1.0)

    def test_note_un(self):
        assert _normalise_note(1) == pytest.approx(0.2)

    def test_retourne_float(self):
        assert isinstance(_normalise_note(3.0), float)


class TestNormaliseProximite:
    """Tests pour _normalise_proximite : plus c'est proche, plus le score est élevé."""

    def test_distance_zero_retourne_un(self):
        """Chauffeur sur place → score maximal 1.0."""
        assert _normalise_proximite(0.0, 5.0) == pytest.approx(1.0)

    def test_distance_egale_rayon_retourne_zero(self):
        """Chauffeur exactement à la limite du rayon → score 0.0."""
        assert _normalise_proximite(5.0, 5.0) == pytest.approx(0.0)

    def test_distance_superieure_rayon_clampee_zero(self):
        """Distance > rayon → score 0.0 (ne peut pas être négatif)."""
        assert _normalise_proximite(10.0, 5.0) == 0.0

    def test_rayon_zero_retourne_zero(self):
        """Rayon nul → score 0.0 (division par zéro évitée)."""
        assert _normalise_proximite(0.0, 0.0) == 0.0

    def test_moitie_du_rayon(self):
        """Distance = rayon/2 → score 0.5."""
        assert _normalise_proximite(2.5, 5.0) == pytest.approx(0.5)

    def test_rayon_negatif_retourne_zero(self):
        """Rayon négatif → traité comme invalide → 0.0."""
        assert _normalise_proximite(1.0, -5.0) == 0.0

    def test_grande_distance_grande_rayon(self):
        """Fonctionne avec de grandes valeurs."""
        result = _normalise_proximite(50.0, 100.0)
        assert result == pytest.approx(0.5)

    def test_retourne_float(self):
        assert isinstance(_normalise_proximite(1.0, 5.0), float)
