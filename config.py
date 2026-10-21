"""
Configuration de l'application Flask
"""
import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")

    # Connexion MySQL (valeurs par défaut adaptées à une installation locale).
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "3306")
    DB_NAME = os.getenv("DB_NAME", "taxi_reservation")

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}"
        f"@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Paramètres métier
    RAYON_RECHERCHE_KM = float(os.getenv("RAYON_RECHERCHE_KM", "30"))
    POIDS_NOTE = 0.50
    POIDS_PROXIMITE = 0.30
    POIDS_FIABILITE = 0.20
