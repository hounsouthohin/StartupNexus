# Gestion du magasin — ce que l'usine a compris

En bref : 1 rôle (L'administrateur), 9 sortes de fiches, 1 circuit d'étapes.

## Le visiteur (sans compte)
- Ne voit rien

## L'administrateur (responsable de l'app)
- Voit tout, crée, modifie et supprime : Clients, Fournisseurs, Références produits, Commandes clients, Factures, Encaissements, Commandes fournisseurs, Mouvements de stock
- Livraisons : voit tout, en crée, les modifie, les supprime, les fait passer de « programmée » à « complète » ou « partielle »

## Les étapes

- La livraison commence « programmée » ; de « programmée », vers « complète » ou « partielle »
  - L'administrateur fait passer de « programmée » à « complète » ou « partielle »

## Les informations de chaque fiche

- **Client** : Nom (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Prénom (texte court) · ☐ Téléphone (téléphone) · ☐ Email (e-mail) · ☐ Adresse (texte long)
- **Fournisseur** : Nom (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Téléphone (téléphone) · ☐ Email (e-mail) · ☐ Adresse (texte long) · ☐ Délai de livraison habituel (jours) (nombre)
- **Référence produit** : Désignation (texte court) ◦ choisi par nous · Prix (montant)
  - proposé (à cocher) : ☐ Code référence (texte court) · ☐ Description (texte long) · ☐ Dimensions (texte court) · ☐ Prix d'achat (montant)
- **Commande client** : Numéro de commande (texte court) ◦ choisi par nous
  - relié à : Client, Référence produit
  - proposé (à cocher) : ☐ Quantité (nombre) · ☐ Montant total (montant) · ☐ Acompte versé (montant) · ☐ Date de livraison souhaitée (date)
- **Facture** : Numéro de facture (texte court) ◦ choisi par nous
  - relié à : Client, Commande client
  - proposé (à cocher) : ☐ Montant TTC (montant) · ☐ Date d'échéance (date)
- **Encaissement** : Référence (texte court) ◦ choisi par nous
  - relié à : Client
  - proposé (à cocher) : ☐ Montant (montant) · ☐ Mode de paiement (texte court) · ☐ Date d'encaissement (date)
- **Commande fournisseur** : Numéro de commande fournisseur (texte court) ◦ choisi par nous
  - relié à : Fournisseur, Commande client
  - proposé (à cocher) : ☐ Date de livraison prévue (date) · ☐ Montant (montant) · ☐ Référence chez le fournisseur (texte court)
- **Mouvement de stock** : Type de mouvement (choix parmi : entrée, sortie, réservation contremarque)
  - relié à : Référence produit, Commande client
  - proposé (à cocher) : ☐ Quantité (nombre) · ☐ Commentaire (texte long)
- **Livraison** : Date de livraison prévue (date)
  - relié à : Commande client, Client
  - proposé (à cocher) : ☐ Adresse de livraison (texte long) · ☐ Créneau horaire (texte court) · ☐ Remarques (texte long)

## Questions

- Votre brief ne disait pas comment reconnaître certaines fiches ; nous avons choisi : Client → « Nom » · Fournisseur → « Nom » · Référence produit → « Désignation » · Commande client → « Numéro de commande » · Facture → « Numéro de facture » · Encaissement → « Référence » · Commande fournisseur → « Numéro de commande fournisseur »

## Pas encore dans notre stock (vos mots)

- Facturation des clients (factures produites à partir des commandes) — « Gestion et Suivi des commandes et facturations clients »
- Suivi des encaissements clients (paiements reçus) — « Gestion et suivi des encaissements clients »
- Gestion des stocks : calcul des quantités selon les entrées, les sorties et les réservations en contremarque — « Gestion et suivi des stocks, entrée/sortie/ réservation contremarque »
- Programmation des livraisons clients, complètes ou partielles — « Programmation des Livraisons clients ( complété ou partielle ) »
- Utilisation du logiciel en intranet (hébergement sur le réseau interne) — « Utilisation du logiciel en intranet »
- Application smartphone pour utiliser le logiciel — « Utilisation du logiciel depuis smartphone, développement d'une application. »

---

## Volet concepteur

### Pour répondre (`python -m usine.miroir repondre <lecture> id=valeur …`)

- `nom:Client:nom` = oui | <nouveau nom>  (Client → « Nom »)
- `nom:Fournisseur:nom` = oui | <nouveau nom>  (Fournisseur → « Nom »)
- `nom:Produit:designation` = oui | <nouveau nom>  (Référence produit → « Désignation »)
- `nom:CommandeClient:numero` = oui | <nouveau nom>  (Commande client → « Numéro de commande »)
- `nom:Facture:numero` = oui | <nouveau nom>  (Facture → « Numéro de facture »)
- `nom:Encaissement:reference` = oui | <nouveau nom>  (Encaissement → « Référence »)
- `nom:CommandeFournisseur:numero` = oui | <nouveau nom>  (Commande fournisseur → « Numéro de commande fournisseur »)
- `garder:Client:Prénom` = oui | non
- `garder:Client:Téléphone` = oui | non
- `garder:Client:Email` = oui | non
- `garder:Client:Adresse` = oui | non
- `garder:Fournisseur:Téléphone` = oui | non
- `garder:Fournisseur:Email` = oui | non
- `garder:Fournisseur:Adresse` = oui | non
- `garder:Fournisseur:Délai de livraison habituel (jours)` = oui | non
- `garder:Produit:Code référence` = oui | non
- `garder:Produit:Description` = oui | non
- `garder:Produit:Dimensions` = oui | non
- `garder:Produit:Prix d'achat` = oui | non
- `garder:CommandeClient:Quantité` = oui | non
- `garder:CommandeClient:Montant total` = oui | non
- `garder:CommandeClient:Acompte versé` = oui | non
- `garder:CommandeClient:Date de livraison souhaitée` = oui | non
- `garder:Facture:Montant TTC` = oui | non
- `garder:Facture:Date d'échéance` = oui | non
- `garder:Encaissement:Montant` = oui | non
- `garder:Encaissement:Mode de paiement` = oui | non
- `garder:Encaissement:Date d'encaissement` = oui | non
- `garder:CommandeFournisseur:Date de livraison prévue` = oui | non
- `garder:CommandeFournisseur:Montant` = oui | non
- `garder:CommandeFournisseur:Référence chez le fournisseur` = oui | non
- `garder:MouvementStock:Quantité` = oui | non
- `garder:MouvementStock:Commentaire` = oui | non
- `garder:Livraison:Adresse de livraison` = oui | non
- `garder:Livraison:Créneau horaire` = oui | non
- `garder:Livraison:Remarques` = oui | non

### Pourquoi chaque droit

- administrateur / Client : tient le registre (supprimer : seulement si le brief le dit) ; exception : « Liberté d'intervention en tant qu'administrateur sur la suppression de données » — « Gestion et suivi des encaissements clients » « Liberté d'intervention en tant qu'administrateur sur la suppression de données »
- administrateur / Fournisseur : tient le registre (supprimer : seulement si le brief le dit) ; exception : « Liberté d'intervention en tant qu'administrateur sur la suppression de données » — « commandes fournisseurs lié à nos commandes clients » « Liberté d'intervention en tant qu'administrateur sur la suppression de données »
- administrateur / Produit : préréglage catalogue : visible de tous les connectés ; gestionnaire du catalogue (supprimer : seulement si le brief le dit) ; exception : « Liberté d'intervention en tant qu'administrateur sur la suppression de données » — « Base de données de nos références produits, avec prix » « Liberté d'intervention en tant qu'administrateur sur la suppression de données »
- administrateur / CommandeClient : tient le registre (supprimer : seulement si le brief le dit) ; exception : « Liberté d'intervention en tant qu'administrateur sur la suppression de données » — « Gestion et Suivi des commandes et facturations clients » « Liberté d'intervention en tant qu'administrateur sur la suppression de données »
- administrateur / Facture : tient le registre (supprimer : seulement si le brief le dit) ; exception : « Liberté d'intervention en tant qu'administrateur sur la suppression de données » — « commandes et facturations clients » « Liberté d'intervention en tant qu'administrateur sur la suppression de données »
- administrateur / Encaissement : tient le registre (supprimer : seulement si le brief le dit) ; exception : « Liberté d'intervention en tant qu'administrateur sur la suppression de données » — « Gestion et suivi des encaissements clients » « Liberté d'intervention en tant qu'administrateur sur la suppression de données »
- administrateur / CommandeFournisseur : tient le registre (supprimer : seulement si le brief le dit) ; exception : « Liberté d'intervention en tant qu'administrateur sur la suppression de données » — « commandes fournisseurs lié à nos commandes clients » « Liberté d'intervention en tant qu'administrateur sur la suppression de données »
- administrateur / MouvementStock : tient le registre (supprimer : seulement si le brief le dit) ; exception : « Liberté d'intervention en tant qu'administrateur sur la suppression de données » — « Gestion et suivi des stocks, entrée/sortie/ réservation contremarque » « Liberté d'intervention en tant qu'administrateur sur la suppression de données »
- administrateur / Livraison : tient le registre (supprimer : seulement si le brief le dit) ; fait évoluer l'état des fiches du registre ; exception : « Liberté d'intervention en tant qu'administrateur sur la suppression de données » — « Programmation des Livraisons clients ( complété ou partielle ) » « Liberté d'intervention en tant qu'administrateur sur la suppression de données »
