# Comment construire l'usine solidement : la conception de chaque mécanisme — 13 novembre 2026

> **Pour qui** : Arthur, pour comprendre comment chaque mécanisme de l'usine se construit avant d'écrire du code. Le texte
> peut aussi être donné à une IA extérieure pour critique.
> **Ce que c'est** : pour chaque mécanisme, à quoi il sert, comment le construire solidement, ses pièges, et comment on
> prouve qu'il marche.
> **Ce que ce n'est pas** : le plan de match (ordre, étapes), qui est dans `USINE.md` §4 ; ni du code.
> **Complété le 13 nov (soir)** par la recherche de Claude en ligne (archivée :
> `archives/echanges-2026-11/sorties-claude-en-ligne-2026-11-13.md`) : voir §15 (points vérifiés) et §16 (ce qu'elle
> ajoute ou corrige, mécanisme par mécanisme).
> **Statuts** : tout est **Avis** (de la conception, rien n'est encore mesuré), sauf mention **Prouvé** (un fichier ou un
> essai du projet) ou **À vérifier** (un fait extérieur cité de mémoire).

---

## 0. L'idée qui tient tout

L'usine est surtout du **logiciel ordinaire et prévisible** : un compilateur (la Description devient une app) et un banc
d'essai (des juges). Ce sont des choses que l'informatique sait construire solidement depuis longtemps.

L'IA n'agit qu'à **deux endroits** :

- elle **lit** la demande (les lecteurs) ;
- elle **construit le reste** de l'app (l'agent).

Ces deux endroits sont **enfermés** : l'IA propose, un programme contrôle. La solidité de l'usine ne dépend donc pas de
l'IA. Elle vient de l'ingénierie classique : contrats, isolement, tests, traces. Ce que l'IA ajoute (la compréhension,
la richesse des écrans) est **vérifié avant de passer**.

---

## 1. Les règles de fabrication communes à tous les mécanismes

Ces huit règles s'appliquent à chaque pièce de l'usine. La plupart existent déjà dans l'usine d'octobre.

1. **Des fichiers figés, de forme fixe, entre deux étapes.** Une étape lit des fichiers, en écrit d'autres. Chaque
   fichier a un schéma (pydantic côté Python, des types côté TypeScript). Rien ne passe en texte libre ni « en
   mémoire ». *Prouvé : c'est déjà le cas (`01-description.json`, `02-matrice.json`, rapports).*
2. **Une empreinte pour tout.** Chaque fichier produit porte l'empreinte de ses entrées. Une étape ne se rejoue que si ses
   entrées changent. On obtient ainsi la reprise, la reproductibilité, et on ne repaie jamais une étape déjà faite.
3. **Ce qui vient d'une IA passe un contrôle strict.** Si la réponse est mal formée, on renvoie l'erreur précise à l'IA,
   jamais une réparation devinée. *Prouvé : les lecteurs (3 essais, citations vérifiées mot pour mot).*
4. **Un seul endroit du code par outil extérieur.** Le modèle d'IA, ZenStack, Docker, Playwright et chaque service sont
   touchés par un **adaptateur** et un seul. Changer d'outil, c'est changer l'adaptateur. *Prouvé : `ia.py` pour les
   modèles, `lib/session.ts` pour la connexion.*
5. **Échouer franchement.** Un refus porte un code stable (`[bloc:…]`) ; jamais de rattrapage silencieux. *Prouvé.*
6. **Chaque mécanisme a sa preuve.** Un programme montre qu'il fait ce qu'il doit, **et** qu'il refuse ce qu'il doit
   refuser. *Prouvé : `preuve_regles.mts`, `preuve_ecrans.py`, `preuve_porte.py`, `preuve_reponses.py`.*
7. **Tout se rejoue sans payer.** Des exemples enregistrés (descriptions, réponses d'IA figées, constructions d'agent
   figées) permettent de tester l'usine à 0 $ après chaque modification. *Prouvé en partie : `--rejouer`, les exemples.*
8. **Tout laisse une trace structurée** : qui, quoi, avec quelles versions, combien, avec quel résultat.

---

## 2. La carte des mécanismes

| # | Mécanisme | À quoi il sert | Existe ? |
|---|---|---|---|
| 3 | **Orchestrateur et planificateur** | enchaîner les étapes, décider, reprendre | en partie (`assembler.py`, journal, reprise) |
| 4 | **Agent enfermé** | construire ce que l'assembleur ne sait pas faire | prouvé à la main seulement |
| 5 | **Juges** | dire, preuves à l'appui, si l'app est conforme | droits oui ; écrans d'un agent non |
| 6 | **Sabotages et qualification des juges** | prouver que les juges voient les défauts et acceptent les apps justes | oui pour nos juges, sur nos apps |
| 7 | **Assembleur** | poser le cœur sûr (données, droits, écrans de base) | oui |
| 8 | **Catalogue des capacités** | ce que l'usine sait faire, avec ses preuves | oui sous forme de blocs |
| 9 | **Compréhension et miroir** | comprendre la demande et la faire valider | oui, sauf la page du client |
| 10 | **Évolution et flotte** | changer une app livrée sans rien perdre ; mettre à jour toutes les apps | non |
| 11 | **Livraison** | comptes, mise en ligne, sauvegardes, surveillance | non |
| 12 | **Traces, mesures et mémoire** | savoir si l'usine progresse, et retenir les leçons | en partie |
| 13 | **Sécurité de l'usine** | protéger le PC, les secrets, les données des clients | non |

Vue d'ensemble :

```
                    ORCHESTRATEUR (Python + une table PostgreSQL) : enchaîne, décide, reprend, trace
  demande ─► Comprendre ─► Valider ─► Planifier ─► Poser le cœur ─► Construire le reste ─► Juger ─► Livrer / Faire évoluer
             (lecteurs)    (miroir,   (catalogue)  (assembleur)     (agent, boîte n° 1)    (juges,
                            porte)                                         ▲              boîte n° 2)
                                                                           └─ rapport ◄──────┘
             CATALOGUE DES CAPACITÉS : vocabulaire, pièces, documentation pour l'agent, juges, preuves, versions
```

---

## 3. L'orchestrateur et le planificateur

### Ce qu'il fait

C'est le **chef de chantier**. Il prépare chaque étape, la lance, récupère ce qu'elle produit, et décide de la suite :
continuer, corriger, s'arrêter ou demander à un humain. Il ne construit rien lui-même, et il ne juge rien lui-même.

### Comment le construire solidement

- **Une construction est une machine à états** : `comprise → validée → planifiée → cœur posé → construite → jugée →
  admise / refusée / en attente d'un humain`. Chaque passage est une ligne dans une table PostgreSQL : la construction,
  l'étape, l'état, les empreintes d'entrée et de sortie, le coût, la date. Les fichiers restent dans un dossier par
  construction (comme `runs/` aujourd'hui).
- **Chaque étape est rejouable sans danger.** La relancer avec les mêmes entrées donne le même résultat, ou réutilise
  celui déjà produit. Si le PC s'éteint en pleine construction, on relance, et l'orchestrateur repart de la dernière
  étape terminée.
- **L'empreinte d'une étape d'agent** comprend : l'image de la boîte, le modèle, la version du moteur, et le **texte
  exact** des consignes données. Sinon une reprise rejouerait, sans le savoir, un autre agent (remarque de Claude en
  ligne).
- **Les attentes humaines sont des états explicites** : « en attente de validation du client », « en attente d'une
  décision après deux corrections ratées ». Rien ne reste bloqué en silence.
- **Une ligne de commande d'abord** (`python -m usine …`), une page plus tard.
- **Notre code, pas un moteur de flux.** Le nôtre existe déjà en partie : `journal.etape`, `--reprendre`, `--rejouer`.
  DBOS (bibliothèque Python de flux durables sur PostgreSQL) seulement si plusieurs processus doivent un jour reprendre
  ensemble. Temporal reste écarté : trop lourd, et déjà quitté avec l'usine 1.

### Le planificateur (une partie de l'orchestrateur)

Il compare la Description validée au catalogue, et en tire **une liste de tâches, sans IA** : « les ordres viennent du
plan, pas de l'IA », comme le dit notre règle de circulation n° 6.

- Il note les capacités nécessaires, admises ou non. Une seule non admise rend l'app non livrable : elle reste
  constructible en essai.
- Il dit ce que l'assembleur pose et ce que l'agent doit faire. La liste des tâches de l'agent est tirée de la
  Description : un écran hors stock, un tableau de bord, un calcul, un parcours que les pièces fixes ne couvrent pas.

### Les pièges

- Un orchestrateur qui « devient intelligent » : il ne doit jamais interpréter du texte d'IA pour décider. Il ne lit que
  des verdicts typés.
- Des étapes qui se parlent directement : elles passent toujours par des fichiers figés.

### Comment on prouve qu'il marche

- On coupe une construction au milieu, on la relance, et l'on vérifie qu'elle repart au bon endroit sans rien repayer.
- On rejoue une construction figée, et l'on vérifie qu'elle donne les mêmes verdicts.
- Un faux agent (qui rend toujours la même réponse) et un faux juge (qui refuse toujours) vérifient que les décisions
  sont les bonnes : corriger deux fois, puis s'arrêter et demander à un humain.

---

## 4. L'agent enfermé dans sa boîte

C'est le mécanisme le plus nouveau, et celui où l'on peut le plus se tromper. Je le détaille.

### 4.1 Ce qu'est un agent, sans magie

Un agent est une **boucle** :

1. on envoie au modèle des **consignes** et une **tâche** ;
2. le modèle répond par une **action**, par exemple une commande `ls` ou « écris ce fichier » ;
3. le programme **exécute** l'action et récupère le résultat (l'**observation**) ;
4. il **ajoute** l'action et l'observation à la conversation, et renvoie le tout au modèle ;
5. on recommence, jusqu'à ce que le modèle dise « terminé », ou qu'une **limite** soit atteinte (nombre d'étapes, coût,
   temps).

