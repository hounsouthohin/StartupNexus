"""PREUVE du bloc « À l'écran » du miroir (contrat des noms à l'écran, morceau 4 ; 0 $, aucune IA, rapide).

Les témoins (ce qui doit passer) :
  - LA COUVERTURE : sur les exemples fabriqués et sur les lectures des 10 briefs d'apprentissage, chaque nom que l'app
    montrera (recalculé depuis la description, par le calcul même du traducteur) figure dans la vue du client, dans le
    bloc de sa fiche, à la ligne de son action ;
  - deux actions de même nom sur deux pages différentes : la description est acceptée.
Les sabotages (ce qui doit être attrapé, avec la bonne raison) :
  7.  un nom retiré de sa ligne mais écrit ailleurs dans la vue (dans le bloc d'une autre fiche, ou sur une autre ligne
      de sa fiche) → le contrôle échoue en nommant le nom ;
  7 bis. un nom attendu par l'inspecteur (son inventaire) que la vue ne montre pas → le contrôle le nomme ;
  8.  deux actions de même nom sur une même page → la description est refusée, en nommant le nom.

    python -m usine.miroir.preuve_ecran
"""
import copy
import json
import sys
from pathlib import Path

from pydantic import ValidationError

from ..description import Description
from .contenu import A_L_ECRAN, _marque, construire, couverture_ecran, depuis_run, en_markdown

sys.stdout.reconfigure(encoding="utf-8")
RUNS = Path(__file__).resolve().parents[2] / "runs"
echecs: list[str] = []


def attendu(ok: bool, quoi: str) -> None:
    print(f"  {'✓' if ok else '✗'} {quoi}")
    if not ok:
        echecs.append(quoi)


def dernier(motif: str) -> Path:
    return sorted(p for p in RUNS.glob(motif) if p.is_dir())[-1]


# ── LES TÉMOINS : la couverture ──────────────────────────────────────────────────────────────────────────────────────
print("== Couverture du bloc « À l'écran »")
miroirs = {}
for ex in ("mediatheque", "essai-types", "union-sportive", "essai-textes-obligatoires"):
    run = dernier(f"*-{ex}")
    miroirs[ex] = construire(json.loads((run / "01-description.json").read_text(encoding="utf-8")), [], {})
APPRENTISSAGE = ["mesures-terrain", "cabinet-pluri", "renovation", "autocars", "formation", "gestion-immo",
                 "union-sportive", "marketplace", "reseau-social", "transport-mobile"]
hors = []
for b in APPRENTISSAGE:
    mi = depuis_run(dernier(f"*-{b}-claude-comprendre"))
    if mi["perimetre"] == "hors":
        hors.append(b)
    else:
        miroirs[f"lecture {b}"] = mi
total_noms = 0
for nom, mi in miroirs.items():
    trous = couverture_ecran(mi)
    n = sum(len(x["noms"]) for f in mi["fiches"] for x in f.get("a_l_ecran", []))
    blocs = sum(1 for f in mi["fiches"] if f.get("a_l_ecran"))
    total_noms += n
    attendu(not trous and n > 0, f"{nom} : {n} noms dans {blocs} blocs, tous à leur ligne" + "".join(f"\n      {t}" for t in trous))
attendu(len(hors) == 2, f"hors périmètre (aucune fiche, rien à montrer) : {', '.join(hors)}")
print(f"  → {total_noms} noms contrôlés sur {len(miroirs)} miroirs")

# ── Témoin : un même nom sur deux pages différentes est permis ────────────────────────────────────────────────────────
# Aucun exemple n'a ce cas (leurs noms d'étape sont tous différents) : on le fabrique sur une copie de l'union, deux
# fiches à circuit recevant chacune une étape « Valider ».
desc_union = json.loads((dernier("*-union-sportive") / "01-description.json").read_text(encoding="utf-8"))
circuits = [e for e in desc_union["acces"]["entities"] if e.get("process")][:2]
for e in circuits:
    arrivee = next(t for ts in e["process"]["transitions"].values() for t in ts)
    desc_union["ecran"][e["name"]]["boutons"] = {arrivee: "Valider"}
