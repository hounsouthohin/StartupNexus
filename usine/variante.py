"""REFUSER, PUIS PROPOSER À LA PLACE : pourquoi l'usine refuse une description, et la variante qu'elle sait
construire sans les blocs pas encore construits. Déplacé de repetition.py (16 oct, N1.4a) : le miroir montre au
client ce que la répétition fabriquait déjà — une seule logique pour les deux (principe 3).
"""
from __future__ import annotations

import copy
import re

from pydantic import ValidationError

from .description import Description


def blocs_refuses(raisons: str) -> list[str]:
    """Les blocs pas encore construits que citent des refus — lus dans leurs CODES stables (« [bloc:<id>] »,
    « [limite:…] », « [erreur:…] »), écrits par la description et le calculateur (12 oct : avant, des morceaux de
    phrase, cassés dès qu'un message était reformulé)."""
    return sorted({m[1] if m[0] == "bloc" else f"{m[0]} {m[1]}" for m in re.findall(r"\[(bloc|limite|erreur):([\w:-]+)\]", raisons)})


def refus(brut: dict) -> str:
    """Pourquoi l'usine refuserait cette description : contrôle strict, puis matrice ('' si rien)."""
    from .matrice import compute_matrix
    try:
        desc = Description.model_validate(brut)
    except (ValidationError, ValueError) as x:
        return str(x)
    m = compute_matrix(desc.acces)
    return ("matrice refusée :\n- " + "\n- ".join(m.errors)) if m.errors else ""


def _retirer_fiches(d: dict, noms: set[str]) -> set[str]:
    """Retire des fiches de la déclaration, avec leurs lignes (enfants), les liens vers elles et leurs exceptions."""
    noms = set(noms)
    while enfants := {e["name"] for e in d["entities"] if e.get("parent") in noms} - noms:
        noms |= enfants
    d["entities"] = [e for e in d["entities"] if e["name"] not in noms]
    for e in d["entities"]:
        e["references"] = [r for r in e.get("references", []) if r not in noms]
    d["exceptions"] = [x for x in d.get("exceptions", []) if x["entity"] not in noms]
    return noms


def variante(decl: dict, raisons: str) -> tuple[dict, list[str]]:
    """Ce que l'usine sait construire sans les blocs pas encore construits, et ce qu'elle retire — en phrases pour le
    client. (n° 58, 18 oct) RÈGLE : une variante ne fait que RETIRER (une fiche, un lien, un droit) ; elle ne donne et
    ne transfère jamais un droit (avant : « saisie pour autrui » faisait saisir le propriétaire lui-même — l'étudiant
    créait ses notes et ses diplômes ; trouvé par le critique, essai A). `elargissements` le vérifie après coup."""
    d, retire = copy.deepcopy(decl), []
    codes = blocs_refuses(raisons)
    ent = lambda n: next((e for e in d["entities"] if e["name"] == n), {"label": n, "label_plural": n})
    def act(a, debut=False):                   # « le décideur », « l'employé », « la secrétaire »
        x = next((x for x in d["actors"] if x["id"] == a), {"label": a or "?", "feminine": False})
        s = f"l'{x['label'].lower()}" if x["label"][:1].lower() in "aeiouyhéèêàâîôû" else f"{'la' if x.get('feminine') else 'le'} {x['label'].lower()}"
        return s[0].upper() + s[1:] if debut else s
    if "limite ligne-de-ligne" in codes:      # (N1.3) les fiches enfants sont construites ; pas une ligne de ligne
        natures = {e["name"]: e["nature"] for e in d["entities"]}
        petits = {e["name"] for e in d["entities"] if e["nature"] == "child" and natures.get(e.get("parent")) == "child"}
        retire += [f"les {ent(n)['label_plural']} (des lignes à l'intérieur d'autres lignes) : pas encore possible — retirées"
                   for n in sorted(petits)]
        _retirer_fiches(d, petits)
    if "portee:published" in codes:            # brouillons et publication : la fiche est retirée (rendre tout visible donnerait un droit)
        pub = {e["name"] for e in d["entities"] if e.get("publication")}
        retire += [f"les {ent(n)['label_plural']} avec brouillons et publication : pas encore possible — retirées" for n in sorted(pub)]
        _retirer_fiches(d, pub)
    if "lien:profil" in codes:
        for e in d["entities"]:
            if e["nature"] == "profile" and e.get("references"):
                retire.append(f"relier chaque {e['label']} à " + ", ".join(ent(r)["label"] for r in e["references"])
                              + " : pas encore possible — lien retiré")
                e["references"] = []
    if "portee:designe" in codes:
        # (a) « voir les siennes » par un acteur qui ne possède pas ces fiches : le droit est retiré, et dit en clair
        proprio = {e["name"]: e.get("owner") for e in d["entities"]}
        hors = [x for x in d.get("exceptions", []) if x["action"] == "see" and x.get("allow", True)
                and x.get("scope", "own") == "own" and proprio.get(x["entity"]) != x["actor"]]
        retire += [f"⚠ {act(x['actor'], True)} ne verra pas les {ent(x['entity'])['label_plural']} qui le concernent "
                   "(voir celles qui le désignent : pas encore possible)" for x in hors]
        d["exceptions"] = [x for x in d.get("exceptions", []) if x not in hors]
        # (b) les liens à choisir PARMI LES SIENS : ceux que le calculateur a refusés (12 oct : lus dans la matrice)
        from .matrice import AccessDeclaration, compute_matrix
        for lien in compute_matrix(AccessDeclaration(**d)).own_choice_links:
            fiche, cible = lien.split(">")
            e = next(x for x in d["entities"] if x["name"] == fiche)
            if cible in e.get("references", []):
                e["references"].remove(cible)
                retire.append(f"choisir, dans un(e) {e['label']}, un(e) {ent(cible)['label']} parmi les siens : "
                              "pas encore possible — lien retiré")
    if "acteur:invitation" in codes:
        natures = {e["name"]: e["nature"] for e in d["entities"]}
        proprio = {e["name"]: e.get("owner") for e in d["entities"]}
        inv = [x for x in d.get("exceptions", []) if x["action"] == "create" and x.get("allow", True)
               and natures.get(x["entity"]) == "profile" and proprio.get(x["entity"]) != x["actor"]]
        retire += [f"{act(x['actor'], True)} crée le compte des {ent(x['entity'])['label_plural']} : pas encore possible "
                   "(les invitations arrivent avec la connexion)" for x in inv]
        d["exceptions"] = [x for x in d.get("exceptions", []) if x not in inv]
    if "lien:pour-autrui" in codes:             # (n° 58) la fiche est RETIRÉE — le propriétaire ne saisit pas à la place
        autrui = {e["name"]: (e.get("entered_by") or (e.get("process") or {}).get("initiator")) for e in d["entities"]
                  if e["nature"] == "collection" and (e.get("entered_by") or (e.get("process") and e["process"]["initiator"] != e["owner"]))}
        retire += [f"les {ent(n)['label_plural'].lower()} que {act(qui)} saisit pour {act(ent(n).get('owner'))} : pas encore possible — retirées"
                   for n, qui in sorted(autrui.items())]
        _retirer_fiches(d, set(autrui))
    if "erreur etats-inconnus" in codes:       # seulement les exceptions qui DONNENT (en retirer une qui interdit élargirait)
        etats = {e["name"]: (set((e.get("process") or {}).get("transitions", {}))
                             | {t for ts in (e.get("process") or {}).get("transitions", {}).values() for t in ts}) for e in d["entities"]}
        mauvaises = [x for x in d.get("exceptions", []) if x.get("allow", True) and not
                     (set(x.get("while_states", [])) | set(x.get("transitions", {}))
                      | {t for ts in x.get("transitions", {}).values() for t in ts}) <= etats.get(x["entity"], set())]
        retire += [f"un droit de {act(x['actor'])} sur les {ent(x['entity'])['label_plural']} lié à une étape que le brief ne "
                   "définit pas — retiré" for x in mauvaises]
        d["exceptions"] = [x for x in d.get("exceptions", []) if x not in mauvaises]
    return d, retire


