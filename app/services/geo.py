"""
Utilitaires géographiques (distance euclidienne).
"""
from math import radians, cos, sqrt


def distance_euclidienne_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Distance euclidienne approximative entre deux points GPS (en km).
    Convertit les degrés en kilomètres puis applique le théorème de Pythagore.
    """
    # 1 degré de latitude ≈ 111 km partout sur Terre
    # 1 degré de longitude ≈ 111 km × cos(latitude), car les méridiens
    # se rapprochent quand on s'éloigne de l'équateur
    
    lat_moyenne = radians((lat1 + lat2) / 2)
    dx = (lon2 - lon1) * 111 * cos(lat_moyenne)
    dy = (lat2 - lat1) * 111
    return sqrt(dx ** 2 + dy ** 2)
