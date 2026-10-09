"""Le CATALOGUE DES BLOCS de l'usine (N1.1b).

Un BLOC = un mot de vocabulaire de l'usine (une nature de fiche, une action, un type de champ…) avec
ses 4 parties, livrées ensemble :
    construire  — comment il devient règles, base, données (traducteurs)
    écran       — comment il s'affiche et se saisit (squelette de l'app)
    juger       — comment on vérifie qu'il est respecté (testeur, tests d'écran)
    prouver     — dans quelle app il a été fabriqué ET où ses juges ont été prouvés par sabotage

Règle (USINE.md, 8 oct) : aucun mot de vocabulaire n'entre dans l'usine sans son bloc. Le CONTRÔLE
D'ARCHITECTURE (controle()) lit le vocabulaire DANS LE CODE (les formes strictes) et vérifie que chaque
mot a son bloc ici, et que chaque partie déclarée existe vraiment. Un mot pas encore construit doit
être REFUSÉ par l'usine (« refuse ») : jamais traité à moitié.
"""
from __future__ import annotations

import json
import typing
from dataclasses import dataclass, field
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]

# où vit chaque partie (fichier, texte qu'on doit y trouver)
S, MOD, E, D = "usine/traduire/schema.py", "usine/traduire/modele.py", "usine/traduire/ecran.py", "usine/traduire/depart.py"
DESC, MAT = "usine/description.py", "factory-sprint0/agents/capability_matrix.py"
V, P, F = "usine/modele-app/components/vues.tsx", "usine/modele-app/components/pieces.tsx", "usine/modele-app/lib/fiche.ts"
JB = "usine/modele-app/verification/blocs/"
NOY, CAS, E2E = "usine/modele-app/verification/noyau.mts", "usine/modele-app/verification/cas.mts", "usine/modele-app/e2e/roles.spec.ts"
EX_MED, EX_TYP = "usine/exemples/mediatheque.json", "usine/exemples/types.json"


@dataclass
class Partie:
    fichier: str
    repere: str            # texte qui doit se trouver dans le fichier (preuve que la partie existe)
    note: str = ""


@dataclass
class Bloc:
    id: str
    famille: str
    nom: str
    role: str                                   # en une phrase simple
    construire: Partie | None = None
    ecran: Partie | None = None
    juger: Partie | None = None
    prouver: Partie | None = None
    refuse: Partie | None = None                # pas encore construit : où l'usine le refuse
    notes: list[str] = field(default_factory=list)

    @property
    def parties(self) -> dict[str, Partie | None]:
        return {"construire": self.construire, "écran": self.ecran, "juger": self.juger, "prouver": self.prouver}

    @property
    def etat(self) -> str:
        if self.refuse:
            return "refusé"
        n = sum(1 for p in self.parties.values() if p)
        return "complet" if n == 4 else "partiel"


def _type(t: str, nom: str, base: str, role: str) -> Bloc:
    return Bloc(
        id=f"type:{t}", famille="Types de champs", nom=nom, role=role,
        construire=Partie(S, f'"{t}"' if t != "choix" else "def enum_choix", f"colonne {base} ; données de démo : {D}"),
        ecran=Partie(V, f"{t}:", "saisie (ENTREE) et affichage (valeur)"),
        juger=Partie(JB + "champs.mts", f"{base}:" if base != "enum" else "schema.enums", "une autre valeur valide, pour les fraudes"),
        prouver=Partie(EX_TYP, f'"type": "{t}"', "app d'essai des 11 types : fabriquée, jugée, prouvée"),
    )


