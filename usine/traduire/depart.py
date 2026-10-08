"""Traducteur n°3 : les données de départ (contenu des catalogues) et l'ordre de vidage de la base
(les fiches qui en désignent d'autres d'abord)."""
from __future__ import annotations

from ..description import Description
from ..matrice import Matrix
from .modele import bas, construire


def traduire_depart(desc: Description, m: Matrix) -> dict:
    fiches = construire(desc, m)
    restantes, ordre = dict(fiches), []
    while restantes:
        # une fiche peut être vidée quand plus aucune fiche restante ne la désigne
        libres = [n for n in restantes if not any(l.cible == n for f in restantes.values() if f.nom != n for l in f.liens)]
        if not libres:
            raise ValueError(f"liens circulaires entre {sorted(restantes)} (non pris en charge)")
        for n in sorted(libres):
            ordre.append(bas(n))
            restantes.pop(n)
    return {"suppression": ordre, "creation": list(reversed(ordre)),
            "donnees": {bas(k): v for k, v in desc.depart.items()}}
