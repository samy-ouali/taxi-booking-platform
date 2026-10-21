"""
Routes publiques : page d'accueil, pages statiques.
"""
from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user

bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    if current_user.is_authenticated:
        if current_user.role == "CLIENT":
            return redirect(url_for("client.dashboard"))
        if current_user.role == "CHAUFFEUR":
            return redirect(url_for("chauffeur.dashboard"))
        if current_user.role == "ADMIN":
            return redirect(url_for("admin.dashboard"))
    return render_template("index.html")
