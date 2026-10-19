"""RÉPÉTITION GÉNÉRALE, temps 1 (0 $) : les 10 briefs du lot d'apprentissage passent dans toute la
chaîne, à partir des descriptions DÉJÀ PAYÉES à l'étude 05 (gpt-5.5 ; v3 quand elle existe, sinon v2).

Pour chaque brief :
  1. périmètre : les « hors » doivent être reconnus (grille de l'étude 05) ;
  2. description : le contrôle strict l'accepte, ou dit quel BLOC manque ;
  3. fabrication : l'app est fabriquée et jugée (règles, écrans) — sinon, l'étape qui échoue.
Si la description est refusée pour un bloc pas encore construit (enfant, publication…), une VARIANTE
sans ce bloc est aussi essayée, pour trouver les blocages SUIVANTS (étiquetée comme telle).

Les descriptions de l'étude 05 n'ont pas de champs : un champ « nom » FACULTATIF est ajouté à chaque
fiche par la répétition (pas par l'IA), seulement pour que les listes soient lisibles. Les formulaires
et les champs se jugeront au temps 2 (lecteurs 6-7, sur accord de dépense).

    python -m usine.repetition [--seulement appr-formation]

TEMPS 2 (coût IA) : `--chaine-reelle [--modele gpt-5.5]` — les 7 lecteurs lisent chaque brief (champs et
libellés compris), puis l'app est fabriquée et jugée ; chaque app est ensuite remise à l'utilisateur pour
un essai à la main (`python -m usine demarrer runs/<n°>`).
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
from datetime import datetime
from pathlib import Path

import yaml
from pydantic import ValidationError

from .assembler import RUNS, fabriquer
from .description import Description

RACINE = Path(__file__).resolve().parents[1]
E5 = RACINE / "poc" / "comprehension"
# (16 oct, N1.4a) refuser puis proposer à la place : partagé avec le miroir (usine/variante.py)
from .variante import blocs_refuses, proposer, refus, variante  # noqa: E402,F401


def source(projet: str) -> tuple[Path, str]:
    for version in ("v3-passe1", "v2-passe1"):
        p = E5 / "sorties" / "gpt-5.5" / version / f"{projet}.json"
        if p.exists():
            return p, version
    raise FileNotFoundError(projet)


def description_brute(projet: str, decl: dict) -> dict:
    return {"app": {"nom": projet.removeprefix("appr-"), "titre": projet.removeprefix("appr-").replace("-", " ").capitalize()},
            "acces": decl,
            "champs": {e["name"]: [{"nom": "nom", "libelle": "Nom", "type": "texte", "obligatoire": False,
                                    "origine": "necessaire"}] for e in decl["entities"]},
            "ecran": {}, "depart": {}}


def essayer(nom: str, brut: dict, dossier: Path) -> dict:
    """Contrôle strict puis fabrication ; renvoie le verdict."""
    try:
        Description.model_validate(brut)
    except (ValidationError, ValueError) as x:
        texte = str(x)
        return {"etape": "description refusée", "raisons": [l.strip("- ").strip() for l in texte.splitlines()[1:] if l.strip()],
                "blocs": blocs_refuses(texte)}
    chemin = dossier / f"{nom}.json"
    chemin.write_text(json.dumps(brut, ensure_ascii=False, indent=2), encoding="utf-8")
    debut = datetime.now()
    try:
        run = fabriquer(chemin, essai=True)      # (N1.4c) essai de l'usine, sans client : marqué, la porte ne s'applique pas
    except Exception as x:   # l'étape qui échoue est dans le journal de fabrication
        runs = sorted((p for p in RUNS.glob(f"*-{brut['app']['nom']}") if p.stat().st_mtime >= debut.timestamp() - 1),
                      key=lambda p: p.stat().st_mtime)
        echec = {}
        if runs and (runs[-1] / "journal.jsonl").exists():
            evts = [json.loads(l) for l in (runs[-1] / "journal.jsonl").read_text(encoding="utf-8").splitlines()]
            echec = next((e for e in reversed(evts) if e.get("statut") == "echec"), {})
        return {"etape": f"fabrication : {echec.get('etape', '?')}", "raisons": [str(echec.get("erreur", x))[:600]],
                "run": runs[-1].name if runs else None}
    rapport = json.loads((run / "99-rapport.json").read_text(encoding="utf-8"))
    return {"etape": "fabriquée et jugée", "run": run.name, **rapport.get("verdicts", {}), "blocs_utilises": rapport.get("blocs", [])}


def chaine_reelle(projets: dict[str, str], source: str, modele: str, dossier: Path,
                  deja: dict[str, Path] | None = None, client_simule: bool = False) -> list[dict]:
    """TEMPS 2 : la chaîne RÉELLE — les lecteurs IA lisent le brief (champs compris), puis l'usine fabrique
    et juge. Si la description est refusée pour un bloc pas encore construit, une variante sans ce bloc
    est fabriquée (étiquetée) pour que l'utilisateur puisse tester le reste.
    deja : les compréhensions complètes d'une répétition précédente (reprises à 0 $, jamais repayées)."""
    from .comprendre import comprendre
    tableau = []
    for projet in projets:
        if deja and projet in deja:
            print(f"\n════ {projet} — compréhension reprise de {deja[projet].name} (déjà payée)", flush=True)
            ligne = fabriquer_depuis(deja[projet], projet, projets[projet], dossier, client_simule)
            ligne["deja_paye"] = True
            tableau.append(ligne)
            (dossier / "repetition.json").write_text(json.dumps(tableau, ensure_ascii=False, indent=2), encoding="utf-8")
            a_tester(dossier)
            continue
        print(f"\n════ {projet} — compréhension ({modele})", flush=True)
        try:
            run_c = comprendre(f"{source}#{projet}", projet.removeprefix("appr-"), modele)
        except SystemExit as x:   # crédit épuisé chez le fournisseur : on s'arrête en gardant ce qui est fait
            print(f"   ARRÊT de la répétition : {x}", flush=True)
            break
        tableau.append(fabriquer_depuis(run_c, projet, projets[projet], dossier, client_simule))
        (dossier / "repetition.json").write_text(json.dumps(tableau, ensure_ascii=False, indent=2), encoding="utf-8")
        a_tester(dossier)
    return tableau


