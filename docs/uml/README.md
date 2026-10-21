# Diagrammes UML

> Sujet 10 - Système de réservation de taxi
> Groupe 16 - Samy Ouali

Les diagrammes sont au format **Mermaid** (`.mmd`). Ils sont directement
rendus par GitHub, VS Code (extension *Markdown Preview Mermaid Support*),
ou l'éditeur en ligne [mermaid.live](https://mermaid.live).

Les exports PNG sont dans [`png/`](png/).

---

## 1. Diagramme de classes
Fichier : [`01_diagramme_classes.mmd`](01_diagramme_classes.mmd)

Représente la structure orientée objet du système. Met en évidence la
spécialisation `Utilisateur -> Client / Chauffeur`, les associations
`Client - Course - Chauffeur`, ainsi que les classes `NotificationDemande`
et `Evaluation` qui tracent le processus de matching et de feedback.

## 2. Diagramme de séquence - Réservation
Fichier : [`02_diagramme_sequence_reservation.mmd`](02_diagramme_sequence_reservation.mmd)

Déroule le scénario principal : saisie par le client → calcul du prix →
recherche des candidats → notifications → acceptation par le chauffeur.

## 3. Diagramme d'activité - Algorithme de matching
Fichier : [`03_diagramme_activite_matching.mmd`](03_diagramme_activite_matching.mmd)

Décrit pas à pas le filtrage (rayon, capacité) puis le calcul du score
pondéré `0.50·note + 0.30·proximité + 0.20·fiabilité`.

## 4. Diagramme de composants
Fichier : [`04_diagramme_composants.mmd`](04_diagramme_composants.mmd)

Architecture 3-tiers : Navigateur ⇄ Flask (routes + services + ORM) ⇄ MySQL.

## 5. Diagramme d'états - Cycle de vie d'une Course
Fichier : [`05_diagramme_etats_course.mmd`](05_diagramme_etats_course.mmd)

Transitions entre `EN_RECHERCHE`, `ATTRIBUEE`, `EN_COURS`, `TERMINEE`,
`ANNULEE`, `ECHEC`.

## 6. Diagramme de cas d'utilisation (enrichi)
Fichier : [`06_diagramme_cas_utilisation.mmd`](06_diagramme_cas_utilisation.mmd)

Version étoffée par rapport au checkpoint 1 : ajout des cas admin,
include entre `Réserver` et `Calculer prix`, acteurs externes
(Paiement, GPS).
