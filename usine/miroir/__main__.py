"""python -m usine.miroir runs/<n°>-<nom>-comprendre [...] : (ré)écrit le miroir de compréhensions déjà faites
(0 $, aucune IA ; avec les réponses déjà données) et vérifie sa couverture — rien de ce qui sera construit ne doit
y manquer.

python -m usine.miroir repondre runs/<lecture> id=valeur [id=valeur …] : (N1.4b) ajoute des réponses (les
identifiants sont au volet concepteur du miroir), recalcule, et dit ce qui a changé et ce qui n'a pas pu s'appliquer."""
import sys
from pathlib import Path

from .contenu import couverture, depuis_run, ecrire
from .reponses import ajouter, comparer

sys.stdout.reconfigure(encoding="utf-8")


def etat(mi: dict) -> str:
    if mi["perimetre"] == "hors":
        return "hors périmètre"
    return (f"{sum(len(r['phrases']) for r in mi['roles'])} phrases, {len(mi['questions'])} question(s)"
            + (", refus + variante" if mi["refus"] and not mi["refus"]["rien_ne_se_construit"] else ", refus (rien ne se construit)" if mi["refus"] else ""))


if sys.argv[1:2] == ["valider"]:      # (N1.4c) python -m usine.miroir valider <lecture> --client "…" [--concepteur "…"]
    import argparse
    from .porte import valider
    a = argparse.ArgumentParser(prog="usine.miroir valider")
    a.add_argument("lecture", type=Path)
    a.add_argument("--client", required=True)
    a.add_argument("--concepteur", default="concepteur")
    args = a.parse_args(sys.argv[2:])
    raisons = valider(args.lecture, args.client, args.concepteur)
    if raisons:
        print("VALIDATION REFUSÉE :", *raisons, sep="\n  - ")
        sys.exit(1)
    print(f"VALIDÉE par {args.client} (avec {args.concepteur}) — à fabriquer :\n"
          f"  python -m usine fabriquer {args.lecture / 'description-validee.json'}")
    sys.exit(0)

if sys.argv[1:2] == ["repondre"]:
    run = Path(sys.argv[2])
    nouvelles = dict(a.split("=", 1) for a in sys.argv[3:])
    avant = depuis_run(run)
    ajouter(run, nouvelles, qui="concepteur (ligne de commande)")
    apres = depuis_run(run)
    ecrire(run, apres)
    for r in apres.get("reponses", []):
        if r["id"] in nouvelles:
            print(f"{'✓' if r['applique'] else '✗'} {r['id']} = {r['valeur']}" + ("" if r["applique"] else f" — {r['message']}"))
    print("Ce qui a changé :", *(comparer(avant, apres) or ["rien"]), sep="\n  ")
    trous = couverture(apres)
    print("couverture :", "complète" if not trous else trous)
    sys.exit(1 if trous else 0)

manques = 0
for arg in sys.argv[1:]:
    run = Path(arg)
    mi = depuis_run(run)
    ecrire(run, mi)
    trous = couverture(mi)
    manques += len(trous)
    print(f"{'✓' if not trous else '✗'} {run.name:<62} {etat(mi)}" + "".join(f"\n    manque : {t}" for t in trous))
sys.exit(1 if manques else 0)
