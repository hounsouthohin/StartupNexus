# Gestion BTP — ce que l'usine a compris

En bref : 2 rôles (Le gérant, Le conducteur de travaux), 7 sortes de fiches, aucun circuit d'étapes.

## Le visiteur (sans compte)
- Ne voit rien

## Le gérant (responsable de l'app)
- Voit tout, crée et modifie : Marchandises, Mouvements de stock, Clients, Devis, Factures, Chantiers
- Voit tout, crée, modifie et supprime : Rapports de chantier (dans chaque Chantier)

## Le conducteur de travaux (invité par gerant)
- Voit tout, crée et modifie : Chantiers
- Voit tout, crée, modifie et supprime : Rapports de chantier (dans chaque Chantier)

## Les informations de chaque fiche

- **Marchandise** : Nom (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Unité (sac, tonne, pièce…) (texte court) · ☐ Quantité en stock (nombre) · ☐ Seuil d'alerte (nombre) · ☐ Prix d'achat unitaire (montant)
- **Mouvement de stock** : Sens du mouvement (choix parmi : entrée, sortie)
  - relié à : Marchandise, Chantier
  - proposé (à cocher) : ☐ Quantité (nombre) · ☐ Date du mouvement (date) · ☐ Fournisseur (texte court)
- **Client** : Nom (texte court) ◦ choisi par nous · Type de client (choix parmi : professionnel, particulier)
  - proposé (à cocher) : ☐ Valeur « petit promoteur immobilier » pour le type de client (choix) · ☐ Adresse (texte long) · ☐ Email (e-mail) · ☐ Téléphone (téléphone) · ☐ Numéro SIRET (texte court)
- **Devis** : Intitulé (texte court) ◦ choisi par nous
  - relié à : Client
  - proposé (à cocher) : ☐ Description des travaux (texte long) · ☐ Montant HT (montant) · ☐ Taux de TVA (nombre) · ☐ Date de validité (date) · ☐ Demandé en ligne (oui / non)
- **Facture** : Numéro de facture (texte court) ◦ choisi par nous
  - relié à : Client
  - proposé (à cocher) : ☐ Montant HT (montant) · ☐ Taux de TVA (nombre) · ☐ Date d'échéance (date) · ☐ Date de paiement (date)
- **Chantier** : Nom du chantier (texte court) ◦ choisi par nous · Avancement (%) (nombre) · Délai (date de fin prévue) (date) · Organisation des domaines d'application (texte long)
  - proposé (à cocher) : ☐ Adresse du chantier (texte long) · ☐ Date de début (date) · ☐ Domaine (gros œuvre, 2nd œuvre) (choix) · ☐ Budget (montant)
- **Rapport de chantier** : Type de document (choix parmi : C/R, rapport)
  - relié à : dans chaque Chantier
  - proposé (à cocher) : ☐ Intitulé (texte court) · ☐ Date de la visite (date) · ☐ Contenu (texte long) · ☐ Photos (lien web)

## Questions

- Le conducteur de travaux verra tous les Chantiers, pas seulement ceux qui le concernent — d'accord ?
- Votre brief ne disait pas comment reconnaître certaines fiches ; nous avons choisi : Marchandise → « Nom » · Client → « Nom » · Devis → « Intitulé » · Facture → « Numéro de facture » · Chantier → « Nom du chantier »

## Pas encore dans notre stock (vos mots)

- Calcul des quantités en stock à partir des entrées et des sorties de marchandises — « mieux contrôler les entrées et les sorties des marchandises »
- Production de devis (documents chiffrés avec calcul des montants) — « La création d’un outil pour réaliser des devis »
- Facturation des clients professionnels et particuliers (factures, montants) — « gérer la partie facturation pour nos clients professionnels et particuliers »
- Site internet vitrine pour présenter le savoir-faire — « Création d’un site internet (afin de mettre en avant notre savoir-faire »
- Devis en ligne pour les particuliers depuis le site internet — « proposer la possibilité d’établir un devis en ligne à nos clients particuliers »
- Application mobile pour le suivi de chantier — « La création d’une application (web et mobile) »
- Suivi des délais et organisation des corps de métier sur les chantiers — « les délais, l’organisation des différents domaines d’application »
- Comptes rendus et rapports de chantier — « C/R, rapports »

---

## Volet concepteur

### Pour répondre (`python -m usine.miroir repondre <lecture> id=valeur …`)

- `registre_entier:conducteur_travaux:Chantier` = oui | non
- `nom:Marchandise:nom` = oui | <nouveau nom>  (Marchandise → « Nom »)
- `nom:Client:nom` = oui | <nouveau nom>  (Client → « Nom »)
- `nom:Devis:intitule` = oui | <nouveau nom>  (Devis → « Intitulé »)
- `nom:Facture:numero` = oui | <nouveau nom>  (Facture → « Numéro de facture »)
- `nom:Chantier:nom` = oui | <nouveau nom>  (Chantier → « Nom du chantier »)
- `garder:Marchandise:Unité (sac, tonne, pièce…)` = oui | non
- `garder:Marchandise:Quantité en stock` = oui | non
- `garder:Marchandise:Seuil d'alerte` = oui | non
- `garder:Marchandise:Prix d'achat unitaire` = oui | non
- `garder:MouvementStock:Quantité` = oui | non
- `garder:MouvementStock:Date du mouvement` = oui | non
- `garder:MouvementStock:Fournisseur` = oui | non
- `garder:Client:Valeur « petit promoteur immobilier » pour le type de client` = oui | non
- `garder:Client:Adresse` = oui | non
- `garder:Client:Email` = oui | non
- `garder:Client:Téléphone` = oui | non
- `garder:Client:Numéro SIRET` = oui | non
- `garder:Devis:Description des travaux` = oui | non
- `garder:Devis:Montant HT` = oui | non
- `garder:Devis:Taux de TVA` = oui | non
- `garder:Devis:Date de validité` = oui | non
- `garder:Devis:Demandé en ligne` = oui | non
- `garder:Facture:Montant HT` = oui | non
- `garder:Facture:Taux de TVA` = oui | non
- `garder:Facture:Date d'échéance` = oui | non
- `garder:Facture:Date de paiement` = oui | non
- `garder:Chantier:Adresse du chantier` = oui | non
- `garder:Chantier:Date de début` = oui | non
- `garder:Chantier:Domaine (gros œuvre, 2nd œuvre)` = oui | non
- `garder:Chantier:Budget` = oui | non
- `garder:RapportChantier:Intitulé` = oui | non
- `garder:RapportChantier:Date de la visite` = oui | non
- `garder:RapportChantier:Contenu` = oui | non
- `garder:RapportChantier:Photos` = oui | non

### Pourquoi chaque droit

- gerant / Marchandise : tient le registre (supprimer : seulement si le brief le dit) — « marchandises qui serviront à nos chantiers (sac de colle à carrelage, ciment, parpaing »
- gerant / MouvementStock : tient le registre (supprimer : seulement si le brief le dit) — « contrôler les entrées et les sorties des marchandises qui serviront à nos chantiers »
- gerant / Client : tient le registre (supprimer : seulement si le brief le dit) — « nos clients professionnels et particuliers (également petits promoteurs immobiliers et clients particuliers) »
- gerant / Devis : tient le registre (supprimer : seulement si le brief le dit) — « établir un devis en ligne à nos clients particuliers »
- gerant / Facture : tient le registre (supprimer : seulement si le brief le dit) — « gérer la partie facturation pour nos clients professionnels et particuliers »
- gerant / Chantier : tient le registre (supprimer : seulement si le brief le dit) — « le suivi de nos chantiers (afin de connaître leur avancement, les délais »
- gerant / RapportChantier : enfant de Chantier : même visibilité que le parent, géré par qui gère le parent — « le suivi de nos chantiers (afin de connaître leur avancement, les délais »
- conducteur_travaux / Chantier : tient le registre (supprimer : seulement si le brief le dit) ; exception : « pour le suivi de nos chantiers (afin de connaître leur avancement » — « le suivi de nos chantiers (afin de connaître leur avancement, les délais » « pour le suivi de nos chantiers (afin de connaître leur avancement »
- conducteur_travaux / RapportChantier : enfant de Chantier : même visibilité que le parent, géré par qui gère le parent — « le suivi de nos chantiers (afin de connaître leur avancement, les délais » « pour le suivi de nos chantiers (afin de connaître leur avancement »
