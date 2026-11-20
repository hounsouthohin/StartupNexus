"""Traducteur n°2 : description + matrice → notice.ts (fiches, champs, liens, circuit) et droits.ts
(droits d'écran, menu, profil). Des DONNÉES TypeScript : les pièces fixes du squelette les lisent."""
from __future__ import annotations

import json

from ..description import Description
from ..matrice import VISITOR, Matrix
from .modele import FicheApp, bas, construire, premier_texte

ENTETE = "// FICHIER PRODUIT PAR L'USINE — ne pas modifier : il est régénéré à chaque fabrication.\n"
AFFICHAGE = {"date": "date", "date_heure": "date_heure", "oui_non": "oui_non", "montant": "montant", "choix": "choix"}


def _options(c) -> dict:
    """Les valeurs d'un champ « choix » : code (base de données) → libellé (écran)."""
    return {"options": {v.code: v.libelle for v in c.valeurs}} if c.type == "choix" else {}


def _j(x) -> str:
    return json.dumps(x, ensure_ascii=False)


def _maj(s: str) -> str:
    return s[:1].upper() + s[1:]


# (contrat des noms à l'écran, 20 nov 2026) LE TITRE d'une fiche vient de la description (format 2), jamais deviné ici.
def titre_de(desc: Description, fiches: dict[str, FicheApp], nom: str) -> dict | None:
    """{"champ": "title"} si le titre est un champ de la fiche (a) ; {"lien": "book", "champ": "title"} s'il vient de
    la fiche qu'elle désigne (b, un seul niveau) ; None pour une fiche qui n'en a pas (profil, ligne)."""
    ec = desc.ecran.get(nom)
    t = ec.titre if ec else None
    if not t:
        return None
    if t[:1].isupper():
        cible = desc.ecran[t].titre
        lien = next(l for l in fiches[nom].liens if l.cible == t and not l.proprietaire)
        return {"lien": lien.nom, "champ": cible}
    return {"champ": t}


def affiche_de(desc: Description, fiches: dict[str, FicheApp], cible: str) -> str:
    """Ce qui montre une fiche liée (listes de choix, fiche désignée) : son titre. Un titre tiré d'une fiche liée
    s'écrit « lien.champ » (le squelette inclut alors ce lien). Une fiche sans titre (profil, ligne) garde l'ancienne
    règle « premier champ texte »."""
    t = titre_de(desc, fiches, cible)
    if t is None:
        return premier_texte(fiches[cible])
    return f"{t['lien']}.{t['champ']}" if "lien" in t else t["champ"]


# ─── (contrat des noms à l'écran) LES NOMS QUE L'APP MONTRE, calculés à un seul endroit ─────────────────────────────
# La notice (les écrans) et le miroir (ce que le client valide) les lisent ici tous les deux : le client valide donc
# exactement ce que l'app affichera, sans copie d'une règle.

def libelle_liste(e) -> str:
    """Le nom d'une liste : son entrée de menu et le titre de sa page (« Emprunts »)."""
    return _maj(e.label_plural)


def boutons_etapes(desc: Description, f: FicheApp) -> dict[str, str]:
    """Le bouton qui mène à chaque état d'arrivée : le nom donné dans la description, sinon le libellé de l'état."""
    e = f.e
    ecran = desc.ecran.get(e.name)
    boutons = (ecran.boutons if ecran else {}) or {}
    cibles = {t for ts in e.process.transitions.values() for t in ts}
    return {t: boutons.get(t) or _maj(e.process.labels.get(t, t)) for t in f.etats if t in cibles}


