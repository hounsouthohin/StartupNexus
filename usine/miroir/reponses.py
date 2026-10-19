"""MIROIR, réponses (N1.4b) : chaque réponse du client — ou du concepteur assis à côté de lui — est une OPÉRATION
écrite d'avance sur la description, sans IA. La lecture d'origine ne change jamais : la description à jour =
lecture + réponses (reponses.json), recalculée à chaque fois ; on peut donc revenir en arrière.

Une réponse qui ne produit pas l'effet voulu, ou qui ferait refuser la description, n'est PAS appliquée : l'usine
dit pourquoi, en phrases. Règle validée le 18 oct : une proposition AUTOMATIQUE ne fait que retirer (n° 58) ; une
réponse EXPLICITE du client peut donner un droit (« le directeur voit tous les soldes ») — notée (qui, quand).

    appliquer(brut, propositions, reponses) → (description à jour, résultat de chaque réponse)
    comparer(miroir_avant, miroir_apres) → ce qui a changé, en lignes « + » / « − »
"""
from __future__ import annotations

import copy
import json
from datetime import datetime
from pathlib import Path

from pydantic import ValidationError

from ..matrice import VISITOR, AccessDeclaration, compute_matrix
from ..variante import proposer, refus

CITATION = "(réponse au miroir)"
# la réponse qui CHANGE quelque chose, par sorte de question (l'autre laisse la description telle quelle)
OPERANTE = {"registre_entier": "non", "tout_le_monde": "non", "vu_via": "non", "visiteur": "non", "voir_tous": "oui",
            "accepter_proposition": "oui"}
RESERVES = ("id", "status", "ownerId", "userId", "createdAt", "published")


def champ_propose(p: dict, champs: list) -> dict | None:
    """Le champ ajouté quand une proposition est gardée (le client simulé des répétitions passe par ici aussi).
    Facultatif, origine « proposition » ; un « choix » proposé n'a pas de valeurs : il devient un texte."""
    from ..comprendre import code_valeur
    if p["libelle"].lower() in {c["libelle"].lower() for c in champs}:
        return None
    nom = code_valeur(p["libelle"], set())
    nom = "".join(w if i == 0 else w.capitalize() for i, w in enumerate(nom.removeprefix("v_").split("_")))
    pris, base, k = {c["nom"] for c in champs}, nom, 2
    while nom in pris or nom in RESERVES:
        nom, k = f"{base}{k}", k + 1
    return {"nom": nom, "libelle": p["libelle"], "type": "texte" if p["type"] == "choix" else p["type"],
            "obligatoire": False, "valeurs": [], "origine": "proposition", "citation": ""}


# ─── Les opérations (sur une copie de la description) ─────────────────────────────────────────────────────
def _entite(d: dict, nom: str) -> dict:
    return next(e for e in d["acces"]["entities"] if e["name"] == nom)


def _interdire_voir(d: dict, actor: str, entity: str) -> None:
    """« Non, il ne doit pas les voir » : il ne les tient plus, ses droits écrits sur elles tombent, un refus de voir
    est écrit. (Ses autres droits sur ces fiches tomberaient de toute façon : on ne modifie pas ce qu'on ne voit pas.)"""
    e = _entite(d, entity)
    if isinstance(e.get("manager"), list):
        e["manager"] = [x for x in e["manager"] if x != actor]
    elif e.get("manager") == actor:
        e["manager"] = None
    ex = d["acces"].setdefault("exceptions", [])
    ex[:] = [x for x in ex if not (x["actor"] == actor and x["entity"] == entity and x.get("allow", True))]
    ex.append({"actor": actor, "entity": entity, "action": "see", "allow": False, "citation": CITATION})


def _voir_tous(d: dict, actor: str, entity: str) -> None:
    """« Oui, il doit voir TOUS les … » (décision explicite du client) : son « voir les siennes » devient « toutes »."""
    ex = d["acces"].setdefault("exceptions", [])
    ex[:] = [x for x in ex if not (x["actor"] == actor and x["entity"] == entity and x["action"] == "see")]
    ex.append({"actor": actor, "entity": entity, "action": "see", "allow": True, "scope": "all", "citation": CITATION})


