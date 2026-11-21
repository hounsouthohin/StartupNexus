"""PREUVE du contrôle du lecteur des libellés (contrat des noms à l'écran, morceau 2 ; 0 $, aucune IA, rapide).

Sur les fiches RÉELLES des lectures d'apprentissage déjà faites (ce que le lecteur avait reçu, reconstruit depuis
`lecteurs.json`), on soumet au contrôle des réponses écrites à la main :
  témoins   - une réponse complète (l'ancienne réponse du lecteur + un nom de création par fiche principale) : acceptée ;
            - l'ancienne réponse, avec l'ancien contexte (sans « principales ») : acceptée, comme avant ;
  sabotages - l'ancienne réponse avec le nouveau contexte (aucun nom de création) : refusée ;
            - un nom de création manquant, vide, trop long, un geste (« Créer »), égal à une étape de la fiche, égal à
              une création en un clic affichée sur sa page, ou donné à une fiche qui n'est pas principale : refusée,
              en nommant la fiche.
Chaque sorte de sabotage doit être essayée au moins une fois sur l'ensemble des lectures.

    python -m usine.comprendre.preuve_libelles
"""
import copy
import sys
from pathlib import Path

from . import donnees_libelles, infos_fiches
from . import lecteurs as L
from .completion import nom_creation_par_defaut

sys.stdout.reconfigure(encoding="utf-8")
RUNS = Path(__file__).resolve().parents[2] / "runs"
APPRENTISSAGE = ["mesures-terrain", "cabinet-pluri", "renovation", "autocars", "formation", "gestion-immo",
                 "union-sportive", "transport-mobile"]          # les 2 autres briefs sont hors périmètre (aucune fiche)
echecs: list[str] = []
essayes: dict[str, int] = {}


def attendu(ok: bool, quoi: str) -> None:
    print(f"  {'✓' if ok else '✗'} {quoi}")
    if not ok:
        echecs.append(quoi)


def lecture(b: str):
    import json
    run = sorted(p for p in RUNS.glob(f"*-{b}-claude-comprendre") if p.is_dir())[-1]
    lect = json.loads((run / "lecteurs.json").read_text(encoding="utf-8"))
    fiches = L.SortieFiches.model_validate(lect["fiches"])
    info = infos_fiches(fiches, L.SortieCircuits.model_validate(lect["circuits"]))
    return fiches, info, L.SortieLibelles.model_validate(lect["libelles"])


def complete(ancienne: L.SortieLibelles, fiches: L.SortieFiches, principales: list[str]) -> L.SortieLibelles:
    """L'ancienne réponse, plus un nom de création (la règle de grammaire) pour chaque fiche principale."""
    o = copy.deepcopy(ancienne)
    fem = {f.nom: (f.libelle, f.feminin) for f in fiches.fiches}
    vus = {f.fiche for f in o.fiches}
    for n in principales:
        if n not in vus:
            o.fiches.append(L.LibellesFiche(fiche=n, verbe_creation=None, boutons={}))
    for f in o.fiches:
        if f.fiche in principales:
            f.creation = nom_creation_par_defaut(*fem[f.fiche])
    return o


def sabotage(sorte: str, o: L.SortieLibelles, ctx: dict, fiche: str, mot: str) -> None:
    errs = L.controle_libelles(o, ctx)
    essayes[sorte] = essayes.get(sorte, 0) + 1
    attendu(any(fiche in e and mot in e for e in errs), f"{sorte} ({fiche}) → « {next((e for e in errs if fiche in e), 'acceptée à tort')[:95]} »")


for b in APPRENTISSAGE:
    print(f"== {b}")
    fiches, info, ancienne = lecture(b)
    _, ctx = donnees_libelles("", info)
    ctx_ancien = {"arrivees": ctx["arrivees"]}
    pr = ctx["principales"]
    attendu(not L.controle_libelles(ancienne, ctx_ancien), "témoin : l'ancienne réponse, ancien contexte → acceptée")
    bonne = complete(ancienne, fiches, pr)
    errs = L.controle_libelles(bonne, ctx)
    attendu(not errs, f"témoin : réponse complète ({len(pr)} fiche(s) principale(s)) → acceptée" + (f" — {errs[:2]}" if errs else ""))
    if errs:
        continue
    sabotage("l'ancienne réponse, nouveau contexte", ancienne, ctx, pr[0], "il manque « creation »")
    cible = pr[0]
    for sorte, valeur, mot in (("nom manquant", None, "il manque"), ("nom vide", "  ", "il manque"),
                               ("nom trop long", "Créer une nouvelle fiche pour enregistrer tout cela", "trop long"),
                               ("un geste seul", "Créer", "geste")):
        o = copy.deepcopy(bonne)
        next(f for f in o.fiches if f.fiche == cible).creation = valeur
        sabotage(sorte, o, ctx, cible, mot)
    etape = next((f for f in bonne.fiches if f.fiche in pr and f.boutons), None)
    if etape:
        o = copy.deepcopy(bonne)
        f = next(x for x in o.fiches if x.fiche == etape.fiche)
        f.creation = next(iter(f.boutons.values()))
        sabotage("égal à une étape de sa fiche", o, ctx, etape.fiche, "autre action de sa page")
    clic = next(((n, g) for n in pr for g in ctx["designee_par"].get(n, [])
                 if any(x.fiche == g and x.verbe_creation for x in bonne.fiches)), None)
    if clic:
        o = copy.deepcopy(bonne)
        verbe = next(x.verbe_creation for x in o.fiches if x.fiche == clic[1])
        next(x for x in o.fiches if x.fiche == clic[0]).creation = verbe
        sabotage("égal à une création en un clic de sa page", o, ctx, clic[0], "autre action de sa page")
    secondaire = next((n for n in info if n not in pr), None)
    if secondaire:
        o = copy.deepcopy(bonne)
        f = next((x for x in o.fiches if x.fiche == secondaire), None)
        if f is None:
            o.fiches.append(L.LibellesFiche(fiche=secondaire, verbe_creation=None, boutons={}))
            f = o.fiches[-1]
        f.creation = "Nouvelle ligne"
        sabotage("donné à une fiche qui n'est pas principale", o, ctx, secondaire, "n'est pas principale")

print("== Chaque sorte de sabotage essayée")
for sorte in ("l'ancienne réponse, nouveau contexte", "nom manquant", "nom vide", "nom trop long", "un geste seul",
              "égal à une étape de sa fiche", "égal à une création en un clic de sa page",
              "donné à une fiche qui n'est pas principale"):
    attendu(essayes.get(sorte, 0) > 0, f"{sorte} : {essayes.get(sorte, 0)} fois")
print(f"ÉCHECS : {len(echecs)}", *echecs, sep="\n  ")
sys.exit(1 if echecs else 0)
