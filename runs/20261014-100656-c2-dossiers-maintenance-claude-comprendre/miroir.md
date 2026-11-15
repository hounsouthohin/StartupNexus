# Suivi de maintenance — ce que l'usine a compris

En bref : 1 rôle (Le gestionnaire), 12 sortes de fiches, aucun circuit d'étapes.

## Le visiteur (sans compte)
- Ne voit rien

## Le gestionnaire (responsable de l'app)
- Voit tout, crée et modifie : dossiers clients, installateurs, mainteneurs, prestataires, marques de matériel, types de matériel, interventions de maintenance, formulaires de maintenance, rapports d’intervention, rapports de formation
- Voit tout, crée, modifie et supprime : matériels installés (dans chaque dossier client), pièces jointes (dans chaque dossier client)

## Les informations de chaque fiche

- **Dossier client** : Numéro (texte court) · Nom du client (texte court) · Adresse (texte long) · Divers (texte long, facultatif) · Interlocuteurs (texte long)
  - relié à : installateur, mainteneur, prestataire
  - proposé (à cocher) : ☐ Téléphone (téléphone) · ☐ Email (e-mail)
- **Installateur** : Nom (texte court) · Adresse (texte long) · Interlocuteurs (texte long)
  - proposé (à cocher) : ☐ Téléphone (téléphone) · ☐ Email (e-mail)
- **Mainteneur** : Nom (texte court) · Adresse (texte long) · Interlocuteurs (texte long)
  - proposé (à cocher) : ☐ Téléphone (téléphone) · ☐ Email (e-mail)
- **Prestataire** : Nom (texte court) · Adresse (texte long) · Interlocuteurs (texte long)
  - proposé (à cocher) : ☐ Nature de la prestation (texte court) · ☐ Téléphone (téléphone) · ☐ Email (e-mail)
- **Marque de matériel** : Nom de la marque (texte court) ◦ choisi par nous
- **Type de matériel** : Nom du type de matériel (texte court) ◦ choisi par nous
  - relié à : marque de matériel
  - proposé (à cocher) : ☐ Rubriques du formulaire préétabli (texte long)
- **Matériel installé** : Désignation (texte court) ◦ choisi par nous
  - relié à : dans chaque dossier client, marque de matériel, type de matériel
  - proposé (à cocher) : ☐ Numéro de série (texte court) · ☐ Date d'installation (date) · ☐ Emplacement (texte court)
- **Pièce jointe** : Intitulé (texte court) ◦ choisi par nous
  - relié à : dans chaque dossier client
  - proposé (à cocher) : ☐ Fichier ou lien vers le document (lien web) · ☐ Description (texte long)
- **Intervention de maintenance** : Intitulé (texte court) ◦ choisi par nous
  - relié à : dossier client, matériel installé
  - proposé (à cocher) : ☐ Date de l'intervention (date) · ☐ Technicien (texte court) · ☐ Travaux réalisés (texte long)
- **Formulaire de maintenance** : Intitulé (texte court) ◦ choisi par nous
  - relié à : matériel installé, intervention de maintenance
  - proposé (à cocher) : ☐ Contenu du formulaire (relevés et contrôles) (texte long) · ☐ Observations (texte long)
- **Rapport d’intervention** : Intitulé (texte court) ◦ choisi par nous
  - relié à : intervention de maintenance
  - proposé (à cocher) : ☐ Contenu du rapport (texte long) · ☐ Validé par le client (oui / non)
- **Rapport de formation** : Intitulé (texte court) ◦ choisi par nous
  - relié à : dossier client
  - proposé (à cocher) : ☐ Date de la formation (date) · ☐ Personnes formées (texte long) · ☐ Formateur (texte court) · ☐ Contenu de la formation (texte long)

## Questions

- Votre brief ne disait pas comment reconnaître certaines fiches ; nous avons choisi : marque de matériel → « Nom de la marque » · type de matériel → « Nom du type de matériel » · matériel installé → « Désignation » · pièce jointe → « Intitulé » · intervention de maintenance → « Intitulé » · formulaire de maintenance → « Intitulé » · rapport d’intervention → « Intitulé » · rapport de formation → « Intitulé »

## Pas encore dans notre stock (vos mots)

