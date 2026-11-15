# Réservations CrossFit — ce que l'usine a compris

En bref : 2 rôles (Le coach, L'adhérent), 4 sortes de fiches, 1 circuit d'étapes.

## ⚠ Ce que vous demandez et que je ne sais pas encore faire

- Le coach crée le compte des Adhérents : pas encore possible (les invitations arrivent avec la connexion)

**Je vous propose de construire tout le reste**, décrit ci-dessous.

## Le visiteur (sans compte)
- Ne voit rien

## Le coach (responsable de l'app)
- Voit tout et supprime : Adhérents
- Voit tout, crée et modifie : Créneaux
- Voit tout : Réservations

## L'adhérent (s'inscrit lui-même)
- Voit tout : Créneaux
- Voit seulement les siennes, crée et modifie : Inscriptions en liste d'attente
- a son Adhérent, créé automatiquement, qu'il peut modifier
- Réservations : voit seulement les siennes, en crée, les fait passer de « inscrite » à « annulée »

## Les étapes

- La réservation passe par : « inscrite » → « annulée »
  - L'adhérent fait passer de « inscrite » à « annulée »

## Les informations de chaque fiche

- **Adhérent** : Nom (texte court) · Prénom (texte court) · Type d'abonnement (choix parmi : séance, semaine, mois) · Date d'anniversaire de l'abonnement (date) · En situation régulière (a payé) (oui / non)
  - proposé (à cocher) : ☐ Téléphone (téléphone) · ☐ Montant de l'abonnement (montant)
- **Créneau** : Intitulé (texte court) ◦ choisi par nous · Nombre de places maximum (nombre)
  - proposé (à cocher) : ☐ Date et heure de début (date et heure) · ☐ Durée (minutes) (nombre) · ☐ Coach (texte court)
- **Réservation** : aucune information (seulement ses liens)
  - relié à : Créneau
  - proposé (à cocher) : ☐ Date de la séance (date)
- **Inscription en liste d'attente** : aucune information (seulement ses liens)
  - relié à : Créneau
  - proposé (à cocher) : ☐ Rang dans la liste d'attente (nombre)

## Questions

- Votre brief ne disait pas comment reconnaître certaines fiches ; nous avons choisi : Créneau → « Intitulé »
- Acceptez-vous de construire le reste, sans ce qui n'est pas encore possible ?

## Pas encore dans notre stock (vos mots)

- Vue emploi du temps (planning des créneaux) consultable en temps réel par le coach et par les adhérents — « Le client doit avoir une visualisation en temps réel de l’emploie du temps ... L’administrateur dispose d’une visualisation en temps réel sur l’emploi du temps de la salle »
- Comptage des adhérents inscrits à chaque créneau — « une visualisation globale sur le nombre d’adhérents à chaque créneaux »
- Limite de 15 places par créneau et calcul des places disponibles — « Le client choisi son ou ses créneaux selon les places disponibles ... 15 personnes par créneaux maximum »
- Liste d'attente gérée automatiquement quand un créneau est complet — « Liste d’attente pour les personnes voulant s’inscrire à une séance qui est déjà complète »
- Annulation interdite moins de 2 heures avant la séance (règle liée à l'heure) — « 2H max avant la séance pour pouvoir l’annuler »
- Limite d'un créneau par jour et par adhérent (à confirmer, le brief dit aussi « son ou ses créneaux ») — « Il choisi un créneaux par jour ( 6 créneaux par jour) »
- Indicateur de couleur vert/rouge selon que l'adhérent a payé et est en situation régulière (suivi des paiements) — « vert si le client a payé et est en situation régulière et rouge à l’inverse »
- Notification de rappel au coach 2 jours avant l'échéance de l'abonnement d'un adhérent — « Le coach reçoit une notification de l’application ... 2 jours avant la fin de sa date d’anniversaire »
- Notification au coach quand un adhérent annule une séance — « L’administrateur est notifier si le client annule une séance »
- Message de relance automatique au coach et à l'adhérent à l'échéance de l'abonnement — « L’application relance l’administrateur tout comme le client avec un message lorsque que la date d’anniversaire (date d’inscription) arrive à échéance »

---

## Volet concepteur

### Pour répondre (`python -m usine.miroir repondre <lecture> id=valeur …`)

- `nom:Creneau:intitule` = oui | <nouveau nom>  (Créneau → « Intitulé »)
- `accepter_proposition` = oui | non
- `garder:Adherent:Téléphone` = oui | non
- `garder:Adherent:Montant de l'abonnement` = oui | non
- `garder:Creneau:Date et heure de début` = oui | non
- `garder:Creneau:Durée (minutes)` = oui | non
- `garder:Creneau:Coach` = oui | non
- `garder:Reservation:Date de la séance` = oui | non
- `garder:InscriptionAttente:Rang dans la liste d'attente` = oui | non

### Pourquoi chaque droit

- coach / Adherent : exception : « Le coach veut avoir une visualisation sur chaque adhérents de sa salle de crossfit » ; exception : « il faut que le coach puisse ajouter et supprimer les clients » — « Le coach veut avoir une visualisation sur chaque adhérents de sa salle de crossfit » « il faut que le coach puisse ajouter et supprimer les clients »
- coach / Creneau : préréglage catalogue : visible de tous les connectés ; gestionnaire du catalogue (supprimer : seulement si le brief le dit) ; exception : « L’administrateur dispose d’une visualisation en temps réel sur l’emploi du temps de la salle » — « Le client doit avoir une visualisation en temps réel de l’emploie du temps » « L’administrateur dispose d’une visualisation en temps réel sur l’emploi du temps de la salle »
- coach / Reservation : exception : « Le coach veut avoir une visualisation globale sur le nombre d’adhérents à chaque créneaux (qui sera présent à quelle séance) » — « Le coach veut avoir une visualisation globale sur le nombre d’adhérents à chaque créneaux (qui sera présent à quelle séance) »
- adherent / Creneau : préréglage catalogue : visible de tous les connectés ; exception : « Le client doit avoir une visualisation en temps réel de l’emploie du temps » — « Le client doit avoir une visualisation en temps réel de l’emploie du temps » « Le client doit avoir une visualisation en temps réel de l’emploie du temps »
- adherent / InscriptionAttente : préréglage collection : le propriétaire crée et modifie les siens — « Liste d’attente pour les personnes voulant s’inscrire à une séance qui est déjà complète »
- adherent / Adherent : préréglage profil : sa propre fiche, créée automatiquement ; exception : « Le client devra crée un compte » — « Le client devra crée un compte en entrant les informations ci dessous » « Le client devra crée un compte »
- adherent / Reservation : préréglage collection + processus : l'initiateur crée et suit les siens ; le propriétaire fait évoluer l'état de ses propres éléments ; exception : « Le client choisi son ou ses créneaux selon les places disponibles » ; exception : « 2H max avant la séance pour pouvoir l’annuler » — « Le client choisi son ou ses créneaux selon les places disponibles » « 2H max avant la séance pour pouvoir l’annuler » « Le client choisi son ou ses créneaux selon les places disponibles » « 2H max avant la séance pour pouvoir l’annuler »

### Refus — blocs : acteur:invitation

- [bloc:acteur:invitation] coach / Adherent : créer le compte d'une autre personne, c'est l'inviter — arrive avec la connexion et l'équipe (N1.5) [type=value_error, input_value={'app': {'nom': 'c2-cross...ns': {}}}, 'depart': {}}, input_type=dict]
- For further information visit https://errors.pydantic.dev/2.12/v/value_error
