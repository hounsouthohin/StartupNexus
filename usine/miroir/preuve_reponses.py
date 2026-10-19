"""PREUVE N1.4b (0 $) : chaque réponse possible du miroir, rejouée seule sur toutes les lectures déjà faites.
Vérifie : (1) jamais en silence — appliquée, ou refusée AVEC une explication ; (2) appliquée → l'effet voulu et RIEN
d'autre (droits : seuls ceux de l'acteur visé — ou du visiteur — changent ; champs : la matrice ne bouge pas, un seul
champ ajouté ou renommé ; « accepter » = la proposition) ; (3) le miroir d'après reste complet ; (4) « garder toutes
les propositions » = le client simulé des répétitions.

    python -m usine.miroir.preuve_reponses
"""
import copy
import json
import sys
from collections import Counter
from pathlib import Path

from ..matrice import VISITOR, AccessDeclaration, compute_matrix
from ..variante import proposer
from .contenu import construire, couverture
from .reponses import appliquer

sys.stdout.reconfigure(encoding="utf-8")
RUNS = Path(__file__).resolve().parents[2] / "runs"
VALEUR = {"garder": "oui", "nom": "Nom d'essai", "registre_entier": "non", "tout_le_monde": "non", "vu_via": "non",
          "visiteur": "non", "voir_tous": "oui", "accepter_proposition": "oui"}


def cases(d: dict) -> dict:
    m = compute_matrix(AccessDeclaration(**d["acces"]))
    return {(c.actor, c.entity): (c.see, tuple(c.see_via), c.create, c.edit, tuple(c.edit_while), c.delete,
                                  tuple(c.delete_while), tuple(sorted((s, tuple(t)) for s, t in c.transitions.items())))
            for c in m.cells}


def ids(mi: dict) -> list[str]:
    out = []
    for q in mi["questions"]:
        out += [x["id"] for x in q["details"]] if q.get("details") else [q["id"]]
    return out + [p["id"] for f in mi["fiches"] for p in f["propositions"]]


bilan, defauts, refus_exemples = Counter(), [], {}
lectures = sorted(p for p in RUNS.glob("*-comprendre") if (p / "lecteurs.json").exists() and (p / "description-brute.json").exists())
for run in lectures:
    lect = json.loads((run / "lecteurs.json").read_text(encoding="utf-8"))
    if (lect.get("perimetre") or {}).get("perimetre") == "hors":
        continue
    brut = json.loads((run / "description-brute.json").read_text(encoding="utf-8"))
    hors = (lect.get("perimetre") or {}).get("hors_stock", [])
    props = {f["fiche"]: f["propositions"] for f in ((lect.get("champs") or {}).get("fiches") or []) if f.get("propositions")}
    avant = cases(brut)
    mi = construire(brut, hors, props)
    for i in ids(mi):
        sorte = "accepter_proposition" if i == "accepter_proposition" else i.split(":")[0]
        d2, (res,) = appliquer(brut, props, [{"id": i, "valeur": VALEUR[sorte]}])
        if not res["applique"]:
            if not res["message"] or "'" + i.split(":")[-2] + "/" in res["message"]:
                defauts.append(f"{run.name} {i} : refusée SANS explication")
            bilan[(sorte, "refusée (expliquée)")] += 1
            refus_exemples.setdefault(sorte, f"{run.name[16:50]} {i} → {res['message'][:150]}")
            continue
        bilan[(sorte, "appliquée")] += 1
        apres = cases(d2)
        if sorte in ("registre_entier", "tout_le_monde", "vu_via", "voir_tous", "visiteur"):
            vise = VISITOR if sorte == "visiteur" else i.split(":")[1]
            autres = [k for k in avant if k[0] != vise and avant[k] != apres.get(k)]
            if autres:
                defauts.append(f"{run.name} {i} : touche aussi {autres[:3]}")
        elif sorte in ("garder", "nom"):
            if avant != apres:
                defauts.append(f"{run.name} {i} : la matrice a changé")
            a = {(f, c["nom"], c["libelle"]) for f, l in brut["champs"].items() for c in l}
            b = {(f, c["nom"], c["libelle"]) for f, l in d2["champs"].items() for c in l}
            if len(b - a) != 1 or len(a - b) != (1 if sorte == "nom" else 0):
                defauts.append(f"{run.name} {i} : champs changés {sorted(b - a)[:2]} / {sorted(a - b)[:2]}")
        elif sorte == "accepter_proposition" and d2 != proposer(brut)["courant"]:
            defauts.append(f"{run.name} {i} : ≠ la proposition")
        trous = couverture(construire(d2, hors, props))
        if trous:
            defauts.append(f"{run.name} {i} : miroir incomplet {trous[:2]}")
    # (4) garder TOUTES les propositions = le client simulé
    tout = [{"id": i, "valeur": "oui"} for i in ids(mi) if i.startswith("garder:")]
    d_tout, _ = appliquer(brut, props, tout)
    from ..repetition import accepter_propositions
    simule = copy.deepcopy(brut)
    accepter_propositions(simule, run)
    montrees = {f["fiche"] for f in mi["fiches"]}       # le miroir ne propose que les champs des fiches qu'il montre
    ok = all(d_tout["champs"].get(f) == simule["champs"].get(f) for f in montrees)
    bilan[("client simulé identique", "oui" if ok else "NON")] += 1
    if not ok:
        defauts.append(f"{run.name} : garder tout ≠ client simulé")

print(f"lectures : {len(lectures)}")
for (sorte, etat), n in sorted(bilan.items()):
    print(f"  {sorte:<26} {etat:<22} {n}")
print("exemples de réponses refusées (avec leur explication) :", *[f"  {k} : {v}" for k, v in refus_exemples.items()], sep="\n")
print(f"DÉFAUTS : {len(defauts)}", *defauts[:15], sep="\n  ")
sys.exit(1 if defauts else 0)