- Numérotation des dossiers clients (attribution d'un numéro, peut-être automatique, à confirmer) — « Attribution d’un numéro »
- Pièces jointes rattachées au dossier client — « Affectations de pièces jointes »
- Recherche multicritères sur tous les champs des dossiers clients et sur les installateurs, mainteneurs et prestataires — « Recherche multicritères sur tous les champs clients »
- Formulaire de maintenance préétabli, généré automatiquement selon le matériel installé et réutilisé d'une intervention à l'autre — « génération d’un formulaire préétabli en fonction du matériel ... Réutilisation du formulaire »
- Édition du formulaire de maintenance (impression ou PDF, à confirmer) — « Saisie, sauvegarde et édition du formulaire »
- Édition des rapports d'intervention et des rapports de formation (impression ou PDF, à confirmer) — « Edition et sauvegarde rapport d’intervention ... Edition et sauvegarde rapport de formation »

---

## Volet concepteur

### Pour répondre (`python -m usine.miroir repondre <lecture> id=valeur …`)

- `nom:MarqueMateriel:nom` = oui | <nouveau nom>  (marque de matériel → « Nom de la marque »)
- `nom:TypeMateriel:nom` = oui | <nouveau nom>  (type de matériel → « Nom du type de matériel »)
- `nom:MaterielInstalle:designation` = oui | <nouveau nom>  (matériel installé → « Désignation »)
- `nom:PieceJointe:intitule` = oui | <nouveau nom>  (pièce jointe → « Intitulé »)
- `nom:InterventionMaintenance:intitule` = oui | <nouveau nom>  (intervention de maintenance → « Intitulé »)
- `nom:FormulaireMaintenance:intitule` = oui | <nouveau nom>  (formulaire de maintenance → « Intitulé »)
- `nom:RapportIntervention:intitule` = oui | <nouveau nom>  (rapport d’intervention → « Intitulé »)
- `nom:RapportFormation:intitule` = oui | <nouveau nom>  (rapport de formation → « Intitulé »)
- `garder:DossierClient:Téléphone` = oui | non
- `garder:DossierClient:Email` = oui | non
- `garder:Installateur:Téléphone` = oui | non
- `garder:Installateur:Email` = oui | non
- `garder:Mainteneur:Téléphone` = oui | non
- `garder:Mainteneur:Email` = oui | non
- `garder:Prestataire:Nature de la prestation` = oui | non
- `garder:Prestataire:Téléphone` = oui | non
- `garder:Prestataire:Email` = oui | non
- `garder:TypeMateriel:Rubriques du formulaire préétabli` = oui | non
- `garder:MaterielInstalle:Numéro de série` = oui | non
- `garder:MaterielInstalle:Date d'installation` = oui | non
- `garder:MaterielInstalle:Emplacement` = oui | non
- `garder:PieceJointe:Fichier ou lien vers le document` = oui | non
- `garder:PieceJointe:Description` = oui | non
- `garder:InterventionMaintenance:Date de l'intervention` = oui | non
- `garder:InterventionMaintenance:Technicien` = oui | non
- `garder:InterventionMaintenance:Travaux réalisés` = oui | non
- `garder:FormulaireMaintenance:Contenu du formulaire (relevés et contrôles)` = oui | non
- `garder:FormulaireMaintenance:Observations` = oui | non
- `garder:RapportIntervention:Contenu du rapport` = oui | non
- `garder:RapportIntervention:Validé par le client` = oui | non
- `garder:RapportFormation:Date de la formation` = oui | non
- `garder:RapportFormation:Personnes formées` = oui | non
- `garder:RapportFormation:Formateur` = oui | non
- `garder:RapportFormation:Contenu de la formation` = oui | non

### Pourquoi chaque droit

- gestionnaire / DossierClient : tient le registre (supprimer : seulement si le brief le dit) — « Possibilité d’affecter plusieurs Installateurs/Mainteneurs/Prestataires à un client »
- gestionnaire / Installateur : tient le registre (supprimer : seulement si le brief le dit) — « (*) possibilité de créer une liste et de choisir dans la liste »
- gestionnaire / Mainteneur : tient le registre (supprimer : seulement si le brief le dit) — « (*) possibilité de créer une liste et de choisir dans la liste »
- gestionnaire / Prestataire : tient le registre (supprimer : seulement si le brief le dit) — « (*) possibilité de créer une liste et de choisir dans la liste »
- gestionnaire / MarqueMateriel : préréglage catalogue : visible de tous les connectés ; gestionnaire du catalogue (supprimer : seulement si le brief le dit) — « Possibilité de créer et modifier les listes de matériel »
- gestionnaire / TypeMateriel : préréglage catalogue : visible de tous les connectés ; gestionnaire du catalogue (supprimer : seulement si le brief le dit) — « Possibilité de créer et modifier les listes de matériel »
- gestionnaire / InterventionMaintenance : tient le registre (supprimer : seulement si le brief le dit) — « gérer les dossiers clients et les interventions de maintenance »
- gestionnaire / FormulaireMaintenance : tient le registre (supprimer : seulement si le brief le dit) — « Réutilisation du formulaire et sauvegarde en fonction des interventions de maintenance »
- gestionnaire / RapportIntervention : tient le registre (supprimer : seulement si le brief le dit) — « Edition et sauvegarde rapport d’intervention »
- gestionnaire / RapportFormation : tient le registre (supprimer : seulement si le brief le dit) — « Edition et sauvegarde rapport de formation »
- gestionnaire / MaterielInstalle : enfant de dossier client : même visibilité que le parent, géré par qui gère le parent — « Possibilité d’affecter plusieurs Installateurs/Mainteneurs/Prestataires à un client »
- gestionnaire / PieceJointe : enfant de dossier client : même visibilité que le parent, géré par qui gère le parent — « Possibilité d’affecter plusieurs Installateurs/Mainteneurs/Prestataires à un client »
