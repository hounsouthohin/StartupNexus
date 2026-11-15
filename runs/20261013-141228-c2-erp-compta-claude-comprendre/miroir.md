# Gestion d'entreprise — ce que l'usine a compris

En bref : 2 rôles (Le dirigeant, L'expert comptable), 3 sortes de fiches, aucun circuit d'étapes.

## Le visiteur (sans compte)
- Ne voit rien

## Le dirigeant (responsable de l'app)
- Voit tout, crée et modifie : factures, écritures comptables, articles en stock

## L'expert comptable (invité par dirigeant)
- Voit tout, crée et modifie : écritures comptables

## Les informations de chaque fiche

- **Facture** : Numéro de facture (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Date de facture (date) · ☐ Client facturé (texte court) · ☐ Montant hors taxes (montant) · ☐ Montant TVA (montant) · ☐ Montant TTC (montant) · ☐ Date d'échéance (date)
- **Écriture comptable** : Libellé (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Date de l'écriture (date) · ☐ Numéro de compte (texte court) · ☐ Montant au débit (montant) · ☐ Montant au crédit (montant) · ☐ Journal (texte court) · ☐ Pièce justificative (texte court)
- **Article en stock** : Nom de l'article (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Référence (texte court) · ☐ Quantité en stock (nombre) · ☐ Prix unitaire de vente (montant) · ☐ Prix d'achat (montant) · ☐ Seuil d'alerte de stock (nombre) · ☐ Description (texte long)

## Questions

- L'expert comptable verra toutes les écritures comptables, pas seulement celles qui le concernent — d'accord ?
- Votre brief ne disait pas comment reconnaître certaines fiches ; nous avons choisi : facture → « Numéro de facture » · écriture comptable → « Libellé » · article en stock → « Nom de l'article »

## Pas encore dans notre stock (vos mots)

- Facturation (émission de factures) — « faire de la facturation »
- Comptabilité — « la comptabilité »
- Gestion financière — « la gestion financière »
- Version hybride (mobile) de l'application dans un second temps — « puis hybride plus tard »
- Option de saisie automatique — « une option de saisie automatique »

---

## Volet concepteur

### Pour répondre (`python -m usine.miroir repondre <lecture> id=valeur …`)

- `registre_entier:expert_comptable:EcritureComptable` = oui | non
- `nom:Facture:numero` = oui | <nouveau nom>  (facture → « Numéro de facture »)
- `nom:EcritureComptable:libelle` = oui | <nouveau nom>  (écriture comptable → « Libellé »)
- `nom:Article:nom` = oui | <nouveau nom>  (article en stock → « Nom de l'article »)
- `garder:Facture:Date de facture` = oui | non
- `garder:Facture:Client facturé` = oui | non
- `garder:Facture:Montant hors taxes` = oui | non
- `garder:Facture:Montant TVA` = oui | non
- `garder:Facture:Montant TTC` = oui | non
- `garder:Facture:Date d'échéance` = oui | non
- `garder:EcritureComptable:Date de l'écriture` = oui | non
- `garder:EcritureComptable:Numéro de compte` = oui | non
- `garder:EcritureComptable:Montant au débit` = oui | non
- `garder:EcritureComptable:Montant au crédit` = oui | non
- `garder:EcritureComptable:Journal` = oui | non
- `garder:EcritureComptable:Pièce justificative` = oui | non
- `garder:Article:Référence` = oui | non
- `garder:Article:Quantité en stock` = oui | non
- `garder:Article:Prix unitaire de vente` = oui | non
- `garder:Article:Prix d'achat` = oui | non
- `garder:Article:Seuil d'alerte de stock` = oui | non
- `garder:Article:Description` = oui | non

### Pourquoi chaque droit

- dirigeant / Facture : tient le registre (supprimer : seulement si le brief le dit) — « faire de la facturation »
- dirigeant / EcritureComptable : tient le registre (supprimer : seulement si le brief le dit) — « la possibilité de rajouter un expert comptable »
- dirigeant / Article : tient le registre (supprimer : seulement si le brief le dit) — « la gestion de stock »
- expert_comptable / EcritureComptable : tient le registre (supprimer : seulement si le brief le dit) — « la possibilité de rajouter un expert comptable »
