# Gestion BTP — ce que l'usine a compris

En bref : 2 rôles (L'administrateur, Le conducteur de travaux), 8 sortes de fiches, aucun circuit d'étapes.

## Le visiteur (sans compte)
- Voit tout : devis
- voit les clients affichés dans les devis qu'il consulte (sans page à part)

## L'administrateur (responsable de l'app)
- Voit tout, crée et modifie : clients, marchandises, entrées de stock, sorties de stock, devis, factures
- Voit tout : chantiers, rapports de chantier (dans chaque chantier)

## Le conducteur de travaux (invité par administrateur)
- Voit tout : devis
- Voit tout, crée et modifie : chantiers
- Voit tout, crée, modifie et supprime : rapports de chantier (dans chaque chantier)
- voit les clients affichés dans les devis qu'il consulte (sans page à part)

## Les informations de chaque fiche

- **Client** : Type de client (choix parmi : professionnels, particuliers, petits promoteurs immobiliers)
  - proposé (à cocher) : ☐ Nom du client (texte court) · ☐ Adresse email (e-mail) · ☐ Téléphone (téléphone)
- **Marchandise** : Nom (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Unité de mesure (texte court) · ☐ Stock minimum (nombre)
- **Entrée de stock** : Intitulé (texte court) ◦ choisi par nous
  - relié à : marchandise
  - proposé (à cocher) : ☐ Quantité entrée (nombre) · ☐ Date d’entrée (date)
- **Sortie de stock** : Intitulé (texte court) ◦ choisi par nous
  - relié à : marchandise, chantier
  - proposé (à cocher) : ☐ Quantité sortie (nombre) · ☐ Date de sortie (date)
- **Devis** : Intitulé (texte court) ◦ choisi par nous
  - relié à : client
  - proposé (à cocher) : ☐ Numéro de devis (texte court) · ☐ Montant total (montant) · ☐ Date de validité (date)
- **Facture** : Intitulé (texte court) ◦ choisi par nous
  - relié à : client
  - proposé (à cocher) : ☐ Numéro de facture (texte court) · ☐ Montant total (montant) · ☐ Date d’échéance (date)
- **Chantier** : Avancement (texte court) · Délais (texte court) · Organisation des différents domaines d’application (texte long)
  - proposé (à cocher) : ☐ Nom du chantier (texte court) · ☐ Adresse du chantier (texte court) · ☐ Date de début prévue (date)
- **Rapport de chantier** : Intitulé (texte court) ◦ choisi par nous
  - relié à : dans chaque chantier
  - proposé (à cocher) : ☐ Contenu du rapport (texte long) · ☐ Date du rapport (date)

## Questions

- Les visiteurs sans compte pourront consulter tous les devis — d'accord ? (si certains ne doivent pas être visibles, par exemple des brouillons, répondez non)
- Le conducteur de travaux verra les clients (ex. nom, coordonnées) affichés dans les devis qu'il traite — est-ce acceptable ? → **oui, nécessairement** : il doit les voir quand même — clôture : affiché dans les devis qu'il voit
- Le conducteur de travaux verra tous les devis, pas seulement ceux qui le concernent — d'accord ?
- Le conducteur de travaux verra tous les chantiers, pas seulement ceux qui le concernent — d'accord ? → **oui, nécessairement** : entité Chantier (registre) : il faut au moins un acteur qui le tient (« manager »)
- Votre brief ne disait pas comment reconnaître certaines fiches ; nous avons choisi : marchandise → « Nom » · entrée de stock → « Intitulé » · sortie de stock → « Intitulé » · devis → « Intitulé » · facture → « Intitulé » · rapport de chantier → « Intitulé »

## Pas encore dans notre stock (vos mots)

- Gestion de stock avec contrôle des entrées et sorties de marchandises — « application de gestion des stock (pour mieux contrôler les entrées et les sorties des marchandises »
- Réalisation de devis — « un outil pour réaliser des devis »
- Facturation clients — « gérer la partie facturation pour nos clients professionnels et particuliers »
- Site internet vitrine — « Création d’un site internet (afin de mettre en avant notre savoir-faire »
- Devis en ligne pour les clients particuliers — « proposer la possibilité d’établir un devis en ligne à nos clients particuliers »
- Application mobile — « une application (web et mobile) »
- Gestion des délais et de l’organisation des chantiers — « les délais, l’organisation des différents domaines d’application »
- Comptes-rendus et rapports de chantier — « C/R, rapports »

---

## Volet concepteur

### Pour répondre (`python -m usine.miroir repondre <lecture> id=valeur …`)

- `visiteur:visitor:Devis` = oui | non
- `vu_via:conducteur_de_travaux:Client` = oui
- `registre_entier:conducteur_de_travaux:Devis` = oui | non
- `registre_entier:conducteur_de_travaux:Chantier` = oui
- `nom:Marchandise:nom` = oui | <nouveau nom>  (marchandise → « Nom »)
- `nom:EntreeStock:intitule` = oui | <nouveau nom>  (entrée de stock → « Intitulé »)
- `nom:SortieStock:intitule` = oui | <nouveau nom>  (sortie de stock → « Intitulé »)
- `nom:Devis:intitule` = oui | <nouveau nom>  (devis → « Intitulé »)
- `nom:Facture:intitule` = oui | <nouveau nom>  (facture → « Intitulé »)
- `nom:RapportChantier:intitule` = oui | <nouveau nom>  (rapport de chantier → « Intitulé »)
- `garder:Client:Nom du client` = oui | non
- `garder:Client:Adresse email` = oui | non
- `garder:Client:Téléphone` = oui | non
- `garder:Marchandise:Unité de mesure` = oui | non
- `garder:Marchandise:Stock minimum` = oui | non
- `garder:EntreeStock:Quantité entrée` = oui | non
- `garder:EntreeStock:Date d’entrée` = oui | non
- `garder:SortieStock:Quantité sortie` = oui | non
- `garder:SortieStock:Date de sortie` = oui | non
- `garder:Devis:Numéro de devis` = oui | non
- `garder:Devis:Montant total` = oui | non
- `garder:Devis:Date de validité` = oui | non
- `garder:Facture:Numéro de facture` = oui | non
- `garder:Facture:Montant total` = oui | non
- `garder:Facture:Date d’échéance` = oui | non
- `garder:Chantier:Nom du chantier` = oui | non
- `garder:Chantier:Adresse du chantier` = oui | non
- `garder:Chantier:Date de début prévue` = oui | non
- `garder:RapportChantier:Contenu du rapport` = oui | non
- `garder:RapportChantier:Date du rapport` = oui | non

### Pourquoi chaque droit

- visitor / Devis : registre public : visible de tous — « établir un devis en ligne à nos clients particuliers »
- visitor / Client : clôture : affiché dans les devis qu'il voit
- administrateur / Client : tient le registre (supprimer : seulement si le brief le dit) — « clients professionnels et particuliers (également petits promoteurs immobiliers et clients particuliers) »
- administrateur / Marchandise : tient le registre (supprimer : seulement si le brief le dit) — « marchandises qui serviront à nos chantiers (sac de colle à carrelage, ciment, parpaing »
- administrateur / EntreeStock : tient le registre (supprimer : seulement si le brief le dit) — « contrôler les entrées et les sorties des marchandises »
- administrateur / SortieStock : tient le registre (supprimer : seulement si le brief le dit) — « sorties des marchandises qui serviront à nos chantiers »
- administrateur / Devis : tient le registre (supprimer : seulement si le brief le dit) — « établir un devis en ligne à nos clients particuliers »
- administrateur / Facture : tient le registre (supprimer : seulement si le brief le dit) — « gérer la partie facturation pour nos clients professionnels et particuliers »
- administrateur / Chantier : responsable de l'app : voit les registres de l'équipe (lecture) — « suivi de nos chantiers »
- administrateur / RapportChantier : enfant de chantier : même visibilité que le parent — « suivi de nos chantiers »
- conducteur_de_travaux / Devis : registre public : visible de tous — « établir un devis en ligne à nos clients particuliers »
- conducteur_de_travaux / Chantier : tient le registre (supprimer : seulement si le brief le dit) ; exception : « pour le suivi de nos chantiers (afin de connaître leur avancement, les délais » — « suivi de nos chantiers » « pour le suivi de nos chantiers (afin de connaître leur avancement, les délais »
- conducteur_de_travaux / RapportChantier : exception : « ) pour nos conducteurs de travaux » ; enfant de chantier : même visibilité que le parent, géré par qui gère le parent — « ) pour nos conducteurs de travaux » « suivi de nos chantiers » « pour le suivi de nos chantiers (afin de connaître leur avancement, les délais »
- conducteur_de_travaux / Client : clôture : affiché dans les devis qu'il voit
