"""La DESCRIPTION de l'app : le contrat d'entrée de toute la chaîne (règle 3 : forme stricte).

= le format d'accès du calculateur (acteurs, fiches, circuits, exceptions) tel quel
+ les CHAMPS de chaque fiche (types fermés)
+ les libellés d'écran (verbe de création, boutons du circuit)
+ les données de départ (le contenu des catalogues).
Aujourd'hui écrite à la main (N1.0) ; demain produite par les agents de compréhension (N1.1).
"""
from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .matrice import AccessDeclaration


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


# Types de champs pris en charge. « montant » et « choix » (tables de choix) arrivent en N1.1.
TypeChamp = Literal["texte", "texte_long", "nombre", "date", "date_heure", "oui_non", "email", "telephone", "url"]
RESERVES = {"id", "ownerId", "userId", "status", "createdAt"}
IDENT = re.compile(r"^[a-z][A-Za-z0-9]*$")


class Champ(_Strict):
    nom: str                        # identifiant (camelCase, sans accent)
    libelle: str
    type: TypeChamp
    obligatoire: bool = True
    citation: str = ""


class EcranFiche(_Strict):
    verbe_creation: str | None = None             # « Emprunter » (bouton sur la fiche liée)
    boutons: dict[str, str] = Field(default_factory=dict)   # état cible → libellé du bouton


class App(_Strict):
    nom: str                        # identifiant court (minuscules, chiffres, tirets)
    titre: str


class Description(_Strict):
    app: App
    acces: AccessDeclaration
    champs: dict[str, list[Champ]] = Field(default_factory=dict)
    ecran: dict[str, EcranFiche] = Field(default_factory=dict)
    depart: dict[str, list[dict]] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _coherence(self) -> "Description":
        noms = {e.name for e in self.acces.entities}
        errs: list[str] = []
        if not re.match(r"^[a-z][a-z0-9-]*$", self.app.nom):
            errs.append(f"app.nom « {self.app.nom} » : minuscules, chiffres et tirets")
        refs = {f"{r[0].lower()}{r[1:]}Id" for e in self.acces.entities for r in e.references}
        for fiche, champs in self.champs.items():
            if fiche not in noms:
                errs.append(f"champs : fiche « {fiche} » inconnue")
            vus = set()
            for c in champs:
                if not IDENT.match(c.nom):
                    errs.append(f"{fiche}.{c.nom} : identifiant camelCase sans accent")
                if c.nom in RESERVES or c.nom in refs:
                    errs.append(f"{fiche}.{c.nom} : nom réservé par l'usine")
                if c.nom in vus:
                    errs.append(f"{fiche}.{c.nom} : en double")
                vus.add(c.nom)
        for e in self.acces.entities:
            if e.nature == "child":
                errs.append(f"{e.name} : les fiches enfants arrivent en N1.x (pas dans le squelette)")
        for fiche in self.ecran:
            if fiche not in noms:
                errs.append(f"ecran : fiche « {fiche} » inconnue")
        for fiche, lignes in self.depart.items():
            if fiche not in noms:
                errs.append(f"depart : fiche « {fiche} » inconnue")
                continue
            connus = {c.nom for c in self.champs.get(fiche, [])}
            requis = {c.nom for c in self.champs.get(fiche, []) if c.obligatoire}
            for i, ligne in enumerate(lignes):
                if set(ligne) - connus:
                    errs.append(f"depart.{fiche}[{i}] : champs inconnus {sorted(set(ligne) - connus)}")
                if requis - set(ligne):
                    errs.append(f"depart.{fiche}[{i}] : champs obligatoires manquants {sorted(requis - set(ligne))}")
        if errs:
            raise ValueError("description refusée :\n- " + "\n- ".join(errs))
        return self