Tout le reste (le contexte, la mémoire, les outils) n'est que la réponse à trois questions : **que met-on dans la
conversation, quelles actions permet-on, et quand s'arrête-t-on.**

**Le problème central** : à chaque tour, la conversation grossit, et tout est renvoyé au modèle. Après une heure (A0 a
duré 1 h 02), elle devient longue, chère et confuse. Le modèle oublie des consignes du début, répète des erreurs, se
noie dans des journaux de compilation. C'est ce qu'on appelle **l'accumulation de contexte**.

### 4.2 Le moteur : on l'achète, et on le branche derrière une prise unique

- **On n'écrit pas la boucle.** On prend un moteur existant : mini-swe-agent, une boucle d'une centaine de lignes qui
  n'utilise que le terminal (**Prouvé** par la recherche du 13 nov : limites d'étapes, de coût (3 $ par défaut) et de
  durée, arrêt après 3 erreurs de format consécutives, trajectoire complète enregistrée, exécution dans Docker). OpenCode
  sert de comparaison.
- **Une prise unique** : l'orchestrateur ne connaît qu'une interface, `construire(tâche, boîte, limites) → résultat`.
  Le résultat contient le commit produit, la trajectoire, le coût et la raison de l'arrêt. Chaque moteur est un
  **adaptateur** derrière cette prise.
- **Révisé le 14 nov, après relecture** : l'abonnement ne peut pas servir de « cerveau » à un autre agent. Les
  conditions d'Anthropic prévoient « l'usage ordinaire de Claude Code ». Tant qu'il n'y a pas de budget d'API,
  **l'artisan est donc Claude Code lui-même**. Il ne modifie que les écrans, et toutes ses commandes passent par
  l'atelier (`conception/essai-agent-constructeur.md`). mini-swe-agent viendra avec l'API, derrière la même prise. Les
  deux options ci-dessous sont l'histoire de cette décision.
- *(Histoire, 13 nov)* **D'où venait le modèle** : on étendait la **boîte aux lettres** qui marche déjà pour les
  lecteurs (`lecteur-isole`).
  - **Option 1, d'abord** : mini-swe-agent tourne dans la boîte Docker ; à chaque fois qu'il a besoin du modèle, un
    adaptateur écrit la conversation dans la boîte aux lettres, et un agent neuf de la session isolée (lire et écrire
    seulement) répond par la prochaine action. Aucun compte ni aucune clé dans la boîte ; passer à l'API ne change que
    l'adaptateur. Prix à payer : un aller-retour par étape (environ 30 par tâche), et un quota qui fond vite, puisque
    chaque appel relit tout l'historique.
  - **Option 2, en secours** : la boîte aux lettres porte une tâche entière, et la session lance un agent constructeur
    qui a le terminal et l'édition sur le dossier de la tâche. C'est plus rapide, mais la boîte n'est plus qu'un dossier
    Windows protégé par des réglages, et on dépend de Claude Code.
  - **Pour de vrais clients : l'API**, sous conditions commerciales (§16.11).
  - L'essai jetable 1.2 du plan tranche entre les deux options.
- **Changer de moteur ou de modèle ne touche à rien d'autre.** Avant d'adopter un moteur ou un modèle, on le fait passer
  sur un petit **banc des moteurs** : quelques tâches fixes, jugées par nos juges (§4.13).

### 4.3 La boîte : ce que l'agent peut et ne peut pas faire

La boîte est un **conteneur Docker** créé pour une seule tâche, puis détruit. Elle est construite ainsi :

| Élément | Réglage | Pourquoi |
|---|---|---|
| Système | Linux, l'image figée de la pile (Node, dépendances exactes, Playwright) | mêmes versions partout ; plus aucun piège de PowerShell pour l'agent |
| Fichiers du **cœur** (ce que l'assembleur a posé) | **en lecture seule** | l'agent ne peut physiquement pas toucher aux droits, aux tables ni au squelette : le manifeste de propriété est appliqué par le système de fichiers lui-même, pas vérifié après coup |
| Dossier `sur-mesure/` | en écriture | c'est sa zone |
| Dépendances | déjà installées dans l'image, **aucun accès à npm** | il ne peut pas ajouter une bibliothèque ; s'il en a besoin, il le **propose** (on l'ajoutera à l'image, avec sa raison) |
| Réseau | **aucun**, sauf vers le compteur du modèle | il ne peut rien télécharger ni rien envoyer ailleurs |
| Clé de l'IA | **absente de la boîte** : la boîte parle à un **compteur** (un relais placé dehors) qui détient la clé | la clé ne peut pas fuir ; le compteur mesure le coût réel et **coupe** au-delà du budget (LiteLLM le fait, *À vérifier*) |
| Base de données | une base d'essai à lui, jetable | il peut lancer l'app et l'essayer ; il n'a jamais accès à la base des juges |
| Ressources | plafonds de processeur, de mémoire et de durée | une boucle folle ne bloque pas le PC |
| Données des clients | jamais | l'agent ne travaille que sur des données de démonstration |

### 4.4 Ce qu'on donne à l'agent : le contexte de départ

Tout ce que l'agent reçoit est **généré par l'usine**, versionné, et entre dans l'empreinte de la construction.

1. **Les consignes générales** (fixes, les mêmes pour toutes les apps) : qui il est, ce qu'il a le droit de faire, ses
   outils, comment terminer, ce qu'il ne doit jamais faire (toucher au cœur, contourner les droits, inventer une table).
2. **La tâche** : une seule, précise (voir §4.5), avec son **critère de réussite** visible.
3. **La fiche de l'app**, générée depuis la Description en deux formes :
   - un résumé lisible (fiches, rôles, états, qui fait quoi) ;
   - des **types TypeScript générés** (noms des fiches, champs, états).

   Le code de l'agent est ainsi vérifié par le compilateur contre la Description du jour : si la Description change,
   le compilateur montre exactement ce qui casse.
4. **L'`AGENTS.md` généré** :
   - les conventions (noms, contrat d'accessibilité, points d'extension) ;
   - **la seule façon d'accéder aux données** : le client ZenStack lié à la personne connectée (*Prouvé* : `dbFor(user)`
     existe déjà dans le squelette), avec lequel les droits s'appliquent d'eux-mêmes ;
   - la documentation des capacités utilisées par cette app, et seulement celles-là ;
   - les pièges connus, tirés de notre registre (par exemple : une action est un formulaire POST, jamais un lien ; la
     session se lit derrière `Suspense`).
5. **La documentation des bibliothèques**, en local. Next.js 16 fournit déjà la sienne dans `node_modules`, avec un
   index : l'agent la consulte au besoin, au lieu de tout recevoir d'avance.

**Ce qu'on ne lui donne pas :**

- **les juges** et leurs données ;
- **la demande brute du client.** La Description validée est la seule source. Lui donner la demande l'inviterait à la
  « recomprendre » autrement que le client l'a validée. S'il voit un manque, il le signale (§4.8).

### 4.5 Découper : la vraie parade à l'accumulation de contexte

**La règle la plus importante : jamais « construis l'app » en une seule conversation d'une heure.** L'orchestrateur
découpe le travail en **petites tâches**, et chaque tâche est **une conversation neuve** :

- une tâche « fondations » d'abord (mise en page commune, composants partagés) ;
- puis une tâche par écran, tableau de bord, calcul ou parcours à réaliser ;
- chaque tâche commence par l'état du dépôt git (le travail déjà fait est dans les fichiers, pas dans la mémoire de
  l'agent) et par une **fiche d'avancement écrite par l'orchestrateur** : tâches faites, verdicts, ce qui reste.

Pourquoi c'est solide :

- le contexte reste petit, donc moins cher et plus précis ;
- un échec ne concerne qu'une tâche, et c'est elle seule qu'on relance ;
- la reprise après une coupure est naturelle ;
- le coût se mesure tâche par tâche ;
- plus tard, des tâches indépendantes pourront tourner en parallèle.

