# Union sportive — ce que l'usine a compris

En bref : 1 rôle (L'administrateur), 7 sortes de fiches, 4 circuits d'étapes.

## Le visiteur (sans compte)
- Voit tout : Activités

## L'administrateur (responsable de l'app)
- Voit tout, crée et modifie : Activités, Participants, Inscriptions aux activités
- Adhérents : voit tout, en crée, les modifie, les supprime, les fait passer de « actif » à « inactif », les fait passer de « inactif » à « actif »
- Adhésions : voit tout, en crée, les modifie, les fait passer de « en attente de paiement » à « active »
- Paiements : voit tout, en crée, les modifie, les fait passer de « en attente » à « confirmé »
- Homologations : voit tout, en crée, les modifie, les fait passer de « en attente » à « validée »

## Les étapes

- L'adhérent passe par : « actif » → « inactif »
  - L'administrateur fait passer de « actif » à « inactif »
  - L'administrateur fait passer de « inactif » à « actif »
- L'adhésion passe par : « en attente de paiement » → « active »
  - L'administrateur fait passer de « en attente de paiement » à « active »
- Le paiement passe par : « en attente » → « confirmé »
  - L'administrateur fait passer de « en attente » à « confirmé »
- L'homologation passe par : « en attente » → « validée »
  - L'administrateur fait passer de « en attente » à « validée »

## Les informations de chaque fiche

- **Adhérent** : Nom (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Prénom (texte court) · ☐ Date de naissance (date) · ☐ Email (e-mail) · ☐ Téléphone (téléphone) · ☐ Adresse (texte long) · ☐ Consentement RGPD (oui / non)
- **Adhésion** : Année (nombre) · Cotisation (montant) · Date de début de validité (date) · Date de fin de validité (date)
  - relié à : Adhérent
  - proposé (à cocher) : ☐ Mode de renouvellement (choix) · ☐ Catégorie d'adhésion (texte court)
- **Activité** : Intitulé (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Date et heure (date et heure) · ☐ Lieu (texte court) · ☐ Description (texte long) · ☐ Tarif (montant) · ☐ Annulée (oui / non) · ☐ Nombre de places (nombre)
- **Participant** : Nom (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Prénom (texte court) · ☐ Email (e-mail) · ☐ Téléphone (téléphone) · ☐ Date de naissance (date)
- **Inscription à une activité** : Référence (texte court) ◦ choisi par nous
  - relié à : Participant, Activité
  - proposé (à cocher) : ☐ Remarque (texte long)
- **Paiement** : Référence (texte court) ◦ choisi par nous
  - relié à : Adhésion, Inscription à une activité
  - proposé (à cocher) : ☐ Montant (montant) · ☐ Date de paiement (date) · ☐ Mode de paiement (choix) · ☐ Référence de transaction en ligne (texte court)
- **Homologation** : Référence (texte court) ◦ choisi par nous
  - relié à : Inscription à une activité, Paiement
  - proposé (à cocher) : ☐ Date d'homologation (date) · ☐ Numéro d'homologation (texte court) · ☐ Commentaire (texte long)

## Questions

- Les visiteurs sans compte pourront consulter toutes les Activités — d'accord ? (si certains ne doivent pas être visibles, par exemple des brouillons, répondez non)
- Votre brief ne disait pas comment reconnaître certaines fiches ; nous avons choisi : Adhérent → « Nom » · Activité → « Intitulé » · Participant → « Nom » · Inscription à une activité → « Référence » · Paiement → « Référence » · Homologation → « Référence »

## Pas encore dans notre stock (vos mots)

- Paiement en ligne via un module intégré — « intégration d'un module de paiement en ligne »
- Validation d'une adhésion ou d'une activité bloquée tant que le paiement n'est pas confirmé — « Vérification du paiement avant activation ... Validation d'activité ou d'adhésion uniquement après paiement confirmé »
- Renouvellement automatique des adhésions — « Renouvellement automatique ou manuel »
- Vue calendrier des activités, consultable aussi par le public — « Calendrier d'activités »
- Exports CSV/Excel des données, filtrables par période — « Export par période ... Export CSV/Excel (adhérents, adhésions, activités, homologations) »
- Tableaux de bord de suivi — « Tableaux de bord de suivi »
- Conformité RGPD (conservation, droits des personnes) — « Respect du RGPD »

---

## Volet concepteur

### Pour répondre (`python -m usine.miroir repondre <lecture> id=valeur …`)

- `visiteur:visitor:Activite` = oui | non
- `nom:Adherent:nom` = oui | <nouveau nom>  (Adhérent → « Nom »)
- `nom:Activite:intitule` = oui | <nouveau nom>  (Activité → « Intitulé »)
- `nom:Participant:nom` = oui | <nouveau nom>  (Participant → « Nom »)
- `nom:Inscription:reference` = oui | <nouveau nom>  (Inscription à une activité → « Référence »)
- `nom:Paiement:reference` = oui | <nouveau nom>  (Paiement → « Référence »)
- `nom:Homologation:reference` = oui | <nouveau nom>  (Homologation → « Référence »)
- `garder:Adherent:Prénom` = oui | non
- `garder:Adherent:Date de naissance` = oui | non
- `garder:Adherent:Email` = oui | non
- `garder:Adherent:Téléphone` = oui | non
- `garder:Adherent:Adresse` = oui | non
- `garder:Adherent:Consentement RGPD` = oui | non
- `garder:Adhesion:Mode de renouvellement` = oui | non
- `garder:Adhesion:Catégorie d'adhésion` = oui | non
- `garder:Activite:Date et heure` = oui | non
- `garder:Activite:Lieu` = oui | non
- `garder:Activite:Description` = oui | non
- `garder:Activite:Tarif` = oui | non
- `garder:Activite:Annulée` = oui | non
- `garder:Activite:Nombre de places` = oui | non
- `garder:Participant:Prénom` = oui | non
- `garder:Participant:Email` = oui | non
- `garder:Participant:Téléphone` = oui | non
- `garder:Participant:Date de naissance` = oui | non
- `garder:Inscription:Remarque` = oui | non
- `garder:Paiement:Montant` = oui | non
- `garder:Paiement:Date de paiement` = oui | non
- `garder:Paiement:Mode de paiement` = oui | non
- `garder:Paiement:Référence de transaction en ligne` = oui | non
- `garder:Homologation:Date d'homologation` = oui | non
- `garder:Homologation:Numéro d'homologation` = oui | non
- `garder:Homologation:Commentaire` = oui | non

### Pourquoi chaque droit

- visitor / Activite : catalogue public : visible des visiteurs ; exception : « Affichage public consultable sur tous supports » — « Gestion interne : création, modification, annulation » « Affichage public consultable sur tous supports »
- administrateur / Activite : préréglage catalogue : visible de tous les connectés ; gestionnaire du catalogue (supprimer : seulement si le brief le dit) ; exception : « Gestion interne : création, modification, annulation » ; exception : « Gestion interne : création, modification, annulation » — « Gestion interne : création, modification, annulation » « Gestion interne : création, modification, annulation » « Gestion interne : création, modification, annulation »
- administrateur / Participant : tient le registre (supprimer : seulement si le brief le dit) — « Suivi des inscrits aux activités »
- administrateur / Inscription : tient le registre (supprimer : seulement si le brief le dit) ; exception : « Suivi des inscrits aux activités » — « Lien entre participant, activité et statut d'homologation » « Suivi des inscrits aux activités »
- administrateur / Adherent : tient le registre (supprimer : seulement si le brief le dit) ; fait évoluer l'état des fiches du registre ; exception : « Création, modification, suppression de fiches membres » ; exception : « Création, modification, suppression de fiches membres » ; exception : « Création, modification, suppression de fiches membres » — « Création, modification, suppression de fiches membres » « Statut actif/inactif » « Création, modification, suppression de fiches membres » « Création, modification, suppression de fiches membres » « Création, modification, suppression de fiches membres »
- administrateur / Adhesion : tient le registre (supprimer : seulement si le brief le dit) ; fait évoluer l'état des fiches du registre ; exception : « Enregistrement des adhésions » ; exception : « Validation d'activité ou d'adhésion uniquement après paiement confirmé » — « Enregistrement des adhésions (année, cotisation, dates de validité) » « Validation d'activité ou d'adhésion uniquement après paiement confirmé » « Enregistrement des adhésions » « Validation d'activité ou d'adhésion uniquement après paiement confirmé »
- administrateur / Paiement : tient le registre (supprimer : seulement si le brief le dit) ; fait évoluer l'état des fiches du registre ; exception : « Saisie manuelle » — « Validation d'activité ou d'adhésion uniquement après paiement confirmé » « Saisie manuelle ou intégration d'un module de paiement en ligne » « Saisie manuelle »
- administrateur / Homologation : tient le registre (supprimer : seulement si le brief le dit) ; fait évoluer l'état des fiches du registre ; exception : « Validation d'une activité uniquement après paiement » — « Validation d'une activité uniquement après paiement » « Validation d'une activité uniquement après paiement »
