# Gestion des interventions — ce que l'usine a compris

En bref : 3 rôles (Le gérant, Le responsable d'équipe, L'agent), 6 sortes de fiches, aucun circuit d'étapes.

## ⚠ Ce que vous demandez et que je ne sais pas encore faire

- les interventions que le responsable d'équipe saisit pour l'agent : pas encore possible — retirées

**Je vous propose de construire tout le reste**, décrit ci-dessous.

## Le visiteur (sans compte)
- Ne voit rien

## Le gérant (responsable de l'app)
- Voit tout : Agents
- Voit tout, crée et modifie : Clients, Sites, Types de prestation, Absences

## Le responsable d'équipe (invité par gerant)
- Voit tout : Agents, Types de prestation
- Voit tout, crée et modifie : Clients, Sites, Absences

## L'agent (invité par gerant)
- Voit tout : Types de prestation
- Voit seulement les siennes, crée et modifie : Signalements de problème
- a son Agent, créé automatiquement, qu'il peut modifier

## Les informations de chaque fiche

- **Agent** : Nom (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Prénom (texte court) · ☐ Téléphone (téléphone) · ☐ Fonction (agent, responsable d'équipe) (choix)
- **Client** : Nom (texte court) ◦ choisi par nous · Coordonnées (texte long)
  - proposé (à cocher) : ☐ Interlocuteur (texte court) · ☐ Email (e-mail) · ☐ Consignes générales (texte long)
- **Site** : Adresse (texte court) · Type de locaux (texte court) · Consignes particulières (texte long, facultatif) · Fréquence de passage (choix parmi : tous les jours, une fois par semaine, une fois par mois, ponctuellement après travaux ou événement)
  - relié à : Client
  - proposé (à cocher) : ☐ Nom du site (texte court) · ☐ Informations d'accès (codes, clés, horaires) (texte long) · ☐ Contact sur place (téléphone)
- **Type de prestation** : Intitulé (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Description (texte long) · ☐ Durée habituelle (minutes) (nombre)
- **Signalement de problème** : Type de problème (texte court) · Commentaire (texte long) · Photo (lien vers le fichier) (lien web, facultatif)
  - proposé (à cocher) : ☐ Suite donnée (texte long)
- **Absence** : Motif (choix parmi : congé, maladie)
  - relié à : Agent
  - proposé (à cocher) : ☐ Date de début (date) · ☐ Date de fin (date) · ☐ Commentaire (texte long)

## Questions

- Le responsable d'équipe verra tous les Clients, pas seulement ceux qui le concernent — d'accord ? → **oui, nécessairement** : il doit les voir quand même — clôture : affiché dans les Sites qu'il voit; clôture : choisit les Clients de ses Sites
- Le responsable d'équipe verra tous les Sites, pas seulement ceux qui le concernent — d'accord ?
- Le responsable d'équipe verra toutes les Absences, pas seulement celles qui le concernent — d'accord ?
- Votre brief ne disait pas comment reconnaître certaines fiches ; nous avons choisi : Agent → « Nom » · Client → « Nom » · Type de prestation → « Intitulé »
- Acceptez-vous de construire le reste, sans ce qui n'est pas encore possible ?

## Pas encore dans notre stock (vos mots)

- Préparer et visualiser les plannings (semaine, jour, par site et par personne) — « D’organiser les plannings de nos 2 responsables d’équipes et de nos 25 agents ... Préparer les plannings de la semaine : qui va où, à quelle heure, pour quel type de prestation. »
- Détecter qu’un agent est déjà prévu ailleurs au même moment (éviter les doublons) — « Voir facilement si un agent est déjà prévu ailleurs au même moment, afin d’éviter les doublons. »
- Gérer les absences des agents et réorganiser rapidement les interventions — « Gérer les absences d’un agent (congé, maladie) et pouvoir réorganiser rapidement les interventions. »
- Utilisation par les agents depuis leur smartphone (Android, iOS si possible, éventuellement en PWA) — « Les agents, eux, utiliseront principalement leur smartphone (Android surtout, iOS si possible, mais ce n’est pas bloquant au départ). ... wpa au lieu versions mobiles par exemple »
- Photos avant/après sur les interventions et photo jointe au signalement d’un problème — « photos avant/après quand c’est nécessaire ... ajouter des photos si besoin ... avec un commentaire et, si possible, une photo »
- Sortir des rapports d’intervention par site ou par client sur une période donnée, pour montrer le suivi aux clients — « pouvoir sortir des petits rapports d’intervention (par site ou par client) sur une période donnée ... pour pouvoir montrer à nos clients un minimum de suivi (rapports d’intervention, photos, historique par site) »

---

## Volet concepteur

### Pour répondre (`python -m usine.miroir repondre <lecture> id=valeur …`)

- `registre_entier:responsable_equipe:Client` = oui
- `registre_entier:responsable_equipe:Site` = oui | non
- `registre_entier:responsable_equipe:Absence` = oui | non
- `nom:Agent:nom` = oui | <nouveau nom>  (Agent → « Nom »)
- `nom:Client:nom` = oui | <nouveau nom>  (Client → « Nom »)
- `nom:TypePrestation:intitule` = oui | <nouveau nom>  (Type de prestation → « Intitulé »)
- `accepter_proposition` = oui | non
- `garder:Agent:Prénom` = oui | non
- `garder:Agent:Téléphone` = oui | non
- `garder:Agent:Fonction (agent, responsable d'équipe)` = oui | non
- `garder:Client:Interlocuteur` = oui | non
- `garder:Client:Email` = oui | non
- `garder:Client:Consignes générales` = oui | non
- `garder:Site:Nom du site` = oui | non
- `garder:Site:Informations d'accès (codes, clés, horaires)` = oui | non
- `garder:Site:Contact sur place` = oui | non
- `garder:TypePrestation:Description` = oui | non
- `garder:TypePrestation:Durée habituelle (minutes)` = oui | non
- `garder:Signalement:Suite donnée` = oui | non
- `garder:Absence:Date de début` = oui | non
- `garder:Absence:Date de fin` = oui | non
- `garder:Absence:Commentaire` = oui | non

### Pourquoi chaque droit

- gerant / Agent : clôture : affiché dans les Absences qu'il voit ; clôture : choisit les Agents de ses Absences — « Gérer les absences d’un agent (congé, maladie) »
- gerant / Client : tient le registre (supprimer : seulement si le brief le dit) — « Créer une fiche pour chaque client, avec ses coordonnées »
- gerant / Site : tient le registre (supprimer : seulement si le brief le dit) — « de leurs différents sites (adresses, types de locaux, consignes particulières, fréquence de nettoyage) »
- gerant / TypePrestation : préréglage catalogue : visible de tous les connectés ; gestionnaire du catalogue (supprimer : seulement si le brief le dit) — « qui va où, à quelle heure, pour quel type de prestation »
- gerant / Absence : tient le registre (supprimer : seulement si le brief le dit) — « Gérer les absences d’un agent (congé, maladie) »
- responsable_equipe / Agent : clôture : affiché dans les Absences qu'il voit ; clôture : choisit les Agents de ses Absences — « Gérer les absences d’un agent (congé, maladie) »
- responsable_equipe / TypePrestation : préréglage catalogue : visible de tous les connectés — « qui va où, à quelle heure, pour quel type de prestation »
- responsable_equipe / Client : tient le registre (supprimer : seulement si le brief le dit) — « Créer une fiche pour chaque client, avec ses coordonnées »
- responsable_equipe / Site : tient le registre (supprimer : seulement si le brief le dit) — « de leurs différents sites (adresses, types de locaux, consignes particulières, fréquence de nettoyage) »
- responsable_equipe / Absence : tient le registre (supprimer : seulement si le brief le dit) — « Gérer les absences d’un agent (congé, maladie) »
- agent / TypePrestation : préréglage catalogue : visible de tous les connectés — « qui va où, à quelle heure, pour quel type de prestation »
- agent / Signalement : préréglage collection : le propriétaire crée et modifie les siens ; exception : « permettre à l’agent de nous remonter l’information simplement, avec un commentaire » — « permettre à l’agent de nous remonter l’information simplement, avec un commentaire et, si possible, une photo » « permettre à l’agent de nous remonter l’information simplement, avec un commentaire »
- agent / Agent : préréglage profil : sa propre fiche, créée automatiquement — « environ 25 agents qui interviennent sur l’ensemble de la région »

### Refus — blocs : lien:pour-autrui

- [bloc:lien:pour-autrui] Intervention : fiches saisies pour quelqu'un d'autre — arrivent avec l'écran « choisir la personne » (N1.x) [type=value_error, input_value={'app': {'nom': 'c2-netto...ns': {}}}, 'depart': {}}, input_type=dict]
- For further information visit https://errors.pydantic.dev/2.12/v/value_error
