# Gestion Meubles — ce que l'usine a compris

En bref : 1 rôle (L'administrateur), 10 sortes de fiches, aucun circuit d'étapes.

## Le visiteur (sans compte)
- Ne voit rien

## L'administrateur (responsable de l'app)
- Voit tout, crée, modifie et supprime : clients, fournisseurs, références produits, commandes clients, factures clients, encaissements clients, commandes fournisseurs, stocks produits, mouvements de stock, livraisons clients

## Les informations de chaque fiche

- **Client** : Nom (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Email (e-mail) · ☐ Téléphone (téléphone) · ☐ Adresse (texte long)
- **Fournisseur** : Nom (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Email (e-mail) · ☐ Téléphone (téléphone) · ☐ Adresse (texte long)
- **Référence produit** : Prix (montant)
  - proposé (à cocher) : ☐ Libellé du produit (texte court) · ☐ Description (texte long)
- **Commande client** : Intitulé (texte court) ◦ choisi par nous
  - relié à : client
  - proposé (à cocher) : ☐ Numéro de commande (texte court) · ☐ Montant total (montant)
- **Facture client** : Intitulé (texte court) ◦ choisi par nous
  - relié à : client, commande client
  - proposé (à cocher) : ☐ Numéro de facture (texte court) · ☐ Montant total (montant)
- **Encaissement client** : Intitulé (texte court) ◦ choisi par nous
  - relié à : client
  - proposé (à cocher) : ☐ Montant encaissé (montant) · ☐ Mode de paiement (texte court)
- **Commande fournisseur** : Intitulé (texte court) ◦ choisi par nous
  - relié à : fournisseur, commande client
  - proposé (à cocher) : ☐ Numéro de commande fournisseur (texte court) · ☐ Montant total (montant)
- **Stock produit** : Intitulé (texte court) ◦ choisi par nous
  - relié à : référence produit
  - proposé (à cocher) : ☐ Quantité en stock (nombre) · ☐ Emplacement (texte court)
- **Mouvement de stock** : Type de mouvement (choix parmi : entrée, sortie, réservation contremarque)
  - relié à : référence produit
  - proposé (à cocher) : ☐ Quantité (nombre) · ☐ Commentaire (texte long)
- **Livraison client** : Type de livraison (choix parmi : complété, partielle)
  - relié à : client, commande client
  - proposé (à cocher) : ☐ Date prévue de livraison (date) · ☐ Adresse de livraison (texte long)

## Questions

- Votre brief ne disait pas comment reconnaître certaines fiches ; nous avons choisi : client → « Nom » · fournisseur → « Nom » · commande client → « Intitulé » · facture client → « Intitulé » · encaissement client → « Intitulé » · commande fournisseur → « Intitulé » · stock produit → « Intitulé »

## Pas encore dans notre stock (vos mots)

- Facturation clients — « Gestion et Suivi des commandes et facturations clients »
- Suivi des encaissements clients — « Gestion et suivi des encaissements clients »
- Gestion des stocks avec entrées, sorties et réservations — « Gestion et suivi des stocks, entrée/sortie/ réservation contremarque »
- Programmation des livraisons clients — « Programmation des Livraisons clients ( complété ou partielle ) »
- Utilisation sur smartphone avec développement d’une application — « Utilisation du logiciel depuis smartphone, développement d'une application. »
- Fonction de retour arrière sur page — « avec possibilité de retour arrière sur page »

---

## Volet concepteur

### Pour répondre (`python -m usine.miroir repondre <lecture> id=valeur …`)

- `nom:Client:nom` = oui | <nouveau nom>  (client → « Nom »)
- `nom:Fournisseur:nom` = oui | <nouveau nom>  (fournisseur → « Nom »)
- `nom:CommandeClient:intitule` = oui | <nouveau nom>  (commande client → « Intitulé »)
- `nom:FactureClient:intitule` = oui | <nouveau nom>  (facture client → « Intitulé »)
- `nom:EncaissementClient:intitule` = oui | <nouveau nom>  (encaissement client → « Intitulé »)
- `nom:CommandeFournisseur:intitule` = oui | <nouveau nom>  (commande fournisseur → « Intitulé »)
- `nom:StockProduit:intitule` = oui | <nouveau nom>  (stock produit → « Intitulé »)
- `garder:Client:Email` = oui | non
- `garder:Client:Téléphone` = oui | non
- `garder:Client:Adresse` = oui | non
- `garder:Fournisseur:Email` = oui | non
- `garder:Fournisseur:Téléphone` = oui | non
- `garder:Fournisseur:Adresse` = oui | non
- `garder:ReferenceProduit:Libellé du produit` = oui | non
- `garder:ReferenceProduit:Description` = oui | non
- `garder:CommandeClient:Numéro de commande` = oui | non
- `garder:CommandeClient:Montant total` = oui | non
- `garder:FactureClient:Numéro de facture` = oui | non
- `garder:FactureClient:Montant total` = oui | non
- `garder:EncaissementClient:Montant encaissé` = oui | non
- `garder:EncaissementClient:Mode de paiement` = oui | non
- `garder:CommandeFournisseur:Numéro de commande fournisseur` = oui | non
- `garder:CommandeFournisseur:Montant total` = oui | non
- `garder:StockProduit:Quantité en stock` = oui | non
- `garder:StockProduit:Emplacement` = oui | non
- `garder:MouvementStock:Quantité` = oui | non
- `garder:MouvementStock:Commentaire` = oui | non
- `garder:LivraisonClient:Date prévue de livraison` = oui | non
- `garder:LivraisonClient:Adresse de livraison` = oui | non

### Pourquoi chaque droit

- administrateur / Client : tient le registre (supprimer : seulement si le brief le dit) ; exception : « Liberté d'intervention en tant qu'administrateur sur la suppression de données » — « Gestion et Suivi des commandes et facturations clients » « Liberté d'intervention en tant qu'administrateur sur la suppression de données »
- administrateur / Fournisseur : tient le registre (supprimer : seulement si le brief le dit) ; exception : « Liberté d'intervention en tant qu'administrateur sur la suppression de données » — « Gestion et Suivi  des commandes fournisseurs » « Liberté d'intervention en tant qu'administrateur sur la suppression de données »
- administrateur / ReferenceProduit : préréglage catalogue : visible de tous les connectés ; gestionnaire du catalogue (supprimer : seulement si le brief le dit) ; exception : « Liberté d'intervention en tant qu'administrateur sur la suppression de données » — « Base de données de nos références produits, avec prix » « Liberté d'intervention en tant qu'administrateur sur la suppression de données »
- administrateur / CommandeClient : tient le registre (supprimer : seulement si le brief le dit) ; exception : « Liberté d'intervention en tant qu'administrateur sur la suppression de données » — « Gestion et Suivi des commandes et facturations clients » « Liberté d'intervention en tant qu'administrateur sur la suppression de données »
- administrateur / FactureClient : tient le registre (supprimer : seulement si le brief le dit) ; exception : « Liberté d'intervention en tant qu'administrateur sur la suppression de données » — « Gestion et Suivi des commandes et facturations clients » « Liberté d'intervention en tant qu'administrateur sur la suppression de données »
- administrateur / EncaissementClient : tient le registre (supprimer : seulement si le brief le dit) ; exception : « Liberté d'intervention en tant qu'administrateur sur la suppression de données » — « Gestion et suivi des encaissements clients » « Liberté d'intervention en tant qu'administrateur sur la suppression de données »
- administrateur / CommandeFournisseur : tient le registre (supprimer : seulement si le brief le dit) ; exception : « Liberté d'intervention en tant qu'administrateur sur la suppression de données » — « Gestion et Suivi  des commandes fournisseurs lié à nos commandes clients » « Liberté d'intervention en tant qu'administrateur sur la suppression de données »
- administrateur / StockProduit : tient le registre (supprimer : seulement si le brief le dit) ; exception : « Liberté d'intervention en tant qu'administrateur sur la suppression de données » — « Gestion et suivi des stocks, entrée/sortie/ réservation contremarque » « Liberté d'intervention en tant qu'administrateur sur la suppression de données »
- administrateur / MouvementStock : tient le registre (supprimer : seulement si le brief le dit) ; exception : « Liberté d'intervention en tant qu'administrateur sur la suppression de données » — « entrée/sortie/ réservation contremarque » « Liberté d'intervention en tant qu'administrateur sur la suppression de données »
- administrateur / LivraisonClient : tient le registre (supprimer : seulement si le brief le dit) ; exception : « Liberté d'intervention en tant qu'administrateur sur la suppression de données » — « Programmation des Livraisons clients ( complété ou partielle ) » « Liberté d'intervention en tant qu'administrateur sur la suppression de données »
