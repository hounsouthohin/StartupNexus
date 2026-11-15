# Seconde lecture des trois essais

## Essai de la boîte (l'atelier)

**VERDICT : OK AVEC CORRECTIONS**

**Question 1 : Docker Desktop sans réseau, plutôt qu'une distribution dédiée avec réseau interne ?** Oui, c'est plus sûr : sans réseau, il n'y a plus de passerelle vers l'hôte, ni de DNS. C'est aussi plus simple. Deux réserves, traitées plus bas : les fichiers partagés avec Windows deviennent le principal canal restant, et la base dans l'atelier demande quelques réglages précis.

**BLOQUANT**

Aucun.

**À CORRIGER**

1. **Les zones en écriture sont sur le disque de Windows.** `sur-mesure/`, `.next/` et `test-results/` sont montés depuis `C:\`. Un programme qui écrit un fichier énorme remplit le disque du PC : `--memory` ne limite pas ça. Or, dans l'essai de l'agent constructeur, l'artisan modifie les fichiers **depuis Windows**, avec ses propres outils, et pas depuis l'atelier. L'atelier n'a donc besoin d'écrire **aucun** fichier de l'app. **Correction :** monter toute l'app en lecture seule, et mettre `.next/` et `test-results/` sur un disque en mémoire de taille limitée. Ajouter un sabotage : « écrire un fichier de 20 Go » doit échouer, et le disque du PC ne doit pas bouger. Ça supprime aussi le risque des liens symboliques déposés dans une zone partagée.

2. **PostgreSQL ne démarre pas tel quel avec `--user 1000:1000`.** Selon la documentation de l'image officielle, PostgreSQL accepte n'importe quel identifiant d'utilisateur tant que le propriétaire du dossier de données correspond, mais `initdb` exige que l'utilisateur existe dans `/etc/passwd`. Avec `--cap-drop ALL`, l'image ne peut pas non plus corriger les propriétaires au démarrage : un exemple montre l'échec de `chmod` sur le dossier de données. **Correction :** construire l'image avec les données déjà initialisées, appartenant à l'utilisateur `postgres` de l'image (999). Au démarrage, copier ces données dans le disque en mémoire. Le témoin n° 3 le confirmera. Source : [image officielle PostgreSQL](https://hub.docker.com/_/postgres).

3. **Dans l'atelier, toute commande est administrateur de la base.** L'image officielle autorise les connexions locales **sans mot de passe** depuis l'intérieur du même conteneur. L'agent peut donc modifier le schéma ou les données de démonstration de sa base. Ce n'est pas grave en soi, à une condition : les juges ne réutilisent **jamais** la base de l'agent. **Correction :** écrire dans le dossier que les juges tournent toujours dans un atelier **neuf**. En défense supplémentaire : faire tourner PostgreSQL sous l'utilisateur 999, les commandes de l'agent sous 1000 (`docker exec -u 1000`), et donner à l'app un rôle de base sans privilèges d'administration, avec mot de passe.

4. **Le disque en mémoire compte dans la mémoire de l'atelier.** Les données de la base, `.next/`, la construction de Next.js et Chromium partagent le même plafond `--memory`, dans une machine virtuelle de 7,6 Go déjà partagée avec la base de l'usine. **Correction :** fixer `--memory` d'après une mesure du témoin n° 2 (construire), plus une marge, et noter le pic de mémoire. Le fait que le disque en mémoire compte dans ce plafond reste à vérifier sur ce poste.

**SUGGESTIONS**

1. **Question 2 (PostgreSQL dans l'atelier, données en mémoire).** Les pièges sont ceux des points 2 à 4 ci-dessus. Un de plus : sans `--init`, PostgreSQL et l'app lancés par un script de démarrage ne sont pas surveillés. Le script doit attendre `pg_isready` avant de rendre la main ; c'est déjà prévu pour la mesure.
2. **Question 3 (que joint un conteneur sans réseau ?).** Rien par le réseau : il ne reste que l'interface locale. Les canaux restants sont les fichiers montés (point 1), le noyau partagé de la machine virtuelle, et les commandes envoyées de l'extérieur par `docker exec`. Le sabotage n° 4 suffit pour le réseau ; ajouter une vérification simple : `ip link` ne montre que `lo`.
3. **Figer la version de Docker Desktop** (désactiver ses mises à jour automatiques pendant les essais), pour que ses changements ne faussent pas les mesures.

**NON VÉRIFIÉ**

- Que le disque en mémoire compte dans le plafond `--memory` sous Docker Desktop.
- La lenteur des montages depuis `C:\` avec Docker Desktop ; la mesure du dossier le dira.

## Essai de l'agent constructeur

**VERDICT : OK AVEC CORRECTIONS** (après le point bloquant)

**Question 1 : est-ce l'« usage ordinaire » ?** Oui. La page officielle dit que l'authentification par abonnement est conçue pour l'usage ordinaire de Claude Code et des autres applications natives d'Anthropic. Arthur qui ouvre une session pour coder une tâche de son propre projet, c'en est l'exemple même. Les citations du dossier sont exactes : les limites annoncées supposent un usage ordinaire et individuel de Claude Code et de l'Agent SDK, et Anthropic interdit de faire passer des requêtes par ces identifiants pour le compte d'autres utilisateurs. Je ne parle pas au nom d'Anthropic ; c'est une lecture de la page publique.

**Question 2 : une session « facteur » qui lance un artisan neuf par tâche ?** La documentation officielle prévoit l'automatisation de Claude Code avec un abonnement : un jeton longue durée, créé par `claude setup-token`, pour les chaînes d'intégration continue et les scripts sans connexion par navigateur. Lancer le programme officiel `claude` pour ses propres tâches reste donc de l'usage de Claude Code. La limite est le volume : « usage ordinaire et individuel ». Pour développer et tester l'usine à petit volume, l'abonnement convient. Dès que la chaîne tourne régulièrement, ou travaille pour de vrais clients, l'API s'impose. C'est aussi la règle de confidentialité déjà retenue.

**BLOQUANT**

1. **La règle « `docker exec boite-agent …` » laisse passer ce que le terminal de Windows fait autour de la commande.** Une redirection (`docker exec boite-agent cat x > fichier`) s'exécute **sur le PC**, pas dans l'atelier ; elle peut écrire hors de la zone de travail, y compris dans le cœur de la copie sur le disque. La règle repose sur la reconnaissance de la commande par Claude Code. La documentation le dit : les règles sont appliquées par Claude Code, pas par le modèle, et le dossier rappelle qu'elles ne sont pas une frontière de sécurité.
   - **Pourquoi c'est grave :** c'est précisément ce que l'atelier devait rendre impossible, et le principe « rien ne dépend de son obéissance » ne tiendrait plus.
   - **Correction :** remplacer la règle générale par des règles **exactes** sur trois ou quatre scripts sans argument (`atelier verifier`, `atelier construire`, `atelier demarrer`, éventuellement `atelier journal`). Ce sont les scripts qui appellent `docker exec -u 1000 boite-agent …`, avec des options figées. La documentation prévoit ce cas : pour autoriser une invocation précise, écrire une règle exacte pour la commande complète. Pour lire le code, l'artisan a déjà ses outils de lecture et de recherche ; il n'a pas besoin d'un terminal libre.
   - **Source :** [permissions de Claude Code](https://code.claude.com/docs/en/permissions).

**À CORRIGER**

1. **Le mode `dontAsk` doit être forcé, pas supposé.** Selon un article récent (non officiel), le mode automatique est devenu le mode de départ des sessions interactives, et en mode `dontAsk` les chemins protégés (dont `.claude`) sont refusés. **Correction :** fixer `"defaultMode": "dontAsk"` dans les réglages du dossier, et, au début de la session, enregistrer la sortie de `/permissions` : la documentation indique que cette vue liste toutes les règles et le fichier de réglages d'où vient chacune. Ça montre aussi si des règles ou des serveurs MCP des réglages personnels d'Arthur s'ajoutent à ceux du dossier.

2. **L'atelier ne protège pas les fichiers du cœur sur le disque.** L'artisan modifie les fichiers depuis Windows ; la lecture seule de l'atelier ne protège que l'intérieur du conteneur. Si une règle de modification laissait passer un fichier du cœur, l'atelier monterait le fichier **modifié**. **Correction :** calculer l'empreinte de chaque fichier du cœur avant et après la tâche, comme le fait déjà `juger.ps1`. C'est la vraie garde ; la liste des fichiers changés ne suffit pas si elle est tirée de ce que l'artisan déclare.

3. **Les commandes en lecture seule intégrées.** La documentation indique que Claude Code reconnaît un ensemble de commandes en lecture seule et les lance sans demande de permission, dans tous les modes. Si elles s'exécutent sur le PC, l'artisan pourrait lire des fichiers hors du dossier ; ils partiraient alors dans sa conversation, donc chez Anthropic. **Correction :** vérifier pendant l'essai à vide si une commande comme la lecture d'un fichier du dossier personnel est refusée ; sinon, ajouter des règles de refus explicites. Retirer aussi tout `.env` de la copie de l'app.

4. **Le test caché s'exécute dans un atelier neuf**, à partir des fichiers finaux, avec une base neuve. Jamais dans l'atelier de l'artisan (voir l'essai de la boîte, point 3).

5. **Question 4 : la tâche est ambiguë sur le nombre.** « Le nombre de fiches affichées » : avant ou après la recherche ? Le test n° 1 compare au total permis, sans recherche. L'artisan peut raisonnablement compter après filtrage. **Correction :** préciser dans `TACHE.md` que le nombre suit le filtre, et ajouter au test : après avoir tapé le nom d'une fiche, le texte affiché est « 1 fiche(s) ». Ajouter aussi un rôle qui ne voit aucune fiche d'une liste : « 0 fiche(s) ».

**SUGGESTIONS**

1. Le critère « plus d'un quart de la fenêtre d'usage » est bon. Noter aussi la durée de la fenêtre, pour pouvoir comparer d'un essai à l'autre.
2. L'option « hors de l'atelier » est précieuse : c'est le seul moyen de savoir ce que l'atelier coûte en qualité.

**NON VÉRIFIÉ**

- Comment Claude Code traite exactement une redirection ou une substitution dans une commande autorisée par une règle générale. Un problème signalé montre qu'en mode `dontAsk` certaines formes (les variables) sont refusées, mais je n'ai pas trouvé de règle complète. C'est justement pourquoi je recommande des règles exactes.
- Que les commandes en lecture seule intégrées respectent ou non les règles de lecture.
- La position d'Anthropic sur un volume précis d'usage.

## Essai du juge d'écrans

**VERDICT : OK AVEC CORRECTIONS** (après le point bloquant)

Les corrections de la première lecture sont bien reprises. Il reste un trou, né de l'une d'elles.

**BLOQUANT**

1. **Le rejeu de la requête n'est jamais prouvé.** Le rejeu est le seul moyen de juger une interdiction quand le bouton est caché. Mais aucun sabotage ne le met à l'épreuve : le n° 2 montre le bouton (on clique simplement), et le n° 3 attend un échec du rejeu. Un rejeu qui échoue pour une raison technique ressemblerait exactement à une interdiction respectée. Or Next.js compare l'en-tête `Origin` à l'hôte, et interrompt la requête s'ils ne correspondent pas. Un rejeu mal formé échouerait donc toujours, en silence.
   - **Correction :**
     - un **témoin de rejeu** : la requête du jumeau permis, rejouée avec la session de la **même** personne permise, sur une base remise à zéro, doit réussir ;
     - un **sabotage n° 6** : le bouton est caché au membre de l'équipe, et la règle du serveur est assouplie. Le rejeu doit réussir, et l'inspecteur doit dire **interdiction violée** ;
     - garder l'en-tête `Origin` lors du rejeu, et des identifiants de fiches **fixes** dans les données de départ : la requête désigne la fiche par son identifiant.
   - **Source :** [guide des Server Actions (non officiel)](https://www.digitalapplied.com/blog/nextjs-server-actions-production-patterns-2026-guide) ; [Next.js](https://nextjs.org/docs/app/guides/server-actions).

**À CORRIGER**

1. **« Une fois la page stable » doit être défini.** Attendre la fin de toute activité réseau est déconseillé par Playwright au profit des assertions qui attendent un élément précis. **Correction :** la page est stable quand le repère attendu du chemin (par exemple le titre de la liste) est visible ; ensuite seulement, on compte les éléments.

2. **Un navigateur neuf par parcours.** Sinon, le cache de navigation de Next.js côté navigateur peut montrer des données d'avant la remise à zéro, et produire un faux « comportement faux ».

3. **Les caches du serveur après la remise à zéro.** Si un écran d'agent met des données en cache côté serveur, il montrera d'anciennes données après la remise à zéro. **Correction :** relever, avant l'essai, si les apps utilisent des directives de cache ; si oui, classer ces échecs à part, sans les compter comme des défauts de l'app.

4. **La règle de connexion « contient l'identifiant ».** Avec `gerant_1` et `gerant_2`, ça marche ; mais `gerant_1` est aussi contenu dans `gerant_10`. Utiliser une correspondance exacte, comme pour les boutons.

**SUGGESTIONS**

1. La remise à zéro dans la même base est le bon choix. Utiliser `TRUNCATE … RESTART IDENTITY CASCADE`, pour que les compteurs d'identifiants repartent de zéro, et que les identifiants fixes du point bloquant restent valables.

**NON VÉRIFIÉ**

- La façon exacte dont Next.js 16.4.6 réagit à un rejeu de Server Action entre deux sessions : en-têtes requis, validité de l'identifiant d'action après une remise à zéro des données. Le témoin de rejeu le tranchera.
- L'usage de directives de cache dans les apps A, A0 et B.