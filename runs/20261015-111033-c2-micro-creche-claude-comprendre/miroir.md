# Gestion de la micro-crèche — ce que l'usine a compris

En bref : 3 rôles (La direction, Le membre du personnel, Le parent), 9 sortes de fiches, aucun circuit d'étapes.

## ⚠ Ce que vous demandez et que je ne sais pas encore faire

- La direction crée le compte des membres du personnel : pas encore possible (les invitations arrivent avec la connexion)
- La direction crée le compte des parents : pas encore possible (les invitations arrivent avec la connexion)
- les fiches de paie que la direction saisit pour le membre du personnel : pas encore possible — retirées
- les photos que le membre du personnel saisit pour le parent : pas encore possible — retirées
- les transmissions que le membre du personnel saisit pour le parent : pas encore possible — retirées

**Je vous propose de construire tout le reste**, décrit ci-dessous.

## Le visiteur (sans compte)
- Ne voit rien

## La direction (responsable de l'app)
- Voit tout : pointages
- Voit tout, crée et modifie : articles en stock, documents

## Le membre du personnel (invité par direction)
- Voit seulement les siennes, crée et modifie : plannings, pointages, signalements de besoin
- Voit tout : articles en stock
- a son membre du personnel, créé automatiquement, qu'il peut modifier

## Le parent (invité par direction)
- Voit seulement les siennes, crée et modifie : enfants, réservations de créneau
- a son parent, créé automatiquement, qu'il peut modifier

## Les informations de chaque fiche

