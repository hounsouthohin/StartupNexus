"""
scripts/matrix_ai_probe.py
──────────────────────────
Test de l'IA en fin de phase 3 (USINE.md) : l'IA sait-elle remplir l'entrée de la matrice ?

Pour chaque projet du banc (harness/matrices/<projet>.access.yaml) :
  1. on donne à l'IA le brief + les acteurs + les entités (noms, libellés, et les états quand
     l'entité en a) — SANS leur classement ;
  2. elle classe : nature, propriétaire, gestionnaires, public, publication, saisi par, parent,
     qui crée, qui fait évoluer chaque état, et comment on devient chaque acteur ;
  3. si sa classification est refusée (validation stricte), on lui renvoie l'erreur précise
     (2 essais de plus, règle 3 d'USINE.md §4.6) ;
  4. on recalcule la matrice avec SA classification (références, citations et exceptions
     restent celles écrites à la main) et on la compare à la matrice attendue.

Les exemples du prompt viennent volontairement d'AUTRES domaines que ceux du banc :
le score mesure la compréhension, pas la reconnaissance d'exemples.

Usage (dans le conteneur) : python scripts/matrix_ai_probe.py [--only <projet>] [--model gpt-4o-mini]
"""
from __future__ import annotations

import argparse
import asyncio
import copy
import json
import sys
from collections import Counter
from pathlib import Path

import yaml
from pydantic import ValidationError

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from scripts.matrix_bench import MATRICES, _actual_cell, _brief, _expected_cell  # noqa: E402
from agents.capability_matrix import AccessDeclaration, compute_matrix  # noqa: E402

SYSTEM = """Tu lis le brief d'une application et tu classes ses entités pour un calculateur de droits.
On te donne les acteurs et les entités : ne les renomme pas, n'en invente pas.

NATURE (une par entité) :
- "profile" : l'identité d'UNE personne sur elle-même (nom, téléphone, coordonnées). Une par personne.
    Ce n'est PAS « mes affaires » : « mon carnet de recettes » ou « mes factures » ne sont pas des profils.
- "catalog" : un référentiel commun, consulté par tous, géré par un ou des responsables
    (le menu d'un restaurant, les modèles de vélos d'un loueur).
- "collection" : des éléments qui APPARTIENNENT chacun à un acteur précis
    (les tickets d'un client, les devis d'un artisan, les candidatures d'un étudiant).
    « mes X personnalisés » = collection. Une collection reste une collection même si ses éléments
    référencent autre chose (un devis référence un client : c'est quand même une collection).
- "child" : des éléments SANS propriétaire à eux, qui n'existent qu'à l'intérieur d'un parent et se
    gèrent avec lui (les lignes d'un devis, les commentaires d'un ticket). En cas de doute : collection.

CHAMPS (pour désigner un acteur, utilise TOUJOURS son id exact, jamais son libellé) :
- "owner" (profile, collection) : l'acteur à qui chaque élément appartient.
- "manager" (catalog SEULEMENT) : les acteurs dont le brief dit qu'ils créent, proposent ou gèrent
    ce catalogue ; liste vide si le brief ne le dit pas.
- "public" : true seulement si le brief dit qu'un visiteur NON connecté le voit. Une collection
    publique (les annonces de particuliers : chacun gère les siennes, tout le monde les voit) a public=true.
- "publication" : true seulement si le brief parle de brouillon / publié. Un simple statut ne suffit pas.
- "entered_by" : seulement si le brief dit qu'un acteur saisit les éléments POUR leur propriétaire
    (le comptable saisit les dépenses de ses clients) ; sinon null.
- "parent" (child seulement) : l'entité parente.
- "created_by" : l'acteur qui crée les éléments (souvent le propriétaire).
- "evolution" (seulement pour les entités dont on te donne les états) : pour CHAQUE état qui a une
    suite, l'acteur qui fait passer à l'état suivant. Ex. {"brouillon": "auteur", "soumis": "relecteur"}.

ACTEURS — "becomes" : "bootstrap" pour le propriétaire de l'app (celui qui dit « je » dans le brief,
ou le responsable unique) ; "invited" seulement si le brief dit qu'un acteur en fait venir un autre
(avec "invited_by") ; sinon "signup" (s'inscrit seul).

Réponds UNIQUEMENT en JSON, pour TOUS les acteurs et TOUTES les entités donnés :
{"actors": {"<id>": {"becomes": "<valeur>", "invited_by": "<id ou null>"}},
 "entities": {"<Nom>": {"nature": "<valeur>", "owner": "<id ou null>", "manager": ["<id>"],
                         "public": true ou false, "publication": true ou false,
                         "entered_by": "<id ou null>", "parent": "<Nom ou null>",
                         "created_by": "<id ou null>", "evolution": "<objet ou null>"}}}"""


def _bool(value, where: str) -> bool:
    """Booléen strict (règle 3) : « false » en texte n'est PAS vrai. Tout le reste est refusé."""
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, str) and value.strip().lower() in ("true", "false"):
        return value.strip().lower() == "true"
    raise ValueError(f"{where} : booléen attendu (true / false), reçu {value!r}")


