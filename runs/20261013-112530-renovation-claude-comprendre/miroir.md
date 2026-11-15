# Suivi des chantiers — ce que l'usine a compris

En bref : 2 rôles (Le dirigeant, Le chef de projet), 8 sortes de fiches, aucun circuit d'étapes.

## Le visiteur (sans compte)
- Ne voit rien

## Le dirigeant (responsable de l'app)
- Voit tout : Chantiers, Devis, Suivis de chantier (dans chaque Chantier), Documents (dans chaque Chantier), Photos (dans chaque Chantier), Bons de commande, Factures
- Voit tout, crée et modifie : Agences

## Le chef de projet (invité par dirigeant)
- Voit tout, crée et modifie : Chantiers, Devis, Bons de commande, Factures
- Voit tout, crée, modifie et supprime : Suivis de chantier (dans chaque Chantier), Documents (dans chaque Chantier), Photos (dans chaque Chantier)
- Voit tout : Agences

## Les informations de chaque fiche

- **Chantier** : Ville (texte court) · Avancement (%) (nombre) · Marge réalisée (montant, facultatif) · Rentabilité (%) (nombre, facultatif)
  - relié à : Agence
  - proposé (à cocher) : ☐ Nom du chantier (texte court) · ☐ Adresse du chantier (texte long) · ☐ Client (texte court) · ☐ Date de début (date) · ☐ Date de fin prévue (date) · ☐ Budget prévu (montant)
- **Devis** : Numéro du devis (texte court) ◦ choisi par nous
  - relié à : Chantier
  - proposé (à cocher) : ☐ Montant HT (montant) · ☐ Description des travaux (texte long) · ☐ Date de validité (date)
- **Suivi de chantier** : Intitulé (texte court) ◦ choisi par nous
  - relié à : dans chaque Chantier
  - proposé (à cocher) : ☐ Date du suivi (date) · ☐ Avancement constaté (%) (nombre) · ☐ Observations (texte long)
- **Document** : Nom du document (texte court) ◦ choisi par nous
  - relié à : dans chaque Chantier
  - proposé (à cocher) : ☐ Lien vers le fichier (lien web) · ☐ Type de document (texte court)
- **Photo** : Légende (texte court) ◦ choisi par nous
  - relié à : dans chaque Chantier
  - proposé (à cocher) : ☐ Lien vers l'image (lien web) · ☐ Date de prise de vue (date)
- **Bon de commande** : Numéro du bon de commande (texte court) ◦ choisi par nous
  - relié à : Chantier
  - proposé (à cocher) : ☐ Fournisseur (texte court) · ☐ Montant (montant) · ☐ Date de livraison souhaitée (date)
- **Facture** : Numéro de facture (texte court) ◦ choisi par nous
  - relié à : Chantier
  - proposé (à cocher) : ☐ Montant TTC (montant) · ☐ Date d'échéance (date) · ☐ Date de paiement (date)
- **Agence** : Nom de l'agence (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Ville (texte court) · ☐ Adresse (texte long) · ☐ Téléphone (téléphone)

## Questions

- Le chef de projet verra tous les Chantiers, pas seulement ceux qui le concernent — d'accord ? → **oui, nécessairement** : entité Chantier (registre) : il faut au moins un acteur qui le tient (« manager »)
- Le chef de projet verra tous les Devis, pas seulement ceux qui le concernent — d'accord ? → **oui, nécessairement** : entité Devis (registre) : il faut au moins un acteur qui le tient (« manager »)
- Le chef de projet verra tous les Bons de commande, pas seulement ceux qui le concernent — d'accord ? → **oui, nécessairement** : entité BonDeCommande (registre) : il faut au moins un acteur qui le tient (« manager »)
- Le chef de projet verra toutes les Factures, pas seulement celles qui le concernent — d'accord ? → **oui, nécessairement** : entité Facture (registre) : il faut au moins un acteur qui le tient (« manager »)
- Votre brief ne disait pas comment reconnaître certaines fiches ; nous avons choisi : Devis → « Numéro du devis » · Suivi de chantier → « Intitulé » · Document → « Nom du document » · Photo → « Légende » · Bon de commande → « Numéro du bon de commande » · Facture → « Numéro de facture » · Agence → « Nom de l'agence »

## Pas encore dans notre stock (vos mots)

- Joindre des documents et des photos aux chantiers — « devis, suivis, documents, photos »
- Automatiser les tâches répétitives et les processus — « L'automatisation des tâches répétitives ... Une centralisation et automatisation des processus et des données »
- Produire des devis, des bons de commande et des factures — « devis, bons de commande, facturation »
- Calculer et suivre les marges et la rentabilité par chantier, par ville et au global — « des marges réalisées ... Une visibilité sur les marges et la rentabilité par chantier, ville et globale »
- Utiliser l'outil sur téléphone mobile depuis le terrain, y compris hors ligne — « accessible depuis le terrain (mobile) ... Utilisation sur téléphone mobile indispensable, utilisable hors ligne »
- Communiquer entre les acteurs internes et externes — « L'amélioration de la communication interne et externe ... Une meilleure communication entre les acteurs internes et externes »
- Cloisonner les accès par agence — « Accès sécurisé et différencié par agence et rôle »

---

## Volet concepteur

