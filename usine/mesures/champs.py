"""MESURE du lecteur 6 (champs) contre la grille écrite d'avance (champs_references.yaml).

Le lecteur reçoit les fiches déjà trouvées (sorties gpt-5.5 de l'étude 05, ou lecteurs.json d'un
`comprendre`) : on mesure LUI seul, sur de bonnes entrées, sans repayer les lecteurs 1-5.

    python -m usine.mesures.champs --modele gpt-5.4-mini [--mediatheque runs/<n°>-comprendre] [--seulement autocars]

Verdicts par champ annoncé « cité par le brief » : juste (attendu, bon type) · type faux · accepté
(défendable) · interdit (un lien, l'état, une date automatique) · INVENTÉ. Un attendu absent est
« oublié » (« proposé » s'il figure dans les propositions). Les correspondances (alias) sont
affichées : le juge se relit.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

import yaml

from ..comprendre import infos_fiches
from ..comprendre import lecteurs as L
from ..comprendre.ia import Budget, PlafondAtteint, client_pour, demander
from ..comprendre import lire_brief

RACINE = Path(__file__).resolve().parents[2]
GRILLE = Path(__file__).resolve().parent / "champs_references.yaml"


def norm(s: str) -> str:
    s = re.sub(r"([a-z])([A-Z])", r"\1 \2", s or "")
    return re.sub(r"[^a-z0-9 ]+", " ", L.sans_accents(s)).strip()


def colle(*alias_lists) -> list[str]:
    return [norm(a) for lst in alias_lists for a in lst]


def position(texte: str, alias: list[str]) -> int | None:
    """Où apparaît le premier alias dans le texte (sans accents, camelCase découpé) ; None si aucun.
    Les alias de moins de 3 lettres sont ignorés (trop de faux amis)."""
    t = norm(texte).replace(" ", "")
    trouves = [t.find(a.replace(" ", "")) for a in alias if len(a.replace(" ", "")) >= 3 and a.replace(" ", "") in t]
    return min(trouves) if trouves else None


def contient(texte: str, alias: list[str]) -> bool:
    return position(texte, alias) is not None


def juger(ref: dict, sortie: L.SortieChamps, info: dict) -> dict:
    res = {"justes": [], "type_faux": [], "acceptes": [], "interdits": [], "inventes": [], "necessaires": [],
           "oublies": [], "proposes_au_lieu": [], "fiches_sans_grille": [], "propositions": 0}
    for f in sortie.fiches:
        # la fiche de la grille dont un alias apparaît LE PLUS TÔT (« InscriptionActivite » → inscription)
        places = [(position(f.fiche, colle(r["alias"])), k) for k, r in ref.items()]
        places = sorted((pos, k) for pos, k in places if pos is not None)
        cle = places[0][1] if places else None
        res["propositions"] += len(f.propositions)
        if cle is None:
            res["fiches_sans_grille"].append(f.fiche)
            continue
        r, trouves = ref[cle], set()
        for c in f.champs:
            txt = f"{c.nom} {c.libelle}"
            nom = f"{f.fiche}.{c.nom} ({c.type})"
            if c.origine == "necessaire":
                res["necessaires"].append(nom)
                continue
            i = next((i for i, a in enumerate(r.get("attendus", [])) if i not in trouves and contient(txt, colle(a["alias"]))), None)
            if i is not None:
                trouves.add(i)
                a = r["attendus"][i]
                ok = c.type in a["types"]
                if ok and a.get("valeurs"):
                    ok = sorted(norm(v) for v in c.valeurs) == sorted(norm(v) for v in a["valeurs"])
                res["justes" if ok else "type_faux"].append(nom + ("" if ok else f" — attendu {a['types']}" + (f" {a.get('valeurs')}" if a.get("valeurs") else "")))
            elif contient(txt, colle(r.get("interdits", []))):
                res["interdits"].append(nom)
            elif contient(txt, colle(r.get("acceptables", []))):
                res["acceptes"].append(nom)
            else:
                res["inventes"].append(nom + f" — « {c.citation} »")
        for i, a in enumerate(r.get("attendus", [])):
            if i not in trouves:
                prop = next((p for p in f.propositions if contient(p.libelle, colle(a["alias"]))), None)
                (res["proposes_au_lieu"] if prop else res["oublies"]).append(f"{f.fiche} : {a['alias'][0]}")
    return res


def sources(args) -> dict:
    """brief → (texte, fiches, circuits) : sorties gpt-5.5 de l'étude 05, ou un `comprendre` de la médiathèque."""
    grille = yaml.safe_load(GRILLE.read_text(encoding="utf-8"))
    out = {}
    for nom, g in grille.items():
        if args.seulement and nom not in args.seulement:
            continue
        brief = lire_brief(str(RACINE / g["brief"]))
        if g.get("source_fiches"):
            src = json.loads((RACINE / g["source_fiches"]).read_text(encoding="utf-8"))
        elif nom == "mediatheque" and args.mediatheque:
            src = json.loads((Path(args.mediatheque) / "lecteurs.json").read_text(encoding="utf-8"))
        else:
            print(f"{nom} : pas de fiches sources (--mediatheque runs/<n°>-comprendre) — sauté")
            continue
        out[nom] = (brief, L.SortieFiches.model_validate(src["fiches"]),
                    L.SortieCircuits.model_validate(src.get("circuits") or {"circuits": []}), g["fiches"])
    return out


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser()
    p.add_argument("--modele", default="gpt-5.4-mini")
    p.add_argument("--plafond", type=float, default=0.20)
    p.add_argument("--mediatheque", help="dossier d'un `comprendre` de la médiathèque (pour ses fiches)")
    p.add_argument("--seulement", action="append", default=[])
    args = p.parse_args()
    budget = Budget(args.modele, args.plafond)
    client = client_pour(args.modele)
    dossier = RACINE / "runs" / f"{datetime.now():%Y%m%d-%H%M%S}-mesure-champs-{args.modele}"
    dossier.mkdir(parents=True)
    bilan = {}
    for nom, (brief, fiches, circuits, ref) in sources(args).items():
        info = infos_fiches(fiches, circuits)
        donnees = [{"fiche": n, "libelle": i["libelle"], "nature": i["nature"],
                    "designe": [lib for _, lib in i["liens"]], "etats": i["etats"]} for n, i in info.items()]
        appels: list = []
        try:
            sortie = demander(client, budget, L.Q_CHAMPS, {"brief": brief, "fiches": donnees}, L.SortieChamps,
                              L.controle_champs, {"brief": brief, "fiches_info": info}, appels)
        except PlafondAtteint as x:
            print(f"ARRÊT : {x}")
            break
        refus = sum(1 for a in appels if a["erreurs"])
        (dossier / f"{nom}.json").write_text(json.dumps({"sortie": sortie and sortie.model_dump(), "appels": appels},
                                                        ensure_ascii=False, indent=2), encoding="utf-8")
        if sortie is None:
            print(f"\n== {nom} : REFUSÉ 3 fois — {appels[-1]['erreurs'][:3]}")
            bilan[nom] = "refusé"
            continue
        r = juger(ref, sortie, info)
        bilan[nom] = {k: (len(v) if isinstance(v, list) else v) for k, v in r.items()}
        attendus = sum(len(x.get("attendus", [])) for x in ref.values())
        print(f"\n== {nom} : attendus justes {len(r['justes'])}/{attendus} · type faux {len(r['type_faux'])} · "
              f"oubliés {len(r['oublies'])} (dont proposés {len(r['proposes_au_lieu'])}) · inventés {len(r['inventes'])} · "
              f"interdits {len(r['interdits'])} · réponses refusées avant acceptation : {refus}")
        for k in ("justes", "type_faux", "oublies", "proposes_au_lieu", "inventes", "interdits", "acceptes", "necessaires", "fiches_sans_grille"):
            if r[k]:
                print(f"   {k:<18} " + " | ".join(r[k]))
    (dossier / "bilan.json").write_text(json.dumps({"bilan": bilan, "depense": budget.bilan()}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nDépense : {budget.depense:.4f} $ ({budget.appels} appels) — détail : {dossier.relative_to(RACINE)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
