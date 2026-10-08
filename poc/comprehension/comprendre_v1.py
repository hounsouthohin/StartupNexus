"""
E5 — Les agents de compréhension (essai jetable, l'usine n'est pas touchée).

Chaque agent répond à UNE question sur le brief, en JSON. Sa réponse est contrôlée par programme
(forme stricte, identifiants connus, citations recopiées mot pour mot) ; si elle est refusée, on lui
renvoie l'erreur précise (2 essais de plus — règle 3 d'USINE.md §4.6). Les agents ne connaissent
pas les préréglages : c'est le calculateur de la phase 3 qui en déduit la matrice.

  1. Acteurs              qui se connecte, et comment on le devient
  2. Fiches               ce qu'on enregistre, sa nature, à qui c'est
  3. Circuits             quelles fiches passent par des états, qui fait chaque étape
  4. Droits explicites    ce que le brief DIT explicitement (supprimer, tout voir…)
  5. Périmètre            dans ou hors de nos logiciels de gestion ; ce qui est hors stock

Les exemples des consignes viennent d'autres domaines que les briefs testés (un pressing, une école
de musique) : on mesure la compréhension, pas la reconnaissance d'exemples.

Usage : python comprendre.py --model gpt-5.4-mini [--only appr-formation]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, ValidationError

ROOT = Path(__file__).resolve().parents[2]
FACTORY = ROOT / "factory-sprint0"
sys.path.insert(0, str(FACTORY))
from agents.capability_matrix import (  # noqa: E402  (lecture seule)
    AccessDeclaration, _norm, compute_matrix, explain, questions,
)

BRIEFS = FACTORY / "harness" / "briefs_reels" / "apprentissage" / "briefs.json"
OUT = Path(__file__).resolve().parent / "sorties"


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


# ─── Formes attendues ──────────────────────────────────────────────────────────────────────
class ActeurIA(_Strict):
    id: str
    libelle: str
    libelle_pluriel: str
    feminin: bool
    devient: Literal["signup", "bootstrap", "invited"]
    invite_par: str | None
    citation: str


class NonUtilisateur(_Strict):
    libelle: str
    citation: str


class SortieActeurs(_Strict):
    acteurs: list[ActeurIA]
    non_utilisateurs: list[NonUtilisateur]


class FicheIA(_Strict):
    nom: str
    libelle: str
    libelle_pluriel: str
    feminin: bool
    nature: Literal["profile", "catalog", "collection", "child"]
    proprietaire: str | None
    gestionnaires: list[str]
    publique: bool
    publication: bool
    saisie_par: str | None
    parent: str | None
    references: list[str]
    citation: str


class SortieFiches(_Strict):
    fiches: list[FicheIA]


class CircuitIA(_Strict):
    fiche: str
    etat_initial: str
    transitions: dict[str, list[str]]
    libelles: dict[str, str]
    initiateur: str
    decideur: str
    etapes_par: dict[str, str]
    citation: str


class SortieCircuits(_Strict):
    circuits: list[CircuitIA]


class DroitIA(_Strict):
    acteur: str
    fiche: str
    action: Literal["see", "create", "edit", "delete", "transition"]
    autorise: bool
    portee: Literal["own", "all"]
    pendant_etats: list[str]
    transitions: dict[str, list[str]]
    citation: str


class SortieDroits(_Strict):
    droits: list[DroitIA]


Categorie = Literal[
    "paiement", "notification", "integration", "document", "planning", "calcul_statistiques",
    "fichiers_photos", "mobile_hors_ligne", "partage_fin", "cloisonnement", "automatisation",
    "messagerie", "autre",
]


class BesoinHorsStock(_Strict):
    besoin: str
    categorie: Categorie
    citation: str


class SortiePerimetre(_Strict):
    perimetre: Literal["dans", "hors"]
    raison: str
    hors_stock: list[BesoinHorsStock]


# ─── Consignes ─────────────────────────────────────────────────────────────────────────────
COMMUN = """Tu lis le brief d'un client qui veut un logiciel. Réponds UNIQUEMENT en JSON, dans la
forme demandée. Chaque « citation » est un passage COURT et continu du brief, recopié MOT POUR MOT
(sans le corriger, même s'il contient des fautes) ; pour assembler deux passages, sépare-les par « ... ».
N'invente rien : ce que le brief ne dit pas, on le demandera au client plus tard."""

Q_ACTEURS = COMMUN + """

QUESTION : qui SE CONNECTE à l'application ?
- L'auteur du brief (« je », « nous », l'entreprise, l'association) est un acteur « bootstrap » :
  le responsable de l'application. Nomme-le par son rôle (gérant, administrateur…).
- Le personnel interne ou des partenaires qui doivent avoir un accès : « invited » (un acteur les
  fait entrer ; par défaut le responsable), avec « invite_par ».
- « signup » (s'inscrit seul) UNIQUEMENT pour un public qui crée lui-même son compte (les clients
  d'un service en ligne). Jamais pour du personnel.
- Une personne dont le brief parle mais qui, d'après le brief, ne se connecte pas (les clients d'un
  pressing dont on gère les commandes, les élèves dont on tient les fiches) va dans
  « non_utilisateurs » : ce sera une fiche. En cas de doute : non_utilisateurs.
Exemple (autre domaine) : « Je tiens un pressing ; mes deux employés enregistrent les dépôts des
clients » → acteurs : gerant (bootstrap), employe (invited par gerant) ; non_utilisateurs : client.
Forme : {"acteurs": [{"id": "minuscules_sans_accent", "libelle": "…", "libelle_pluriel": "…",
"feminin": false, "devient": "bootstrap|invited|signup", "invite_par": "id ou null",
"citation": "…"}], "non_utilisateurs": [{"libelle": "…", "citation": "…"}]}"""

Q_FICHES = COMMUN + """

QUESTION : quelles FICHES l'application enregistre-t-elle ? On te donne les acteurs déjà trouvés.
NATURE de chaque fiche :
- "profile" : l'identité d'UN acteur qui se connecte, sur lui-même (une par personne). Propriétaire = cet acteur.
- "catalog" : une liste gérée par des responsables, sans propriétaire individuel : un référentiel
  (tarifs, salles) OU des fiches tenues par l'équipe (les clients d'un pressing, les élèves d'une
  école de musique). « gestionnaires » = les acteurs qui la tiennent.
- "collection" : des éléments qui APPARTIENNENT chacun à un acteur qui se connecte (les demandes
  d'un client inscrit, les notes de frais d'un employé). « proprietaire » = cet acteur ;
  « saisie_par » = un autre acteur s'il les saisit POUR le propriétaire.
- "child" : des lignes qui n'existent qu'à l'intérieur d'une autre fiche (les articles d'un dépôt
  au pressing) ; « parent » = cette fiche.
« publique » : true seulement si le brief dit qu'un visiteur SANS compte la voit. « publication » :
true seulement si le brief parle de brouillon/publié. « references » : les autres fiches qu'elle
désigne (un dépôt désigne un client). Utilise les id exacts des acteurs.
Exemple (autre domaine) : école de musique — Eleve (catalog, gestionnaires [directeur]),
Cours (catalog), Inscription (catalog, references [Eleve, Cours]).
Forme : {"fiches": [{"nom": "NomEnPascalCase", "libelle": "…", "libelle_pluriel": "…",
"feminin": false, "nature": "…", "proprietaire": "id ou null", "gestionnaires": ["id"],
"publique": false, "publication": false, "saisie_par": "id ou null", "parent": "Nom ou null",
"references": ["Nom"], "citation": "…"}]}"""

Q_CIRCUITS = COMMUN + """

QUESTION : quelles fiches passent par des ÉTATS ou des étapes (demande → acceptée, ouverte →
clôturée, actif/inactif, annulée…) ? Ne liste QUE celles dont le brief parle ainsi.
Pour chacune : les états (noms techniques en minuscules sans accent, libellés en français), les
flèches permises, l'état de départ, qui crée la fiche (« initiateur »), qui fait évoluer l'état
(« decideur »), et dans « etapes_par » les étapes faites par un AUTRE acteur que le décideur
(état de départ → acteur). Utilise les id exacts des acteurs et les noms exacts des fiches.
Exemple (autre domaine) : un dépôt au pressing : recu → nettoye → rendu ; l'employé crée et fait
tout → {"fiche": "Depot", "etat_initial": "recu", "transitions": {"recu": ["nettoye"],
"nettoye": ["rendu"], "rendu": []}, "libelles": {"recu": "reçu", "nettoye": "nettoyé",
"rendu": "rendu"}, "initiateur": "employe", "decideur": "employe", "etapes_par": {}, "citation": "…"}
Forme : {"circuits": [ … ]} (liste vide si aucune)."""

Q_DROITS = COMMUN + """

QUESTION : quels DROITS le brief énonce-t-il EXPLICITEMENT ? Une phrase du type « X peut
supprimer Y », « X voit toutes les Y », « X ne peut pas modifier Y », « Y est consultable par
tous ». Ne déduis rien : uniquement ce qui est écrit. Liste-les même s'ils te semblent évidents.
action : see (voir), create, edit (modifier), delete (supprimer), transition (faire évoluer l'état).
portee (pour see) : "all" (toutes) ou "own" (les siennes). acteur : un id d'acteur, ou "visitor"
pour une personne sans compte. « pendant_etats » : seulement si le brief limite à certains états.
Exemple (autre domaine) : « le directeur peut supprimer les fiches élèves » →
{"acteur": "directeur", "fiche": "Eleve", "action": "delete", "autorise": true, "portee": "all",
"pendant_etats": [], "transitions": {}, "citation": "…"}
Forme : {"droits": [ … ]} (liste vide si aucun)."""

Q_PERIMETRE = COMMUN + """

QUESTION : ce projet est-il dans notre périmètre, et qu'est-ce qui est HORS STOCK ?
Notre périmètre : les logiciels de GESTION de petites structures (cabinet, atelier, association,
PME…) : des fiches, des personnes qui se connectent avec des rôles, qui voient / créent / modifient /
suppriment, des demandes qui passent par des états. « hors » si le CŒUR du projet est autre chose :
place de marché avec paiements et commissions, réseau social ou messagerie, application mobile
native, objet connecté, jeu, site vitrine…
Notre STOCK (ce que nous savons faire aujourd'hui) : fiches ; acteurs et rôles ; voir (rien / les
siennes / toutes / publiées / au travers d'une autre fiche) ; créer, modifier, supprimer ; fiches
enfants ; circuits d'états avec qui fait chaque étape ; catalogue public.
Tout le reste est HORS STOCK, par exemple : paiement, envoi d'e-mails/SMS/notifications, rappels,
liens avec un autre logiciel, documents PDF générés, vue planning/calendrier, calculs/statistiques/
tableaux de bord, exports, photos et pièces jointes, hors ligne/mobile natif, partage fiche par
fiche, cloisonnement par agence ou par équipe (« ses » clients, « son » agence), automatisations,
messagerie. Liste CHAQUE besoin hors stock du brief, avec sa citation.
Forme : {"perimetre": "dans|hors", "raison": "…", "hors_stock": [{"besoin": "…",
"categorie": "paiement|notification|integration|document|planning|calcul_statistiques|
fichiers_photos|mobile_hors_ligne|partage_fin|cloisonnement|automatisation|messagerie|autre",
"citation": "…"}]}"""


# ─── Contrôles (règle 3 : refuser, jamais deviner) ─────────────────────────────────────────
ID = re.compile(r"^[a-z][a-z0-9_]*$")
NAME = re.compile(r"^[A-Z][A-Za-z0-9]*$")


def _fragments(citation: str) -> list[str]:
    """La forme ne compte pas, le contenu oui : guillemets d'encadrement et ponctuation finale
    ignorés ; une citation « A … B » est vérifiée morceau par morceau (chaque morceau mot pour mot)."""
    parts = citation.replace("…", "...").split("...")
    return [p.strip().strip("\"'«»“”").strip().rstrip(".,;:").strip() for p in parts if p.strip(" \"'«»“”.,;:")]


def _cites(brief: str, items: list[tuple[str, str]]) -> list[str]:
    nb = _norm(brief)
    return [f"{who} : citation introuvable mot pour mot dans le brief — « {c} » (recopie un passage exact, "
            "sans le reformuler ni le corriger ; pour assembler deux passages, sépare-les par « ... »)"
            for who, c in items
            if not _fragments(c) or any(_norm(f) not in nb for f in _fragments(c))]


def check_acteurs(o: SortieActeurs, brief: str, ctx: dict) -> list[str]:
    errs = []
    ids = [a.id for a in o.acteurs]
    if not o.acteurs:
        errs.append("aucun acteur")
    if len(set(ids)) != len(ids):
        errs.append("identifiants d'acteurs en double")
    if "visitor" in ids:
        errs.append("« visitor » est réservé (le visiteur existe toujours)")
    if not any(a.devient == "bootstrap" for a in o.acteurs):
        errs.append("il faut un acteur « bootstrap » (le responsable de l'application)")
    for a in o.acteurs:
        if not ID.match(a.id):
            errs.append(f"id « {a.id} » : minuscules, chiffres et _ seulement")
        if a.devient == "invited" and a.invite_par not in ids:
            errs.append(f"{a.id} : « invite_par » doit être un id d'acteur")
        if a.devient != "invited" and a.invite_par:
            errs.append(f"{a.id} : « invite_par » seulement si devient = invited")
    errs += _cites(brief, [(f"acteur {a.id}", a.citation) for a in o.acteurs]
                   + [(f"non-utilisateur {n.libelle}", n.citation) for n in o.non_utilisateurs])
    return errs


def check_fiches(o: SortieFiches, brief: str, ctx: dict) -> list[str]:
    errs, actors = [], ctx["actor_ids"]
    names = [f.nom for f in o.fiches]
    if len(set(names)) != len(names):
        errs.append("noms de fiches en double")
    for f in o.fiches:
        w = f"fiche {f.nom}"
        if not NAME.match(f.nom):
            errs.append(f"{w} : nom en PascalCase sans accent")
        if f.nature in ("profile", "collection") and f.proprietaire not in actors:
            errs.append(f"{w} ({f.nature}) : « proprietaire » doit être un id d'acteur parmi {actors}")
        if f.nature in ("catalog", "child") and f.proprietaire:
            errs.append(f"{w} ({f.nature}) : pas de « proprietaire » (mettre null)")
        if f.nature != "catalog" and f.gestionnaires:
            errs.append(f"{w} : « gestionnaires » seulement pour un catalog")
        errs += [f"{w} : gestionnaire « {g} » inconnu" for g in f.gestionnaires if g not in actors]
        if f.saisie_par and (f.nature != "collection" or f.saisie_par not in actors):
            errs.append(f"{w} : « saisie_par » seulement pour une collection, et un id d'acteur")
        if f.nature == "child" and f.parent not in names:
            errs.append(f"{w} (child) : « parent » doit être une fiche de la liste")
        if f.nature != "child" and f.parent:
            errs.append(f"{w} : « parent » seulement pour un child")
        errs += [f"{w} : référence « {r} » inconnue — les références sont des NOMS DE FICHES parmi {names} "
                 "(pas des acteurs)" for r in f.references if r not in names]
    errs += _cites(brief, [(f"fiche {f.nom}", f.citation) for f in o.fiches])
    return errs


def check_circuits(o: SortieCircuits, brief: str, ctx: dict) -> list[str]:
    errs, actors, names = [], ctx["actor_ids"], ctx["fiche_names"]
    for c in o.circuits:
        w = f"circuit {c.fiche}"
        if c.fiche not in names:
            errs.append(f"{w} : fiche inconnue (parmi {names})")
        states = set(c.transitions) | {s for t in c.transitions.values() for s in t}
        if c.etat_initial not in states:
            errs.append(f"{w} : état initial absent des transitions")
        errs += [f"{w} : état « {s} » en minuscules sans accent" for s in states if not ID.match(s)]
        for role, who in [("initiateur", c.initiateur), ("decideur", c.decideur), *c.etapes_par.items()]:
            if who not in actors:
                errs.append(f"{w} : {role} « {who} » n'est pas un id d'acteur parmi {actors}")
        errs += [f"{w} : étape « {s} » sans flèche sortante" for s in c.etapes_par if not c.transitions.get(s)]
    errs += _cites(brief, [(f"circuit {c.fiche}", c.citation) for c in o.circuits])
    return errs


def check_droits(o: SortieDroits, brief: str, ctx: dict) -> list[str]:
    errs, actors, names = [], ctx["actor_ids"] + ["visitor"], ctx["fiche_names"]
    for d in o.droits:
        w = f"droit {d.acteur}/{d.fiche}/{d.action}"
        if d.acteur not in actors:
            errs.append(f"{w} : acteur inconnu (parmi {actors})")
        if d.fiche not in names:
            errs.append(f"{w} : fiche inconnue (parmi {names})")
    errs += _cites(brief, [(f"droit {d.acteur}/{d.fiche}/{d.action}", d.citation) for d in o.droits])
    return errs


def check_perimetre(o: SortiePerimetre, brief: str, ctx: dict) -> list[str]:
    return _cites(brief, [(f"hors stock « {b.besoin} »", b.citation) for b in o.hors_stock])


# ─── Appel d'un agent, avec renvoi des erreurs ─────────────────────────────────────────────
# ─── Fournisseurs d'IA ─────────────────────────────────────────────────────────────────────
# Gemini (Google AI Studio) s'appelle avec le même code qu'OpenAI, via la porte compatible de
# Google : seuls la clé et l'adresse changent. Le fournisseur se déduit du nom du modèle.
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"


def make_client(model: str):
    import os
    from openai import OpenAI
    if model.startswith("gemini"):
        key = os.getenv("GEMINI_API_KEY")
        if not key:
            raise SystemExit("GEMINI_API_KEY absente de factory-sprint0/.env")
        return OpenAI(api_key=key, base_url=GEMINI_URL)
    return OpenAI()


def _create(client, **kwargs):
    """Appel avec patience : l'offre gratuite de Gemini limite le nombre d'appels par minute.
    Un compte sans crédit, lui, s'arrête tout de suite (inutile d'attendre)."""
    from openai import APIConnectionError, APITimeoutError, InternalServerError, RateLimitError
    for wait in (15, 30, 60, 90, 120):
        try:
            return client.chat.completions.create(**kwargs)
        except (InternalServerError, APIConnectionError, APITimeoutError) as e:
            # engorgement passager du fournisseur (« high demand ») : on patiente
            print(f"   (fournisseur indisponible : {str(e)[:80]} — nouvel essai dans {wait} s)", flush=True)
            time.sleep(wait)
            continue
        except RateLimitError as e:
            if "insufficient_quota" in str(e) or "credit_balance" in str(e):
                raise SystemExit(f"Plus de crédit chez ce fournisseur : {e}")
            if "PerDay" in str(e):
                raise SystemExit("Quota JOURNALIER épuisé pour ce modèle (offre gratuite) : inutile d'attendre.")
            if "limit: 0" in str(e):
                raise SystemExit("Ce modèle n'est pas inclus dans l'offre gratuite (limite à 0) : "
                                 "inutile d'attendre, choisir un autre modèle ou passer à l'offre payante.")
            print(f"   (limite de débit atteinte, nouvel essai dans {wait} s)", flush=True)
            time.sleep(wait)
    return client.chat.completions.create(**kwargs)


def ask(client, model: str, system: str, payload: dict, shape, check, brief: str, ctx: dict, log: list):
    messages = [{"role": "system", "content": system},
                {"role": "user", "content": json.dumps(payload, ensure_ascii=False)}]
    extra = {} if model.startswith(("gpt-5", "o", "gemini")) else {"temperature": 0}
    errors: list[str] = []
    for attempt in range(1, 4):
        resp = _create(client, model=model, messages=messages,
                       response_format={"type": "json_object"}, **extra)
        text = resp.choices[0].message.content or ""
        try:
            out = shape.model_validate_json(text)
            errors = check(out, brief, ctx)
        except ValidationError as e:
            out, errors = None, [f"{'.'.join(map(str, x['loc']))} : {x['msg']}" for x in e.errors()][:15]
        log.append({"agent": shape.__name__, "essai": attempt, "erreurs": errors})
        if out is not None and not errors:
            return out
        messages += [{"role": "assistant", "content": text},
                     {"role": "user", "content": "Réponse refusée :\n- " + "\n- ".join(errors)
                      + "\nCorrige et renvoie le JSON complet."}]
    return None


# ─── Assemblage : la déclaration que lira le calculateur ───────────────────────────────────
def _cite(c: str) -> str:
    """Pour le calculateur (qui vérifie la citation d'un seul tenant) : le plus long passage exact."""
    return max(_fragments(c), key=len)


def assemble(acteurs: SortieActeurs, fiches: SortieFiches, circuits: SortieCircuits, droits: SortieDroits):
    """Les circuits posés sur une fiche qui n'est pas une collection sont hors du vocabulaire D1 :
    on les garde dans la sortie (pour juger la compréhension) mais pas dans la matrice."""
    for group in (acteurs.acteurs, fiches.fiches, circuits.circuits, droits.droits):
        for item in group:
            item.citation = _cite(item.citation)
    by_fiche = {c.fiche: c for c in circuits.circuits}
    natures = {f.nom: f.nature for f in fiches.fiches}
    hors_vocabulaire = [c.fiche for c in circuits.circuits if natures.get(c.fiche) != "collection"]
    data = {
        "actors": [{"id": a.id, "label": a.libelle, "label_plural": a.libelle_pluriel,
                    "feminine": a.feminin, "becomes": a.devient, "invited_by": a.invite_par,
                    "citation": a.citation} for a in acteurs.acteurs],
        "entities": [],
        "exceptions": [{"actor": d.acteur, "entity": d.fiche, "action": d.action, "allow": d.autorise,
                        "scope": d.portee, "while_states": d.pendant_etats, "transitions": d.transitions,
                        "citation": d.citation} for d in droits.droits],
    }
    for f in fiches.fiches:
        e = {"name": f.nom, "label": f.libelle, "label_plural": f.libelle_pluriel, "feminine": f.feminin,
             "nature": f.nature, "owner": f.proprietaire,
             "manager": f.gestionnaires or None, "public": f.publique, "publication": f.publication,
             "entered_by": f.saisie_par, "parent": f.parent, "references": f.references,
             "citation": f.citation}
        c = by_fiche.get(f.nom)
        if c and f.nature == "collection":
            e["process"] = {"initial": c.etat_initial, "transitions": c.transitions,
                            "initiator": c.initiateur, "decider": c.decideur,
                            "steps_by": c.etapes_par, "labels": c.libelles, "citation": c.citation}
        data["entities"].append(e)
    return data, hors_vocabulaire


def run_brief(client, model: str, name: str, brief: str) -> dict:
    log: list = []
    t0 = time.time()
    perimetre = ask(client, model, Q_PERIMETRE, {"brief": brief}, SortiePerimetre, check_perimetre, brief, {}, log)
    acteurs = ask(client, model, Q_ACTEURS, {"brief": brief}, SortieActeurs, check_acteurs, brief, {}, log)
    result = {"projet": name, "modele": model, "perimetre": perimetre and perimetre.model_dump(),
              "acteurs": acteurs and acteurs.model_dump(), "journal": log}
    if acteurs is None:
        result["echec"] = "acteurs refusés après 3 essais"
        return result
    ctx = {"actor_ids": [a.id for a in acteurs.acteurs]}
    base = {"brief": brief, "acteurs": [{"id": a.id, "libelle": a.libelle} for a in acteurs.acteurs],
            "non_utilisateurs": [n.libelle for n in acteurs.non_utilisateurs]}
    fiches = ask(client, model, Q_FICHES, base, SortieFiches, check_fiches, brief, ctx, log)
    result["fiches"] = fiches and fiches.model_dump()
    if fiches is None:
        result["echec"] = "fiches refusées après 3 essais"
        return result
    ctx["fiche_names"] = [f.nom for f in fiches.fiches]
    base2 = {**base, "fiches": [{"nom": f.nom, "libelle": f.libelle, "nature": f.nature} for f in fiches.fiches]}
    circuits = ask(client, model, Q_CIRCUITS, base2, SortieCircuits, check_circuits, brief, ctx, log)
    droits = ask(client, model, Q_DROITS, base2, SortieDroits, check_droits, brief, ctx, log)
    result["circuits"] = circuits and circuits.model_dump()
    result["droits"] = droits and droits.model_dump()
    if circuits is None or droits is None:
        result["echec"] = "circuits ou droits refusés après 3 essais"
        return result
    data, hors_vocab = assemble(acteurs, fiches, circuits, droits)
    result["circuits_hors_vocabulaire_D1"] = hors_vocab
    try:
        decl = AccessDeclaration(**data)
    except ValidationError as e:
        result["echec"] = "assemblage refusé : " + "; ".join(x["msg"] for x in e.errors())
        return result
    m = compute_matrix(decl, brief=brief)
    result["declaration"] = data
    result["matrice_erreurs"] = m.errors
    result["matrice_alertes"] = [i.message for i in m.issues if i.level != "error"]
    if not m.errors:
        result["miroir"] = explain(m, decl)
        result["questions"] = questions(m, decl)
    result["secondes"] = round(time.time() - t0, 1)
    return result


def main() -> int:
    from dotenv import load_dotenv
    load_dotenv(FACTORY / ".env")
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="gpt-5.4-mini")
    parser.add_argument("--only", action="append", default=[])
    parser.add_argument("--modeles", action="store_true", help="lister les modèles du fournisseur et quitter")
    args = parser.parse_args()
    client = make_client(args.model)
    if args.modeles:
        for m in sorted(x.id for x in client.models.list().data):
            print(m)
        return 0
    briefs = json.loads(BRIEFS.read_text(encoding="utf-8"))
    out_dir = OUT / args.model
    out_dir.mkdir(parents=True, exist_ok=True)
    for b in briefs:
        name = b["project_name"]
        if args.only and name not in args.only:
            continue
        r = run_brief(client, args.model, name, b["brief"]["description"])
        (out_dir / f"{name}.json").write_text(json.dumps(r, ensure_ascii=False, indent=2), encoding="utf-8")
        refus = sum(1 for x in r["journal"] if x["erreurs"])
        print(f"{name:<24} périmètre={(r.get('perimetre') or {}).get('perimetre')}  "
              f"acteurs={len((r.get('acteurs') or {}).get('acteurs', []))}  "
              f"fiches={len((r.get('fiches') or {}).get('fiches', []))}  réponses refusées={refus}  "
              f"{'ÉCHEC : ' + r['echec'] if r.get('echec') else 'matrice ' + ('OK' if not r.get('matrice_erreurs') else 'ERREURS')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
