# Médiathèque associative — ce que l'usine a compris

En bref : 3 rôles (Le gestionnaire de la médiathèque, L'adhérent, Le bibliothécaire), 3 sortes de fiches, 1 circuit d'étapes.

## Le visiteur (sans compte)
- Voit tout : ouvrages

## Le gestionnaire de la médiathèque (responsable de l'app)
- Voit tout, crée et modifie : ouvrages

## L'adhérent (invité par gestionnaire)
- Voit tout : ouvrages
- Voit seulement les siennes et crée : emprunts
- a son profil adhérent, créé automatiquement, qu'il peut modifier

## Le bibliothécaire (invité par gestionnaire)
- Voit tout : ouvrages
- voit les profils adhérents affichés dans les emprunts qu'il consulte (sans page à part)
- Emprunts : voit tout, les fait passer de « demandé » à « accepté » ou « refusé », les fait passer de « accepté » à « rendu »

## Les étapes

- L'emprunt commence « demandé » ; de « demandé », vers « accepté » ou « refusé » ; de « accepté », vers « rendu »
  - Le bibliothécaire fait passer de « demandé » à « accepté » ou « refusé »
  - Le bibliothécaire fait passer de « accepté » à « rendu »

## Les informations de chaque fiche

- **Ouvrage** : Titre (texte court) · Auteur (texte court) · Résumé (texte long) · Genre (choix parmi : roman, essai, bande dessinée, jeunesse) · Année de publication (nombre)
- **Profil adhérent** : Nom (texte court) · Email (e-mail) · Téléphone (téléphone)
- **Emprunt** : aucune information (seulement ses liens)
  - relié à : ouvrage, profil adhérent

## Questions

- Les visiteurs sans compte pourront consulter tous les ouvrages — d'accord ? (si certains ne doivent pas être visibles, par exemple des brouillons, répondez non)
- Le bibliothécaire verra les profils adhérents (ex. nom, coordonnées) affichés dans les emprunts qu'il traite — est-ce acceptable ? → **oui, nécessairement** : il doit les voir quand même — clôture : affiché dans les emprunts qu'il voit

## Pas encore dans notre stock (vos mots)

- Interface claire, chaleureuse et accessible — « L'interface doit être claire, chaleureuse et accessible. »

---

## Volet concepteur

### Pour répondre (`python -m usine.miroir repondre <lecture> id=valeur …`)

- `visiteur:visitor:Ouvrage` = oui | non
- `vu_via:bibliothecaire:ProfilAdherent` = oui

### Pourquoi chaque droit

- visitor / Ouvrage : catalogue public : visible des visiteurs ; exception : « Les visiteurs, sans se connecter, peuvent parcourir le catalogue public des ouvrages » — « le catalogue public des ouvrages : chaque ouvrage a un titre, un auteur, un résumé (texte long), un genre (roman, essai, bande dessinée, jeunesse) et une année de publication » « Les visiteurs, sans se connecter, peuvent parcourir le catalogue public des ouvrages »
- gestionnaire / Ouvrage : préréglage catalogue : visible de tous les connectés ; gestionnaire du catalogue (supprimer : seulement si le brief le dit) — « le catalogue public des ouvrages : chaque ouvrage a un titre, un auteur, un résumé (texte long), un genre (roman, essai, bande dessinée, jeunesse) et une année de publication »
- adherent / Ouvrage : préréglage catalogue : visible de tous les connectés — « le catalogue public des ouvrages : chaque ouvrage a un titre, un auteur, un résumé (texte long), un genre (roman, essai, bande dessinée, jeunesse) et une année de publication »
- adherent / Emprunt : préréglage collection + processus : l'initiateur crée et suit les siens ; exception : « un adhérent gère son profil (nom, email, téléphone) et demande à emprunter un ouvrage » ; exception : « Un adhérent ne voit que ses propres emprunts » — « un adhérent gère son profil (nom, email, téléphone) et demande à emprunter un ouvrage : un emprunt concerne un ouvrage, a une date de demande et un état » « un adhérent gère son profil (nom, email, téléphone) et demande à emprunter un ouvrage » « Un adhérent ne voit que ses propres emprunts »
- adherent / ProfilAdherent : préréglage profil : sa propre fiche, créée automatiquement ; exception : « un adhérent gère son profil » — « Après connexion, un adhérent gère son profil (nom, email, téléphone) » « un adhérent gère son profil »
- bibliothecaire / Ouvrage : préréglage catalogue : visible de tous les connectés — « le catalogue public des ouvrages : chaque ouvrage a un titre, un auteur, un résumé (texte long), un genre (roman, essai, bande dessinée, jeunesse) et une année de publication »
- bibliothecaire / ProfilAdherent : clôture : affiché dans les emprunts qu'il voit
- bibliothecaire / Emprunt : décideur du processus : voit tout et fait évoluer l'état ; exception : « voit tous les emprunts de tous les adhérents » ; exception : « Un emprunt commence en demandé, puis il est soit accepté » ; exception : « Un emprunt commence en demandé, puis il est soit accepté, soit refusé » ; exception : « un emprunt accepté passe ensuite à rendu » — « Le ou la bibliothécaire, en revanche, voit tous les emprunts de tous les adhérents et est la seule personne à pouvoir accepter, refuser ou marquer un emprunt comme rendu ; un adhérent ne fait que demander et suivre » « voit tous les emprunts de tous les adhérents » « Un emprunt commence en demandé, puis il est soit accepté » « Un emprunt commence en demandé, puis il est soit accepté, soit refusé » « un emprunt accepté passe ensuite à rendu »
