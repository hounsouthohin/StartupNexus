"""PREUVE de la description de format 2 (contrat des noms à l'écran, morceaux 1 et 3 — 20 nov 2026).

Les sabotages (ce que les contrôles doivent REFUSER, avec la bonne raison et la bonne fiche) et les témoins (ce qu'ils
doivent ACCEPTER, et ce que la complétion doit retrouver). Sans réseau, sans base, sans IA.

    python -m usine.preuve_description
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

from .comprendre.completion import completer
from .description import Description

RACINE = Path(__file__).resolve().parent
sys.stdout.reconfigure(encoding="utf-8")


def exemple(nom: str) -> dict:
    return json.loads((RACINE / "exemples" / f"{nom}.json").read_text(encoding="utf-8"))


def verdict(d: dict) -> str | None:
    """None si acceptée, sinon le message de refus."""
    try:
        Description.model_validate(d)
        return None
    except Exception as x:          # pydantic emballe le ValueError : le message est dans le texte
        return str(x)


resultats: list[tuple[str, bool, str]] = []


def sabotage(nom: str, d: dict, attendus: list[str]):
    """Doit être REFUSÉE, et le message doit contenir chacun des morceaux attendus (la raison ET la fiche)."""
    m = verdict(d)
    ok = m is not None and all(a in m for a in attendus)
    resultats.append((f"sabotage — {nom}", ok, "refusée" if m else "ACCEPTÉE à tort"))
    if m is not None and not ok:
        resultats[-1] = (resultats[-1][0], False, f"refusée, mais pas pour la raison attendue {attendus} : {m[:300]}")


def temoin(nom: str, d: dict, verifier=None):
    m = verdict(d)
    ok = m is None and (verifier is None or verifier(Description.model_validate(d)))
    resultats.append((f"témoin — {nom}", ok, "acceptée" if m is None else f"REFUSÉE à tort : {m[:300]}"))


def avec(base: dict, chemin: list, valeur=None, retirer: bool = False) -> dict:
    d = copy.deepcopy(base)
    x = d
    for k in chemin[:-1]:
        x = x[k]
    if retirer:
        x.pop(chemin[-1], None)
    else:
        x[chemin[-1]] = valeur
    return d


med, typ, uni = exemple("mediatheque"), exemple("types"), exemple("union-sportive")

# ── Les témoins : les trois exemples de format 2 sont acceptés ──
temoin("la médiathèque (titre de l'emprunt tiré du livre : visible en entier de chaque rôle)", med,
       lambda d: d.ecran["Borrowing"].titre == "Book")
temoin("les types", typ)
temoin("l'union sportive (son « nom » devenu obligatoire)", uni)
temoin("un nom mal espacé est normalisé", avec(med, ["ecran", "Book", "creation"], "  Nouvel    ouvrage "),
       lambda d: d.ecran["Book"].creation == "Nouvel ouvrage")

# ── Les sabotages des contrôles (n° 1 à 6 du contrat) ──
sabotage("1. une fiche principale sans titre", avec(med, ["ecran", "Book", "titre"], retirer=True),
         ["[contrat:titre]", "Book", "aucun titre"])
sabotage("1 bis. une fiche principale sans nom de création", avec(typ, ["ecran", "Article", "creation"], retirer=True),
         ["[contrat:creation]", "Article"])
sabotage("2. un titre numérique", avec(typ, ["ecran", "Article", "titre"], "stock"), ["[contrat:titre]", "Article.stock", "texte court"])
sabotage("2 bis. un titre daté", avec(typ, ["ecran", "Article", "titre"], "dateAjout"), ["[contrat:titre]", "Article.dateAjout"])
sabotage("2 ter. un titre en texte long", avec(typ, ["ecran", "Article", "titre"], "description"),
         ["[contrat:titre]", "Article.description", "texte_long"])
sabotage("3. un titre facultatif", avec(typ, ["ecran", "Commande", "titre"], "objet"), ["[contrat:titre]", "Commande.objet", "facultatif"])
sabotage("4. un titre tiré d'une fiche que le gérant ne voit pas en entier (les adresses, vues seulement au travers)",
         avec(typ, ["ecran", "Commande", "titre"], "Adresse"), ["[contrat:titre]", "Commande", "gerant", "TOUTES"])
sabotage("4 bis. un titre tiré d'une fiche non désignée", avec(med, ["ecran", "Book", "titre"], "Borrowing"),
         ["[contrat:titre]", "Book", "n'est pas une fiche qu'elle désigne"])
sabotage("5. un nom de création égal à une étape de la même page", avec(med, ["ecran", "Borrowing", "creation"], "Accepter"),
         ["[contrat:noms]", "Borrowing", "Accepter"])
sabotage("5 bis. un nom de création égal à un geste que l'app a déjà", avec(typ, ["ecran", "Article", "creation"], "Modifier"),
         ["[contrat:noms]", "Article", "Modifier"])
sabotage("6. une description de format 1 (sans numéro)", avec(med, ["format"], retirer=True),
         ["[format]", "format 1 (sans numéro), attendu 2"])
sabotage("6 bis. une description d'un format inconnu", avec(med, ["format"], 3), ["[format]", "format 3, attendu 2"])

# ── La complétion : sur les exemples privés de leurs noms et de leur format, elle retrouve les choix faits à la main ──
for nom, base in (("médiathèque", med), ("types", typ), ("union sportive", uni)):
    nu = copy.deepcopy(base)
    nu.pop("format")
    for ec in nu["ecran"].values():
        ec.pop("creation", None)
        ec.pop("titre", None)
    complete, ajouts = completer(nu)
    m = verdict(complete)
    attendu = {f: (ec.get("creation"), ec.get("titre")) for f, ec in base["ecran"].items() if ec.get("creation")}
    obtenu = {f: (ec.get("creation"), ec.get("titre")) for f, ec in complete["ecran"].items() if ec.get("creation")}
    ok = m is None and attendu == obtenu
    resultats.append((f"témoin — la complétion retrouve les choix de la {nom}" if nom == "médiathèque" else
                      f"témoin — la complétion retrouve les choix des {nom}" if nom == "types" else
                      f"témoin — la complétion retrouve les choix de l'{nom}", ok,
                      "identiques" if ok else f"écart : attendu {attendu}, obtenu {obtenu}, refus {m and m[:200]}"))

# la complétion, quand aucun champ ni aucune fiche désignée ne reconnaît la fiche : un « Libellé » à valider au miroir
sans_texte = copy.deepcopy(uni)
sans_texte.pop("format")
sans_texte["champs"]["Participant"] = []
for ec in sans_texte["ecran"].values():
    ec.pop("creation", None)
    ec.pop("titre", None)
complete, ajouts = completer(sans_texte)
libelle = next((c for c in complete["champs"]["Participant"] if c["nom"] == "libelle"), None)
ok = (verdict(complete) is None and complete["ecran"]["Participant"]["titre"] == "libelle" and libelle is not None
      and libelle["obligatoire"] and libelle["origine"] == "necessaire")
resultats.append(("témoin — une fiche sans texte ni lien reçoit un « Libellé » obligatoire, « nécessaire » (montré au miroir)",
                  ok, "ajouté" if ok else f"non : {complete['ecran'].get('Participant')}, {libelle}"))

# la complétion ne prend PAS un titre tiré d'une fiche que quelqu'un ne voit pas en entier : l'adresse ne peut pas titrer
# la commande pour le gérant ; la commande garde son champ « reference »
sans_ref = copy.deepcopy(typ)
sans_ref.pop("format")
sans_ref["champs"]["Commande"] = [c for c in sans_ref["champs"]["Commande"] if c["nom"] != "reference"]
for ec in sans_ref["ecran"].values():
    ec.pop("creation", None)
    ec.pop("titre", None)
complete, _ = completer(sans_ref)
t = complete["ecran"]["Commande"]["titre"]
ok = verdict(complete) is None and t not in ("Adresse",)
resultats.append(("témoin — la complétion ne tire jamais un titre d'une fiche invisible à un rôle (l'adresse pour le gérant)",
                  ok, f"titre retenu : « {t} »"))

for nom, ok, detail in resultats:
    print(f"{'✓' if ok else '✗'} {nom} — {detail}")
echecs = [r for r in resultats if not r[1]]
print(f"\n{len(resultats) - len(echecs)}/{len(resultats)} conformes")
sys.exit(1 if echecs else 0)
