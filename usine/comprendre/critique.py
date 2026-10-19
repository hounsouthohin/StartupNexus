"""CRITIQUE (essai A, 18 oct) : un lecteur IA relit le brief ET le miroir (vue du client) et signale ce que
l'usine a pu mal comprendre — un besoin oublié, une contradiction, un cœur non construit. Un AVIS seulement : il
ne change jamais la description ; s'il est adopté, ses signalements iront au volet concepteur du miroir
(USINE.md §8, place A). Les critères d'adoption sont écrits d'avance (usine/outils/essai_critique.py).
"""
from __future__ import annotations

from typing import Literal

from .lecteurs import COMMUN, _cites, _Strict


class Signalement(_Strict):
    sorte: Literal["besoin_oublie", "contradiction", "coeur_non_construit"]
    gravite: Literal["bloquant", "important", "mineur"]
    explication: str
    citation: str


class SortieCritique(_Strict):
    coeur_du_besoin: str
    signalements: list[Signalement]


Q_CRITIQUE = COMMUN + """

TON RÔLE : relecteur critique. On te donne le brief du client et le MIROIR : ce que l'usine a compris et
va construire (rôles et droits, étapes, informations de chaque fiche, questions), et ce qu'elle annonce ne
pas savoir faire (« pas encore dans notre stock », refus). Cherche ce que l'usine a MAL compris, du point
de vue du client :
- "besoin_oublie" : un besoin du brief qui n'apparaît NULLE PART dans le miroir — ni construit, ni annoncé
  comme pas encore possible ;
- "contradiction" : le miroir dit autre chose que le brief (un rôle, un droit, une étape, une information) ;
- "coeur_non_construit" : le besoin PRINCIPAL du client (ce pour quoi il veut ce logiciel) n'est pas
  construit — même s'il est honnêtement annoncé comme pas encore possible.
Gravité : "bloquant" (le client ne voudrait pas de cette application), "important" (il le remarquera
vite), "mineur". Ne signale PAS : ce qui est déjà annoncé comme pas encore possible (sauf le cœur), les
informations proposées à cocher, les noms choisis, le style. Si tout est juste, renvoie une liste vide :
un bon relecteur ne signale que ce qui est réellement faux ou manquant.
« coeur_du_besoin » : en une phrase, ce que le client veut avant tout.
Forme : {"coeur_du_besoin": "…", "signalements": [{"sorte": "besoin_oublie|contradiction|coeur_non_construit",
"gravite": "bloquant|important|mineur", "explication": "…", "citation": "…"}]}"""


def controle_critique(o: SortieCritique, ctx: dict) -> list[str]:
    return _cites(ctx["brief"], [(f"signalement {i + 1}", s.citation) for i, s in enumerate(o.signalements)])