def _construite(d: dict) -> dict:
    """Ce qui sera construit à partir de d : d lui-même, ou la proposition si d est refusée (les questions du miroir
    portent sur elle ; l'effet d'une réponse se vérifie donc sur elle)."""
    p = proposer(d)
    return p["courant"] if not p["elargit"] else d


def _erreurs(d: dict) -> set[str]:
    try:
        return set(compute_matrix(AccessDeclaration(**_construite(d)["acces"])).errors)
    except (ValidationError, ValueError):
        return set()


def _effet(d: dict, r: dict, avant: set[str]) -> str:
    """'' si l'effet voulu est obtenu sur ce qui sera construit ; sinon pourquoi, en phrases (rien en silence)."""
    m = compute_matrix(AccessDeclaration(**_construite(d)["acces"]))
    neuves = [e for e in m.errors if e not in avant]   # seulement ce que CETTE réponse casserait (pas un refus d'avant)
    if neuves:
        return "impossible : " + " ; ".join(e.split("] ", 1)[-1] for e in neuves)[:400]
    sorte, _, reste = r["id"].partition(":")
    fiche = reste.split(":")[-1]
    if sorte not in ("garder", "nom") and fiche not in m.entities:
        return "impossible : ces fiches ne seront pas construites (voir « pas encore possible »)"
    if sorte in ("registre_entier", "tout_le_monde", "vu_via"):
        actor, entity = reste.split(":")
        c = m.cell(actor, entity)
        if c.see != "none" or c.see_via:
            pourquoi = [w for w in c.why if w.startswith("clôture")] or c.why
            return "impossible : il doit les voir quand même — " + "; ".join(pourquoi[-2:])
    if sorte == "visiteur":
        if m.cell(VISITOR, reste.split(":")[-1]).see != "none":
            return "impossible : le visiteur les voit encore"
    if sorte == "voir_tous":
        actor, entity = reste.split(":")
        if m.cell(actor, entity).see != "all":
            return "impossible : il ne les voit toujours pas toutes"
    return ""


def _une(d: dict, r: dict, propositions: dict, avant: set[str]) -> str:
    """Applique UNE réponse sur d (modifié en place) ; '' si appliquée, sinon pourquoi (d est alors à jeter)."""
    sorte, _, reste = r["id"].partition(":")
    v = str(r["valeur"]).strip()
    if sorte == "garder":
        if v != "oui":
            return "ok-rien"
        fiche, libelle = reste.split(":", 1)
        p = next((p for p in propositions.get(fiche, []) if p["libelle"] == libelle), None)
        if p is None or fiche not in {e["name"] for e in d["acces"]["entities"]}:
            return "cette proposition n'existe pas (ou plus)"
        champ = champ_propose(p, d["champs"].setdefault(fiche, []))
        if champ is None:
            return "ok-rien"
        d["champs"][fiche].append(champ)
    elif sorte == "nom":
        fiche, nom = reste.split(":", 1)
        champ = next((c for c in d["champs"].get(fiche, []) if c["nom"] == nom), None)
        if champ is None:
            return "ce champ n'existe plus"
        if not v or v.lower() == "oui":
            return "ok-rien"
        champ["libelle"] = v
    elif sorte in ("registre_entier", "tout_le_monde", "vu_via"):
        if v != "non":
            return "ok-rien"
        _interdire_voir(d, *reste.split(":"))
    elif sorte == "visiteur":
        if v != "non":
            return "ok-rien"
        # (seulement le visiteur : rendre la fiche « non publique » retirait aussi la vue d'autres rôles — vu par la preuve)
        d["acces"].setdefault("exceptions", []).append({"actor": VISITOR, "entity": reste.split(":")[-1], "action": "see",
                                                        "allow": False, "citation": CITATION})
    elif sorte == "voir_tous":
        if v != "oui":
            return "ok-rien"
        _voir_tous(d, *reste.split(":"))
    else:
        return f"réponse inconnue : {r['id']}"
    return _effet(d, r, avant)


