"""Vue structurée de l'app, partagée par tous les traducteurs (règle 1 : un fait, un seul auteur).
Qui possède quoi, quels liens, quels noms de champs : calculé UNE fois ici."""
from __future__ import annotations

from dataclasses import dataclass, field

from ..description import Champ, Description
from ..matrice import Entity, Matrix


def bas(nom: str) -> str:
    """« BorrowingStatus » → « borrowingStatus » (nom côté API et noms de relations)."""
    return nom[0].lower() + nom[1:]


@dataclass
class Lien:
    nom: str            # nom de la relation (« book »)
    cible: str          # fiche visée (« Book »)
    fk: str             # champ qui porte la clé (« bookId » ou, pour le profil du propriétaire, « ownerId »)
    ref: str            # champ visé (« id » ou « userId »)
    proprietaire: bool  # True : c'est le profil du propriétaire (lien rempli automatiquement)


@dataclass
class FicheApp:
    e: Entity
    champs: list[Champ]
    proprio: str | None                 # champ qui porte l'identifiant du propriétaire
    liens: list[Lien] = field(default_factory=list)
    inverses: list[tuple[str, str]] = field(default_factory=list)   # (nom de relation, fiche qui pointe ici)
    etats: list[str] = field(default_factory=list)

    @property
    def nom(self) -> str:
        return self.e.name


def etats_ordonnes(e: Entity) -> list[str]:
    """États dans un ordre stable : l'état initial, puis en suivant les flèches."""
    if not e.process:
        return []
    p, vus, file = e.process, [], [e.process.initial]
    while file:
        s = file.pop(0)
        if s in vus:
            continue
        vus.append(s)
        file += p.transitions.get(s, [])
    tous = {s for t in p.transitions.values() for s in t} | set(p.transitions)
    return vus + sorted(tous - set(vus))     # états inaccessibles (rares) à la fin


def construire(desc: Description, m: Matrix) -> dict[str, FicheApp]:
    ents = {e.name: e for e in desc.acces.entities}
    fiches: dict[str, FicheApp] = {}
    for e in desc.acces.entities:
        proprio = "userId" if e.nature == "profile" else "ownerId" if e.nature == "collection" else None
        fiches[e.name] = FicheApp(e=e, champs=list(desc.champs.get(e.name, [])), proprio=proprio, etats=etats_ordonnes(e))
    for e in desc.acces.entities:
        f = fiches[e.name]
        for r in e.references:
            cible = ents[r]
            # le profil du propriétaire : lien porté par ownerId → userId, rempli automatiquement
            if cible.nature == "profile" and e.nature == "collection" and cible.owner == e.owner:
                f.liens.append(Lien(nom=bas(r), cible=r, fk="ownerId", ref="userId", proprietaire=True))
            else:
                f.liens.append(Lien(nom=bas(r), cible=r, fk=f"{bas(r)}Id", ref="id", proprietaire=False))
            fiches[r].inverses.append((f"{bas(e.name)}s", e.name))
    return fiches


def premier_texte(f: FicheApp) -> str:
    for c in f.champs:
        if c.type in ("texte", "email"):
            return c.nom
    return "id"
