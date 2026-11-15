# Gestion du bâtiment — ce que l'usine a compris

En bref : 2 rôles (Le gérant, Le conducteur de travaux), 7 sortes de fiches, aucun circuit d'étapes.

## Le visiteur (sans compte)
- Ne voit rien

## Le gérant (responsable de l'app)
- Voit tout, crée et modifie : clients, marchandises, mouvements de stock, devis, factures
- Voit tout : chantiers, comptes rendus de chantier (dans chaque chantier)

## Le conducteur de travaux (invité par gerant)
- Voit tout, crée et modifie : chantiers
- Voit tout, crée, modifie et supprime : comptes rendus de chantier (dans chaque chantier)

## Les informations de chaque fiche

- **Client** : Nom (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Type de client (choix) · ☐ Adresse (texte court) · ☐ Email (e-mail) · ☐ Téléphone (téléphone)
- **Marchandise** : Nom (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Unité (texte court) · ☐ Quantité en stock (nombre) · ☐ Seuil d'alerte (nombre)
- **Mouvement de stock** : Type de mouvement (choix parmi : entrée, sortie)
  - relié à : marchandise
  - proposé (à cocher) : ☐ Quantité (nombre) · ☐ Date du mouvement (date) · ☐ Chantier concerné (texte court)
- **Devis** : Intitulé (texte court) ◦ choisi par nous
  - relié à : client
  - proposé (à cocher) : ☐ Montant total (montant) · ☐ Date de validité (date) · ☐ Description des travaux (texte long)
- **Facture** : Numéro de facture (texte court) ◦ choisi par nous
  - relié à : client
  - proposé (à cocher) : ☐ Montant (montant) · ☐ Date d'échéance (date) · ☐ Date de paiement (date)
- **Chantier** : Nom du chantier (texte court) ◦ choisi par nous · Avancement (nombre) · Délais (texte court) · Organisation des domaines d'application (texte long)
  - proposé (à cocher) : ☐ Adresse du chantier (texte court) · ☐ Date de début (date) · ☐ Date de fin prévue (date)
- **Compte rendu de chantier** : Intitulé (texte court) ◦ choisi par nous
  - relié à : dans chaque chantier
  - proposé (à cocher) : ☐ Date du compte rendu (date) · ☐ Contenu (texte long)

## Questions

- Le conducteur de travaux verra tous les chantiers, pas seulement ceux qui le concernent — d'accord ? → **oui, nécessairement** : entité Chantier (registre) : il faut au moins un acteur qui le tient (« manager »)
- Votre brief ne disait pas comment reconnaître certaines fiches ; nous avons choisi : client → « Nom » · marchandise → « Nom » · devis → « Intitulé » · facture → « Numéro de facture » · chantier → « Nom du chantier » · compte rendu de chantier → « Intitulé »

## Pas encore dans notre stock (vos mots)

- Devis et facturation pour les clients professionnels et particuliers — « réaliser des devis, et gérer la partie facturation »
- Site internet pour présenter le savoir-faire de l'entreprise — « Création d’un site internet »
- Devis en ligne que les clients particuliers établissent eux-mêmes sur le site — « la possibilité d’établir un devis en ligne à nos clients particuliers »
- Application de suivi de chantiers aussi disponible sur mobile — « La création d’une application (web et mobile) »

---

## Volet concepteur

### Pour répondre (`python -m usine.miroir repondre <lecture> id=valeur …`)

- `registre_entier:conducteur_travaux:Chantier` = oui
- `nom:Client:nom` = oui | <nouveau nom>  (client → « Nom »)
- `nom:Marchandise:nom` = oui | <nouveau nom>  (marchandise → « Nom »)
- `nom:Devis:intitule` = oui | <nouveau nom>  (devis → « Intitulé »)
- `nom:Facture:numero` = oui | <nouveau nom>  (facture → « Numéro de facture »)
- `nom:Chantier:nom` = oui | <nouveau nom>  (chantier → « Nom du chantier »)
- `nom:CompteRenduChantier:intitule` = oui | <nouveau nom>  (compte rendu de chantier → « Intitulé »)
- `garder:Client:Type de client` = oui | non
- `garder:Client:Adresse` = oui | non
- `garder:Client:Email` = oui | non
- `garder:Client:Téléphone` = oui | non
- `garder:Marchandise:Unité` = oui | non
- `garder:Marchandise:Quantité en stock` = oui | non
- `garder:Marchandise:Seuil d'alerte` = oui | non
- `garder:MouvementStock:Quantité` = oui | non
- `garder:MouvementStock:Date du mouvement` = oui | non
- `garder:MouvementStock:Chantier concerné` = oui | non
- `garder:Devis:Montant total` = oui | non
- `garder:Devis:Date de validité` = oui | non
- `garder:Devis:Description des travaux` = oui | non
- `garder:Facture:Montant` = oui | non
- `garder:Facture:Date d'échéance` = oui | non
- `garder:Facture:Date de paiement` = oui | non
- `garder:Chantier:Adresse du chantier` = oui | non
- `garder:Chantier:Date de début` = oui | non
- `garder:Chantier:Date de fin prévue` = oui | non
- `garder:CompteRenduChantier:Date du compte rendu` = oui | non
- `garder:CompteRenduChantier:Contenu` = oui | non

### Pourquoi chaque droit

- gerant / Client : tient le registre (supprimer : seulement si le brief le dit) — « nos clients professionnels et particuliers »
- gerant / Marchandise : tient le registre (supprimer : seulement si le brief le dit) — « marchandises qui serviront à nos chantiers »
- gerant / MouvementStock : tient le registre (supprimer : seulement si le brief le dit) — « contrôler les entrées et les sorties des marchandises »
- gerant / Devis : tient le registre (supprimer : seulement si le brief le dit) — « réaliser des devis »
- gerant / Facture : tient le registre (supprimer : seulement si le brief le dit) — « gérer la partie facturation pour nos clients professionnels et particuliers »
- gerant / Chantier : responsable de l'app : voit les registres de l'équipe (lecture) — « suivi de nos chantiers »
- gerant / CompteRenduChantier : enfant de chantier : même visibilité que le parent — « suivi de nos chantiers »
- conducteur_travaux / Chantier : tient le registre (supprimer : seulement si le brief le dit) — « suivi de nos chantiers »
- conducteur_travaux / CompteRenduChantier : enfant de chantier : même visibilité que le parent, géré par qui gère le parent — « suivi de nos chantiers »
