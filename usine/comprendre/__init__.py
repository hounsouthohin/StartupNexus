"""COMPRENDRE : brief → description de l'app (description.json), par 7 lecteurs IA puis du programme.

Chaque étape laisse sa fiche dans runs/<n°>-<nom>-comprendre/ (règles 6 et 7) :
  brief.txt · lecteurs.json (réponses brutes + journal des appels) · description.json (le contrat
  d'entrée de `fabriquer`) · miroir.md (ce que l'app fera, en phrases, et ce qu'il faut demander au
  client) · 99-rapport.json (dépense, verdict).
Les lecteurs ne décident que de ce qu'ils lisent ; tout le reste (matrice, codes des choix, contrôle
final) est calculé. Plafond de dépense par lancement (ia.py) : la règle de budget est dans le code.
"""
from __future__ import annotations

import json
import re
import time
import unicodedata
from datetime import datetime
from pathlib import Path

from pydantic import ValidationError

from ..description import Description
from ..journal import Journal
from ..matrice import AccessDeclaration, compute_matrix, explain, questions
from . import lecteurs as L
from .ia import Budget, PlafondAtteint, client_pour, demander

RACINE = Path(__file__).resolve().parents[2]
RUNS = RACINE / "runs"


def lire_brief(chemin: str) -> str:
    """Un .txt, ou un fichier de briefs .json (« fichier.json#nom_du_projet » si plusieurs)."""
    fichier, _, projet = chemin.partition("#")
    p = Path(fichier)
    if p.suffix == ".json":
        data = json.loads(p.read_text(encoding="utf-8"))
        items = data if isinstance(data, list) else [data]
        if projet:
            items = [x for x in items if x.get("project_name") == projet]
        if len(items) != 1:
            raise SystemExit(f"{chemin} : préciser le projet (« fichier.json#nom ») parmi "
                             f"{[x.get('project_name') for x in (data if isinstance(data, list) else [data])]}")
        return items[0]["brief"]["description"]
    return p.read_text(encoding="utf-8")


def code_valeur(libelle: str, pris: set[str]) -> str:
    """Le code stable d'une valeur de choix : « bande dessinée » → « bande_dessinee », « 1 » → « v_1 »."""
    s = "".join(ch for ch in unicodedata.normalize("NFD", libelle.lower()) if unicodedata.category(ch) != "Mn")
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_") or "valeur"
    if s[0].isdigit():
        s = f"v_{s}"
    code, n = s, 2
    while code in pris:
        code, n = f"{s}_{n}", n + 1
    pris.add(code)
    return code


def _cite(c: str) -> str:
    """Pour le calculateur (qui vérifie la citation d'un seul tenant) : le plus long passage exact."""
    return max(L._fragments(c), key=len) if L._fragments(c) else c


def declaration(acteurs: L.SortieActeurs, fiches: L.SortieFiches, circuits: L.SortieCircuits, droits: L.SortieDroits) -> dict:
    """Les réponses des lecteurs 1-4 → le format d'accès du calculateur (étude 05). Un circuit posé sur
    une fiche qui n'est ni une collection ni un registre est hors vocabulaire : il n'entre pas."""
    par_fiche = {c.fiche: c for c in circuits.circuits}
    data = {
        "actors": [{"id": a.id, "label": a.libelle, "label_plural": a.libelle_pluriel, "feminine": a.feminin,
                    "becomes": a.devient, "invited_by": a.invite_par, "citation": _cite(a.citation)} for a in acteurs.acteurs],
        "entities": [],
        "exceptions": [{"actor": d.acteur, "entity": d.fiche, "action": d.action, "allow": d.autorise, "scope": d.portee,
                        "while_states": d.pendant_etats, "transitions": d.transitions, "citation": _cite(d.citation)}
                       for d in droits.droits],
    }
    for f in fiches.fiches:
        e = {"name": f.nom, "label": f.libelle, "label_plural": f.libelle_pluriel, "feminine": f.feminin,
             "nature": f.nature, "owner": f.proprietaire, "manager": f.gestionnaires or None, "public": f.publique,
             "publication": f.publication, "entered_by": f.saisie_par, "parent": f.parent,
             "references": f.references, "citation": _cite(f.citation)}
        c = par_fiche.get(f.nom)
        if c and f.nature in ("collection", "registry"):
            e["process"] = {"initial": c.etat_initial, "transitions": c.transitions, "initiator": c.initiateur,
                            "decider": c.decideur, "steps_by": c.etapes_par, "labels": c.libelles,
                            "citation": _cite(c.citation)}
        data["entities"].append(e)
    return data


