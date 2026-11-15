# Gestion du garage — ce que l'usine a compris

En bref : 2 rôles (Le gérant, L'employé), 5 sortes de fiches, 1 circuit d'étapes.

## Le visiteur (sans compte)
- Ne voit rien

## Le gérant (responsable de l'app)
- Voit tout, crée et modifie : Clients, Véhicules, Check-ups, Documents de réparation
- Voit tout, crée, modifie et supprime : Photos de pièces (dans chaque Check-up)

## L'employé (invité par gerant)
- Voit tout, crée et modifie : Clients, Véhicules, Check-ups
- Voit tout, crée, modifie et supprime : Photos de pièces (dans chaque Check-up)
- Documents de réparation : voit tout, en crée, les modifie, les fait passer de « à effectuer » à « terminée »

## Les étapes

- Le document de réparation passe par : « à effectuer » → « terminée »
  - L'employé fait passer de « à effectuer » à « terminée »

## Les informations de chaque fiche

- **Client** : Nom (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Prénom (texte court) · ☐ Téléphone (téléphone) · ☐ Email (e-mail) · ☐ Adresse (texte long)
- **Véhicule** : Immatriculation (texte court) ◦ choisi par nous
  - relié à : Client
  - proposé (à cocher) : ☐ Marque (texte court) · ☐ Modèle (texte court) · ☐ Kilométrage (nombre) · ☐ Date de réception (date) · ☐ Numéro de série (VIN) (texte court)
- **Check-up** : État de la mécanique (texte long)
  - relié à : Véhicule
  - proposé (à cocher) : ☐ Kilométrage relevé (nombre) · ☐ Conclusions / recommandations (texte long)
- **Photo de pièce** : Pièce (texte court) · Photo (lien web)
  - relié à : dans chaque Check-up
  - proposé (à cocher) : ☐ Description de la dégradation (texte long)
- **Document de réparation** : Réparations à effectuer (texte long)
  - relié à : Check-up, Véhicule
  - proposé (à cocher) : ☐ Rapport des travaux réalisés (texte long) · ☐ Date de fin de réparation (date) · ☐ Montant estimé (montant)

## Questions

- L'employé verra tous les Clients, pas seulement ceux qui le concernent — d'accord ? → **oui, nécessairement** : il doit les voir quand même — clôture : affiché dans les Véhicules qu'il voit; clôture : choisit les Clients de ses Véhicules
- L'employé verra tous les Véhicules, pas seulement ceux qui le concernent — d'accord ? → **oui, nécessairement** : il doit les voir quand même — clôture : affiché dans les Check-ups qu'il voit; clôture : choisit les Véhicules de ses Check-ups
- L'employé verra tous les Check-ups, pas seulement ceux qui le concernent — d'accord ? → **oui, nécessairement** : il doit les voir quand même — clôture : affiché dans les Documents de réparation qu'il voit; clôture : choisit les Check-ups de ses Documents de réparation
- L'employé verra tous les Documents de réparation, pas seulement ceux qui le concernent — d'accord ? → **oui, nécessairement** : entité DocumentReparation (registre) : l'initiateur (employe) doit être parmi ceux qui le tiennent
- Votre brief ne disait pas comment reconnaître certaines fiches ; nous avons choisi : Client → « Nom » · Véhicule → « Immatriculation »

## Pas encore dans notre stock (vos mots)

- Photos des pièces dégradées lors du check-up — « photo des pièces qui sont dégradé »
- Rapport de check-up imprimable à présenter au client — « le rapport sera imprimable afin de pouvoir présenter au client le rapport des traveaux »
- Génération d'un document des réparations à effectuer à partir du check-up — « génération d'un document de réparation à effectuer en fonction du checkup »

---

## Volet concepteur

### Pour répondre (`python -m usine.miroir repondre <lecture> id=valeur …`)

- `registre_entier:employe:Client` = oui
- `registre_entier:employe:Vehicule` = oui
- `registre_entier:employe:Checkup` = oui
- `registre_entier:employe:DocumentReparation` = oui
- `nom:Client:nom` = oui | <nouveau nom>  (Client → « Nom »)
- `nom:Vehicule:immatriculation` = oui | <nouveau nom>  (Véhicule → « Immatriculation »)
- `garder:Client:Prénom` = oui | non
- `garder:Client:Téléphone` = oui | non
- `garder:Client:Email` = oui | non
- `garder:Client:Adresse` = oui | non
- `garder:Vehicule:Marque` = oui | non
- `garder:Vehicule:Modèle` = oui | non
- `garder:Vehicule:Kilométrage` = oui | non
- `garder:Vehicule:Date de réception` = oui | non
- `garder:Vehicule:Numéro de série (VIN)` = oui | non
- `garder:Checkup:Kilométrage relevé` = oui | non
- `garder:Checkup:Conclusions / recommandations` = oui | non
- `garder:PhotoPiece:Description de la dégradation` = oui | non
- `garder:DocumentReparation:Rapport des travaux réalisés` = oui | non
- `garder:DocumentReparation:Date de fin de réparation` = oui | non
- `garder:DocumentReparation:Montant estimé` = oui | non

### Pourquoi chaque droit

- gerant / Client : tient le registre (supprimer : seulement si le brief le dit) — « présenter au client le rapport des traveaux »
- gerant / Vehicule : tient le registre (supprimer : seulement si le brief le dit) — « la réception du véhicule »
- gerant / Checkup : tient le registre (supprimer : seulement si le brief le dit) — « un check complet de l'état de la mécanique de la voiture »
- gerant / DocumentReparation : tient le registre (supprimer : seulement si le brief le dit) — « génération d'un document de réparation à effectuer en fonction du checkup »
- gerant / PhotoPiece : enfant de Check-up : même visibilité que le parent, géré par qui gère le parent — « un check complet de l'état de la mécanique de la voiture »
- employe / Client : tient le registre (supprimer : seulement si le brief le dit) — « présenter au client le rapport des traveaux »
- employe / Vehicule : tient le registre (supprimer : seulement si le brief le dit) — « la réception du véhicule »
- employe / Checkup : tient le registre (supprimer : seulement si le brief le dit) — « un check complet de l'état de la mécanique de la voiture »
- employe / PhotoPiece : enfant de Check-up : même visibilité que le parent, géré par qui gère le parent — « un check complet de l'état de la mécanique de la voiture »
- employe / DocumentReparation : tient le registre (supprimer : seulement si le brief le dit) ; fait évoluer l'état des fiches du registre — « génération d'un document de réparation à effectuer en fonction du checkup » « génération d'un document de réparation à effectuer en fonction du checkup, confirmation de la fin de la réparation »
