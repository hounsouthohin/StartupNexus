# Gestion commerciale — ce que l'usine a compris

En bref : 1 rôle (Le gérant), 4 sortes de fiches, aucun circuit d'étapes.

## Le visiteur (sans compte)
- Ne voit rien

## Le gérant (responsable de l'app)
- Voit tout, crée, modifie et supprime : clients, ventes, articles en stock
- Voit tout, crée et modifie : commandes

## Les informations de chaque fiche

- **Client** : Nom (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Email (e-mail) · ☐ Téléphone (téléphone) · ☐ Adresse (texte long)
- **Vente** : Référence (texte court) ◦ choisi par nous
  - relié à : client
  - proposé (à cocher) : ☐ Montant (montant) · ☐ Quantité vendue (nombre)
- **Commande** : Référence (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Montant (montant) · ☐ Quantité commandée (nombre) · ☐ Date de livraison prévue (date)
- **Article en stock** : Nom (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Quantité en stock (nombre) · ☐ Prix unitaire (montant) · ☐ Référence article (texte court)

## Questions

- Votre brief ne disait pas comment reconnaître certaines fiches ; nous avons choisi : client → « Nom » · vente → « Référence » · commande → « Référence » · article en stock → « Nom »

## Pas encore dans notre stock (vos mots)

- Tableau de bord affichant le total des ventes — « 1 page dashboard reprenant le total des ventes »
- Classement des plus gros clients sur le tableau de bord — « les plus gros clients »
- Comptage du nombre de commandes (et autres indicateurs non précisés) sur le tableau de bord — « le nombre de commandes etc »

---

## Volet concepteur

### Pour répondre (`python -m usine.miroir repondre <lecture> id=valeur …`)

- `nom:Client:nom` = oui | <nouveau nom>  (client → « Nom »)
- `nom:Vente:reference` = oui | <nouveau nom>  (vente → « Référence »)
- `nom:Commande:reference` = oui | <nouveau nom>  (commande → « Référence »)
- `nom:Article:nom` = oui | <nouveau nom>  (article en stock → « Nom »)
- `garder:Client:Email` = oui | non
- `garder:Client:Téléphone` = oui | non
- `garder:Client:Adresse` = oui | non
- `garder:Vente:Montant` = oui | non
- `garder:Vente:Quantité vendue` = oui | non
- `garder:Commande:Montant` = oui | non
- `garder:Commande:Quantité commandée` = oui | non
- `garder:Commande:Date de livraison prévue` = oui | non
- `garder:Article:Quantité en stock` = oui | non
- `garder:Article:Prix unitaire` = oui | non
- `garder:Article:Référence article` = oui | non

### Pourquoi chaque droit

- gerant / Client : tient le registre (supprimer : seulement si le brief le dit) ; exception : « 1 page de gestion des clients (recherche,ajout,suppression,modification) » ; exception : « 1 page de gestion des clients (recherche,ajout,suppression,modification) » ; exception : « 1 page de gestion des clients (recherche,ajout,suppression,modification) » ; exception : « 1 page de gestion des clients (recherche,ajout,suppression,modification) » — « 1 page de gestion des clients (recherche,ajout,suppression,modification) » « 1 page de gestion des clients (recherche,ajout,suppression,modification) » « 1 page de gestion des clients (recherche,ajout,suppression,modification) » « 1 page de gestion des clients (recherche,ajout,suppression,modification) » « 1 page de gestion des clients (recherche,ajout,suppression,modification) »
- gerant / Vente : tient le registre (supprimer : seulement si le brief le dit) ; exception : « 1 page de gestion des ventes (ajout/affichage/suppression/modification) » ; exception : « 1 page de gestion des ventes (ajout/affichage/suppression/modification) » ; exception : « 1 page de gestion des ventes (ajout/affichage/suppression/modification) » ; exception : « 1 page de gestion des ventes (ajout/affichage/suppression/modification) » — « 1 page de gestion des ventes (ajout/affichage/suppression/modification) » « 1 page de gestion des ventes (ajout/affichage/suppression/modification) » « 1 page de gestion des ventes (ajout/affichage/suppression/modification) » « 1 page de gestion des ventes (ajout/affichage/suppression/modification) » « 1 page de gestion des ventes (ajout/affichage/suppression/modification) »
- gerant / Article : tient le registre (supprimer : seulement si le brief le dit) ; exception : « 1 page de gestion de stock (recherche,ajout,suppression,modification) » ; exception : « 1 page de gestion de stock (recherche,ajout,suppression,modification) » ; exception : « 1 page de gestion de stock (recherche,ajout,suppression,modification) » ; exception : « 1 page de gestion de stock (recherche,ajout,suppression,modification) » — « 1 page de gestion de stock (recherche,ajout,suppression,modification) » « 1 page de gestion de stock (recherche,ajout,suppression,modification) » « 1 page de gestion de stock (recherche,ajout,suppression,modification) » « 1 page de gestion de stock (recherche,ajout,suppression,modification) » « 1 page de gestion de stock (recherche,ajout,suppression,modification) »
- gerant / Commande : tient le registre (supprimer : seulement si le brief le dit) — « gestion de commandes/stock/ventes/clients »