def infos_fiches(fiches: L.SortieFiches, circuits: L.SortieCircuits) -> dict:
    """Ce que les lecteurs 6 et 7 reçoivent sur chaque fiche (et que leurs contrôles vérifient)."""
    lib = {f.nom: f.libelle for f in fiches.fiches}
    avec_circuit = {c.fiche: c for c in circuits.circuits}
    out = {}
    for f in fiches.fiches:
        liens = [(r, lib.get(r, r)) for r in f.references] + ([(f.parent, lib.get(f.parent, f.parent))] if f.parent else [])
        c = avec_circuit.get(f.nom)
        out[f.nom] = {"libelle": f.libelle, "nature": f.nature, "liens": liens, "circuit": bool(c),
                      "etats": (c.libelles if c else {}),
                      "arrivees": sorted({t for ts in c.transitions.values() for t in ts}) if c else []}
    return out


def lire_champs(sortie: L.SortieChamps | None, brief: str) -> tuple[dict, dict]:
    """Réponse du lecteur 6 → (champs de la description, propositions pour le miroir)."""
    champs, propositions = {}, {}
    for f in (sortie.fiches if sortie else []):
        liste = []
        for c in f.champs:
            pris: set[str] = set()
            liste.append({"nom": c.nom, "libelle": c.libelle, "type": c.type, "obligatoire": c.obligatoire,
                          "valeurs": [{"code": code_valeur(v, pris), "libelle": v} for v in c.valeurs],
                          "origine": c.origine, "citation": _cite(c.citation) if c.origine == "brief" else ""})
        champs[f.fiche] = liste
        if f.propositions:
            propositions[f.fiche] = [p.model_dump() for p in f.propositions]
    return champs, propositions


