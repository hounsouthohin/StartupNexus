# Gestion de l'école — ce que l'usine a compris

En bref : 1 rôle (Le gestionnaire de l'école), 6 sortes de fiches, aucun circuit d'étapes.

## Le visiteur (sans compte)
- Ne voit rien

## Le gestionnaire de l'école (responsable de l'app)
- Voit tout, crée et modifie : élèves, parents, inscriptions, paiements mensuels, notes de classe, documents administratifs ou financiers

## Les informations de chaque fiche

- **Élève** : Nom (texte court) ◦ choisi par nous
  - relié à : parent
  - proposé (à cocher) : ☐ Prénom (texte court) · ☐ Date de naissance (date) · ☐ Classe (texte court)
- **Parent** : Nom (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Prénom (texte court) · ☐ Téléphone (téléphone) · ☐ Email (e-mail) · ☐ Adresse (texte long)
- **Inscription** : Intitulé (texte court) ◦ choisi par nous
  - relié à : élève
  - proposé (à cocher) : ☐ Année scolaire (texte court) · ☐ Classe (texte court) · ☐ Frais d'inscription (montant)
- **Paiement mensuel** : Référence (texte court) ◦ choisi par nous
  - relié à : élève
  - proposé (à cocher) : ☐ Montant (montant) · ☐ Mois concerné (texte court) · ☐ Date de paiement (date) · ☐ Mode de paiement (texte court)
- **Note de classe** : Intitulé (texte court) ◦ choisi par nous
  - relié à : élève
  - proposé (à cocher) : ☐ Valeur de la note (nombre) · ☐ Matière (texte court) · ☐ Date de l'évaluation (date) · ☐ Coefficient (nombre) · ☐ Période (trimestre) (texte court)
- **Document administratif ou financier** : Type de document (choix parmi : Financier, Administratif)
  - relié à : élève, parent
  - proposé (à cocher) : ☐ Titre (texte court) · ☐ Fichier ou lien (lien web) · ☐ Date du document (date)

## Questions

- Votre brief ne disait pas comment reconnaître certaines fiches ; nous avons choisi : élève → « Nom » · parent → « Nom » · inscription → « Intitulé » · paiement mensuel → « Référence » · note de classe → « Intitulé »

## Pas encore dans notre stock (vos mots)

- Gestion des paiements mensuels (scolarité) — « les payements mensuels »
- Documents financiers ou administratifs sur l'élève ou son parent — « tout autres documents financiers ou administratifs concernant l'élève ou son parent »

---

## Volet concepteur

### Pour répondre (`python -m usine.miroir repondre <lecture> id=valeur …`)

- `nom:Eleve:nom` = oui | <nouveau nom>  (élève → « Nom »)
- `nom:Parent:nom` = oui | <nouveau nom>  (parent → « Nom »)
- `nom:Inscription:intitule` = oui | <nouveau nom>  (inscription → « Intitulé »)
- `nom:Paiement:reference` = oui | <nouveau nom>  (paiement mensuel → « Référence »)
- `nom:Note:intitule` = oui | <nouveau nom>  (note de classe → « Intitulé »)
- `garder:Eleve:Prénom` = oui | non
- `garder:Eleve:Date de naissance` = oui | non
- `garder:Eleve:Classe` = oui | non
- `garder:Parent:Prénom` = oui | non
- `garder:Parent:Téléphone` = oui | non
- `garder:Parent:Email` = oui | non
- `garder:Parent:Adresse` = oui | non
- `garder:Inscription:Année scolaire` = oui | non
- `garder:Inscription:Classe` = oui | non
- `garder:Inscription:Frais d'inscription` = oui | non
- `garder:Paiement:Montant` = oui | non
- `garder:Paiement:Mois concerné` = oui | non
- `garder:Paiement:Date de paiement` = oui | non
- `garder:Paiement:Mode de paiement` = oui | non
- `garder:Note:Valeur de la note` = oui | non
- `garder:Note:Matière` = oui | non
- `garder:Note:Date de l'évaluation` = oui | non
- `garder:Note:Coefficient` = oui | non
- `garder:Note:Période (trimestre)` = oui | non
- `garder:Document:Titre` = oui | non
- `garder:Document:Fichier ou lien` = oui | non
- `garder:Document:Date du document` = oui | non

### Pourquoi chaque droit

- gestionnaire / Eleve : tient le registre (supprimer : seulement si le brief le dit) — « concernant l'élève ou son parent »
- gestionnaire / Parent : tient le registre (supprimer : seulement si le brief le dit) — « l'élève ou son parent »
- gestionnaire / Inscription : tient le registre (supprimer : seulement si le brief le dit) — « tant les inscriptions »
- gestionnaire / Paiement : tient le registre (supprimer : seulement si le brief le dit) — « les payements mensuels »
- gestionnaire / Note : tient le registre (supprimer : seulement si le brief le dit) — « le notes de classe »
- gestionnaire / Document : tient le registre (supprimer : seulement si le brief le dit) — « tout autres documents financiers ou administratifs concernant l'élève ou son parent »
