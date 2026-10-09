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
        "titre": f"Mon {e.label}" if e.nature == "profile" else _maj(e.label_plural),
        "champs": champs,
        "modifiables": [{"nom": c.nom, "libelle": c.libelle, "saisie": c.type, "obligatoire": c.obligatoire, **_options(c)}
                        for c in f.champs],
    }
    if f.liens:
        roles = {a.id: a.label for a in desc.acces.actors}
        # le profil du propriétaire s'affiche sous le nom de son rôle (« Adhérent »), pas « Profil »
        n["liens"] = [{"nom": l.nom, "affiche": premier_texte(fiches[l.cible]),
                       "libelle": _maj(roles.get(e.owner, fiches[l.cible].e.label) if l.proprietaire else fiches[l.cible].e.label)}
                      for l in f.liens]
    tri = "createdAt" if e.process else premier_texte(f)
    if tri != "id":
        n["tri"] = {"champ": tri, "sens": "desc" if e.process else "asc"}
    if e.process:
        boutons = (ecran.boutons if ecran else {}) or {}
        cibles = {t for ts in e.process.transitions.values() for t in ts}
        n["etat"] = {"champ": "status", "initial": e.process.initial,
                     "libelles": e.process.labels or {s: s for s in f.etats},
                     "boutons": {t: boutons.get(t) or _maj(e.process.labels.get(t, t)) for t in f.etats if t in cibles}}
    # « Emprunter » : un bouton sur chaque fiche liée pour créer, d'un clic, la fiche qui la désigne —
    # seulement si le clic suffit à la remplir : aucun champ obligatoire, et un seul lien à poser
    # (sinon il faut un formulaire : N1.5)
    actions = []
    for autre in fiches.values():
        if any(c.obligatoire for c in autre.champs) or len([x for x in autre.liens if not x.proprietaire]) != 1:
            continue
        for l in autre.liens:
            if l.cible == e.name and not l.proprietaire and any(
                    c.entity == autre.nom and c.create == "yes" for c in m.cells):
                verbe = (desc.ecran.get(autre.nom).verbe_creation if desc.ecran.get(autre.nom) else None)
                actions.append({"libelle": verbe or f"Nouveau : {autre.e.label}", "cree": autre.nom, "lien": l.fk})
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
        if c.edit:
            d["modifier"] = True
        if c.transitions:
            d["transitions"] = c.transitions
        if d:
            matrice[c.actor][c.entity] = d
    menu = []
    profil = None
    for f in fiches.values():
        e = f.e
        if e.nature == "profile":
            menu.append({"fiche": e.name, "chemin": "/profil", "libelle": f"Mon {e.label}", "action": "voir"})
            profil = {"fiche": e.name, "role": e.owner,
                      "obligatoires": [{"nom": c.nom, "type": c.type, **({"defaut": c.valeurs[0].code} if c.type == "choix" else {})}
                                       for c in f.champs if c.obligatoire]}
        else:
            menu.append({"fiche": e.name, "chemin": f"/f/{e.name}", "libelle": _maj(e.label_plural), "action": "voir"})
    return "\n".join([
        ENTETE,
        "import type { NomFiche } from './notice';",
        "import type { Droits } from './peut';", "",
        f"export type Role = {' | '.join(_j(r) for r in roles)};",
        f"export const ROLES_CONNECTES: Role[] = {_j(roles[1:])};",
        f"export const TITRE = {_j(desc.app.titre)};",
        f"export const MATRICE: Record<Role, Partial<Record<NomFiche, Droits>>> = {_j(matrice)};",
        f"export const MENU: {{ fiche: NomFiche; chemin: string; libelle: string; action: 'voir' }}[] = {_j(menu)};",
        "export const PROFIL: { fiche: NomFiche; role: Role; obligatoires: { nom: string; type: string; defaut?: string }[] } | null = "
        f"{_j(profil)};", "",
    ])
