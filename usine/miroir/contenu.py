"""MIROIR, contenu (N1.4a) : ce que l'usine a compris, CALCULÉ depuis la description et la matrice — jamais
écrit par l'IA, donc il ne peut pas dire autre chose que ce qui sera fabriqué (principe 3).

Lu À DEUX (phase 1 accompagnée, 16 oct) : la vue du client, et sur chaque ligne un volet « concepteur »
(pourquoi, citations du brief, codes des refus). Une description refusée montre ce qui est refusé, pourquoi,
et la variante proposée à la place (usine/variante.py, la même que la répétition fabrique).

    construire(brut, hors_stock, propositions) → miroir (miroir.json)
    en_markdown(miroir) → miroir.md          couverture(miroir) → ce qui manquerait (doit être vide)
"""
from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from ..description import Description
from ..matrice import VISITOR, AccessDeclaration, compute_matrix, questions_detail
from ..variante import proposer, refus

TYPES = {"texte": "texte court", "texte_long": "texte long", "nombre": "nombre", "montant": "montant",
         "date": "date", "date_heure": "date et heure", "oui_non": "oui / non", "email": "e-mail",
         "telephone": "téléphone", "url": "lien web", "choix": "choix"}
ORIGINES = {"brief": "cité dans votre brief", "necessaire": "choisi par nous (le brief n'en disait rien)",
            "proposition": "proposé par nous, accepté"}
DEVIENT = {"bootstrap": "responsable de l'app", "signup": "s'inscrit lui-même", "invited": "invité par {}"}
VOIT = {"all": "voit toutes les fiches", "own": "voit seulement les siennes", "published": "voit celles qui sont publiées"}


def le(label: str, fem: bool = False) -> str:
    return f"l'{label}" if label[:1].lower() in "aeiouyhéèêàâîôû" else f"{'la' if fem else 'le'} {label}"


def _type(c: dict) -> str:
    if c["type"] == "choix" and c.get("valeurs"):
        return "choix parmi : " + ", ".join(v["libelle"] for v in c["valeurs"])
    return TYPES.get(c["type"], c["type"])


def _droits(c) -> dict:
    """Les droits d'une case, tels que le miroir les montre (et que la couverture vérifie)."""
    return {"see": c.see, "see_via": list(c.see_via), "create": c.create, "create_while": list(c.create_while),
            "edit": c.edit, "edit_while": list(c.edit_while), "delete": c.delete, "delete_while": list(c.delete_while),
            "transitions": dict(c.transitions)}


def _actif(d: dict) -> bool:
    return d["see"] != "none" or bool(d["see_via"]) or d["create"] != "no" or d["edit"] or d["delete"] or bool(d["transitions"])


