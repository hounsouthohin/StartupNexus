# Gestion du cabinet — ce que l'usine a compris

En bref : 3 rôles (L'associé, Le manager, Le collaborateur), 6 sortes de fiches, 1 circuit d'étapes.

## Le visiteur (sans compte)
- Ne voit rien

## L'associé (responsable de l'app)
- Voit tout, crée et modifie : Dossiers juridiques, Types de dossier, Clients, Forfaits de facturation
- Voit tout : Profils collaborateurs

## Le manager (invité par associe)
- Voit tout : Types de dossier, Profils collaborateurs, Clients
- Dossiers juridiques : voit tout, en crée, les modifie, les fait passer de « à attribuer » à « attribué »

## Le collaborateur (invité par associe)
- Voit tout : Types de dossier
- Voit seulement les siennes, crée et modifie : Tâches
- a son Profil collaborateur, créé automatiquement, qu'il peut modifier

## Les étapes

- Le dossier juridique passe par : « à attribuer » → « attribué »
  - Le manager fait passer de « à attribuer » à « attribué »

## Les informations de chaque fiche

- **Dossier juridique** : Niveau d'importance (texte court) · Niveau d'urgence (texte court) · Charge de travail prévue (heures) (nombre, facultatif)
  - relié à : Type de dossier, Client, Profil collaborateur
  - proposé (à cocher) : ☐ Intitulé ou référence du dossier (texte court) · ☐ Description du dossier (texte long) · ☐ Date d'échéance (date)
- **Type de dossier** : Nom (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Description (texte long) · ☐ Charge de travail moyenne (heures) (nombre)
- **Profil collaborateur** : Nom (texte court) ◦ choisi par nous · Spécialités (texte court) · Ancienneté (années) (nombre)
  - proposé (à cocher) : ☐ Prénom (texte court) · ☐ Email (e-mail) · ☐ Fonction (collaborateur, manager, associé) (texte court) · ☐ Équipe (texte court) · ☐ Seuil de charge de travail (nombre) · ☐ Date d'arrivée au cabinet (date)
- **Tâche** : Intitulé (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Description (texte long) · ☐ Durée estimée (heures) (nombre) · ☐ Échéance (date)
- **Client** : Nom (texte court) ◦ choisi par nous
  - proposé (à cocher) : ☐ Email (e-mail) · ☐ Téléphone (téléphone) · ☐ Adresse (texte long)
- **Forfait de facturation** : Heures déjà facturées (nombre) · Nombre d'heures maximum négocié (nombre)
  - relié à : Client
  - proposé (à cocher) : ☐ Intitulé du forfait (texte court) · ☐ Montant du forfait (montant) · ☐ Seuil d'alerte (% du maximum) (nombre) · ☐ Date de début (date) · ☐ Date de fin (date)

## Questions

- Le manager verra tous les Dossiers juridiques, pas seulement ceux qui le concernent — d'accord ? → **oui, nécessairement** : entité Dossier (registre) : l'initiateur (manager) doit être parmi ceux qui le tiennent
- Le manager verra tous les Clients, pas seulement ceux qui le concernent — d'accord ? → **oui, nécessairement** : il doit les voir quand même — clôture : affiché dans les Dossiers juridiques qu'il voit; clôture : choisit les Clients de ses Dossiers juridiques
- Votre brief ne disait pas comment reconnaître certaines fiches ; nous avons choisi : Type de dossier → « Nom » · Profil collaborateur → « Nom » · Tâche → « Intitulé » · Client → « Nom »

## Pas encore dans notre stock (vos mots)

- Aide automatique à la répartition des dossiers selon les dossiers déjà attribués, les spécialités et l'ancienneté des collaborateurs — « Assistance à la répartition des dossiers pour le manager en fonction des dossiers déjà attribués, des spécialités des collaborateurs, de leur ancienneté »
- Lien avec le logiciel existant où sont saisies les heures effectuées — « les heures ayant été effectuées étant rentrées dans un autre logiciel, nous souhaiterions lier les deux »
- Vue en temps réel de la charge de travail des équipes pour l'associé — « L'associé est ainsi conscient en temps réel de la charge de travail de ses équipes »
- L'associé ne voit que la charge de « ses » équipes — « la charge de travail de ses équipes »
- Alerte par e-mail quand un collaborateur a une charge de travail trop importante — « système d'alerte mail dès lors qu'un collaborateur possède une charge de travail trop importante »
- Prévision par machine learning de la charge de travail future d'un dossier selon sa typologie — « Machine learning pour prévoir, selon la typologie de dossier, la charge de travail que celui-ci peut représenter dans l'avenir »
- Suivi des forfaits de facturation (heures déjà facturées par rapport au maximum négocié) — « suivi des forfait de facturation »
- Alerte quand le nombre d'heures facturées approche du maximum négocié avec le client — « un système d'alertes dès lors que le nombre d'heures déjà facturées s'approchent du maximum négocié avec le client »

---

## Volet concepteur

### Pour répondre (`python -m usine.miroir repondre <lecture> id=valeur …`)

- `registre_entier:manager:Dossier` = oui
- `registre_entier:manager:Client` = oui
- `nom:TypeDossier:nom` = oui | <nouveau nom>  (Type de dossier → « Nom »)
- `nom:Collaborateur:nom` = oui | <nouveau nom>  (Profil collaborateur → « Nom »)
- `nom:Tache:intitule` = oui | <nouveau nom>  (Tâche → « Intitulé »)
- `nom:Client:nom` = oui | <nouveau nom>  (Client → « Nom »)
- `garder:Dossier:Intitulé ou référence du dossier` = oui | non
- `garder:Dossier:Description du dossier` = oui | non
- `garder:Dossier:Date d'échéance` = oui | non
- `garder:TypeDossier:Description` = oui | non
- `garder:TypeDossier:Charge de travail moyenne (heures)` = oui | non
- `garder:Collaborateur:Prénom` = oui | non
- `garder:Collaborateur:Email` = oui | non
- `garder:Collaborateur:Fonction (collaborateur, manager, associé)` = oui | non
- `garder:Collaborateur:Équipe` = oui | non
- `garder:Collaborateur:Seuil de charge de travail` = oui | non
- `garder:Collaborateur:Date d'arrivée au cabinet` = oui | non
- `garder:Tache:Description` = oui | non
- `garder:Tache:Durée estimée (heures)` = oui | non
- `garder:Tache:Échéance` = oui | non
- `garder:Client:Email` = oui | non
- `garder:Client:Téléphone` = oui | non
- `garder:Client:Adresse` = oui | non
- `garder:ForfaitFacturation:Intitulé du forfait` = oui | non
- `garder:ForfaitFacturation:Montant du forfait` = oui | non
- `garder:ForfaitFacturation:Seuil d'alerte (% du maximum)` = oui | non
- `garder:ForfaitFacturation:Date de début` = oui | non
- `garder:ForfaitFacturation:Date de fin` = oui | non

### Pourquoi chaque droit

- associe / Dossier : tient le registre (supprimer : seulement si le brief le dit) — « pour chaque dossier juridique, classement en fonction du niveau d'importance et d'urgence »
- associe / TypeDossier : préréglage catalogue : visible de tous les connectés ; gestionnaire du catalogue (supprimer : seulement si le brief le dit) — « selon la typologie de dossier »
- associe / Client : tient le registre (supprimer : seulement si le brief le dit) — « du maximum négocié avec le client »
- associe / ForfaitFacturation : tient le registre (supprimer : seulement si le brief le dit) — « suivi des forfait de facturation avec un système d'alertes dès lors que le nombre d'heures déjà facturées s'approchent du maximum négocié avec le client »
- associe / Collaborateur : clôture : affiché dans les Dossiers juridiques qu'il voit ; clôture : choisit les Profils collaborateurs de ses Dossiers juridiques — « pour chaque dossier juridique, classement en fonction du niveau d'importance et d'urgence »
- manager / TypeDossier : préréglage catalogue : visible de tous les connectés — « selon la typologie de dossier »
- manager / Collaborateur : clôture : affiché dans les Dossiers juridiques qu'il voit ; clôture : choisit les Profils collaborateurs de ses Dossiers juridiques — « pour chaque dossier juridique, classement en fonction du niveau d'importance et d'urgence »
- manager / Client : clôture : affiché dans les Dossiers juridiques qu'il voit ; clôture : choisit les Clients de ses Dossiers juridiques — « pour chaque dossier juridique, classement en fonction du niveau d'importance et d'urgence »
- manager / Dossier : tient le registre (supprimer : seulement si le brief le dit) ; fait évoluer l'état des fiches du registre ; exception : « Assistance à la répartition des dossiers pour le manager » — « pour chaque dossier juridique, classement en fonction du niveau d'importance et d'urgence » « Assistance à la répartition des dossiers pour le manager en fonction des dossiers déjà attribués » « Assistance à la répartition des dossiers pour le manager »
- collaborateur / TypeDossier : préréglage catalogue : visible de tous les connectés — « selon la typologie de dossier »
- collaborateur / Tache : préréglage collection : le propriétaire crée et modifie les siens ; exception : « Interface permettant à tous les collaborateurs de rentrer en temps réel leurs tâches à effectuer » — « permettant à tous les collaborateurs de rentrer en temps réel leurs tâches à effectuer » « Interface permettant à tous les collaborateurs de rentrer en temps réel leurs tâches à effectuer »
- collaborateur / Collaborateur : préréglage profil : sa propre fiche, créée automatiquement — « des spécialités des collaborateurs, de leur ancienneté »
