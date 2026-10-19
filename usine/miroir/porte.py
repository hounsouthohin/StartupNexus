"""LA PORTE (N1.4c, 19 oct) : rien ne se fabrique pour un client sans qu'il ait validé son miroir ; toute
modification après la validation l'annule.

    valider(lecture, client, concepteur) → description-validee.json + validation.json (qui, quand, empreintes)
    verifier(description) → lève PorteFermee si la description n'est pas celle, intacte, que le client a validée

Règles validées par l'utilisateur : la validation est REFUSÉE tant qu'une demande refusée n'a pas sa proposition
acceptée, ou qu'une question sur les DROITS n'a pas de réponse (valider ne dit jamais « oui » à la place du client ;
les champs proposés et les noms peuvent rester tels quels). Les essais de l'usine (répétitions, corpus, exemples)
passent par un mode `essai` explicite, marqué « essai — non validée par un client ».
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path

from pydantic import ValidationError

from ..description import Description

DROITS = ("registre_entier", "tout_le_monde", "vu_via", "visiteur", "voir_tous")
ESSAI = "essai — non validée par un client"


class PorteFermee(RuntimeError):
    pass


def _empreinte(chemin: Path) -> str:
    return hashlib.sha256(chemin.read_bytes()).hexdigest() if chemin.exists() else ""


def a_valider(mi: dict) -> list[str]:
    """Pourquoi ce miroir ne peut pas encore être validé (vide = il peut l'être)."""
    from .contenu import couverture
    if mi["perimetre"] == "hors":
        return ["hors de notre périmètre : rien à construire"]
    raisons = []
    if mi["refus"]:
        raisons.append("des demandes ne sont pas encore possibles : acceptez la proposition (accepter_proposition = oui) "
                       "ou revoyez-les ensemble" if not mi["refus"]["rien_ne_se_construit"]
                       else "rien ne peut encore se construire sans en reparler ensemble")
    repondues = {r["id"] for r in mi.get("reponses", []) if r["applique"]}
    sans = [q for q in mi["questions"] if q["sorte"] in DROITS and len(q["reponses"]) > 1 and q["id"] not in repondues]
    raisons += [f"question sans réponse (droits) : {q['texte']}  [{q['id']}]" for q in sans]
    raisons += [f"miroir incomplet : {t}" for t in couverture(mi)]
    return raisons


def valider(run: Path, client: str, concepteur: str) -> list[str]:
    """Valide le miroir de cette lecture ; renvoie [] si c'est fait, sinon pourquoi c'est refusé."""
    from .contenu import depuis_run
    mi = depuis_run(run)
    raisons = a_valider(mi)
    if raisons:
        return raisons
    try:
        desc = Description.model_validate(mi["_courant"])
    except (ValidationError, ValueError) as x:
        return [f"la description ne passe pas les contrôles : {str(x).splitlines()[1:2]}"]
    chemin = run / "description-validee.json"
    chemin.write_text(desc.model_dump_json(indent=2), encoding="utf-8")
    (run / "validation.json").write_text(json.dumps({
        "description": chemin.name, "empreinte": _empreinte(chemin),
        "reponses_empreinte": _empreinte(run / "reponses.json"),
        "client": client, "concepteur": concepteur, "quand": datetime.now().isoformat(timespec="seconds"),
        "reponses": len(mi.get("reponses", []))}, ensure_ascii=False, indent=1), encoding="utf-8")
    return []


def annuler(run: Path, pourquoi: str) -> None:
    """Une nouvelle réponse après la validation l'annule (elle reste écrite, marquée annulée)."""
    v = run / "validation.json"
    if v.exists():
        val = json.loads(v.read_text(encoding="utf-8"))
        if not val.get("annulee"):
            val["annulee"] = {"quand": datetime.now().isoformat(timespec="seconds"), "pourquoi": pourquoi}
            v.write_text(json.dumps(val, ensure_ascii=False, indent=1), encoding="utf-8")


def verifier(chemin: Path) -> dict:
    """La porte de `fabriquer` : la validation existe, n'est pas annulée, porte sur CE fichier, intact, et aucune
    réponse n'a été ajoutée depuis. Renvoie la validation ; lève PorteFermee sinon."""
    v = chemin.parent / "validation.json"
    if not v.exists():
        raise PorteFermee(f"« {chemin} » n'a pas été validée par le client (python -m usine.miroir valider <lecture> "
                          "--client …) ; pour un essai de l'usine : --essai")
    val = json.loads(v.read_text(encoding="utf-8"))
    if val.get("annulee"):
        raise PorteFermee(f"validation annulée le {val['annulee']['quand']} : {val['annulee']['pourquoi']} — à revalider")
    if chemin.name != val["description"]:
        raise PorteFermee(f"ce n'est pas la description validée (« {val['description']} »)")
    if _empreinte(chemin) != val["empreinte"]:
        raise PorteFermee("la description a été modifiée depuis sa validation — à revalider")
    if _empreinte(chemin.parent / "reponses.json") != val["reponses_empreinte"]:
        raise PorteFermee("des réponses ont changé depuis la validation — à revalider")
    return val
