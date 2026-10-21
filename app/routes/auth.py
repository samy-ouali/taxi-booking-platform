"""
Routes d'authentification : inscription, connexion, déconnexion.
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required

from app import db
from app.models import Utilisateur, Client, Chauffeur

bp = Blueprint("auth", __name__)


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = Utilisateur.query.filter_by(email=email).first()
        if user and user.check_password(password) and user.actif:
            login_user(user)
            flash(f"Bienvenue {user.prenom} !", "success")
            return redirect(url_for("main.index"))
        flash("Identifiants incorrects", "danger")
    return render_template("auth/login.html")


@bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        role = request.form.get("role", "CLIENT")
        email = request.form.get("email", "").strip().lower()

        if Utilisateur.query.filter_by(email=email).first():
            flash("Cet email est déjà utilisé.", "danger")
            return redirect(url_for("auth.register"))

        user = Utilisateur(
            nom=request.form.get("nom", "").strip(),
            prenom=request.form.get("prenom", "").strip(),
            email=email,
            telephone=request.form.get("telephone", "").strip(),
            role=role,
        )
        user.set_password(request.form.get("password", ""))
        db.session.add(user)
        db.session.flush()  # pour récupérer l'id

        if role == "CLIENT":
            db.session.add(Client(id_client=user.id_utilisateur))
        elif role == "CHAUFFEUR":
            db.session.add(
                Chauffeur(
                    id_chauffeur=user.id_utilisateur,
                    numero_permis=request.form.get("numero_permis", "N/A"),
                    zone_service=request.form.get("zone_service", ""),
                )
            )

        db.session.commit()
        flash("Compte créé, vous pouvez vous connecter.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")


@bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Déconnecté.", "info")
    return redirect(url_for("main.index"))