def _phrases(m, decl: AccessDeclaration, a: str) -> list[dict]:
    """Les phrases d'un acteur : les fiches aux droits SIMPLES identiques sont regroupées en une phrase ;
    celles qui dépendent d'un état, d'un circuit ou d'un affichage indirect gardent la leur."""
    ent = {e.name: e for e in decl.entities}
    nom = lambda e: e.label_plural + (f" (dans chaque {ent[e.parent].label})" if e.parent else "")
    etat = lambda e, s: f"« {e.process.labels.get(s, s) if e.process else s} »"
    groupes: dict[tuple, list] = {}
    seules: list[dict] = []
    for name in m.entities:
        c, e = m.cell(a, name), ent[name]
        d = _droits(c)
        if not _actif(d):
            continue
        case = {"fiche": name, "droits": d, "pourquoi": list(c.why), "citations": list(c.sources)}
        # a) son profil
        if e.nature == "profile" and c.see == "own":
            seules.append({"texte": f"a {'sa' if e.feminine else 'son'} {e.label}, créé{'e' if e.feminine else ''} "
                                    "automatiquement" + (", qu'il peut modifier" if c.edit else ""), "cases": [case]})
            continue
        # b0) (n° 59) crée sans voir ensuite (un dépôt) — avant : « affichés dans les  qu'il consulte », phrase vide
        if c.see == "none" and not c.see_via:
            seules.append({"texte": f"crée des {e.label_plural} sans les voir ensuite (dépôt)", "cases": [case]})
            continue
        # b) vu seulement au travers d'autres fiches
        if c.see == "none":
            via = " et les ".join(ent[v].label_plural for v in c.see_via)
            seules.append({"texte": f"voit les {e.label_plural} affiché{'e' if e.feminine else ''}s dans les {via} qu'il consulte (sans page à part)"
                                    + (", en crée" if c.create == "yes" else ""), "cases": [case]})
            continue
        simple = not (c.create_while or c.edit_while or c.delete_while or c.transitions or c.see_via)
        if simple:
            groupes.setdefault((c.see, c.create, c.edit, c.delete), []).append((e, case))
            continue
        parts = [VOIT[c.see].replace("toutes les fiches", "tout")]
        ils = "elles" if e.feminine else "ils"
        if c.create == "yes":
            parts.append("en crée" + (f" tant que {le(ent[e.parent].label, ent[e.parent].feminine)} est "
                                      + " ou ".join(etat(ent[e.parent], s) for s in c.create_while) if c.create_while and e.parent else ""))
        if c.edit:
            parts.append("les modifie" + (f" quand {ils} sont " + " ou ".join(etat(e, s) for s in c.edit_while) if c.edit_while else ""))
        if c.delete:
            parts.append("les supprime" + (f" quand {ils} sont " + " ou ".join(etat(e, s) for s in c.delete_while) if c.delete_while else ""))
        for s, t in c.transitions.items():
            parts.append(f"les fait passer de {etat(e, s)} à " + " ou ".join(etat(e, v) for v in t))
        if c.see_via:
            parts.append("les voit aussi dans les " + " et les ".join(ent[v].label_plural for v in c.see_via))
        seules.append({"texte": f"{nom(e)[0].upper()}{nom(e)[1:]} : " + ", ".join(parts), "cases": [case]})
    phrases = []
    for (see, create, edit, delete), liste in groupes.items():
        verbes = ["voit tout" if see == "all" else VOIT[see]]
        verbes += (["crée"] if create == "yes" else ["les reçoit créées automatiquement"] if create == "auto" else [])
        verbes += (["modifie"] if edit else []) + (["supprime"] if delete else [])
        texte = (", ".join(verbes[:-1]) + " et " + verbes[-1] if len(verbes) > 1 else verbes[0])
        phrases.append({"texte": f"{texte[0].upper()}{texte[1:]} : " + ", ".join(nom(e) for e, _ in liste),
                        "cases": [case for _, case in liste]})
    return phrases + seules


def _circuits(m, decl: AccessDeclaration) -> list[dict]:
    lab = {a.id: a for a in decl.actors}
    out = []
    for e in decl.entities:
        if not e.process:
            continue
        p = e.process
        nomme = lambda s: f"« {p.labels.get(s, s)} »"
        ordre, file = [], [p.initial]
        while file:
            s = file.pop(0)
            if s not in ordre:
                ordre.append(s)
                file += p.transitions.get(s, [])
        lineaire = all(len(p.transitions.get(s, [])) <= 1 for s in ordre)
        texte = (f"{le(e.label, e.feminine).capitalize()} passe par : " + " → ".join(nomme(s) for s in ordre) if lineaire else
                 f"{le(e.label, e.feminine).capitalize()} commence {nomme(p.initial)} ; " +
                 " ; ".join(f"de {nomme(s)}, vers " + " ou ".join(nomme(t) for t in p.transitions[s]) for s in ordre if p.transitions.get(s)))
        qui = [f"{le(lab[c.actor].label, lab[c.actor].feminine).capitalize()} fait passer de {nomme(s)} à " + " ou ".join(nomme(t) for t in ts)
               for c in m.cells if c.entity == e.name and c.actor != VISITOR for s, ts in c.transitions.items()]
        out.append({"fiche": e.name, "texte": texte, "qui": qui, "citations": [p.citation] if p.citation else []})
    return out


