# Planning autocars — ce que l'usine a compris

En bref : 1 rôle (Le gérant), 5 sortes de fiches, aucun circuit d'étapes.

## Le visiteur (sans compte)
- Ne voit rien

## Le gérant (responsable de l'app)
- Voit tout, crée et modifie : clients, chauffeurs, véhicules, courses, factures

## Les informations de chaque fiche

- **Client** : Nom (texte court) ◦ choisi par nous · Coordonnées (texte long) · Reste dû (montant, facultatif) · Avoir en cours (montant, facultatif)
  - proposé (à cocher) : ☐ Client régulier (oui / non) · ☐ Téléphone (téléphone) · ☐ Email (e-mail) · ☐ Adresse (texte long)
- **Chauffeur** : Nom (texte court) ◦ choisi par nous · Couleur (texte court)
  - proposé (à cocher) : ☐ Prénom (texte court) · ☐ Téléphone (téléphone) · ☐ Email (e-mail) · ☐ Numéro de permis / carte conducteur (texte court)
- **Véhicule** : Immatriculation (texte court) ◦ choisi par nous · Couleur (texte court)
  - proposé (à cocher) : ☐ Marque et modèle (texte court) · ☐ Nombre de places (nombre) · ☐ Date du prochain contrôle technique (date)
- **Course** : Intitulé (texte court) ◦ choisi par nous
  - relié à : client, chauffeur, véhicule
  - proposé (à cocher) : ☐ Date et heure de début (date et heure) · ☐ Date et heure de fin (date et heure) · ☐ Lieu de prise en charge (texte court) · ☐ Destination (texte court) · ☐ Nombre de passagers (nombre) · ☐ Prix (montant) · ☐ Programme / instructions pour le chauffeur (texte long)
- **Facture** : Numéro de facture (texte court) ◦ choisi par nous
  - relié à : client, course
  - proposé (à cocher) : ☐ Montant HT (montant) · ☐ Montant TTC (montant) · ☐ Montant réglé (montant) · ☐ Date d'échéance (date) · ☐ Facture proforma (oui / non) · ☐ Date de transmission à EBP (date)

## Questions

- Votre brief ne disait pas comment reconnaître certaines fiches ; nous avons choisi : client → « Nom » · chauffeur → « Nom » · véhicule → « Immatriculation » · course → « Intitulé » · facture → « Numéro de facture »

## Pas encore dans notre stock (vos mots)

- Vue planning des chauffeurs avec leurs amplitudes — « Établissement de planning comprenant les amplitudes chauffeurs »
- Calcul et affichage des temps de pause obligatoires prévus par la loi — « affichant les temps de pauses obligatoires demandés par la loi »
- Codes couleurs par chauffeur et par véhicule dans le planning — « Codes couleurs par chauffeurs et par véhicules »
- Suivi automatique de la facturation — « Suivi de facturation automatique »
- Envoi des programmes aux chauffeurs directement depuis le logiciel — « Possibilité d'envoyer directement depuis le logiciel les programmes aux chauffeurs »
- Transmission des données de facturation au logiciel EBP pour établir les factures proforma — « Transmission depuis le logiciel des données pour facturation au logiciel EBP pour établir les factures proforma »
- Calcul du reste dû ou de l'avoir en cours sur la fiche client — « reste dû ou avoir en cours »

---

## Volet concepteur

### Pour répondre (`python -m usine.miroir repondre <lecture> id=valeur …`)

- `nom:Client:nom` = oui | <nouveau nom>  (client → « Nom »)
- `nom:Chauffeur:nom` = oui | <nouveau nom>  (chauffeur → « Nom »)
- `nom:Vehicule:immatriculation` = oui | <nouveau nom>  (véhicule → « Immatriculation »)
- `nom:Course:intitule` = oui | <nouveau nom>  (course → « Intitulé »)
- `nom:Facture:numero` = oui | <nouveau nom>  (facture → « Numéro de facture »)
- `garder:Client:Client régulier` = oui | non
- `garder:Client:Téléphone` = oui | non
- `garder:Client:Email` = oui | non
- `garder:Client:Adresse` = oui | non
- `garder:Chauffeur:Prénom` = oui | non
- `garder:Chauffeur:Téléphone` = oui | non
- `garder:Chauffeur:Email` = oui | non
- `garder:Chauffeur:Numéro de permis / carte conducteur` = oui | non
- `garder:Vehicule:Marque et modèle` = oui | non
- `garder:Vehicule:Nombre de places` = oui | non
- `garder:Vehicule:Date du prochain contrôle technique` = oui | non
- `garder:Course:Date et heure de début` = oui | non
- `garder:Course:Date et heure de fin` = oui | non
- `garder:Course:Lieu de prise en charge` = oui | non
- `garder:Course:Destination` = oui | non
- `garder:Course:Nombre de passagers` = oui | non
- `garder:Course:Prix` = oui | non
- `garder:Course:Programme / instructions pour le chauffeur` = oui | non
- `garder:Facture:Montant HT` = oui | non
- `garder:Facture:Montant TTC` = oui | non
- `garder:Facture:Montant réglé` = oui | non
- `garder:Facture:Date d'échéance` = oui | non
- `garder:Facture:Facture proforma` = oui | non
- `garder:Facture:Date de transmission à EBP` = oui | non

### Pourquoi chaque droit

- gerant / Client : tient le registre (supprimer : seulement si le brief le dit) ; exception : « Création de fiches clients pour les réguliers » — « Création de fiches clients pour les réguliers comprenant l'intégralité des informations » « Création de fiches clients pour les réguliers »
- gerant / Chauffeur : tient le registre (supprimer : seulement si le brief le dit) — « envoyer directement depuis le logiciel les programmes aux chauffeurs »
- gerant / Vehicule : tient le registre (supprimer : seulement si le brief le dit) — « Codes couleurs par chauffeurs et par véhicules »
- gerant / Course : tient le registre (supprimer : seulement si le brief le dit) — « Établissement de planning comprenant les amplitudes chauffeurs »
- gerant / Facture : tient le registre (supprimer : seulement si le brief le dit) — « Suivi de facturation automatique »