*Prouvé* : l'évolution de l'app A a été réussie par une **session neuve, sans mémoire** (52 lignes migrées sur 52). Le
contexte dans les fichiers a suffi. *À vérifier* : Anthropic décrit le même principe pour les agents de longue durée (une
fiche d'avancement, une liste de fonctions à faire, un commit par fonction, une session neuve à chaque fois).

**Le risque** : des tâches séparées qui se contredisent (styles différents, composants en double). Les parades : la tâche
« fondations », les conventions d'`AGENTS.md`, et un juge de cohérence simple (la compilation, et l'absence de doublons
de composants).

### 4.6 Pendant une tâche : garder le contexte propre

Même une petite tâche peut gonfler. Les sources sont connues : les longues sorties de commandes (compilation, tests,
journaux), la lecture de gros fichiers, et les tentatives ratées qui se répètent. Les parades, de la plus simple à la
plus compliquée :

1. **Des outils qui répondent court** (§4.7) : notre outil de vérification rend les 10 premières erreurs, résumées, pas
   600 lignes de journal.
2. **Couper les sorties trop longues** : le moteur garde le début et la fin d'une sortie, et dit qu'il a coupé
   (mini-swe-agent le fait, *À vérifier*).
3. **Des limites** : nombre d'étapes, coût et durée par tâche.
4. **Détecter les boucles** : la même commande ou la même erreur trois fois de suite, et la tâche s'arrête avec la raison
   « boucle ».
5. **Recommencer plutôt que compresser.** Si une tâche s'enlise, on la relance dans une conversation neuve, avec un
   résumé **écrit par l'orchestrateur** (ce qui a été essayé, ce qui a échoué). On ne fait pas résumer l'agent par
   lui-même. La compression automatique de l'historique n'est construite que si les mesures la rendent nécessaire.

**On mesure** : la taille du contexte à chaque étape, enregistrée dans les traces. C'est la courbe qui dira si le
découpage suffit.

### 4.7 Les outils de la boîte (l'interface entre l'agent et l'ordinateur)

L'équipe de SWE-agent a montré que **la qualité des outils donnés à l'agent compte autant que le modèle** (*Prouvé* dans
leur article de 2024, *À vérifier* pour le détail). On lui donne le terminal, plus quelques commandes écrites par nous :

| Commande | Ce qu'elle fait | Ce qu'elle rend |
|---|---|---|
| `verifier` | types, règles de style, construction de l'app, respect des zones | « OK », ou les premières erreurs, résumées et classées |
| `essayer <parcours>` | joue un **parcours public** du contrat sur l'app lancée | réussi, ou l'étape qui a échoué et ce qui était attendu |
| `demarrer` / `arreter` | lance ou arrête l'app sur sa base d'essai | l'adresse, ou l'erreur de démarrage |
| `base-neuve` | remet sa base d'essai à zéro, avec les données de démonstration | « OK » |
| `doc <sujet>` | cherche dans la documentation locale | les passages pertinents, courts |
| `signaler <texte>` | inscrit un manque du contrat (« il manque un lien entre devis et événement ») | « noté » ; c'est une **proposition** pour le miroir |
| `terminer` | annonce la fin de la tâche | — |

### 4.8 Fin de tâche : les contrôles mécaniques

Quand l'agent dit « terminé », l'orchestrateur :

1. **récupère le commit**, c'est-à-dire la différence exacte avec le départ ;
2. fait passer des **contrôles mécaniques**, rapides et sans IA :
   - les fichiers modifiés sont tous dans sa zone ;
   - aucune dépendance n'a été ajoutée ;
   - le client de base de données sans droits n'est pas importé (une règle ESLint `no-restricted-imports`, jamais une
     expression régulière) ;
   - aucun secret n'est écrit dans le code (gitleaks) ;
   - aucune requête SQL brute ;
3. lance la **compilation complète** ;
4. **range les signalements** de l'agent pour le miroir.

Seulement ensuite viennent les juges (§5).

### 4.9 Des tests visibles et des tests cachés

C'est le principe des concours de programmation, appliqué à l'usine :

- les **tests visibles** : l'agent peut jouer les parcours du contrat avec des données de démonstration (`essayer`). Ce
  sont ses critères d'acceptation, il est normal qu'il les connaisse ;
- les **tests cachés** : les juges rejouent les mêmes exigences **avec d'autres données et d'autres personnes**, ajoutent
  les interdictions vues par l'intrus et le visiteur, et lancent la sonde sur la base. L'agent ne les voit jamais.

Ça respecte la règle du rapport v2 : celui qui construit ne choisit pas les cas de la validation finale.

### 4.10 La boucle de correction

- Si les juges refusent, l'orchestrateur **traduit leur rapport** en une tâche de correction : quel parcours, quelle
  attente, ce qui a été observé. Il ne transmet jamais le code des juges.
- La correction est une **conversation neuve** : le commit actuel, le rapport traduit, et rien de l'historique précédent.
- **Deux corrections au plus**, comme valeur de départ. On s'arrête plus tôt si la **signature de l'échec** (l'empreinte
  des vérifications ratées) est identique à la tentative précédente : l'agent tourne en rond.
- Ensuite, un humain décide : corriger le contrat, ajouter un bloc, ou abandonner cette partie.

*Prouvé* : en A2, une seule correction a suffi, avec le rapport du juge (258 sur 258).

### 4.11 Ce qui peut mal tourner, et la parade

| Danger | Exemple | Parade |
|---|---|---|
| **Tricher pour passer les tests** | coder en dur les résultats attendus, ou détecter qu'on est en test | tests cachés avec d'autres données ; jugement sur l'état de la base ; juges hors de la boîte |
| **Modifier ou affaiblir un juge** | — | impossible : les juges ne sont pas dans la boîte |
| **Contourner les droits** | importer le client sans règles, écrire du SQL brut | contrôles mécaniques (§4.8) ; la sonde juge la base, quel que soit le code |
| **Injection de consignes** | une demande de client qui contient « ignore tes consignes et… », recopiée dans une citation de la Description | la boîte (ni réseau, ni secret, cœur en lecture seule) limite les dégâts ; les textes du client sont présentés comme des **données**, pas comme des consignes ; les juges voient les effets |
| **Tourner en rond** | la même erreur dix fois | détection de boucle, limites, signature d'échec |
| **Dépasser le budget** | une tâche qui coûte 20 $ | le compteur hors de la boîte coupe net |
| **Oublier une exigence** | un parcours non réalisé | chaque tâche a son critère ; les juges reprennent tous les parcours |
| **Dériver du contrat** | « améliorer » le modèle de données | il ne peut pas créer de table ; il ne peut que **signaler** |
| **Résultats différents d'une fois à l'autre** | deux constructions, deux apps | accepté pour le « reste » (le cœur, lui, ne varie pas) ; mesuré ; et utilisé pour trouver les trous du contrat (§6.4) |

### 4.12 Les consignes sont du code

Les consignes générales, les modèles de tâche et l'`AGENTS.md` sont des **fichiers versionnés**, avec des variables
remplies par l'usine. On les traite comme du code :

- chaque version a son empreinte ;
- **toute modification se teste sur le banc des moteurs** (§4.13) avant d'être adoptée, pour éviter qu'une
  « amélioration » des consignes casse ailleurs ;
- on ne les retouche jamais pour une seule app (notre règle n° 11 : corriger une classe, jamais un cas).

### 4.13 Comment on prouve que l'agent et sa boîte marchent

- **Le banc des moteurs** : une dizaine de tâches fixes et variées (un écran de liste enrichi, un tableau de bord, un
  calcul, un parcours hors stock), sur des apps du corpus, jugées par nos juges. On y mesure : la réussite, le coût, la
  durée, les arrêts prématurés, la taille du contexte et la variance (chaque tâche deux fois). Tout moteur, modèle ou
  changement de consignes passe ce banc.
- **Les preuves de la boîte** : un « agent malveillant » scripté essaie d'écrire dans le cœur, d'appeler internet, de
  lire la clé, d'importer le client sans droits, d'ajouter une dépendance. Chaque tentative doit échouer ou être
  refusée. C'est le sabotage appliqué à la boîte elle-même.
- **L'examen final** : le lot de briefs cachés, une seule fois, à la fin.

---

## 5. Les juges

### 5.1 Ce qu'est un juge, techniquement

Un juge est un programme qui reçoit **le contrat validé** et **l'app en marche**, et qui rend une **liste de verdicts**.
Chaque verdict contient :

- **l'exigence** qu'il vérifie, reliée à sa source : une case de la matrice, un parcours, une règle d'une capacité ;
- **le résultat** : conforme, non conforme, ou non jugé ;
- **la sorte d'échec** : fonctionnel, convention non respectée, ambiguïté, ou environnement ;
- **la preuve** : ce qui a été fait, ce qui était attendu, ce qui a été observé.

La sortie est un fichier JSON de forme fixe. L'orchestrateur ne lit que ça.

### 5.2 Où un juge regarde : les frontières observables

Un juge **ne lit jamais le code** de l'app (sauf les contrôles mécaniques du §4.8). Il observe l'app par ses frontières :

