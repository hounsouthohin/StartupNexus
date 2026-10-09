"""Traducteur n°3 : les données de départ (contenu des catalogues) et l'ordre de vidage de la base
(les fiches qui en désignent d'autres d'abord).

Quand la description ne donne pas le contenu d'un catalogue ou d'un registre (cas d'une description
écrite par les lecteurs IA), 3 fiches de DÉMONSTRATION sont fabriquées par programme, à partir des
types des champs — jamais par l'IA. Elles sont listées dans « demonstration » (le client les remplace).
"""
from __future__ import annotations

from ..description import Champ, Description
from ..matrice import Matrix
from .modele import bas, construire

NB_DEMO = 3


def valeur_demo(c: Champ, i: int):
    t = c.type
    if t == "texte_long":
        return f"{c.libelle} {i} (exemple)"
    if t == "nombre":
        return i
    if t == "montant":
        return 10 * i + 0.5
    if t == "date":
        return f"2026-0{i}-15T00:00:00.000Z"      # un jour : minuit UTC, comme une saisie de date
    if t == "date_heure":
        return f"2026-0{i}-15T09:00:00.000Z"
    if t == "oui_non":
        return i % 2 == 0
    if t == "email":
        return f"exemple{i}@exemple.invalid"
    if t == "telephone":
        return f"060000000{i}"
    if t == "url":
        return f"https://exemple.invalid/{i}"
    if t == "choix":
        return c.valeurs[(i - 1) % len(c.valeurs)].code
    return f"{c.libelle} {i}"


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
    donnees = {bas(k): v for k, v in desc.depart.items()}
    demo = []
    for f in fiches.values():
        # sans propriétaire ni lien à poser : une fiche de démonstration se suffit à elle-même
        if f.e.nature in ("catalog", "registry") and not desc.depart.get(f.nom) and not f.liens:
            donnees[bas(f.nom)] = [{c.nom: valeur_demo(c, i) for c in f.champs} for i in range(1, NB_DEMO + 1)]
            demo.append(f.nom)
    return {"suppression": ordre, "creation": list(reversed(ordre)), "donnees": donnees, "demonstration": demo}