def comprendre(chemin_brief: str, nom: str, modele: str = "gpt-5.5", plafond: float = 0.20,
               reprendre: Path | None = None) -> Path:
    """reprendre : un dossier « …-comprendre » précédent ; chaque réponse déjà payée y est réutilisée
    si elle passe les contrôles ACTUELS (sinon le lecteur est redemandé)."""
    brief = lire_brief(chemin_brief)
    anciens = json.loads((reprendre / "lecteurs.json").read_text(encoding="utf-8")) if reprendre else {}
    run = RUNS / f"{datetime.now():%Y%m%d-%H%M%S}-{nom}-comprendre"
    run.mkdir(parents=True)
    (run / "brief.txt").write_text(brief, encoding="utf-8")
    journal = Journal(run, total=10)
    budget = Budget(modele, plafond)
    client = client_pour(modele)
    appels: list = []
    sorties: dict = {}
    rapport: dict = {"run": run.name, "brief": chemin_brief, "modele": modele}
    print(f"Compréhension : {run.relative_to(RACINE)} (modèle {modele}, plafond {plafond:.2f} $)\n")

    def fin(verdict: str) -> Path:
        rapport.update(verdict=verdict, depense=budget.bilan(), fini=datetime.now().isoformat(timespec="seconds"))
        (run / "lecteurs.json").write_text(json.dumps({**sorties, "journal": appels}, ensure_ascii=False, indent=2), encoding="utf-8")
        (run / "99-rapport.json").write_text(json.dumps(rapport, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n{verdict} — dépense : {budget.depense:.3f} $ ({budget.appels} appels)")
        return run

    def lecteur(titre: str, consigne: str, donnees: dict, forme, controle, ctx: dict, cle: str):
        with journal.etape(titre) as e:
            if anciens.get(cle) is not None:
                ancien = forme.model_validate(anciens[cle])
                if not controle(ancien, {**ctx, "brief": brief}):
                    sorties[cle] = anciens[cle]
                    e["resume"] = f"repris de {reprendre.name} (0 $)"
                    return ancien
                print("   (réponse précédente refusée par les contrôles actuels : redemandée)", flush=True)
            t0 = time.time()
            r = demander(client, budget, consigne, donnees, forme, controle, {**ctx, "brief": brief}, appels)
            sorties[cle] = r.model_dump() if r else None
            refus = sum(1 for x in appels if x["lecteur"] == forme.__name__ and x["erreurs"])
            e["resume"] = (("refusé 3 fois" if r is None else "accepté") + (f" ({refus} réponse(s) refusée(s) avant)" if refus and r else "")
                           + f" · {budget.depense:.3f} $ cumulés · {time.time() - t0:.0f} s")
            return r

    try:
        perimetre = lecteur("Lecteur 5 — périmètre et hors stock", L.Q_PERIMETRE, {"brief": brief},
                            L.SortiePerimetre, L.controle_perimetre, {}, "perimetre")
        if perimetre is None:
            return fin("ÉCHEC : périmètre illisible")
        if perimetre.perimetre == "hors":
            (run / "miroir.md").write_text(f"# Hors de notre périmètre\n\n{perimetre.raison}\n", encoding="utf-8")
            return fin("HORS PÉRIMÈTRE (aucune description produite)")
        acteurs = lecteur("Lecteur 1 — acteurs", L.Q_ACTEURS, {"brief": brief}, L.SortieActeurs, L.controle_acteurs, {}, "acteurs")
        if acteurs is None:
            return fin("ÉCHEC : acteurs refusés 3 fois")
        ctx = {"actor_ids": [a.id for a in acteurs.acteurs], "non_users": [n.libelle for n in acteurs.non_utilisateurs]}
        base = {"brief": brief, "acteurs": [{"id": a.id, "libelle": a.libelle} for a in acteurs.acteurs],
                "non_utilisateurs": [n.libelle for n in acteurs.non_utilisateurs]}
        fiches = lecteur("Lecteur 2 — fiches", L.Q_FICHES, base, L.SortieFiches, L.controle_fiches, ctx, "fiches")
        if fiches is None:
            return fin("ÉCHEC : fiches refusées 3 fois")
        ctx.update(fiche_names=[f.nom for f in fiches.fiches],
                   registry_managers={f.nom: f.gestionnaires for f in fiches.fiches if f.nature == "registry"},
                   public_fiches={f.nom for f in fiches.fiches if f.publique})
        base2 = {**base, "fiches": [{"nom": f.nom, "libelle": f.libelle, "nature": f.nature} for f in fiches.fiches]}
        circuits = lecteur("Lecteur 3 — circuits", L.Q_CIRCUITS, base2, L.SortieCircuits, L.controle_circuits, ctx, "circuits")
        if circuits is None:
            return fin("ÉCHEC : circuits refusés 3 fois")
        # (N1.1) le lecteur 4 reçoit les états des circuits (codes → libellés) et ses états sont contrôlés
        ctx["etats"] = {c.fiche: set(c.transitions) | {t for ts in c.transitions.values() for t in ts} for c in circuits.circuits}
        base2 = {**base2, "circuits": [{"fiche": c.fiche, "etats": c.libelles} for c in circuits.circuits]}
        droits = lecteur("Lecteur 4 — droits explicites", L.Q_DROITS, base2, L.SortieDroits, L.controle_droits, ctx, "droits")
        if droits is None:
            return fin("ÉCHEC : droits refusés 3 fois")

        with journal.etape("Calculer la matrice (et revoir les droits si un acteur devient aveugle)") as e:
            data = declaration(acteurs, fiches, circuits, droits)
            decl = AccessDeclaration(**data)
            m = compute_matrix(decl, brief=brief)
            # contrôle croisé (étude 05) : une interdiction qui rend un acteur aveugle est renvoyée, une fois
            aveugles = [i.message for i in m.issues if "ne voit rien" in i.message]
            if aveugles and any(not d.autorise for d in droits.droits):
                alerte = ("Avec les droits que tu as donnés : " + " ; ".join(aveugles) + ". Vérifie que le brief dit "
                          "vraiment cela (une phrase générale n'est pas une interdiction totale) et renvoie la liste corrigée.")
                revus = demander(client, budget, L.Q_DROITS, {**base2, "alerte": alerte}, L.SortieDroits, L.controle_droits,
                                 {**ctx, "brief": brief}, appels)
                if revus is not None:
                    droits, sorties["droits_revus"] = revus, revus.model_dump()
                    data = declaration(acteurs, fiches, circuits, droits)
                    decl = AccessDeclaration(**data)
                    m = compute_matrix(decl, brief=brief)
            if m.errors:
                rapport["matrice_erreurs"] = m.errors
                e["resume"] = f"{len(m.errors)} erreur(s)"
            else:
                e["resume"] = f"{len(decl.actors)} rôles, {len(decl.entities)} fiches"
        if m.errors:
            return fin("ÉCHEC : matrice refusée — " + " ; ".join(m.errors))

        info = infos_fiches(fiches, circuits)
        donnees_fiches = [{"fiche": n, "libelle": i["libelle"], "nature": i["nature"],
                           "designe": [lib for _, lib in i["liens"]], "etats": i["etats"]} for n, i in info.items()]
        champs_ia = lecteur("Lecteur 6 — champs", L.Q_CHAMPS, {"brief": brief, "fiches": donnees_fiches},
                            L.SortieChamps, L.controle_champs, {"fiches_info": info}, "champs")
        libelles = lecteur("Lecteur 7 — libellés d'écran", L.Q_LIBELLES,
                           {"brief": brief, "fiches": [{**d, "arrivees": info[d["fiche"]]["arrivees"]} for d in donnees_fiches]},
                           L.SortieLibelles, L.controle_libelles, {"arrivees": {n: i["arrivees"] for n, i in info.items()}}, "libelles")
        if champs_ia is None or libelles is None:
            return fin("ÉCHEC : champs ou libellés refusés 3 fois")
    except PlafondAtteint as x:
        return fin(f"ARRÊT : {x}")

    with journal.etape("Assembler et contrôler la description") as e:
        champs, propositions = lire_champs(champs_ia, brief)
        ecran = {f.fiche: {"verbe_creation": f.verbe_creation, "boutons": f.boutons}
                 for f in libelles.fiches if f.verbe_creation or f.boutons}
        brut = {"app": {"nom": nom, "titre": libelles.titre}, "acces": data, "champs": champs, "ecran": ecran, "depart": {}}
        (run / "description-brute.json").write_text(json.dumps(brut, ensure_ascii=False, indent=2), encoding="utf-8")
        try:
            desc = Description.model_validate(brut)
        except (ValidationError, ValueError) as x:
            rapport["description_refusee"] = str(x)
            e["resume"] = "refusée (voir 99-rapport.json)"
            desc = None
        else:
            (run / "description.json").write_text(desc.model_dump_json(indent=2), encoding="utf-8")
            e["resume"] = f"{sum(len(c) for c in champs.values())} champs, {sum(len(p) for p in propositions.values())} proposition(s)"

    with journal.etape("Écrire le miroir (ce que l'app fera, ce qu'il faut demander)") as e:
        miroir = miroir_md(perimetre, decl, m, champs, propositions)
        (run / "miroir.md").write_text(miroir, encoding="utf-8")
        e["resume"] = f"{miroir.count('?')} question(s)"
    if desc is None:
        return fin("DESCRIPTION REFUSÉE : " + rapport["description_refusee"].splitlines()[1 if "\n" in rapport["description_refusee"] else 0])
    return fin("DESCRIPTION PRÊTE : python -m usine fabriquer " + str((run / "description.json").relative_to(RACINE)))


def miroir_md(perimetre: L.SortiePerimetre, decl: AccessDeclaration, m, champs: dict, propositions: dict) -> str:
    """Première forme du miroir (N1.2 en fera la porte de validation) : tout ce que le client doit voir."""
    lignes = ["# Ce que l'application fera", ""]
    for acteur, phrases in explain(m, decl).items():
        lignes += [f"## {acteur}", *[f"- {p}" for p in phrases], ""]
    lignes += ["# Les informations enregistrées", ""]
    for fiche, liste in champs.items():
        noms = [f"{c['libelle']} ({c['type']}{', facultatif' if not c['obligatoire'] else ''})" for c in liste]
        lignes.append(f"- **{fiche}** : " + (", ".join(noms) if noms else "aucune (seulement ses liens)"))
    necessaires = [(f, c["libelle"]) for f, liste in champs.items() for c in liste if c["origine"] == "necessaire"]
    qs = questions(m, decl) + [f"Le brief ne dit rien des informations de « {f} » : nous avons mis « {lib} » — "
                               "est-ce le bon nom pour la reconnaître ? (oui / non)" for f, lib in necessaires]
    if qs:
        lignes += ["", "# Questions", "", *[f"- {q}" for q in qs]]
    if propositions:
        lignes += ["", "# Informations que nous pourrions ajouter (à confirmer)", ""]
        for fiche, ps in propositions.items():
            lignes.append(f"- **{fiche}** : " + ", ".join(f"{p['libelle']} ({p['type']})" for p in ps))
    if perimetre.hors_stock:
        lignes += ["", "# Pas encore dans notre stock (à traiter à part)", "",
                   *[f"- {b.besoin} — « {b.citation} »" for b in perimetre.hors_stock]]
    return "\n".join(lignes) + "\n"
