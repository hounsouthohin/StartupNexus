"""La DESCRIPTION de l'app : le contrat d'entrée de toute la chaîne (règle 3 : forme stricte).

= le format d'accès du calculateur (acteurs, fiches, circuits, exceptions) tel quel
+ les CHAMPS de chaque fiche (types fermés)
+ les libellés d'écran (verbe de création, boutons du circuit)
+ les données de départ (le contenu des catalogues).
Écrite par les lecteurs IA (`python -m usine comprendre`, N1.1) ou à la main (usine/exemples/).
"""
from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .matrice import AccessDeclaration


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


# Types de champs pris en charge (11 des 12 de l'étude 01 ; les « liens multiples » viendront avec
# le traducteur complet, N1.3).
TypeChamp = Literal["texte", "texte_long", "nombre", "montant", "date", "date_heure", "oui_non",
                    "email", "telephone", "url", "choix"]
RESERVES = {"id", "ownerId", "userId", "status", "createdAt", "published"}
IDENT = re.compile(r"^[a-z][A-Za-z0-9]*$")
CODE = re.compile(r"^[a-z][a-z0-9_]*$")


class Valeur(_Strict):
    """Une valeur d'un champ « choix » : un code stable (base de données) et son libellé (écran)."""
    code: str
    libelle: str


class Champ(_Strict):
    nom: str                        # identifiant (camelCase, sans accent)
    libelle: str
    type: TypeChamp
    obligatoire: bool = True
    valeurs: list[Valeur] = Field(default_factory=list)      # seulement pour « choix »
    # « brief » : cité par le brief ; « necessaire » : le brief ne cite rien, il faut au moins un nom
    # pour reconnaître la fiche (clôture) — le miroir le montrera au client
    origine: Literal["brief", "necessaire"] = "brief"
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
                codes = [v.code for v in c.valeurs]
                if c.type == "choix" and (len(codes) < 2 or len(set(codes)) != len(codes)
                                          or not all(CODE.match(x) for x in codes)):
                    errs.append(f"{fiche}.{c.nom} : un choix a au moins 2 valeurs, codes uniques en minuscules")
                if c.type != "choix" and c.valeurs:
                    errs.append(f"{fiche}.{c.nom} : des valeurs seulement pour un choix")
        for e in self.acces.entities:
            if e.nature == "child":
                errs.append(f"{e.name} : les fiches enfants arrivent en N1.x (pas dans le squelette)")
            # (N1.1b, trouvé par l'inventaire des blocs) la publication n'a pas encore son bloc : la règle
            # citerait un champ « published » jamais créé — refusée franchement plutôt qu'à moitié faite
            if e.publication:
                errs.append(f"{e.name} : la publication (brouillon / publié) arrive en N1.3 (bloc pas encore construit)")
        for fiche in self.ecran:
            if fiche not in noms:
                errs.append(f"ecran : fiche « {fiche} » inconnue")
        for fiche, lignes in self.depart.items():
            if fiche not in noms:
                errs.append(f"depart : fiche « {fiche} » inconnue")
                continue
            connus = {c.nom for c in self.champs.get(fiche, [])}
            requis = {c.nom for c in self.champs.get(fiche, []) if c.obligatoire}
            choix = {c.nom: {v.code for v in c.valeurs} for c in self.champs.get(fiche, []) if c.type == "choix"}
            for i, ligne in enumerate(lignes):
                if set(ligne) - connus:
                    errs.append(f"depart.{fiche}[{i}] : champs inconnus {sorted(set(ligne) - connus)}")
                if requis - set(ligne):
                    errs.append(f"depart.{fiche}[{i}] : champs obligatoires manquants {sorted(requis - set(ligne))}")
                errs += [f"depart.{fiche}[{i}].{n} : « {ligne[n]} » n'est pas un code permis {sorted(codes)}"
                         for n, codes in choix.items() if n in ligne and ligne[n] not in codes]
        if errs:
            raise ValueError("description refusée :\n- " + "\n- ".join(errs))
        return self