def _fiches(decl: AccessDeclaration, champs: dict, propositions: dict) -> list[dict]:
    ent = {e.name: e for e in decl.entities}
    out = []
    for e in decl.entities:
        relie = ([f"dans chaque {ent[e.parent].label}"] if e.parent else []) + [ent[r].label for r in e.references if r in ent]
        out.append({"fiche": e.name, "libelle": e.label, "nature": e.nature, "relie_a": relie,
                    "champs": [{"nom": c["nom"], "libelle": c["libelle"], "type": _type(c), "obligatoire": c["obligatoire"],
                                "origine": c["origine"], "origine_texte": ORIGINES[c["origine"]], "citation": c.get("citation", "")}
                               for c in champs.get(e.name, [])],
                    "propositions": [{"id": f"garder:{e.name}:{p['libelle']}", "libelle": p["libelle"],
                                      "type": TYPES.get(p.get("type"), p.get("type", ""))}
                                     for p in propositions.get(e.name, [])
                                     if p["libelle"] not in {c["libelle"] for c in champs.get(e.name, [])}],
                    "citations": [e.citation] if e.citation else []})
    return out


def _questions(m, decl: AccessDeclaration, champs: dict, brut: dict, refuse: dict | None) -> list[dict]:
    """Les questions sur les droits restent une par une (une erreur y coûte) ; celles sur les noms choisis
    faute d'indication sont regroupées en UNE (au lieu d'une par fiche : le client s'en lassait).
    (N1.4b) Chaque question a un identifiant stable et ses réponses possibles (usine/miroir/reponses.py)."""
    qs = [{"id": f"{q['sorte']}:{q['actor']}:{q['entity']}", "sorte": q["sorte"], "texte": q["texte"].removesuffix(" (oui / non)"),
           "reponses": ["oui", "non"]} for q in questions_detail(m, decl)]
    ent = {e.name: e for e in decl.entities}
    noms = [{"id": f"nom:{f}:{c['nom']}", "texte": f"{ent[f].label} → « {c['libelle']} »"} for f, liste in champs.items()
            if f in ent for c in liste if c["origine"] == "necessaire"]
    if noms:
        qs.append({"id": "noms", "sorte": "noms", "texte": "Votre brief ne disait pas comment reconnaître certaines fiches ; nous avons choisi :",
                   "details": noms, "reponses": ["oui", "<nouveau nom>"]})
    # (N1.4b) « voir les siennes » refusé (pas encore construit) : le client peut décider qu'il voit TOUT
    acteurs = {a["id"]: a for a in brut["acces"]["actors"]}
    entites = {e["name"]: e for e in brut["acces"]["entities"]}
    for x in brut["acces"].get("exceptions", []):
        if (x["action"] == "see" and x.get("allow", True) and x.get("scope", "own") == "own"
                and entites.get(x["entity"], {}).get("owner") != x["actor"] and x["actor"] in acteurs and x["entity"] in entites
                and x["entity"] in ent):                       # pas pour une fiche que la proposition retire
            a, e = acteurs[x["actor"]], entites[x["entity"]]
            qs.append({"id": f"voir_tous:{x['actor']}:{x['entity']}", "sorte": "voir_tous", "reponses": ["oui", "non"],
                       "texte": f"« Seulement ceux qui le concernent » n'est pas encore possible : {le(a['label'].lower(), a.get('feminine', False))} "
                                f"doit-{'elle' if a.get('feminine') else 'il'} voir TOUS les {e['label_plural'].lower()} ?"})
    if refuse and not refuse["rien_ne_se_construit"]:
        qs.append({"id": "accepter_proposition", "sorte": "proposition", "reponses": ["oui", "non"],
                   "texte": "Acceptez-vous de construire le reste, sans ce qui n'est pas encore possible ?"})
    return qs