def accepter_propositions(brut: dict, run_c: Path) -> int:
    """CLIENT SIMULÉ (répétition seulement, étiqueté) : il accepte toutes les propositions de champs du
    lecteur 6, comme le fera un client au miroir (N1.4). Champs facultatifs, origine « proposition ».
    Un « choix » proposé n'a pas de valeurs : il devient un texte. Renvoie le nombre de champs ajoutés."""
    from .miroir.reponses import champ_propose      # (N1.4b) le même ajout que la réponse « garder » du miroir
    lect = json.loads((run_c / "lecteurs.json").read_text(encoding="utf-8"))
    ajoutes = 0
    for f in (lect.get("champs") or {}).get("fiches", []):
        champs = brut["champs"].setdefault(f["fiche"], [])
        for p in f.get("propositions", []):
            champ = champ_propose(p, champs)
            if champ is not None:
                champs.append(champ)
                ajoutes += 1
    return ajoutes


def fabriquer_depuis(run_c: Path, projet: str, attendu: str, dossier: Path, client_simule: bool = False) -> dict:
    """D'une compréhension (déjà payée) à l'app : la description est recontrôlée avec le code ACTUEL ;
    si elle est refusée pour un bloc pas encore construit, la variante sans ce bloc est fabriquée.
    client_simule : les propositions de champs sont acceptées (étiqueté dans la ligne et dans a-tester.md)."""
    rapport = json.loads((run_c / "99-rapport.json").read_text(encoding="utf-8"))
    ligne = {"brief": projet, "comprehension": run_c.name, "verdict_comprehension": rapport["verdict"],
             "cout": rapport["depense"]["dollars"], "perimetre_attendu": attendu}
    source = next((run_c / f for f in ("description.json", "description-brute.json") if (run_c / f).exists()), None)
    if source is None:
        return ligne
    brut = json.loads(source.read_text(encoding="utf-8"))
    ligne["champs"] = sum(len(c) for c in brut["champs"].values())
    if client_simule:
        ligne["client_simule"] = accepter_propositions(brut, run_c)
    # refus de la description PUIS de la matrice, et la variante proposée à la place (usine/variante.py)
    p = proposer(brut)
    if p["texte"]:
        ligne["refus"] = {"raisons": p["raisons"], "blocs": p["blocs"], "elargit": p["elargit"]}
    if p["retire"] and p["elargit"]:          # (n° 58) une variante qui donnerait des droits n'est ni proposée ni fabriquée
        print(f"   → pas de variante : elle donnerait des droits ({'; '.join(p['elargit'])})", flush=True)
    elif p["retire"]:
        courant = {**p["courant"], "app": {**p["courant"]["app"], "nom": p["courant"]["app"]["nom"] + "-variante"}}
        print(f"   → variante sans : {', '.join(p['retire'])}", flush=True)
        ligne["variante"] = {"sans": p["retire"], **essayer(courant["app"]["nom"], courant, dossier)}
    elif not p["texte"]:
        ligne["essai"] = essayer(brut["app"]["nom"], brut, dossier)
    return ligne


