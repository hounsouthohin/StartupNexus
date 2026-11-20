# L'essai de la boîte : un atelier fermé pour l'agent tient-il sur ce PC ?

> **Taille** : moyen (essai jetable) · **Statut** : **fini : l'atelier tient** (14 nov ; redémarrage du PC vérifié le
> 16 nov)
> **Dates** : écrit le 14 nov 2026 · relu le 14 nov · révisé le 14 nov · seconde lecture le 14 nov · lancé le 14 nov

## Avant : la conception

### 1. En mots simples
- **Ce que c'est.** Un atelier fermé à clé, où l'agent IA travaille sur une app. Dans l'atelier, il trouve :
  - l'app ;
  - ses outils, déjà posés ;
  - une base de données jetable, pleine de données de démonstration.

  Il n'a **pas de câble réseau**, ne voit pas le reste du PC, et ne peut pas toucher aux pièces de sécurité de l'app
  (les données et les droits), vissées en lecture seule. Après chaque tâche, on jette l'atelier et on en prend un neuf.
  Techniquement, c'est un **conteneur Docker** (une sorte de mini-ordinateur Linux, créé en quelques secondes).
- **Pourquoi on le fait.** L'agent exécute des commandes. Sur le PC sans protection, une seule mauvaise commande,
  qu'elle vienne d'une erreur ou d'un texte piégé, pourrait :
  - effacer des fichiers ;
  - lire la clé de l'usine ;
  - installer une bibliothèque piégée ;
  - envoyer des données sur internet ;
  - modifier les droits d'une app.

  La règle de l'usine est « les consignes expliquent, la boîte impose » : la sécurité ne doit jamais reposer sur
  l'obéissance de l'IA.
- **Pourquoi une « machine virtuelle ».** Ces ateliers sont des mini-ordinateurs Linux ; Windows ne sait pas les faire
  tourner seul. **Docker Desktop**, déjà installé, fait tourner pour cela un petit Linux caché (WSL). C'est lui qui
  héberge déjà la base de l'usine. On s'en sert tel quel : rien de nouveau à installer.
- **Ce qu'on verra à la fin.** On saura si l'atelier se monte vite, s'il enferme vraiment l'agent, et si l'app s'y
  construit à une vitesse raisonnable. Si non, on prend un autre ordinateur (sous Linux, ou loué en ligne).

### 2. À quoi ça sert
L'atelier est le premier maillon de la chaîne complète (le squelette de bout en bout). Si l'atelier ne tient pas sur ce
PC, toute la suite change.

### 3. Ce qui existe déjà
- **Docker Desktop** (moteur 28.3), qui fait tourner la base PostgreSQL de l'usine (conteneur `temporal-postgresql`).
  Il ne redémarrait pas tout seul : **son démarrage automatique est désactivé** (`AutoStart : false` dans ses
  réglages, vu le 14 nov). C'est la seule cause du piège « Docker s'arrête à chaque redémarrage ».
- Une ancienne distribution Linux (Ubuntu 20.04, avec un vieux Docker), à laquelle **on ne touche pas**.
- La machine : Intel i7 à 4 cœurs, 16 Go de mémoire, 117 Go libres. Le Linux caché voit 7,6 Go de mémoire.
- Le squelette des apps (`usine/modele-app/`, Next.js 16.4.6) : il n'utilise **aucune police téléchargée** sur
  internet (vérifié le 14 nov). Sa construction ne demande donc pas de réseau. Sous Windows, construire la médiathèque
  prend environ 31 s.

### 4. Comment on la construit
**Le moteur : Docker Desktop, tel qu'il est**, avec deux réglages :
- « démarrer Docker Desktop à l'ouverture de session » (une case dans ses réglages) ;
- la base de l'usine redémarre seule (`docker update --restart unless-stopped temporal-postgresql`).

