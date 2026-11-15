# Gestion GymPlus — ce que l'usine a compris

En bref : 1 rôle (Le gérant), 5 sortes de fiches, aucun circuit d'étapes.

## Le visiteur (sans compte)
- Ne voit rien

## Le gérant (responsable de l'app)
- Voit tout, crée et modifie : Adhérents, Abonnements, Paiements, Présences, Activités sportives

## Les informations de chaque fiche

- **Adhérent** : Nom (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Prénom (texte court) · ☐ Email (e-mail) · ☐ Téléphone (téléphone) · ☐ Date de naissance (date)
- **Abonnement** : Intitulé (texte court) ◦ choisi par nous
  - relié à : Adhérent
  - proposé (à cocher) : ☐ Date de début (date) · ☐ Date de fin (date) · ☐ Tarif (montant) · ☐ Type d'abonnement (texte court)
- **Paiement** : Référence (texte court) ◦ choisi par nous
  - relié à : Adhérent, Abonnement
  - proposé (à cocher) : ☐ Montant (montant) · ☐ Date de paiement (date) · ☐ Moyen de paiement (texte court)
- **Présence** : Référence (texte court) ◦ choisi par nous
  - relié à : Adhérent, Activité sportive
  - proposé (à cocher) : ☐ Date et heure d'arrivée (date et heure) · ☐ Date et heure de départ (date et heure)
- **Activité sportive** : Nom (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Description (texte long) · ☐ Durée (minutes) (nombre) · ☐ Capacité maximale (nombre) · ☐ Coach (texte court)

## Questions

- Votre brief ne disait pas comment reconnaître certaines fiches ; nous avons choisi : Adhérent → « Nom » · Abonnement → « Intitulé » · Paiement → « Référence » · Présence → « Référence » · Activité sportive → « Nom »

## Pas encore dans notre stock (vos mots)

- Gestion des paiements des adhérents — « des abonnements, des paiements, des présences »

---

## Volet concepteur

### Pour répondre (`python -m usine.miroir repondre <lecture> id=valeur …`)

- `nom:Adherent:nom` = oui | <nouveau nom>  (Adhérent → « Nom »)
- `nom:Abonnement:intitule` = oui | <nouveau nom>  (Abonnement → « Intitulé »)
- `nom:Paiement:reference` = oui | <nouveau nom>  (Paiement → « Référence »)
- `nom:Presence:reference` = oui | <nouveau nom>  (Présence → « Référence »)
- `nom:Activite:nom` = oui | <nouveau nom>  (Activité sportive → « Nom »)
- `garder:Adherent:Prénom` = oui | non
- `garder:Adherent:Email` = oui | non
- `garder:Adherent:Téléphone` = oui | non
- `garder:Adherent:Date de naissance` = oui | non
- `garder:Abonnement:Date de début` = oui | non
- `garder:Abonnement:Date de fin` = oui | non
- `garder:Abonnement:Tarif` = oui | non
- `garder:Abonnement:Type d'abonnement` = oui | non
- `garder:Paiement:Montant` = oui | non
- `garder:Paiement:Date de paiement` = oui | non
- `garder:Paiement:Moyen de paiement` = oui | non
- `garder:Presence:Date et heure d'arrivée` = oui | non
- `garder:Presence:Date et heure de départ` = oui | non
- `garder:Activite:Description` = oui | non
- `garder:Activite:Durée (minutes)` = oui | non
- `garder:Activite:Capacité maximale` = oui | non
- `garder:Activite:Coach` = oui | non

### Pourquoi chaque droit

- gerant / Adherent : tient le registre (supprimer : seulement si le brief le dit) — « la gestion des adhérents »
- gerant / Abonnement : tient le registre (supprimer : seulement si le brief le dit) — « des adhérents, des abonnements »
- gerant / Paiement : tient le registre (supprimer : seulement si le brief le dit) — « des abonnements, des paiements »
- gerant / Presence : tient le registre (supprimer : seulement si le brief le dit) — « des présences et des activités sportives »
- gerant / Activite : préréglage catalogue : visible de tous les connectés ; gestionnaire du catalogue (supprimer : seulement si le brief le dit) — « des activités sportives »