def derniere_comprehension(ligne: dict) -> Path:
    """La compréhension complète la plus récente de ce brief (ex. après un lecteur redemandé par un contrôle
    corrigé), sinon celle de la ligne."""
    nom = ligne["brief"].removeprefix("appr-")
    complets = sorted(p for p in RUNS.glob(f"*-{nom}-comprendre") if (p / "99-rapport.json").exists())
    return complets[-1] if complets else RUNS / ligne["comprehension"]


def a_tester(dossier: Path) -> Path:
    """La liste des apps à essayer à la main (guide : usine/ESSAIS.md), une ligne par app fabriquée."""
    tableau = json.loads((dossier / "repetition.json").read_text(encoding="utf-8"))
    lignes = [f"# Apps à essayer — {dossier.name}", "", "Mode d'emploi et fiche de retour : `usine/ESSAIS.md`.", "",
              "**Apps d'ESSAI — non validées par un client** (N1.4c : la porte ne s'applique qu'aux apps des clients).", "",
              "| Brief | App | Juges de l'usine | Lancer | Lire avant (brief, miroir) |", "|---|---|---|---|---|"]
    for l in tableau:
        comp = f"runs/{l['comprehension']}"
        cs = f" · client simulé (+{l['client_simule']} champs proposés par l'IA)" if l.get("client_simule") else ""
        for cle, nom in (("essai", "app" + cs), ("variante", "variante sans " + ", ".join(l.get("variante", {}).get("sans", [])) + cs)):
            e = l.get(cle)
            if e and e.get("etape") == "fabriquée et jugée":
                lignes.append(f"| {l['brief']} | {nom} | {e.get('regles', '')} · {e.get('ecrans', '')} | "
                              f"`python -m usine demarrer runs/{e['run']} --depart` | `{comp}/brief.txt`, `{comp}/miroir.md` |")
            elif e:
                lignes.append(f"| {l['brief']} | {nom} | **{e.get('etape')}** | — | `{comp}/miroir.md` |")
        if not l.get("essai") and not l.get("variante"):
            lignes.append(f"| {l['brief']} | — | {l['verdict_comprehension'][:90]} | — | `{comp}/miroir.md` |")
    chemin = dossier / "a-tester.md"
    chemin.write_text("\n".join(lignes) + "\n", encoding="utf-8")
    return chemin


