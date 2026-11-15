# Union sportive — ce que l'usine a compris

En bref : 1 rôle (L'administrateur de l'association), 8 sortes de fiches, 4 circuits d'étapes.

## Le visiteur (sans compte)
- Voit tout : activités

## L'administrateur de l'association (responsable de l'app)
- Voit tout, crée et modifie : participants, participations à une activité, homologations
- a son profil administrateur, créé automatiquement, qu'il peut modifier
- Adhérents : voit tout, en crée, les modifie, les supprime, les fait passer de « actif » à « inactif », les fait passer de « inactif » à « actif »
- Adhésions : voit tout, en crée, les modifie, les fait passer de « enregistrée » à « activée »
- Activités : voit tout, en crée, les modifie, les fait passer de « créée » à « annulée »
- Paiements : voit tout, en crée, les modifie, les fait passer de « saisi » à « confirmé »

## Les étapes

- L'adhérent passe par : « actif » → « inactif »
  - L'administrateur de l'association fait passer de « actif » à « inactif »
  - L'administrateur de l'association fait passer de « inactif » à « actif »
- L'adhésion passe par : « enregistrée » → « activée »
  - L'administrateur de l'association fait passer de « enregistrée » à « activée »
- L'activité passe par : « créée » → « annulée »
  - L'administrateur de l'association fait passer de « créée » à « annulée »
- Le paiement passe par : « saisi » → « confirmé »
  - L'administrateur de l'association fait passer de « saisi » à « confirmé »

## Les informations de chaque fiche

