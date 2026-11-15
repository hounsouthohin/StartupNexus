# Gestion du restaurant — ce que l'usine a compris

En bref : 5 rôles (L'administrateur, Le serveur, Le caissier, Le cuisinier, Le livreur), 14 sortes de fiches, 2 circuits d'étapes.

## Le visiteur (sans compte)
- Ne voit rien

## L'administrateur (responsable de l'app)
- Voit tout, crée et modifie : Tables, Catégories, Produits, Clients, Commandes, Paiements, Factures, Livraisons, Réservations, Fournisseurs, Articles en stock
- Voit tout, crée, modifie et supprime : Variantes (dans chaque Produit), Lignes de commande (dans chaque Commande), Mouvements de stock (dans chaque Article en stock)

## Le serveur (invité par administrateur)
- Voit tout : Tables, Catégories, Produits, Variantes (dans chaque Produit)
- Voit tout, crée et modifie : Clients, Commandes
- Voit tout, crée, modifie et supprime : Lignes de commande (dans chaque Commande)
- Réservations : voit tout, en crée, les modifie, les fait passer de « demandée » à « confirmée » ou « annulée », les fait passer de « confirmée » à « annulée »

## Le caissier (invité par administrateur)
- Voit tout : Tables, Catégories, Produits, Variantes (dans chaque Produit)
- Voit tout, crée et modifie : Clients, Commandes, Paiements, Factures
- Voit tout, crée, modifie et supprime : Lignes de commande (dans chaque Commande)

## Le cuisinier (invité par administrateur)
- Voit tout : Tables, Catégories, Produits, Variantes (dans chaque Produit), Clients
- Voit tout, crée et modifie : Commandes
- Voit tout, crée, modifie et supprime : Lignes de commande (dans chaque Commande)

## Le livreur (invité par administrateur)
- Voit tout : Tables, Catégories, Produits, Variantes (dans chaque Produit), Commandes
- Livraisons : voit tout, en crée, les modifie, les fait passer de « en attente » à « en cours de livraison », les fait passer de « en cours de livraison » à « livrée »

## Les étapes

- La livraison passe par : « en attente » → « en cours de livraison » → « livrée »
  - Le livreur fait passer de « en attente » à « en cours de livraison »
  - Le livreur fait passer de « en cours de livraison » à « livrée »
- La réservation commence « demandée » ; de « demandée », vers « confirmée » ou « annulée » ; de « confirmée », vers « annulée »
  - Le serveur fait passer de « demandée » à « confirmée » ou « annulée »
  - Le serveur fait passer de « confirmée » à « annulée »

## Les informations de chaque fiche

- **Table** : Numéro de table (texte court) ◦ choisi par nous · Statut (choix parmi : libre, occupée, réservée, en attente de paiement)
  - proposé (à cocher) : ☐ Nombre de places (nombre) · ☐ Position sur le plan de salle (texte court)
- **Catégorie** : Nom de la catégorie (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Ordre d'affichage dans le menu (nombre)
- **Produit** : Prix (montant) · Disponible (oui / non) · Actif (non désactivé) (oui / non)
  - relié à : Catégorie
  - proposé (à cocher) : ☐ Nom du produit (texte court) · ☐ Description (texte long)
- **Variante** : Nom de la variante (texte court) ◦ choisi par nous
  - relié à : dans chaque Produit
  - proposé (à cocher) : ☐ Type de variante (ex. cuisson, taille) (texte court) · ☐ Supplément de prix (montant)
- **Client** : Nom (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Téléphone (téléphone) · ☐ Email (e-mail) · ☐ Adresse (texte long)
- **Commande** : Type de commande (hors salle) (choix parmi : à emporter, livraison, facultatif)
  - relié à : Table, Client
  - proposé (à cocher) : ☐ Nombre de couverts (nombre) · ☐ Note pour la cuisine (texte long)
- **Ligne de commande** : Quantité (nombre)
  - relié à : dans chaque Commande, Produit, Variante
  - proposé (à cocher) : ☐ Prix unitaire appliqué (montant) · ☐ Remarque (texte court)
- **Paiement** : Mode de paiement (choix parmi : espèce, carte, mobile money)
  - relié à : Commande
  - proposé (à cocher) : ☐ Montant payé (montant) · ☐ Référence de transaction (texte court)
- **Facture** : Numéro de facture (texte court) ◦ choisi par nous
  - relié à : Commande
  - proposé (à cocher) : ☐ Montant total (montant)
- **Livraison** : Livreur (texte court, facultatif)
  - relié à : Commande
  - proposé (à cocher) : ☐ Adresse de livraison (texte long) · ☐ Téléphone de contact (téléphone) · ☐ Frais de livraison (montant) · ☐ Heure de livraison prévue (date et heure)
- **Réservation** : Canal de réservation (choix parmi : manuelle, interface publique)
  - relié à : Client, Table
  - proposé (à cocher) : ☐ Date et heure de la réservation (date et heure) · ☐ Nombre de personnes (nombre) · ☐ Commentaire (texte long)
- **Fournisseur** : Nom du fournisseur (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Téléphone (téléphone) · ☐ Email (e-mail) · ☐ Adresse (texte long)
- **Article en stock** : Nom de l'article (texte court) ◦ choisi par nous · Quantité en stock (nombre) · Seuil critique (nombre)
  - proposé (à cocher) : ☐ Unité de mesure (texte court)
- **Mouvement de stock** : Type de mouvement (choix parmi : entrée, sortie)
  - relié à : dans chaque Article en stock, Fournisseur
  - proposé (à cocher) : ☐ Quantité (nombre) · ☐ Motif (texte court)

## Questions

- Le serveur verra tous les Clients, pas seulement ceux qui le concernent — d'accord ? → **oui, nécessairement** : il doit les voir quand même — clôture : affiché dans les Commandes qu'il voit; clôture : choisit les Clients de ses Commandes
- Le serveur verra toutes les Commandes, pas seulement celles qui le concernent — d'accord ?
- Le serveur verra toutes les Réservations, pas seulement celles qui le concernent — d'accord ? → **oui, nécessairement** : entité Reservation (registre) : l'initiateur (serveur) doit être parmi ceux qui le tiennent
- Le caissier verra tous les Clients, pas seulement ceux qui le concernent — d'accord ? → **oui, nécessairement** : il doit les voir quand même — clôture : affiché dans les Commandes qu'il voit; clôture : choisit les Clients de ses Commandes
- Le caissier verra toutes les Commandes, pas seulement celles qui le concernent — d'accord ? → **oui, nécessairement** : il doit les voir quand même — clôture : affiché dans les Paiements qu'il voit; clôture : choisit les Commandes de ses Paiements
- Le caissier verra tous les Paiements, pas seulement ceux qui le concernent — d'accord ?
- Le caissier verra toutes les Factures, pas seulement celles qui le concernent — d'accord ?
- Le cuisinier verra tous les Clients, pas seulement ceux qui le concernent — d'accord ? → **oui, nécessairement** : il doit les voir quand même — clôture : affiché dans les Commandes qu'il voit; clôture : choisit les Clients de ses Commandes
- Le cuisinier verra toutes les Commandes, pas seulement celles qui le concernent — d'accord ?
- Le livreur verra toutes les Commandes, pas seulement celles qui le concernent — d'accord ? → **oui, nécessairement** : il doit les voir quand même — clôture : affiché dans les Livraisons qu'il voit; clôture : choisit les Commandes de ses Livraisons
- Le livreur verra toutes les Livraisons, pas seulement celles qui le concernent — d'accord ? → **oui, nécessairement** : entité Livraison (registre) : l'initiateur (livreur) doit être parmi ceux qui le tiennent
- Votre brief ne disait pas comment reconnaître certaines fiches ; nous avons choisi : Table → « Numéro de table » · Catégorie → « Nom de la catégorie » · Variante → « Nom de la variante » · Client → « Nom » · Facture → « Numéro de facture » · Fournisseur → « Nom du fournisseur » · Article en stock → « Nom de l'article »

## Pas encore dans notre stock (vos mots)

- Historique des connexions des utilisateurs — « Historique de connexion »
- Plan de salle visuel des tables — « Plan de salle visuel »
- Envoi automatique des commandes en cuisine, avec impression ou affichage à l'écran — « Envoi automatique en cuisine (impression ou affichage à l’écran) »
- Suivi des stocks en temps réel (quantités calculées) — « Suivi en temps réel des stocks »
- Alerte quand un stock passe sous un seuil critique — « Alerte de seuil critique »
- Encaissement par espèces, carte et mobile money — « Paiement par espèce, carte, mobile money »
- Facture imprimée ou en PDF — « Facture imprimée ou PDF »
- Diviser l'addition entre plusieurs clients — « Possibilité de diviser l’addition »
- Prise de réservation par le public via une interface publique — « Prise de réservation manuelle ou via une interface publique »
- Confirmation automatique des réservations — « Confirmation automatique »
- Rappel des réservations — « annulation, rappel »
- Chiffre d'affaires journalier et mensuel — « Chiffre d'affaires journalier, mensuel »
- Classement des produits les plus vendus — « Produits les plus vendus »
- Mesure de la performance du personnel — « Performance du personnel »
- Rapport de stock — « Rapport de stock »
- Application mobile native — « Mobile : Flutter ou React Native »
- Technologies imposées pour le back-end, le front-end et la base de données — « Back-end : Laravel (PHP), Node.js ou Django »

---

## Volet concepteur

### Pour répondre (`python -m usine.miroir repondre <lecture> id=valeur …`)

- `registre_entier:serveur:Client` = oui
- `registre_entier:serveur:Commande` = oui | non
- `registre_entier:serveur:Reservation` = oui
- `registre_entier:caissier:Client` = oui
- `registre_entier:caissier:Commande` = oui
- `registre_entier:caissier:Paiement` = oui | non
- `registre_entier:caissier:Facture` = oui | non
- `registre_entier:cuisinier:Client` = oui
- `registre_entier:cuisinier:Commande` = oui | non
- `registre_entier:livreur:Commande` = oui
- `registre_entier:livreur:Livraison` = oui
- `nom:Table:numero` = oui | <nouveau nom>  (Table → « Numéro de table »)
- `nom:Categorie:nom` = oui | <nouveau nom>  (Catégorie → « Nom de la catégorie »)
- `nom:Variante:nom` = oui | <nouveau nom>  (Variante → « Nom de la variante »)
- `nom:Client:nom` = oui | <nouveau nom>  (Client → « Nom »)
- `nom:Facture:numero` = oui | <nouveau nom>  (Facture → « Numéro de facture »)
- `nom:Fournisseur:nom` = oui | <nouveau nom>  (Fournisseur → « Nom du fournisseur »)
- `nom:ArticleStock:nom` = oui | <nouveau nom>  (Article en stock → « Nom de l'article »)
- `garder:Table:Nombre de places` = oui | non
- `garder:Table:Position sur le plan de salle` = oui | non
- `garder:Categorie:Ordre d'affichage dans le menu` = oui | non
- `garder:Produit:Nom du produit` = oui | non
- `garder:Produit:Description` = oui | non
- `garder:Variante:Type de variante (ex. cuisson, taille)` = oui | non
- `garder:Variante:Supplément de prix` = oui | non
- `garder:Client:Téléphone` = oui | non
- `garder:Client:Email` = oui | non
- `garder:Client:Adresse` = oui | non
- `garder:Commande:Nombre de couverts` = oui | non
- `garder:Commande:Note pour la cuisine` = oui | non
- `garder:LigneCommande:Prix unitaire appliqué` = oui | non
- `garder:LigneCommande:Remarque` = oui | non
- `garder:Paiement:Montant payé` = oui | non
- `garder:Paiement:Référence de transaction` = oui | non
- `garder:Facture:Montant total` = oui | non
- `garder:Livraison:Adresse de livraison` = oui | non
- `garder:Livraison:Téléphone de contact` = oui | non
- `garder:Livraison:Frais de livraison` = oui | non
- `garder:Livraison:Heure de livraison prévue` = oui | non
- `garder:Reservation:Date et heure de la réservation` = oui | non
- `garder:Reservation:Nombre de personnes` = oui | non
- `garder:Reservation:Commentaire` = oui | non
- `garder:Fournisseur:Téléphone` = oui | non
- `garder:Fournisseur:Email` = oui | non
- `garder:Fournisseur:Adresse` = oui | non
- `garder:ArticleStock:Unité de mesure` = oui | non
- `garder:MouvementStock:Quantité` = oui | non
- `garder:MouvementStock:Motif` = oui | non

### Pourquoi chaque droit

- administrateur / Table : préréglage catalogue : visible de tous les connectés ; gestionnaire du catalogue (supprimer : seulement si le brief le dit) — « Statut des tables (libre, occupée, réservée, en attente de paiement) »
- administrateur / Categorie : préréglage catalogue : visible de tous les connectés ; gestionnaire du catalogue (supprimer : seulement si le brief le dit) — « Catégorisation : entrées, plats, desserts, boissons »
- administrateur / Produit : préréglage catalogue : visible de tous les connectés ; gestionnaire du catalogue (supprimer : seulement si le brief le dit) — « Ajout, modification et désactivation des produits »
- administrateur / Client : tient le registre (supprimer : seulement si le brief le dit) — « Prise de réservation manuelle ou via une interface publique »
- administrateur / Commande : tient le registre (supprimer : seulement si le brief le dit) — « Attribution des commandes à une table »
- administrateur / Paiement : tient le registre (supprimer : seulement si le brief le dit) — « Paiement par espèce, carte, mobile money »
- administrateur / Facture : tient le registre (supprimer : seulement si le brief le dit) — « Facture imprimée ou PDF »
- administrateur / Livraison : tient le registre (supprimer : seulement si le brief le dit) — « Suivi des livreurs et états de livraison »
- administrateur / Reservation : tient le registre (supprimer : seulement si le brief le dit) — « Prise de réservation manuelle ou via une interface publique »
- administrateur / Fournisseur : tient le registre (supprimer : seulement si le brief le dit) — « Gestion des fournisseurs »
- administrateur / ArticleStock : tient le registre (supprimer : seulement si le brief le dit) — « Suivi en temps réel des stocks »
- administrateur / Variante : enfant de Produit : même visibilité que le parent, géré par qui gère le parent — « Ajout, modification et désactivation des produits »
- administrateur / LigneCommande : enfant de Commande : même visibilité que le parent, géré par qui gère le parent — « Attribution des commandes à une table »
- administrateur / MouvementStock : enfant de Article en stock : même visibilité que le parent, géré par qui gère le parent — « Suivi en temps réel des stocks »
- serveur / Table : préréglage catalogue : visible de tous les connectés — « Statut des tables (libre, occupée, réservée, en attente de paiement) »
- serveur / Categorie : préréglage catalogue : visible de tous les connectés — « Catégorisation : entrées, plats, desserts, boissons »
- serveur / Produit : préréglage catalogue : visible de tous les connectés — « Ajout, modification et désactivation des produits »
- serveur / Variante : enfant de Produit : même visibilité que le parent — « Ajout, modification et désactivation des produits »
- serveur / Client : tient le registre (supprimer : seulement si le brief le dit) — « Prise de réservation manuelle ou via une interface publique »
- serveur / Commande : tient le registre (supprimer : seulement si le brief le dit) — « Attribution des commandes à une table »
- serveur / LigneCommande : enfant de Commande : même visibilité que le parent, géré par qui gère le parent — « Attribution des commandes à une table »
- serveur / Reservation : tient le registre (supprimer : seulement si le brief le dit) ; fait évoluer l'état des fiches du registre — « Prise de réservation manuelle ou via une interface publique »
- caissier / Table : préréglage catalogue : visible de tous les connectés — « Statut des tables (libre, occupée, réservée, en attente de paiement) »
- caissier / Categorie : préréglage catalogue : visible de tous les connectés — « Catégorisation : entrées, plats, desserts, boissons »
- caissier / Produit : préréglage catalogue : visible de tous les connectés — « Ajout, modification et désactivation des produits »
- caissier / Variante : enfant de Produit : même visibilité que le parent — « Ajout, modification et désactivation des produits »
- caissier / Client : tient le registre (supprimer : seulement si le brief le dit) — « Prise de réservation manuelle ou via une interface publique »
- caissier / Commande : tient le registre (supprimer : seulement si le brief le dit) — « Attribution des commandes à une table »
- caissier / Paiement : tient le registre (supprimer : seulement si le brief le dit) — « Paiement par espèce, carte, mobile money »
- caissier / Facture : tient le registre (supprimer : seulement si le brief le dit) — « Facture imprimée ou PDF »
- caissier / LigneCommande : enfant de Commande : même visibilité que le parent, géré par qui gère le parent — « Attribution des commandes à une table »
- cuisinier / Table : préréglage catalogue : visible de tous les connectés — « Statut des tables (libre, occupée, réservée, en attente de paiement) »
- cuisinier / Categorie : préréglage catalogue : visible de tous les connectés — « Catégorisation : entrées, plats, desserts, boissons »
- cuisinier / Produit : préréglage catalogue : visible de tous les connectés — « Ajout, modification et désactivation des produits »
- cuisinier / Variante : enfant de Produit : même visibilité que le parent — « Ajout, modification et désactivation des produits »
- cuisinier / Client : clôture : affiché dans les Commandes qu'il voit ; clôture : choisit les Clients de ses Commandes — « Attribution des commandes à une table »
- cuisinier / Commande : tient le registre (supprimer : seulement si le brief le dit) — « Attribution des commandes à une table »
- cuisinier / LigneCommande : enfant de Commande : même visibilité que le parent, géré par qui gère le parent — « Attribution des commandes à une table »
- livreur / Table : préréglage catalogue : visible de tous les connectés — « Statut des tables (libre, occupée, réservée, en attente de paiement) »
- livreur / Categorie : préréglage catalogue : visible de tous les connectés — « Catégorisation : entrées, plats, desserts, boissons »
- livreur / Produit : préréglage catalogue : visible de tous les connectés — « Ajout, modification et désactivation des produits »
- livreur / Variante : enfant de Produit : même visibilité que le parent — « Ajout, modification et désactivation des produits »
- livreur / Commande : clôture : affiché dans les Livraisons qu'il voit ; clôture : choisit les Commandes de ses Livraisons — « Suivi des livreurs et états de livraison »
- livreur / Livraison : tient le registre (supprimer : seulement si le brief le dit) ; fait évoluer l'état des fiches du registre — « Suivi des livreurs et états de livraison »
