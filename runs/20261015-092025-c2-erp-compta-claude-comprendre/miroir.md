# Gestion d'entreprise — ce que l'usine a compris

En bref : 2 rôles (L'administrateur, L'expert comptable), 3 sortes de fiches, aucun circuit d'étapes.

## Le visiteur (sans compte)
- Ne voit rien

## L'administrateur (responsable de l'app)
- Voit tout, crée et modifie : factures, écritures comptables, articles en stock

## L'expert comptable (invité par administrateur)
- Ne voit rien

## Les informations de chaque fiche

- **Facture** : Numéro de facture (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Montant total (montant) · ☐ Date d'échéance (date) · ☐ Taux de TVA (nombre)
- **Écriture comptable** : Libellé de l'écriture (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Date de l'écriture (date) · ☐ Montant (montant) · ☐ Compte comptable (texte court)
- **Article en stock** : Désignation de l'article (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Référence (texte court) · ☐ Quantité en stock (nombre) · ☐ Prix unitaire (montant)

## Questions

- Votre brief ne disait pas comment reconnaître certaines fiches ; nous avons choisi : facture → « Numéro de facture » · écriture comptable → « Libellé de l'écriture » · article en stock → « Désignation de l'article »

## Pas encore dans notre stock (vos mots)

- Facturation (émission de factures) — « faire de la facturation »
- Comptabilité (calculs et écritures comptables) — « la comptabilité »
- Gestion financière (suivi et calculs financiers) — « la gestion financière »
- Gestion de stock (suivi des quantités et mouvements) — « la gestion de stock »
- Saisie automatique — « une option de saisie automatique »
- Version hybride (mobile) dans un second temps — « puis hybride plus tard »

---

## Volet concepteur

### Pour répondre (`python -m usine.miroir repondre <lecture> id=valeur …`)

- `nom:Facture:numero` = oui | <nouveau nom>  (facture → « Numéro de facture »)
- `nom:EcritureComptable:libelle` = oui | <nouveau nom>  (écriture comptable → « Libellé de l'écriture »)
- `nom:ArticleStock:designation` = oui | <nouveau nom>  (article en stock → « Désignation de l'article »)
- `garder:Facture:Montant total` = oui | non
- `garder:Facture:Date d'échéance` = oui | non
- `garder:Facture:Taux de TVA` = oui | non
- `garder:EcritureComptable:Date de l'écriture` = oui | non
- `garder:EcritureComptable:Montant` = oui | non
- `garder:EcritureComptable:Compte comptable` = oui | non
- `garder:ArticleStock:Référence` = oui | non
- `garder:ArticleStock:Quantité en stock` = oui | non
- `garder:ArticleStock:Prix unitaire` = oui | non

### Pourquoi chaque droit

- administrateur / Facture : tient le registre (supprimer : seulement si le brief le dit) — « de la facturation »
- administrateur / EcritureComptable : tient le registre (supprimer : seulement si le brief le dit) — « la comptabilité »
- administrateur / ArticleStock : tient le registre (supprimer : seulement si le brief le dit) — « la gestion de stock »
