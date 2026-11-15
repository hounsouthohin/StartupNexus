# Gustave Rénovation — ce que l'usine a compris

En bref : 2 rôles (L'administrateur, Le chef de projet), 10 sortes de fiches, aucun circuit d'étapes.

## ⚠ Ce que vous demandez et que je ne sais pas encore faire

- relier chaque profil administrateur à agence : pas encore possible — lien retiré
- relier chaque profil chef de projet à agence : pas encore possible — lien retiré

**Je vous propose de construire tout le reste**, décrit ci-dessous.

## Le visiteur (sans compte)
- Ne voit rien

## L'administrateur (responsable de l'app)
- Voit tout, crée et modifie : agences
- Voit tout : chantiers, devis (dans chaque chantier), suivis de chantier (dans chaque chantier), documents (dans chaque chantier), photos (dans chaque chantier), bons de commande (dans chaque chantier), factures (dans chaque chantier)
- a son profil administrateur, créé automatiquement, qu'il peut modifier

## Le chef de projet (invité par administrateur)
- Voit tout : agences
- Voit tout, crée et modifie : chantiers
- Voit tout, crée, modifie et supprime : devis (dans chaque chantier), suivis de chantier (dans chaque chantier), documents (dans chaque chantier), photos (dans chaque chantier), bons de commande (dans chaque chantier), factures (dans chaque chantier)
- a son profil chef de projet, créé automatiquement, qu'il peut modifier

## Les informations de chaque fiche

- **Profil administrateur** : Nom (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Email (e-mail) · ☐ Téléphone (téléphone)
- **Profil chef de projet** : Nom (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Email (e-mail) · ☐ Téléphone (téléphone)
- **Agence** : Nom (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Ville (texte court) · ☐ Adresse (texte long)
- **Chantier** : Avancement (texte court) · Marge réalisée (montant) · Rentabilité (texte court) · Ville (texte court)
  - relié à : agence
  - proposé (à cocher) : ☐ Nom du chantier (texte court) · ☐ Adresse du chantier (texte long) · ☐ Date de début prévue (date) · ☐ Date de fin prévue (date)
- **Devis** : Intitulé (texte court) ◦ choisi par nous
  - relié à : dans chaque chantier
  - proposé (à cocher) : ☐ Numéro de devis (texte court) · ☐ Montant total (montant)
- **Suivi de chantier** : Intitulé (texte court) ◦ choisi par nous
  - relié à : dans chaque chantier
  - proposé (à cocher) : ☐ Compte rendu (texte long) · ☐ Date du suivi (date)
- **Document** : Intitulé (texte court) ◦ choisi par nous
  - relié à : dans chaque chantier
  - proposé (à cocher) : ☐ Type de document (texte court) · ☐ Description (texte long)
- **Photo** : Intitulé (texte court) ◦ choisi par nous
  - relié à : dans chaque chantier
  - proposé (à cocher) : ☐ Description (texte long) · ☐ Date de prise de vue (date)
- **Bon de commande** : Intitulé (texte court) ◦ choisi par nous
  - relié à : dans chaque chantier
  - proposé (à cocher) : ☐ Numéro de bon de commande (texte court) · ☐ Montant total (montant)
- **Facture** : Intitulé (texte court) ◦ choisi par nous
  - relié à : dans chaque chantier
  - proposé (à cocher) : ☐ Numéro de facture (texte court) · ☐ Montant total (montant) · ☐ Date de facture (date)

## Questions

- Le chef de projet verra tous les chantiers, pas seulement ceux qui le concernent — d'accord ? → **oui, nécessairement** : entité Chantier (registre) : il faut au moins un acteur qui le tient (« manager »)
- Votre brief ne disait pas comment reconnaître certaines fiches ; nous avons choisi : profil administrateur → « Nom » · profil chef de projet → « Nom » · agence → « Nom » · devis → « Intitulé » · suivi de chantier → « Intitulé » · document → « Intitulé » · photo → « Intitulé » · bon de commande → « Intitulé » · facture → « Intitulé »
- Acceptez-vous de construire le reste, sans ce qui n'est pas encore possible ?

## Pas encore dans notre stock (vos mots)

- Gestion de documents et photos associés aux chantiers — « La centralisation de l'ensemble des données chantiers (devis, suivis, documents, photos) »
- Automatisation des tâches répétitives autour des devis, bons de commande et facturation — « L'automatisation des tâches répétitives (devis, bons de commande, facturation) »
- Facturation — « facturation »
- Suivi des marges réalisées — « Le suivi de l'avancement des chantiers et des marges réalisées »
- Utilisation mobile sur le terrain — « accessible depuis le terrain (mobile) »
- Communication interne et externe — « L'amélioration de la communication interne et externe »
- Utilisation hors ligne sur téléphone mobile — « Utilisation sur téléphone mobile indispensable, utilisable hors ligne »
- Cloisonnement des accès par agence — « Accès sécurisé et différencié par agence et rôle »
- Automatisation des processus — « Une centralisation et automatisation des processus et des données »
- Calculs et visibilité sur marges et rentabilité par chantier, ville et globale — « Une visibilité sur les marges et la rentabilité par chantier, ville et globale »
- Communication entre acteurs internes et externes — « Une meilleure communication entre les acteurs internes et externes »

---

## Volet concepteur

### Pour répondre (`python -m usine.miroir repondre <lecture> id=valeur …`)

- `registre_entier:chef_de_projet:Chantier` = oui
- `nom:ProfilAdministrateur:nom` = oui | <nouveau nom>  (profil administrateur → « Nom »)
- `nom:ProfilChefDeProjet:nom` = oui | <nouveau nom>  (profil chef de projet → « Nom »)
- `nom:Agence:nom` = oui | <nouveau nom>  (agence → « Nom »)
- `nom:Devis:intitule` = oui | <nouveau nom>  (devis → « Intitulé »)
- `nom:SuiviChantier:intitule` = oui | <nouveau nom>  (suivi de chantier → « Intitulé »)
- `nom:Document:intitule` = oui | <nouveau nom>  (document → « Intitulé »)
- `nom:Photo:intitule` = oui | <nouveau nom>  (photo → « Intitulé »)
- `nom:BonDeCommande:intitule` = oui | <nouveau nom>  (bon de commande → « Intitulé »)
- `nom:Facture:intitule` = oui | <nouveau nom>  (facture → « Intitulé »)
- `accepter_proposition` = oui | non
- `garder:ProfilAdministrateur:Email` = oui | non
- `garder:ProfilAdministrateur:Téléphone` = oui | non
- `garder:ProfilChefDeProjet:Email` = oui | non
- `garder:ProfilChefDeProjet:Téléphone` = oui | non
- `garder:Agence:Ville` = oui | non
- `garder:Agence:Adresse` = oui | non
- `garder:Chantier:Nom du chantier` = oui | non
- `garder:Chantier:Adresse du chantier` = oui | non
- `garder:Chantier:Date de début prévue` = oui | non
- `garder:Chantier:Date de fin prévue` = oui | non
- `garder:Devis:Numéro de devis` = oui | non
- `garder:Devis:Montant total` = oui | non
- `garder:SuiviChantier:Compte rendu` = oui | non
- `garder:SuiviChantier:Date du suivi` = oui | non
- `garder:Document:Type de document` = oui | non
- `garder:Document:Description` = oui | non
- `garder:Photo:Description` = oui | non
- `garder:Photo:Date de prise de vue` = oui | non
- `garder:BonDeCommande:Numéro de bon de commande` = oui | non
- `garder:BonDeCommande:Montant total` = oui | non
- `garder:Facture:Numéro de facture` = oui | non
- `garder:Facture:Montant total` = oui | non
- `garder:Facture:Date de facture` = oui | non

### Pourquoi chaque droit

- administrateur / Agence : préréglage catalogue : visible de tous les connectés ; gestionnaire du catalogue (supprimer : seulement si le brief le dit) — « par agence »
- administrateur / Chantier : responsable de l'app : voit les registres de l'équipe (lecture) — « centralisation de l'ensemble des données chantiers »
- administrateur / Devis : enfant de chantier : même visibilité que le parent — « centralisation de l'ensemble des données chantiers »
- administrateur / SuiviChantier : enfant de chantier : même visibilité que le parent — « centralisation de l'ensemble des données chantiers »
- administrateur / Document : enfant de chantier : même visibilité que le parent — « centralisation de l'ensemble des données chantiers »
- administrateur / Photo : enfant de chantier : même visibilité que le parent — « centralisation de l'ensemble des données chantiers »
- administrateur / BonDeCommande : enfant de chantier : même visibilité que le parent — « centralisation de l'ensemble des données chantiers »
- administrateur / Facture : enfant de chantier : même visibilité que le parent — « centralisation de l'ensemble des données chantiers »
- administrateur / ProfilAdministrateur : préréglage profil : sa propre fiche, créée automatiquement — « Accès sécurisé et différencié par agence et rôle »
- chef_de_projet / Agence : préréglage catalogue : visible de tous les connectés — « par agence »
- chef_de_projet / Chantier : tient le registre (supprimer : seulement si le brief le dit) — « centralisation de l'ensemble des données chantiers »
- chef_de_projet / Devis : enfant de chantier : même visibilité que le parent, géré par qui gère le parent — « centralisation de l'ensemble des données chantiers »
- chef_de_projet / SuiviChantier : enfant de chantier : même visibilité que le parent, géré par qui gère le parent — « centralisation de l'ensemble des données chantiers »
- chef_de_projet / Document : enfant de chantier : même visibilité que le parent, géré par qui gère le parent — « centralisation de l'ensemble des données chantiers »
- chef_de_projet / Photo : enfant de chantier : même visibilité que le parent, géré par qui gère le parent — « centralisation de l'ensemble des données chantiers »
- chef_de_projet / BonDeCommande : enfant de chantier : même visibilité que le parent, géré par qui gère le parent — « centralisation de l'ensemble des données chantiers »
- chef_de_projet / Facture : enfant de chantier : même visibilité que le parent, géré par qui gère le parent — « centralisation de l'ensemble des données chantiers »
- chef_de_projet / ProfilChefDeProjet : préréglage profil : sa propre fiche, créée automatiquement — « chefs de projet »

### Refus — blocs : lien:profil

- [bloc:lien:profil] ProfilAdministrateur : un profil qui désigne une autre fiche (Agence) arrive en N1.3 (bloc « lien depuis un profil » pas encore construit)
- [bloc:lien:profil] ProfilChefDeProjet : un profil qui désigne une autre fiche (Agence) arrive en N1.3 (bloc « lien depuis un profil » pas encore construit) [type=value_error, input_value={'app': {'nom': 'renovati...ns': {}}}, 'depart': {}}, input_type=dict]
- For further information visit https://errors.pydantic.dev/2.12/v/value_error