def appliquer(brut: dict, propositions: dict, reponses: list[dict]) -> tuple[dict, list[dict]]:
    """La description à jour : la lecture + les réponses, dans l'ordre (« accepter la proposition » en dernier)."""
    d, resultats, accepter = copy.deepcopy(brut), [], None
    for r in reponses:
        if r["id"] == "accepter_proposition":
            accepter = r
            continue
        d2 = copy.deepcopy(d)
        try:
            pourquoi = _une(d2, r, propositions, _erreurs(d))
        except (ValidationError, ValueError, KeyError, StopIteration) as x:
            pourquoi = f"impossible : {(str(x).splitlines() or [type(x).__name__])[0][:200]}"
        if pourquoi in ("", "ok-rien"):
            # le texte de l'erreur seulement (pydantic y recopie toute la description : « [type=…, input_value=…] »)
            net = lambda t: {l.split(" [type=")[0].strip() for l in t.splitlines() if l.strip()}
            neufs = sorted(net(refus(d2)) - net(refus(d)))
            if neufs:
                pourquoi = "impossible : la description serait refusée — " + " ".join(neufs)[:300]
        applique = pourquoi in ("", "ok-rien")
        if applique:
            d = d2
        resultats.append({**r, "applique": applique, "message": "" if applique else pourquoi})
    if accepter is not None and str(accepter["valeur"]).strip() == "oui":
        p = proposer(d)
        message = ("" if p["retire"] and not p["elargit"] else
                   "elle donnerait des droits que le brief refuse" if p["elargit"] else "rien à accepter : aucun refus")
        if not message:
            d = p["courant"]
        # (honnêteté) ce qui a été laissé de côté reste écrit : après l'acceptation, le refus disparaît du miroir
        resultats.append({**accepter, "applique": not message,
                          "message": message or "construit SANS : " + " ; ".join(p["retire"])})
    return d, resultats


# ─── Ce qui a changé ──────────────────────────────────────────────────────────────────────────────────────
def _lignes(mi: dict) -> set[str]:
    out = set()
    for r in mi.get("roles", []):
        out |= {f"{r['libelle']} — {p['texte']}" for p in r["phrases"]}
    for f in mi.get("fiches", []):
        out |= {f"{f['libelle']} : information « {c['libelle']} » ({c['type']}, {c['origine_texte']})" for c in f["champs"]}
    if mi.get("refus"):
        out |= {f"pas encore possible : {x}" for x in mi["refus"]["pas_encore"]}
        out.add("rien ne se construit sans en reparler" if mi["refus"]["rien_ne_se_construit"] else "proposition : construire le reste")
    return out


def comparer(avant: dict, apres: dict) -> list[str]:
    a, b = _lignes(avant), _lignes(apres)
    return [f"+ {x}" for x in sorted(b - a)] + [f"− {x}" for x in sorted(a - b)]


# ─── reponses.json (dans le dossier de la lecture) ────────────────────────────────────────────────────────
def lire(run: Path) -> list[dict]:
    f = run / "reponses.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else []


def ajouter(run: Path, nouvelles: dict[str, str], qui: str) -> list[dict]:
    """Ajoute des réponses (une nouvelle réponse à la même question remplace l'ancienne) ; renvoie la liste."""
    rs = [r for r in lire(run) if r["id"] not in nouvelles]
    quand = datetime.now().isoformat(timespec="seconds")
    rs += [{"id": k, "valeur": v, "qui": qui, "quand": quand} for k, v in nouvelles.items()]
    (run / "reponses.json").write_text(json.dumps(rs, ensure_ascii=False, indent=1), encoding="utf-8")
    return rs