VOIR = {"none": 0, "own": 1, "published": 1, "all": 2}


def elargissements(brut: dict, courant: dict) -> list[str]:
    """(n° 58) Les droits que la proposition DONNE au-delà de la lecture d'origine (vide = elle ne fait que retirer).
    Comparaison des deux matrices, case par case ; une fiche retirée n'a plus de case."""
    from .matrice import AccessDeclaration, compute_matrix
    try:
        avant = compute_matrix(AccessDeclaration(**brut["acces"]))
    except (ValidationError, ValueError):
        return []                                           # rien de calculable à comparer
    apres = compute_matrix(AccessDeclaration(**courant["acces"]))
    out = []
    for b in apres.cells:
        try:
            a = avant.cell(b.actor, b.entity)
        except KeyError:
            continue
        en_plus = []
        if VOIR[b.see] > VOIR[a.see] or {a.see, b.see} == {"own", "published"} or (a.see == "none" and set(b.see_via) - set(a.see_via)):
            en_plus.append(f"voir ({a.see} → {b.see})")
        if b.create != "no" and a.create == "no":
            en_plus.append("créer")
        for droit, ok_a, ok_b, w_a, w_b in (("modifier", a.edit, b.edit, a.edit_while, b.edit_while),
                                            ("supprimer", a.delete, b.delete, a.delete_while, b.delete_while)):
            if ok_b and (not ok_a or (w_a and (not w_b or not set(w_b) <= set(w_a)))):
                en_plus.append(droit)
        en_plus += [f"faire passer de {s} à {t}" for s, ts in b.transitions.items() for t in ts if t not in a.transitions.get(s, [])]
        if en_plus:
            out.append(f"{b.actor} / {b.entity} : " + ", ".join(en_plus))
    return out


def proposer(brut: dict) -> dict:
    """Ce que l'usine refuse dans cette description, et la variante qu'elle propose à la place : refus de la
    description PUIS de la matrice ; chaque variante peut en révéler un suivant (3 au plus).
    → courant (la description à construire : la brute si rien n'est refusé), texte, raisons, blocs, retire,
      elargit (droits que la variante DONNERAIT — doit être vide), reste_refuse (rien ne se construit : un refus que
      la variante ne lève pas, ou une variante qui élargirait)."""
    toutes, retire_tout, courant = [], [], brut
    for _ in range(3):
        raisons = refus(courant)
        if not raisons:
            break
        toutes.append(raisons)
        decl2, retire = variante(courant["acces"], raisons)
        if not retire:
            break
        gardes = {e["name"] for e in decl2["entities"]}
        courant = {**courant, "acces": decl2, "champs": {k: v for k, v in courant["champs"].items() if k in gardes},
                   "ecran": {k: v for k, v in courant["ecran"].items() if k in gardes}}
        retire_tout += retire
    texte = "\n".join(toutes)
    elargit = elargissements(brut, courant) if retire_tout else []
    return {"courant": courant, "texte": texte, "blocs": blocs_refuses(texte) if texte else [],
            "raisons": [l.strip("- ").strip() for l in texte.splitlines()
                        if l.strip() and not l.strip().endswith(":") and "validation error" not in l],
            "retire": retire_tout, "elargit": elargit,
            "reste_refuse": bool(toutes) and (bool(refus(courant)) or bool(elargit))}
