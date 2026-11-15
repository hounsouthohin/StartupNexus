# Gestion d’entreprise — ce que l'usine a compris

En bref : 3 rôles (L'administrateur, L'utilisateur, L'expert comptable), 4 sortes de fiches, aucun circuit d'étapes.

## Le visiteur (sans compte)
- Ne voit rien

## L'administrateur (responsable de l'app)
- Voit tout : factures, écritures comptables, opérations financières, articles de stock

## L'utilisateur (invité par administrateur)
- Voit tout, crée et modifie : factures, écritures comptables, opérations financières, articles de stock

## L'expert comptable (invité par administrateur)
- Voit tout, crée et modifie : écritures comptables

## Les informations de chaque fiche

- **Facture** : Intitulé (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Numéro de facture (texte court) · ☐ Date de facture (date) · ☐ Montant total (montant)
- **Écriture comptable** : Intitulé (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Libellé comptable (texte court) · ☐ Date d’écriture (date) · ☐ Montant (montant)
- **Opération financière** : Intitulé (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Date de l’opération (date) · ☐ Montant (montant) · ☐ Description (texte long)
- **Article de stock** : Intitulé (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Référence (texte court) · ☐ Quantité en stock (nombre) · ☐ Seuil d’alerte (nombre)

## Questions

- L'utilisateur verra toutes les factures, pas seulement celles qui le concernent — d'accord ? → **oui, nécessairement** : entité Facture (registre) : il faut au moins un acteur qui le tient (« manager »)
- L'utilisateur verra toutes les écritures comptables, pas seulement celles qui le concernent — d'accord ?
- L'utilisateur verra toutes les opérations financières, pas seulement celles qui le concernent — d'accord ? → **oui, nécessairement** : entité OperationFinanciere (registre) : il faut au moins un acteur qui le tient (« manager »)
- L'utilisateur verra tous les articles de stock, pas seulement ceux qui le concernent — d'accord ? → **oui, nécessairement** : entité ArticleStock (registre) : il faut au moins un acteur qui le tient (« manager »)
- L'expert comptable verra toutes les écritures comptables, pas seulement celles qui le concernent — d'accord ?
- Votre brief ne disait pas comment reconnaître certaines fiches ; nous avons choisi : facture → « Intitulé » · écriture comptable → « Intitulé » · opération financière → « Intitulé » · article de stock → « Intitulé »

## Pas encore dans notre stock (vos mots)

- Application hybride plus tard — « application web dans un premier temps puis hybride plus tard »
- Facturation — « faire de la facturation »
- Comptabilité — « la comptabilité »
- Gestion financière — « la gestion financière »
- Gestion de stock avec calculs de quantités/mouvements — « la gestion de stock »
- Saisie automatique — « une option de saisie automatique »

---

## Volet concepteur

### Pour répondre (`python -m usine.miroir repondre <lecture> id=valeur …`)

- `registre_entier:utilisateur:Facture` = oui
- `registre_entier:utilisateur:EcritureComptable` = oui | non
- `registre_entier:utilisateur:OperationFinanciere` = oui
- `registre_entier:utilisateur:ArticleStock` = oui
- `registre_entier:expert_comptable:EcritureComptable` = oui | non
- `nom:Facture:intitule` = oui | <nouveau nom>  (facture → « Intitulé »)
- `nom:EcritureComptable:intitule` = oui | <nouveau nom>  (écriture comptable → « Intitulé »)
- `nom:OperationFinanciere:intitule` = oui | <nouveau nom>  (opération financière → « Intitulé »)
- `nom:ArticleStock:intitule` = oui | <nouveau nom>  (article de stock → « Intitulé »)
- `garder:Facture:Numéro de facture` = oui | non
- `garder:Facture:Date de facture` = oui | non
- `garder:Facture:Montant total` = oui | non
- `garder:EcritureComptable:Libellé comptable` = oui | non
- `garder:EcritureComptable:Date d’écriture` = oui | non
- `garder:EcritureComptable:Montant` = oui | non
- `garder:OperationFinanciere:Date de l’opération` = oui | non
- `garder:OperationFinanciere:Montant` = oui | non
- `garder:OperationFinanciere:Description` = oui | non
- `garder:ArticleStock:Référence` = oui | non
- `garder:ArticleStock:Quantité en stock` = oui | non
- `garder:ArticleStock:Seuil d’alerte` = oui | non

### Pourquoi chaque droit

- administrateur / Facture : responsable de l'app : voit les registres de l'équipe (lecture) — « faire de la facturation »
- administrateur / EcritureComptable : responsable de l'app : voit les registres de l'équipe (lecture) — « rajouter un expert comptable »
- administrateur / OperationFinanciere : responsable de l'app : voit les registres de l'équipe (lecture) — « la gestion financière »
- administrateur / ArticleStock : responsable de l'app : voit les registres de l'équipe (lecture) — « la gestion de stock »
- utilisateur / Facture : tient le registre (supprimer : seulement si le brief le dit) — « faire de la facturation »
- utilisateur / EcritureComptable : tient le registre (supprimer : seulement si le brief le dit) — « rajouter un expert comptable »
- utilisateur / OperationFinanciere : tient le registre (supprimer : seulement si le brief le dit) — « la gestion financière »
- utilisateur / ArticleStock : tient le registre (supprimer : seulement si le brief le dit) — « la gestion de stock »
- expert_comptable / EcritureComptable : tient le registre (supprimer : seulement si le brief le dit) — « rajouter un expert comptable »
