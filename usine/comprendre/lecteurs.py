"""Les LECTEURS IA : chacun lit le brief et répond à UNE question, en JSON de forme fixe ; sa réponse
est contrôlée par programme (contrôle_* : forme, identifiants connus, citations mot pour mot) et
refusée avec l'erreur précise sinon. Ils n'ont aucun outil et n'agissent sur rien (USINE.md §3.1).

  1. Acteurs              qui se connecte, et comment on le devient            ┐ version v3 de l'étude 05
  2. Fiches               ce qu'on enregistre, sa nature, à qui c'est          │ (poc/comprehension/
  3. Circuits             quelles fiches passent par des états, qui fait quoi  │  comprendre.py), recopiés
  4. Droits explicites    ce que le brief DIT (supprimer, tout voir…)          │  SANS changement : mesurés
  5. Périmètre            dans ou hors de nos logiciels ; ce qui est hors stock ┘  9/10 avec gpt-5.5
  6. Champs (N1.1)        les informations de chaque fiche, leur type
  7. Libellés (N1.1)      le titre de l'app, les verbes des boutons

Les exemples des consignes viennent d'autres domaines que les briefs testés (un pressing, une école
de musique) : on mesure la compréhension, pas la reconnaissance d'exemples.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Literal

from pydantic import BaseModel, ConfigDict

from ..matrice import _norm


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


# ─── Formes attendues (1-5 : v3 de l'étude 05) ──────────────────────────────────────────────
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
    nature: Literal["profile", "catalog", "registry", "collection", "child"]
    proprietaire: str | None
    gestionnaires: list[str]
    publique: bool
    publication: bool
    saisie_par: str | None
    parent: str | None
    references: list[str]
    citation: str


class Correspondance(_Strict):
    non_utilisateur: str
    fiche: str | None
    raison: str


class SortieFiches(_Strict):
    fiches: list[FicheIA]
    correspondances: list[Correspondance]


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


# ─── Formes attendues (6-7 : N1.1) ──────────────────────────────────────────────────────────
TypeChampIA = Literal["texte", "texte_long", "nombre", "montant", "date", "date_heure", "oui_non",
                      "email", "telephone", "url", "choix"]


class ChampIA(_Strict):
    nom: str
    libelle: str
    type: TypeChampIA
    obligatoire: bool
    valeurs: list[str]
    origine: Literal["brief", "necessaire"]
    citation: str


class PropositionIA(_Strict):
    libelle: str
    type: TypeChampIA
    raison: str


class ChampsFiche(_Strict):
    fiche: str
    champs: list[ChampIA]
    propositions: list[PropositionIA]


class SortieChamps(_Strict):
    fiches: list[ChampsFiche]


class LibellesFiche(_Strict):
    fiche: str
    verbe_creation: str | None
    boutons: dict[str, str]


class SortieLibelles(_Strict):
    titre: str
    fiches: list[LibellesFiche]


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
- "catalog" : un RÉFÉRENTIEL que tous les connectés consultent (tarifs, salles, types de prestation).
  « gestionnaires » = qui le modifie ; liste vide seulement si c'est une liste fixe qui ne change jamais.
- "registry" : des fiches TENUES PAR L'ÉQUIPE, sans propriétaire individuel, que seuls ceux qui les
  tiennent voient (les clients d'un pressing, les élèves d'une école de musique, des dossiers, des
  chantiers, des factures). « gestionnaires » = les acteurs qui les tiennent (au moins un).
  En cas de doute entre catalog et registry : registry (le plus prudent).
PRUDENCE (v3) : si le brief LIMITE l'accès à des fiches (« les professionnels concernés »,
« confidentialité », « seulement ses… », « pas un accès total »), ne nomme PAS ces acteurs
gestionnaires du registre pour leur donner accès à tout : laisse-le à celui qui le tient ; ce
partage fin n'est pas dans notre stock (il sera signalé hors stock).
- "collection" : des éléments qui APPARTIENNENT chacun à un acteur qui se connecte (les demandes
  d'un client inscrit, les notes de frais d'un employé). « proprietaire » = cet acteur ;
  « saisie_par » = un autre acteur s'il les saisit POUR le propriétaire.
- "child" : des lignes qui n'existent qu'à l'intérieur d'une autre fiche (les articles d'un dépôt
  au pressing) ; « parent » = cette fiche.
« publique » : true seulement si le brief dit qu'un visiteur SANS compte la voit. « publication » :
true seulement si le brief parle de brouillon/publié. « references » : les autres fiches qu'elle
désigne (un dépôt désigne un client). Utilise les id exacts des acteurs.
Relie chaque fiche aux fiches qu'elle désigne (une inscription désigne un élève ET un cours).
CORRESPONDANCES : pour CHAQUE non-utilisateur qu'on te donne, dis quelle fiche le représente
(ou null, avec la raison, si ce n'est pas une chose à enregistrer).
Exemple (autre domaine) : école de musique — Eleve (registry, gestionnaires [directeur]),
Instrument (catalog, gestionnaires [directeur]), Inscription (registry, gestionnaires [directeur],
references [Eleve, Instrument]) ; correspondances : élève → Eleve.
Forme : {"fiches": [{"nom": "NomEnPascalCase", "libelle": "…", "libelle_pluriel": "…",
"feminin": false, "nature": "…", "proprietaire": "id ou null", "gestionnaires": ["id"],
"publique": false, "publication": false, "saisie_par": "id ou null", "parent": "Nom ou null",
"references": ["Nom"], "citation": "…"}],
"correspondances": [{"non_utilisateur": "libellé exact donné", "fiche": "Nom ou null", "raison": "…"}]}"""

