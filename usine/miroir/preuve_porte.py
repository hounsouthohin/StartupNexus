"""PREUVE N1.4c (0 $, rapide) : la porte, sur des COPIES de lectures (les originaux ne changent pas).
  1. une description non validée est refusée ;
  5. la validation est refusée tant qu'un refus n'a pas sa proposition acceptée ou qu'une question sur les droits
     n'a pas de réponse — puis acceptée une fois tout répondu ;
  3. un caractère modifié dans la description validée → refusée ;
  4. une réponse ajoutée après la validation l'annule → refusée.
Les fabrications réelles (validée, et essai de répétition) se font à part.

    python -m usine.miroir.preuve_porte <dossier de travail>
"""
import shutil
import sys
from pathlib import Path

from .contenu import depuis_run
from .porte import DROITS, PorteFermee, valider, verifier
from .reponses import ajouter

sys.stdout.reconfigure(encoding="utf-8")
RUNS = Path(__file__).resolve().parents[2] / "runs"
travail = Path(sys.argv[1])
echecs = []


def attendu(ok: bool, quoi: str) -> None:
    print(f"  {'✓' if ok else '✗'} {quoi}")
    if not ok:
        echecs.append(quoi)


def refusee(chemin: Path) -> str:
    try:
        verifier(chemin)
        return ""
    except PorteFermee as x:
        return str(x)


for nom in ("c2-nettoyage-industriel", "c2-dossiers-maintenance"):
    src = sorted(p for p in RUNS.glob(f"*-{nom}-claude-comprendre") if not p.name.startswith("20261015-09"))[-1]
    run = travail / src.name
    shutil.rmtree(run, ignore_errors=True)
    shutil.copytree(src, run)
    for f in ("reponses.json", "validation.json", "description-validee.json"):
        (run / f).unlink(missing_ok=True)
    print(f"== {nom}")
    if (run / "description.json").exists():
        m = refusee(run / "description.json")
        attendu(bool(m), f"1. description non validée refusée — « {m[:90]} »")
    mi = depuis_run(run)
    droits = [q for q in mi["questions"] if q["sorte"] in DROITS and len(q["reponses"]) > 1]
    raisons = valider(run, "Client d'essai", "Concepteur")
    attendu(bool(raisons) == bool(droits or mi["refus"]),
            f"5. validation sans réponses : {'refusée — ' + str(len(raisons)) + ' raison(s)' if raisons else 'acceptée (rien à répondre)'}")
    for r in raisons[:3]:
        print(f"       · {r[:130]}")
    if raisons:
        reps = {q["id"]: "oui" for q in droits}
        if mi["refus"] and not mi["refus"]["rien_ne_se_construit"]:
            reps["accepter_proposition"] = "oui"
        ajouter(run, reps, "preuve")
        raisons = valider(run, "Client d'essai", "Concepteur")
        attendu(not raisons, f"5. validation après réponse à tout : {'acceptée' if not raisons else raisons[:2]}")
    if raisons:
        continue
    d = run / "description-validee.json"
    attendu(not refusee(d), "   la description validée passe la porte")
    texte = d.read_text(encoding="utf-8")
    d.write_text(texte.replace('"nom"', '"Nom"', 1), encoding="utf-8")
    attendu("modifiée" in refusee(d), f"3. un caractère modifié → « {refusee(d)[:70]} »")
    d.write_text(texte, encoding="utf-8")
    attendu(not refusee(d), "   restaurée → passe à nouveau")
    prop = next((p["id"] for f in mi["fiches"] for p in f["propositions"]), None)
    if prop:
        ajouter(run, {prop: "oui"}, "preuve")
        attendu("annulée" in refusee(d), f"4. réponse après validation → « {refusee(d)[:80]} »")
        attendu(not valider(run, "Client d'essai", "Concepteur") and not refusee(d), "   revalidée → passe à nouveau")

print(f"ÉCHECS : {len(echecs)}", *echecs, sep="\n  ")
sys.exit(1 if echecs else 0)
