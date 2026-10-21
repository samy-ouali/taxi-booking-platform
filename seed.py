"""
Script de peuplement de la BDD (données de test pour la démo).

Usage :
    python seed.py

Pré-requis :
    - BDD `taxi_reservation` créée (lancer sql/01_schema.sql dans phpMyAdmin)
    - fichier .env configuré
"""
from datetime import datetime, time, timedelta
from decimal import Decimal

from app import create_app, db
from app.models import (
    Utilisateur,
    Client,
    Chauffeur,
    CategorieTaxi,
    TrancheTarif,
    Taxi,
    Course,
    Evaluation,
)

app = create_app()


def run():
    with app.app_context():
        # Nettoyage complet
        db.drop_all()
        db.create_all()

        # 1. Catégories
        cats = {
            "Berline": CategorieTaxi(
                libelle="Berline", capacite_personnes=4, capacite_bagages=3,
                prix_base=Decimal("3.50"), tarif_km=Decimal("1.80"),
                supplement_personne=Decimal("0.00"), supplement_bagage=Decimal("0.50"),
            ),
            "Van": CategorieTaxi(
                libelle="Van", capacite_personnes=7, capacite_bagages=6,
                prix_base=Decimal("5.00"), tarif_km=Decimal("2.20"),
                supplement_personne=Decimal("0.50"), supplement_bagage=Decimal("0.80"),
            ),
            "Premium": CategorieTaxi(
                libelle="Premium", capacite_personnes=4, capacite_bagages=3,
                prix_base=Decimal("6.00"), tarif_km=Decimal("2.80"),
                supplement_personne=Decimal("0.00"), supplement_bagage=Decimal("0.50"),
            ),
        }
        db.session.add_all(cats.values())

        # 2. Tranches tarifaires
        db.session.add_all([
            TrancheTarif(libelle="Jour",  heure_debut=time(6, 0), heure_fin=time(20, 0), coefficient=Decimal("1.00")),
            TrancheTarif(libelle="Soir",  heure_debut=time(20, 0), heure_fin=time(23, 59), coefficient=Decimal("1.25")),
            TrancheTarif(libelle="Nuit",  heure_debut=time(0, 0), heure_fin=time(6, 0), coefficient=Decimal("1.25")),
        ])

        # 3. Admin
        admin = Utilisateur(
            nom="Ouali", prenom="Samy", email="admin@taxi.local",
            telephone="0600000000", role="ADMIN", note_moyenne=Decimal("5.00")
        )
        admin.set_password("password")
        db.session.add(admin)

        # 4. Clients
        clients_data = [
            ("Dupont", "Alice",    "alice@mail.com",    "0611111111"),
            ("Martin", "Bob",      "bob@mail.com",      "0622222222"),
            ("Bernard", "Camille", "camille@mail.com",  "0633333333"),
        ]
        clients = []
        for nom, prenom, email, tel in clients_data:
            u = Utilisateur(nom=nom, prenom=prenom, email=email,
                            telephone=tel, role="CLIENT")
            u.set_password("password")
            db.session.add(u)
            db.session.flush()
            c = Client(id_client=u.id_utilisateur, preferences_paiement="CARTE")
            db.session.add(c)
            clients.append((u, c))

        # 5. Chauffeurs + taxis
        # Pos GPS autour de Paris (pour la démo)
        chauffeurs_data = [
            ("Durand", "David",   "david@taxi.com",   "0644444444", "P-1001", 4.9, 98, 2,  48.8566, 2.3522, "Berline",  "AB-123-CD", "Peugeot 508"),
            ("Petit",  "Emma",    "emma@taxi.com",    "0655555555", "P-1002", 4.6, 92, 5,  48.8600, 2.3400, "Berline",  "EF-456-GH", "Renault Talisman"),
            ("Roux",   "Fabien",  "fabien@taxi.com",  "0666666666", "P-1003", 4.2, 85, 8,  48.8710, 2.3460, "Van",      "IJ-789-KL", "Mercedes Vito"),
            ("Leroy",  "Gina",    "gina@taxi.com",    "0677777777", "P-1004", 4.8, 96, 3,  48.8500, 2.3600, "Premium",  "MN-012-OP", "BMW 5"),
            ("Morel",  "Hugo",    "hugo@taxi.com",    "0688888888", "P-1005", 3.9, 80, 10, 48.8800, 2.3000, "Berline",  "QR-345-ST", "Skoda Octavia"),
            ("Favre",  "Iris",   "iris@taxi.com",   "0699999999", "P-2001", 4.7, 95, 4, 46.2044, 6.1432, "Berline",  "GE-001-VD", "Tesla Model 3"),
            ("Dubois", "Julien", "julien@taxi.com", "0700000000", "P-2002", 4.5, 90, 6, 46.1885, 6.2362, "Van",      "GE-002-VD", "Mercedes Vito"),
            ("Lola", "Moreau", "lola@taxi.com", "0712345678", "P-3003", 4.9, 100, 0, 46.1953, 6.2024, "Berline", "GE-003-VD", "Audi A4"),

        ]
        chauffeurs = []
        for (nom, prenom, email, tel, permis, note, tx_acc, tx_ann,
             lat, lon, cat, immat, modele) in chauffeurs_data:
            u = Utilisateur(
                nom=nom, prenom=prenom, email=email, telephone=tel,
                role="CHAUFFEUR", note_moyenne=Decimal(str(note)),
            )
            u.set_password("password")
            db.session.add(u)
            db.session.flush()
            ch = Chauffeur(
                id_chauffeur=u.id_utilisateur,
                numero_permis=permis,
                statut="DISPONIBLE",
                zone_service="Paris",
                taux_acceptation=Decimal(str(tx_acc)),
                taux_annulation=Decimal(str(tx_ann)),
            )
            db.session.add(ch)
            db.session.flush()
            t = Taxi(
                immatriculation=immat,
                marque_modele=modele,
                id_categorie=cats[cat].id_categorie,
                id_chauffeur=ch.id_chauffeur,
                statut_disponibilite="DISPONIBLE",
                latitude=Decimal(str(lat)),
                longitude=Decimal(str(lon)),
            )
            db.session.add(t)
            chauffeurs.append((u, ch, t))

        db.session.commit()

        # 6. Une course historique terminée (pour avoir une évaluation)
        c_client = clients[0][1]
        c_chauf = chauffeurs[0][1]
        c_taxi = chauffeurs[0][2]
        course = Course(
            id_client=c_client.id_client,
            id_chauffeur=c_chauf.id_chauffeur,
            id_taxi=c_taxi.id_taxi,
            depart_adresse="Gare de Lyon, Paris",
            arrivee_adresse="Aéroport Orly",
            depart_lat=Decimal("48.8448"), depart_lon=Decimal("2.3735"),
            arrivee_lat=Decimal("48.7262"), arrivee_lon=Decimal("2.3652"),
            distance_estimee_km=Decimal("18.5"),
            nb_personnes=2, nb_bagages=2,
            date_depart_souhaitee=datetime.utcnow() - timedelta(days=1),
            statut="TERMINEE",
            prix_estime=Decimal("38.50"),
            prix_final=Decimal("38.50"),
        )
        db.session.add(course)
        db.session.flush()
        db.session.add(Evaluation(
            id_course=course.id_course,
            auteur_id=clients[0][0].id_utilisateur,
            cible_id=chauffeurs[0][0].id_utilisateur,
            note=5, commentaire="Très bon chauffeur, ponctuel.",
        ))

        db.session.commit()

        print("=" * 60)
        print(" Base peuplée avec succès.")
        print(" Comptes de test (mot de passe : password) :")
        print(" - Admin    : admin@taxi.local")
        print(" - Client   : alice@mail.com / bob@mail.com / camille@mail.com")
        print(" - Chauffeur: david@taxi.com / emma@taxi.com / fabien@taxi.com …")
        print("=" * 60)


if __name__ == "__main__":
    run()
