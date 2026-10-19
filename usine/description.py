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
    # pour reconnaître la fiche (clôture) — le miroir le montrera au client ; « proposition » : proposé
    # par l'IA et ACCEPTÉ par le client (miroir, N1.4 — en répétition : client simulé, étiqueté)
    origine: Literal["brief", "necessaire", "proposition"] = "brief"
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
        # (12 oct) chaque refus d'un bloc pas construit commence par un CODE stable « [bloc:<id du catalogue>] » ou
        # « [limite:…] » : le catalogue des blocs et l'outil de répétition lisent le code, plus des morceaux de phrase
        natures = {e.name: e.nature for e in self.acces.entities}
        for e in self.acces.entities:
            # (N1.3) les fiches enfants (les lignes d'une fiche) sont construites ; une ligne de ligne, pas encore
            # (13 oct) une ligne qui « désigne » aussi son parent : le même lien deux fois — refusé franchement
            # (la génération du schéma plantait sur un champ en double)
            if e.nature == "child" and e.parent in e.references:
                errs.append(f"[erreur:enfant-designe-parent] {e.name} : désigne aussi son parent {e.parent} "
                            "(le lien vers le parent existe déjà)")
            if e.nature == "child" and natures.get(e.parent) == "child":
                errs.append(f"[limite:ligne-de-ligne] {e.name} : une ligne de ligne (enfant de {e.parent}, lui-même enfant) n'est pas encore construite")
            # (N1.1b, trouvé par l'inventaire des blocs) la publication n'a pas encore son bloc : la règle
            # citerait un champ « published » jamais créé — refusée franchement plutôt qu'à moitié faite
            if e.publication:
                errs.append(f"[bloc:portee:published] {e.name} : la publication (brouillon / publié) arrive en N1.3 (bloc pas encore construit)")
            # (N1.2) saisie pour autrui : l'écran devrait faire choisir la personne concernée — bloc pas encore
            # construit (aucun des vrais briefs ne l'a demandé) : refusé franchement
            if e.nature == "collection" and (e.entered_by or (e.process and e.process.initiator != e.owner)):
                errs.append(f"[bloc:lien:pour-autrui] {e.name} : fiches saisies pour quelqu'un d'autre — arrivent avec l'écran « choisir la personne » (N1.x)")
            # (répétition temps 2, trouvé par le juge des règles) un profil est créé tout seul à la première
            # connexion : un lien obligatoire (« son agence ») ne peut pas y être rempli — l'app plantait à la
            # première connexion de ce rôle. Bloc « lien depuis un profil » pas encore construit : refusé franchement
            if e.nature == "profile" and e.references:
                errs.append(f"[bloc:lien:profil] {e.name} : un profil qui désigne une autre fiche ({', '.join(e.references)}) arrive en N1.3 "
                            "(bloc « lien depuis un profil » pas encore construit)")
        # (répétition temps 2, trouvé par le testeur qui plantait) « les siennes » sur une fiche SANS propriétaire
        # (« le client voit ses équipements » : l'équipement le désigne, il ne lui appartient pas) — aucune
        # règle n'était écrite (l'acteur ne voyait rien, en silence). Bloc « celles qui le désignent » pas
        # encore construit : refusé franchement
        proprio = {e.name: e.owner for e in self.acces.entities}
        for x in self.acces.exceptions:
            # (13 oct, corpus) même chose pour un acteur qui n'est PAS le propriétaire (« l'enseignant voit les siennes »
            # parmi les notes des étudiants) : il n'en possède aucune — il veut celles qui le désignent
            # (14 oct, corpus) créer le PROFIL d'une autre personne (« le RH crée les comptes des employés ») : c'est
            # inviter quelqu'un — bloc pas encore construit (N1.5) ; traduit tel quel, la règle laissait le RH se créer
            # une fiche d'employé à lui-même (le juge l'a vu)
            if x.action == "create" and x.allow and natures.get(x.entity) == "profile" and proprio.get(x.entity) != x.actor:
                errs.append(f"[bloc:acteur:invitation] {x.actor} / {x.entity} : créer le compte d'une autre personne, c'est "
                            "l'inviter — arrive avec la connexion et l'équipe (N1.5)")
            if x.action == "see" and x.allow and x.scope == "own" and x.entity in proprio and proprio[x.entity] != x.actor:
                errs.append(f"[bloc:portee:designe] {x.actor} / {x.entity} : « les siennes » sur des fiches qu'il ne possède pas "
                            f"({'sans propriétaire' if not proprio[x.entity] else 'elles sont à « ' + proprio[x.entity] + ' »'}) — "
                            "« celles qui le désignent » arrive en N1.3 (bloc pas encore construit)")
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