def creations_en_un_clic(desc: Description, m: Matrix, fiches: dict[str, FicheApp], cible: str) -> list[dict]:
    """« Emprunter » : sur chaque fiche `cible`, un bouton qui crée d'un clic la fiche qui la désigne — seulement si
    le clic suffit à la remplir : aucun champ obligatoire, et un seul lien à poser (sinon il faut un formulaire)."""
    actions = []
    for autre in fiches.values():
        if autre.e.nature == "child" or any(c.obligatoire for c in autre.champs) or len([x for x in autre.liens if not x.proprietaire]) != 1:
            continue
        for l in autre.liens:
            if l.cible == cible and not l.proprietaire and any(
                    c.entity == autre.nom and c.create == "yes" for c in m.cells):
                verbe = (desc.ecran.get(autre.nom).verbe_creation if desc.ecran.get(autre.nom) else None)
                actions.append({"libelle": verbe or f"Nouveau : {autre.e.label}", "cree": autre.nom, "lien": l.fk})
    return actions


def noms_a_l_ecran(desc: Description, m: Matrix) -> dict[str, dict]:
    """Pour chaque fiche principale (ni profil ni ligne : hors du contrat), les noms que l'app montre :
    {"menu": "Emprunts", "creation": "Nouvel emprunt", "creation_visible": True,   (False : aucun rôle n'en crée)
     "titre": {"sorte": "Emprunt", "champ": "Titre", "via": "Book"},   (via : la fiche désignée ; None si c'est un de ses champs)
     "etapes": {"accepted": "Accepter", …}, "clics": [{"libelle": "Emprunter", "depuis": "Book"}]}"""
    fiches = construire(desc, m)
    out: dict[str, dict] = {}
    for f in fiches.values():
        e = f.e
        if e.nature in ("profile", "child"):
            continue
        t = titre_de(desc, fiches, e.name)
        if t is None:
            titre = None
        elif "lien" in t:
            cible = next(l.cible for l in f.liens if l.nom == t["lien"])
            titre = {"sorte": _maj(e.label), "champ": next(c.libelle for c in fiches[cible].champs if c.nom == t["champ"]),
                     "via": cible}
        else:
            titre = {"sorte": _maj(e.label), "champ": next(c.libelle for c in f.champs if c.nom == t["champ"]), "via": None}
        # le bouton de création n'apparaît que pour un rôle qui crée : le miroir le dit au lieu de le faire valider en vain
        cree = any(c.entity == e.name and c.create == "yes" for c in m.cells)
        out[e.name] = {"menu": libelle_liste(e), "creation": desc.ecran[e.name].creation, "creation_visible": cree, "titre": titre,
                       "etapes": boutons_etapes(desc, f) if e.process else {},
                       "clics": [{"libelle": a["libelle"], "depuis": depuis}
                                 for depuis in fiches for a in creations_en_un_clic(desc, m, fiches, depuis) if a["cree"] == e.name]}
    return out


