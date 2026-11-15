# Gestion des commandes — ce que l'usine a compris

En bref : 1 rôle (Le gestionnaire), 3 sortes de fiches, aucun circuit d'étapes.

## ⚠ Ce que vous demandez et que je ne sais pas encore faire

- (voir le volet concepteur)

**Rien ne peut encore se construire sans en reparler ensemble.**

## Le visiteur (sans compte)
- Ne voit rien

## Le gestionnaire (responsable de l'app)
- Voit tout, crée et modifie : commandes, interventions planifiées
- Voit tout, crée, modifie et supprime : livrables (dans chaque commande)

## Les informations de chaque fiche

- **Commande** : Référence (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Client (texte court) · ☐ Type de mesure (texte court) · ☐ Lieu (site de mesure) (texte court) · ☐ Date souhaitée de réalisation (date) · ☐ Montant (montant)
- **Intervention planifiée** : Intitulé (texte court) ◦ choisi par nous
  - relié à : commande
  - proposé (à cocher) : ☐ Date et heure prévues (date et heure) · ☐ Lieu d'intervention (texte court) · ☐ Intervenants (texte court) · ☐ Matériel nécessaire (texte long)
- **Livrable** : Intitulé (texte court) ◦ choisi par nous
  - relié à : dans chaque commande, commande
  - proposé (à cocher) : ☐ Date d'échéance (date) · ☐ Type de livrable (texte court) · ☐ Lien vers le fichier (lien web) · ☐ Date de remise (date)

## Questions

- Votre brief ne disait pas comment reconnaître certaines fiches ; nous avons choisi : commande → « Référence » · intervention planifiée → « Intitulé » · livrable → « Intitulé »

## Pas encore dans notre stock (vos mots)

- Planning logistique des commandes et des interventions sur le terrain — « un planning logistique »
- Automatisation de la gestion des livrables — « une automatisation de la gestion des livrables »

---

## Volet concepteur

### Pour répondre (`python -m usine.miroir repondre <lecture> id=valeur …`)

- `nom:Commande:reference` = oui | <nouveau nom>  (commande → « Référence »)
- `nom:Intervention:intitule` = oui | <nouveau nom>  (intervention planifiée → « Intitulé »)
- `nom:Livrable:intitule` = oui | <nouveau nom>  (livrable → « Intitulé »)
- `garder:Commande:Client` = oui | non
- `garder:Commande:Type de mesure` = oui | non
- `garder:Commande:Lieu (site de mesure)` = oui | non
- `garder:Commande:Date souhaitée de réalisation` = oui | non
- `garder:Commande:Montant` = oui | non
- `garder:Intervention:Date et heure prévues` = oui | non
- `garder:Intervention:Lieu d'intervention` = oui | non
- `garder:Intervention:Intervenants` = oui | non
- `garder:Intervention:Matériel nécessaire` = oui | non
- `garder:Livrable:Date d'échéance` = oui | non
- `garder:Livrable:Type de livrable` = oui | non
- `garder:Livrable:Lien vers le fichier` = oui | non
- `garder:Livrable:Date de remise` = oui | non

### Pourquoi chaque droit

- gestionnaire / Commande : tient le registre (supprimer : seulement si le brief le dit) — « faciliterait la gestion des commandes (mesure scientifiques sur terrain) »
- gestionnaire / Intervention : tient le registre (supprimer : seulement si le brief le dit) — « qui inclurait un planning logistique »
- gestionnaire / Livrable : enfant de commande : même visibilité que le parent, géré par qui gère le parent — « faciliterait la gestion des commandes (mesure scientifiques sur terrain) »

### Refus — blocs : erreur enfant-designe-parent

- [erreur:enfant-designe-parent] Livrable : désigne aussi son parent Commande (le lien vers le parent existe déjà) [type=value_error, input_value={'app': {'nom': 'mesures-...ns': {}}}, 'depart': {}}, input_type=dict]
- For further information visit https://errors.pydantic.dev/2.12/v/value_error