BLOCS: list[Bloc] = [
    # ── Natures de fiches ──────────────────────────────────────────────────
    Bloc("nature:profile", "Natures de fiches", "Profil", "l'identité d'une personne qui se connecte, une par personne",
         Partie(S, "userId String @unique"), Partie(P, "export function MonProfil"), Partie(JB + "creer.mts", "spec.profile"),
         Partie(EX_MED, '"nature": "profile"', "médiathèque")),
    Bloc("nature:catalog", "Natures de fiches", "Catalogue", "une liste de référence que les connectés consultent",
         Partie(MAT, '"catalog"', "préréglages du calculateur"), Partie(P, "export function ListeDeFiches"),
         Partie(JB + "voir.mts", "voir : toutes"), Partie(EX_MED, '"nature": "catalog"', "médiathèque")),
    Bloc("nature:collection", "Natures de fiches", "Collection", "des fiches qui appartiennent chacune à une personne",
         Partie(S, "ownerId String"), Partie(P, "export function ListeDeFiches"), Partie(JB + "voir.mts", "les siennes seulement"),
         Partie(EX_MED, '"nature": "collection"', "médiathèque")),
    Bloc("nature:registry", "Natures de fiches", "Registre", "des fiches tenues par l'équipe, vues seulement de ceux qui les tiennent",
         Partie(MAT, '"registry"', "préréglages du calculateur"), Partie(P, "export function ListeDeFiches"),
         Partie(JB + "voir.mts", "voir : rien"), None,
         notes=["jamais fabriqué dans une app prouvée : la répétition générale (lot d'apprentissage, surtout des registres) le prouvera"]),
    Bloc("nature:child", "Natures de fiches", "Enfant", "des lignes qui n'existent qu'à l'intérieur d'une autre fiche",
         refuse=Partie(DESC, "les fiches enfants arrivent", "refusé par la description"), notes=["prévu en N1.3"]),
    # ── Actions ────────────────────────────────────────────────────────────
    Bloc("action:see", "Actions", "Voir", "qui voit quelles fiches (rien, les siennes, toutes, au travers d'une autre)",
         Partie(S, "@@allow('read'"), Partie(E, '"chemin": f"/f/{e.name}"', "menu par rôle et listes"),
         Partie(JB + "voir.mts", "export const voir"), Partie(EX_MED, '"references"', "médiathèque ; sabotages d'écran « perd voir », « menu »")),
    Bloc("action:create", "Actions", "Créer", "qui crée quelles fiches, pour lui seul, dans l'état de départ",
         Partie(S, "@@allow('create'"), Partie(P, "useCreate()", "bouton d'un clic ; formulaires de création : N1.5"),
         Partie(JB + "creer.mts", "export const creer"), Partie(EX_MED, '"initiator"', "médiathèque ; sabotage d'écran « reçoit créer »"),
         notes=["création d'un clic seulement si la fiche n'a ni champ obligatoire ni second lien (formulaires : N1.5)"]),
    Bloc("action:edit", "Actions", "Modifier", "qui modifie quelles fiches, et dans quels états",
         Partie(S, "@@allow('update'"), Partie(V, "export function Formulaire", "formulaire du profil ; les autres : N1.5"),
         Partie(JB + "modifier.mts", "export const modifier"), Partie(EX_MED, '"nature": "profile"', "médiathèque (profil)"),
         notes=["l'écran de modification n'existe que pour le profil (N1.5)"]),
    Bloc("action:delete", "Actions", "Supprimer", "jamais par défaut ; seulement si le brief le dit",
         Partie(S, "@@allow('delete'"), None, Partie(JB + "supprimer.mts", "export const supprimer"), None,
         notes=["pas de bouton « supprimer » (N1.5)", "seul le REFUS est prouvé : aucune app prouvée n'accorde la suppression"]),
    Bloc("action:transition", "Actions", "Étapes d'un circuit", "les états d'une fiche et qui la fait passer de l'un à l'autre",
         Partie(S, "une règle par flèche"), Partie(P, "n.etat.boutons", "boutons de décision"),
         Partie(JB + "circuit.mts", "export const circuit"), Partie(EX_MED, '"transitions"', "médiathèque ; sabotages d'écran « perd / gagne une étape »")),
    # ── Portées ────────────────────────────────────────────────────────────
    Bloc("portee:via", "Portées de lecture", "Au travers d'une autre fiche", "voir une fiche seulement quand une fiche qu'on voit la désigne",
         Partie(S, "?[true]"), Partie(V, "function valeurLien"), Partie(JB + "voir.mts", "seulement au travers"),
         Partie(EX_MED, '"references": ["Book", "Member"]', "médiathèque : le bibliothécaire voit les profils au travers des emprunts")),
    Bloc("portee:published", "Portées de lecture", "Publiées seulement", "brouillon / publié : les autres ne voient que le publié",
         refuse=Partie(DESC, "la publication (brouillon / publié) arrive", "refusé par la description"), notes=["prévu en N1.3"]),
    # ── Acteurs ────────────────────────────────────────────────────────────
    Bloc("acteur:roles", "Acteurs", "Rôles", "chaque personne connectée a un rôle ; les règles listent les rôles, jamais « tout connecté »",
         Partie(S, "def _role"), Partie("usine/modele-app/app/connexion/[qui]/route.ts", "export async function POST", "connexion simulée ; Clerk et invitations : N1.5"),
         Partie(NOY, "export const users"), Partie(EX_MED, '"becomes"', "médiathèque")),
    Bloc("acteur:visitor", "Acteurs", "Visiteur", "quelqu'un sans compte : ne voit que ce qui est public",
         Partie(S, "VISITOR"), Partie(E2E, "'visitor'"), Partie(NOY, "'visitor'"), Partie(EX_MED, '"public": true', "médiathèque")),
    Bloc("acteur:intrus", "Acteurs", "Intrus", "connecté mais sans rôle déclaré : exactement les droits du visiteur",
         Partie(S, "jamais « tout connecté »"), Partie("usine/modele-app/lib/session.ts", "ROLES_CONNECTES.includes"),
         Partie(NOY, "INTRUDER"), Partie(EX_MED, '"becomes"', "médiathèque")),
    # ── Liens ──────────────────────────────────────────────────────────────
    Bloc("lien:reference", "Liens", "Lien vers une fiche", "une fiche en désigne une autre (un emprunt désigne un ouvrage)",
         Partie(MOD, "class Lien"), Partie(V, "function valeurLien"), Partie(JB + "creer.mts", "foreignKeys"),
         Partie(EX_MED, '"references"', "médiathèque")),
    Bloc("lien:multiple", "Liens", "Liens multiples", "une fiche en désigne plusieurs du même genre (un article et ses étiquettes)",
         refuse=Partie(DESC, "les « liens multiples » viendront", "absent du vocabulaire de la description"), notes=["prévu en N1.3"]),
    # ── Garanties (règles systématiques) ───────────────────────────────────
    Bloc("garantie:proprietaire", "Garanties", "Propriétaire immuable", "le propriétaire d'une fiche ne change jamais",
         Partie(S, "le propriétaire ne change jamais"), None, Partie(JB + "modifier.mts", "changer le propriétaire"),
         Partie(EX_MED, '"owner"', "médiathèque (sabotage « règle supprimée »)"), notes=["règle serveur seulement : rien à afficher"]),
    Bloc("garantie:date", "Garanties", "Date de création immuable", "on ne peut pas antidater une fiche",
         Partie(S, "la date de création non plus"), None, Partie(JB + "modifier.mts", "sa date de création"),
         Partie(EX_TYP, '"nature": "collection"', "app des types et médiathèque"), notes=["règle serveur seulement : rien à afficher"]),
    Bloc("garantie:cloture", "Garanties", "Clôture à la création", "on ne désigne que des fiches qu'on a le droit de voir",
         Partie(S, "check({l.nom}, 'read')"), None, Partie(JB + "creer.mts", "qu'il ne voit pas"), None,
         notes=["règle serveur seulement", "prouvée seulement quand la fiche désignée n'est pas publique : jamais encore (toujours « sans effet »)"]),
    Bloc("garantie:etape-seule", "Garanties", "Une étape ne change que l'état", "pendant une étape, aucun autre champ ne bouge",
         Partie(S, "def _inchange"), None, Partie(JB + "circuit.mts", "en changeant aussi"),
         Partie(EX_TYP, '"obligatoire": false', "app des types : champs facultatifs vides et remplis"), notes=["règle serveur seulement"]),
] + [
    _type("texte", "Texte", "String", "quelques mots (un nom, un titre)"),
    _type("texte_long", "Texte long", "String", "plusieurs lignes (un résumé)"),
    _type("nombre", "Nombre", "Int", "un entier (une quantité, une année)"),
    _type("montant", "Montant", "Decimal", "une somme d'argent, aux centimes près"),
    _type("date", "Date", "DateTime", "un jour"),
    _type("date_heure", "Date et heure", "DateTime", "un instant"),
    _type("oui_non", "Oui / non", "Boolean", "une case à cocher"),
    _type("email", "E-mail", "String", "une adresse e-mail"),
    _type("telephone", "Téléphone", "String", "un numéro de téléphone"),
    _type("url", "Adresse web", "String", "un lien vers un site"),
    _type("choix", "Liste fixe", "enum", "une valeur parmi une liste donnée par le brief"),
]
# les parties « écran » d'une règle serveur n'existent pas par nature : ce n'est pas un manque
SANS_ECRAN = {"garantie:proprietaire", "garantie:date", "garantie:cloture", "garantie:etape-seule"}


