-- =====================================================================
-- Jeu de données de test pour la démo du checkpoint 2
-- Mot de passe de tous les comptes : "password" (hash bcrypt généré dans seed.py)
-- Pour démarrer rapidement, préférer l'utilisation de app/seed.py
-- =====================================================================
USE taxi_reservation;

-- Catégories de taxi
INSERT INTO categorie_taxi (libelle, capacite_personnes, capacite_bagages, prix_base, tarif_km, supplement_personne, supplement_bagage) VALUES
  ('Berline',     4, 3, 3.50, 1.80, 0.00, 0.50),
  ('Van',         7, 6, 5.00, 2.20, 0.50, 0.80),
  ('Premium',     4, 3, 6.00, 2.80, 0.00, 0.50),
  ('PMR',         3, 2, 4.50, 2.00, 0.00, 0.00);

-- Tranches tarifaires
INSERT INTO tranche_tarif (libelle, heure_debut, heure_fin, coefficient) VALUES
  ('Jour',  '06:00:00', '20:00:00', 1.00),
  ('Nuit',  '20:00:00', '23:59:59', 1.25),
  ('Nuit',  '00:00:00', '06:00:00', 1.25);
