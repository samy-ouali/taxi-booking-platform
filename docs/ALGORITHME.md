# Algorithme de matching chauffeur

> Sujet 10 - Système de réservation de taxi
> Groupe 16 - Samy Ouali
> Checkpoint 2

## 1. Objectif

Étant donnée une course `C` soumise par un client, le système doit
déterminer **automatiquement** le ou les chauffeurs les plus pertinents
pour prendre la course, en combinant trois critères :

1. la **qualité** du chauffeur (sa note moyenne),
2. la **proximité** géographique de son taxi par rapport au point de départ,
3. la **fiabilité** historique du chauffeur (taux d'acceptation / d'annulation).

## 2. Entrées

- `C` : l'instance de `Course` nouvellement créée
  - coordonnées de départ `(lat_d, lon_d)`
  - `nb_personnes`, `nb_bagages`
- paramètres de configuration :
  - `rayon_km` (par défaut 5)
  - poids `w_note = 0.50`, `w_prox = 0.30`, `w_fia = 0.20`

## 3. Sortie

Une liste triée (par score décroissant) de `Candidat = (chauffeur, taxi, distance, score)`.

## 4. Étapes

### 4.1. Filtrage

On interroge la base pour ne conserver que :
- les chauffeurs `statut = DISPONIBLE` et `utilisateur.actif = true` ;
- dont un taxi a `statut_disponibilite = DISPONIBLE` ;
- dont la catégorie de taxi respecte `capacite_personnes >= nb_personnes` et
  `capacite_bagages >= nb_bagages`.

```sql
SELECT * FROM chauffeur c
JOIN taxi t ON t.id_chauffeur = c.id_chauffeur
JOIN categorie_taxi ct ON ct.id_categorie = t.id_categorie
JOIN utilisateur u ON u.id_utilisateur = c.id_chauffeur
WHERE c.statut = 'DISPONIBLE'
  AND t.statut_disponibilite = 'DISPONIBLE'
  AND ct.capacite_personnes >= :nb_p
  AND ct.capacite_bagages   >= :nb_b
  AND u.actif = 1;
```

### 4.2. Filtrage géographique

Pour chaque chauffeur, on calcule une **distance euclidienne approchée** (en km)
entre la position du taxi et le départ de la course (`app/services/geo.py`) :

```
dx = Δlongitude × 111 × cos(latitude moyenne)
dy = Δlatitude × 111
d  = √(dx² + dy²)
```

Un degré de latitude vaut environ 111 km ; un degré de longitude vaut 111 km
multiplié par le cosinus de la latitude. Sur les courtes distances d'un trajet
urbain, cette approximation est très proche de la formule de Haversine, et
plus simple à calculer.

Seuls les taxis dont `d <= rayon_km` sont conservés.

### 4.3. Normalisation des critères

Pour que les trois critères soient comparables, chacun est ramené dans `[0,1]` :

| Critère         | Formule                              | Borne |
|-----------------|--------------------------------------|-------|
| Note qualité    | `note_moyenne / 5`                   | [0,1] |
| Proximité       | `1 - distance_km / rayon_km`         | [0,1] |
| Fiabilité       | `0.7·taux_acc + 0.3·(1 - taux_ann)`  | [0,1] |

> Un chauffeur avec `taux_acceptation = 100%` et `taux_annulation = 0%`
> obtient une fiabilité de 1.0. À l'inverse, 0% d'acceptation et 100%
> d'annulation = 0.0.

### 4.4. Score final pondéré

```
score = 0.50 · note_norm + 0.30 · prox_norm + 0.20 · fia
```

La somme des poids vaut `0.50 + 0.30 + 0.20 = 1.00`, donc
`score ∈ [0, 1]`.

### 4.5. Tri et notification

On trie les candidats par score décroissant, puis on crée une
`NotificationDemande` par candidat (avec son score). Le premier chauffeur
qui accepte reçoit la course, les autres notifications passent en `EXPIREE`.

## 5. Pseudo-code

```python
def chercher_candidats(course, rayon_km=5,
                       w_note=0.5, w_prox=0.3, w_fia=0.2):
    candidats = []
    for (ch, tx, cat, user) in requete_sql_filtree(course):
        if tx.position is None or course.depart is None:
            continue
        d = distance_euclidienne_km(tx.position, course.depart)
        if d > rayon_km:
            continue
        note_n = (user.note_moyenne or 0) / 5
        prox_n = max(0, 1 - d / rayon_km)
        fia    = 0.7 * ch.taux_acc + 0.3 * (1 - ch.taux_ann)
        score  = w_note * note_n + w_prox * prox_n + w_fia * fia
        candidats.append(Candidat(ch, tx, d, score))
    candidats.sort(key=lambda c: c.score, reverse=True)
    return candidats
```

## 6. Exemples chiffrés

**Cas 1 : candidat parfait**
- note = 5/5, distance = 0 km, rayon = 5 km, acc = 100%, ann = 0%
- note_n = 1.0 ; prox_n = 1.0 ; fia = 1.0
- **score = 0.50·1 + 0.30·1 + 0.20·1 = 1.00**

**Cas 2 : candidat moyen**
- note = 4/5, distance = 2.5 km, rayon = 5 km, acc = 92%, ann = 5%
- note_n = 0.80 ; prox_n = 0.50 ; fia = 0.7·0.92 + 0.3·0.95 = 0.929
- **score = 0.40 + 0.15 + 0.186 = 0.736**

**Cas 3 : candidat médiocre**
- note = 3/5, distance = 4.9 km, rayon = 5 km, acc = 60%, ann = 20%
- note_n = 0.60 ; prox_n = 0.02 ; fia = 0.7·0.60 + 0.3·0.80 = 0.66
- **score = 0.30 + 0.006 + 0.132 = 0.438**

## 7. Complexité

Soit `n` le nombre de chauffeurs disponibles et compatibles.

- Filtrage SQL : indexable sur `statut`, `id_categorie`, `actif` → quasi `O(n)`.
- Calcul de distance et score : `O(n)`.
- Tri final : `O(n log n)`.

Complexité totale : **O(n log n)**. Pour `n ~ quelques dizaines dans un
rayon de 5 km`, la sélection est immédiate.

## 8. Points d'évolution

- Intégration d'une **API de routage** (Google Maps, OSRM) pour remplacer
  la distance à vol d'oiseau par la distance routière.
- **Penalisation** des chauffeurs très sollicités (équité).
- Apprentissage des **préférences client** (modèle de recommandation).
- Notification **en temps réel** via WebSocket.