def construire(brut: dict, hors_stock: list[dict], propositions: dict, critique: dict | None = None) -> dict:
    """Le miroir d'une description (brute : peut-être refusée) — ce qui sera construit, en données. `critique` :
    l'avis du lecteur 8 (adopté le 18 oct), montré au volet concepteur seulement."""
    p = proposer(brut)
    courant = p["courant"] if not p["elargit"] else brut       # (n° 58) une variante qui élargirait n'est pas proposée
    miroir = {"titre": courant["app"].get("titre") or courant["app"]["nom"], "perimetre": "dans", "critique": critique,
              "refus": ({"raisons": p["raisons"], "blocs": p["blocs"], "pas_encore": p["retire"], "elargit": p["elargit"],
                         "rien_ne_se_construit": p["reste_refuse"]} if p["texte"] else None),
              "hors_stock": [{"besoin": h["besoin"], "categorie": h["categorie"], "citation": h.get("citation", "")} for h in hors_stock]}
    try:
        decl = Description.model_validate(courant).acces
    except (ValidationError, ValueError):
        try:
            decl = AccessDeclaration(**courant["acces"])
        except (ValidationError, ValueError):
            return {**miroir, "roles": [], "circuits": [], "fiches": [], "questions": []}
    m = compute_matrix(decl)
    roles = []
    for a in m.actors:
        act = next((x for x in decl.actors if x.id == a), None)
        roles.append({"id": a, "libelle": "Le visiteur (sans compte)" if a == VISITOR else le(act.label, act.feminine).capitalize(),
                      "devient": "" if a == VISITOR else DEVIENT[act.becomes].format(act.invited_by or ""),
                      "citations": [act.citation] if act and act.citation else [],
                      "phrases": _phrases(m, decl, a) or [{"texte": "Ne voit rien", "cases": []}]})
    champs = courant["champs"]
    qs = _questions(m, decl, champs, brut, miroir["refus"])
    # (N1.4b) chaque question est essayée d'avance : si la réponse qui change quelque chose est impossible (le seul qui
    # tient ces fiches, une clôture…), ce n'est pas une vraie question — le miroir l'annonce avec la raison
    from .reponses import OPERANTE, appliquer
    for q in qs:
        if q["sorte"] in OPERANTE:
            _, (r,) = appliquer(brut, propositions, [{"id": q["id"], "valeur": OPERANTE[q["sorte"]]}])
            if not r["applique"]:
                q["reponses"], q["impossible"] = [x for x in q["reponses"] if x != OPERANTE[q["sorte"]]], r["message"]
    return {**miroir, "en_bref": {"roles": [r["libelle"] for r in roles if r["id"] != VISITOR],
                                  "fiches": len(decl.entities), "circuits": sum(1 for e in decl.entities if e.process)},
            "roles": roles, "circuits": _circuits(m, decl), "fiches": _fiches(decl, champs, propositions),
            "questions": qs,
            "_courant": courant, "_brut": brut, "_propositions": propositions, "_hors_stock": hors_stock}


def construire_hors(raison: str, hors_stock: list[dict]) -> dict:
    return {"perimetre": "hors", "raison": raison,
            "hors_stock": [{"besoin": h["besoin"], "categorie": h["categorie"], "citation": h.get("citation", "")} for h in hors_stock]}


