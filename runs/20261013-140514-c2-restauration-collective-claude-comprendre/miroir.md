# Restauration collective — ce que l'usine a compris

En bref : 2 rôles (L'administrateur, L'utilisateur), 8 sortes de fiches, aucun circuit d'étapes.

## Le visiteur (sans compte)
- Ne voit rien

## L'administrateur (responsable de l'app)
- Voit tout, crée et modifie : sites, articles, achats, inventaires, recettes, factures, dépenses, employés

## L'utilisateur (invité par administrateur)
- Voit tout : sites, articles, recettes
- Voit tout, crée et modifie : achats, inventaires, factures, dépenses

## Les informations de chaque fiche

- **Site** : Nom du site (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Adresse (texte long) · ☐ Responsable du site (texte court)
- **Article** : Nom de l'article (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Unité de mesure (texte court) · ☐ Prix unitaire (montant) · ☐ Seuil de stock minimum (nombre) · ☐ Catégorie (texte court)
- **Achat** : Référence (texte court) ◦ choisi par nous
  - relié à : site, article
  - proposé (à cocher) : ☐ Date d'achat (date) · ☐ Fournisseur (texte court) · ☐ Quantité (nombre) · ☐ Montant (montant)
- **Inventaire** : Intitulé (texte court) ◦ choisi par nous
  - relié à : site, article
  - proposé (à cocher) : ☐ Date de l'inventaire (date) · ☐ Quantité comptée (nombre) · ☐ Écart constaté (nombre)
- **Recette** : Nom de la recette (texte court) ◦ choisi par nous
  - relié à : article
  - proposé (à cocher) : ☐ Nombre de portions (nombre) · ☐ Coût par portion (montant) · ☐ Instructions de préparation (texte long)
- **Facture** : Numéro de facture (texte court) ◦ choisi par nous
  - relié à : site
  - proposé (à cocher) : ☐ Client facturé (texte court) · ☐ Date de facture (date) · ☐ Montant total (montant) · ☐ Date d'échéance (date)
- **Dépense** : Libellé (texte court) ◦ choisi par nous
  - relié à : site
  - proposé (à cocher) : ☐ Montant (montant) · ☐ Date de la dépense (date) · ☐ Catégorie (texte court) · ☐ Justificatif (texte court)
- **Employé** : Nom (texte court) ◦ choisi par nous
  - relié à : site
  - proposé (à cocher) : ☐ Prénom (texte court) · ☐ Poste (texte court) · ☐ Date d'embauche (date) · ☐ Téléphone (téléphone) · ☐ Email (e-mail)

## Questions

- L'utilisateur verra tous les achats, pas seulement ceux qui le concernent — d'accord ?
- L'utilisateur verra tous les inventaires, pas seulement ceux qui le concernent — d'accord ?
- L'utilisateur verra toutes les factures, pas seulement celles qui le concernent — d'accord ?
- L'utilisateur verra toutes les dépenses, pas seulement celles qui le concernent — d'accord ?
- Votre brief ne disait pas comment reconnaître certaines fiches ; nous avons choisi : site → « Nom du site » · article → « Nom de l'article » · achat → « Référence » · inventaire → « Intitulé » · recette → « Nom de la recette » · facture → « Numéro de facture » · dépense → « Libellé » · employé → « Nom »

## Pas encore dans notre stock (vos mots)

- Calcul du coût des repas — « coût des repas »
- Facturation — « facturation »
- Tableaux de bord consolidés — « tableaux de bord consolidés »
- Reporting détaillé par site et au niveau global — « reporting détaillé par site et au niveau global »
- Exports Excel et PDF — « des exports Excel/PDF sont requis »

---

## Volet concepteur

### Pour répondre (`python -m usine.miroir repondre <lecture> id=valeur …`)

- `registre_entier:utilisateur:Achat` = oui | non
- `registre_entier:utilisateur:Inventaire` = oui | non
- `registre_entier:utilisateur:Facture` = oui | non
- `registre_entier:utilisateur:Depense` = oui | non
- `nom:Site:nom` = oui | <nouveau nom>  (site → « Nom du site »)
- `nom:Article:nom` = oui | <nouveau nom>  (article → « Nom de l'article »)
- `nom:Achat:reference` = oui | <nouveau nom>  (achat → « Référence »)
- `nom:Inventaire:intitule` = oui | <nouveau nom>  (inventaire → « Intitulé »)
- `nom:Recette:nom` = oui | <nouveau nom>  (recette → « Nom de la recette »)
- `nom:Facture:numero` = oui | <nouveau nom>  (facture → « Numéro de facture »)
- `nom:Depense:libelle` = oui | <nouveau nom>  (dépense → « Libellé »)
- `nom:Employe:nom` = oui | <nouveau nom>  (employé → « Nom »)
- `garder:Site:Adresse` = oui | non
- `garder:Site:Responsable du site` = oui | non
- `garder:Article:Unité de mesure` = oui | non
- `garder:Article:Prix unitaire` = oui | non
- `garder:Article:Seuil de stock minimum` = oui | non
- `garder:Article:Catégorie` = oui | non
- `garder:Achat:Date d'achat` = oui | non
- `garder:Achat:Fournisseur` = oui | non
- `garder:Achat:Quantité` = oui | non
- `garder:Achat:Montant` = oui | non
- `garder:Inventaire:Date de l'inventaire` = oui | non
- `garder:Inventaire:Quantité comptée` = oui | non
- `garder:Inventaire:Écart constaté` = oui | non
- `garder:Recette:Nombre de portions` = oui | non
- `garder:Recette:Coût par portion` = oui | non
- `garder:Recette:Instructions de préparation` = oui | non
- `garder:Facture:Client facturé` = oui | non
- `garder:Facture:Date de facture` = oui | non
- `garder:Facture:Montant total` = oui | non
- `garder:Facture:Date d'échéance` = oui | non
- `garder:Depense:Montant` = oui | non
- `garder:Depense:Date de la dépense` = oui | non
- `garder:Depense:Catégorie` = oui | non
- `garder:Depense:Justificatif` = oui | non
- `garder:Employe:Prénom` = oui | non
- `garder:Employe:Poste` = oui | non
- `garder:Employe:Date d'embauche` = oui | non
- `garder:Employe:Téléphone` = oui | non
- `garder:Employe:Email` = oui | non

### Pourquoi chaque droit

- administrateur / Site : préréglage catalogue : visible de tous les connectés ; gestionnaire du catalogue (supprimer : seulement si le brief le dit) — « restauration collective multi-sites »
- administrateur / Article : préréglage catalogue : visible de tous les connectés ; gestionnaire du catalogue (supprimer : seulement si le brief le dit) — « la gestion des stocks »
- administrateur / Achat : tient le registre (supprimer : seulement si le brief le dit) — « gestion des stocks, achats »
- administrateur / Inventaire : tient le registre (supprimer : seulement si le brief le dit) — « achats, inventaires »
- administrateur / Recette : préréglage catalogue : visible de tous les connectés ; gestionnaire du catalogue (supprimer : seulement si le brief le dit) — « inventaires, recettes, coût des repas »
- administrateur / Facture : tient le registre (supprimer : seulement si le brief le dit) — « coût des repas, facturation »
- administrateur / Depense : tient le registre (supprimer : seulement si le brief le dit) — « facturation, dépenses »
- administrateur / Employe : tient le registre (supprimer : seulement si le brief le dit) — « dépenses, RH »
- utilisateur / Site : préréglage catalogue : visible de tous les connectés — « restauration collective multi-sites »
- utilisateur / Article : préréglage catalogue : visible de tous les connectés — « la gestion des stocks »
- utilisateur / Recette : préréglage catalogue : visible de tous les connectés — « inventaires, recettes, coût des repas »
- utilisateur / Achat : tient le registre (supprimer : seulement si le brief le dit) — « gestion des stocks, achats »
- utilisateur / Inventaire : tient le registre (supprimer : seulement si le brief le dit) — « achats, inventaires »
- utilisateur / Facture : tient le registre (supprimer : seulement si le brief le dit) — « coût des repas, facturation »
- utilisateur / Depense : tient le registre (supprimer : seulement si le brief le dit) — « facturation, dépenses »