| Frontière | Comment | Pour quoi |
|---|---|---|
| **La base de données** | le client ZenStack avec les droits d'une personne, puis l'état réel de la base | les droits (juge des règles, sonde), le résultat métier d'un parcours |
| **Le navigateur** | Playwright, éléments trouvés par rôle et par nom accessible | les parcours d'écrans, l'affordance honnête, l'accessibilité (axe-core) |
| **Les services simulés** | les doublures locales des services extérieurs (boîte d'e-mails de test, stockage de fichiers local, paiement en mode test…) | ce que l'app envoie vers l'extérieur |
| **Les journaux** | la sortie de l'app | aucune erreur d'exécution, aucun secret dans les journaux |

### 5.3 D'où viennent les attentes

Les attentes viennent **toujours de la source validée par le client** : la matrice pour les droits, les parcours pour les
écrans, le contrat de chaque capacité pour le reste. Jamais du code ni d'une IA. *Prouvé : un test qui lisait les droits
produits n'attrapait qu'un sabotage sur quatre ; en lisant la matrice, quatre sur quatre.*

### 5.4 Les données d'essai : un mécanisme à part entière

Un juge ne vaut que par les situations qu'il essaie. Les données d'essai sont donc **générées depuis la Description**,
de façon à couvrir chaque case :

- deux personnes par rôle (pour vérifier « les siennes » contre « celles d'un autre »), l'intrus et le visiteur
  (*Prouvé* : `cas.mts`, `noyau.mts`) ;
- des fiches dans **chaque état** du circuit, des fiches liées et des fiches reliées à rien (un vrai trou trouvé ainsi
  en octobre) ;
- des valeurs limites : un champ facultatif vide, un montant à zéro, une date en bordure.

Chaque passage de juge part d'une **base neuve**. Une base modèle PostgreSQL copiée en une seconde (`CREATE DATABASE …
TEMPLATE …`) rend ça rapide.

### 5.5 Les familles de juges

| Famille | Exemples | Coût | Quand |
|---|---|---|---|
| **Mécaniques** (sans lancer l'app) | zones, dépendances, imports interdits, secrets, failles connues des dépendances (`npm audit`), analyse de code (Semgrep) | secondes | toujours, en premier |
| **Droits** | juge des règles (case par case, rôle par rôle), sonde (ce que la base permet vraiment) | secondes | toujours |
| **Parcours** | chaque parcours du contrat, joué par chaque rôle concerné, interdictions comprises | une minute environ | toujours |
| **Capacité** | ce que garantit chaque capacité utilisée (un calcul juste, un fichier invisible aux autres, une notification au bon destinataire…) | variable | si l'app utilise la capacité |
| **Universels** | aucune erreur d'exécution, accessibilité de base, temps de réponse raisonnable | secondes | toujours |

On les lance du moins cher au plus cher, et on s'arrête dès qu'une famille critique échoue. Ça économise le temps des
boucles de correction.

### 5.6 Le moteur de parcours (le juge d'écrans qui manque aujourd'hui)

- **Un parcours est une donnée** (les 7 éléments : acteur, état initial, objet, action, résultat visible, résultat métier,
  interdiction), rangée dans la Description.
- **La plupart sont calculés** depuis la matrice : pour chaque flèche d'un circuit et chaque rôle autorisé, « ce rôle fait
  passer cette fiche de A à B » ; pour les autres rôles, l'interdiction. Seuls les parcours hors matrice sont écrits par
  l'analyste et validés par le client.
- **Le moteur est un programme Playwright sans IA.** Il prépare l'état initial (dans la base), se connecte comme l'acteur,
  trouve l'objet et l'action **par rôle et par nom** (le libellé validé de la Description), agit, puis vérifie le
  résultat visible à l'écran et le résultat métier **dans la base**.
- **Classer les échecs mécaniquement** :
  - un élément introuvable veut dire que le contrat d'accessibilité n'est pas respecté : c'est un défaut de l'app, mais
    d'une autre famille que la logique métier ;
  - deux éléments trouvés, le mode strict de Playwright s'arrête : c'est une ambiguïté ;
  - un délai dépassé ou une panne de navigateur relève de l'environnement, et l'on rejoue une fois ;
  - une action faite avec une base fausse est un échec fonctionnel.
- **Ne pas se laisser tromper** : vérifier que l'élément trouvé est **visible**, et que c'est bien **lui** qui produit
  l'effet dans la base (un nom accessible collé sur le mauvais bouton satisferait la convention sans faire le travail).
- **Les composants qui n'entrent pas dans le contrat** (glisser-déposer, grille de calendrier, éditeur riche) ont des
  **exceptions déclarées**, composant par composant, avec leur propre façon d'être pilotés.
- **On part de l'existant** : nos tests d'écran (`e2e/blocs/`) trouvent déjà les boutons par leur rôle et par le libellé
  de la Description. Il faut les détacher du squelette (adresses des pages, repères internes).

### 5.7 Les pièges des juges

- **Les tests d'écran instables**, qui échouent une fois sur dix à cause d'un délai. Jamais d'attente fixe : on laisse
  Playwright attendre l'élément. On mesure l'instabilité en jouant le témoin trois fois (*Prouvé* : « témoin vert ×3 »).
  **Un juge instable est un juge disqualifié**, tant qu'il n'est pas corrigé.
- **Un juge lent** rend chaque boucle de correction lente. On fixe un budget de temps par famille. *Prouvé* aujourd'hui :
  6,5 s pour les droits, 59 s pour les écrans.
- **Un juge qui dépend du constructeur** : il ne doit jamais lire un fichier produit par l'agent pour former ses attentes.

### 5.8 Comment on garde les juges intacts

- Ils vivent dans **leur propre image**, hors de la boîte de l'agent, et sont versionnés.
- Leur empreinte est vérifiée avant chaque passage (*Prouvé* : `juger.ps1`).
- Une nouvelle version d'un juge doit être **requalifiée** (§6) avant de servir.
- Un juge est du code : il a ses propres tests, plus sa preuve par sabotage.

---

## 6. Les sabotages, et la qualification des juges

### 6.1 Ce qu'on veut prouver

Un juge doit faire deux choses : **refuser les apps fautives** (sinon il est aveugle) et **accepter les apps justes**
(sinon c'est un juge qui refuse tout, et qui ne sert à rien). On prouve les deux.

### 6.2 Quatre façons de fabriquer des sabotages

1. **Saboter le contrat, puis régénérer.** On inverse une case de la matrice (« l'employé peut approuver »), on
   refabrique, et le juge, qui lit la matrice d'origine, doit voir l'écart. Le sabotage est **valide par construction**,
   puisque le comportement attendu a changé. *Prouvé* : nos sabotages d'écrans sont déjà tirés de la matrice.
2. **Muter le code des droits** : on modifie une règle du schéma ZenStack en passant par l'arbre syntaxique de son
   langage (jamais par des expressions régulières). *Prouvé* : 49 mutants classés pour le juge des règles. *À vérifier* :
   le parseur de ZenStack existe-t-il comme bibliothèque réutilisable ?
3. **Injecter des pannes** : couper un service simulé, ralentir le réseau, arrêter l'app au mauvais moment, envoyer deux
   requêtes en même temps.
4. **Un agent saboteur**, isolé, à qui on demande un défaut d'une famille précise dans une app d'agent.

### 6.3 Ne pas tourner en rond

Un sabotage peut ne rien changer (un « mutant équivalent », qu'aucun juge ne peut voir puisqu'il n'y a rien à voir). Pour
écarter ces faux sabotages sans juger le juge par lui-même :

- **validation croisée** : la sonde valide les sabotages qui servent à qualifier le juge des règles, et inversement ;
- **sabotage du contrat** quand c'est possible, puisqu'il est valide par construction ;
- **revue humaine d'un échantillon**, pour mesurer le taux de sabotages sans effet ;
- le dossier de preuve dit alors « valides à X % près, mesuré sur un échantillon », jamais « valides ».

### 6.4 Le banc de qualification

C'est un **tableau calculé** :

- les **lignes** sont des apps conformes d'origines variées (assemblées, construites par un agent puis revues, ou
  transformées sans changer leur comportement : renommer, réordonner, changer la mise en page) ;
- les **colonnes** sont des sabotages ;
- chaque **case** donne le verdict attendu (accepter ou refuser).

Le banc se rejoue à chaque version d'un juge. Le **dossier de preuve** en sort : les sabotages attrapés par famille, les
faux positifs, et les limites (ce que ce juge ne sait pas voir).

**Bonus, la variance au service du contrat.** Deux constructions qui passent toutes deux les juges, mais que la sonde ou
un parcours voient se comporter différemment, révèlent un trou du contrat : une question à ajouter au miroir. *Prouvé
ailleurs* : ClarifyGPT le fait sur de petites fonctions (source donnée par Claude en ligne).

---

## 7. L'assembleur

### Ce qu'il fait

Il transforme la Description validée en **cœur** de l'app : les tables, les **droits**, la notice d'écran, les données de
démonstration et le squelette. C'est un **compilateur**. *Prouvé* : 10 étapes, 3 min 27 s, 31 apps sur 31 sans défaut
de droits sur le corpus.

### Comment le construire solidement (ce qui est déjà fait, et ce qui change)

- **Les trois temps d'un compilateur** :
  1. contrôler l'entrée (la Description, en forme stricte) ;
  2. calculer (la matrice et les doctrines) ;
  3. produire (les traducteurs).

  C'est déjà sa structure.
- **Produire depuis des données typées, jamais en recollant du texte.** C'est la leçon de l'usine 1, dont les modèles
  transportés en texte et relus par des expressions régulières cassaient. Chaque fichier produit est relu par son outil
  (`zen generate` lit le schéma) : s'il ne se relit pas, la fabrication s'arrête.
- **Des fichiers de référence** : pour chaque exemple, les fichiers produits attendus sont gardés. Toute modification de
  l'assembleur montre exactement ce qui change dans chaque app. *Prouvé en partie : les outils de photo avant/après
  d'octobre.*
- **Le cœur est régénéré en entier, et jamais retouché à la main** (le patron Generation Gap). Le code de l'agent vit à
  part, dans `sur-mesure/`.
- **Les points d'extension** (nouveau) : le squelette offre des emplacements typés où le code de l'agent se branche. Des
  pages en plus, un panneau dans la page d'une fiche, une entrée de menu par rôle, un indicateur au tableau de bord.
  Le squelette les découvre tout seul (un registre), et les **types générés** depuis la Description les relient au
  contrat. Après une évolution, le compilateur montre ce que le code de l'agent doit adapter. *Prouvé* : lors de
  l'évolution de B, le typage a désigné le seul endroit cassé.

### Comment il grandit

Un nouveau bloc, c'est :

- un mot de vocabulaire dans la Description ;
- son traducteur ;
- sa pièce d'écran ;
- son module de juge ;
- sa preuve.

Le contrôle d'architecture refuse un bloc incomplet. *Prouvé.* Ce qui ne mérite pas d'être assemblé (un écran unique,
un calcul propre à une app) va à l'agent, dans `sur-mesure/`.

### Les pièges

- **Toucher au squelette pendant une fabrication en cours.** *Prouvé* : l'incohérence d'octobre.
- **Une doctrine écrite à deux endroits** (le calculateur et un traducteur). Chaque concept n'a qu'une source.
- **L'assembleur qui grossit sans fin.** Avec l'agent pour la périphérie, on n'assemble que ce qui doit être sûr ou
  reproductible.

---

## 8. Le catalogue des capacités : une recette pour toutes

### Ce qu'est une capacité

C'est le **bloc d'aujourd'hui, élargi**. Une capacité est un savoir-faire vérifiable : « joindre des fichiers à une fiche
sans que les autres les voient », « calculer un total juste et l'afficher », « chercher dans les fiches qu'on a le droit
de voir », « présenter des créneaux dans un calendrier », « encaisser en mode test », « prévenir quelqu'un ». Toutes
suivent **la même recette** ; aucune n'est un cas spécial.

### Ce que contient son dossier

| Partie | Contenu |
|---|---|
| Vocabulaire | ce qu'elle ajoute à la Description (le contenant de la loi du contenant) |
| Contrat | ce qu'elle reçoit, garantit, interdit, et son périmètre |
| Pièces fixes (si besoin) | ce qui doit être sûr et écrit une fois : ses tables, leurs droits, un adaptateur vers un service |
| Documentation pour l'agent | comment l'utiliser, injectée seulement dans les apps qui en ont besoin |
| Doublure locale | un faux service pour les essais (stockage local, paiement en mode test…), si elle touche l'extérieur |
| Juges | ce qui prouve qu'elle est bien utilisée |
| Sabotages | ce qui prouve que ses juges voient les défauts |
| Preuve | les apps où elle a été prouvée, les verdicts, les versions (empreinte de l'image) |
| État | **calculé** : candidate, admise, ou à revérifier |

### Comment on en ajoute une

1. On écrit le contrat et le vocabulaire, que le miroir sait montrer au client.
2. **On écrit les juges et les sabotages avant de construire** : apprendre à vérifier avant d'apprendre à construire.
3. On décide de ce qui doit être une pièce fixe (ce qui touche aux droits, aux tables ou à l'argent) et de ce que
   l'agent peut faire seul.
4. On construit sur une première app, puis on réutilise sur **deux apps qui n'ont pas servi à l'apprendre**, sans
   toucher aux juges.
5. On rejoue tout le corpus : aucune régression.
6. L'état passe à « admise », par le calcul.

La première capacité à ajouter est **un choix à faire ensemble**, selon la fréquence dans les demandes réelles. Notre
corpus en donne une idée : tableaux de bord dans environ 13 briefs sur 33, calendrier dans 11.

---

## 9. La compréhension et le miroir (le maillon faible)

Claude en ligne a raison : une mauvaise lecture de la demande traverse **toute** l'usine, puisque l'assembleur traduit
fidèlement une matrice fausse. Le seul filet, c'est le miroir.

### Ce qui existe

*Prouvé* :

- **7 lecteurs** sans outils, avec un contrôle strict et des citations vérifiées ;
- **un critique** ;
- **des phrases du miroir calculées** depuis la matrice ;
- **des réponses du client** en opérations typées ;
- **une porte** avec empreintes ;
- 9 lectures justes sur 10.

### Ce qu'il faut construire, et comment

- **La page du client** : une page simple qui montre les phrases et les questions, et enregistre chaque réponse comme une
  opération typée. La validation est signée par l'empreinte de la Description. Plus tard, l'usine pourra fabriquer cette
  page elle-même.
- **Les propositions de l'agent** (les `signaler` du §4.7) deviennent des questions du miroir : « l'usine a remarqué
  qu'un devis semble lié à un événement : voulez-vous ce lien ? ».
- **Les parcours dans le miroir**, en phrases : « Le responsable approuve une demande en attente ; elle passe à
  "Approuvée" ; un employé ne peut pas le faire. »
- **Mesurer le miroir avec de vrais clients.** C'est le seul moyen de savoir s'il attrape les erreurs de lecture. On
  mesure : les erreurs trouvées par le client, celles trouvées plus tard, et le temps passé.
- **Les trois dettes de lisibilité** relevées quand Arthur a joué le client.

---

## 10. L'évolution et la flotte

### Ce que ça doit permettre

Changer une app livrée (« ajoute un champ », « un nouvel état ») **sans perdre de données**. Et mettre à jour toutes
les apps d'un coup quand la pile ou un juge change.

### Comment le construire

- **Des noms internes figés** dès la mise en service : renommer ne change que le libellé (*Prouvé* : c'est déjà le cas).
- **Une Description versionnée.** Chaque version est validée par la porte, et l'app sait de quelle version de la
  Description et de quelle image elle vient.
- **Le format de la Description lui-même est versionné.** Quand on ajoute du vocabulaire, les anciennes Descriptions
  doivent toujours se lire : un numéro de format, et des fonctions de mise à niveau. On l'oublie facilement.
- **Une évolution est une liste d'opérations typées** (ajouter un champ, retirer un état, ajouter une fiche…). Chacune
  porte sa **migration de données** : la valeur à mettre dans les fiches existantes, où vont les fiches d'un état
  supprimé, etc. Le client valide ces choix dans le miroir de l'évolution (« 37 fiches sont "en attente" : où vont-elles
  ? »).
- **La partie SQL** est faite par l'outil de migration établi de la pile (ZenStack et Prisma, *À vérifier* pour la
  version 3). **La partie données** est faite par de petites opérations typées écrites une fois par sorte d'opération.
- **Une répétition sur une copie** de la base : on migre la copie, on lance les juges, et l'on vérifie « aucune fiche
  perdue » (comptes et empreintes avant et après). Puis sauvegarde, migration réelle, et retour arrière possible.
- **Le code de l'agent s'adapte** : après la refabrication du cœur, la compilation montre ce qui casse dans
  `sur-mesure/`, et une tâche d'adaptation est donnée à l'agent.
- **La flotte** : une nouvelle image (une montée de version, une faille corrigée) entraîne la refabrication de chaque cœur
  depuis sa Description, le passage des juges, puis le déploiement. On commence toujours par une app d'essai.

---

## 11. La livraison

- **Les comptes** : Better Auth, branché à **un seul endroit** (`lib/session.ts`, qui simule aujourd'hui la connexion).
  Le critère décisif : pouvoir créer, isoler et supprimer automatiquement des personnes d'essai de chaque rôle, pour les
  juges. Les invitations (« le RH crée les comptes ») viennent avec.
- **La mise en ligne** : un serveur loué avec Coolify (ou Dokploy, ou Kamal). Chaque app a son conteneur, sa base, son
  adresse et ses secrets. **On ne déploie qu'un commit jugé**, vérifié par son empreinte.
- **Les sauvegardes** : automatiques, et **essayées** (une sauvegarde qu'on n'a jamais restaurée n'existe pas).
- **La surveillance** : Sentry ou OpenTelemetry pour voir les erreurs. Les demandes du client sont triées : défaut de
  l'usine, évolution, ou question d'usage.
- **La sécurité au-delà des droits**, avant le premier client : en-têtes, limites de requêtes, dépendances, liste OWASP
  ASVS.

---

## 12. Les traces, les mesures et la mémoire de l'usine

- **Une ligne par construction et par tâche** dans PostgreSQL : empreintes, image, moteur, modèle, consignes, coût réel
  (lu dans les réponses de l'API, via le compteur), durée, taille du contexte, verdicts. **Un dossier** avec la
  trajectoire de l'agent, le commit et les rapports.
- **Les mesures qui disent si l'usine progresse** :
  - la conformité ;
  - les défauts par famille ;
  - les faux positifs ;
  - le coût par app **admise** (corrections comprises) ;
  - les interventions humaines ;
  - la convergence (défauts nouveaux par app nouvelle).
- **La mémoire (« retenir »)** : chaque échec récurrent, repéré par sa **signature** à travers les constructions, devient
  l'une de trois choses :
  - une correction de l'assembleur ;
  - un nouveau juge ;
  - une ligne dans les pièges de l'`AGENTS.md`.

  Toujours inscrit au registre, et jamais corrigé pour un seul brief.
- *Prouvé : il existe déjà `journal.jsonl`, `99-rapport.json`, `audit_session.py`, le tableau de bord et le registre
  (59 corrections).*

---

## 13. La sécurité de l'usine elle-même

- **Le PC** : l'agent ne travaille jamais sur le PC, seulement dans sa boîte, sur une copie.
- **Les secrets** : aucun dans les boîtes. La clé de l'IA reste dans le compteur, les accès aux bases chez les juges et
  l'orchestrateur.
- **Les données des clients** : jamais dans la boîte de l'agent. Les demandes passent par des offres d'IA qui ne
  s'entraînent pas sur les données envoyées.
- **L'injection de consignes** : les textes des clients sont toujours présentés comme des données (§4.11).
- **L'usine elle-même** : ses dépendances sont figées et examinées comme celles des apps.

---

## 14. Comment développer tout ça sans aller à l'aveugle

### 14.1 Un squelette qui marche de bout en bout, d'abord

Le piège serait de perfectionner chaque mécanisme l'un après l'autre (d'abord l'orchestrateur parfait, puis l'agent
parfait…). On découvrirait trop tard qu'ils s'emboîtent mal.

La méthode solide, appelée « walking skeleton » (Alistair Cockburn), est différente : construire **d'abord une version
très mince de toute la chaîne**, qui marche de bout en bout sur l'app la plus simple (la médiathèque). Cette version
comprend :

- la boîte ;
- un moteur ;
- une seule tâche d'agent ;
- les juges existants plus la sonde ;
- une boucle de correction ;
- les traces.

Ensuite seulement, on **épaissit** chaque mécanisme, en mesurant à chaque fois sur le banc. C'est ce qui avait marché pour
le niveau 1 : le « squelette qui marche » N1.0, avant N1.1 et la suite.

### 14.2 Pour chaque mécanisme, toujours le même ordre

1. Une **fiche courte** validée par Arthur : but, démonstration, ce qui est touché, taille, risque.
2. **La preuve d'abord** : le programme qui montrera que le mécanisme marche et refuse ce qu'il doit refuser.
3. Le code, en reprenant l'existant avant de réécrire.
4. La preuve au vert, le registre à jour, une mesure.

### 14.3 Ce qui dépend de quoi

```
image figée ──► boîte ──► moteur derrière la prise ──► tâche d'agent ──┐
                                                                       ├──► boucle de correction ──► capacités ──► livraison
sonde prouvée + données d'essai ──► moteur de parcours ──► juges ──────┘
points d'extension du squelette ──► garde de sur-mesure/ ──► évolution
traces : dès le premier jour, partout
```

### 14.4 Les risques techniques à lever tôt (parce qu'ils peuvent tout changer)

| Risque | Ce qui le lèverait vite |
|---|---|
| Un moteur ouvert, avec un modèle donné, construit nettement moins bien que Claude Code | le banc des moteurs, sur 3 ou 4 tâches |
| Le moteur de parcours est trop fragile sur des écrans d'agent | le jouer sur les apps A, A0 et B déjà construites |
| Docker et WSL2 trop pénibles sur ce poste | monter la boîte et la détruire 20 fois de suite |
| Le contexte déborde même avec des petites tâches | la courbe de taille du contexte sur le banc |
| Le miroir n'attrape pas les erreurs de lecture | un premier vrai client |

---

## 15. Les points « à vérifier » : vérifiés le 13 novembre

Vérifiés à la source par Claude en ligne (sources dans le fichier archivé) :

| Point | Résultat |
|---|---|
| mini-swe-agent tourne dans Docker | confirmé (trajectoires publiques) |
| ses limites | confirmé : étapes, coût, durée, arrêt après 3 erreurs de format consécutives |
| sa trajectoire | confirmé : messages, coût, nombre d'appels, format versionné |
| il passe par LiteLLM | confirmé ; il a dû exclure deux versions **compromises** de LiteLLM |
| **il coupe les sorties trop longues** | **non vérifié** : à lire dans son code avant l'essai 1.2 (nos outils bornent leurs sorties de toute façon) |
| LiteLLM en relais | confirmé : clés virtuelles, budget maximal par clé et par fenêtre de temps, dépense suivie ; demande PostgreSQL |
| le guide d'Anthropic sur les agents de longue durée | confirmé : session de préparation, fichier d'avancement, liste de fonctions, une fonction par session, commits |
| SWE-agent : la qualité des outils compte | confirmé : +10,7 points avec une interface conçue pour le modèle ; sans commande d'édition, 18,0 % → 10,3 % |
| l'analyseur de ZenStack comme bibliothèque | confirmé : `@zenstackhq/language` (Langium), avec un générateur qui réimprime l'arbre |
| les migrations de ZenStack v3 | confirmé : `zen migrate` enveloppe Prisma Migrate |
| Docker Engine dans WSL2 sans Docker Desktop | confirmé : installation directe, démarrage par systemd ; fichiers dans le système de fichiers de WSL |

Une affirmation de la recherche est **fausse pour notre projet** : « shadcn/ui, déjà dans la pile ». Le squelette n'a
aucune bibliothèque de composants : Tailwind 4 et nos propres pièces (`usine/modele-app/components/`). Voir §16.12.

---

## 16. Ce que la recherche du 13 novembre ajoute ou corrige

Statuts : **Prouvé** = source citée par la recherche, ou fait du projet ; **Avis** = jugement ; ma **critique** est
signalée quand je ne suis pas d'accord ou que je nuance.

### 16.1 L'agent : le contexte et ses couches

Le fait (**Prouvé**, Chroma, 18 modèles) : la qualité baisse dès que l'entrée s'allonge, de façon irrégulière, et les
informations « presque justes mais fausses » accélèrent la baisse. Pour un agent de code, ce sont exactement les
anciennes versions d'un fichier et les tentatives ratées.

Le contexte d'une tâche est un empilement, **du plus stable au plus variable** (l'ordre compte aussi pour le cache, si
un jour on passe par l'API) :

| Couche | Contenu | Change… |
|---|---|---|
| 1. Consignes générales | rôle, règles, méthode, façon de terminer | jamais pour une app |
| 2. AGENTS.md généré | conventions, pièges du registre, documentation des seules capacités utilisées | à chaque version de l'app |
| 3. Fiche de l'app | résumé lisible, types générés depuis la Description | à chaque version de l'app |
| 4. Tâche et fiche d'avancement | quoi faire, critère de réussite, ce qui est fait | à chaque tâche |
| 5. Historique de la tâche | actions et observations | à chaque étape |

Trois parades contre le gonflement de la couche 5 :
1. des outils qui rendent des sorties courtes par construction ;
2. **masquer les vieilles observations** (« sortie retirée ») plutôt que les résumer, comme les processeurs d'historique de
   SWE-agent (**Prouvé**) ; une étude de 2025 le trouverait aussi efficace qu'un résumé par IA (*à vérifier*) ;
3. repartir à neuf quand une tâche s'enlise, avec un résumé écrit **par l'orchestrateur**.

**Notre version fait mieux qu'Anthropic sur un point** (Avis) : chez eux, l'agent coche ses fonctions ; chez nous, la
liste vient du planificateur et **ce sont les juges qui cochent**. L'agent ne peut ni oublier une tâche, ni se déclarer
fini trop tôt. Pas de sous-agents lancés par l'agent lui-même au début : l'orchestrateur joue ce rôle, de façon
traçable.

### 16.2 Les outils et les consignes de l'agent

Règles pour chaque outil de la boîte (Avis) :
- une sortie bornée, qui dit quand elle coupe ;
- une sortie actionnable (fichier, ligne, message), classée par importance ;
- une sortie déterministe ;
- **une vérification automatique après chaque modification** (le typage des fichiers touchés, ajouté à l'observation) :
  c'est l'équivalent du vérificateur d'édition de SWE-agent ;
- la description de l'outil fait partie des consignes et se teste sur le banc.

Les consignes sont des modèles versionnés, avec des variables remplies par l'usine ; leur empreinte entre dans celle de
la construction. Structure stable :
- le rôle ;
- le contexte ;
- les règles absolues ;
- la méthode : s'orienter, planifier court, réaliser, vérifier, terminer ;
- le format de fin ;
- quelques exemples variés plutôt qu'une longue liste de cas.

Les textes du client sont rangés dans un bloc de données délimité, jamais mêlés aux consignes. Le déterminisme
n'existe pas : on mesure la variance, on compte sur les juges.

### 16.3 La sécurité de l'agent face à l'injection de consignes

**Prouvé** (Beurer-Kellner et al., 2025) : six patrons restreignent volontairement un agent. Notre usine en applique
déjà trois :
- **« planifier puis exécuter »** : le planificateur, un programme, fixe les tâches avant que l'agent voie quoi que ce
  soit ;
- **une IA en quarantaine** : les lecteurs ne rendent que du JSON contrôlé ;
- **la réduction du contexte** : l'agent ne reçoit jamais la demande brute.

La surface qui reste : les libellés et citations de la Description. Ils vont dans un bloc de données, et les juges
vérifient les effets.

Leçon au passage (**Prouvé**) : deux versions de LiteLLM ont été compromises. Les dépendances **de l'usine elle-même**
sont figées avec leurs empreintes, comme celles des apps. Le 13 nov, `next build` a d'ailleurs refusé de construire
avec Next.js 16.4.0 (failles critiques) : registre n° 60.

### 16.4 La boîte : le durcissement ordinaire

En plus de §4.3 (Avis) :
- un utilisateur non administrateur ;
- un système de fichiers en lecture seule hors des zones permises ;
- les privilèges retirés et un nombre de processus plafonné ;
- un réseau interne qui ne voit que le relais.

gVisor plus tard, seulement si des données sensibles entrent en jeu. Toutes les conditions d'arrêt sont branchées
(étapes, coût, durée, erreurs de format, signature de boucle). Une panne du modèle se relance après une attente
croissante et se classe « environnement », pas « l'agent a échoué ». La trajectoire est enregistrée après chaque étape.
Une tâche part d'un commit et rend un commit, ou rien.

### 16.5 Les juges : cinq sortes d'oracles

| Oracle | Principe | Dans l'usine |
|---|---|---|
| Spécification exécutable | les attentes se calculent depuis le contrat | chaque case de la matrice, chaque parcours |
| Propriétés | une règle vraie pour toutes les entrées | « personne ne voit une fiche hors de son périmètre », quelles que soient les données |
| **Modèle** | un modèle simple, comparé à l'app après une suite d'actions | la matrice et les circuits **sont** ce modèle |
| Relation métamorphique | deux exécutions liées par une règle connue | doubler une quantité double un montant ; filtrer puis compter donne au plus le total |
| Différentiel | deux réalisations indépendantes s'accordent | le cœur assemblé contre une version d'agent ; une formule évaluée par un interpréteur de référence et par l'app |

**Le juge par modèle** (Avis, l'idée la plus forte de la recherche) : fast-check (**Prouvé** : génère des entrées, réduit
un échec à son plus petit contre-exemple, rejoue par graine, sait tester par modèle) tire au hasard des suites d'actions
faites par des rôles différents. Par exemple : créer, faire passer une étape, retirer un rôle, puis modifier. Après
chaque action, il compare la base au modèle. Il trouve **par construction** la famille que notre juge des règles rate :
modifier ses fiches après avoir perdu son rôle.

Ce qu'on ajoute aux données d'essai et à la stabilité :
- **Données d'essai** : générées depuis la Description ; combinaisons **par paires** quand les dimensions se multiplient
  (rôle × état × lien × valeur limite) ; une graine enregistrée ; une base neuve copiée d'une base modèle PostgreSQL.
- **Stabilité** (**Prouvé** : chez Google, près de 16 % des tests montraient une instabilité) :
  - jamais d'attente fixe ;
  - l'horloge de Playwright, installée avant de charger la page ;
  - un fuseau et une langue fixés ;
  - **on ne relance un juge que pour classer une panne d'environnement, et la relance est inscrite** ;
  - chaque juge est joué plusieurs fois sur les témoins, et une seule hésitation le met à l'écart.
- **Ce qu'un juge rend** : un verdict par exigence, relié à son identifiant stable ; une exigence non jugée est dite
  « non jugée » ; une preuve rejouable (données, graine, actions, attendu, observé) ; un format fixe et versionné. Pour
  les contrôles mécaniques, le format standard SARIF (*à vérifier*).
- **Vitesse** : du moins cher au plus cher, arrêt dès qu'une famille critique échoue ; un budget de temps par famille
  (un juge qui ralentit est une régression).

**Ma critique** sur « les juges sont le seul code qu'Arthur doit relire ligne par ligne ». C'est juste sur le fond :
une erreur de juge passe en silence. Mais exiger une relecture ligne par ligne d'un code TypeScript serait irréaliste
et donnerait une fausse assurance. Ce que je propose (`USINE.md` §2.3) :
- chaque juge a sa fiche « ce que je vérifie / ce que je ne vérifie pas », validée par Arthur ;
- son code est gardé court ;
- le banc de qualification fait la preuve mécanique ;
- Arthur lit le code quand il le peut.

### 16.6 Les sabotages : deux familles de plus, et l'usine elle-même

En plus des quatre familles de §6.2 (contrat inversé, règle mutée, panne injectée, agent saboteur) (Avis) :
- **saboter l'environnement** : changer le fuseau, avancer l'horloge au-delà d'une échéance, vider un service simulé ;
- **saboter les données** : une fiche orpheline, un champ facultatif vide, une valeur limite.

**Le test par mutation s'applique aussi à l'usine** : StrykerJS pour TypeScript, mutmut pour Python (**Prouvé**). Le
calculateur, les traducteurs et l'orchestrateur sont du code dont tout dépend ; une usine qui exige des preuves de ses
apps les exige de ses propres pièces. Les mutants équivalents survivent par nature : ils demandent un tri humain.

Le banc de qualification mesure la détection par famille, les faux positifs (zéro sur les témoins), la stabilité (zéro
hésitation), la vitesse et les limites (écrites, jamais cachées). **Les seuils se fixent avant de lancer.**

### 16.7 L'assembleur est un compilateur

- **Trois temps, sans raccourci** : lire et contrôler la Description (pydantic, fait) ; calculer **une** représentation
  intermédiaire, la matrice et le modèle normalisé, où toutes les décisions sont prises une fois ; émettre. Aucun
  émetteur ne lit la sortie d'un autre.
- **Générer avec des structures** :
  - le schéma ZenStack se construit comme un arbre avec `@zenstackhq/language`, puis s'imprime ; à défaut, tout
    schéma produit est relu par l'analyseur officiel. C'est aussi ce qui permet de muter les règles proprement ;
  - le TypeScript passe par ts-morph puis Prettier ;
  - un gabarit texte reste permis pour un fichier simple, si ses variables sont typées et si le fichier est relu par
    l'outil officiel du langage.
- **Une sortie stable, octet pour octet** : vérifiée en générant deux fois ; un en-tête « généré, ne pas modifier » avec
  l'empreinte de la source ; des fichiers de référence par exemple (tests d'approbation). *(Le banc du calculateur l'a
  déjà montré le 13 nov : sortie identique au caractère près après le déménagement.)*
- **Les doctrines testées comme des propriétés** : « aucune règle n'accorde la suppression si la Description ne la
  demande pas », « connecté ne veut jamais dire toute personne connectée », « on ne désigne jamais une fiche qu'on ne
  peut pas voir ». Un générateur de Descriptions aléatoires mais valides (Hypothesis, *à vérifier*) les vérifie sur des
  milliers de cas au lieu de 14 matrices ; mutmut dit si ces tests voient une doctrine cassée.
- **Les types générés depuis la Description sont le contrat** entre le cœur et `sur-mesure/` : le code de l'agent est
  compilé contre eux, et c'est le compilateur qui signale la première incompatibilité après une évolution.

### 16.8 L'orchestrateur, la compréhension et le miroir

**L'orchestrateur** (Avis) :
- une **table des transitions** permises (un passage non prévu est refusé et inscrit) ;
- **écrire avant d'agir** (au redémarrage, une étape lancée mais pas finie se reconnaît et se rejoue) ;
- un **verrou PostgreSQL** par app ;
- la **preuve par coupures** : on le tue au hasard et on vérifie trois choses : il reprend au bon endroit, il ne repaie
  rien, et les verdicts sont identiques.

**La compréhension** :
- les sorties structurées d'Anthropic garantissent la forme JSON (**Prouvé**), à utiliser le jour où l'on passe par
  l'API. La forme n'est pas la vérité : nos contrôles stricts (citations mot pour mot, identifiants connus, cohérence
  entre lecteurs) restent nécessaires ;
- les lecteurs se mesurent comme un modèle d'apprentissage : un jeu figé de briefs aux réponses attendues, rejoué à
  chaque changement (l'étude E5 en est le début) ;
- **le désaccord comme détecteur d'ambiguïté** : lire le même brief deux fois (ou par deux modèles) et comparer. Un
  désaccord devient une question du miroir. C'est bien moins cher que construire deux apps, et la boîte aux lettres le
  rend gratuit.

**Le miroir** a ses propriétés : chaque case de la matrice apparaît dans une phrase et une seule ; chaque question
correspond à un vrai choix dans la Description.

### 16.9 L'évolution, et une recette pour toutes les capacités

**L'évolution** :
- le patron « étendre, migrer, retirer » (**Prouvé**, Fowler) : jamais une suppression dans la même étape que le code qui
  en dépend ; un renommage se fait par ajout, copie, puis retrait ;
- chaque opération porte sa **classe de risque** (sans perte / avec perte, ce qui exige l'accord explicite du client) ;
- les fonctions de mise à niveau des Descriptions sont testées sur toutes les Descriptions enregistrées ;
- la **répétition sur une copie restaurée** prouve à la fois la migration et la sauvegarde ;
- la flotte se met à jour app par app, et s'arrête au premier échec.

**Les capacités** (Avis) : même recette, montrée sur six exemples.

| Capacité | Ajout à la Description | Pièce fixe | L'agent | Le juge tire la bonne réponse de… | Doublure |
|---|---|---|---|---|---|
| Tableaux de bord | indicateurs : quoi compter, sur quelles fiches, pour quel rôle | aucune | graphiques, mise en page | l'agrégat recalculé dans la base, avec les droits du rôle | aucune |
| Calendrier | créneaux, durées, conflits interdits | non-chevauchement, s'il touche aux données | la vue calendrier | créneaux attendus, horloge et fuseau figés | horloge de Playwright |
| Fichiers joints | champ fichier, types et tailles | stockage et ses droits | téléversement, aperçu | un fichier de A illisible pour B, à l'écran et par l'adresse directe | stockage local |
| Calculs et montants | formules, unités, arrondis | évaluation de la formule, si elle engage de l'argent | affichage, saisie | un interpréteur de référence ; des propriétés | aucune |
| Recherche et filtres | champs cherchables et filtrables | aucune | barre de recherche, filtres | ensembles attendus, jamais une fiche hors des droits | aucune |
| Notifications | événement, destinataire, contenu | l'intention d'envoi rangée en base | le gabarit du message | bon destinataire, bon contenu, une seule fois | une boîte de test |

**Première capacité : les tableaux de bord** (décidé le 13 nov).

### 16.10 Rendre l'usine visible et manipulable (le « jumeau numérique »)

Quatre niveaux (Avis) :

| Niveau | Ce qu'on voit ou fait | Source | Quand |
|---|---|---|---|
| Voir | une salle de contrôle en direct : constructions, étapes, tâche et commandes de l'agent, verdicts, coût | la table de traces | après le squelette qui marche |
| Rejouer | revoir une construction comme un film | trajectoires de l'agent, événements de l'orchestrateur | en même temps |
| Agir | pause, reprise, relance d'une tâche, décision après deux corrections ratées | des **commandes typées** envoyées à l'orchestrateur, qui décide | quand les décisions humaines deviennent fréquentes |
| Prévoir | durée et coût estimés avant de lancer | l'historique des constructions | bien plus tard |

**La règle : la vue lit, elle ne façonne pas.** L'erreur de l'usine Temporal n'était pas l'envie de voir. C'était de
laisser la visualisation dicter l'architecture (une activité par agent pour les voir interagir). Une commande refusée
par l'orchestrateur est inscrite, jamais forcée.

**À faire dès le squelette** : seulement des **événements complets** :
- pour chaque étape : la construction, l'étape, l'état, le début et la fin, les empreintes, le coût ;
- pour chaque pas de l'agent : la commande, les fichiers touchés, la taille du contexte ;
- pour chaque juge : chaque verdict, avec son exigence et sa preuve ;
- pour chaque décision humaine : qui, quoi, quand.

Plus tard :
- **Langfuse**, pour le détail des agents : arbre, frise temporelle, coût par étape ; licence MIT, installable chez soi
  (**Prouvé**) ;
- une page à nous pour la vue d'ensemble.

Le plaisir de voir l'usine travailler compte aussi : pour déboguer, pour rester motivé, pour la montrer.

### 16.11 La confidentialité des données

**Prouvé** :
- tout ce que l'usine donne au modèle part chez le fournisseur, même quand Claude Code tourne sur la machine ;
- sur un abonnement (Free, Pro, Max), les données peuvent servir à l'entraînement si le réglage est activé, et sont
  conservées jusqu'à 5 ans dans ce cas, 30 jours sinon ;
- sur l'API, pas d'entraînement par défaut, et une option sans conservation existe ;
- au Québec, la Loi 25 (article 17) exige une évaluation des facteurs relatifs à la vie privée avant d'envoyer des
  renseignements personnels hors du Québec. Héberger hors du Québec compte comme un tel envoi.

La parade est dans l'architecture : **aucune donnée réelle dans l'usine**.
1. La demande est anonymisée avant les lecteurs.
2. L'agent ne voit que des données de démonstration.
3. Les vraies données ne vivent que dans l'app livrée.

Concrètement :
- pendant le développement : abonnement avec le réglage d'entraînement désactivé, et seulement des demandes fictives ou
  publiques ;
- pour de vrais clients : l'API sous conditions commerciales, et une mention au contrat du client ;
- pour les cas les plus sensibles, en repli : un modèle local, mesuré sur le banc.

**Ma critique** sur « l'anonymisation est une petite étape de programme, sans IA ». C'est faux pour les noms de
personnes : un programme sans IA ne les reconnaît qu'avec des listes et des expressions régulières, ce qui est fragile
et contraire à notre règle « pas de solution maison fragile ». Ma proposition :
- **maintenant**, rien à construire : les demandes sont fictives ou publiques, et au premier client, Arthur rédige la
  demande avec lui (« ses mots », sans noms ni coordonnées) ;
- **plus tard** (service en ligne), un outil établi comme Microsoft Presidio (reconnaissance d'entités, modèles français
  de spaCy), mesuré sur un jeu de demandes avant d'être cru.

### 16.12 Le design des apps

Deux questions à ne pas confondre :
- **l'app est-elle utilisable ?** Ça se mesure en partie, donc ça peut avoir des juges ;
- **est-elle belle et à l'image du client ?** Aucun juge fiable n'existe : ça se règle par la validation du client.

Décisions proposées par la recherche, avec mes nuances :
1. **Un système de design comme source unique du style** : couleurs, typographie, espacements, arrondis. Une règle de
   lint refuse toute couleur ou taille hors du système, et l'agent n'installe aucune autre bibliothèque d'interface.
   **Correction** : shadcn/ui n'est pas dans notre pile. Le système de design sera fait de jetons (variables Tailwind 4)
   et de nos propres pièces. Ajouter shadcn/ui serait une décision de dépendance, avec sa raison et sa porte de sortie.
2. **L'identité du client dans la Description** (logo, couleurs, ton), validée au miroir. Changer d'image, c'est changer
   des valeurs, pas du code.
3. **Montrer avant de construire** : des aperçus d'écrans dans le miroir.
4. **Des captures d'écran par les juges dès le premier jour** : presque gratuit, et utile pour comparer avant et après
   une évolution. Prévu dans le squelette (`USINE.md` étape 2).
5. **Une IA peut donner son avis sur l'apparence, jamais un verdict.**
6. **Seul ce qui se mesure devient un juge** : contraste et étiquettes accessibles, pas de défilement horizontal sur
   téléphone, respect du système de design, temps de chargement.

Le contrat d'accessibilité et le design vont ensemble : des éléments bien nommés rendent l'app accessible **et**
testable par le moteur de parcours. Une limite à accepter : les apps seront propres et cohérentes, mais elles se
ressembleront. Un design unique est une demande de « bord », chiffrée à part.

### 16.13 La capacité de Claude Code à construire l'usine

La réponse de la recherche, que je partage :
- Claude Code peut écrire l'essentiel du code de l'usine, et vite. Le squelette de bout en bout est probablement une
  affaire de jours à deux semaines de sessions (estimation, pas mesure). L'usine 2 (environ 6 800 lignes avec ses
  preuves) et A0 (une heure) le montrent.
- Il ne peut pas **décider** à la place d'Arthur (ordre, seuils, ce qui est critique), ni **se juger lui-même**, ni
  **remplacer l'expérience** (variance, stabilité, coût réel), qui prend du temps calendaire. Il ne peut pas non plus
  travailler longtemps sans lui : les limites de l'abonnement imposent des sessions courtes, une tâche à la fois.
- **Le vrai risque est d'aller trop vite** : beaucoup de code, de la complexité qui s'empile. Les garde-fous sont la
  méthode : une fiche avant chaque mécanisme, la preuve d'abord, un mécanisme à la fois.

Le rôle d'Arthur dans la construction de l'usine est celui du miroir et des juges dans l'usine : Claude Code construit,
Arthur fixe le contrat et vérifie.
