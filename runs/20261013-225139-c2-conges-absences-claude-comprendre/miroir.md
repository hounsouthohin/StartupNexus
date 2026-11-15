# Gestion des congés — ce que l'usine a compris

En bref : 1 rôle (Le gestionnaire du personnel), 3 sortes de fiches, aucun circuit d'étapes.

## Le visiteur (sans compte)
- Ne voit rien

## Le gestionnaire du personnel (responsable de l'app)
- Voit tout, crée et modifie : agents, types de congé, congés

## Les informations de chaque fiche

- **Agent** : Nom (texte court) ◦ choisi par nous · Jours ouvrables de congé (nombre)
  - proposé (à cocher) : ☐ Prénom (texte court) · ☐ Matricule (texte court) · ☐ Service (texte court) · ☐ Email (e-mail) · ☐ Jours de congé restants (nombre)
- **Type de congé** : Nom (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Décompté des 30 jours ouvrables (oui / non) · ☐ Nombre de jours maximum (nombre)
- **Congé** : Intitulé (texte court) ◦ choisi par nous
  - relié à : agent, type de congé
  - proposé (à cocher) : ☐ Date de début (date) · ☐ Date de fin (date) · ☐ Nombre de jours ouvrables (nombre) · ☐ Motif (texte long)

## Questions

- Votre brief ne disait pas comment reconnaître certaines fiches ; nous avons choisi : agent → « Nom » · type de congé → « Nom » · congé → « Intitulé »

## Pas encore dans notre stock (vos mots)

- Tableau de bord pour voir d'un coup d'œil qui est en congé — « un tableau de bord ou je peux voir qui est en congé »
- Calcul du solde de 30 jours ouvrables de congé par agent (décompte des jours ouvrables pris et restants) — « la gestion de 30 jours ouvrable de congé pour chaque agent »

---

## Volet concepteur

### Pour répondre (`python -m usine.miroir repondre <lecture> id=valeur …`)

- `nom:Agent:nom` = oui | <nouveau nom>  (agent → « Nom »)
- `nom:TypeConge:nom` = oui | <nouveau nom>  (type de congé → « Nom »)
- `nom:Conge:intitule` = oui | <nouveau nom>  (congé → « Intitulé »)
- `garder:Agent:Prénom` = oui | non
- `garder:Agent:Matricule` = oui | non
- `garder:Agent:Service` = oui | non
- `garder:Agent:Email` = oui | non
- `garder:Agent:Jours de congé restants` = oui | non
- `garder:TypeConge:Décompté des 30 jours ouvrables` = oui | non
- `garder:TypeConge:Nombre de jours maximum` = oui | non
- `garder:Conge:Date de début` = oui | non
- `garder:Conge:Date de fin` = oui | non
- `garder:Conge:Nombre de jours ouvrables` = oui | non
- `garder:Conge:Motif` = oui | non

### Pourquoi chaque droit

- gestionnaire / Agent : tient le registre (supprimer : seulement si le brief le dit) — « 30 jours ouvrable de congé pour chaque agent »
- gestionnaire / TypeConge : préréglage catalogue : visible de tous les connectés ; gestionnaire du catalogue (supprimer : seulement si le brief le dit) — « un congé avaloire (circonstanciel) ou annuel »
- gestionnaire / Conge : tient le registre (supprimer : seulement si le brief le dit) ; exception : « je peux voir qui est en congé » — « savoir qui a pris un congé avaloire (circonstanciel) ou annuel » « je peux voir qui est en congé »