def couverture(miroir: dict) -> list[str]:
    """Ce que le miroir oublierait de ce qui sera construit (vide = complet) : chaque case active de la matrice
    est montrée par une phrase AVEC exactement ses droits, chaque champ, chaque proposition, chaque besoin hors
    stock, et le refus s'il y en a un."""
    if miroir["perimetre"] == "hors" or "_courant" not in miroir:
        return []
    courant, manque = miroir["_courant"], []
    try:                                   # la même description que celle du miroir (construire)
        decl = Description.model_validate(courant).acces
    except (ValidationError, ValueError):
        decl = AccessDeclaration(**courant["acces"])
    m = compute_matrix(decl)
    montrees = {(r["id"], case["fiche"]): case["droits"] for r in miroir["roles"] for ph in r["phrases"] for case in ph["cases"]}
    for c in m.cells:
        d = _droits(c)
        if _actif(d) and montrees.get((c.actor, c.entity)) != d:
            manque.append(f"droits de {c.actor} sur {c.entity}")
        if not _actif(d) and (c.actor, c.entity) in montrees:
            manque.append(f"droit montré sans exister : {c.actor} sur {c.entity}")
    fiches = {f["fiche"]: f for f in miroir["fiches"]}
    for nom, liste in courant["champs"].items():
        for c in liste:
            if c["nom"] not in {x["nom"] for x in fiches.get(nom, {}).get("champs", [])}:
                manque.append(f"champ {nom}.{c['nom']}")
    for nom, liste in miroir["_propositions"].items():     # proposée, ou déjà parmi les champs (acceptée)
        if nom in fiches:
            vus = {x["libelle"] for x in fiches[nom]["propositions"] + fiches[nom]["champs"]}
            manque += [f"proposition {nom}.{p['libelle']}" for p in liste if p["libelle"] not in vus]
    vus = {h["besoin"] for h in miroir["hors_stock"]}
    manque += [f"hors stock « {h['besoin']} »" for h in miroir["_hors_stock"] if h["besoin"] not in vus]
    if bool(refus(miroir["_brut"])) != bool(miroir["refus"]):
        manque.append("refus de la description (montré ≠ réel)")
    return manque


def en_markdown(mi: dict) -> str:
    """La lecture du miroir (avant la page, N1.4d) : la vue du client, puis le volet concepteur."""
    if mi["perimetre"] == "hors":
        return f"# Hors de notre périmètre\n\n{mi['raison']}\n"
    L = [f"# {mi['titre']} — ce que l'usine a compris", ""]
    b = mi["en_bref"]
    n = lambda k, mot: f"{k or 'aucun'} {mot}{'s' if k > 1 else ''}"
    L += [f"En bref : {n(len(b['roles']), 'rôle')} ({', '.join(b['roles'])}), {n(b['fiches'], 'sorte')} de fiches, "
          f"{n(b['circuits'], 'circuit')} d'étapes.", ""]
    if mi["refus"]:
        r = mi["refus"]
        L += ["## ⚠ Ce que vous demandez et que je ne sais pas encore faire", ""]
        L += [f"- {x}" for x in r["pas_encore"]] or ["- (voir le volet concepteur)"]
        L += ["", "**Rien ne peut encore se construire sans en reparler ensemble.**" if r["rien_ne_se_construit"]
              else "**Je vous propose de construire tout le reste**, décrit ci-dessous.", ""]
    for r in mi["roles"]:
        L += [f"## {r['libelle']}" + (f" ({r['devient']})" if r["devient"] else ""), *[f"- {p['texte']}" for p in r["phrases"]], ""]
    if mi["circuits"]:
        L += ["## Les étapes", ""]
        for c in mi["circuits"]:
            L += [f"- {c['texte']}", *[f"  - {q}" for q in c["qui"]]]
        L.append("")
    L += ["## Les informations de chaque fiche", ""]
    for f in mi["fiches"]:
        champs = " · ".join(f"{c['libelle']} ({c['type']}{'' if c['obligatoire'] else ', facultatif'})"
                            + ("" if c["origine"] == "brief" else " ◦ " + ("choisi par nous" if c["origine"] == "necessaire" else "proposé, accepté"))
                            for c in f["champs"]) or "aucune information (seulement ses liens)"
        L.append(f"- **{f['libelle'].capitalize()}** : {champs}")
        if f["relie_a"]:
            L.append(f"  - relié à : {', '.join(f['relie_a'])}")
        if f["propositions"]:
            L.append("  - proposé (à cocher) : " + " · ".join(f"☐ {p['libelle']} ({p['type']})" for p in f["propositions"]))
    if mi["questions"]:
        L += ["", "## Questions", ""]
        for q in mi["questions"]:
            L.append(f"- {q['texte']}" + (" " + " · ".join(d["texte"] for d in q["details"]) if q.get("details") else "")
                     + (f" → **{q['reponses'][0] if q['reponses'] else 'oui'}, nécessairement** : {q['impossible'].removeprefix('impossible : ')}"
                        if q.get("impossible") else ""))
    if mi.get("reponses"):
        L += ["", "## Vos réponses", ""]
        L += [f"- {r['id']} = « {r['valeur']} »" + ((f" — {r['message']}" if r["message"] else "") if r["applique"]
                                                         else f" — **non appliquée** : {r['message']}") for r in mi["reponses"]]
    if mi["hors_stock"]:
        L += ["", "## Pas encore dans notre stock (vos mots)", "", *[f"- {h['besoin']} — « {h['citation']} »" for h in mi["hors_stock"]]]
    L += ["", "---", "", "## Volet concepteur", "", "### Pour répondre (`python -m usine.miroir repondre <lecture> id=valeur …`)", ""]
    for q in mi["questions"]:
        L += ([f"- `{d['id']}` = oui | <nouveau nom>  ({d['texte']})" for d in q["details"]] if q.get("details")
              else [f"- `{q['id']}` = {' | '.join(q['reponses'])}"])
    L += [f"- `{p['id']}` = oui | non" for f in mi["fiches"] for p in f["propositions"]]
    L += ["", "### Pourquoi chaque droit", ""]
    for r in mi["roles"]:
        for p in r["phrases"]:
            for case in p["cases"]:
                L.append(f"- {r['id']} / {case['fiche']} : " + " ; ".join(case["pourquoi"] or ["préréglage de la nature"])
                         + (" — « " + " » « ".join(case["citations"]) + " »" if case["citations"] else ""))
    if mi["refus"]:
        r = mi["refus"]
        L += ["", f"### Refus — blocs : {', '.join(r['blocs']) or '—'}", "", *[f"- {x}" for x in r["raisons"]]]
        if r["elargit"]:
            L += ["", "Variante NON proposée : elle donnerait des droits que le brief refuse —", *[f"- {x}" for x in r["elargit"]]]
    if mi.get("critique"):
        ordre = {"bloquant": 0, "important": 1, "mineur": 2}
        L += ["", "### Avis du critique (IA — un avis, à vérifier)", "", f"Cœur du besoin selon lui : {mi['critique']['coeur_du_besoin']}", ""]
        L += [f"- **{s['gravite']}** ({s['sorte'].replace('_', ' ')}) — {s['explication']} — « {s['citation']} »"
              for s in sorted(mi["critique"]["signalements"], key=lambda s: ordre[s["gravite"]])] or ["- rien à signaler"]
    return "\n".join(L) + "\n"


