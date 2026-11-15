# Gestion des autocars — ce que l'usine a compris

En bref : 1 rôle (Le gérant), 5 sortes de fiches, aucun circuit d'étapes.

## Le visiteur (sans compte)
- Ne voit rien

## Le gérant (responsable de l'app)
- Voit tout, crée et modifie : Clients, Chauffeurs, Véhicules, Courses, Factures

## Les informations de chaque fiche

- **Client** : Nom (texte court) ◦ choisi par nous · Coordonnées (texte long) · Reste dû (montant, facultatif) · Avoir en cours (montant, facultatif)
  - proposé (à cocher) : ☐ Téléphone (téléphone) · ☐ Email (e-mail) · ☐ Client régulier (oui / non)
- **Chauffeur** : Nom (texte court) ◦ choisi par nous · Couleur (texte court)
  - proposé (à cocher) : ☐ Prénom (texte court) · ☐ Téléphone (téléphone) · ☐ Email (e-mail)
- **Véhicule** : Immatriculation (texte court) ◦ choisi par nous · Couleur (texte court)
  - proposé (à cocher) : ☐ Marque et modèle (texte court) · ☐ Nombre de places (nombre)
- **Course** : Intitulé (texte court) ◦ choisi par nous
  - relié à : Client, Chauffeur, Véhicule
  - proposé (à cocher) : ☐ Date et heure de début (date et heure) · ☐ Date et heure de fin (date et heure) · ☐ Lieu de départ (texte court) · ☐ Destination (texte court) · ☐ Nombre de passagers (nombre) · ☐ Prix (montant)
- **Facture** : Numéro (texte court) ◦ choisi par nous
  - relié à : Client, Course
  - proposé (à cocher) : ☐ Montant (montant) · ☐ Date de facture (date) · ☐ Montant réglé (montant) · ☐ Proforma (oui / non) · ☐ Transmise à EBP (oui / non)

## Questions

- Votre brief ne disait pas comment reconnaître certaines fiches ; nous avons choisi : Client → « Nom » · Chauffeur → « Nom » · Véhicule → « Immatriculation » · Course → « Intitulé » · Facture → « Numéro »

## Pas encore dans notre stock (vos mots)

- Vue planning des chauffeurs — « Établissement de planning »
- Calcul des amplitudes des chauffeurs et des temps de pause obligatoires prévus par la loi — « comprenant les amplitudes chauffeurs, affichant les temps de pauses obligatoires demandés par la loi »
- Codes couleurs par chauffeur et par véhicule dans l'affichage du planning — « Codes couleurs par chauffeurs et par véhicules »
- Suivi automatique de la facturation — « Suivi de facturation automatique »
- Envoi des programmes aux chauffeurs directement depuis le logiciel — « Possibilité d'envoyer directement depuis le logiciel les programmes aux chauffeurs »
- Transmission des données de facturation au logiciel EBP pour établir les factures proforma — « Transmission depuis le logiciel des données pour facturation au logiciel EBP pour établir les factures proforma »
- Calcul du reste dû ou de l'avoir en cours sur la fiche client — « reste dû ou avoir en cours »

---

## Volet concepteur

### Pour répondre (`python -m usine.miroir repondre <lecture> id=valeur …`)

- `nom:Client:nom` = oui | <nouveau nom>  (Client → « Nom »)
- `nom:Chauffeur:nom` = oui | <nouveau nom>  (Chauffeur → « Nom »)
- `nom:Vehicule:immatriculation` = oui | <nouveau nom>  (Véhicule → « Immatriculation »)
- `nom:Course:intitule` = oui | <nouveau nom>  (Course → « Intitulé »)
- `nom:Facture:numero` = oui | <nouveau nom>  (Facture → « Numéro »)
- `garder:Client:Téléphone` = oui | non
- `garder:Client:Email` = oui | non
- `garder:Client:Client régulier` = oui | non
- `garder:Chauffeur:Prénom` = oui | non
- `garder:Chauffeur:Téléphone` = oui | non
- `garder:Chauffeur:Email` = oui | non
- `garder:Vehicule:Marque et modèle` = oui | non
- `garder:Vehicule:Nombre de places` = oui | non
- `garder:Course:Date et heure de début` = oui | non
- `garder:Course:Date et heure de fin` = oui | non
- `garder:Course:Lieu de départ` = oui | non
- `garder:Course:Destination` = oui | non
- `garder:Course:Nombre de passagers` = oui | non
- `garder:Course:Prix` = oui | non
- `garder:Facture:Montant` = oui | non
- `garder:Facture:Date de facture` = oui | non
- `garder:Facture:Montant réglé` = oui | non
- `garder:Facture:Proforma` = oui | non
- `garder:Facture:Transmise à EBP` = oui | non

### Pourquoi chaque droit

- gerant / Client : tient le registre (supprimer : seulement si le brief le dit) — « Création de fiches clients pour les réguliers comprenant l'intégralité des informations (coordonnées, courses précédentes, reste dû ou avoir en cours) »
- gerant / Chauffeur : tient le registre (supprimer : seulement si le brief le dit) — « Établissement de planning comprenant les amplitudes chauffeurs »
- gerant / Vehicule : tient le registre (supprimer : seulement si le brief le dit) — « Codes couleurs par chauffeurs et par véhicules »
- gerant / Course : tient le registre (supprimer : seulement si le brief le dit) — « Établissement de planning comprenant les amplitudes chauffeurs »
- gerant / Facture : tient le registre (supprimer : seulement si le brief le dit) — « logiciel de gestion de planning et suivis de facture »