def resumer(tableau: list[dict], dossier: Path, paye: bool) -> None:
    print(f"\n\nRÉPÉTITION ({'chaîne réelle' if paye else 'rejouée, 0 $'}) — {dossier.relative_to(RACINE)}")
    for l in tableau:
        e, v = l.get("essai", {}), l.get("variante", {})
        print(f"- {l['brief']:<28} {l['cout']:.3f} $ · {l['verdict_comprehension'][:50]} | "
              + (f"{e.get('etape')} {e.get('regles', '')} {e.get('ecrans', '')}" if e else "")
              + (f"variante ({', '.join(v['sans'])}) : {v.get('etape')} {v.get('regles', '')} {v.get('ecrans', '')}" if v else ""))
    if paye:
        print(f"Dépense de ce lancement : {sum(l['cout'] for l in tableau if not l.get('deja_paye')):.3f} $ "
              f"(compréhensions reprises, déjà payées : {sum(l['cout'] for l in tableau if l.get('deja_paye')):.3f} $)")
    print(f"À essayer : {dossier.relative_to(RACINE)}/a-tester.md")


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser()
    p.add_argument("--seulement", action="append", default=[])
    p.add_argument("--chaine-reelle", action="store_true", help="temps 2 : les lecteurs IA lisent les briefs (coût IA)")
    p.add_argument("--modele", default="gpt-5.5")
    p.add_argument("--corpus", help="dossier d'un corpus (briefs.json + references.yaml), ex. usine/corpus ; "
                                    "par défaut le lot d'apprentissage")
    p.add_argument("--a-tester", type=Path, help="réécrire la liste des apps à essayer d'une répétition déjà faite")
    p.add_argument("--reprendre-de", type=Path, action="append", default=[],
                   help="(avec --chaine-reelle) reprendre à 0 $ les compréhensions complètes d'une répétition précédente")
    p.add_argument("--client-simule", action="store_true",
                   help="les apps prennent les champs proposés par l'IA, comme si le client les acceptait au miroir (étiqueté)")
    p.add_argument("--rejouer", type=Path, help="refabriquer (0 $) à partir des compréhensions d'une répétition réelle déjà faite")
    p.add_argument("--rassembler", type=Path, nargs="+", help="une seule liste à essayer : pour chaque brief, la ligne la plus "
                                                              "récente de ces répétitions (dans l'ordre donné)")
    args = p.parse_args()
    if args.rassembler:
        par_brief: dict[str, dict] = {}
        for d in args.rassembler:
            for l in json.loads((d / "repetition.json").read_text(encoding="utf-8")):
                par_brief[l["brief"]] = l
        dossier = RUNS / f"{datetime.now():%Y%m%d-%H%M%S}-repetition-rassemblee"
        dossier.mkdir(parents=True)
        (dossier / "repetition.json").write_text(json.dumps(list(par_brief.values()), ensure_ascii=False, indent=2), encoding="utf-8")
        print(a_tester(dossier))
        return 0
    if args.a_tester:
        print(a_tester(args.a_tester))
        return 0
    if args.rejouer:
        anciennes = json.loads((args.rejouer / "repetition.json").read_text(encoding="utf-8"))
        dossier = RUNS / f"{datetime.now():%Y%m%d-%H%M%S}-repetition-rejouee"
        dossier.mkdir(parents=True)
        tableau = []
        for l in anciennes:
            if args.seulement and l["brief"] not in args.seulement:
                continue
            print(f"\n════ {l['brief']} — refabriqué depuis {l['comprehension']} (0 $)", flush=True)
            tableau.append(fabriquer_depuis(derniere_comprehension(l), l["brief"], l.get("perimetre_attendu", "?"), dossier,
                                             args.client_simule))
            (dossier / "repetition.json").write_text(json.dumps(tableau, ensure_ascii=False, indent=2), encoding="utf-8")
            a_tester(dossier)
        resumer(tableau, dossier, paye=False)
        return 0
    if args.chaine_reelle:
        if args.corpus:
            refs, briefs = RACINE / args.corpus / "references.yaml", f"{args.corpus}/briefs.json"
        else:
            refs, briefs = E5 / "references.yaml", "factory-sprint0/harness/briefs_reels/apprentissage/briefs.json"
        grille = yaml.safe_load(refs.read_text(encoding="utf-8"))["briefs"]
        projets = {x: r["perimetre"] for x, r in grille.items() if not args.seulement or x in args.seulement}
        deja = {}
        for r in args.reprendre_de:
            for l in json.loads((r / "repetition.json").read_text(encoding="utf-8")):
                if (RUNS / l["comprehension"] / "99-rapport.json").exists():
                    deja[l["brief"]] = RUNS / l["comprehension"]
        dossier = RUNS / f"{datetime.now():%Y%m%d-%H%M%S}-repetition-reelle"
        dossier.mkdir(parents=True)
        try:
            resumer(chaine_reelle(projets, briefs, args.modele, dossier, deja, args.client_simule), dossier, paye=True)
        finally:
            if args.modele == "boite":
                from .comprendre.ia import fin_de_lot
                fin_de_lot()           # la session isolée s'arrête
        return 0
    grille = yaml.safe_load((E5 / "references.yaml").read_text(encoding="utf-8"))["briefs"]
    dossier = RUNS / f"{datetime.now():%Y%m%d-%H%M%S}-repetition"
    dossier.mkdir(parents=True)
    tableau = []
    for projet, ref in grille.items():
        if args.seulement and projet not in args.seulement:
            continue
        chemin, version = source(projet)
        r = json.loads(chemin.read_text(encoding="utf-8"))
        ligne = {"brief": projet, "source": f"étude 05, {version}", "perimetre_attendu": ref["perimetre"],
                 "perimetre_obtenu": (r.get("perimetre") or {}).get("perimetre")}
        print(f"\n════ {projet} ({version}) — périmètre attendu {ligne['perimetre_attendu']}, obtenu {ligne['perimetre_obtenu']}", flush=True)
        if ref["perimetre"] == "hors" or ligne["perimetre_obtenu"] == "hors":
            ligne["verdict"] = ("hors périmètre reconnu ✔" if ligne["perimetre_obtenu"] == ref["perimetre"] == "hors"
                                else f"périmètre FAUX (attendu {ref['perimetre']})")
            tableau.append(ligne)
            continue
        if not r.get("declaration"):
            ligne["verdict"] = f"compréhension incomplète à l'étude 05 : {r.get('echec', '?')}"
            tableau.append(ligne)
            continue
        ligne["essai"] = essayer(projet.removeprefix("appr-"), description_brute(projet, r["declaration"]), dossier)
        refus_matrice = "Calculer la matrice" in ligne["essai"]["etape"] and "absent(s) du circuit" in " ".join(ligne["essai"]["raisons"])
        if ligne["essai"]["etape"] == "description refusée" or refus_matrice:
            decl2, retire = variante(r["declaration"], " ".join(ligne["essai"]["raisons"]))
            if retire:
                print(f"   → variante sans : {', '.join(retire)}", flush=True)
                ligne["variante"] = {"sans": retire, **essayer(projet.removeprefix("appr-") + "-variante",
                                                                 description_brute(projet + "-variante", decl2), dossier)}
        tableau.append(ligne)
        (dossier / "repetition.json").write_text(json.dumps(tableau, ensure_ascii=False, indent=2), encoding="utf-8")
    (dossier / "repetition.json").write_text(json.dumps(tableau, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n\nRÉPÉTITION — {dossier.relative_to(RACINE)}")
    for l in tableau:
        e, v = l.get("essai", {}), l.get("variante", {})
        print(f"- {l['brief']:<24} " + (l.get("verdict") or f"{e.get('etape')} {e.get('regles', '')} {e.get('ecrans', '')}"
              + (f" | variante ({', '.join(v['sans'])}) : {v.get('etape')} {v.get('regles', '')} {v.get('ecrans', '')}" if v else "")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