def _fiche(f: FicheApp, fiches: dict[str, FicheApp], desc: Description, m: Matrix) -> dict:
    e = f.e
    ecran = desc.ecran.get(e.name)
    champs = []
    if e.process:
        champs.append({"nom": "status", "libelle": "État", "type": "etat"})
    for c in f.champs:
        champs.append({"nom": c.nom, "libelle": c.libelle, **({"type": AFFICHAGE[c.type]} if c.type in AFFICHAGE else {}),
                       **_options(c)})
    if e.process:
        champs.append({"nom": "createdAt", "libelle": "Créé le", "type": "date_heure"})
    n: dict = {
        "modele": bas(e.name),
        "libelle": e.label,
        # la liste (aussi celle des profils, vue par d'autres rôles) ; « Mon … » est le titre de /profil
        "titre": libelle_liste(e),
        "champs": champs,
        "modifiables": [{"nom": c.nom, "libelle": c.libelle, "saisie": c.type, "obligatoire": c.obligatoire, **_options(c)}
                        for c in f.champs],
    }
    if e.nature not in ("profile", "child"):     # (N1.3) une ligne s'ajoute depuis la page de son parent
        # (contrat des noms à l'écran) le nom du bouton de création VIENT DE LA DESCRIPTION (format 2), montré au client
        # au miroir ; la règle de grammaire n'est plus ici (elle est dans la complétion, avant le miroir)
        n["creation"] = {"libelle": ecran.creation}
        n["titreFiche"] = titre_de(desc, fiches, e.name)
    if f.liens:
        roles = {a.id: a.label for a in desc.acces.actors}
        # le profil du propriétaire s'affiche sous le nom de son rôle (« Adhérent »), pas « Profil » ;
        # (N1.2) fk / cible / proprietaire : pour les listes de choix des formulaires (le lien vers le
        # profil du propriétaire est posé automatiquement : jamais choisi)
        n["liens"] = [{"nom": l.nom, "affiche": affiche_de(desc, fiches, l.cible),
                       "libelle": _maj(roles.get(e.owner, fiches[l.cible].e.label) if l.proprietaire else fiches[l.cible].e.label),
                       "fk": l.fk, "cible": l.cible, "proprietaire": l.proprietaire, **({"parent": True} if l.parent else {})}
                      for l in f.liens]
    lp = next((l for l in f.liens if l.parent), None)
    if lp:
        n["parent"] = {"fiche": lp.cible, "fk": lp.fk}     # (N1.3) une ligne : posée depuis la page de son parent
    if f.enfants:
        # (N1.3) les lignes de cette fiche, affichées (et gérées) dans sa page
        n["enfants"] = [{"fiche": src, "fk": next(l.fk for l in fiches[src].liens if l.parent),
                         "libelle": _maj(fiches[src].e.label_plural), "libelle_un": fiches[src].e.label}
                        for _rel, src in f.enfants]
    if f.inverses:
        # (N1.2) les fiches qui peuvent désigner celle-ci : une fiche désignée ne se supprime pas (intégrité),
        # l'écran le dit au lieu de proposer un bouton que le serveur refuserait
        n["designee_par"] = [{"relation": rel, "libelle": fiches[source].e.label_plural, "libelle_un": fiches[source].e.label}
                             for rel, source in f.inverses]
    # le tri ne fait pas partie du contrat : les fiches à circuit, les plus récentes d'abord (inchangé, les tests en
    # dépendent) ; les autres fiches principales, par leur titre s'il est un de leurs champs, sinon par date de création
    t = n.get("titreFiche")
    if e.process:
        tri, sens = "createdAt", "desc"
    elif t is not None:
        tri, sens = (t["champ"], "asc") if "lien" not in t else ("createdAt", "asc")
    else:
        tri, sens = premier_texte(f), "asc"
    if tri != "id":
        n["tri"] = {"champ": tri, "sens": sens}
    if e.process:
        n["etat"] = {"champ": "status", "initial": e.process.initial,
                     "libelles": e.process.labels or {s: s for s in f.etats},
                     "boutons": boutons_etapes(desc, f)}
    actions = creations_en_un_clic(desc, m, fiches, e.name)        # « Emprunter » sur chaque ouvrage
    if actions:
        n["actionsLigne"] = actions
    return n


def traduire_notice(desc: Description, m: Matrix) -> str:
    fiches = construire(desc, m)
    noms = list(fiches)
    lignes = [ENTETE, f"import type {{ {', '.join(noms)} }} from '@/zenstack/models';",
              "import type { Fiche } from './fiche';", "",
              f"export type NomFiche = {' | '.join(_j(x) for x in noms)};", ""]
    for nom, f in fiches.items():
        # « satisfies Fiche<Modèle> » : chaque nom de champ est vérifié contre le schéma (étude 06)
        lignes.append(f"const fiche{nom} = {_j(_fiche(f, fiches, desc, m))} satisfies Fiche<{nom}>;")
    lignes += ["", "export const NOTICE = { " + ", ".join(f"{x}: fiche{x}" for x in noms)
               + " } as unknown as Record<NomFiche, Fiche>;", ""]
    return "\n".join(lignes)