try:
    Description.model_validate(desc_union)
    mi_t = construire(desc_union, [], {})
    pages = sorted(f["fiche"] for f in mi_t["fiches"] for x in f.get("a_l_ecran", []) if x["ou"] == "etape" and "Valider" in x["noms"])
    attendu(len(pages) == 2 and not couverture_ecran(mi_t),
            f"témoin : « Valider » sur deux pages différentes ({', '.join(pages)}) → accepté, couverture complète")
except (ValidationError, ValueError) as x:
    attendu(False, f"témoin : un même nom sur deux pages refusé à tort — {str(x)[:120]}")

# ── Sabotage 7 : un nom retiré de sa ligne, mais présent ailleurs ─────────────────────────────────────────────────────
print("== Sabotages")
mi = miroirs["mediatheque"]
md = en_markdown(mi)
attendu(not couverture_ecran(mi, md), "la vue intacte de la médiathèque passe (témoin du sabotage)")


def ligne_de(texte: str, ou: str, nom: str) -> str:
    return next(l for l in texte.split("\n") if l.startswith(f"    - {A_L_ECRAN[ou]} :") and _marque(ou, nom) in l)


# 7a. « Nouvel emprunt » quitte le bloc de l'emprunt et s'écrit dans celui de l'ouvrage
l_emprunt = ligne_de(md, "creation", "Nouvel emprunt")
l_ouvrage = ligne_de(md, "creation", "Nouvel ouvrage")
s = md.replace(l_emprunt, f"    - {A_L_ECRAN['creation']} : (aucun)").replace(l_ouvrage, l_ouvrage + " ; « Nouvel emprunt »")
t = couverture_ecran(mi, s)
attendu(any("Borrowing" in x and "« Nouvel emprunt »" in x for x in t) and "« Nouvel emprunt »" in s,
        f"7. « Nouvel emprunt » écrit dans le bloc de l'ouvrage, plus dans le sien → « {(t[0] if t else 'non vu')[:100]} »")
# 7b. « Accepter » quitte la ligne des étapes et s'écrit sur la ligne du menu, dans le même bloc
l_etapes = ligne_de(md, "etape", "Accepter")
l_menu = ligne_de(md, "menu", "Emprunts")
s = md.replace(l_etapes, l_etapes.replace("« Accepter » (vers « accepté »), ", "")).replace(l_menu, l_menu + " ; « Accepter »")
t = couverture_ecran(mi, s)
attendu(any("« Accepter »" in x and A_L_ECRAN["etape"] in x for x in t),
        f"7. « Accepter » écrit sur la ligne du menu, plus sur celle des étapes → « {(t[0] if t else 'non vu')[:100]} »")
# 7c. le nom n'est plus que dans le volet concepteur (pas dans la vue du client)
s = md.replace(l_emprunt, f"    - {A_L_ECRAN['creation']} : (aucun)") + "\n« Nouvel emprunt »\n"
t = couverture_ecran(mi, s)
attendu(any("« Nouvel emprunt »" in x for x in t), f"7. « Nouvel emprunt » seulement après le volet concepteur → « {(t[0] if t else 'non vu')[:100]} »")
# 7 bis. un nom attendu par l'inspecteur (son inventaire) que la vue ne montre pas
t = couverture_ecran(mi, md, attendus=[("Borrowing", "creation", "Nouveau prêt")])
attendu(any("« Nouveau prêt »" in x for x in t), f"7 bis. un nom de l'inventaire absent de la vue → « {(t[0] if t else 'non vu')[:100]} »")

# ── Sabotage 8 : deux actions de même nom sur une même page ───────────────────────────────────────────────────────────
d8 = copy.deepcopy(json.loads((dernier("*-mediatheque") / "01-description.json").read_text(encoding="utf-8")))
d8["ecran"]["Borrowing"]["boutons"] = {"accepted": "Valider", "refused": "Valider", "returned": "Marquer rendu"}
try:
    Description.model_validate(d8)
    attendu(False, "8. deux étapes « Valider » sur la page de l'emprunt → acceptée à tort")
except (ValidationError, ValueError) as x:
    m = next((l for l in str(x).splitlines() if "Valider" in l), str(x)[:120])
    attendu("« Valider »" in m and "Borrowing" in m, f"8. deux étapes « Valider » sur la page de l'emprunt → « {m.strip()[:110]} »")

print(f"ÉCHECS : {len(echecs)}", *echecs, sep="\n  ")
sys.exit(1 if echecs else 0)
