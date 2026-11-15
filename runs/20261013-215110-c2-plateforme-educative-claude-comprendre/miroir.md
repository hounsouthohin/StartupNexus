# Gestion de scolarité — ce que l'usine a compris

En bref : 5 rôles (L'administrateur, Le membre de la direction, Le secrétaire académique, L'enseignant, L'étudiant), 7 sortes de fiches, 1 circuit d'étapes.

## ⚠ Ce que vous demandez et que je ne sais pas encore faire

- ⚠ L'enseignant ne verra pas les Notes qui le concernent (voir celles qui le désignent : pas encore possible)
- les attestations que le secrétaire académique saisit pour l'étudiant : pas encore possible — retirées
- les bulletins que le secrétaire académique saisit pour l'étudiant : pas encore possible — retirées
- les diplômes que le secrétaire académique saisit pour l'étudiant : pas encore possible — retirées
- les notes que l'enseignant saisit pour l'étudiant : pas encore possible — retirées

**Je vous propose de construire tout le reste**, décrit ci-dessous.

## Le visiteur (sans compte)
- Ne voit rien

## L'administrateur (responsable de l'app)
- Voit tout, crée et modifie : Filières, Matières
- Voit tout : Évaluations

## Le membre de la direction (invité par administrateur)
- Voit tout : Filières, Matières

## Le secrétaire académique (invité par administrateur)
- Voit tout : Filières, Matières, Pièces jointes (dans chaque Inscription)
- Inscriptions : voit tout, les fait passer de « soumise » à « validée »

## L'enseignant (invité par administrateur)
- Voit tout : Filières, Matières
- Voit tout, crée et modifie : Évaluations
- a son Enseignant, créé automatiquement, qu'il peut modifier

## L'étudiant (s'inscrit lui-même)
- Voit tout : Filières, Matières
- Voit seulement les siennes et crée : Inscriptions
- Voit seulement les siennes : Pièces jointes (dans chaque Inscription)
- a son Étudiant, créé automatiquement, qu'il peut modifier

## Les étapes

- L'inscription passe par : « soumise » → « validée »
  - Le secrétaire académique fait passer de « soumise » à « validée »

## Les informations de chaque fiche

- **Étudiant** : Nom (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Prénom (texte court) · ☐ Numéro étudiant (texte court) · ☐ Date de naissance (date) · ☐ Email (e-mail) · ☐ Téléphone (téléphone)
- **Enseignant** : Nom (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Prénom (texte court) · ☐ Email (e-mail) · ☐ Téléphone (téléphone) · ☐ Grade ou statut (texte court)
- **Filière** : Nom (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Code (texte court) · ☐ Niveau (texte court) · ☐ Durée (années) (nombre) · ☐ Description (texte long)
- **Matière** : Nom (texte court) ◦ choisi par nous
  - relié à : Filière
  - proposé (à cocher) : ☐ Code (texte court) · ☐ Coefficient (nombre) · ☐ Crédits ECTS (nombre) · ☐ Semestre (texte court) · ☐ Volume horaire (nombre)
- **Inscription** : Intitulé (texte court) ◦ choisi par nous
  - relié à : Filière
  - proposé (à cocher) : ☐ Année universitaire (texte court) · ☐ Niveau d'études (texte court) · ☐ Établissement d'origine (texte court) · ☐ Commentaire de validation (texte long)
- **Pièce jointe** : Type de document (texte court)
  - relié à : dans chaque Inscription
  - proposé (à cocher) : ☐ Fichier (lien) (lien web) · ☐ Texte extrait par OCR (texte long)
- **Évaluation** : Intitulé (texte court) ◦ choisi par nous
  - relié à : Matière
  - proposé (à cocher) : ☐ Date (date) · ☐ Type d'évaluation (texte court) · ☐ Coefficient (nombre) · ☐ Note maximale (nombre)

## Questions

- L'enseignant verra toutes les Évaluations, pas seulement celles qui le concernent — d'accord ? → **oui, nécessairement** : entité Evaluation (registre) : il faut au moins un acteur qui le tient (« manager »)
- Votre brief ne disait pas comment reconnaître certaines fiches ; nous avons choisi : Étudiant → « Nom » · Enseignant → « Nom » · Filière → « Nom » · Matière → « Nom » · Inscription → « Intitulé » · Évaluation → « Intitulé »
- Acceptez-vous de construire le reste, sans ce qui n'est pas encore possible ?

## Pas encore dans notre stock (vos mots)

- Une même solution proposée à plusieurs établissements, dont les données doivent être séparées — « Il s’agit d’une solution que je souhaiterais proposer à plusieurs établissements. »
- Automatisation des processus d'inscription, de gestion des notes et de délivrance des attestations et diplômes — « Automatiser les processus d’inscription, de gestion des notes, et de délivrance des attestations et diplômes. »
- Traçabilité des données académiques (historique des actions, journal) — « Garantir la traçabilité, la transparence et la sécurité des données académiques. »
- Dépôt de pièces jointes au dossier d'inscription (carte d'identité...) — « Upload de documents (carte d’identité…) »
- Analyse des pièces jointes par OCR et IA pour pré-remplir automatiquement les champs du formulaire — « avec analyse des pièces jointes par OCR ... OCR + IA pour pré-remplir automatiquement les champs. »
- Formulaire d'inscription dynamique — « Formulaire dynamique de saisie. »
- Calcul automatique des notes (moyennes, résultats) — « Enregistrement et calcul automatisé des notes. »
- Génération de bulletins semestriels et annuels — « Génération de bulletins semestriels/annuels. »
- Génération en PDF des attestations et diplômes, téléchargeables par les étudiants — « Génération d’attestations et diplômes avec QR code. ... Génération PDF avec »
- QR code intégré aux documents pour en vérifier l'authenticité — « Intégration d’un QR code pour authentification »
- Signature électronique et système de validation sécurisé — « Intégration d’une signature électronique et d’un système de validation sécurisé. »
- Tableaux de bord pour chaque rôle et tableau de bord synthétique (étudiants inscrits, résultats, documents délivrés) — « Tableau de bord pour les différents rôles (admin, direction, enseignants, étudiants). ... Tableau de bord synthétique (étudiants inscrits, résultats, documents délivrés). »
- Export des données par la direction — « supervision des opérations et export des données. »
- Notifications aux étudiants (validation du dossier) et rappels d'échéances — « Notifications (validation, échéances). »
- Archivage sécurisé des données — « Archivage sécurisé. »
- Recherche multicritères (étudiants, filières, années) — « Recherche multicritères (étudiants, filières, années). »

---

## Volet concepteur

### Pour répondre (`python -m usine.miroir repondre <lecture> id=valeur …`)

- `registre_entier:enseignant:Evaluation` = oui
- `nom:Etudiant:nom` = oui | <nouveau nom>  (Étudiant → « Nom »)
- `nom:Enseignant:nom` = oui | <nouveau nom>  (Enseignant → « Nom »)
- `nom:Filiere:nom` = oui | <nouveau nom>  (Filière → « Nom »)
- `nom:Matiere:nom` = oui | <nouveau nom>  (Matière → « Nom »)
- `nom:Inscription:intitule` = oui | <nouveau nom>  (Inscription → « Intitulé »)
- `nom:Evaluation:intitule` = oui | <nouveau nom>  (Évaluation → « Intitulé »)
- `accepter_proposition` = oui | non
- `garder:Etudiant:Prénom` = oui | non
- `garder:Etudiant:Numéro étudiant` = oui | non
- `garder:Etudiant:Date de naissance` = oui | non
- `garder:Etudiant:Email` = oui | non
- `garder:Etudiant:Téléphone` = oui | non
- `garder:Enseignant:Prénom` = oui | non
- `garder:Enseignant:Email` = oui | non
- `garder:Enseignant:Téléphone` = oui | non
- `garder:Enseignant:Grade ou statut` = oui | non
- `garder:Filiere:Code` = oui | non
- `garder:Filiere:Niveau` = oui | non
- `garder:Filiere:Durée (années)` = oui | non
- `garder:Filiere:Description` = oui | non
- `garder:Matiere:Code` = oui | non
- `garder:Matiere:Coefficient` = oui | non
- `garder:Matiere:Crédits ECTS` = oui | non
- `garder:Matiere:Semestre` = oui | non
- `garder:Matiere:Volume horaire` = oui | non
- `garder:Inscription:Année universitaire` = oui | non
- `garder:Inscription:Niveau d'études` = oui | non
- `garder:Inscription:Établissement d'origine` = oui | non
- `garder:Inscription:Commentaire de validation` = oui | non
- `garder:PieceJointe:Fichier (lien)` = oui | non
- `garder:PieceJointe:Texte extrait par OCR` = oui | non
- `garder:Evaluation:Date` = oui | non
- `garder:Evaluation:Type d'évaluation` = oui | non
- `garder:Evaluation:Coefficient` = oui | non
- `garder:Evaluation:Note maximale` = oui | non

### Pourquoi chaque droit

- administrateur / Filiere : préréglage catalogue : visible de tous les connectés ; gestionnaire du catalogue (supprimer : seulement si le brief le dit) — « Ajout/modification des filières, matières, enseignants »
- administrateur / Matiere : préréglage catalogue : visible de tous les connectés ; gestionnaire du catalogue (supprimer : seulement si le brief le dit) — « Ajout/modification des filières, matières, enseignants »
- administrateur / Evaluation : responsable de l'app : voit les registres de l'équipe (lecture) — « Gestion des cours, évaluations, notes et bulletins »
- direction / Filiere : préréglage catalogue : visible de tous les connectés — « Ajout/modification des filières, matières, enseignants »
- direction / Matiere : préréglage catalogue : visible de tous les connectés — « Ajout/modification des filières, matières, enseignants »
- secretaire / Filiere : préréglage catalogue : visible de tous les connectés — « Ajout/modification des filières, matières, enseignants »
- secretaire / Matiere : préréglage catalogue : visible de tous les connectés — « Ajout/modification des filières, matières, enseignants »
- secretaire / PieceJointe : enfant de Inscription : même visibilité que le parent — « Secrétariat académique : validation des dossiers »
- secretaire / Inscription : décideur du processus : voit tout et fait évoluer l'état ; exception : « Secrétariat académique : validation des dossiers » — « Secrétariat académique : validation des dossiers » « Secrétariat académique : validation des dossiers »
- enseignant / Filiere : préréglage catalogue : visible de tous les connectés — « Ajout/modification des filières, matières, enseignants »
- enseignant / Matiere : préréglage catalogue : visible de tous les connectés — « Ajout/modification des filières, matières, enseignants »
- enseignant / Evaluation : tient le registre (supprimer : seulement si le brief le dit) — « Gestion des cours, évaluations, notes et bulletins »
- enseignant / Enseignant : préréglage profil : sa propre fiche, créée automatiquement — « Ajout/modification des filières, matières, enseignants »
- etudiant / Filiere : préréglage catalogue : visible de tous les connectés — « Ajout/modification des filières, matières, enseignants »
- etudiant / Matiere : préréglage catalogue : visible de tous les connectés — « Ajout/modification des filières, matières, enseignants »
- etudiant / Inscription : préréglage collection + processus : l'initiateur crée et suit les siens ; exception : « Étudiants : inscription » — « Gestion des inscriptions en ligne » « Étudiants : inscription »
- etudiant / PieceJointe : enfant de Inscription : même visibilité que le parent — « Gestion des inscriptions en ligne » « Étudiants : inscription »
- etudiant / Etudiant : préréglage profil : sa propre fiche, créée automatiquement — « Portail étudiant et interface d’administration »

### Refus — blocs : lien:pour-autrui, portee:designe

- [bloc:lien:pour-autrui] Note : fiches saisies pour quelqu'un d'autre — arrivent avec l'écran « choisir la personne » (N1.x)
- [bloc:lien:pour-autrui] Bulletin : fiches saisies pour quelqu'un d'autre — arrivent avec l'écran « choisir la personne » (N1.x)
- [bloc:lien:pour-autrui] Attestation : fiches saisies pour quelqu'un d'autre — arrivent avec l'écran « choisir la personne » (N1.x)
- [bloc:lien:pour-autrui] Diplome : fiches saisies pour quelqu'un d'autre — arrivent avec l'écran « choisir la personne » (N1.x)
- [bloc:portee:designe] enseignant / Note : « les siennes » sur des fiches qu'il ne possède pas (elles sont à « etudiant ») — « celles qui le désignent » arrive en N1.3 (bloc pas encore construit) [type=value_error, input_value={'app': {'nom': 'c2-plate...ns': {}}}, 'depart': {}}, input_type=dict]
- For further information visit https://errors.pydantic.dev/2.12/v/value_error
