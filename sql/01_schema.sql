-- =====================================================================
-- Sujet 10 : Système de réservation de taxi
-- Groupe 16 - Samy Ouali
-- Schéma logique de la base de données (MySQL / phpMyAdmin)
-- =====================================================================

DROP DATABASE IF EXISTS taxi_reservation;
CREATE DATABASE taxi_reservation
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;
USE taxi_reservation;

-- ---------------------------------------------------------------------
-- Table : utilisateur (super-type)
-- ---------------------------------------------------------------------
CREATE TABLE utilisateur (
    id_utilisateur   INT AUTO_INCREMENT PRIMARY KEY,
    nom              VARCHAR(80)  NOT NULL,
    prenom           VARCHAR(80)  NOT NULL,
    email            VARCHAR(120) NOT NULL UNIQUE,
    telephone        VARCHAR(20)  NOT NULL,
    mot_de_passe_hash VARCHAR(255) NOT NULL,
    role             ENUM('CLIENT','CHAUFFEUR','ADMIN') NOT NULL,
    note_moyenne     DECIMAL(3,2) DEFAULT 0.00,
    actif            BOOLEAN DEFAULT TRUE,
    created_at       DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- Table : client (sous-type)
-- ---------------------------------------------------------------------
CREATE TABLE client (
    id_client            INT PRIMARY KEY,
    preferences_paiement ENUM('CARTE','ESPECES','APPLICATION') DEFAULT 'CARTE',
    CONSTRAINT fk_client_utilisateur
        FOREIGN KEY (id_client) REFERENCES utilisateur(id_utilisateur)
        ON DELETE CASCADE
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- Table : chauffeur (sous-type)
-- ---------------------------------------------------------------------
CREATE TABLE chauffeur (
    id_chauffeur     INT PRIMARY KEY,
    numero_permis    VARCHAR(30)  NOT NULL UNIQUE,
    statut           ENUM('DISPONIBLE','OCCUPE','HORS_SERVICE') DEFAULT 'DISPONIBLE',
    zone_service     VARCHAR(80),
    taux_acceptation DECIMAL(5,2) DEFAULT 100.00,
    taux_annulation  DECIMAL(5,2) DEFAULT 0.00,
    CONSTRAINT fk_chauffeur_utilisateur
        FOREIGN KEY (id_chauffeur) REFERENCES utilisateur(id_utilisateur)
        ON DELETE CASCADE
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- Table : categorie_taxi
-- ---------------------------------------------------------------------
CREATE TABLE categorie_taxi (
    id_categorie        INT AUTO_INCREMENT PRIMARY KEY,
    libelle             VARCHAR(50) NOT NULL UNIQUE,
    capacite_personnes  INT NOT NULL,
    capacite_bagages    INT NOT NULL,
    prix_base           DECIMAL(6,2) NOT NULL,
    tarif_km            DECIMAL(5,2) NOT NULL,
    supplement_personne DECIMAL(5,2) DEFAULT 0.00,
    supplement_bagage   DECIMAL(5,2) DEFAULT 0.00
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- Table : taxi
-- ---------------------------------------------------------------------
CREATE TABLE taxi (
    id_taxi             INT AUTO_INCREMENT PRIMARY KEY,
    immatriculation     VARCHAR(15) NOT NULL UNIQUE,
    marque_modele       VARCHAR(80) NOT NULL,
    id_categorie        INT NOT NULL,
    id_chauffeur        INT NOT NULL,
    statut_disponibilite ENUM('DISPONIBLE','OCCUPE','HORS_SERVICE') DEFAULT 'DISPONIBLE',
    latitude            DECIMAL(10,7),
    longitude           DECIMAL(10,7),
    CONSTRAINT fk_taxi_categorie
        FOREIGN KEY (id_categorie) REFERENCES categorie_taxi(id_categorie),
    CONSTRAINT fk_taxi_chauffeur
        FOREIGN KEY (id_chauffeur) REFERENCES chauffeur(id_chauffeur)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- Table : tranche_tarif
-- ---------------------------------------------------------------------
CREATE TABLE tranche_tarif (
    id_tranche  INT AUTO_INCREMENT PRIMARY KEY,
    libelle     VARCHAR(50) NOT NULL,
    heure_debut TIME NOT NULL,
    heure_fin   TIME NOT NULL,
    coefficient DECIMAL(4,2) NOT NULL DEFAULT 1.00
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- Table : course
-- ---------------------------------------------------------------------
CREATE TABLE course (
    id_course            INT AUTO_INCREMENT PRIMARY KEY,
    id_client            INT NOT NULL,
    id_chauffeur         INT DEFAULT NULL,
    id_taxi              INT DEFAULT NULL,
    id_tranche           INT DEFAULT NULL,
    depart_adresse       VARCHAR(160) NOT NULL,
    arrivee_adresse      VARCHAR(160) NOT NULL,
    depart_lat           DECIMAL(10,7),
    depart_lon           DECIMAL(10,7),
    arrivee_lat          DECIMAL(10,7),
    arrivee_lon          DECIMAL(10,7),
    distance_estimee_km  DECIMAL(6,2) NOT NULL,
    nb_personnes         INT NOT NULL,
    nb_bagages           INT NOT NULL DEFAULT 0,
    date_demande         DATETIME DEFAULT CURRENT_TIMESTAMP,
    date_depart_souhaitee DATETIME NOT NULL,
    statut               ENUM('EN_RECHERCHE','ATTRIBUEE','EN_COURS','TERMINEE','ANNULEE','ECHEC') DEFAULT 'EN_RECHERCHE',
    prix_estime          DECIMAL(8,2),
    prix_final           DECIMAL(8,2),
    CONSTRAINT fk_course_client
        FOREIGN KEY (id_client) REFERENCES client(id_client),
    CONSTRAINT fk_course_chauffeur
        FOREIGN KEY (id_chauffeur) REFERENCES chauffeur(id_chauffeur),
    CONSTRAINT fk_course_taxi
        FOREIGN KEY (id_taxi) REFERENCES taxi(id_taxi),
    CONSTRAINT fk_course_tranche
        FOREIGN KEY (id_tranche) REFERENCES tranche_tarif(id_tranche)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- Table : notification_demande
-- ---------------------------------------------------------------------
CREATE TABLE notification_demande (
    id_notification INT AUTO_INCREMENT PRIMARY KEY,
    id_course       INT NOT NULL,
    id_chauffeur    INT NOT NULL,
    date_envoi      DATETIME DEFAULT CURRENT_TIMESTAMP,
    reponse         ENUM('EN_ATTENTE','ACCEPTEE','REFUSEE','EXPIREE') DEFAULT 'EN_ATTENTE',
    date_reponse    DATETIME DEFAULT NULL,
    score_selection DECIMAL(5,2),
    CONSTRAINT fk_notif_course
        FOREIGN KEY (id_course) REFERENCES course(id_course)
        ON DELETE CASCADE,
    CONSTRAINT fk_notif_chauffeur
        FOREIGN KEY (id_chauffeur) REFERENCES chauffeur(id_chauffeur)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- Table : evaluation
-- ---------------------------------------------------------------------
CREATE TABLE evaluation (
    id_evaluation INT AUTO_INCREMENT PRIMARY KEY,
    id_course     INT NOT NULL,
    auteur_id     INT NOT NULL,
    cible_id      INT NOT NULL,
    note          INT NOT NULL CHECK (note BETWEEN 1 AND 5),
    commentaire   VARCHAR(500),
    date_eval     DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_eval_course
        FOREIGN KEY (id_course) REFERENCES course(id_course)
        ON DELETE CASCADE,
    CONSTRAINT fk_eval_auteur
        FOREIGN KEY (auteur_id) REFERENCES utilisateur(id_utilisateur),
    CONSTRAINT fk_eval_cible
        FOREIGN KEY (cible_id)  REFERENCES utilisateur(id_utilisateur)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- Index utiles
-- ---------------------------------------------------------------------
CREATE INDEX idx_course_statut     ON course(statut);
CREATE INDEX idx_taxi_dispo        ON taxi(statut_disponibilite);
CREATE INDEX idx_chauffeur_statut  ON chauffeur(statut);
CREATE INDEX idx_notif_reponse     ON notification_demande(reponse);