*Écarté pour l'instant* : installer une distribution Linux dédiée avec son propre Docker. C'était la première version
de ce dossier, pour régler le redémarrage ; une case à cocher le règle. On la garde **en repli**, si Docker Desktop se
montre trop lent ou instable.

**L'image figée** (le « modèle » de l'atelier, construit une fois par version du squelette) :
- Node 22, et les bibliothèques exactes du squelette, installées dans `/work/node_modules`, en lecture seule ;
- les moteurs de Prisma, téléchargés **une fois, à la construction de l'image**. Ça supprime au passage la panne
  connue « Prisma télécharge son moteur à chaque fabrication » ;
- Chromium, pour essayer l'app ;
- **PostgreSQL**, avec les données de démonstration déjà chargées ;
- le contrôle des failles des bibliothèques, fait à la construction de l'image : l'atelier, lui, n'a pas de réseau.

**L'atelier** (un conteneur par tâche, jeté après) :

| Ce qu'on règle | Comment (réglage Docker) | Pourquoi |
|---|---|---|
| **Pas de réseau du tout** | `--network none` | il ne peut ni joindre internet, ni le PC, ni la base de l'usine. L'app et sa base se parlent à l'intérieur de l'atelier, sans réseau |
| Sa base de données | PostgreSQL **dans l'atelier**. Ses données sont **déjà initialisées dans l'image**, au nom de l'utilisateur `postgres` (999), puis copiées au démarrage sur un disque en mémoire (`tmpfs`) | une base à lui, jetée avec l'atelier ; sans réseau, aucune autre base n'est joignable. Initialiser au démarrage échouerait sans privilèges |
| Qui parle à la base | PostgreSQL tourne en utilisateur 999 ; les commandes envoyées de l'extérieur tournent en utilisateur 1000 (`docker exec -u 1000`) ; l'app se connecte avec un rôle de base **sans privilèges d'administration**, protégé par un mot de passe | l'agent ne peut pas devenir administrateur de sa base par un raccourci |
| **Toute l'app** | montée en **lecture seule** | l'artisan modifie les fichiers depuis Windows, avec ses propres outils : l'atelier, lui, n'a besoin d'écrire **aucun** fichier de l'app. Un programme de l'atelier ne peut donc ni remplir le disque du PC, ni déposer un lien piégé |
| Ce que la construction écrit (`.next/`, `test-results/`) | sur un disque en mémoire de **taille limitée** | la construction peut écrire, sans toucher au disque du PC |
| Le reste du système | `--read-only` ; `HOME`, les caches de npm, de Next.js et de Playwright, et `/tmp` sur un disque en mémoire | rien ne survit à l'atelier ; les outils peuvent quand même écrire leurs fichiers temporaires |
| Qui il est | un utilisateur ordinaire (`--user 1000:1000`), aucun privilège (`--cap-drop ALL`, `--security-opt no-new-privileges`) | il ne peut pas devenir administrateur |
| Le moteur Docker | son « socket » n'est **jamais** monté dans l'atelier | sinon, l'atelier pourrait commander tout Docker, donc en sortir |
| Ses limites | `--memory` (fixée d'après la mesure du témoin « construire », plus une marge), `--cpus`, `--pids-limit` | une boucle folle ne fige pas le PC. Les disques en mémoire comptent sans doute dans ce plafond : on le vérifie |
| Docker Desktop | sa version est **figée** pendant les essais (téléchargement automatique des mises à jour coupé) | une mise à jour en cours d'essai fausserait les mesures |
| Chromium | `--shm-size` suffisante (pas `--ipc=host`), et `--init` | Chromium a besoin de mémoire partagée ; `--ipc=host` affaiblirait l'isolement ; `--init` évite les processus fantômes |
| Le bruit | `NEXT_TELEMETRY_DISABLED=1` | Next.js n'essaie pas d'envoyer de statistiques |
| Les secrets | aucun : rien n'est monté hors de l'app | il n'y a rien à voler |

L'agent (voir l'essai de l'agent constructeur) n'entre jamais lui-même dans l'atelier : il y envoie ses commandes de
l'extérieur (`docker exec`). C'est pour cela que l'atelier n'a besoin d'aucun réseau.

**Une règle qui en découle** : les juges tournent **toujours dans un atelier neuf**, jamais dans celui de l'artisan.
Dans son atelier, l'artisan peut modifier sa base de démonstration ; ce n'est pas grave tant qu'aucun juge ne s'en
sert.

### 5. Les pièges et leurs parades
- **Un témoin qui échoue pour une mauvaise raison** : un outil qui veut écrire dans son cache, une police à
  télécharger. Parade : les **témoins passent d'abord** ; on ne lance les sabotages qu'ensuite. Les polices sont
  vérifiées (aucune), et les caches sont sur un disque en mémoire.
- **Mesurer la base trop tôt** : un PostgreSQL qui démarre n'accepte pas tout de suite les connexions. Parade : on
  chronomètre jusqu'à ce que `pg_isready` réponde.
- **Le Linux caché partagé** (7,6 Go) entre Docker Desktop, la base de l'usine et l'atelier. Parade : on mesure ; on ne
  touche au réglage de mémoire que si c'est nécessaire.
- **Des fichiers lents** : l'app est sur `C:\`, Docker la lit à travers Windows. Parade : les bibliothèques sont dans
  l'image (ce qui pèse), seule l'app est montée (elle est petite). On mesure le temps de construction.
- **Des ateliers qui ne meurent pas** : un nom et une étiquette par tâche, et un comptage des restes à la fin.
- **Le disque virtuel de Docker grossit** et ne rétrécit pas seul : on note sa taille avant et après.

### 6. Comment on prouve qu'elle marche (écrit avant)
**Les témoins d'abord** : un atelier neuf doit pouvoir faire tout ce qui est permis.
1. Écrire dans ses zones en mémoire (`.next/`, `/tmp`).
2. Compiler et construire la médiathèque (on note aussi le pic de mémoire).
3. Démarrer sa base, et y lire les données de démonstration.
4. Lancer l'app et l'ouvrir dans Chromium, dans l'atelier.

**Les mesures** :

| Mesure | Seuil |
|---|---|
| Après un redémarrage du PC, Docker et la base de l'usine reviennent seuls | oui, sans rien faire |
| L'image se construit ; reconstruite sans changement | taille notée ; reconstruction < 1 min |
| 20 cycles : monter l'atelier jusqu'à ce que sa base réponde, compiler la médiathèque, tout jeter | **20/20** sans erreur ; monter + jeter < 15 s (médiane) ; aucun reste à la fin |
| Construire la médiathèque dans l'atelier | ≤ 2× le temps sous Windows (≤ 62 s) |
| Docker Desktop, la base de l'usine et l'atelier en même temps | aucun conflit ; mémoire totale notée |
| Taille du disque virtuel de Docker | notée avant et après |

**Ce que l'atelier doit refuser** : 11 sabotages, lancés de l'intérieur ; chacun doit **échouer**.
1. Écrire dans un fichier de l'app, et en particulier dans les pièces de sécurité (le schéma des droits).
2. Installer une bibliothèque (`npm install`).
3. Joindre internet.
4. Joindre le PC ou la machine virtuelle : la base de l'usine, Windows, et toute adresse de l'hôte. On essaie les ports
   courants de l'adresse de l'hôte (`host.docker.internal`) et de la passerelle.
5. **Résoudre un nom** sur internet (`registry.npmjs.org`) : c'est une voie de fuite classique, par le DNS.
6. **Joindre le moteur Docker** (`/var/run/docker.sock`).
7. Devenir administrateur, ou écrire hors des zones permises (`/`, `/etc`).
8. Lire un secret : un `.env` à clé, la boîte aux lettres, le dossier personnel.
9. Une explosion de processus : l'atelier est stoppé, le PC reste utilisable.
10. Un programme qui dévore la mémoire : l'atelier est tué, le PC reste utilisable.
11. Écrire un fichier de 20 Go : l'écriture échoue, et l'espace libre du disque du PC ne bouge pas.

S'y ajoute une vérification simple : à l'intérieur, la liste des cartes réseau (`ip link`) ne montre que la boucle
locale (`lo`).

**Le critère d'arrêt**, avec la décision écrite d'avance :
- un sabotage qui réussit, et qu'aucun réglage ne referme → l'atelier n'est pas sûr ici. On essaie d'abord le repli
  (une distribution Linux dédiée, avec un pare-feu qui coupe l'hôte) ; s'il échoue aussi → un autre ordinateur ;
- plus d'un cycle raté sur 20, ou une construction plus de 3 fois plus lente → le repli ;
- le PC figé par un sabotage → le repli.

### 7. Le périmètre
- **Touché** :
  - deux réglages de Docker Desktop : le démarrage automatique, et le redémarrage de la base de l'usine ;
  - un dossier d'essai jetable, `C:\Users\BAMBARA Arthur\essais\boite\` (le modèle de l'atelier, les scripts, les
    mesures) ;
  - une image Docker, effaçable.
- **Pas touché** : le dépôt `StartupNexus` (sauf ce dossier), les données de la base de l'usine, l'ancienne Ubuntu,
  `lecteur-isole`.
- **Taille max** : 2 jours. **Risque** : faible ; tout s'efface (l'image, les ateliers), et les deux réglages se
  décochent.