def vocabulaire() -> dict[str, list[str]]:
    """Les mots de vocabulaire, lus DANS LE CODE (les formes strictes), pas recopiés à la main."""
    from ..description import TypeChamp
    from ..matrice import Entity
    from agents.capability_matrix import AccessException, Cell

    def args(modele, champ) -> list[str]:
        a = modele.model_fields[champ].annotation
        return [x for x in typing.get_args(a) if isinstance(x, str)] or [
            x for sous in typing.get_args(a) for x in typing.get_args(sous) if isinstance(x, str)]
    return {
        "nature": args(Entity, "nature"),
        "action": args(AccessException, "action"),
        "type": list(typing.get_args(TypeChamp)),
        # rien / les siennes / toutes : le cœur du bloc « voir » ; les autres portées ont leur bloc
        "portee": [s for s in args(Cell, "see") if s not in ("none", "own", "all")] + ["via"],
    }


def controle() -> list[str]:
    """Le CONTRÔLE D'ARCHITECTURE : chaque mot a son bloc ; chaque partie déclarée existe vraiment."""
    erreurs = []
    ids = {b.id for b in BLOCS}
    for famille, mots in vocabulaire().items():
        for mot in mots:
            if f"{famille}:{mot}" not in ids:
                erreurs.append(f"le mot « {mot} » ({famille}) n'a pas de bloc dans le catalogue")
    for b in BLOCS:
        for nom, p in list(b.parties.items()) + [("refus", b.refuse)]:
            if p is None:
                continue
            chemin = RACINE / p.fichier
            if not chemin.exists():
                erreurs.append(f"{b.id} / {nom} : fichier {p.fichier} introuvable")
            elif p.repere not in chemin.read_text(encoding="utf-8"):
                erreurs.append(f"{b.id} / {nom} : « {p.repere} » introuvable dans {p.fichier}")
        if not b.refuse and b.etat == "partiel":
            manquants = [n for n, p in b.parties.items() if p is None and not (n == "écran" and b.id in SANS_ECRAN)]
            if manquants and not b.notes:
                erreurs.append(f"{b.id} : parties manquantes {manquants} sans explication")
    return erreurs


def blocs_de(desc) -> list[str]:
    """Les blocs qu'une description utilise (pour le rapport de fabrication)."""
    utilises = {f"nature:{e.nature}" for e in desc.acces.entities}
    utilises |= {f"type:{c.type}" for cs in desc.champs.values() for c in cs}
    if any(e.process for e in desc.acces.entities):
        utilises |= {"action:transition", "garantie:etape-seule"}
    if any(e.references for e in desc.acces.entities):
        utilises |= {"lien:reference", "garantie:cloture"}
    if any(e.owner for e in desc.acces.entities):
        utilises.add("garantie:proprietaire")
    utilises |= {"action:see", "action:create", "acteur:roles", "acteur:visitor", "acteur:intrus", "garantie:date"}
    utilises |= {f"action:{x.action}" for x in desc.acces.exceptions}
    return sorted(u for u in utilises if u in {b.id for b in BLOCS})
