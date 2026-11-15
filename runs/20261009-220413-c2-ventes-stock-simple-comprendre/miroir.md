# Gestion commerciale — ce que l'usine a compris

En bref : 1 rôle (L'administrateur), 4 sortes de fiches, aucun circuit d'étapes.

## Le visiteur (sans compte)
- Ne voit rien

## L'administrateur (responsable de l'app)
- Voit tout, crée, modifie et supprime : ventes, clients, stocks
- Voit tout, crée et modifie : commandes

## Les informations de chaque fiche

- **Vente** : Intitulé (texte court) ◦ choisi par nous
  - relié à : client
  - proposé (à cocher) : ☐ Montant (montant) · ☐ Date de vente (date)
- **Client** : Nom (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Prénom (texte court) · ☐ Email (e-mail) · ☐ Téléphone (téléphone)
- **Stock** : Intitulé (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Quantité (nombre) · ☐ Seuil d'alerte (nombre)
- **Commande** : Intitulé (texte court) ◦ choisi par nous
  - relié à : client
  - proposé (à cocher) : ☐ Référence (texte court) · ☐ Montant total (montant)

## Questions

- Votre brief ne disait pas comment reconnaître certaines fiches ; nous avons choisi : vente → « Intitulé » · client → « Nom » · stock → « Intitulé » · commande → « Intitulé »

## Pas encore dans notre stock (vos mots)

- Dashboard avec indicateurs et statistiques — « 1 page dashboard reprenant le total des ventes, les plus gros clients , le nombre de commandes etc »
- Recherche dans la gestion des clients — « 1 page de gestion des clients (recherche,ajout,suppression,modification) »
- Recherche dans la gestion de stock — « 1 page de gestion de stock (recherche,ajout,suppression,modification) »

---

## Volet concepteur

### Pour répondre (`python -m usine.miroir repondre <lecture> id=valeur …`)

- `nom:Vente:intitule` = oui | <nouveau nom>  (vente → « Intitulé »)
- `nom:Client:nom` = oui | <nouveau nom>  (client → « Nom »)
- `nom:Stock:intitule` = oui | <nouveau nom>  (stock → « Intitulé »)
- `nom:Commande:intitule` = oui | <nouveau nom>  (commande → « Intitulé »)
- `garder:Vente:Montant` = oui | non
- `garder:Vente:Date de vente` = oui | non
- `garder:Client:Prénom` = oui | non
- `garder:Client:Email` = oui | non
- `garder:Client:Téléphone` = oui | non
- `garder:Stock:Quantité` = oui | non
- `garder:Stock:Seuil d'alerte` = oui | non
- `garder:Commande:Référence` = oui | non
- `garder:Commande:Montant total` = oui | non

### Pourquoi chaque droit

- administrateur / Vente : tient le registre (supprimer : seulement si le brief le dit) ; exception : « 1 page de gestion des ventes (ajout/affichage/suppression/modification) » ; exception : « 1 page de gestion des ventes (ajout/affichage/suppression/modification) » ; exception : « 1 page de gestion des ventes (ajout/affichage/suppression/modification) » ; exception : « 1 page de gestion des ventes (ajout/affichage/suppression/modification) » — « 1 page de gestion des ventes (ajout/affichage/suppression/modification) » « 1 page de gestion des ventes (ajout/affichage/suppression/modification) » « 1 page de gestion des ventes (ajout/affichage/suppression/modification) » « 1 page de gestion des ventes (ajout/affichage/suppression/modification) » « 1 page de gestion des ventes (ajout/affichage/suppression/modification) »
- administrateur / Client : tient le registre (supprimer : seulement si le brief le dit) ; exception : « 1 page de gestion des clients (recherche,ajout,suppression,modification) » ; exception : « 1 page de gestion des clients (recherche,ajout,suppression,modification) » ; exception : « 1 page de gestion des clients (recherche,ajout,suppression,modification) » ; exception : « 1 page de gestion des clients (recherche,ajout,suppression,modification) » — « 1 page de gestion des clients (recherche,ajout,suppression,modification) » « 1 page de gestion des clients (recherche,ajout,suppression,modification) » « 1 page de gestion des clients (recherche,ajout,suppression,modification) » « 1 page de gestion des clients (recherche,ajout,suppression,modification) » « 1 page de gestion des clients (recherche,ajout,suppression,modification) »
- administrateur / Stock : tient le registre (supprimer : seulement si le brief le dit) ; exception : « 1 page de gestion de stock (recherche,ajout,suppression,modification) » ; exception : « 1 page de gestion de stock (recherche,ajout,suppression,modification) » ; exception : « 1 page de gestion de stock (recherche,ajout,suppression,modification) » ; exception : « 1 page de gestion de stock (recherche,ajout,suppression,modification) » — « 1 page de gestion de stock (recherche,ajout,suppression,modification) » « 1 page de gestion de stock (recherche,ajout,suppression,modification) » « 1 page de gestion de stock (recherche,ajout,suppression,modification) » « 1 page de gestion de stock (recherche,ajout,suppression,modification) » « 1 page de gestion de stock (recherche,ajout,suppression,modification) »
- administrateur / Commande : tient le registre (supprimer : seulement si le brief le dit) — « gestion de commandes/stock/ventes/clients »