Q_CIRCUITS = COMMUN + """

QUESTION : quelles fiches passent par des ÉTATS ou des étapes (demande → acceptée, ouverte →
clôturée, actif/inactif, annulée…) ? Ne liste QUE celles dont le brief parle ainsi, avec au moins
deux états et une flèche ; n'invente pas d'états que le brief ne suggère pas. Sur un « registry »,
l'initiateur est l'un de ceux qui tiennent le registre.
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
MÉTHODE : passe en revue CHAQUE verbe d'action du brief (créer, saisir, modifier, supprimer,
consulter, afficher, partager, valider, annuler…) et note qui le fait, sur quelle fiche.
ATTENTION : « annuler » n'est pas « supprimer » (une annulation est un état, la fiche reste) ;
une phrase générale (« tous les utilisateurs n'ont pas un accès total ») n'est PAS une interdiction
totale : elle dit seulement que certains ne voient pas tout — n'en tire aucun droit.
PRUDENCE (v3) : ne donne pas « voir toutes » à un acteur dont le brief LIMITE l'accès (« les
professionnels concernés », « ses propres… ») : ce partage fin n'est pas dans notre stock.
Le « visitor » (sans compte) ne reçoit un droit que si le brief parle d'un accès public, sans
compte (« consultable par tous », « affichage public ») — jamais pour « les utilisateurs ».
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
IMPORTANT : « hors stock » n'est pas « hors périmètre ». Un logiciel de gestion qui demande aussi
des choses hors stock (planning, factures, paiement d'appoint…) reste DANS le périmètre : on
listera ces besoins comme hors stock.
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

Q_CHAMPS = COMMUN + """

QUESTION : quelles INFORMATIONS (champs) chaque fiche enregistre-t-elle ? On te donne les fiches
déjà trouvées, les fiches qu'elles désignent (leurs liens) et leurs états (circuits).
MÉTHODE : parcours le brief phrase par phrase et relève TOUTE information qu'il rattache à une fiche,
y compris dans une énumération (« des fiches X comprenant A, B et C », « X (A, B, C) », « X avec A »)
et dans les tournures « un A par X » (une information de X) ou « fixer / planifier le A de X ».
Pour chaque fiche :
- « origine » = "brief" : le brief CITE cette information pour cette fiche (« chaque ouvrage a un
  titre ») ; « citation » obligatoire, mot pour mot.
- « origine » = "necessaire" : SEULEMENT si le brief ne cite aucune information pour cette fiche :
  UN champ texte pour la reconnaître dans une liste (son nom, son intitulé) ; citation vide "".
- Tout autre champ utile mais NON cité va dans « propositions » (on demandera au client) — jamais
  dans « champs ».
NE LISTE PAS — l'application les gère déjà :
- les liens vers d'autres fiches (un emprunt désigne un ouvrage → pas de champ « ouvrage ») ;
- l'état ou le statut d'une fiche qui a un circuit ;
- le propriétaire, et la date de création ou de demande (enregistrées automatiquement : « une
  demande a une date de demande » → pas de champ) ;