- **Membre du personnel** : Nom (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Prénom (texte court) · ☐ Poste / fonction (texte court) · ☐ Téléphone (téléphone) · ☐ Email (e-mail)
- **Parent** : Nom (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Prénom (texte court) · ☐ Téléphone (téléphone) · ☐ Email (e-mail) · ☐ Adresse (texte long)
- **Enfant** : Nom (texte court) ◦ choisi par nous · Informations de santé (texte long) · Habitudes (texte long)
  - proposé (à cocher) : ☐ Prénom (texte court) · ☐ Date de naissance (date) · ☐ Allergies (texte long) · ☐ Personnes autorisées à récupérer l'enfant (texte long)
- **Réservation de créneau** : Début du créneau (date et heure) · Fin du créneau (date et heure)
  - relié à : enfant
  - proposé (à cocher) : ☐ Commentaire (texte long)
- **Planning** : Intitulé (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Date de début (date) · ☐ Date de fin (date) · ☐ Horaires (texte long)
- **Pointage** : Intitulé (texte court) ◦ choisi par nous · Heure d'arrivée (date et heure) · Heure de départ (date et heure, facultatif)
  - proposé (à cocher) : ☐ Commentaire (texte long)
- **Signalement de besoin** : Intitulé (texte court) ◦ choisi par nous
  - relié à : article en stock
  - proposé (à cocher) : ☐ Quantité souhaitée (nombre) · ☐ Commentaire (texte long) · ☐ Urgent (oui / non)
- **Article en stock** : Nom (texte court) ◦ choisi par nous · Quantité en stock (nombre) · Seuil d'alerte (nombre)
  - proposé (à cocher) : ☐ Unité (texte court) · ☐ Catégorie (texte court) · ☐ Fournisseur (texte court)
- **Document** : Titre (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Lien du fichier (lien web) · ☐ Message (texte long) · ☐ Description (texte long)

## Questions

- Le membre du personnel verra tous les articles en stock, pas seulement ceux qui le concernent — d'accord ? → **oui, nécessairement** : il doit les voir quand même — clôture : affiché dans les signalements de besoin qu'il voit; clôture : choisit les articles en stock de ses signalements de besoin
- Votre brief ne disait pas comment reconnaître certaines fiches ; nous avons choisi : membre du personnel → « Nom » · parent → « Nom » · enfant → « Nom » · planning → « Intitulé » · pointage → « Intitulé » · signalement de besoin → « Intitulé » · article en stock → « Nom » · document → « Titre »
- Acceptez-vous de construire le reste, sans ce qui n'est pas encore possible ?

## Pas encore dans notre stock (vos mots)

- Planning du personnel — « Planning du personnel »
- Réservation de créneaux de garde par les parents (gestion de créneaux sur un calendrier) — « Réservation de créneaux de garde »
- Mise à disposition des fiches de paie (documents) pour le personnel — « Accès aux fiches de paie »
- Accès sécurisé des parents à des photos — « Accès sécurisé à des photos »
- Alerte quand un stock passe sous un seuil — « Gestion des stocks (ajout, seuils d’alerte) »
- Envoi de documents par la direction — « Envoi de documents/messages »
- Communication et envoi de messages avec les parents — « la communication avec les parents ... Envoi de documents/messages »
- Application mobile Android/iOS — « Application mobile Android/iOS (cross-platform possible) »
- Double authentification (2FA) optionnelle — « Authentification sécurisée (2FA optionnelle) »
- Interface multilingue (français, créole) — « Interface multilingue (français obligatoire, créole souhaité) »
- Back-office de facturation (optionnel) — « Ajout d’un back-office de facturation »
- Back-office de messagerie (optionnel) — « back-office de facturation ou de messagerie »

---

## Volet concepteur

### Pour répondre (`python -m usine.miroir repondre <lecture> id=valeur …`)

- `registre_entier:personnel:ArticleStock` = oui
- `nom:ProfilPersonnel:nom` = oui | <nouveau nom>  (membre du personnel → « Nom »)
- `nom:ProfilParent:nom` = oui | <nouveau nom>  (parent → « Nom »)
- `nom:Enfant:nom` = oui | <nouveau nom>  (enfant → « Nom »)
- `nom:Planning:intitule` = oui | <nouveau nom>  (planning → « Intitulé »)
- `nom:Pointage:intitule` = oui | <nouveau nom>  (pointage → « Intitulé »)
- `nom:SignalementBesoin:intitule` = oui | <nouveau nom>  (signalement de besoin → « Intitulé »)
- `nom:ArticleStock:nom` = oui | <nouveau nom>  (article en stock → « Nom »)
- `nom:Document:titre` = oui | <nouveau nom>  (document → « Titre »)
- `accepter_proposition` = oui | non
- `garder:ProfilPersonnel:Prénom` = oui | non
- `garder:ProfilPersonnel:Poste / fonction` = oui | non
- `garder:ProfilPersonnel:Téléphone` = oui | non
- `garder:ProfilPersonnel:Email` = oui | non
- `garder:ProfilParent:Prénom` = oui | non
- `garder:ProfilParent:Téléphone` = oui | non
- `garder:ProfilParent:Email` = oui | non
- `garder:ProfilParent:Adresse` = oui | non
- `garder:Enfant:Prénom` = oui | non
- `garder:Enfant:Date de naissance` = oui | non
- `garder:Enfant:Allergies` = oui | non
- `garder:Enfant:Personnes autorisées à récupérer l'enfant` = oui | non
- `garder:Reservation:Commentaire` = oui | non
- `garder:Planning:Date de début` = oui | non
- `garder:Planning:Date de fin` = oui | non
- `garder:Planning:Horaires` = oui | non
- `garder:Pointage:Commentaire` = oui | non
- `garder:SignalementBesoin:Quantité souhaitée` = oui | non
- `garder:SignalementBesoin:Commentaire` = oui | non
- `garder:SignalementBesoin:Urgent` = oui | non
- `garder:ArticleStock:Unité` = oui | non
- `garder:ArticleStock:Catégorie` = oui | non
- `garder:ArticleStock:Fournisseur` = oui | non
- `garder:Document:Lien du fichier` = oui | non
- `garder:Document:Message` = oui | non
- `garder:Document:Description` = oui | non

### Pourquoi chaque droit

- direction / Pointage : exception : « Suivi des présences et pointages » — « Suivi des présences et pointages »
- direction / ArticleStock : tient le registre (supprimer : seulement si le brief le dit) ; exception : « Gestion des stocks (ajout » — « Gestion des stocks (ajout, seuils d’alerte) » « Gestion des stocks (ajout »
- direction / Document : tient le registre (supprimer : seulement si le brief le dit) ; exception : « Envoi de documents/messages » — « Envoi de documents/messages » « Envoi de documents/messages »
- personnel / Planning : préréglage collection : le propriétaire crée et modifie les siens — « Planning du personnel »
- personnel / Pointage : préréglage collection : le propriétaire crée et modifie les siens ; exception : « Pointage d’arrivée/départ » — « Suivi des présences et pointages » « Pointage d’arrivée/départ »
- personnel / SignalementBesoin : préréglage collection : le propriétaire crée et modifie les siens ; exception : « Signalement de besoins (stocks manquants) » — « Signalement de besoins (stocks manquants) » « Signalement de besoins (stocks manquants) »
- personnel / ArticleStock : clôture : affiché dans les signalements de besoin qu'il voit ; clôture : choisit les articles en stock de ses signalements de besoin — « Signalement de besoins (stocks manquants) »
- personnel / ProfilPersonnel : préréglage profil : sa propre fiche, créée automatiquement — « Création comptes personnel/parents »
- parent / Enfant : préréglage collection : le propriétaire crée et modifie les siens — « Informations enfants (santé, habitudes »
- parent / Reservation : préréglage collection : le propriétaire crée et modifie les siens ; exception : « Réservation de créneaux de garde » — « Réservation de créneaux de garde » « Réservation de créneaux de garde »
- parent / ProfilParent : préréglage profil : sa propre fiche, créée automatiquement — « Création comptes personnel/parents »

### Refus — blocs : acteur:invitation, lien:pour-autrui

- [bloc:lien:pour-autrui] Transmission : fiches saisies pour quelqu'un d'autre — arrivent avec l'écran « choisir la personne » (N1.x)
- [bloc:lien:pour-autrui] Photo : fiches saisies pour quelqu'un d'autre — arrivent avec l'écran « choisir la personne » (N1.x)
- [bloc:lien:pour-autrui] FicheDePaie : fiches saisies pour quelqu'un d'autre — arrivent avec l'écran « choisir la personne » (N1.x)
- [bloc:acteur:invitation] direction / ProfilPersonnel : créer le compte d'une autre personne, c'est l'inviter — arrive avec la connexion et l'équipe (N1.5)
- [bloc:acteur:invitation] direction / ProfilParent : créer le compte d'une autre personne, c'est l'inviter — arrive avec la connexion et l'équipe (N1.5) [type=value_error, input_value={'app': {'nom': 'c2-micro...ns': {}}}, 'depart': {}}, input_type=dict]
- For further information visit https://errors.pydantic.dev/2.12/v/value_error
