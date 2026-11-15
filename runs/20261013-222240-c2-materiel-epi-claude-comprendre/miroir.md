# Gestion EPI montagne — ce que l'usine a compris

En bref : 1 rôle (Le gestionnaire du matériel), 2 sortes de fiches, aucun circuit d'étapes.

## Le visiteur (sans compte)
- Ne voit rien

## Le gestionnaire du matériel (responsable de l'app)
- Voit tout, crée et modifie : Matériels
- Voit tout, crée, modifie et supprime : Vérifications (dans chaque Matériel)

## Les informations de chaque fiche

- **Matériel** : Désignation (texte court) ◦ choisi par nous · Date de fabrication (date) · Date de fin de vie (date) · Valeur (montant)
  - proposé (à cocher) : ☐ Numéro de série (texte court) · ☐ Marque / modèle (texte court) · ☐ Catégorie de matériel (texte court) · ☐ Date d'achat / de mise en service (date) · ☐ Durée d'amortissement (années) (nombre) · ☐ Quantité en stock (nombre) · ☐ Date de prochaine vérification (date)
- **Vérification** : Date de vérification (date)
  - relié à : dans chaque Matériel
  - proposé (à cocher) : ☐ Résultat (conforme / non conforme) (choix) · ☐ Vérificateur (texte court) · ☐ Observations (texte long) · ☐ Date de la prochaine vérification (date)

## Questions

- Votre brief ne disait pas comment reconnaître certaines fiches ; nous avons choisi : Matériel → « Désignation »

## Pas encore dans notre stock (vos mots)

- Calcul automatique de l'amortissement de la valeur de chaque matériel selon les années — « amortissements de la valeur en fonction des années »
- Édition (document généré) d'une fiche de suivi individuelle par matériel — « édition d'une fiche de suivie individuelle »
- Vue de synthèse des stocks et des valeurs, avec le montant d'amortissement par exercice comptable, pour la comptabilité — « visualisation des stocks, valeurs, montant d'amortissement par exercice pour la compta »
- Alertes à date pour la péremption du matériel et pour les vérifications à faire — « alerte péremption et vérification à la date »

---

## Volet concepteur

### Pour répondre (`python -m usine.miroir repondre <lecture> id=valeur …`)

- `nom:Materiel:designation` = oui | <nouveau nom>  (Matériel → « Désignation »)
- `garder:Materiel:Numéro de série` = oui | non
- `garder:Materiel:Marque / modèle` = oui | non
- `garder:Materiel:Catégorie de matériel` = oui | non
- `garder:Materiel:Date d'achat / de mise en service` = oui | non
- `garder:Materiel:Durée d'amortissement (années)` = oui | non
- `garder:Materiel:Quantité en stock` = oui | non
- `garder:Materiel:Date de prochaine vérification` = oui | non
- `garder:Verification:Résultat (conforme / non conforme)` = oui | non
- `garder:Verification:Vérificateur` = oui | non
- `garder:Verification:Observations` = oui | non
- `garder:Verification:Date de la prochaine vérification` = oui | non

### Pourquoi chaque droit

- gestionnaire / Materiel : tient le registre (supprimer : seulement si le brief le dit) ; exception : « application de saisie des matériels » ; exception : « visualisation des stocks, valeurs » — « saisie des matériels, date de fabrication, fin de vie » « application de saisie des matériels » « visualisation des stocks, valeurs »
- gestionnaire / Verification : exception : « saisie des vérifications pour chaque matériel » ; enfant de Matériel : même visibilité que le parent, géré par qui gère le parent — « saisie des vérifications pour chaque matériel » « saisie des matériels, date de fabrication, fin de vie » « application de saisie des matériels » « visualisation des stocks, valeurs »