- les listes de fiches liées (« l'historique des commandes d'un client ») : c'est un lien, pas un champ.
TYPES : texte (court), texte_long (plusieurs lignes), nombre (entier : quantité, année), montant
(somme d'argent), date, date_heure, oui_non, email, telephone, url, choix (une valeur parmi une liste
FIXE que le brief énumère : « valeurs » = ces libellés, dans l'ordre du brief ; sinon « valeurs » = []).
« choix » seulement si le brief énumère les valeurs possibles ; sinon texte.
« obligatoire » : true, sauf si le brief le dit facultatif ou si l'information n'existe pas toujours
(une date de retour avant le retour).
« nom » : identifiant camelCase sans accent (« anneePublication ») ; « libelle » : en français, pour
l'écran (« Année de publication »).
Exemple (autre domaine) : « École de musique : chaque élève a un nom, un prénom, une date de
naissance et un niveau (débutant, intermédiaire, avancé) ; une inscription désigne un élève et un
instrument, avec son tarif annuel. » → Eleve : nom, prenom (texte), dateNaissance (date), niveau
(choix : débutant, intermédiaire, avancé) ; Inscription : tarifAnnuel (montant) — pas de champ
« élève » ni « instrument » : ce sont des liens ; Instrument (le brief n'en dit rien) : un champ
"necessaire" nom (texte), et en proposition « marque ».
Forme : {"fiches": [{"fiche": "NomExact", "champs": [{"nom": "…", "libelle": "…", "type": "…",
"obligatoire": true, "valeurs": [], "origine": "brief|necessaire", "citation": "…"}],
"propositions": [{"libelle": "…", "type": "…", "raison": "…"}]}]}
Une entrée pour CHAQUE fiche reçue, même sans champ."""

Q_LIBELLES = """Tu prépares les LIBELLÉS de l'écran d'une application de gestion, en français. Réponds
UNIQUEMENT en JSON. On te donne le brief, les fiches, leurs liens et leurs circuits d'états.
1. « titre » : le nom de l'application, court (2 à 4 mots) : « Médiathèque », « Gestion du club ».
2. Pour chaque fiche qui a un circuit : « boutons » = pour CHAQUE état d'arrivée d'une flèche, le
   libellé du bouton qui y fait passer, à l'infinitif (« accepte » → « Accepter », « rendu » →
   « Marquer rendu », « annule » → « Annuler »).
3. Pour chaque fiche qui désigne une autre fiche : « verbe_creation » = le libellé du bouton qui la
   crée d'un clic depuis la fiche désignée (une réservation créée depuis une salle → « Réserver » ;
   une inscription depuis un cours → « S'inscrire ») ; null si ça n'a pas de sens.
Forme : {"titre": "…", "fiches": [{"fiche": "NomExact", "verbe_creation": "… ou null",
"boutons": {"etat": "Libellé"}}]} — une entrée pour chaque fiche qui a un circuit ou des liens."""


# ─── Contrôles (règle 3 : refuser, jamais deviner) ─────────────────────────────────────────
ID = re.compile(r"^[a-z][a-z0-9_]*$")
NAME = re.compile(r"^[A-Z][A-Za-z0-9]*$")
CAMEL = re.compile(r"^[a-z][A-Za-z0-9]*$")
RESERVES = {"id", "ownerId", "userId", "status", "createdAt", "published"}


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


def sans_accents(s: str) -> str:
    return "".join(ch for ch in unicodedata.normalize("NFD", s.lower()) if unicodedata.category(ch) != "Mn")


def controle_acteurs(o: SortieActeurs, ctx: dict) -> list[str]:
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
    errs += _cites(ctx["brief"], [(f"acteur {a.id}", a.citation) for a in o.acteurs]
                   + [(f"non-utilisateur {n.libelle}", n.citation) for n in o.non_utilisateurs])
    return errs


def controle_fiches(o: SortieFiches, ctx: dict) -> list[str]:
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
        if f.nature in ("catalog", "registry", "child") and f.proprietaire:
            errs.append(f"{w} ({f.nature}) : pas de « proprietaire » (mettre null)")
        if f.nature not in ("catalog", "registry") and f.gestionnaires:
            errs.append(f"{w} : « gestionnaires » seulement pour un catalog ou un registry")
        if f.nature == "registry" and not f.gestionnaires:
            errs.append(f"{w} (registry) : qui tient ces fiches ? « gestionnaires » doit contenir au moins un acteur")
        errs += [f"{w} : gestionnaire « {g} » inconnu" for g in f.gestionnaires if g not in actors]
        if f.saisie_par and (f.nature != "collection" or f.saisie_par not in actors):
            errs.append(f"{w} : « saisie_par » seulement pour une collection, et un id d'acteur")
        if f.nature == "child" and f.parent not in names:
            errs.append(f"{w} (child) : « parent » doit être une fiche de la liste")
        if f.nature != "child" and f.parent:
            errs.append(f"{w} : « parent » seulement pour un child")
        errs += [f"{w} : référence « {r} » inconnue — les références sont des NOMS DE FICHES parmi {names} "
                 "(pas des acteurs)" for r in f.references if r not in names]
    # contrôle croisé avec le lecteur 1 : chaque non-utilisateur devient une fiche (ou est écarté avec raison)
    given = [c.non_utilisateur for c in o.correspondances]
    for label in ctx.get("non_users", []):
        if label not in given:
            errs.append(f"correspondances : il manque « {label} » (dis quelle fiche le représente, ou null avec la raison)")
    for c in o.correspondances:
        if c.fiche is not None and c.fiche not in names:
            errs.append(f"correspondance « {c.non_utilisateur} » → « {c.fiche} » : cette fiche n'existe pas dans ta liste")
        if c.fiche is None and not c.raison.strip():
            errs.append(f"correspondance « {c.non_utilisateur} » : null sans raison")
    errs += _cites(ctx["brief"], [(f"fiche {f.nom}", f.citation) for f in o.fiches])
    return errs


def controle_circuits(o: SortieCircuits, ctx: dict) -> list[str]:
    errs, actors, names = [], ctx["actor_ids"], ctx["fiche_names"]
    for c in o.circuits:
        w = f"circuit {c.fiche}"
        if c.fiche not in names:
            errs.append(f"{w} : fiche inconnue (parmi {names})")
        states = set(c.transitions) | {s for t in c.transitions.values() for s in t}
        if c.etat_initial not in states:
            errs.append(f"{w} : état initial absent des transitions")
        if len(states) < 2 or not any(c.transitions.values()):
            errs.append(f"{w} : un circuit a au moins deux états et une flèche (sinon, ne le liste pas)")
        managers = ctx.get("registry_managers", {}).get(c.fiche)
        if managers is not None and c.initiateur not in managers:
            errs.append(f"{w} : sur un registre, l'initiateur est l'un de ceux qui le tiennent : {managers}")
        errs += [f"{w} : état « {s} » en minuscules sans accent" for s in states if not ID.match(s)]
        for role, who in [("initiateur", c.initiateur), ("decideur", c.decideur), *c.etapes_par.items()]:
            if who not in actors:
                errs.append(f"{w} : {role} « {who} » n'est pas un id d'acteur parmi {actors}")
        errs += [f"{w} : étape « {s} » sans flèche sortante" for s in c.etapes_par if not c.transitions.get(s)]
    errs += _cites(ctx["brief"], [(f"circuit {c.fiche}", c.citation) for c in o.circuits])
    return errs


def controle_droits(o: SortieDroits, ctx: dict) -> list[str]:
    errs, actors, names = [], ctx["actor_ids"] + ["visitor"], ctx["fiche_names"]
    public = ctx.get("public_fiches", set())
    for d in o.droits:
        w = f"droit {d.acteur}/{d.fiche}/{d.action}"
        if d.acteur not in actors:
            errs.append(f"{w} : acteur inconnu (parmi {actors})")
        if d.fiche not in names:
            errs.append(f"{w} : fiche inconnue (parmi {names})")
        if d.acteur == "visitor" and d.autorise and d.fiche in names and d.fiche not in public:
            errs.append(f"{w} : le visiteur (personne SANS compte) ne peut recevoir un droit que sur une "
                        f"fiche publique ; « {d.fiche} » ne l'est pas d'après la liste des fiches. "
                        "Retire ce droit (« visitor » ne veut pas dire « les utilisateurs »).")
        # (N1.1, contrôle ajouté — trou trouvé au premier essai bout à bout) : les états cités sont les
        # CODES du circuit de la fiche, pas leurs libellés
        etats = ctx.get("etats", {}).get(d.fiche, set())
        cites = set(d.pendant_etats) | set(d.transitions) | {t for ts in d.transitions.values() for t in ts}
        if cites - etats:
            errs.append(f"{w} : état(s) {sorted(cites - etats)} inconnu(s) — utilise les CODES des états du circuit "
                        f"de {d.fiche} : {sorted(etats) or 'aucun (cette fiche n’a pas de circuit)'}")
    errs += _cites(ctx["brief"], [(f"droit {d.acteur}/{d.fiche}/{d.action}", d.citation) for d in o.droits])
    return errs


def controle_perimetre(o: SortiePerimetre, ctx: dict) -> list[str]:
    return _cites(ctx["brief"], [(f"hors stock « {b.besoin} »", b.citation) for b in o.hors_stock])


def controle_champs(o: SortieChamps, ctx: dict) -> list[str]:
    """ctx["fiches_info"] : nom → {"libelle", "liens": [(nom, libelle)], "circuit": bool}."""
    errs, info = [], ctx["fiches_info"]
    recues = [f.fiche for f in o.fiches]
    errs += [f"fiche « {n} » : il manque son entrée (même sans champ)" for n in info if n not in recues]
    errs += [f"fiche « {n} » inconnue (parmi {list(info)})" for n in recues if n not in info]
    errs += [f"fiche « {n} » : en double" for n in set(recues) if recues.count(n) > 1]
    for f in o.fiches:
        if f.fiche not in info:
            continue
        fi, vus, w = info[f.fiche], set(), f"fiche {f.fiche}"
        liens_interdits = {sans_accents(x) for nom, lib in fi["liens"] for x in (nom, lib, f"{nom[0].lower()}{nom[1:]}Id")}
        for c in f.champs:
            wc = f"{w}, champ {c.nom}"
            if not CAMEL.match(c.nom):
                errs.append(f"{wc} : « nom » en camelCase sans accent")
            if c.nom in RESERVES:
                errs.append(f"{wc} : nom réservé par l'application ({sorted(RESERVES)})")
            if c.nom in vus:
                errs.append(f"{wc} : en double")
            vus.add(c.nom)
            if sans_accents(c.nom) in liens_interdits or sans_accents(c.libelle) in liens_interdits:
                errs.append(f"{wc} : c'est un LIEN vers une autre fiche, déjà géré — retire ce champ")
            if fi["circuit"] and sans_accents(c.libelle) in {"etat", "statut", "status"}:
                errs.append(f"{wc} : l'état de cette fiche vient de son circuit, déjà géré — retire ce champ")
            if c.type == "choix" and (len(c.valeurs) < 2 or len(set(c.valeurs)) != len(c.valeurs)):
                errs.append(f"{wc} (choix) : au moins deux « valeurs », sans doublon")
            if c.type != "choix" and c.valeurs:
                errs.append(f"{wc} : « valeurs » seulement pour un choix (sinon [])")
            if c.origine == "necessaire" and c.type != "texte":
                errs.append(f"{wc} : un champ « necessaire » est de type texte")
        necessaires = [c for c in f.champs if c.origine == "necessaire"]
        if len(necessaires) > 1:
            errs.append(f"{w} : au plus UN champ « necessaire »")
        if not f.champs and not fi["liens"]:
            errs.append(f"{w} : sans aucun champ ni lien, cette fiche serait impossible à reconnaître dans une "
                        "liste — relève ce que le brief en dit, ou mets UN champ « necessaire » (son nom)")
        if necessaires and any(c.origine == "brief" for c in f.champs):
            errs.append(f"{w} : un champ « necessaire » seulement si le brief ne cite AUCUNE information "
                        "pour cette fiche (sinon, mets-le en proposition)")
    errs += _cites(ctx["brief"], [(f"{f.fiche}.{c.nom}", c.citation) for f in o.fiches for c in f.champs
                                  if c.origine == "brief"])
    return errs


def controle_libelles(o: SortieLibelles, ctx: dict) -> list[str]:
    """ctx["arrivees"] : fiche → états d'arrivée de son circuit (vide si pas de circuit)."""
    errs, arrivees = [], ctx["arrivees"]
    if not (2 <= len(o.titre.strip()) <= 40):
        errs.append("« titre » : 2 à 40 caractères")
    vus = {f.fiche: f for f in o.fiches}
    for f in o.fiches:
        if f.fiche not in arrivees:
            errs.append(f"fiche « {f.fiche} » inconnue (parmi {list(arrivees)})")
            continue
        en_trop = set(f.boutons) - set(arrivees[f.fiche])
        if en_trop:
            errs.append(f"fiche {f.fiche} : boutons pour des états qui ne sont pas des arrivées : {sorted(en_trop)}")
        errs += [f"fiche {f.fiche} : bouton « {e} » vide" for e, lib in f.boutons.items() if not lib.strip()]
    for n, etats in arrivees.items():
        manquants = [e for e in etats if e not in (vus[n].boutons if n in vus else {})]
        if manquants:
            errs.append(f"fiche {n} : il manque le bouton de chaque état d'arrivée {manquants}")
    return errs
