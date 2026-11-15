# Gestion des formations — ce que l'usine a compris

En bref : 1 rôle (Le responsable de l'organisme de formation), 10 sortes de fiches, 1 circuit d'étapes.

## Le visiteur (sans compte)
- Ne voit rien

## Le responsable de l'organisme de formation (responsable de l'app)
- Voit tout, crée et modifie : entités prescriptrices, stagiaires, formateurs, salles, affectations aux sessions, factures, bilans, écritures comptables
- Voit tout, crée, modifie et supprime : étapes du rétroplanning (dans chaque session de formation)
- Sessions de formation : voit tout, en crée, les modifie, les fait passer de « convocation téléphonique » à « envoi du contrat », les fait passer de « envoi du contrat » à « planification (date, formateur, salle) », les fait passer de « planification (date, formateur, salle) » à « facturation », les fait passer de « facturation » à « bilan établi »

## Les étapes

- La session de formation passe par : « convocation téléphonique » → « envoi du contrat » → « planification (date, formateur, salle) » → « facturation » → « bilan établi »
  - Le responsable de l'organisme de formation fait passer de « convocation téléphonique » à « envoi du contrat »
  - Le responsable de l'organisme de formation fait passer de « envoi du contrat » à « planification (date, formateur, salle) »
  - Le responsable de l'organisme de formation fait passer de « planification (date, formateur, salle) » à « facturation »
  - Le responsable de l'organisme de formation fait passer de « facturation » à « bilan établi »

## Les informations de chaque fiche

- **Entité prescriptrice** : Nom (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Adresse (texte long) · ☐ Email (e-mail) · ☐ Téléphone (téléphone) · ☐ Nom du contact (texte court)
- **Stagiaire** : Nom (texte court) ◦ choisi par nous
  - relié à : entité prescriptrice
  - proposé (à cocher) : ☐ Prénom (texte court) · ☐ Téléphone (téléphone) · ☐ Email (e-mail) · ☐ Adresse (texte long)
- **Formateur** : Nom (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Prénom (texte court) · ☐ Téléphone (téléphone) · ☐ Email (e-mail) · ☐ Domaines de formation (texte court)
- **Salle** : Nom (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Capacité (nombre) · ☐ Adresse (texte court)
- **Session de formation** : Date (date, facultatif)
  - relié à : formateur, salle
  - proposé (à cocher) : ☐ Intitulé de la formation (texte court) · ☐ Date de fin (date) · ☐ Durée (heures) (nombre) · ☐ Nombre de places (nombre)
- **Affectation à une session** : Intitulé (texte court) ◦ choisi par nous
  - relié à : stagiaire, session de formation
  - proposé (à cocher) : ☐ Convocation téléphonique faite (oui / non) · ☐ Contrat envoyé (oui / non) · ☐ Présence (oui / non)
- **Étape du rétroplanning** : Intitulé (texte court) ◦ choisi par nous
  - relié à : dans chaque session de formation
  - proposé (à cocher) : ☐ Date prévue (date) · ☐ Réalisée (oui / non) · ☐ Date de réalisation (date) · ☐ Commentaire (texte long)
- **Facture** : Numéro (texte court) ◦ choisi par nous
  - relié à : session de formation, entité prescriptrice
  - proposé (à cocher) : ☐ Montant (montant) · ☐ Date d'émission (date) · ☐ Date d'échéance (date) · ☐ Payée (oui / non)
- **Bilan** : Intitulé (texte court) ◦ choisi par nous
  - relié à : session de formation, entité prescriptrice
  - proposé (à cocher) : ☐ Contenu du bilan (texte long) · ☐ Date d'envoi à l'entité (date)
- **Écriture comptable** : Libellé (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Date de l'écriture (date) · ☐ Montant (montant) · ☐ Compte (texte court) · ☐ Sens (débit ou crédit) (texte court) · ☐ Référence de la pièce (texte court)

## Questions

- Votre brief ne disait pas comment reconnaître certaines fiches ; nous avons choisi : entité prescriptrice → « Nom » · stagiaire → « Nom » · formateur → « Nom » · salle → « Nom » · affectation à une session → « Intitulé » · étape du rétroplanning → « Intitulé » · facture → « Numéro » · bilan → « Intitulé » · écriture comptable → « Libellé »

## Pas encore dans notre stock (vos mots)

- Rétroplanning d'organisation de chaque session (échéancier des étapes à mener) — « il y a un rétroplanning d'organisation de la session »
- Planifier la date d'une session en fonction du formateur et de la salle (calendrier, disponibilités) — « planifier la date avec le formateur et la salle »
- Envoi d'un contrat (document à produire et à transmettre) — « envoi contrat »
- Facturation — « puis la facturation »
- Établissement d'un bilan pour l'entité qui envoie les stagiaires — « l'établissement d'un bilan pour l'entité de base »
- Gestion comptable associée — « on a besoin d'une gestion comptable associée »

---

## Volet concepteur

### Pour répondre (`python -m usine.miroir repondre <lecture> id=valeur …`)

- `nom:EntitePrescriptrice:nom` = oui | <nouveau nom>  (entité prescriptrice → « Nom »)
- `nom:Stagiaire:nom` = oui | <nouveau nom>  (stagiaire → « Nom »)
- `nom:Formateur:nom` = oui | <nouveau nom>  (formateur → « Nom »)
- `nom:Salle:nom` = oui | <nouveau nom>  (salle → « Nom »)
- `nom:Affectation:intitule` = oui | <nouveau nom>  (affectation à une session → « Intitulé »)
- `nom:EtapeRetroplanning:intitule` = oui | <nouveau nom>  (étape du rétroplanning → « Intitulé »)
- `nom:Facture:numero` = oui | <nouveau nom>  (facture → « Numéro »)
- `nom:Bilan:intitule` = oui | <nouveau nom>  (bilan → « Intitulé »)
- `nom:EcritureComptable:libelle` = oui | <nouveau nom>  (écriture comptable → « Libellé »)
- `garder:EntitePrescriptrice:Adresse` = oui | non
- `garder:EntitePrescriptrice:Email` = oui | non
- `garder:EntitePrescriptrice:Téléphone` = oui | non
- `garder:EntitePrescriptrice:Nom du contact` = oui | non
- `garder:Stagiaire:Prénom` = oui | non
- `garder:Stagiaire:Téléphone` = oui | non
- `garder:Stagiaire:Email` = oui | non
- `garder:Stagiaire:Adresse` = oui | non
- `garder:Formateur:Prénom` = oui | non
- `garder:Formateur:Téléphone` = oui | non
- `garder:Formateur:Email` = oui | non
- `garder:Formateur:Domaines de formation` = oui | non
- `garder:Salle:Capacité` = oui | non
- `garder:Salle:Adresse` = oui | non
- `garder:SessionFormation:Intitulé de la formation` = oui | non
- `garder:SessionFormation:Date de fin` = oui | non
- `garder:SessionFormation:Durée (heures)` = oui | non
- `garder:SessionFormation:Nombre de places` = oui | non
- `garder:Affectation:Convocation téléphonique faite` = oui | non
- `garder:Affectation:Contrat envoyé` = oui | non
- `garder:Affectation:Présence` = oui | non
- `garder:EtapeRetroplanning:Date prévue` = oui | non
- `garder:EtapeRetroplanning:Réalisée` = oui | non
- `garder:EtapeRetroplanning:Date de réalisation` = oui | non
- `garder:EtapeRetroplanning:Commentaire` = oui | non
- `garder:Facture:Montant` = oui | non
- `garder:Facture:Date d'émission` = oui | non
- `garder:Facture:Date d'échéance` = oui | non
- `garder:Facture:Payée` = oui | non
- `garder:Bilan:Contenu du bilan` = oui | non
- `garder:Bilan:Date d'envoi à l'entité` = oui | non
- `garder:EcritureComptable:Date de l'écriture` = oui | non
- `garder:EcritureComptable:Montant` = oui | non
- `garder:EcritureComptable:Compte` = oui | non
- `garder:EcritureComptable:Sens (débit ou crédit)` = oui | non
- `garder:EcritureComptable:Référence de la pièce` = oui | non

### Pourquoi chaque droit

- responsable / EntitePrescriptrice : tient le registre (supprimer : seulement si le brief le dit) — « une entité nous envoie des stagiaires »
- responsable / Stagiaire : tient le registre (supprimer : seulement si le brief le dit) — « une entité nous envoie des stagiaires »
- responsable / Formateur : tient le registre (supprimer : seulement si le brief le dit) — « planifier la date avec le formateur »
- responsable / Salle : préréglage catalogue : visible de tous les connectés ; gestionnaire du catalogue (supprimer : seulement si le brief le dit) — « avec le formateur et la salle »
- responsable / Affectation : tient le registre (supprimer : seulement si le brief le dit) — « des stagiaires que nous répartissons sur des sessions de formation »
- responsable / Facture : tient le registre (supprimer : seulement si le brief le dit) — « puis la facturation »
- responsable / Bilan : tient le registre (supprimer : seulement si le brief le dit) — « l'établissement d'un bilan pour l'entité de base »
- responsable / EcritureComptable : tient le registre (supprimer : seulement si le brief le dit) — « on a besoin d'une gestion comptable associée »
- responsable / EtapeRetroplanning : enfant de session de formation : même visibilité que le parent, géré par qui gère le parent — « planifier la date avec le formateur et la salle » « convocation téléphonique, envoi contrat, planifier la date avec le formateur et la salle »
- responsable / SessionFormation : tient le registre (supprimer : seulement si le brief le dit) ; fait évoluer l'état des fiches du registre — « planifier la date avec le formateur et la salle » « convocation téléphonique, envoi contrat, planifier la date avec le formateur et la salle »
