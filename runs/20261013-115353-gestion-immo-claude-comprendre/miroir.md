# Gestion locative — ce que l'usine a compris

En bref : 1 rôle (Le gestionnaire), 8 sortes de fiches, aucun circuit d'étapes.

## Le visiteur (sans compte)
- Ne voit rien

## Le gestionnaire (responsable de l'app)
- Voit tout, crée et modifie : Propriétaires, Biens, Locataires, Encaissements de loyer, Reversements de loyer, Quittances, Relevés de compte, Opérations bancaires

## Les informations de chaque fiche

- **Propriétaire** : Nom (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Prénom (texte court) · ☐ Adresse email (e-mail) · ☐ Téléphone (téléphone) · ☐ Adresse postale (texte long) · ☐ IBAN (texte court)
- **Bien** : Désignation (texte court) ◦ choisi par nous
  - relié à : Propriétaire
  - proposé (à cocher) : ☐ Adresse (texte long) · ☐ Type de bien (choix) · ☐ Surface (m²) (nombre) · ☐ Montant du loyer (montant) · ☐ Montant des charges (montant)
- **Locataire** : Nom (texte court) ◦ choisi par nous
  - relié à : Bien
  - proposé (à cocher) : ☐ Prénom (texte court) · ☐ Adresse email (e-mail) · ☐ Téléphone (téléphone) · ☐ Date d'entrée dans le logement (date) · ☐ Dépôt de garantie (montant)
- **Encaissement de loyer** : Référence (texte court) ◦ choisi par nous
  - relié à : Locataire, Bien
  - proposé (à cocher) : ☐ Montant encaissé (montant) · ☐ Date d'encaissement (date) · ☐ Période concernée (texte court) · ☐ Mode de paiement (choix)
- **Reversement de loyer** : Référence (texte court) ◦ choisi par nous
  - relié à : Propriétaire, Bien
  - proposé (à cocher) : ☐ Montant reversé (montant) · ☐ Date de reversement (date) · ☐ Honoraires de gestion déduits (montant) · ☐ Période concernée (texte court)
- **Quittance** : Numéro de quittance (texte court) ◦ choisi par nous
  - relié à : Locataire, Encaissement de loyer
  - proposé (à cocher) : ☐ Période (texte court) · ☐ Montant du loyer (montant) · ☐ Montant des charges (montant) · ☐ Date d'envoi (date)
- **Relevé de compte** : Intitulé (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Date de début de période (date) · ☐ Date de fin de période (date) · ☐ Solde (montant) · ☐ Date d'envoi (date)
- **Opération bancaire** : Libellé (texte court) ◦ choisi par nous
  - relié à : Encaissement de loyer, Reversement de loyer
  - proposé (à cocher) : ☐ Date de l'opération (date) · ☐ Montant (montant) · ☐ Sens (débit / crédit) (choix) · ☐ Rapprochée (oui / non)

## Questions

- Votre brief ne disait pas comment reconnaître certaines fiches ; nous avons choisi : Propriétaire → « Nom » · Bien → « Désignation » · Locataire → « Nom » · Encaissement de loyer → « Référence » · Reversement de loyer → « Référence » · Quittance → « Numéro de quittance » · Relevé de compte → « Intitulé » · Opération bancaire → « Libellé »

## Pas encore dans notre stock (vos mots)

- Automatiser des tâches (c'est l'objectif principal du brief) — « créer un logiciel permettant d'automatiser des taches »
- Rapprochement bancaire automatique (il faut un lien avec les données de la banque) — « automatiser le rapprochement bancaire »
- Encaissement des loyers — « l'encaissement des loyers »
- Reversement des loyers — « le reversement des loyers »
- Production des quittances de loyer — « envoyer automatiquement des quittances »
- Envoi automatique des quittances — « envoyer automatiquement des quittances »
- Production et envoi des relevés de compte — « relevé de compte etc.. »

---

## Volet concepteur

### Pour répondre (`python -m usine.miroir repondre <lecture> id=valeur …`)

- `nom:Proprietaire:nom` = oui | <nouveau nom>  (Propriétaire → « Nom »)
- `nom:Bien:designation` = oui | <nouveau nom>  (Bien → « Désignation »)
- `nom:Locataire:nom` = oui | <nouveau nom>  (Locataire → « Nom »)
- `nom:EncaissementLoyer:reference` = oui | <nouveau nom>  (Encaissement de loyer → « Référence »)
- `nom:ReversementLoyer:reference` = oui | <nouveau nom>  (Reversement de loyer → « Référence »)
- `nom:Quittance:numero` = oui | <nouveau nom>  (Quittance → « Numéro de quittance »)
- `nom:ReleveCompte:intitule` = oui | <nouveau nom>  (Relevé de compte → « Intitulé »)
- `nom:OperationBancaire:libelle` = oui | <nouveau nom>  (Opération bancaire → « Libellé »)
- `garder:Proprietaire:Prénom` = oui | non
- `garder:Proprietaire:Adresse email` = oui | non
- `garder:Proprietaire:Téléphone` = oui | non
- `garder:Proprietaire:Adresse postale` = oui | non
- `garder:Proprietaire:IBAN` = oui | non
- `garder:Bien:Adresse` = oui | non
- `garder:Bien:Type de bien` = oui | non
- `garder:Bien:Surface (m²)` = oui | non
- `garder:Bien:Montant du loyer` = oui | non
- `garder:Bien:Montant des charges` = oui | non
- `garder:Locataire:Prénom` = oui | non
- `garder:Locataire:Adresse email` = oui | non
- `garder:Locataire:Téléphone` = oui | non
- `garder:Locataire:Date d'entrée dans le logement` = oui | non
- `garder:Locataire:Dépôt de garantie` = oui | non
- `garder:EncaissementLoyer:Montant encaissé` = oui | non
- `garder:EncaissementLoyer:Date d'encaissement` = oui | non
- `garder:EncaissementLoyer:Période concernée` = oui | non
- `garder:EncaissementLoyer:Mode de paiement` = oui | non
- `garder:ReversementLoyer:Montant reversé` = oui | non
- `garder:ReversementLoyer:Date de reversement` = oui | non
- `garder:ReversementLoyer:Honoraires de gestion déduits` = oui | non
- `garder:ReversementLoyer:Période concernée` = oui | non
- `garder:Quittance:Période` = oui | non
- `garder:Quittance:Montant du loyer` = oui | non
- `garder:Quittance:Montant des charges` = oui | non
- `garder:Quittance:Date d'envoi` = oui | non
- `garder:ReleveCompte:Date de début de période` = oui | non
- `garder:ReleveCompte:Date de fin de période` = oui | non
- `garder:ReleveCompte:Solde` = oui | non
- `garder:ReleveCompte:Date d'envoi` = oui | non
- `garder:OperationBancaire:Date de l'opération` = oui | non
- `garder:OperationBancaire:Montant` = oui | non
- `garder:OperationBancaire:Sens (débit / crédit)` = oui | non
- `garder:OperationBancaire:Rapprochée` = oui | non

### Pourquoi chaque droit

- gestionnaire / Proprietaire : tient le registre (supprimer : seulement si le brief le dit) — « le reversement des loyers »
- gestionnaire / Bien : tient le registre (supprimer : seulement si le brief le dit) — « gestionnaire de biens immobilier »
- gestionnaire / Locataire : tient le registre (supprimer : seulement si le brief le dit) — « l'encaissement des loyers »
- gestionnaire / EncaissementLoyer : tient le registre (supprimer : seulement si le brief le dit) — « l'encaissement des loyers »
- gestionnaire / ReversementLoyer : tient le registre (supprimer : seulement si le brief le dit) — « le reversement des loyers »
- gestionnaire / Quittance : tient le registre (supprimer : seulement si le brief le dit) — « envoyer automatiquement des quittances »
- gestionnaire / ReleveCompte : tient le registre (supprimer : seulement si le brief le dit) — « relevé de compte »
- gestionnaire / OperationBancaire : tient le registre (supprimer : seulement si le brief le dit) — « automatiser le rapprochement bancaire »
