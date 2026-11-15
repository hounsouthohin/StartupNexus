# Gestion des commandes — ce que l'usine a compris

En bref : 1 rôle (Le responsable des commandes), 3 sortes de fiches, aucun circuit d'étapes.

## Le visiteur (sans compte)
- Ne voit rien

## Le responsable des commandes (responsable de l'app)
- Voit tout, crée et modifie : commandes, plannings logistiques, livrables

## Les informations de chaque fiche

- **Commande** : Intitulé (texte court) ◦ choisi par nous
- **Planning logistique** : Intitulé (texte court) ◦ choisi par nous
  - relié à : commande
- **Livrable** : Intitulé (texte court) ◦ choisi par nous
  - relié à : commande

## Questions

- Votre brief ne disait pas comment reconnaître certaines fiches ; nous avons choisi : commande → « Intitulé » · planning logistique → « Intitulé » · livrable → « Intitulé »

## Pas encore dans notre stock (vos mots)

- Planning logistique — « un planning logistique »
- Automatisation de la gestion des livrables — « une automatisation de la gestion des livrables »

---

## Volet concepteur

### Pour répondre (`python -m usine.miroir repondre <lecture> id=valeur …`)

- `nom:Commande:intitule` = oui | <nouveau nom>  (commande → « Intitulé »)
- `nom:PlanningLogistique:intitule` = oui | <nouveau nom>  (planning logistique → « Intitulé »)
- `nom:Livrable:intitule` = oui | <nouveau nom>  (livrable → « Intitulé »)

### Pourquoi chaque droit

- responsable_des_commandes / Commande : tient le registre (supprimer : seulement si le brief le dit) — « gestion de commande »
- responsable_des_commandes / PlanningLogistique : tient le registre (supprimer : seulement si le brief le dit) — « un planning logistique »
- responsable_des_commandes / Livrable : tient le registre (supprimer : seulement si le brief le dit) — « gestion des livrables »
