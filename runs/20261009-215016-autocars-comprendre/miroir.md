# Gestion Autocars — ce que l'usine a compris

En bref : 1 rôle (L'administrateur), 5 sortes de fiches, aucun circuit d'étapes.

## Le visiteur (sans compte)
- Ne voit rien

## L'administrateur (responsable de l'app)
- Voit tout, crée et modifie : chauffeurs, véhicules, clients, courses, factures

## Les informations de chaque fiche

- **Chauffeur** : Nom (texte court) ◦ choisi par nous · Amplitudes (texte long) · Couleur (texte court)
  - proposé (à cocher) : ☐ Email (e-mail) · ☐ Téléphone (téléphone)
- **Véhicule** : Nom (texte court) ◦ choisi par nous · Couleur (texte court)
  - proposé (à cocher) : ☐ Immatriculation (texte court) · ☐ Capacité (nombre)
- **Client** : Nom (texte court) ◦ choisi par nous · Coordonnées (texte long) · Reste dû ou avoir en cours (montant)
  - proposé (à cocher) : ☐ Adresse (texte long) · ☐ Email (e-mail) · ☐ Téléphone (téléphone)
- **Course** : Intitulé (texte court) ◦ choisi par nous
  - relié à : client, chauffeur, véhicule
  - proposé (à cocher) : ☐ Programme (texte long) · ☐ Date et heure de départ (date et heure) · ☐ Lieu de départ (texte court) · ☐ Lieu d'arrivée (texte court)
- **Facture** : Référence (texte court) ◦ choisi par nous
  - relié à : client, course
  - proposé (à cocher) : ☐ Montant (montant) · ☐ Numéro de facture EBP (texte court)

## Questions

- Votre brief ne disait pas comment reconnaître certaines fiches ; nous avons choisi : chauffeur → « Nom » · véhicule → « Nom » · client → « Nom » · course → « Intitulé » · facture → « Référence »

## Pas encore dans notre stock (vos mots)

- Planning des chauffeurs et véhicules — « logiciel de gestion de planning »
- Gestion des amplitudes chauffeurs dans le planning — « Établissement de planning comprenant les amplitudes chauffeurs »
- Affichage ou calcul des pauses obligatoires légales — « affichant les temps de pauses obligatoires demandés par la loi »
- Codes couleurs par chauffeurs et véhicules — « Codes couleurs par chauffeurs et par véhicules »
- Suivi de facturation automatique — « Suivi de facturation automatique »
- Envoi des programmes aux chauffeurs depuis le logiciel — « Possibilité d'envoyer directement depuis le logiciel les programmes aux chauffeurs »
- Transmission de données vers EBP — « Transmission depuis le logiciel des données pour facturation au logiciel EBP »
- Suivi du reste dû ou des avoirs clients — « reste dû ou avoir en cours »

---

## Volet concepteur

### Pour répondre (`python -m usine.miroir repondre <lecture> id=valeur …`)

- `nom:Chauffeur:nom` = oui | <nouveau nom>  (chauffeur → « Nom »)
- `nom:Vehicule:nom` = oui | <nouveau nom>  (véhicule → « Nom »)
- `nom:Client:nom` = oui | <nouveau nom>  (client → « Nom »)
- `nom:Course:intitule` = oui | <nouveau nom>  (course → « Intitulé »)
- `nom:Facture:reference` = oui | <nouveau nom>  (facture → « Référence »)
- `garder:Chauffeur:Email` = oui | non
- `garder:Chauffeur:Téléphone` = oui | non
- `garder:Vehicule:Immatriculation` = oui | non
- `garder:Vehicule:Capacité` = oui | non
- `garder:Client:Adresse` = oui | non
- `garder:Client:Email` = oui | non
- `garder:Client:Téléphone` = oui | non
- `garder:Course:Programme` = oui | non
- `garder:Course:Date et heure de départ` = oui | non
- `garder:Course:Lieu de départ` = oui | non
- `garder:Course:Lieu d'arrivée` = oui | non
- `garder:Facture:Montant` = oui | non
- `garder:Facture:Numéro de facture EBP` = oui | non

### Pourquoi chaque droit

- administrateur / Chauffeur : tient le registre (supprimer : seulement si le brief le dit) — « amplitudes chauffeurs »
- administrateur / Vehicule : tient le registre (supprimer : seulement si le brief le dit) — « par véhicules »
- administrateur / Client : tient le registre (supprimer : seulement si le brief le dit) — « Création de fiches clients pour les réguliers comprenant l'intégralité des informations »
- administrateur / Course : tient le registre (supprimer : seulement si le brief le dit) — « courses précédentes »
- administrateur / Facture : tient le registre (supprimer : seulement si le brief le dit) — « Suivi de facturation automatique »
