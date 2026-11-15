# Bilan postural — ce que l'usine a compris

En bref : 1 rôle (Le praticien), 9 sortes de fiches, aucun circuit d'étapes.

## Le visiteur (sans compte)
- Ne voit rien

## Le praticien (responsable de l'app)
- Voit tout, crée et modifie : Patients, Anamnèses, Examens cliniques, Points osseux, Tableaux de correspondance, Comptes rendus
- Voit tout, crée, modifie et supprime : États de points osseux (dans chaque Examen clinique), Flèches de désalignement (dans chaque Examen clinique), Recommandations (dans chaque Examen clinique)

## Les informations de chaque fiche

- **Patient** : Nom (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Prénom (texte court) · ☐ Date de naissance (date) · ☐ Téléphone (téléphone) · ☐ Email (e-mail) · ☐ Adresse (texte long)
- **Anamnèse** : Intitulé (texte court) ◦ choisi par nous
  - relié à : Patient
  - proposé (à cocher) : ☐ Motif de consultation (texte long) · ☐ Antécédents médicaux (texte long) · ☐ Traitements en cours (texte long) · ☐ Activité physique (texte long)
- **Examen clinique** : Intitulé (texte court) ◦ choisi par nous
  - relié à : Patient
  - proposé (à cocher) : ☐ Date de l'examen (date) · ☐ Observations (texte long) · ☐ Vue du dessin utilisée (texte court)
- **Point osseux** : Nom (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Emplacement sur le dessin (texte court) · ☐ Région du corps (texte court) · ☐ Ordre d'affichage (nombre)
- **État de point osseux** : Position (choix parmi : aligné, gauche, droite)
  - relié à : dans chaque Examen clinique, Point osseux
  - proposé (à cocher) : ☐ Commentaire (texte long)
- **Flèche de désalignement** : Structure bilatérale (texte court) · Direction (texte court)
  - relié à : dans chaque Examen clinique
  - proposé (à cocher) : ☐ Liste des directions possibles (choix) · ☐ Commentaire (texte long)
- **Tableau de correspondance** : Nom (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Combinaison de positions et de flèches concernée (texte long) · ☐ Recommandation associée (texte long) · ☐ Exercices associés (texte long) · ☐ Correction de semelles associée (texte long)
- **Recommandation** : Recommandations (texte long) · Exercices (texte long) · Corrections de semelles (texte long)
  - relié à : dans chaque Examen clinique, Tableau de correspondance
  - proposé (à cocher) : ☐ Priorité (nombre) · ☐ Validée par le praticien (oui / non)
- **Compte rendu** : Contenu (texte long)
  - relié à : Patient, Anamnèse, Examen clinique
  - proposé (à cocher) : ☐ Conclusion (texte long) · ☐ Date d'envoi au patient (date)

## Questions

- Votre brief ne disait pas comment reconnaître certaines fiches ; nous avons choisi : Patient → « Nom » · Anamnèse → « Intitulé » · Examen clinique → « Intitulé » · Point osseux → « Nom » · Tableau de correspondance → « Nom »

## Pas encore dans notre stock (vos mots)

- Utilisation sur iPad pour l'examen clinique, en plus du PC (on ne sait pas encore si c'est une application web adaptée à la tablette ou une application native) — « application métier paramédical web PC + iPad ... iPad pour l’examen clinique »
- Saisie graphique de l'examen sur des dessins du corps humain : points osseux à 3 états et flèches prédéfinies pour indiquer un désalignement — « l’examen clinique sur dessins humains génériques ... certaines structures bilatérales utilisent des flèches prédéfinies pour indiquer désalignement »
- Analyse automatique de la position des points et de la direction des flèches — « L’application analyse automatiquement la position des points et la direction des flèches »
- Croisement avec les tableaux de correspondance du praticien pour proposer automatiquement des recommandations, des exercices et des corrections de semelles — « fait la corrélation avec mes tableaux de correspondance pour générer automatiquement recommandations, exercices et corrections de semelles »
- Rédaction d'un compte rendu complet et hiérarchisé qui rassemble toutes les informations — « toutes les infos sont mis en commun pour éditer un compte rendu complet et hiérarchisé »

---

## Volet concepteur

### Pour répondre (`python -m usine.miroir repondre <lecture> id=valeur …`)

- `nom:Patient:nom` = oui | <nouveau nom>  (Patient → « Nom »)
- `nom:Anamnese:intitule` = oui | <nouveau nom>  (Anamnèse → « Intitulé »)
- `nom:ExamenClinique:intitule` = oui | <nouveau nom>  (Examen clinique → « Intitulé »)
- `nom:PointOsseux:nom` = oui | <nouveau nom>  (Point osseux → « Nom »)
- `nom:TableauCorrespondance:nom` = oui | <nouveau nom>  (Tableau de correspondance → « Nom »)
- `garder:Patient:Prénom` = oui | non
- `garder:Patient:Date de naissance` = oui | non
- `garder:Patient:Téléphone` = oui | non
- `garder:Patient:Email` = oui | non
- `garder:Patient:Adresse` = oui | non
- `garder:Anamnese:Motif de consultation` = oui | non
- `garder:Anamnese:Antécédents médicaux` = oui | non
- `garder:Anamnese:Traitements en cours` = oui | non
- `garder:Anamnese:Activité physique` = oui | non
- `garder:ExamenClinique:Date de l'examen` = oui | non
- `garder:ExamenClinique:Observations` = oui | non
- `garder:ExamenClinique:Vue du dessin utilisée` = oui | non
- `garder:PointOsseux:Emplacement sur le dessin` = oui | non
- `garder:PointOsseux:Région du corps` = oui | non
- `garder:PointOsseux:Ordre d'affichage` = oui | non
- `garder:EtatPointOsseux:Commentaire` = oui | non
- `garder:FlecheDesalignement:Liste des directions possibles` = oui | non
- `garder:FlecheDesalignement:Commentaire` = oui | non
- `garder:TableauCorrespondance:Combinaison de positions et de flèches concernée` = oui | non
- `garder:TableauCorrespondance:Recommandation associée` = oui | non
- `garder:TableauCorrespondance:Exercices associés` = oui | non
- `garder:TableauCorrespondance:Correction de semelles associée` = oui | non
- `garder:Recommandation:Priorité` = oui | non
- `garder:Recommandation:Validée par le praticien` = oui | non
- `garder:CompteRendu:Conclusion` = oui | non
- `garder:CompteRendu:Date d'envoi au patient` = oui | non

### Pourquoi chaque droit

- praticien / Patient : tient le registre (supprimer : seulement si le brief le dit) — « application gestion patient et clinique »
- praticien / Anamnese : tient le registre (supprimer : seulement si le brief le dit) — « PC pour l’administratif et l’anamnèse »
- praticien / ExamenClinique : tient le registre (supprimer : seulement si le brief le dit) — « iPad pour l’examen clinique sur dessins humains génériques »
- praticien / PointOsseux : préréglage catalogue : visible de tous les connectés ; gestionnaire du catalogue (supprimer : seulement si le brief le dit) — « dessins humains génériques »
- praticien / TableauCorrespondance : préréglage catalogue : visible de tous les connectés ; gestionnaire du catalogue (supprimer : seulement si le brief le dit) — « fait la corrélation avec mes tableaux de correspondance »
- praticien / CompteRendu : tient le registre (supprimer : seulement si le brief le dit) — « toutes les infos sont mis en commun pour éditer un compte rendu complet et hiérarchisé »
- praticien / EtatPointOsseux : enfant de Examen clinique : même visibilité que le parent, géré par qui gère le parent — « iPad pour l’examen clinique sur dessins humains génériques »
- praticien / FlecheDesalignement : enfant de Examen clinique : même visibilité que le parent, géré par qui gère le parent — « iPad pour l’examen clinique sur dessins humains génériques »
- praticien / Recommandation : enfant de Examen clinique : même visibilité que le parent, géré par qui gère le parent — « iPad pour l’examen clinique sur dessins humains génériques »
