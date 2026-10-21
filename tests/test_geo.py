"""
Tests unitaires – geo.py
Fonctions testées : distance_euclidienne_km
"""
import pytest
from math import isclose
from app.services.geo import distance_euclidienne_km


class TestDistanceEuclidienneKm:
    """Tests unitaires pour la fonction distance_euclidienne_km."""

    # ── Tests normaux ──────────────────────────────────────────────────────────

    def test_meme_point_retourne_zero(self):
        """Distance d'un point à lui-même = 0."""
        dist = distance_euclidienne_km(46.2044, 6.1432, 46.2044, 6.1432)
        assert dist == pytest.approx(0.0, abs=1e-9)

    def test_geneve_lausanne(self):
        """Genève → Lausanne ≈ 55 km (tolérance ±5 km pour approx euclidienne)."""
        dist = distance_euclidienne_km(46.2044, 6.1432, 46.5197, 6.6323)
        assert 45.0 <= dist <= 65.0

    def test_symetrie(self):
        """dist(A, B) == dist(B, A)."""
        d1 = distance_euclidienne_km(46.2044, 6.1432, 46.5197, 6.6323)
        d2 = distance_euclidienne_km(46.5197, 6.6323, 46.2044, 6.1432)
        assert d1 == pytest.approx(d2, rel=1e-9)

    def test_meme_latitude_distance_longitudinale(self):
        """Sur la même latitude, 1° de longitude ≈ 111*cos(lat) km."""
        lat = 46.0
        dist = distance_euclidienne_km(lat, 6.0, lat, 7.0)
        from math import cos, radians
        attendu = 111 * cos(radians(lat))
        assert dist == pytest.approx(attendu, rel=0.01)

    def test_meme_longitude_distance_latitudinale(self):
        """Sur la même longitude, 1° de latitude ≈ 111 km."""
        dist = distance_euclidienne_km(46.0, 6.0, 47.0, 6.0)
        assert dist == pytest.approx(111.0, rel=0.01)

    def test_courte_distance_quelques_metres(self):
        """Très petite distance (quelques mètres) reste positive."""
        dist = distance_euclidienne_km(46.2044, 6.1432, 46.2045, 6.1433)
        assert dist > 0
        assert dist < 0.2  # moins de 200 m

    # ── Valeurs limites ────────────────────────────────────────────────────────

    def test_coordonnees_equateur(self):
        """Fonctionne à l'équateur (lat = 0)."""
        dist = distance_euclidienne_km(0.0, 0.0, 0.0, 1.0)
        assert dist == pytest.approx(111.0, rel=0.01)

    def test_coordonnees_negatives(self):
        """Fonctionne avec des latitudes/longitudes négatives."""
        dist = distance_euclidienne_km(-33.8688, 151.2093, -33.8688, 152.2093)
        assert dist > 0

    def test_longues_distances(self):
        """Paris → New York ≈ 5 800 km (approx euclidienne moins précise sur grandes distances)."""
        dist = distance_euclidienne_km(48.8566, 2.3522, 40.7128, -74.0060)
        assert 4000 < dist < 8000

    def test_valeur_retournee_est_float(self):
        """Le résultat doit être un float."""
        dist = distance_euclidienne_km(46.2044, 6.1432, 46.5197, 6.6323)
        assert isinstance(dist, float)