### 8. Questions pour le relecteur (seconde lecture)
1. Remplacer « une distribution Linux dédiée + base sur un réseau interne » par « Docker Desktop + **aucun réseau**,
   base dans l'atelier » : est-ce plus sûr, et aussi solide ?
2. PostgreSQL dans l'atelier, en utilisateur ordinaire, avec ses données en mémoire : un piège ?
3. Avec Docker Desktop, que joint encore un conteneur sans réseau (`--network none`) ? Le sabotage n° 4 suffit-il ?

## Relecture

**Relecteur** : Claude en ligne, le 14 nov 2026 · **Verdict** : OK AVEC CORRECTIONS (aucun point bloquant)
(texte complet : `archives/echanges-2026-11/relecture-des-trois-essais-2026-11-14.md`)

| Point du relecteur | Réponse |
|---|---|
| Le réseau interne laisse joindre l'hôte (passerelle, machine virtuelle) | **Accepté, et réglé plus simplement** : l'atelier n'a plus **aucun** réseau, et la base est dedans. Le sabotage n° 4 essaie quand même toutes les adresses de l'hôte |
| La fuite par le DNS | **Accepté** : sabotage n° 5. Sans réseau, il n'y a plus de DNS du tout |
| Le socket de Docker | **Accepté** : sabotage n° 6 |
| Chromium et la mémoire partagée ; `--init` | **Accepté** : `--shm-size` et `--init`, pas `--ipc=host` |
| Une construction qui échoue faute de réseau (polices) | **Vérifié** : le squelette et l'app de l'agent n'utilisent aucune police téléchargée. La télémétrie est coupée quand même |
| Le système de fichiers en lecture seule casse des écritures invisibles | **Accepté** : `HOME` et les caches sur un disque en mémoire ; les témoins passent avant les sabotages |
| Mesurer la base jusqu'à `pg_isready` | **Accepté** (le seuil passe de 10 à 15 s, puisqu'il inclut maintenant l'attente de la base) |
| Suggestion : une image avec les données de démonstration déjà chargées | **Accepté** |
| Suggestion : noter la taille du disque virtuel | **Accepté** |
| Sans root, remappage des utilisateurs : pas nécessaire maintenant | **D'accord** |

