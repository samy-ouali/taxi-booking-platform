"""
Calcul du prix estimé d'une course.

Formule :
    prix = (prix_base
            + tarif_km * distance_km
            + supplement_personne * max(0, nb_personnes - 1)
            + supplement_bagage   * nb_bagages
           ) * coefficient_tranche
"""
from datetime import datetime, time
from decimal import Decimal

from app.models import CategorieTaxi, TrancheTarif


def _to_decimal(value) -> Decimal:
    return Decimal(str(value))


def tranche_active(moment: datetime, tranches) -> TrancheTarif | None:
    """
    Renvoie la tranche tarifaire qui couvre l'heure donnée.
    Gère le cas où la tranche traverse minuit.
    """
    h = moment.time() #on retient uniquement le temps
    for tr in tranches:
        if tr.heure_debut <= tr.heure_fin:
            if tr.heure_debut <= h <= tr.heure_fin:
                return tr
        else:  # tranche qui franchit minuit
            if h >= tr.heure_debut or h <= tr.heure_fin:
                return tr
    return None


def calculer_prix_estime(
    categorie: CategorieTaxi,
    distance_km: float,
    nb_personnes: int,
    nb_bagages: int,
    moment: datetime,
    tranches: list[TrancheTarif],
) -> tuple[Decimal, TrancheTarif | None]:
    """
    Renvoie (prix, tranche_utilisée).
    """
    tr = tranche_active(moment, tranches)
    coef = _to_decimal(tr.coefficient) if tr else Decimal("1.00")

    base = _to_decimal(categorie.prix_base)
    tarif_km = _to_decimal(categorie.tarif_km)
    sup_p = _to_decimal(categorie.supplement_personne or 0)
    sup_b = _to_decimal(categorie.supplement_bagage or 0)

    prix = (
        base
        + tarif_km * _to_decimal(distance_km)
        + sup_p * Decimal(max(0, nb_personnes - 1)) #on ne considère pas le premier passager comme en supplément, et on anticipe l'erreur où nb_personnes = 0
        + sup_b * Decimal(nb_bagages)
    ) * coef

    """"
    Retourne le prix arrondi au centième ainsi que le tarif utilisé.
    """
    return prix.quantize(Decimal("0.01")), tr 

