# Dossiers clients maintenance — ce que l'usine a compris

En bref : 1 rôle (Le gestionnaire), 11 sortes de fiches, aucun circuit d'étapes.

## Le visiteur (sans compte)
- Ne voit rien

## Le gestionnaire (responsable de l'app)
- Voit tout, crée et modifie : dossiers clients, installateurs, mainteneurs, prestataires, types de matériel, matériels installés, interventions de maintenance, formulaires de maintenance, rapports d'intervention, rapports de formation
- Voit tout, crée, modifie et supprime : pièces jointes (dans chaque dossier client)

## Les informations de chaque fiche

- **Dossier client** : Numéro du dossier (texte court) · Nom du client (texte court) · Adresse (texte long) · Divers (texte long, facultatif) · Interlocuteurs (texte long)
  - relié à : installateur, mainteneur, prestataire
  - proposé (à cocher) : ☐ Téléphone (téléphone) · ☐ Email (e-mail)
- **Installateur** : Nom (texte court) · Adresse (texte long) · Interlocuteurs (texte long)
  - proposé (à cocher) : ☐ Téléphone (téléphone)
- **Mainteneur** : Nom (texte court) · Adresse (texte long) · Interlocuteurs (texte long)
  - proposé (à cocher) : ☐ Téléphone (téléphone)
- **Prestataire** : Nom (texte court) · Adresse (texte long) · Interlocuteurs (texte long)
  - proposé (à cocher) : ☐ Téléphone (téléphone)
- **Type de matériel** : Nom du type de matériel (texte court) ◦ choisi par nous · Marque du matériel (texte court)
- **Matériel installé** : Désignation (texte court) ◦ choisi par nous
  - relié à : dossier client, type de matériel
  - proposé (à cocher) : ☐ Numéro de série (texte court) · ☐ Date d'installation (date)
- **Pièce jointe** : Intitulé (texte court) ◦ choisi par nous
  - relié à : dans chaque dossier client
  - proposé (à cocher) : ☐ Description (texte long)
- **Intervention de maintenance** : Intitulé (texte court) ◦ choisi par nous
  - relié à : dossier client, matériel installé
  - proposé (à cocher) : ☐ Date de l'intervention (date) · ☐ Intervenant (texte court) · ☐ Description (texte long)
- **Formulaire de maintenance** : Intitulé (texte court) ◦ choisi par nous
  - relié à : matériel installé, intervention de maintenance
  - proposé (à cocher) : ☐ Contenu saisi (texte long)
- **Rapport d'intervention** : Intitulé (texte court) ◦ choisi par nous
  - relié à : intervention de maintenance
  - proposé (à cocher) : ☐ Contenu du rapport (texte long)
- **Rapport de formation** : Intitulé (texte court) ◦ choisi par nous
  - relié à : dossier client
  - proposé (à cocher) : ☐ Date de la formation (date) · ☐ Contenu du rapport (texte long)

## Questions

- Votre brief ne disait pas comment reconnaître certaines fiches ; nous avons choisi : type de matériel → « Nom du type de matériel » · matériel installé → « Désignation » · pièce jointe → « Intitulé » · intervention de maintenance → « Intitulé » · formulaire de maintenance → « Intitulé » · rapport d'intervention → « Intitulé » · rapport de formation → « Intitulé »

## Pas encore dans notre stock (vos mots)

- Pièces jointes affectées aux dossiers clients — « Affectations de pièces jointes »
- Recherche multicritères sur tous les champs du dossier client et sur les champs installateur/mainteneur/prestataire — « Recherche multicritères sur tous les champs clients »
- Génération automatique d'un formulaire de maintenance préétabli à partir du matériel installé — « génération d’un formulaire préétabli en fonction du matériel »
- Édition et sauvegarde du rapport d'intervention (document produit) — « Edition et sauvegarde rapport d’intervention »
- Édition et sauvegarde du rapport de formation (document produit) — « Edition et sauvegarde rapport de formation »

---

## Volet concepteur

### Pour répondre (`python -m usine.miroir repondre <lecture> id=valeur …`)

- `nom:TypeMateriel:nom` = oui | <nouveau nom>  (type de matériel → « Nom du type de matériel »)
- `nom:MaterielInstalle:designation` = oui | <nouveau nom>  (matériel installé → « Désignation »)
- `nom:PieceJointe:intitule` = oui | <nouveau nom>  (pièce jointe → « Intitulé »)
- `nom:Intervention:intitule` = oui | <nouveau nom>  (intervention de maintenance → « Intitulé »)
- `nom:FormulaireMaintenance:intitule` = oui | <nouveau nom>  (formulaire de maintenance → « Intitulé »)
- `nom:RapportIntervention:intitule` = oui | <nouveau nom>  (rapport d'intervention → « Intitulé »)
- `nom:RapportFormation:intitule` = oui | <nouveau nom>  (rapport de formation → « Intitulé »)
- `garder:DossierClient:Téléphone` = oui | non
- `garder:DossierClient:Email` = oui | non
- `garder:Installateur:Téléphone` = oui | non
- `garder:Mainteneur:Téléphone` = oui | non
- `garder:Prestataire:Téléphone` = oui | non
- `garder:MaterielInstalle:Numéro de série` = oui | non
- `garder:MaterielInstalle:Date d'installation` = oui | non
- `garder:PieceJointe:Description` = oui | non
- `garder:Intervention:Date de l'intervention` = oui | non
- `garder:Intervention:Intervenant` = oui | non
- `garder:Intervention:Description` = oui | non
- `garder:FormulaireMaintenance:Contenu saisi` = oui | non
- `garder:RapportIntervention:Contenu du rapport` = oui | non
- `garder:RapportFormation:Date de la formation` = oui | non
- `garder:RapportFormation:Contenu du rapport` = oui | non

### Pourquoi chaque droit

- gestionnaire / DossierClient : tient le registre (supprimer : seulement si le brief le dit) — « Création dossier client »
- gestionnaire / Installateur : tient le registre (supprimer : seulement si le brief le dit) — « Installateur(*) »
- gestionnaire / Mainteneur : tient le registre (supprimer : seulement si le brief le dit) — « Mainteneur(*) »
- gestionnaire / Prestataire : tient le registre (supprimer : seulement si le brief le dit) — « Prestataire(*) »
- gestionnaire / TypeMateriel : préréglage catalogue : visible de tous les connectés ; gestionnaire du catalogue (supprimer : seulement si le brief le dit) — « Possibilité de créer et modifier les listes de matériel »
- gestionnaire / MaterielInstalle : tient le registre (supprimer : seulement si le brief le dit) — « Matériel installé »
- gestionnaire / Intervention : tient le registre (supprimer : seulement si le brief le dit) — « interventions de maintenance »
- gestionnaire / FormulaireMaintenance : tient le registre (supprimer : seulement si le brief le dit) — « formulaire préétabli en fonction du matériel »
- gestionnaire / RapportIntervention : tient le registre (supprimer : seulement si le brief le dit) — « Edition et sauvegarde rapport d’intervention »
- gestionnaire / RapportFormation : tient le registre (supprimer : seulement si le brief le dit) — « Edition et sauvegarde rapport de formation »
- gestionnaire / PieceJointe : enfant de dossier client : même visibilité que le parent, géré par qui gère le parent — « Création dossier client »