**Changement de ma part, après la relecture** : on garde Docker Desktop au lieu d'installer une distribution Linux
dédiée. La raison qui la justifiait (Docker ne redémarre pas seul) n'était qu'un réglage désactivé. Moins de pièces,
c'est moins de pannes, et c'est plus facile à comprendre. La distribution dédiée devient le repli.

**Seconde lecture** (Claude en ligne, le 14 nov) · **Verdict** : OK AVEC CORRECTIONS (aucun point bloquant) ;
« Docker Desktop sans réseau est plus sûr et plus simple ».

| Point du relecteur | Réponse |
|---|---|
| Les zones en écriture sont sur le disque de Windows | **Accepté** : toute l'app en lecture seule ; `.next/` et `test-results/` sur un disque en mémoire de taille limitée ; sabotage n° 11 (20 Go) |
| PostgreSQL ne démarre pas tel quel avec un autre utilisateur et sans privilèges | **Accepté** : données initialisées dans l'image (utilisateur 999), copiées en mémoire au démarrage |
| Dans l'atelier, toute commande est administrateur de la base | **Accepté** : les juges tournent toujours dans un atelier neuf ; PostgreSQL en 999, commandes en 1000, rôle de l'app sans privilèges, avec mot de passe |
| Le disque en mémoire compte dans le plafond de mémoire | **Accepté** : plafond fixé d'après la mesure, pic noté, comptage vérifié |
| Suggestion : `ip link` ne montre que `lo` | **Accepté** |
| Suggestion : figer la version de Docker Desktop | **Accepté** |