def _to_access(raw_yaml: dict, ai: dict) -> dict:
    """Entrée de la matrice où la classification de l'IA remplace celle écrite à la main."""
    data = copy.deepcopy(raw_yaml)
    actors = ai.get("actors") or {}
    entities = ai.get("entities") or {}
    for a in data["actors"]:
        g = actors.get(a["id"]) or {}
        a["becomes"] = g.get("becomes") or "signup"
        a["invited_by"] = g.get("invited_by")
    for e in data["entities"]:
        g = entities.get(e["name"]) or {}
        e["nature"] = g.get("nature")
        e["owner"] = g.get("owner") if g.get("nature") in ("profile", "collection") else None
        mgr = g.get("manager")
        e["manager"] = ([mgr] if isinstance(mgr, str) else list(mgr or [])) or None if g.get("nature") == "catalog" else None
        e["public"] = _bool(g.get("public"), f"{e['name']}.public")
        e["publication"] = _bool(g.get("publication"), f"{e['name']}.publication")
        e["entered_by"] = g.get("entered_by") if g.get("nature") == "collection" else None
        e["parent"] = g.get("parent") if g.get("nature") == "child" else None
        p = e.get("process")
        if p is not None:
            evo = {s: who for s, who in (g.get("evolution") or {}).items() if who}
            decider = Counter(evo.values()).most_common(1)[0][0] if evo else p["decider"]
            p["initiator"] = g.get("created_by") or p["initiator"]
            p["decider"] = decider
            p["steps_by"] = {s: who for s, who in evo.items() if who != decider and s in p["transitions"]}
            if p["steps_by"] or e["entered_by"]:
                e["entered_by"] = e["entered_by"] if e["entered_by"] == p["initiator"] else None
    return data


def _check(raw_yaml: dict, ai: dict) -> tuple[AccessDeclaration | None, list[str]]:
    try:
        decl = AccessDeclaration(**_to_access(raw_yaml, ai))
    except ValidationError as e:
        return None, [f"{'.'.join(map(str, x['loc']))} : {x['msg']}" for x in e.errors()]
    except ValueError as e:
        return None, [str(e)]
    errors = compute_matrix(decl).errors
    return (decl, []) if not errors else (None, errors)


async def probe(project: str, llm) -> dict:
    from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
    raw_yaml = yaml.safe_load((MATRICES / f"{project}.access.yaml").read_text(encoding="utf-8"))
    hand = AccessDeclaration(**raw_yaml)
    payload = {
        "brief": _brief(project) or "",
        "acteurs": [{"id": a.id, "libelle": a.label} for a in hand.actors],
        "entites": [
            {"nom": e.name, "libelle": e.label,
             **({"etats": {e.process.labels.get(s, s): [e.process.labels.get(t, t) for t in nxt]
                           for s, nxt in e.process.transitions.items()},
                 "noms_techniques_des_etats": {e.process.labels.get(s, s): s for s in e.process.transitions}}
                if e.process else {})}
            for e in hand.entities
        ],
        "consigne": "Dans « evolution », utilise les noms techniques des états.",
    }
    messages = [SystemMessage(content=SYSTEM), HumanMessage(content=json.dumps(payload, ensure_ascii=False))]
    attempts, ai, decl, errors = 0, {}, None, []
    for attempts in range(1, 4):
        resp = await llm.ainvoke(messages)
        try:
            ai = json.loads(resp.content)
        except json.JSONDecodeError:
            errors = ["réponse non JSON"]
        else:
            decl, errors = _check(raw_yaml, ai)
        if decl is not None:
            break
        messages += [AIMessage(content=resp.content),
                     HumanMessage(content="Classification refusée :\n- " + "\n- ".join(errors)
                                  + "\nCorrige et renvoie le JSON complet.")]

    matrix_diffs: list[str] = []
    if decl is None:
        matrix_diffs = [f"refusée après {attempts} essais : {e}" for e in errors]
    else:
        m = compute_matrix(decl)
        cells = (yaml.safe_load((MATRICES / f"{project}.expected.yaml").read_text(encoding="utf-8")) or {}).get("cells") or {}
        for c in m.cells:
            want = _expected_cell((cells.get(c.actor) or {}).get(c.entity) or {})
            got = _actual_cell(c)
            for k in want:
                if want[k] != got[k]:
                    matrix_diffs.append(f"{c.actor}/{c.entity}.{k} : attendu {want[k]!r}, avec l'IA {got[k]!r}")

    # Écarts de classification (pour comprendre), entité par entité
    class_diffs = []
    for e in hand.entities:
        g = (ai.get("entities") or {}).get(e.name) or {}
        if g.get("nature") != e.nature:
            class_diffs.append(f"{e.name} : nature main={e.nature} IA={g.get('nature')}")
    for a in hand.actors:
        g = (ai.get("actors") or {}).get(a.id) or {}
        if g.get("becomes") != a.becomes:
            class_diffs.append(f"acteur {a.id} : main={a.becomes} IA={g.get('becomes')} (chemin d'entrée)")
    return {"project": project, "attempts": attempts, "matrix_diffs": matrix_diffs, "class_diffs": class_diffs}


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", action="append", default=[])
    parser.add_argument("--model", default="gpt-4o-mini")
    args = parser.parse_args()
    from dotenv import load_dotenv
    load_dotenv()
    from agents.llm_provider import get_chat_llm
    llm = get_chat_llm(model=args.model, temperature=0.0).bind(response_format={"type": "json_object"})

    projects = sorted(p.name[: -len(".access.yaml")] for p in MATRICES.glob("*.access.yaml"))
    if args.only:
        projects = [p for p in projects if p in args.only]
    results = [await probe(p, llm) for p in projects]

    print(f"\n═══ Classification par {args.model} → matrice recalculée vs attendue ═══")
    for r in results:
        ok = not r["matrix_diffs"]
        print(f"\n{'✓' if ok else '✗'} {r['project']:<18} essais {r['attempts']} · cases fausses {len(r['matrix_diffs'])}")
        for d in r["class_diffs"]:
            print(f"    classement {d}")
        for d in r["matrix_diffs"][:10]:
            print(f"    matrice    {d}")
    good = sum(1 for r in results if not r["matrix_diffs"])
    print(f"\nMatrices justes avec la classification de l'IA : {good}/{len(results)}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