- **Profil administrateur** : Nom (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Email (e-mail)
- **Adhérent** : Nom (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Prénom (texte court) · ☐ Email (e-mail) · ☐ Téléphone (téléphone)
- **Adhésion** : Année (nombre) · Cotisation (montant) · Date de début de validité (date) · Date de fin de validité (date) · Mode de renouvellement (choix parmi : automatique, manuel)
  - relié à : adhérent
- **Participant** : Nom (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Prénom (texte court) · ☐ Email (e-mail)
- **Activité** : Intitulé (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Description (texte long) · ☐ Date de l'activité (date) · ☐ Lieu (texte court)
- **Participation à une activité** : Statut d'homologation (texte court)
  - relié à : participant, activité
- **Paiement** : Référence (texte court) ◦ choisi par nous
  - relié à : adhésion, activité
  - proposé (à cocher) : ☐ Montant (montant) · ☐ Mode de paiement (texte court)
- **Homologation** : Intitulé (texte court) ◦ choisi par nous
  - relié à : participation à une activité
  - proposé (à cocher) : ☐ Commentaire (texte long)

## Questions

- Les visiteurs sans compte pourront consulter toutes les activités — d'accord ? (si certains ne doivent pas être visibles, par exemple des brouillons, répondez non)
- Votre brief ne disait pas comment reconnaître certaines fiches ; nous avons choisi : profil administrateur → « Nom » · adhérent → « Nom » · participant → « Nom » · activité → « Intitulé » · paiement → « Référence » · homologation → « Intitulé »

## Pas encore dans notre stock (vos mots)

- Renouvellement automatique des adhésions — « Renouvellement automatique ou manuel »
- Vérification/condition d'activation selon paiement — « Vérification du paiement avant activation »
- Export des adhésions par période — « Export par période »
- Calendrier d'activités — « Calendrier d'activités »
- Affichage public sous forme de calendrier — « Affichage public consultable sur tous supports »
- Gestion des annulations d'activités — « Gestion interne : création, modification, annulation »
- Saisie manuelle de paiements — « Saisie manuelle ou intégration d'un module de paiement en ligne »
- Intégration d'un module de paiement en ligne — « intégration d'un module de paiement en ligne »
- Validation d'activité ou d'adhésion conditionnée au paiement confirmé — « Validation d'activité ou d'adhésion uniquement après paiement confirmé »
- Validation d'une activité conditionnée au paiement — « Validation d'une activité uniquement après paiement »
- Exports CSV/Excel — « Export CSV/Excel (adhérents, adhésions, activités, homologations) »
- Tableaux de bord de suivi — « Tableaux de bord de suivi »

---

## Volet concepteur

### Pour répondre (`python -m usine.miroir repondre <lecture> id=valeur …`)

- `visiteur:visitor:Activite` = oui | non
- `nom:ProfilAdministrateur:nom` = oui | <nouveau nom>  (profil administrateur → « Nom »)
- `nom:Adherent:nom` = oui | <nouveau nom>  (adhérent → « Nom »)
- `nom:Participant:nom` = oui | <nouveau nom>  (participant → « Nom »)
- `nom:Activite:intitule` = oui | <nouveau nom>  (activité → « Intitulé »)
- `nom:Paiement:reference` = oui | <nouveau nom>  (paiement → « Référence »)
- `nom:Homologation:intitule` = oui | <nouveau nom>  (homologation → « Intitulé »)
- `garder:ProfilAdministrateur:Email` = oui | non
- `garder:Adherent:Prénom` = oui | non
- `garder:Adherent:Email` = oui | non
- `garder:Adherent:Téléphone` = oui | non
- `garder:Participant:Prénom` = oui | non
- `garder:Participant:Email` = oui | non
- `garder:Activite:Description` = oui | non
- `garder:Activite:Date de l'activité` = oui | non
- `garder:Activite:Lieu` = oui | non
- `garder:Paiement:Montant` = oui | non
- `garder:Paiement:Mode de paiement` = oui | non
- `garder:Homologation:Commentaire` = oui | non

### Pourquoi chaque droit

- visitor / Activite : registre public : visible de tous ; exception : « Affichage public consultable sur tous supports » — « Calendrier d'activités :
- Affichage public consultable sur tous supports
- Gestion interne : création, modification, annulation » « Affichage public consultable sur tous supports »
- administrateur / Participant : tient le registre (supprimer : seulement si le brief le dit) — « Gestion des participants :
- Suivi des inscrits aux activités »
- administrateur / ParticipationActivite : tient le registre (supprimer : seulement si le brief le dit) — « Suivi des inscrits aux activités
- Lien entre participant, activité et statut d'homologation »
- administrateur / Homologation : tient le registre (supprimer : seulement si le brief le dit) ; exception : « Interface d'administration avec authentification sécurisée » — « Homologations :
- Validation d'une activité uniquement après paiement
- Historique complet des homologations » « Interface d'administration avec authentification sécurisée »
- administrateur / ProfilAdministrateur : préréglage profil : sa propre fiche, créée automatiquement — « Interface d'administration avec authentification sécurisée »
- administrateur / Adherent : tient le registre (supprimer : seulement si le brief le dit) ; fait évoluer l'état des fiches du registre ; exception : « Interface d'administration avec authentification sécurisée » ; exception : « Interface d'administration avec authentification sécurisée » ; exception : « Interface d'administration avec authentification sécurisée » — « Création, modification, suppression de fiches membres » « Statut actif/inactif » « Interface d'administration avec authentification sécurisée » « Interface d'administration avec authentification sécurisée » « Interface d'administration avec authentification sécurisée »
- administrateur / Adhesion : tient le registre (supprimer : seulement si le brief le dit) ; fait évoluer l'état des fiches du registre ; exception : « Enregistrement des adhésions (année, cotisation, dates de validité) » ; exception : « Interface d'administration avec authentification sécurisée » ; exception : « Validation d'activité ou d'adhésion uniquement après paiement confirmé » ; exception : « Interface d'administration avec authentification sécurisée » — « Enregistrement des adhésions (année, cotisation, dates de validité) » « Vérification du paiement avant activation » « Enregistrement des adhésions (année, cotisation, dates de validité) » « Interface d'administration avec authentification sécurisée » « Validation d'activité ou d'adhésion uniquement après paiement confirmé » « Interface d'administration avec authentification sécurisée »
- administrateur / Activite : tient le registre (supprimer : seulement si le brief le dit) ; fait évoluer l'état des fiches du registre ; exception : « Interface d'administration avec authentification sécurisée » ; exception : « Interface d'administration avec authentification sécurisée » ; exception : « Interface d'administration avec authentification sécurisée » ; exception : « Validation d'activité ou d'adhésion uniquement après paiement confirmé » ; exception : « Interface d'administration avec authentification sécurisée » — « Calendrier d'activités :
- Affichage public consultable sur tous supports
- Gestion interne : création, modification, annulation » « Gestion interne : création, modification, annulation » « Interface d'administration avec authentification sécurisée » « Interface d'administration avec authentification sécurisée » « Interface d'administration avec authentification sécurisée » « Validation d'activité ou d'adhésion uniquement après paiement confirmé » « Interface d'administration avec authentification sécurisée »
- administrateur / Paiement : tient le registre (supprimer : seulement si le brief le dit) ; fait évoluer l'état des fiches du registre ; exception : « Saisie manuelle ou intégration d'un module de paiement en ligne » — « Paiements :
- Saisie manuelle ou intégration d'un module de paiement en ligne
- Validation d'activité ou d'adhésion uniquement après paiement confirmé » « Saisie manuelle ou intégration d'un module de paiement en ligne
- Validation d'activité ou d'adhésion uniquement après paiement confirmé » « Saisie manuelle ou intégration d'un module de paiement en ligne »
