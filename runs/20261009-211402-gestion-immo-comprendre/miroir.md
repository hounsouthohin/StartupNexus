# Gestion immobilière — ce que l'usine a compris

En bref : 1 rôle (Le gestionnaire de biens immobilier), 5 sortes de fiches, aucun circuit d'étapes.

## Le visiteur (sans compte)
- Ne voit rien

## Le gestionnaire de biens immobilier (responsable de l'app)
- Voit tout, crée et modifie : biens immobiliers, rapprochements bancaires, loyers, quittances, relevés de compte

## Les informations de chaque fiche

- **Bien immobilier** : Nom (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Adresse (texte court) · ☐ Description (texte long)
- **Rapprochement bancaire** : Nom (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Période (texte court) · ☐ Montant rapproché (montant)
- **Loyer** : Nom (texte court) ◦ choisi par nous
  - relié à : bien immobilier
  - proposé (à cocher) : ☐ Montant (montant) · ☐ Période (texte court)
- **Quittance** : Nom (texte court) ◦ choisi par nous
  - relié à : loyer
  - proposé (à cocher) : ☐ Numéro de quittance (texte court) · ☐ Montant quittancé (montant)
- **Relevé de compte** : Nom (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Période (texte court) · ☐ Solde (montant)

## Questions

- Votre brief ne disait pas comment reconnaître certaines fiches ; nous avons choisi : bien immobilier → « Nom » · rapprochement bancaire → « Nom » · loyer → « Nom » · quittance → « Nom » · relevé de compte → « Nom »

## Pas encore dans notre stock (vos mots)

- Automatisation de tâches — « d'automatiser des taches »
- Rapprochement bancaire automatisé — « d'automatiser le rapprochement bancaire »
- Encaissement des loyers — « l'encaissement des loyers »
- Reversement des loyers — « le reversement des loyers »
- Envoi automatique de quittances et relevés de compte — « d'envoyer automatiquement des quittances, relevé de compte etc.. »
- Quittances et relevés de compte générés — « quittances, relevé de compte »

---

## Volet concepteur

### Pour répondre (`python -m usine.miroir repondre <lecture> id=valeur …`)

- `nom:BienImmobilier:nom` = oui | <nouveau nom>  (bien immobilier → « Nom »)
- `nom:RapprochementBancaire:nom` = oui | <nouveau nom>  (rapprochement bancaire → « Nom »)
- `nom:Loyer:nom` = oui | <nouveau nom>  (loyer → « Nom »)
- `nom:Quittance:nom` = oui | <nouveau nom>  (quittance → « Nom »)
- `nom:ReleveDeCompte:nom` = oui | <nouveau nom>  (relevé de compte → « Nom »)
- `garder:BienImmobilier:Adresse` = oui | non
- `garder:BienImmobilier:Description` = oui | non
- `garder:RapprochementBancaire:Période` = oui | non
- `garder:RapprochementBancaire:Montant rapproché` = oui | non
- `garder:Loyer:Montant` = oui | non
- `garder:Loyer:Période` = oui | non
- `garder:Quittance:Numéro de quittance` = oui | non
- `garder:Quittance:Montant quittancé` = oui | non
- `garder:ReleveDeCompte:Période` = oui | non
- `garder:ReleveDeCompte:Solde` = oui | non

### Pourquoi chaque droit

- gestionnaire / BienImmobilier : tient le registre (supprimer : seulement si le brief le dit) — « gestionnaire de biens immobilier »
- gestionnaire / RapprochementBancaire : tient le registre (supprimer : seulement si le brief le dit) — « rapprochement bancaire »
- gestionnaire / Loyer : tient le registre (supprimer : seulement si le brief le dit) — « l'encaissement des loyers, le reversement des loyers »
- gestionnaire / Quittance : tient le registre (supprimer : seulement si le brief le dit) — « envoyer automatiquement des quittances »
- gestionnaire / ReleveDeCompte : tient le registre (supprimer : seulement si le brief le dit) — « relevé de compte »