**Décision d'Arthur** : « go », le 14 nov (« si tu juges bon, on peut commencer »).

## Après : le compte rendu (14 nov 2026)

### 9. Ce qui a été fait
- Docker Desktop : démarrage automatique **activé**, téléchargement des mises à jour **coupé** (version 4.45 figée).
  L'ancien fichier de réglages est gardé : `%APPDATA%\Docker\settings-store.json.avant-essai-boite`. La base de
  l'usine redémarre seule (`unless-stopped`).
- Le dossier d'essai `C:\Users\BAMBARA Arthur\essais\boite\` :
  - `Dockerfile` : le modèle de l'atelier (Node 22, les bibliothèques exactes du squelette, Chromium, PostgreSQL 15
    initialisé au nom de 999, contrôle des failles à la construction) ;
  - `Dockerfile.mediatheque` : la couche propre à l'app, avec ses tables et ses 4 fiches de départ, chargées à la
    construction. Prisma ne télécharge son moteur qu'ici ;
  - `demarrage.sh` : le démarrage de la base dans l'atelier ;
  - `essai.py` : les mesures, les témoins et les sabotages ;
  - `resultats.json` : les résultats ;
  - une copie de la médiathèque, sans aucun `.env`.

### 10. Les écarts avec la conception
- **Le typage** (`tsc`) voulait écrire un petit fichier de travail dans l'app, qui est en lecture seule. C'est
  l'« écriture invisible » annoncée par le relecteur. Corrigé par une option (`--incremental false`), qui fera partie
  de la commande `atelier verifier`.
- **Deux de mes sabotages étaient mal écrits** (mon erreur, corrigée avant de conclure) :
  - « lire un secret » s'est déclenché sur un faux signal : `ls` de deux dossiers affiche leurs noms même s'ils sont
    vides ;
  - « explosion de processus » était compté comme refusé pour une mauvaise raison : l'outil `ps` est absent de
    l'image.
  Les deux sont refaits proprement : chaque vérification dit ce qu'elle trouve, et les processus sont comptés depuis
  l'extérieur. Un sabotage ne compte que s'il est refusé **pour la bonne raison**.
