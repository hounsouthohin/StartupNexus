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
VALIDEE = "validée par le client"


class PorteFermee(RuntimeError):
    pass


def _empreinte(chemin: Path) -> str:
    return hashlib.sha256(chemin.read_bytes()).hexdigest() if chemin.exists() else ""


def ecrire_description(desc: Description, chemin: Path) -> None:
    """La seule façon d'écrire une description (la validation ET la fabrication) : mêmes octets, même empreinte."""
    chemin.write_text(desc.model_dump_json(indent=2), encoding="utf-8")


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


VUE = "miroir.md"      # la vue présentée au client (lue à deux)


def valider(run: Path, client: str, concepteur: str) -> list[str]:
    """Valide le miroir de cette lecture ; renvoie [] si c'est fait, sinon pourquoi c'est refusé.
    (contrat des noms à l'écran, morceau 5) La vue empreintée doit être celle qui DÉCOULE de la description validée : la
    porte la régénère et la compare à la vue présentée (`miroir.md`) ; une vue tirée d'une autre version est refusée."""
    from .contenu import depuis_run, en_markdown
    mi = depuis_run(run)
    raisons = a_valider(mi)
    if raisons:
        return raisons
    vue = run / VUE
    if not vue.exists():
        return [f"la vue du miroir n'a pas été présentée ({VUE} absent) : python -m usine.miroir {run}"]
    if vue.read_text(encoding="utf-8") != en_markdown(mi):
        return [f"la vue présentée ({VUE}) ne découle pas de cette description (une autre version, ou modifiée) : "
                f"régénérez-la (python -m usine.miroir {run}) et relisez-la avec le client"]
    try:
        desc = Description.model_validate(mi["_courant"])
    except (ValidationError, ValueError) as x:
        return [f"la description ne passe pas les contrôles : {str(x).splitlines()[1:2]}"]
    chemin = run / "description-validee.json"
    ecrire_description(desc, chemin)
    (run / "validation.json").write_text(json.dumps({
        "description": chemin.name, "empreinte": _empreinte(chemin),
        "reponses_empreinte": _empreinte(run / "reponses.json"),
        "vue": VUE, "vue_empreinte": _empreinte(vue),
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
    # (contrat des noms à l'écran) la vue que le client a lue : une validation d'avant cette règle n'en a pas l'empreinte
    if not val.get("vue_empreinte"):
        raise PorteFermee("validation d'avant le contrat des noms à l'écran (sans l'empreinte de la vue) — à revalider")
    if _empreinte(chemin.parent / val["vue"]) != val["vue_empreinte"]:
        raise PorteFermee("la vue du miroir a été modifiée depuis sa validation — à revalider")
    return val


def validation_du_run(description: Path, client: dict | None) -> dict:
    """(contrat des noms à l'écran, morceau 5) La validation écrite dans le dossier d'une fabrication. Elle désigne la
    description EXACTE que lisent le traducteur et le juge (`01-description.json`) et porte l'empreinte de ses octets.
    - Un essai de l'usine (`client` absent) est marqué `essai: true` et « essai — non validée par un client » : jamais
      confondu avec un accord de client.
    - Une app de client doit être, à l'octet près, la description que le client a validée ; sinon la porte se ferme."""
    empreinte = _empreinte(description)
    if client is None:
        return {"statut": ESSAI, "essai": True, "description": description.name, "empreinte": empreinte}
    if empreinte != client["empreinte"]:
        raise PorteFermee("la description fabriquée n'est pas, à l'octet près, celle que le client a validée")
    return {"statut": VALIDEE, "essai": False, "description": description.name, "empreinte": empreinte,
            "client": client["client"], "concepteur": client["concepteur"], "quand": client["quand"],
            "validee": {k: client[k] for k in ("description", "empreinte", "reponses_empreinte", "vue", "vue_empreinte")}}