def traduire_roles(desc: Description) -> str:
    """lib/roles.ts : le libellé de chaque rôle pour l'accueil et l'en-tête (répétition temps 2 : l'écran
    affichait l'identifiant, « responsable_des_commandes »)."""
    libelles = {VISITOR: "visiteur", **{a.id: a.label for a in desc.acces.actors}}
    return ("// FICHIER PRODUIT PAR L'USINE — libellés des rôles pour l'écran.\n"
            f"export const LIBELLE_ROLE: Record<string, string> = {_j(libelles)};\n")


def traduire_droits(desc: Description, m: Matrix) -> str:
    fiches = construire(desc, m)
    roles = [VISITOR] + [a.id for a in desc.acces.actors]
    matrice: dict = {r: {} for r in roles}
    for c in m.cells:
        d = {}
        if c.see != "none":
            d["voir"] = True
        if c.create == "yes":
            d["creer"] = True
            if c.create_while:
                d["creer_pendant"] = c.create_while       # (N1.3) une ligne : états du parent où elle s'ajoute (matrice)
        if c.edit:
            d["modifier"] = True
            if c.edit_while:
                d["modifier_pendant"] = c.edit_while      # (N1.2) seulement dans ces états
        if c.delete:
            d["supprimer"] = True
            if c.delete_while:
                d["supprimer_pendant"] = c.delete_while
        if c.transitions:
            d["transitions"] = c.transitions
        if d:
            matrice[c.actor][c.entity] = d
    menu = []
    profils = []
    for f in fiches.values():
        e = f.e
        if e.nature == "profile":
            # (répétition temps 2) UN profil par rôle : l'usine n'en gardait qu'un (le dernier) — les autres
            # rôles n'avaient ni profil créé à la connexion, ni « Mon profil » ; ce qui désignait leur profil
            # (« l'équipe et ses membres ») était impossible à créer. Les autres rôles qui voient ces profils
            # les ont en liste, jamais comme « Mon … ».
            menu.append({"fiche": e.name, "chemin": "/profil", "libelle": f"Mon {e.label}", "action": "voir", "role": e.owner})
            menu.append({"fiche": e.name, "chemin": f"/f/{e.name}", "libelle": libelle_liste(e), "action": "voir",
                         "sauf": e.owner})
            profils.append({"fiche": e.name, "role": e.owner,
                            "obligatoires": [{"nom": c.nom, "type": c.type,
                                              **({"defaut": c.valeurs[0].code} if c.type == "choix" else {})}
                                             for c in f.champs if c.obligatoire]})
        elif e.nature == "child":
            continue                                 # (N1.3) une ligne n'a pas de menu : elle vit dans son parent
        else:
            menu.append({"fiche": e.name, "chemin": f"/f/{e.name}", "libelle": libelle_liste(e), "action": "voir"})
    return "\n".join([
        ENTETE,
        "import type { NomFiche } from './notice';",
        "import type { Droits } from './peut';", "",
        f"export type Role = {' | '.join(_j(r) for r in roles)};",
        f"export const ROLES_CONNECTES: Role[] = {_j(roles[1:])};",
        f"export const TITRE = {_j(desc.app.titre)};",
        f"export const MATRICE: Record<Role, Partial<Record<NomFiche, Droits>>> = {_j(matrice)};",
        "export const MENU: { fiche: NomFiche; chemin: string; libelle: string; action: 'voir'; role?: Role; sauf?: Role }[] = "
        f"{_j(menu)};",
        "export const PROFILS: { fiche: NomFiche; role: Role; obligatoires: { nom: string; type: string; defaut?: string }[] }[] = "
        f"{_j(profils)};",
        "// une entrée de menu « Mon … » n'est que pour son rôle ; la liste du même profil, pour les autres",
        "export const pourRole = (m: { role?: Role; sauf?: Role }, role: Role) => (!m.role || m.role === role) && m.sauf !== role;",
        "",
    ])