### Pour répondre (`python -m usine.miroir repondre <lecture> id=valeur …`)

- `registre_entier:chef_de_projet:Chantier` = oui
- `registre_entier:chef_de_projet:Devis` = oui
- `registre_entier:chef_de_projet:BonDeCommande` = oui
- `registre_entier:chef_de_projet:Facture` = oui
- `nom:Devis:numero` = oui | <nouveau nom>  (Devis → « Numéro du devis »)
- `nom:SuiviChantier:intitule` = oui | <nouveau nom>  (Suivi de chantier → « Intitulé »)
- `nom:Document:nom` = oui | <nouveau nom>  (Document → « Nom du document »)
- `nom:Photo:legende` = oui | <nouveau nom>  (Photo → « Légende »)
- `nom:BonDeCommande:numero` = oui | <nouveau nom>  (Bon de commande → « Numéro du bon de commande »)
- `nom:Facture:numero` = oui | <nouveau nom>  (Facture → « Numéro de facture »)
- `nom:Agence:nom` = oui | <nouveau nom>  (Agence → « Nom de l'agence »)
- `garder:Chantier:Nom du chantier` = oui | non
- `garder:Chantier:Adresse du chantier` = oui | non
- `garder:Chantier:Client` = oui | non
- `garder:Chantier:Date de début` = oui | non
- `garder:Chantier:Date de fin prévue` = oui | non
- `garder:Chantier:Budget prévu` = oui | non
- `garder:Devis:Montant HT` = oui | non
- `garder:Devis:Description des travaux` = oui | non
- `garder:Devis:Date de validité` = oui | non
- `garder:SuiviChantier:Date du suivi` = oui | non
- `garder:SuiviChantier:Avancement constaté (%)` = oui | non
- `garder:SuiviChantier:Observations` = oui | non
- `garder:Document:Lien vers le fichier` = oui | non
- `garder:Document:Type de document` = oui | non
- `garder:Photo:Lien vers l'image` = oui | non
- `garder:Photo:Date de prise de vue` = oui | non
- `garder:BonDeCommande:Fournisseur` = oui | non
- `garder:BonDeCommande:Montant` = oui | non
- `garder:BonDeCommande:Date de livraison souhaitée` = oui | non
- `garder:Facture:Montant TTC` = oui | non
- `garder:Facture:Date d'échéance` = oui | non
- `garder:Facture:Date de paiement` = oui | non
- `garder:Agence:Ville` = oui | non
- `garder:Agence:Adresse` = oui | non
- `garder:Agence:Téléphone` = oui | non

### Pourquoi chaque droit

- dirigeant / Chantier : responsable de l'app : voit les registres de l'équipe (lecture) — « Le suivi de l'avancement des chantiers et des marges réalisées »
- dirigeant / Devis : responsable de l'app : voit les registres de l'équipe (lecture) — « La centralisation de l'ensemble des données chantiers (devis, suivis, documents, photos) »
- dirigeant / SuiviChantier : enfant de Chantier : même visibilité que le parent — « Le suivi de l'avancement des chantiers et des marges réalisées »
- dirigeant / Document : enfant de Chantier : même visibilité que le parent — « Le suivi de l'avancement des chantiers et des marges réalisées »
- dirigeant / Photo : enfant de Chantier : même visibilité que le parent — « Le suivi de l'avancement des chantiers et des marges réalisées »
- dirigeant / BonDeCommande : responsable de l'app : voit les registres de l'équipe (lecture) — « L'automatisation des tâches répétitives (devis, bons de commande, facturation) »
- dirigeant / Facture : responsable de l'app : voit les registres de l'équipe (lecture) — « L'automatisation des tâches répétitives (devis, bons de commande, facturation) »
- dirigeant / Agence : préréglage catalogue : visible de tous les connectés ; gestionnaire du catalogue (supprimer : seulement si le brief le dit) — « Accès sécurisé et différencié par agence et rôle »
- chef_de_projet / Chantier : tient le registre (supprimer : seulement si le brief le dit) — « Le suivi de l'avancement des chantiers et des marges réalisées »
- chef_de_projet / Devis : tient le registre (supprimer : seulement si le brief le dit) — « La centralisation de l'ensemble des données chantiers (devis, suivis, documents, photos) »
- chef_de_projet / BonDeCommande : tient le registre (supprimer : seulement si le brief le dit) — « L'automatisation des tâches répétitives (devis, bons de commande, facturation) »
- chef_de_projet / Facture : tient le registre (supprimer : seulement si le brief le dit) — « L'automatisation des tâches répétitives (devis, bons de commande, facturation) »
- chef_de_projet / SuiviChantier : enfant de Chantier : même visibilité que le parent, géré par qui gère le parent — « Le suivi de l'avancement des chantiers et des marges réalisées »
- chef_de_projet / Document : enfant de Chantier : même visibilité que le parent, géré par qui gère le parent — « Le suivi de l'avancement des chantiers et des marges réalisées »
- chef_de_projet / Photo : enfant de Chantier : même visibilité que le parent, géré par qui gère le parent — « Le suivi de l'avancement des chantiers et des marges réalisées »
- chef_de_projet / Agence : préréglage catalogue : visible de tous les connectés — « Accès sécurisé et différencié par agence et rôle »
