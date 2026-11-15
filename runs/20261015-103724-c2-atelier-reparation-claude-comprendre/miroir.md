# Atelier de réparation — ce que l'usine a compris

En bref : 1 rôle (Le gérant), 4 sortes de fiches, aucun circuit d'étapes.

## Le visiteur (sans compte)
- Ne voit rien

## Le gérant (responsable de l'app)
- Voit tout, crée et modifie : Machines, Bons d'entrée, Bons d'intervention, Commandes de pièces

## Les informations de chaque fiche

- **Machine** : Désignation (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Marque (texte court) · ☐ Modèle (texte court) · ☐ Numéro de série (texte court) · ☐ Nom du client propriétaire (texte court) · ☐ Téléphone du client (téléphone)
- **Bon d'entrée** : Numéro du bon (texte court) ◦ choisi par nous
  - relié à : Machine
  - proposé (à cocher) : ☐ Panne signalée (texte long) · ☐ Accessoires déposés (texte long) · ☐ État visuel à l'entrée (texte long) · ☐ Date de restitution prévue (date)
- **Bon d'intervention** : Numéro du bon (texte court) ◦ choisi par nous
  - relié à : Machine
  - proposé (à cocher) : ☐ Travaux réalisés (texte long) · ☐ Date d'intervention (date) · ☐ Technicien (texte court) · ☐ Temps passé (heures) (nombre) · ☐ Montant facturé (montant)
- **Commande de pièce** : Pièce commandée (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Référence de la pièce (texte court) · ☐ Quantité (nombre) · ☐ Fournisseur (texte court) · ☐ Prix d'achat (montant) · ☐ Date de réception prévue (date)

## Questions

- Votre brief ne disait pas comment reconnaître certaines fiches ; nous avons choisi : Machine → « Désignation » · Bon d'entrée → « Numéro du bon » · Bon d'intervention → « Numéro du bon » · Commande de pièce → « Pièce commandée »

---

## Volet concepteur

### Pour répondre (`python -m usine.miroir repondre <lecture> id=valeur …`)

- `nom:Machine:designation` = oui | <nouveau nom>  (Machine → « Désignation »)
- `nom:BonEntree:numero` = oui | <nouveau nom>  (Bon d'entrée → « Numéro du bon »)
- `nom:BonIntervention:numero` = oui | <nouveau nom>  (Bon d'intervention → « Numéro du bon »)
- `nom:CommandePiece:piece` = oui | <nouveau nom>  (Commande de pièce → « Pièce commandée »)
- `garder:Machine:Marque` = oui | non
- `garder:Machine:Modèle` = oui | non
- `garder:Machine:Numéro de série` = oui | non
- `garder:Machine:Nom du client propriétaire` = oui | non
- `garder:Machine:Téléphone du client` = oui | non
- `garder:BonEntree:Panne signalée` = oui | non
- `garder:BonEntree:Accessoires déposés` = oui | non
- `garder:BonEntree:État visuel à l'entrée` = oui | non
- `garder:BonEntree:Date de restitution prévue` = oui | non
- `garder:BonIntervention:Travaux réalisés` = oui | non
- `garder:BonIntervention:Date d'intervention` = oui | non
- `garder:BonIntervention:Technicien` = oui | non
- `garder:BonIntervention:Temps passé (heures)` = oui | non
- `garder:BonIntervention:Montant facturé` = oui | non
- `garder:CommandePiece:Référence de la pièce` = oui | non
- `garder:CommandePiece:Quantité` = oui | non
- `garder:CommandePiece:Fournisseur` = oui | non
- `garder:CommandePiece:Prix d'achat` = oui | non
- `garder:CommandePiece:Date de réception prévue` = oui | non

### Pourquoi chaque droit

- gerant / Machine : tient le registre (supprimer : seulement si le brief le dit) — « suivi de machine »
- gerant / BonEntree : tient le registre (supprimer : seulement si le brief le dit) — « gestion d'atelier de réparation : bon d'entrée »
- gerant / BonIntervention : tient le registre (supprimer : seulement si le brief le dit) — « bon d'intervention »
- gerant / CommandePiece : tient le registre (supprimer : seulement si le brief le dit) — « commande de pièce »