- **La comparaison « fichiers dans Linux contre fichiers sur `C:\` »** n'a plus d'objet : avec Docker Desktop, l'app est
  lue depuis `C:\`, et la construction reste sous le seuil.
- Un avertissement de Next.js, sans effet : deux fichiers de verrouillage, celui de l'image et celui de l'app. À
  régler dans le squelette (`turbopack.root`) au moment de la chaîne complète.

### 11. Les résultats des preuves (contre les seuils écrits d'avance)

> **Correction du 19 nov, après la vérification de Codex en lecture**
> ([fil](../dialogue/2026-11-19-verification-essai-boite.md)).
> - **Ce qui tient** : les cycles, la construction et les témoins concordent avec les fichiers bruts.
> - **Ce qui ne tient pas** :
>   - « chacun pour la bonne raison » est trop fort. Le script compte toute erreur comme un refus (`essai.py`, ligne
>     209), et le test des processus revu accepte tout maximum compris entre 1 et 512 ;
>   - le réseau n'a été essayé que sur les adresses listées ;
>   - les résultats mêlent une passe d'origine et deux sabotages refaits, sans empreinte.
> - **Bilan** (la formulation de Codex) : **onze indicateurs d'échec sont enregistrés ; ils ne démontrent pas tous un
>   refus effectif par la protection, ni sa raison.** Rien ne prouve une seule version. Les chiffres de faisabilité
>   concordent avec les fichiers historiques. Décision d'Arthur : l'atelier sera qualifié dans la chaîne complète.

| Mesure | Seuil | Résultat |
|---|---|---|
| Témoins : écrire en mémoire, compiler, construire, base et données, app dans Chromium | tous | ✔ **4/4**, plus « seulement la boucle locale » comme carte réseau |
| Construire la médiathèque dans l'atelier | ≤ 62 s | ✔ **35 s** (44 s au premier passage), contre 31 s sous Windows ; pic de mémoire **1,3 Go** |
| 20 cycles monter, compiler, jeter | 20/20 ; médiane < 15 s ; aucun reste | ✔ **20/20** ; monter + jeter : **0,9 s** en médiane (base prête comprise) ; **0 reste** |
| L'image ; reconstruite sans changement | taille notée ; < 1 min | base : 3,3 Go en 4 min 51 ; couche médiathèque : 29 s ; ✔ reconstruction **1 s** |
| Docker Desktop, la base de l'usine et l'atelier ensemble | aucun conflit | ✔ aucun conflit ; machine virtuelle à 3,6 Go de mémoire |
| Disque virtuel de Docker | noté | 11,1 Go après l'essai, stable entre le début et la fin des mesures (la taille d'avant les images n'a pas été relevée) |
| **Sabotages** | 11/11 refusés | ✔ **11/11 refusés, chacun pour la bonne raison** (détail ci-dessous) |
| Après un redémarrage du PC, Docker et la base reviennent seuls | oui | ✔ **vérifié le 16 nov** : session ouverte à 10 h 25, Docker Desktop démarré seul à 10 h 26, base de l'usine en marche sans rien faire |

Les sabotages, un par un :
1. Écrire dans l'app : « système de fichiers en lecture seule ».
2. Installer une bibliothèque : le registre npm est injoignable.
3. Joindre internet : échec.
4. Joindre le PC : 6 adresses × 8 ports, dont la base de l'usine ; aucune joignable.
5. Résoudre un nom : aucun serveur de noms.
6. Le moteur Docker : son « socket » est absent.
7. Devenir administrateur : refusé, et `/etc` en lecture seule.
8. Lire un secret : rien trouvé. Pas de `.env`, aucun dossier du PC, aucune clé, les réglages de la base illisibles.
   Le seul montage est l'app, en lecture seule.
9. Explosion de processus : plafonnée à **511/512** ; Docker a répondu tout du long.
10. Dévorer la mémoire : le programme est tué par le système (`OOM`) ; le PC n'est pas touché.
11. Écrire 20 Go : arrêté à **256 Mo**, la taille du disque en mémoire ; le disque du PC n'a pas bougé.

Pour rejouer : dans `C:\Users\BAMBARA Arthur\essais\boite\`, lancer
`python essai.py temoins`, puis `cycles`, `sabotages` et `sabotages-revus`.

### 12. Comment ça marche, et comment c'est fait (en mots simples)
- **Le moule et l'atelier.** Docker fabrique des mini-ordinateurs Linux jetables. On écrit d'abord une **recette**
  (`Dockerfile`) : partir d'un Linux avec Node, y installer PostgreSQL, les bibliothèques exactes du squelette et
  Chromium. Docker en tire un **moule** (l'image), construit une fois. Chaque atelier est un **tirage** du moule : il
  sort en une seconde, et on le jette après usage.
- **Deux étages de moule** : un moule commun à toutes les apps, et un petit étage par app, avec ses tables et ses
  données de démonstration déjà chargées. C'est pour cela que l'atelier démarre en une seconde, base prête.
- **Les verrous** : ce sont des options de Docker au moment de sortir l'atelier :
  - pas de carte réseau ;
  - l'app vue en lecture seule ;
  - un utilisateur ordinaire, sans privilège ;
  - des plafonds de mémoire et de processus ;
  - des disques en mémoire, petits et effacés à la fin.
- **La mesure** : un petit programme Python (`essai.py`) joue le rôle du testeur. Il sort des ateliers, y envoie des
  commandes de l'extérieur (`docker exec`), chronomètre, puis tente les 11 évasions et note pour chacune la raison du
  refus. Tout est écrit dans `resultats.json`.

### 13. Ce qu'Arthur peut voir lui-même
- **Au prochain redémarrage du PC** : sans rien faire, Docker Desktop démarre, et la commande `docker ps` montre
  `temporal-postgresql` en marche. C'est le dernier point de l'essai.
- `resultats.json`, dans le dossier d'essai : chaque mesure, chaque sabotage et sa raison.

### 14. Ce que ça change pour la suite
- **L'essai du juge d'écrans, révisé** : il tournera **dans un atelier**, et non sur le PC. L'atelier sait déjà faire
  tout ce qu'il faut : l'app, sa base et Chromium y sont, sans réseau. C'est la règle « les juges tournent dans un
  atelier neuf » appliquée dès l'essai, et la base de l'usine n'est plus touchée. Il faudra un étage de moule par app
  essayée (l'app mixte, l'app de l'agent, l'app du brief seul).
- **L'essai de l'agent constructeur** : il lui faut l'étage de moule de l'app de l'agent (ses tables et ses données) et
  les quatre commandes `atelier …`, dont le typage avec la bonne option.
- **Relecture extérieure** : pas nécessaire pour ce compte rendu. Les mesures sont nettes, et les deux tests que j'ai
  corrigés sont décrits. La relecture utile sera celle des **réglages de la session de l'artisan**, avant qu'Arthur
  ne l'ouvre : c'est là que se joue la sécurité de l'essai suivant.
- **Inconnue n° 1 fermée** : l'atelier fermé tient sur ce PC, sans réseau, rapide, sans conflit. La distribution Linux
  dédiée n'est pas nécessaire.
- Non vérifié : que les disques en mémoire comptent bien dans le plafond de mémoire. Ce n'est pas bloquant : le
  disque en mémoire le plus gros est plafonné à 1 Go.
- Pour la chaîne complète :
  - la commande `atelier verifier` porte l'option du typage ;
  - régler `turbopack.root` dans le squelette ;
  - la couche « app » de l'image se construit à chaque version de l'app.
- **Suite** : l'essai de l'agent constructeur peut utiliser cet atelier.
- **Conteneur** : un mini-ordinateur Linux créé en quelques secondes, à partir d'une image, et jeté après usage.
- **Image** : le modèle figé d'un conteneur (le système et les outils déjà installés).
- **WSL** : le Linux caché que Windows fait tourner, et dans lequel Docker Desktop fait vivre ses conteneurs.
- **Socket Docker** : la « télécommande » du moteur Docker ; qui la tient commande tous les conteneurs.
- **DNS** : l'annuaire qui traduit un nom (`registry.npmjs.org`) en adresse ; il peut servir à faire sortir des données.
- **`tmpfs`** : un disque en mémoire, effacé quand l'atelier s'arrête.
