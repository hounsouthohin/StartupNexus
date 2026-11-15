# Gestion du parc automobile — ce que l'usine a compris

En bref : 2 rôles (Le gestionnaire de parc, L'utilisateur), 7 sortes de fiches, aucun circuit d'étapes.

## Le visiteur (sans compte)
- Ne voit rien

## Le gestionnaire de parc (responsable de l'app)
- Voit tout, crée et modifie : Véhicules, Suivis de parc auto, États des lieux d’entrée, États des lieux de sortie, Entretiens, Coûts, Plannings

## L'utilisateur (invité par gestionnaire_parc)
- Voit tout, crée et modifie : Véhicules, Suivis de parc auto, États des lieux d’entrée, États des lieux de sortie, Entretiens, Coûts, Plannings

## Les informations de chaque fiche

- **Véhicule** : Immatriculation (texte court) ◦ choisi par nous · QR code (texte court) · État du véhicule (texte court)
  - proposé (à cocher) : ☐ Marque (texte court) · ☐ Modèle (texte court) · ☐ Date de mise en circulation (date) · ☐ Kilométrage (nombre) · ☐ Prix d'achat (montant)
- **Suivi de parc auto** : Intitulé (texte court) ◦ choisi par nous
  - relié à : Véhicule
  - proposé (à cocher) : ☐ Date du suivi (date) · ☐ Kilométrage relevé (nombre) · ☐ Observations (texte long)
- **État des lieux d’entrée** : Intitulé (texte court) ◦ choisi par nous
  - relié à : Véhicule
  - proposé (à cocher) : ☐ Date et heure de l'état des lieux (date et heure) · ☐ Kilométrage à l'entrée (nombre) · ☐ Niveau de carburant (texte court) · ☐ Dommages constatés (texte long) · ☐ Nom de la personne présente (texte court)
- **État des lieux de sortie** : Intitulé (texte court) ◦ choisi par nous
  - relié à : Véhicule
  - proposé (à cocher) : ☐ Date et heure de l'état des lieux (date et heure) · ☐ Kilométrage à la sortie (nombre) · ☐ Niveau de carburant (texte court) · ☐ Dommages constatés (texte long) · ☐ Nom de la personne présente (texte court)
- **Entretien** : Date de l'entretien (date)
  - relié à : Véhicule
  - proposé (à cocher) : ☐ Type d'entretien (texte court) · ☐ Montant de l'entretien (montant) · ☐ Garage ou prestataire (texte court) · ☐ Kilométrage lors de l'entretien (nombre)
- **Coût** : Type de frais (choix parmi : entretien, réparation, assurance, amortissement) · Montant (montant)
  - relié à : Véhicule
  - proposé (à cocher) : ☐ Date de la dépense (date) · ☐ Description (texte court) · ☐ Autres types de frais (choix)
- **Planning** : Intitulé (texte court) ◦ choisi par nous
  - relié à : Véhicule
  - proposé (à cocher) : ☐ Date et heure de début (date et heure) · ☐ Date et heure de fin (date et heure) · ☐ Conducteur ou utilisateur (texte court) · ☐ Motif (texte court)

## Questions

- L'utilisateur verra tous les Véhicules, pas seulement ceux qui le concernent — d'accord ? → **oui, nécessairement** : il doit les voir quand même — clôture : affiché dans les Suivis de parc auto qu'il voit; clôture : choisit les Véhicules de ses Suivis de parc auto
- L'utilisateur verra tous les Suivis de parc auto, pas seulement ceux qui le concernent — d'accord ?
- L'utilisateur verra tous les États des lieux d’entrée, pas seulement ceux qui le concernent — d'accord ?
- L'utilisateur verra tous les États des lieux de sortie, pas seulement ceux qui le concernent — d'accord ?
- L'utilisateur verra tous les Entretiens, pas seulement ceux qui le concernent — d'accord ?
- L'utilisateur verra tous les Coûts, pas seulement ceux qui le concernent — d'accord ?
- L'utilisateur verra tous les Plannings, pas seulement ceux qui le concernent — d'accord ?
- Votre brief ne disait pas comment reconnaître certaines fiches ; nous avons choisi : Véhicule → « Immatriculation » · Suivi de parc auto → « Intitulé » · État des lieux d’entrée → « Intitulé » · État des lieux de sortie → « Intitulé » · Planning → « Intitulé »

## Pas encore dans notre stock (vos mots)

- Lecture d'un QR code apposé sur chaque véhicule pour accéder directement à ses fiches — « Lecture de QR code apposé sur chaque véhicule ... Lorsqu’on scanne, accès direct à toutes les fiches du véhicule »
- Envoi automatique d'e-mails de rappel (entretien, état des lieux, etc.) — « Envoi automatique d’e-mails (rappel entretien, etat des lieux, etc.) »
- Calcul automatique des frais et du coût global du parc (entretien, réparation, assurance, amortissement) — « Fiche coût global du parc ... Calcul automatique des frais (entretien, réparation, assurance, amortissement…) »
- Mise à jour automatique d'autres fiches quand un état des lieux est saisi (planning, coût global) — « un état des lieux déclenche une mise à jour du planning ou du coût global »
- Planning (des entretiens / du parc) — « une mise à jour du planning »
- Tableau de bord global avec indicateurs (alertes, entretiens à venir) — « Tableau de bord global avec indicateurs (alertes, entretiens à venir, etc.) »
- Alertes automatiques — « automatiser les calculs et alertes »

---

## Volet concepteur

### Pour répondre (`python -m usine.miroir repondre <lecture> id=valeur …`)

- `registre_entier:utilisateur:Vehicule` = oui
- `registre_entier:utilisateur:SuiviParc` = oui | non
- `registre_entier:utilisateur:EtatDesLieuxEntree` = oui | non
- `registre_entier:utilisateur:EtatDesLieuxSortie` = oui | non
- `registre_entier:utilisateur:Entretien` = oui | non
- `registre_entier:utilisateur:Cout` = oui | non
- `registre_entier:utilisateur:Planning` = oui | non
- `nom:Vehicule:immatriculation` = oui | <nouveau nom>  (Véhicule → « Immatriculation »)
- `nom:SuiviParc:intitule` = oui | <nouveau nom>  (Suivi de parc auto → « Intitulé »)
- `nom:EtatDesLieuxEntree:intitule` = oui | <nouveau nom>  (État des lieux d’entrée → « Intitulé »)
- `nom:EtatDesLieuxSortie:intitule` = oui | <nouveau nom>  (État des lieux de sortie → « Intitulé »)
- `nom:Planning:intitule` = oui | <nouveau nom>  (Planning → « Intitulé »)
- `garder:Vehicule:Marque` = oui | non
- `garder:Vehicule:Modèle` = oui | non
- `garder:Vehicule:Date de mise en circulation` = oui | non
- `garder:Vehicule:Kilométrage` = oui | non
- `garder:Vehicule:Prix d'achat` = oui | non
- `garder:SuiviParc:Date du suivi` = oui | non
- `garder:SuiviParc:Kilométrage relevé` = oui | non
- `garder:SuiviParc:Observations` = oui | non
- `garder:EtatDesLieuxEntree:Date et heure de l'état des lieux` = oui | non
- `garder:EtatDesLieuxEntree:Kilométrage à l'entrée` = oui | non
- `garder:EtatDesLieuxEntree:Niveau de carburant` = oui | non
- `garder:EtatDesLieuxEntree:Dommages constatés` = oui | non
- `garder:EtatDesLieuxEntree:Nom de la personne présente` = oui | non
- `garder:EtatDesLieuxSortie:Date et heure de l'état des lieux` = oui | non
- `garder:EtatDesLieuxSortie:Kilométrage à la sortie` = oui | non
- `garder:EtatDesLieuxSortie:Niveau de carburant` = oui | non
- `garder:EtatDesLieuxSortie:Dommages constatés` = oui | non
- `garder:EtatDesLieuxSortie:Nom de la personne présente` = oui | non
- `garder:Entretien:Type d'entretien` = oui | non
- `garder:Entretien:Montant de l'entretien` = oui | non
- `garder:Entretien:Garage ou prestataire` = oui | non
- `garder:Entretien:Kilométrage lors de l'entretien` = oui | non
- `garder:Cout:Date de la dépense` = oui | non
- `garder:Cout:Description` = oui | non
- `garder:Cout:Autres types de frais` = oui | non
- `garder:Planning:Date et heure de début` = oui | non
- `garder:Planning:Date et heure de fin` = oui | non
- `garder:Planning:Conducteur ou utilisateur` = oui | non
- `garder:Planning:Motif` = oui | non

### Pourquoi chaque droit

- gestionnaire_parc / Vehicule : tient le registre (supprimer : seulement si le brief le dit) — « Lecture de QR code apposé sur chaque véhicule »
- gestionnaire_parc / SuiviParc : tient le registre (supprimer : seulement si le brief le dit) — « Fiche suivi de parc auto »
- gestionnaire_parc / EtatDesLieuxEntree : tient le registre (supprimer : seulement si le brief le dit) — « Fiche état des lieux d’entrée »
- gestionnaire_parc / EtatDesLieuxSortie : tient le registre (supprimer : seulement si le brief le dit) — « Fiche état des lieux de sortie »
- gestionnaire_parc / Entretien : tient le registre (supprimer : seulement si le brief le dit) — « entretiens à venir »
- gestionnaire_parc / Cout : tient le registre (supprimer : seulement si le brief le dit) — « Calcul automatique des frais (entretien, réparation, assurance, amortissement »
- gestionnaire_parc / Planning : tient le registre (supprimer : seulement si le brief le dit) — « un état des lieux déclenche une mise à jour du planning »
- utilisateur / Vehicule : tient le registre (supprimer : seulement si le brief le dit) — « Lecture de QR code apposé sur chaque véhicule »
- utilisateur / SuiviParc : tient le registre (supprimer : seulement si le brief le dit) — « Fiche suivi de parc auto »
- utilisateur / EtatDesLieuxEntree : tient le registre (supprimer : seulement si le brief le dit) — « Fiche état des lieux d’entrée »
- utilisateur / EtatDesLieuxSortie : tient le registre (supprimer : seulement si le brief le dit) — « Fiche état des lieux de sortie »
- utilisateur / Entretien : tient le registre (supprimer : seulement si le brief le dit) — « entretiens à venir »
- utilisateur / Cout : tient le registre (supprimer : seulement si le brief le dit) — « Calcul automatique des frais (entretien, réparation, assurance, amortissement »
- utilisateur / Planning : tient le registre (supprimer : seulement si le brief le dit) — « un état des lieux déclenche une mise à jour du planning »
