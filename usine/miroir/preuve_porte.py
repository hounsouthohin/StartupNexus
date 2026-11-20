"""PREUVE N1.4c (0 $, rapide) : la porte, sur des COPIES de lectures (les originaux ne changent pas).
  1. une description non validée est refusée ;
  5. la validation est refusée tant qu'un refus n'a pas sa proposition acceptée ou qu'une question sur les droits
     n'a pas de réponse — puis acceptée une fois tout répondu ;
  3. un caractère modifié dans la description validée → refusée ;
  4. une réponse ajoutée après la validation l'annule → refusée.
  (contrat des noms à l'écran, morceau 5) la validation écrite dans le dossier d'une fabrication :
  6. relue et réécrite comme le fait la fabrication, la description validée garde ses octets → acceptée, et la
     validation désigne ce fichier avec son empreinte ;
  7. un caractère modifié dans la description fabriquée → refusée (« à l'octet près ») ;
  8. un essai → marqué `essai: true` et « essai — non validée par un client », avec l'empreinte du fichier.
  (morceau 5, la vue présentée au client — sabotages 10 et 10 bis du dossier)
  10 bis. une vue présentée qui ne découle pas de la description validée (celle d'avant les réponses, ou un nom changé)
     → validation refusée ;
  10. la vue modifiée après la validation → refusée ; une validation d'avant cette règle (sans empreinte de vue) → refusée.
Comme dans le vrai déroulé, la vue (`miroir.md`) est écrite avant d'être présentée, et réécrite après chaque réponse.
Les fabrications réelles (validée, et essai de répétition) se font à part.

    python -m usine.miroir.preuve_porte <dossier de travail>
"""
import shutil
import sys
from pathlib import Path

import hashlib
import json

from ..description import Description
from .contenu import depuis_run, ecrire
from .porte import DROITS, ESSAI, VUE, PorteFermee, ecrire_description, validation_du_run, valider, verifier
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
    ecrire(run, mi)                                   # la vue présentée au client
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
        # 10 bis : la vue présentée est encore celle d'AVANT les réponses (une autre version) → refusée
        r10 = valider(run, "Client d'essai", "Concepteur")
        attendu(any("ne découle pas" in x for x in r10),
                f"10 bis. la vue d'avant les réponses → « {(r10[0] if r10 else 'acceptée à tort')[:90]} »")
        ecrire(run, depuis_run(run))                  # la vue à jour, relue avec le client
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
    # 10 : la vue modifiée APRÈS la validation → refusée ; une validation d'avant la règle (sans empreinte de vue) → refusée
    vue_md = run / VUE
    octets = vue_md.read_bytes()
    vue_md.write_bytes(octets + b" ")
    attendu("vue du miroir a été modifiée" in refusee(d), f"10. la vue modifiée après la validation → « {refusee(d)[:70]} »")
    vue_md.write_bytes(octets)
    attendu(not refusee(d), "   vue restaurée → passe à nouveau")
    vj = run / "validation.json"
    tj = vj.read_text(encoding="utf-8")
    vj.write_text(json.dumps({k: x for k, x in json.loads(tj).items() if k not in ("vue", "vue_empreinte")},
                             ensure_ascii=False, indent=1), encoding="utf-8")
    attendu("d'avant le contrat" in refusee(d), f"10. une validation sans empreinte de vue → « {refusee(d)[:70]} »")
    vj.write_text(tj, encoding="utf-8")
    attendu(not refusee(d), "   validation restaurée → passe à nouveau")
    # (morceau 5) la fabrication relit la description validée et l'écrit dans son dossier : mêmes octets ?
    val_client = verifier(d)
    fab = run / "fabrication"
    fab.mkdir(exist_ok=True)
    f01 = fab / "01-description.json"
    ecrire_description(Description.model_validate(json.loads(d.read_text(encoding="utf-8"))), f01)
    sha = hashlib.sha256(f01.read_bytes()).hexdigest()
    try:
        v = validation_du_run(f01, val_client)
        attendu(v["essai"] is False and v["description"] == f01.name and v["empreinte"] == sha == val_client["empreinte"],
                f"6. réécrite par la fabrication : mêmes octets → acceptée, empreinte {sha[:12]}…")
    except PorteFermee as x:
        attendu(False, f"6. réécrite par la fabrication → refusée à tort : {x}")
    f01.write_text(f01.read_text(encoding="utf-8").replace('"format": 2', '"format": 2 ', 1), encoding="utf-8")
    try:
        validation_du_run(f01, val_client)
        attendu(False, "7. un caractère modifié dans la description fabriquée → acceptée à tort")
    except PorteFermee as x:
        attendu("octet" in str(x), f"7. un caractère modifié dans la description fabriquée → « {x} »")
    e = validation_du_run(f01, None)
    attendu(e == {"statut": ESSAI, "essai": True, "description": f01.name,
                  "empreinte": hashlib.sha256(f01.read_bytes()).hexdigest()},
            f"8. essai → {json.dumps(e, ensure_ascii=False)[:110]}…")
    prop = next((p["id"] for f in mi["fiches"] for p in f["propositions"]), None)
    if prop:
        ajouter(run, {prop: "oui"}, "preuve")
        attendu("annulée" in refusee(d), f"4. réponse après validation → « {refusee(d)[:80]} »")
        ecrire(run, depuis_run(run))                  # comme `python -m usine.miroir repondre` : la vue est réécrite
        attendu(not valider(run, "Client d'essai", "Concepteur") and not refusee(d), "   revalidée → passe à nouveau")
    # 10 bis (variante, pour toute lecture) : une vue présentée dont un nom à l'écran a été changé → validation refusée
    t = vue_md.read_text(encoding="utf-8")
    i = t.find("    - bouton de création : « ")
    if i < 0:
        attendu(False, "la vue n'a aucun bloc « À l'écran »")
    else:
        vue_md.write_text(t[:i] + t[i:].replace("« ", "« X", 1), encoding="utf-8")
        r = valider(run, "Client d'essai", "Concepteur")
        attendu(any("ne découle pas" in x for x in r), f"10 bis. un nom changé dans la vue présentée → « {(r[0] if r else 'acceptée à tort')[:90]} »")
        vue_md.write_text(t, encoding="utf-8")
        attendu(not valider(run, "Client d'essai", "Concepteur") and not refusee(d), "   vue d'origine → validée à nouveau")

print(f"ÉCHECS : {len(echecs)}", *echecs, sep="\n  ")
sys.exit(1 if echecs else 0)
