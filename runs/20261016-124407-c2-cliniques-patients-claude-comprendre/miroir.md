# Gestion des cliniques — ce que l'usine a compris

En bref : 5 rôles (L'administrateur de la clinique, Le médecin, L'infirmière, La réceptionniste, Le patient), 11 sortes de fiches, aucun circuit d'étapes.

## ⚠ Ce que vous demandez et que je ne sais pas encore faire

- relier chaque médecin à clinique : pas encore possible — lien retiré
- L'administrateur de la clinique crée le compte des patients : pas encore possible (les invitations arrivent avec la connexion)
- L'infirmière crée le compte des patients : pas encore possible (les invitations arrivent avec la connexion)
- Le médecin crée le compte des patients : pas encore possible (les invitations arrivent avec la connexion)

**Je vous propose de construire tout le reste**, décrit ci-dessous.

## Le visiteur (sans compte)
- Ne voit rien

## L'administrateur de la clinique (responsable de l'app)
- Voit tout et modifie : patients, rendez-vous
- Voit tout, crée et modifie : cliniques, notes sur l'état du patient, ordonnances, factures
- Voit tout : jours fériés, rappels de rendez-vous, événements
- voit les médecins affichés dans les rendez-vous qu'il consulte (sans page à part)

## Le médecin (invité par administrateur)
- Voit tout et modifie : patients
- Voit tout : cliniques, jours fériés
- Voit seulement les siennes, crée et modifie : disponibilités
- Voit tout, crée et modifie : ordonnances
- a son médecin, créé automatiquement, qu'il peut modifier

## L'infirmière (invité par administrateur)
- Voit tout et modifie : patients, rendez-vous
- Voit tout : cliniques, jours fériés
- Voit tout, crée et modifie : notes sur l'état du patient, ordonnances
- voit les médecins affichés dans les rendez-vous qu'il consulte (sans page à part)

## La réceptionniste (invité par administrateur)
- Voit tout : cliniques, rendez-vous
- Voit tout, crée et modifie : jours fériés, rappels de rendez-vous, événements

## Le patient (s'inscrit lui-même)
- Voit tout : médecins, cliniques, jours fériés
- Voit seulement les siennes, crée et modifie : rendez-vous
- a son patient, créé automatiquement, qu'il peut modifier

## Les informations de chaque fiche

- **Patient** : Nom (texte court) ◦ choisi par nous · Réception de l'inscription accusée (oui / non)
  - proposé (à cocher) : ☐ Prénom (texte court) · ☐ Date de naissance (date) · ☐ Téléphone (téléphone) · ☐ E-mail (e-mail) · ☐ Adresse (texte long)
- **Médecin** : Notification par e-mail (oui / non)
  - proposé (à cocher) : ☐ Nom (texte court) · ☐ E-mail (e-mail) · ☐ Spécialité (texte court) · ☐ Téléphone (téléphone)
