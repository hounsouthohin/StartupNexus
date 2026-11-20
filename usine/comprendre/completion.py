"""LA COMPLÉTION de la description (format 2, contrat des noms à l'écran, morceau 3 — 20 nov 2026).

Elle se fait AVANT le miroir, et seulement là : tout ce qu'elle ajoute est montré au client, qui peut le corriger. Le
traducteur, lui, ne devine jamais rien (une description sans ces noms est refusée).

Pour chaque fiche principale (ni profil, ni ligne) :
- le nom du bouton de création, s'il manque : la règle de grammaire (« Nouveau / Nouvel / Nouvelle » + le nom), qui
  n'est plus cachée dans le traducteur : elle écrit un nom que le miroir montre ;
- le titre, s'il manque, dans cet ordre :
  (a) le premier champ texte court obligatoire ;
  (b) sinon, la première fiche désignée dont le titre est un tel champ, si CHAQUE rôle qui voit la fiche voit TOUTES
      les fiches désignées (un titre ne doit ni être vide, ni montrer une fiche interdite) ;
  (c) sinon, un champ « Libellé » obligatoire, marqué « nécessaire » : il apparaît dans la question du miroir « nous avons
      choisi : … », et il n'existe que si le client valide.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

from ..description import FORMAT
from ..matrice import AccessDeclaration, compute_matrix


def charger_lecture(chemin: Path) -> dict:
    """Charge une LECTURE de brief (`description-brute.json` ou `description.json` d'un dossier `…-comprendre`) et la
    complète si elle date d'avant le format 2. Une lecture n'est pas encore validée par un client : c'est de la matière
    d'AVANT le miroir, et la complétion est justement l'étape qui la met au format 2 (tout ce qu'elle ajoute est montré
    au client). Une description VALIDÉE par un client (`description-validee.json`) ne passe jamais par ici : en format 1,
    elle reste refusée, et elle doit être revalidée."""
    brut = json.loads(Path(chemin).read_text(encoding="utf-8"))
    if brut.get("format") != FORMAT:
        brut, _ = completer(brut)
    return brut


def nom_creation_par_defaut(label: str, feminine: bool) -> str:
    """« Nouvelle facture », « Nouvel ouvrage », « Nouveau chantier ». Faux devant un h aspiré (« Nouvel hangar ») :
    c'est pourquoi le nom est montré au miroir, où le client le corrige (et le lecteur des libellés en proposera un)."""
    nouveau = "Nouvelle" if feminine else "Nouvel" if label[:1].lower() in "aeiouyéèêâîôh" else "Nouveau"
    return f"{nouveau} {label}"


def completer(brut: dict) -> tuple[dict, list[str]]:
    """Renvoie la description complétée (format 2) et la liste, en français, de ce qui a été ajouté."""
    d = copy.deepcopy(brut)
    d["format"] = FORMAT
    entites = {e["name"]: e for e in d["acces"]["entities"]}
    principales = [n for n, e in entites.items() if e.get("nature") not in ("profile", "child")]
    champs = d.setdefault("champs", {})
    ecran = d.setdefault("ecran", {})
    notes: list[str] = []

    def titre_a(f: str) -> str | None:
        return next((c["nom"] for c in champs.get(f, []) if c.get("type") == "texte" and c.get("obligatoire", True)), None)

    try:
        matrice = compute_matrix(AccessDeclaration(**d["acces"]))
        cases = {(c.actor, c.entity): c for c in matrice.cells} if not matrice.errors else None
    except Exception:            # une déclaration refusée se signale ailleurs, avec sa raison
        matrice, cases = None, None

    def visible_en_entier(f: str, cible: str) -> bool:
        if not cases:
            return False
        for a in matrice.actors:
            vue, vue_cible = cases.get((a, f)), cases.get((a, cible))
            if vue and vue.see != "none" and (not vue_cible or vue_cible.see != "all"):
                return False
        return True

    for f in principales:
        e = entites[f]
        ec = ecran.setdefault(f, {})
        if not ec.get("creation"):
            ec["creation"] = nom_creation_par_defaut(e["label"], e.get("feminine", False))
            notes.append(f"{f} : bouton de création « {ec['creation']} » (règle par défaut)")
        if ec.get("titre"):
            continue
        a = titre_a(f)
        if a:
            ec["titre"] = a
            notes.append(f"{f} : reconnue par son champ « {a} »")
            continue
        proprio = e.get("owner")
        liens = [r for r in e.get("references") or []
                 if r in principales and not (entites[r].get("nature") == "profile" and entites[r].get("owner") == proprio)]
        b = next((r for r in liens if titre_a(r) and visible_en_entier(f, r)), None)
        if b:
            ec["titre"] = b
            notes.append(f"{f} : reconnue par la fiche « {b} » qu'elle désigne")
            continue
        noms = {c["nom"] for c in champs.get(f, [])}
        nom = "libelle" if "libelle" not in noms else "libelleFiche"
        champs.setdefault(f, []).append({"nom": nom, "libelle": "Libellé", "type": "texte", "obligatoire": True,
                                         "valeurs": [], "origine": "necessaire", "citation": ""})
        ec["titre"] = nom
        notes.append(f"{f} : aucun champ ne la reconnaît ; un « Libellé » obligatoire est proposé (à valider au miroir)")
    return d, notes