def depuis_run(run: Path) -> dict:
    """Le miroir d'une compréhension déjà faite (runs/<n°>-<nom>-comprendre), sans rien redemander à l'IA."""
    lect = json.loads((run / "lecteurs.json").read_text(encoding="utf-8"))
    per = lect.get("perimetre") or {}
    hors = per.get("hors_stock", [])
    if per.get("perimetre") == "hors":
        return construire_hors(per.get("raison", ""), hors)
    brut = json.loads((run / "description-brute.json").read_text(encoding="utf-8"))
    props = {f["fiche"]: f["propositions"] for f in ((lect.get("champs") or {}).get("fiches") or []) if f.get("propositions")}
    from .reponses import appliquer, lire               # (N1.4b) la description à jour = lecture + réponses
    reps = lire(run)
    if not reps:
        return construire(brut, hors, props, lect.get("critique"))
    a_jour, resultats = appliquer(brut, props, reps)
    return {**construire(a_jour, hors, props, lect.get("critique")), "reponses": resultats}


def propositions_de(run: Path) -> dict:
    lect = json.loads((run / "lecteurs.json").read_text(encoding="utf-8"))
    return {f["fiche"]: f["propositions"] for f in ((lect.get("champs") or {}).get("fiches") or []) if f.get("propositions")}


def ecrire(run: Path, miroir: dict) -> None:
    (run / "miroir.json").write_text(json.dumps({k: v for k, v in miroir.items() if not k.startswith("_")}, ensure_ascii=False, indent=1),
                                     encoding="utf-8")
    (run / "miroir.md").write_text(en_markdown(miroir), encoding="utf-8")