- **Clinique** : Nom (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Adresse (texte long) · ☐ Téléphone (téléphone) · ☐ Modules activés (texte court)
- **Rendez-vous** : Privé (oui / non)
  - relié à : médecin, clinique
  - proposé (à cocher) : ☐ Date et heure (date et heure) · ☐ Motif (texte long) · ☐ Durée (nombre)
- **Disponibilité** : Intitulé (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Début (date et heure) · ☐ Fin (date et heure) · ☐ Jour de la semaine (texte court)
- **Jour férié** : Nom (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Date (date)
- **Rappel de rendez-vous** : Intitulé (texte court) ◦ choisi par nous
  - relié à : rendez-vous
  - proposé (à cocher) : ☐ Date et heure d'envoi (date et heure) · ☐ Canal (SMS, e-mail) (texte court) · ☐ Message (texte long)
- **Événement** : Intitulé (texte court) ◦ choisi par nous · Important (oui / non) · Date (date)
  - proposé (à cocher) : ☐ Description (texte long) · ☐ Nature (événement ou avis) (texte court) · ☐ Heure (date et heure)
- **Note sur l'état du patient** : État du patient (texte long)
  - relié à : patient
- **Ordonnance** : Médicaments (texte long) · Statut (texte court)
  - relié à : patient
  - proposé (à cocher) : ☐ Posologie (texte long) · ☐ Durée du traitement (texte court)
- **Facture** : Numéro (texte court) ◦ choisi par nous
  - relié à : patient
  - proposé (à cocher) : ☐ Montant (montant) · ☐ Détail des prestations (texte long) · ☐ Payée (oui / non)

## Questions

- L'administrateur de la clinique verra les médecins (ex. nom, coordonnées) affichés dans les rendez-vous qu'il traite — est-ce acceptable ? → **oui, nécessairement** : il doit les voir quand même — clôture : affiché dans les rendez-vous qu'il voit
- Le médecin verra toutes les ordonnances, pas seulement celles qui le concernent — d'accord ?
- L'infirmière verra les médecins (ex. nom, coordonnées) affichés dans les rendez-vous qu'elle traite — est-ce acceptable ? → **oui, nécessairement** : il doit les voir quand même — clôture : affiché dans les rendez-vous qu'il voit
- L'infirmière verra toutes les notes sur l'état du patient, pas seulement celles qui la concernent — d'accord ?
- L'infirmière verra toutes les ordonnances, pas seulement celles qui la concernent — d'accord ?
- La réceptionniste verra tous les rappels de rendez-vous, pas seulement ceux qui la concernent — d'accord ? → **oui, nécessairement** : entité RappelRendezVous (registre) : il faut au moins un acteur qui le tient (« manager »)
- La réceptionniste verra tous les événements, pas seulement ceux qui la concernent — d'accord ? → **oui, nécessairement** : entité Evenement (registre) : il faut au moins un acteur qui le tient (« manager »)
- Votre brief ne disait pas comment reconnaître certaines fiches ; nous avons choisi : patient → « Nom » · clinique → « Nom » · disponibilité → « Intitulé » · jour férié → « Nom » · rappel de rendez-vous → « Intitulé » · événement → « Intitulé » · facture → « Numéro »
- Acceptez-vous de construire le reste, sans ce qui n'est pas encore possible ?

## Pas encore dans notre stock (vos mots)

- Prise de rendez-vous en fonction de la disponibilité des médecins — « Le patient peut prendre rendez-vous avec un médecin selon sa disponibilité »
- Gestion des jours fériés dans l'agenda — « Ajoutez des jours fériés »
- Calendrier du médecin dans son tableau de bord — « Tableau de bord avec un calendrier pour le médecin »
- Vue des événements importants de la journée pour la réceptionniste — « Aperçu rapide des événements importants de la journée »
- Calendrier tenu par la réceptionniste avec les événements et avis importants — « Mettez à jour et gérez le calendrier avec les événements et avis importants »
- Rappels de rendez-vous — « la réceptionniste définit des rappels de rendez-vous »
- Notifications par e-mail aux médecins — « définit la notification par e-mail pour les médecins »
- Alertes par SMS sur les événements importants — « Des alertes de notification sont envoyées parla plateforme sur les événements importants marqués »
- Lien avec le service SMS Twilio — « Notification SMS (Twilio) »
- Tableau de bord général — « Tableau de bord : permet de visualiser les modules importants de l'hôpital »
- Génération de rapports pour la gestion et la direction — « permet d'exploiter les données en générant des rapports pour la gestion ... Accéder et gérer les rapports pour la direction »
- Impression des ordonnances — « obtenez une liste complète des ordonnances de médicaments à un seul endroit et imprimez-la pour votre référence »
- Génération et impression de factures pour les patients — « Impression de la facture : générez une facture pour les patients »
- Plusieurs cliniques gérées dans la même plateforme, chacune avec ses données — « Gestion de plusieurs cliniques/hôpitaux pour les médecins »
- Activation ou désactivation des modules selon les besoins — « sélectionnez et basculez pour activer un module particulier ou le désactiver selon vos besoins »

---

## Volet concepteur

### Pour répondre (`python -m usine.miroir repondre <lecture> id=valeur …`)

- `vu_via:administrateur:Medecin` = oui
- `registre_entier:medecin:Ordonnance` = oui | non
- `vu_via:infirmiere:Medecin` = oui
- `registre_entier:infirmiere:NoteEtatPatient` = oui | non
- `registre_entier:infirmiere:Ordonnance` = oui | non
- `registre_entier:receptionniste:RappelRendezVous` = oui
- `registre_entier:receptionniste:Evenement` = oui
- `nom:Patient:nom` = oui | <nouveau nom>  (patient → « Nom »)
- `nom:Clinique:nom` = oui | <nouveau nom>  (clinique → « Nom »)
- `nom:Disponibilite:intitule` = oui | <nouveau nom>  (disponibilité → « Intitulé »)
- `nom:JourFerie:nom` = oui | <nouveau nom>  (jour férié → « Nom »)
- `nom:RappelRendezVous:intitule` = oui | <nouveau nom>  (rappel de rendez-vous → « Intitulé »)
- `nom:Evenement:intitule` = oui | <nouveau nom>  (événement → « Intitulé »)
- `nom:Facture:numero` = oui | <nouveau nom>  (facture → « Numéro »)
- `accepter_proposition` = oui | non
- `garder:Patient:Prénom` = oui | non
- `garder:Patient:Date de naissance` = oui | non
- `garder:Patient:Téléphone` = oui | non
- `garder:Patient:E-mail` = oui | non
- `garder:Patient:Adresse` = oui | non
- `garder:Medecin:Nom` = oui | non
- `garder:Medecin:E-mail` = oui | non
- `garder:Medecin:Spécialité` = oui | non
- `garder:Medecin:Téléphone` = oui | non
- `garder:Clinique:Adresse` = oui | non
- `garder:Clinique:Téléphone` = oui | non
- `garder:Clinique:Modules activés` = oui | non
- `garder:RendezVous:Date et heure` = oui | non
- `garder:RendezVous:Motif` = oui | non
- `garder:RendezVous:Durée` = oui | non
- `garder:Disponibilite:Début` = oui | non
- `garder:Disponibilite:Fin` = oui | non
- `garder:Disponibilite:Jour de la semaine` = oui | non
- `garder:JourFerie:Date` = oui | non
- `garder:RappelRendezVous:Date et heure d'envoi` = oui | non
- `garder:RappelRendezVous:Canal (SMS, e-mail)` = oui | non
- `garder:RappelRendezVous:Message` = oui | non
- `garder:Evenement:Description` = oui | non
- `garder:Evenement:Nature (événement ou avis)` = oui | non
- `garder:Evenement:Heure` = oui | non
- `garder:Ordonnance:Posologie` = oui | non
- `garder:Ordonnance:Durée du traitement` = oui | non
- `garder:Facture:Montant` = oui | non
- `garder:Facture:Détail des prestations` = oui | non
- `garder:Facture:Payée` = oui | non

### Pourquoi chaque droit

- administrateur / Patient : exception : « L'administrateur de la clinique / l'infirmière peuvent gérer les données des patients » ; exception : « L'administrateur de la clinique / l'infirmière peuvent gérer les données des patients » ; exception : « L'administrateur de la clinique peut accuser réception de l'inscription du patient » — « L'administrateur de la clinique / l'infirmière peuvent gérer les données des patients » « L'administrateur de la clinique / l'infirmière peuvent gérer les données des patients » « L'administrateur de la clinique peut accuser réception de l'inscription du patient »
- administrateur / RendezVous : exception : « L'administrateur de la clinique / l'infirmière » ; exception : « L'administrateur de la clinique / l'infirmière » — « L'administrateur de la clinique / l'infirmière » « L'administrateur de la clinique / l'infirmière »
- administrateur / Clinique : préréglage catalogue : visible de tous les connectés ; gestionnaire du catalogue (supprimer : seulement si le brief le dit) — « Multiclinique : Gestion de plusieurs cliniques/hôpitaux pour les médecins »
- administrateur / NoteEtatPatient : tient le registre (supprimer : seulement si le brief le dit) ; exception : « L'administrateur de la clinique / l'infirmière » — « L'administrateur de la clinique / l'infirmière peuvent gérer les données des patients » « L'administrateur de la clinique / l'infirmière »
- administrateur / Ordonnance : tient le registre (supprimer : seulement si le brief le dit) — « Gérer la prescription des patients »
- administrateur / Facture : tient le registre (supprimer : seulement si le brief le dit) — « générez une facture pour les patients »
- administrateur / JourFerie : préréglage catalogue : visible de tous les connectés — « Ajoutez des jours fériés »
- administrateur / RappelRendezVous : responsable de l'app : voit les registres de l'équipe (lecture) — « la réceptionniste définit des rappels de rendez-vous »
- administrateur / Evenement : responsable de l'app : voit les registres de l'équipe (lecture) — « Mettez à jour et gérez le calendrier avec les événements et avis importants »
- administrateur / Medecin : clôture : affiché dans les rendez-vous qu'il voit
- medecin / Patient : exception : « Le médecin peut gérer les données des patients » ; exception : « Le médecin peut gérer les données des patients » — « Le médecin peut gérer les données des patients » « Le médecin peut gérer les données des patients »
- medecin / Clinique : préréglage catalogue : visible de tous les connectés — « Multiclinique : Gestion de plusieurs cliniques/hôpitaux pour les médecins »
- medecin / JourFerie : préréglage catalogue : visible de tous les connectés — « Ajoutez des jours fériés »
- medecin / Disponibilite : préréglage collection : le propriétaire crée et modifie les siens — « prendre rendez-vous avec un médecin selon sa disponibilité »
- medecin / Ordonnance : tient le registre (supprimer : seulement si le brief le dit) ; exception : « Gérer la prescription des patients » ; exception : « Gérer la prescription des patients » ; exception : « Gérer la prescription des patients » — « Gérer la prescription des patients » « Gérer la prescription des patients » « Gérer la prescription des patients » « Gérer la prescription des patients »
- medecin / Medecin : préréglage profil : sa propre fiche, créée automatiquement — « Gestion de plusieurs cliniques/hôpitaux pour les médecins »
- infirmiere / Patient : exception : « L'administrateur de la clinique / l'infirmière peuvent gérer les données des patients » ; exception : « L'administrateur de la clinique / l'infirmière peuvent gérer les données des patients » — « L'administrateur de la clinique / l'infirmière peuvent gérer les données des patients » « L'administrateur de la clinique / l'infirmière peuvent gérer les données des patients »
- infirmiere / RendezVous : exception : « L'administrateur de la clinique / l'infirmière » ; exception : « L'administrateur de la clinique / l'infirmière » — « L'administrateur de la clinique / l'infirmière » « L'administrateur de la clinique / l'infirmière »
- infirmiere / Clinique : préréglage catalogue : visible de tous les connectés — « Multiclinique : Gestion de plusieurs cliniques/hôpitaux pour les médecins »
- infirmiere / JourFerie : préréglage catalogue : visible de tous les connectés — « Ajoutez des jours fériés »
- infirmiere / NoteEtatPatient : tient le registre (supprimer : seulement si le brief le dit) ; exception : « L'administrateur de la clinique / l'infirmière » — « L'administrateur de la clinique / l'infirmière peuvent gérer les données des patients » « L'administrateur de la clinique / l'infirmière »
- infirmiere / Ordonnance : tient le registre (supprimer : seulement si le brief le dit) — « Gérer la prescription des patients »
- infirmiere / Medecin : clôture : affiché dans les rendez-vous qu'il voit
- receptionniste / Clinique : préréglage catalogue : visible de tous les connectés — « Multiclinique : Gestion de plusieurs cliniques/hôpitaux pour les médecins »
- receptionniste / RendezVous : clôture : affiché dans les rappels de rendez-vous qu'il voit ; clôture : choisit les rendez-vous de ses rappels de rendez-vous — « la réceptionniste définit des rappels de rendez-vous »
- receptionniste / JourFerie : préréglage catalogue : visible de tous les connectés ; gestionnaire du catalogue (supprimer : seulement si le brief le dit) — « Ajoutez des jours fériés »
- receptionniste / RappelRendezVous : tient le registre (supprimer : seulement si le brief le dit) ; exception : « la réceptionniste définit des rappels de rendez-vous » — « la réceptionniste définit des rappels de rendez-vous » « la réceptionniste définit des rappels de rendez-vous »
- receptionniste / Evenement : tient le registre (supprimer : seulement si le brief le dit) ; exception : « Aperçu rapide des événements importants de la journée » ; exception : « Mettez à jour et gérez le calendrier avec les événements et avis importants » ; exception : « Mettez à jour et gérez le calendrier avec les événements et avis importants » — « Mettez à jour et gérez le calendrier avec les événements et avis importants » « Aperçu rapide des événements importants de la journée » « Mettez à jour et gérez le calendrier avec les événements et avis importants » « Mettez à jour et gérez le calendrier avec les événements et avis importants »
- patient / Medecin : clôture : affiché dans les rendez-vous qu'il voit ; clôture : choisit les médecins de ses rendez-vous — « Le patient peut prendre rendez-vous avec un médecin selon sa disponibilité »
- patient / Clinique : préréglage catalogue : visible de tous les connectés — « Multiclinique : Gestion de plusieurs cliniques/hôpitaux pour les médecins »
- patient / JourFerie : préréglage catalogue : visible de tous les connectés — « Ajoutez des jours fériés »
- patient / RendezVous : préréglage collection : le propriétaire crée et modifie les siens ; exception : « Le patient peut prendre rendez-vous avec un médecin selon sa disponibilité » — « Le patient peut prendre rendez-vous avec un médecin selon sa disponibilité » « Le patient peut prendre rendez-vous avec un médecin selon sa disponibilité »
- patient / Patient : préréglage profil : sa propre fiche, créée automatiquement ; exception : « Permet au patient de s'inscrire » — « L'administrateur de la clinique peut accuser réception de l'inscription du patient » « Permet au patient de s'inscrire »

### Refus — blocs : acteur:invitation, lien:profil

- [bloc:lien:profil] Medecin : un profil qui désigne une autre fiche (Clinique) arrive en N1.3 (bloc « lien depuis un profil » pas encore construit)
- [bloc:acteur:invitation] administrateur / Patient : créer le compte d'une autre personne, c'est l'inviter — arrive avec la connexion et l'équipe (N1.5)
- [bloc:acteur:invitation] infirmiere / Patient : créer le compte d'une autre personne, c'est l'inviter — arrive avec la connexion et l'équipe (N1.5)
- [bloc:acteur:invitation] medecin / Patient : créer le compte d'une autre personne, c'est l'inviter — arrive avec la connexion et l'équipe (N1.5) [type=value_error, input_value={'app': {'nom': 'c2-clini...ns': {}}}, 'depart': {}}, input_type=dict]
- For further information visit https://errors.pydantic.dev/2.12/v/value_error
