"""
Factory Flask de l'application
"""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

from config import Config

# Instances partagées
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Veuillez vous connecter pour accéder à cette page."


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)

    # Import des modèles pour que SQLAlchemy les connaisse
    from app.models import utilisateur, course, taxi  # noqa: F401

    # Enregistrement des blueprints
    from app.routes.main import bp as main_bp
    from app.routes.auth import bp as auth_bp
    from app.routes.client import bp as client_bp
    from app.routes.chauffeur import bp as chauffeur_bp
    from app.routes.admin import bp as admin_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(client_bp, url_prefix="/client")
    app.register_blueprint(chauffeur_bp, url_prefix="/chauffeur")
    app.register_blueprint(admin_bp, url_prefix="/admin")

    return app
