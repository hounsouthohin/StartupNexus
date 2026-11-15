Construire l'usine solidement — la technique de chaque mécanisme
Nov 13, 2026 · Claude en ligne, en complément de la conception de l'agent local du 13 novembre
En bref
La conception de l'agent local est solide ; ce document ne la refait pas. Il dit, mécanisme par mécanisme, ce que l'état de l'art enseigne pour la construire sans surprise. Les idées qui comptent le plus :
1.  L'agent : découper, pas compresser. Le contexte d'un modèle se dégrade dès qu'il s'allonge, sur les 18 modèles testés par Chroma. La parade principale est le découpage en petites tâches, chacune dans une conversation neuve, avec une fiche d'avancement écrite par l'orchestrateur. Et ce sont les juges qui cochent les tâches, pas l'agent.
2.  Les consignes expliquent, la boîte impose. Aucune règle de sécurité ne repose sur l'obéissance de l'agent. Les consignes sont du code versionné, testé sur un banc avant toute modification.
3.  Les outils de l'agent comptent autant que le modèle : sorties courtes, bornées, actionnables, et une vérification automatique après chaque modification.
4.  Votre usine applique déjà, sans le savoir, les patrons de sécurité de l'état de l'art contre l'injection de consignes : le plan est fixé par un programme avant que l'agent voie quoi que ce soit.
5.  Les juges : cinq sortes d'oracles, et une stabilité absolue. Votre matrice est un modèle à états : un juge qui joue des suites d'actions au hasard trouverait la famille de défauts que votre juge des règles rate aujourd'hui.
6.  L'assembleur est un compilateur : représentation intermédiaire unique, génération par structures (l'analyseur officiel de ZenStack existe comme bibliothèque), sortie identique au caractère près, et doctrines testées comme des propriétés.
7.  Une seule recette pour toutes les capacités. L'e-mail n'a rien de spécial. Je proposerais de commencer par les tableaux de bord : la capacité la plus demandée dans vos briefs, la moins risquée, et la plus révélatrice du duo agent et juges.
8.  Avant de construire : trois essais jetables (la boîte sur ce poste, un moteur ouvert sur une tâche, le moteur de parcours sur des écrans d'agent), puis le squelette qui marche de bout en bout.
9.  Tous les points « À vérifier » de l'agent local sont vérifiés, sauf un (la coupure des sorties longues par mini-swe-agent).
10.  La salle de contrôle (voir, rejouer, agir, prévoir) lit les traces ; elle ne façonne jamais l'architecture. Il suffit, dès maintenant, d'écrire des événements complets.
11.  Une usine locale n'empêche pas les données de partir chez le fournisseur du modèle. Aucune donnée réelle n'entre dans l'usine (demande anonymisée, données de démonstration), et les vrais clients passent par l'API, pas par l'abonnement.
12.  Le design des apps repose sur un système de design unique, l'identité du client dans la Description, des aperçus dans le miroir et des captures d'écran dès le premier jour. Une IA peut donner un avis sur l'apparence, jamais un verdict.
Comment lire
• Ce document complète celui de l'agent local (« Comment construire l'usine solidement », 13 novembre), sans le répéter. Sa conception est solide et je la reprends comme base. J'y ajoute ce que l'état de l'art enseigne sur chaque mécanisme, avec des sources, et je vérifie ses points « À vérifier ».
• Statuts. [Prouvé] : une source citée et liée, ou un fait du projet. [Avis] : mon jugement. [À vérifier] : non relu à la source.
• Aucune capacité n'est traitée à part. L'e-mail, les tableaux de bord, les fichiers ou le calendrier suivent tous la même recette (section dédiée). Les exemples tournent entre plusieurs capacités.
• Biais. Je suis Claude, d'Anthropic, et plusieurs sources sur les agents viennent d'Anthropic. Je les signale, et je cite des sources indépendantes quand elles existent.
L'agent enfermé
C'est le mécanisme le plus nouveau et le plus risqué. Je le découpe en dix questions : de quoi est fait un agent, ce qu'il voit, comment on découpe son travail, ses outils, ses consignes, sa boîte, sa sécurité, son coût, sa fiabilité, et comment on l'évalue.
1. De quoi est fait un agent : le modèle et son harnais
Un agent, c'est un modèle plus un harnais : la boucle, les outils, ce qu'on met dans la conversation, et les conditions d'arrêt. Le modèle s'achète ; le harnais se configure.
• mini-swe-agent, concrètement. Son agent par défaut a une limite d'étapes, une limite de coût (3 USD par défaut), une limite de durée, et s'arrête après 3 erreurs de format consécutives. Il enregistre sa trajectoire complète, avec les messages et le coût de la tâche (code source) [Prouvé]. Il tourne dans des conteneurs Docker : des jeux de trajectoires publics le montrent exécutant chaque étape dans l'image de la tâche (Hugging Face) [Prouvé].
• Ce qu'on change : les modèles de consignes, les limites, l'environnement. Ce qu'on ne change pas : la boucle. Le moteur est un adaptateur derrière la prise unique de l'agent local.
• Une leçon au passage. Deux versions de LiteLLM, la bibliothèque qui sert à parler aux modèles, ont été compromises ; mini-swe-agent les a exclues (versions de mini-swe-agent) [Prouvé]. Les dépendances de l'usine elle-même doivent être figées avec leurs empreintes, comme celles des apps.
2. Le contexte : pourquoi il pourrit, et comment le garder propre
Le fait. Chroma a testé 18 modèles : leurs performances deviennent de moins en moins fiables à mesure que l'entrée s'allonge, de façon irrégulière, même sur des tâches simples (Chroma, « Context Rot ») [Prouvé]. Les informations proches de la bonne réponse mais fausses accélèrent la dégradation. Pour un agent de code, ce sont exactement les anciennes versions d'un fichier et les tentatives ratées qui restent dans l'historique.
Le principe. Anthropic le résume ainsi : trouver le plus petit ensemble d'informations à fort signal qui maximise les chances du résultat voulu. Ses trois techniques pour les tâches longues : la compaction (résumer puis repartir), les notes structurées gardées hors de la conversation, et les sous-agents au contexte propre (synthèse du guide d'Anthropic) [Prouvé].
Le contexte d'une tâche, couche par couche [Avis]. On le construit comme un empilement, du plus stable au plus variable. L'ordre compte aussi pour le coût (point 8).
Couche
Contenu
Change…
1. Consignes générales
rôle, règles, procédure de travail, façon de terminer
jamais pour une app
2. AGENTS.md généré
conventions, pièges du registre, documentation des seules capacités utilisées
à chaque version de l'app
3. Fiche de l'app
résumé lisible et types générés depuis la Description
à chaque version de l'app
4. Tâche et fiche d'avancement
ce qu'il faut faire, le critère de réussite, ce qui est déjà fait
à chaque tâche
5. Historique de la tâche
actions et observations
à chaque étape
Trois parades contre le gonflement de la couche 5 [Avis].
1.  Des sorties courtes par construction : les outils de l'usine résument (point 4).
2.  Masquer les vieilles observations plutôt que résumer : on garde la trace des actions, mais on remplace les anciennes sorties de commandes par une mention « sortie retirée ». SWE-agent le fait par des « processeurs d'historique » qui tronquent les vieilles observations (analyse de SWE-agent) [Prouvé]. Une étude de 2025 trouverait ce masquage aussi efficace qu'un résumé par IA, pour moins cher [À vérifier].
3.  Repartir à neuf quand une tâche s'enlise, avec un résumé écrit par l'orchestrateur, pas par l'agent.
3. Découper le travail : la vraie parade
Ce que fait Anthropic pour les agents qui travaillent des heures : une première session prépare l'environnement (un script de démarrage, un fichier d'avancement, un premier commit) ; chaque session suivante relit l'avancement et l'historique de git, prend une seule fonction dans une liste, la réalise, la vérifie et la commite (Anthropic, harnais des agents de longue durée) [Prouvé]. Le même article reconnaît que la compaction seule ne suffit pas : l'agent tombait à court de contexte au milieu d'une fonction, laissant la suivante à moitié faite et non documentée [Prouvé]. La liste de fonctions répondait aussi à un autre défaut : l'agent qui déclare trop tôt l'app terminée.
Votre version est plus solide sur un point [Avis]. Chez Anthropic, c'est l'agent qui coche ses fonctions comme réussies. Chez vous, la liste vient du planificateur, la fiche d'avancement est écrite par l'orchestrateur, et ce sont les juges qui cochent. L'agent ne peut ni oublier une tâche, ni se déclarer fini trop tôt.
Le réglage de la taille des tâches [Avis]. Trop grosse, la tâche pourrit son contexte ; trop petite, elle coûte en démarrages et produit des écrans incohérents entre eux. La bonne taille se mesure sur le banc : nombre d'étapes et taille du contexte en fin de tâche. Pas de sous-agents lancés par l'agent lui-même au début : l'orchestrateur joue déjà ce rôle, de façon traçable.
4. Les outils : l'interface entre l'agent et l'ordinateur
Les mesures de SWE-agent (2024). Une interface conçue pour le modèle résout 10,7 points de plus qu'un terminal brut. Sans la commande d'édition dédiée, le taux de réussite tombe de 18,0 % à 10,3 %. Un vérificateur intégré à l'édition refuse les modifications invalides et demande de recommencer, ce qui évite les erreurs en cascade (article SWE-agent) [Prouvé]. Les recherches sont plafonnées à 50 résultats, et une fenêtre de 100 lignes donnait le meilleur résultat (résumé de l'article) [Prouvé].
Nuance. Ces mesures datent de modèles de 2024. mini-swe-agent n'utilise que le terminal, et réussit bien avec les modèles récents. Les modèles ont progressé ; mais le principe d'un retour court et précis reste valable [Avis].
Règles pour chaque outil de la boîte [Avis].
• Une sortie bornée en taille, toujours, et qui dit quand elle coupe.
• Une sortie actionnable : fichier, ligne, message, classée par importance.
• Une sortie déterministe : la même situation donne le même texte.
• Une vérification automatique après chaque modification : la compilation des types sur les fichiers touchés, ajoutée à l'observation. C'est l'équivalent du vérificateur d'édition de SWE-agent.
• La description de l'outil fait partie des consignes : elle se teste sur le banc comme le reste.
5. Les consignes sont du code
• Des modèles versionnés avec des variables remplies par l'usine, comme les gabarits de mini-swe-agent. Leur empreinte entre dans celle de la construction.
• Une structure stable : rôle, contexte, règles absolues, méthode de travail (s'orienter, planifier court, réaliser, vérifier, terminer), format de fin, quelques exemples.
• La bonne altitude. Anthropic conseille des consignes ni vagues, ni écrites comme une cascade de cas particuliers fragiles, et quelques exemples variés plutôt qu'une longue liste de règles (synthèse du guide) [Prouvé].
• La règle la plus importante [Avis] : les consignes expliquent, la boîte impose. Aucune règle de sécurité ne repose sur le fait que l'agent obéisse. « Ne touche pas au cœur » est écrit dans les consignes pour qu'il ne perde pas de temps ; c'est le système de fichiers en lecture seule qui l'en empêche.
• Les textes du client sont des données : rangés dans un bloc délimité et étiqueté, jamais mêlés aux consignes.
• Le déterminisme n'existe pas. Beaucoup de modèles récents ne garantissent pas la même réponse deux fois. On ne compte pas dessus : on compte sur les juges, et on mesure la variance [Avis].
6. La boîte
La conception de l'agent local est la bonne : conteneur jetable, cœur en lecture seule, aucun réseau sauf le compteur, aucune clé dans la boîte. Trois ajouts :
• Le compteur existe tout fait. Le relais LiteLLM crée des clés virtuelles, chacune avec un budget maximal et une fenêtre de temps, et suit la dépense par clé (documentation LiteLLM) [Prouvé]. Une clé par tâche donne un budget par tâche. Il demande une base PostgreSQL, que vous avez déjà [Prouvé].
• Le durcissement ordinaire de Docker : utilisateur non administrateur, système de fichiers en lecture seule hors des zones permises, privilèges retirés, nombre de processus plafonné, réseau interne qui ne voit que le compteur [Avis].
• Plus tard seulement, un isolement renforcé (gVisor) si les apps manipulent des données sensibles [Avis].
7. La sécurité face à l'injection de consignes
L'état de l'art. Un article de 2025 (IBM, Invariant Labs, ETH Zurich, Google, Microsoft…) juge les agents généralistes difficiles à sécuriser, et propose six patrons qui restreignent volontairement ce qu'un agent peut faire. Dans le patron « planifier puis exécuter », le plan est fixé avant de toucher la moindre donnée non fiable ; une injection ne peut donc pas ajouter d'action au plan (Beurer-Kellner et al.) [Prouvé].
Votre usine applique déjà ces patrons [Avis] :
• Planifier puis exécuter : le planificateur, un programme sans IA, fixe les tâches avant que l'agent voie quoi que ce soit ; l'agent ne peut pas en ajouter.
• Une IA en quarantaine : les lecteurs lisent la demande brute, mais ne rendent que du JSON contrôlé strictement. Ce qu'ils produisent est de la donnée.
• La réduction du contexte : l'agent ne reçoit jamais la demande brute.
• La surface qui reste : les libellés et les citations de la Description, recopiés du client. Ils vont dans un bloc de données, et les juges vérifient les effets.
8. Le coût
• La mise en cache des consignes. Chez Anthropic, relire un préfixe déjà en cache coûte 0,1 fois le prix normal sur la plupart des modèles, et l'écrire coûte 1,25 fois (documentation Anthropic) [Prouvé]. D'où l'ordre des couches du point 2 : le stable d'abord. Conséquence heureuse : découper en conversations neuves ne fait pas perdre le cache, puisque les couches 1 à 3 restent identiques d'une tâche à l'autre, tant que les tâches s'enchaînent dans le délai du cache [Avis].
• Le compteur fait foi, pas le calcul de l'agent. mini-swe-agent a dû corriger un cas où des appels facturés mais mal formés n'étaient pas comptés dans la limite (versions) [Prouvé].
• Un modèle moins cher pour les petites tâches, si le banc montre qu'il suffit. La règle « même modèle » ne vaut que pour comparer des moteurs [Avis].
9. La fiabilité
• Toutes les conditions d'arrêt branchées : étapes, coût, durée, erreurs de format répétées, et signature de boucle.
• Distinguer la panne du modèle de l'échec de l'agent. Une erreur de l'API se relance après une attente croissante ; elle se classe « environnement », pas « l'agent a échoué ».
• Enregistrer la trajectoire après chaque étape, comme le fait SWE-agent : une coupure ne perd rien.
• Une tâche commence d'un commit et rend un commit, ou rien. Jamais un état à moitié écrit.
10. Évaluer l'agent
• Le banc des moteurs de l'agent local, avec chaque tâche jouée plusieurs fois : un seul passage ne dit rien de la variance.
• Toute modification passe le banc : consignes, modèle, moteur, outils. Une régression bloque la modification.
• Une partie du banc reste cachée, sinon on finit par régler les consignes sur le banc lui-même.
• L'auto-évaluation de l'agent ne compte pas. Seuls les juges décident. C'est aussi ce qu'a appris Anthropic avec ses agents qui se déclaraient finis trop tôt.
Les juges
Un juge vaut ce que valent quatre choses : d'où il tire la bonne réponse, les situations qu'il essaie, sa stabilité, et la clarté de ce qu'il rend. La conception de l'agent local couvre bien la structure (§5 de son texte). Voici ce que l'état de l'art ajoute.
1. D'où vient la bonne réponse : cinq sortes d'oracles
Oracle
Principe
Exemple dans l'usine
Spécification exécutable
les attentes se calculent depuis le contrat
chaque case de la matrice ; chaque parcours
Propriétés
une règle qui doit rester vraie pour toutes les entrées
« personne ne voit une fiche hors de son périmètre », quelles que soient les données
Modèle
un modèle simple du comportement attendu, comparé à l'app après une suite d'actions
le circuit d'états et la matrice sont déjà ce modèle
Relation métamorphique
deux exécutions liées par une règle connue
doubler une quantité double un montant ; filtrer puis compter donne au plus le total
Différentiel
deux réalisations indépendantes doivent s'accorder
le cœur assemblé et une version d'agent ; une formule évaluée par un interpréteur de référence et par le code de l'app
Les tests par propriétés, concrètement. fast-check, pour TypeScript, génère des centaines d'entrées, réduit automatiquement un échec à son plus petit contre-exemple, et donne une graine qui permet de le rejouer exactement (guide fast-check) [Prouvé]. Il sait aussi faire des tests par modèle : on décrit les commandes permises et un modèle du comportement attendu, et il explore les suites d'opérations, là où se cachent les défauts qui n'apparaissent qu'après un certain enchaînement (fast-check) [Prouvé].
Pourquoi c'est taillé pour votre usine [Avis]. Votre matrice et vos circuits sont un modèle à états. Un juge par modèle tirerait au hasard des suites d'actions faites par des rôles différents (créer, faire passer une étape, retirer un rôle, modifier), et comparerait la base au modèle après chaque action. C'est exactement la famille de défauts que votre juge des règles rate aujourd'hui : modifier ses fiches après avoir perdu son rôle. Un juge par suites d'actions la trouverait par construction.
2. Les situations essayées : les données d'essai
• Générées depuis la Description, pour couvrir chaque case de la matrice et chaque état d'un circuit (l'agent local le décrit bien).
• Des combinaisons par paires quand les dimensions se multiplient (rôle × état × lien × valeur limite) : on couvre chaque paire de valeurs au moins une fois, sans tout combiner [Avis].
• Une graine enregistrée pour toute génération aléatoire : un échec se rejoue à l'identique.
• Une base neuve à chaque passage, copiée d'une base modèle : c'est rapide avec les bases modèles de PostgreSQL.
3. La stabilité : un juge qui hésite est un juge disqualifié
Le problème est massif. Un test instable est un test qui réussit et échoue sur le même code. Chez Google, près de 16 % des 4,2 millions de tests montraient une instabilité, et entre 2 et 16 % du calcul d'intégration continue servait à relancer des tests instables (Lam et al., citant Micco) [Prouvé]. Pour vous, c'est pire : un verdict instable fait tourner l'agent en rond sur un défaut qui n'existe pas.
Les parades [Avis, sauf mention].
• Jamais d'attente fixe : on attend l'élément, pas une durée.
• Une horloge figée. Playwright remplace les fonctions de temps du navigateur par une horloge contrôlée ; il faut l'installer avant de charger la page pour que l'app la voie (guide de l'horloge Playwright) [Prouvé]. Indispensable pour tout ce qui touche aux dates : échéances, calendriers, relances.
• Un fuseau horaire et une langue fixés, une base neuve, des services extérieurs remplacés par leurs doublures.
• La règle de verdict : relancer un juge n'est permis que pour classer une panne d'environnement, et la relance est inscrite au rapport. On ne relance jamais « jusqu'à ce que ça passe ».
• La mesure : chaque juge est joué plusieurs fois sur les témoins. Une seule hésitation, et il est mis à l'écart jusqu'à correction.
4. La vitesse
• Du moins cher au plus cher, et arrêt dès qu'une famille critique échoue.
• En parallèle, un contexte de navigateur par rôle, une base par passage.
• Un budget de temps par famille, mesuré à chaque version du juge. Un juge qui ralentit est une régression.
5. Ce qu'un juge rend
• Un verdict par exigence, relié à son identifiant stable dans le contrat. Une exigence non jugée est dite « non jugée », jamais passée sous silence.
• Une preuve rejouable : les données, la graine, les actions, l'attendu, l'observé.
• Un format fixe et versionné, que l'orchestrateur lit sans interpréter de texte. Pour les contrôles mécaniques (analyse de code, secrets, dépendances), un format standard d'outils d'analyse existe, SARIF [À vérifier] pour le détail.
6. Les juges sont la constitution de l'usine
Les juges sont le seul code de l'usine qu'Arthur doit relire ligne par ligne. Tout le reste peut se tromper, puisque les juges le rattrapent ; une erreur de juge, elle, passe en silence. Ils ont donc leurs propres tests, leur preuve par sabotage, une version, et une requalification à chaque changement [Avis].
Les sabotages et la qualification des juges
1. Les familles de sabotages
Les quatre familles de l'agent local sont les bonnes (contrat inversé, règle du schéma mutée, panne injectée, agent saboteur). J'en ajoute deux [Avis] :
• Saboter l'environnement : changer le fuseau horaire, avancer l'horloge au-delà d'une échéance, vider un service simulé. Ça qualifie les juges de tout ce qui touche au temps.
• Saboter les données : une fiche orpheline, un champ facultatif vide, une valeur limite. Ça qualifie la couverture des données d'essai.
2. Les outils existent
• StrykerJS fait le test par mutation pour JavaScript et TypeScript : il plante de petits défauts dans le code et relance les tests ; un défaut qui survit révèle un test faible. Il calcule un score de mutation, et les mutants équivalents survivent par nature : ils demandent un tri humain (StrykerJS) [Prouvé]. mutmut fait de même pour Python (même source) [Prouvé].
• Ce n'est pas seulement pour les apps. Le calculateur de la matrice, les traducteurs et l'orchestrateur sont du code Python dont dépend toute l'usine. Le test par mutation qualifie leurs propres tests. Une usine qui exige des preuves de ses apps doit les exiger de ses propres pièces [Avis].
3. La validité d'un sabotage
La réponse précédente à l'agent local en traite (validation croisée, sabotage du contrat valide par construction, revue d'un échantillon). En résumé : un sabotage ne compte que si un autre instrument que le juge qualifié montre que le comportement a changé, et le dossier dit « valides à X % près ».
4. Le banc de qualification
Ce qu'on mesure
Comment
Seuil
Détection
sabotages attrapés, par famille
fixé avant de lancer, par famille
Faux positifs
témoins conformes refusés
zéro sur les témoins de référence
Stabilité
même verdict sur plusieurs passages
zéro hésitation
Vitesse
durée par famille
budget fixé
Limites
familles connues comme non détectées
écrites dans le dossier, jamais cachées
Les seuils se fixent avant de lancer la qualification, jamais après avoir vu les résultats [Avis].
L'assembleur comme compilateur
L'assembleur est un compilateur : la Description entre, le cœur de l'app sort. Les compilateurs sont un domaine que l'informatique maîtrise depuis longtemps ; il faut en reprendre les habitudes.
1. Une chaîne en trois temps, sans raccourci
1.  Lire et contrôler la Description (déjà fait par pydantic).
2.  Calculer une représentation intermédiaire : la matrice et le modèle normalisé de l'app. Toutes les décisions sont prises ici, une seule fois.
3.  Émettre : chaque émetteur (schéma, notice d'écran, données, types, parcours calculés) est une fonction de la représentation intermédiaire vers des fichiers. Aucun émetteur ne lit la sortie d'un autre : c'est votre règle « une seule source par concept », appliquée au code de l'usine [Avis].
2. Générer du code avec des structures, pas avec du texte recollé
• Pour le schéma ZenStack. Le paquet @zenstackhq/language contient l'analyseur du langage ZModel, construit avec Langium, et produit un arbre syntaxique (dépôt ZenStack v3) [Prouvé]. Il exporte aussi un générateur qui réécrit un arbre ZModel en texte (dépôt ZenStack v3) [Prouvé]. L'usine peut donc construire le schéma comme un arbre, puis l'imprimer ; ou au minimum relire tout schéma produit avec l'analyseur officiel. C'est aussi ce qui permet de muter les règles proprement, pour les sabotages.
• Pour le TypeScript. ts-morph enveloppe l'API du compilateur TypeScript : on décrit le code à produire par des objets, sans manipuler de chaînes (ts-morph) [Prouvé]. Il ne met pas le code en forme : on le passe ensuite dans Prettier (ts-morph) [Prouvé].
• Quand un gabarit texte suffit (un fichier simple, peu de variables), il reste acceptable, à deux conditions : ses variables sont typées, et le fichier produit est relu par l'outil officiel du langage [Avis].
3. Une sortie stable, octet pour octet
• Même entrée, même sortie, au caractère près : ordre de tri stable, identifiants stables, aucune date ni valeur aléatoire dans les fichiers produits. On le vérifie en générant deux fois [Avis].
• Un en-tête dans chaque fichier produit : « généré, ne pas modifier », avec l'empreinte de sa source. Le manifeste de propriété s'appuie dessus.
• Des fichiers de référence pour chaque exemple : toute modification de l'assembleur montre exactement ce qui change dans chaque app, et ce changement se relit comme une modification de code. On parle souvent de tests d'approbation [Avis].
4. Tester le calculateur par ses doctrines
Vos doctrines sont des propriétés, au sens des tests par propriétés [Avis] :
• « aucune règle n'accorde la suppression si la Description ne la demande pas » ;
• « "connecté" ne veut jamais dire "toute personne connectée" » ;
• « on ne désigne jamais une fiche qu'on ne peut pas voir ».
Un générateur de Descriptions aléatoires mais valides vérifierait chaque doctrine sur des milliers de cas, au lieu de 14 matrices attendues. Hypothesis, pour Python, sait construire des données à partir de modèles typés [À vérifier]. Et le test par mutation (mutmut) dirait si ces tests voient vraiment une doctrine cassée.
5. Les points d'extension et la place de l'agent
Le patron Generation Gap, les points d'extension typés et la découverte par registre, décrits par l'agent local, sont la bonne architecture. Un ajout : les types générés depuis la Description sont le contrat entre le cœur et sur-mesure/. Le code de l'agent est compilé contre eux ; c'est le compilateur, pas un juge, qui signale la première incompatibilité après une évolution [Avis].
6. Les migrations
ZenStack v3 confie les migrations de la base à Prisma Migrate. Ses commandes zen migrate sont de simples enveloppes : elles produisent un schéma Prisma depuis le ZModel, puis lancent la commande Prisma correspondante (doc ZenStack) [Prouvé]. L'assembleur produit donc le ZModel ; l'outil établi produit la migration de structure ; l'usine n'écrit elle-même que les migrations de données (section suivante).
Les autres mécanismes
L'orchestrateur
La conception de l'agent local (machine à états, une ligne par passage, étapes rejouables, attentes humaines explicites) est la bonne. Quatre techniques la rendent solide [Avis] :
• Les transitions permises sont une table. Chaque passage d'état est vérifié contre elle ; un passage non prévu est refusé et inscrit. On ne code pas les états en dur dans des conditions éparpillées.
• Écrire avant d'agir. L'orchestrateur inscrit « je lance l'étape X avec telles entrées » avant de la lancer, puis « terminée, voici la sortie ». Au redémarrage, une étape lancée mais jamais terminée se reconnaît et se rejoue.
• Un seul chantier par app à la fois, garanti par un verrou de PostgreSQL. Deux constructions de la même app en parallèle se marcheraient dessus.
• La preuve par coupures. On tue l'orchestrateur à des moments tirés au hasard, on le relance, et l'on vérifie trois propriétés : il reprend au bon endroit, il ne repaie rien, et les verdicts finaux sont les mêmes.
La compréhension et le miroir
• Le format garanti par le modèle. Les sorties structurées d'Anthropic contraignent la génération pour qu'elle respecte un schéma JSON : la réponse est toujours analysable, sans relance pour cause de format (doc Anthropic) [Prouvé]. Deux limites : seule une partie de JSON Schema est prise en charge, et changer la structure du schéma invalide le cache de la grammaire (même doc) [Prouvé].
• La forme n'est pas la vérité [Avis]. Le format garanti supprime les erreurs de forme, pas les erreurs de sens. Votre contrôle strict reste nécessaire pour ce qui compte : citations recopiées mot pour mot, identifiants connus, cohérence entre lecteurs.
• Mesurer les lecteurs comme un modèle d'apprentissage : un jeu de briefs aux réponses attendues, figé, rejoué à chaque changement de consignes ou de modèle, avec un score par lecteur. Votre étude E5 en est le début.
• Le désaccord comme détecteur d'ambiguïté, en amont [Avis]. Faire lire le même brief deux fois (ou par deux modèles) et comparer les Descriptions coûte quelques centimes. Un désaccord devient une question du miroir. C'est l'idée de ClarifyGPT, appliquée à la lecture plutôt qu'à la construction : bien moins cher que construire deux apps.
• Le miroir a lui aussi ses propriétés à vérifier : chaque case de la matrice apparaît dans une phrase et une seule ; chaque question posée correspond à un choix réel dans la Description.
L'évolution et la flotte
• Le patron « étendre, migrer, contracter ». Un changement incompatible se fait en trois phases séparées : on ajoute le nouveau à côté de l'ancien, on migre, puis on retire l'ancien quand plus rien ne l'utilise. La plupart des refontes de bases de données suivent ce patron (Martin Fowler) [Prouvé]. Pour de petites apps à une seule instance, on peut accepter une courte interruption ; mais la règle reste : jamais une suppression dans la même étape que le code qui en dépend, et un renommage se fait par ajout, copie, puis retrait plus tard [Avis].
• Chaque opération d'évolution porte sa classe de risque : sans perte, ou avec perte (des valeurs ou des fiches disparaissent). Une opération avec perte exige une décision explicite du client dans le miroir de l'évolution [Avis].
• Le format de la Description a ses fonctions de mise à niveau, testées sur toutes les Descriptions déjà enregistrées, à chaque nouveau vocabulaire (l'agent local le signale ; c'est un piège classique).
• La répétition sur une copie sert deux fois [Avis]. Restaurer la dernière sauvegarde dans une base d'essai, migrer, lancer les juges, comparer les comptes et les empreintes : c'est à la fois la répétition de la migration et la preuve que la sauvegarde se restaure.
• La flotte se met à jour app par app, en commençant par une app d'essai, et s'arrête au premier échec.
La livraison
Rien à ajouter à la conception de l'agent local, sinon l'ordre : vrais comptes, déploiement d'un seul commit jugé (vérifié par son empreinte), sauvegardes restaurées au moins une fois, surveillance, puis sécurité au-delà des droits. Tout cela attend le premier vrai client.
Les traces
• Un vocabulaire standard existe. Les conventions d'OpenTelemetry pour l'IA générative donnent les mêmes noms aux appels de modèle, aux jetons, aux appels d'outils et aux exécutions d'agent, quel que soit le fournisseur, sous l'espace de noms gen_ai (SigNoz) [Prouvé]. Elles sont encore au statut « en développement » : il faut figer leur version (Lyzr) [Prouvé].
• Ma recommandation [Avis] : nommer les champs de votre table de traces d'après ces conventions, sans forcément installer toute la chaîne OpenTelemetry au début. Le jour où vous voudrez un outil de visualisation, vos traces seront déjà lisibles.
• La mémoire de l'usine : chaque échec récurrent, reconnu par sa signature, devient une correction de l'assembleur, un juge ou une ligne de pièges dans l'AGENTS.md (conception de l'agent local).
Une seule recette pour toutes les capacités
Aucune capacité n'est un cas spécial. Le dossier décrit par l'agent local (vocabulaire, contrat, pièces fixes, documentation pour l'agent, doublure locale, juges, sabotages, preuve, état calculé) s'applique à toutes. Le tableau le montre sur six capacités ; tout est [Avis].
Capacité
Ce qu'elle ajoute à la Description
Pièce fixe dans le cœur
Ce que fait l'agent
D'où les juges tirent la bonne réponse
Doublure pour les essais
Tableaux de bord
des indicateurs : quoi compter ou additionner, sur quelles fiches, pour quel rôle
aucune : les droits existants s'appliquent
les graphiques et la mise en page
l'agrégat recalculé directement dans la base, avec les droits du rôle
aucune
Calendrier et planning
des créneaux, des durées, des conflits interdits
la règle de non-chevauchement, si elle touche aux données
la vue calendrier
les créneaux attendus, avec une horloge et un fuseau figés
l'horloge de Playwright
Fichiers joints
un champ « fichier », ses types et tailles permis
le stockage et ses droits (qui lit quel fichier)
le téléversement et l'aperçu à l'écran
un fichier déposé par A est illisible pour B, à l'écran comme par l'adresse directe
un stockage local
Calculs et montants
des formules, des unités, des arrondis
l'évaluation de la formule, si le montant engage de l'argent
l'affichage et la saisie
un interpréteur de référence de la formule ; des propriétés (doubler la quantité double le montant)
aucune
Recherche et filtres
les champs cherchables et filtrables
aucune
la barre de recherche et les filtres
les ensembles de résultats attendus, jamais une fiche hors des droits
aucune
Notifications (e-mail, SMS…)
un événement, un destinataire, un contenu
l'intention d'envoi rangée dans la base
le gabarit du message
le bon destinataire, le bon contenu, une seule fois
une boîte d'e-mails de test
Ce que montre le tableau
• Toutes les capacités se ressemblent : un peu de vocabulaire, parfois une pièce fixe là où il y a des droits ou de l'argent, le reste confié à l'agent, et des juges qui lisent la source.
• Les pièces fixes n'apparaissent que là où une erreur fuirait en silence : les droits sur un fichier, un montant qui engage de l'argent, une intention d'envoi qu'on ne doit pas perdre. C'est la règle des trois zones, appliquée capacité par capacité.
Par où commencer ?
Le choix vous appartient. Votre corpus donne la fréquence : des tableaux de bord dans environ 13 briefs sur 33, un calendrier dans 11, selon l'agent local. Je proposerais les tableaux de bord en premier, pour quatre raisons [Avis] :
1.  c'est la capacité la plus demandée dans vos vrais briefs ;
2.  elle ne touche pas aux droits en écriture : le risque est faible ;
3.  elle est presque entièrement faite par l'agent : c'est le meilleur premier test de « l'agent construit la périphérie, les juges vérifient » ;
4.  son oracle est simple et fiable : recalculer l'agrégat dans la base.
Le calendrier viendrait ensuite : plus fréquent qu'il n'y paraît, et le meilleur exercice pour les juges qui dépendent du temps. Les notifications passent au rang d'une capacité ordinaire, à traiter quand les briefs la demandent.
Rendre l'usine visible et manipulable
Le terme. Un jumeau numérique, au sens strict, est une copie numérique d'un système réel, nourrie en continu par ses vraies données. On s'en sert pour le regarder fonctionner, simuler un changement avant de le faire, et prévoir. Pour une usine logicielle, ça donne quatre niveaux [Avis] :
Niveau
Ce qu'on voit ou fait
D'où viennent les données
Quand
Voir
une salle de contrôle en direct : constructions en cours, étape de chacune, tâche et commandes de l'agent, verdicts des juges, coût
la table de traces, lue en continu
après le squelette qui marche
Rejouer
revoir une construction passée comme un film
les trajectoires enregistrées de l'agent et les événements de l'orchestrateur
en même temps
Agir
mettre en pause, reprendre, relancer une tâche, décider après deux corrections ratées, répondre au miroir
des commandes typées envoyées à l'orchestrateur
quand les décisions humaines deviennent fréquentes
Prévoir
estimer la durée et le coût d'une construction avant de la lancer
l'historique des constructions
bien plus tard
La règle : la vue lit, elle ne façonne pas
Le premier essai avec Temporal donnait une activité à chaque agent, surtout pour voir les agents interagir. L'erreur n'était pas l'envie de voir ; c'était de laisser la visualisation dicter l'architecture [Avis].
• L'usine écrit ses événements dans la table de traces ; la vue ne fait que les lire. Changer la vue ne touche jamais l'usine.
• Quand la vue devient manipulable, elle envoie des commandes typées à l'orchestrateur, et c'est lui qui décide, exactement comme le miroir pour le client. Une commande refusée par l'orchestrateur est inscrite, jamais forcée.
• Montrer la réalité, pas une mise en scène. L'architecture retenue compte peu d'agents (les lecteurs et l'agent constructeur). La vue montrera surtout un programme qui enchaîne des étapes et un agent qui avance tâche par tâche. C'est déjà très vivant.
Ce qu'il faut faire dès maintenant
Rien dans l'architecture : seulement des événements complets dès le premier jour [Avis].
• Pour chaque étape : la construction, l'étape, l'état, le début et la fin, les empreintes, le coût.
• Pour chaque pas de l'agent : la commande lancée, les fichiers touchés, la taille du contexte.
• Pour chaque juge : chaque verdict, avec son exigence et sa preuve.
• Pour chaque décision humaine : qui, quoi, quand, et la commande envoyée.
Ne pas tout construire
• Pour le détail des agents, un outil existe. Langfuse affiche chaque exécution sous forme d'arbre, de frise temporelle avec la durée et le coût de chaque étape, et de graphe du déroulement (documentation Langfuse) [Prouvé]. Toutes ses fonctions sont sous licence MIT depuis juin 2025 et il s'installe chez soi ; ClickHouse l'a racheté en janvier 2026 en annonçant qu'il resterait libre et installable chez soi (Langfuse) [Prouvé].
• Pour la vue d'ensemble de l'usine (constructions, étapes, verdicts, décisions), une page à soi, qui lit la table de traces [Avis].
• Le plaisir de voir l'usine travailler compte aussi : pour déboguer, pour rester motivé, et plus tard pour la montrer.
La confidentialité des données
Une usine locale ne protège pas les données qu'elle envoie au modèle. Claude Code tourne sur la machine, mais pour parler au modèle il envoie sur le réseau toutes les consignes et toutes les réponses (documentation Claude Code) [Prouvé]. Tout ce que l'usine donne au modèle (la demande du client, la Description, le code, les messages d'erreur) part chez le fournisseur, hors du Québec. C'est vrai pour tout fournisseur de modèle hébergé.
Ce que le fournisseur en fait dépend du contrat
Type de compte
Entraînement des modèles
Conservation
Source
Abonnement Free, Pro ou Max, y compris Claude Code avec ces comptes
oui si le réglage d'entraînement est activé
jusqu'à 5 ans si le réglage est activé, 30 jours sinon
Anthropic · Claude Code [Prouvé]
API, Team, Enterprise
non par défaut
30 jours en standard ; option sans conservation
Claude Code [Prouvé]
Exception : Fable 5 et Mythos 5
non par défaut
30 jours imposés, pas d'option sans conservation
Voibe [Prouvé]
La loi québécoise
Avant de communiquer des renseignements personnels à l'extérieur du Québec, l'article 17 de la Loi 25 exige une évaluation des facteurs relatifs à la vie privée, qui vérifie que la destination offre une protection adéquate (SiLaw) [Prouvé]. L'hébergement sur des serveurs hors du Québec compte comme une telle communication (Fasken) [Prouvé]. Je ne suis pas juriste : à faire valider avant le premier vrai client.
La parade tient dans l'architecture : aucune donnée réelle dans l'usine
1.  La demande du client est anonymisée automatiquement avant les lecteurs : noms, courriels et téléphones remplacés. C'est une petite étape de programme, sans IA [Avis].
2.  L'agent ne travaille qu'avec des données de démonstration (déjà la règle).
3.  Les vraies données du client ne vivent que dans l'app livrée, jamais dans l'usine.
4.  Ce que le modèle voit se réduit à la description d'un processus métier, sans personne identifiable. Une information d'affaires confidentielle reste possible : elle relève du contrat avec le client et des conditions commerciales du fournisseur.
Concrètement
• Pendant le développement de l'usine, avec l'abonnement : réglage d'entraînement désactivé, et seulement des demandes fictives ou anonymisées [Avis].
• Pour de vrais clients : l'API au minimum, sous conditions commerciales, et une mention dans le contrat du client que sa demande passe par un fournisseur d'IA.
• En repli pour les cas les plus sensibles : un modèle local, dont la qualité sera à mesurer sur le banc.
Le design des apps
Ce n'est pas l'étape d'aujourd'hui, mais quelques décisions coûtent presque rien maintenant et beaucoup plus tard.
Deux questions à ne pas confondre
• L'app est-elle utilisable ? Clarté, cohérence, accessibilité, affichage sur téléphone. Ça se mesure en partie, donc ça peut avoir des juges.
• Est-elle belle, et à l'image du client ? C'est subjectif : aucun juge fiable n'existe. Ça se règle par la validation du client, pas par un verdict.
Ce qu'il faut décider dès maintenant
Tout est [Avis].
1.  Un système de design comme source unique du style : couleurs, typographie, espacements, arrondis, et les composants de shadcn/ui, déjà dans la pile. Chaque écran, posé par l'assembleur ou écrit par l'agent, n'utilise que lui. Une règle de lint refuse toute couleur ou taille hors du système, et l'agent ne peut pas installer d'autre bibliothèque d'interface. La cohérence est garantie, même avec plusieurs auteurs.
2.  L'identité du client fait partie de la Description : logo, couleurs, ton des textes. Elle se valide dans le miroir comme le reste. Changer d'image, c'est changer des valeurs, pas du code.
3.  Montrer avant de construire. Le miroir présente des aperçus des écrans, tirés de la Description et du système de design. Le client corrige l'apparence au moment où ça ne coûte rien.
4.  Les juges font des captures d'écran dès le premier jour. Presque gratuit, et ça permettra plus tard de comparer un écran avant et après une évolution, et de faire relire l'apparence.
5.  Une IA peut donner son avis sur l'apparence, jamais un verdict. C'est la règle générale de l'usine : une IA n'est jamais l'oracle de ce qui a été produit.
6.  Seul ce qui se mesure devient un juge : contraste et étiquettes accessibles, affichage sans défilement horizontal sur téléphone, respect du système de design, temps de chargement.
Le lien avec le reste de l'usine
• Le contrat d'accessibilité et le design vont ensemble : des éléments bien nommés rendent l'app à la fois accessible et testable par le moteur de parcours.
• Le design sur mesure est un « bord » au sens de la règle des trois zones : l'agent peut le faire, à l'intérieur du système de design, et ses écrans passent les mêmes juges.
Une limite à accepter
Par défaut, les apps seront propres et cohérentes, mais elles se ressembleront. La différence viendra des couleurs, de la typographie et de quelques mises en page. Pour des apps de gestion, c'est un compromis raisonnable ; un client qui veut un design unique en fait une demande de « bord », chiffrée à part.
Développer sans aller à l'aveugle
L'agent local propose la bonne méthode : un squelette qui marche de bout en bout d'abord, très mince, puis on épaissit chaque mécanisme en mesurant. J'ajoute un étage avant : les essais jetables.
1. D'abord, des essais jetables sur les risques qui peuvent tout changer
Un essai jetable est un petit programme écrit pour répondre à une question, en un ou deux jours, puis jeté. Il ne fait pas partie de l'usine. Trois questions méritent ce traitement avant toute construction [Avis] :
Question
Essai
Ce qui serait une mauvaise nouvelle
La boîte tient-elle sur ce poste ?
installer Docker Engine directement dans WSL2, puis créer et détruire la boîte 20 fois
des pannes ou des lenteurs qui imposent un autre poste ou un serveur
Un moteur ouvert construit-il assez bien ?
mini-swe-agent dans la boîte, derrière le compteur LiteLLM, sur une seule tâche de l'app A
une qualité nettement inférieure à Claude Code, ou un coût hors budget
Le moteur de parcours tient-il sur des écrans d'agent ?
jouer quelques parcours sur les apps A, A0 et B déjà construites
trop d'échecs de navigation : le contrat d'accessibilité devient prioritaire
Docker Engine s'installe directement dans une distribution Ubuntu de WSL2, sans Docker Desktop, et démarre tout seul si l'on active systemd dans WSL (guide WSL2) [Prouvé]. Les fichiers doivent rester dans le système de fichiers de WSL, pas dans les dossiers de Windows, pour de bonnes performances (même guide) [Prouvé].
2. Ensuite, le squelette qui marche
Une seule commande, sur l'app la plus simple, qui enchaîne tout en version minimale [Avis] :
1.  l'image figée ;
2.  la boîte ;
3.  mini-swe-agent derrière la prise unique ;
4.  une tâche d'agent (par exemple enrichir un écran de liste) ;
5.  les contrôles mécaniques ;
6.  les juges existants et la sonde ;
7.  une boucle de correction ;
8.  une ligne de traces.
La démonstration : la commande va au bout, et la relancer donne les mêmes verdicts sans rien repayer.
3. Puis on épaissit, un mécanisme à la fois
1.  Le banc des moteurs (trois ou quatre tâches) et la qualification du noyau de juges, sabotages et témoins.
2.  Le moteur de parcours, détaché du squelette, avec des données d'essai générées.
3.  La première capacité de bout en bout (je propose les tableaux de bord).
4.  L'évolution : opérations typées, répétition sur une copie.
5.  La livraison, au premier vrai client.
Chaque étape suit l'ordre de l'agent local : une fiche courte validée par Arthur, la preuve écrite d'abord, le code, puis une mesure.
4. Ce qu'on ne construit pas encore
Pour ne pas se disperser [Avis] :
• la compression automatique du contexte, tant que la courbe de taille du contexte ne la réclame pas ;
• DBOS ou un autre moteur de flux, tant qu'un seul processus suffit ;
• un isolement renforcé (gVisor), tant qu'aucune donnée sensible n'est en jeu ;
• toute la chaîne OpenTelemetry : la table de traces suffit, avec des noms compatibles ;
• le choix automatique du modèle selon la tâche, tant que le banc n'a pas montré qu'un modèle moins cher suffit.
Les points « À vérifier » de l'agent local
Point (§15 de son texte)
Résultat
Source
mini-swe-agent tourne dans Docker
Confirmé
trajectoires publiques
mini-swe-agent a des limites d'étapes et de coût
Confirmé, avec aussi une limite de durée et un arrêt après 3 erreurs de format consécutives
code source
mini-swe-agent enregistre sa trajectoire
Confirmé : messages, coût, nombre d'appels, format versionné
code source
mini-swe-agent utilise LiteLLM
Confirmé (il a dû exclure deux versions compromises de LiteLLM)
versions
mini-swe-agent coupe les sorties trop longues
Non vérifié : je ne l'ai pas trouvé dans le code consulté
—
LiteLLM en relais : budget par clé, coupure, mesure du coût
Confirmé : budget maximal par clé et par fenêtre de temps, dépense suivie par clé ; demande une base PostgreSQL
doc LiteLLM
Le guide d'Anthropic sur les agents de longue durée
Confirmé : session de préparation, fichier d'avancement, liste de fonctions, une fonction par session, commits
Anthropic
SWE-agent : la qualité des outils compte
Confirmé, avec les chiffres
article
Le parseur de ZenStack comme bibliothèque
Confirmé : @zenstackhq/language, construit avec Langium, avec un générateur de texte
dépôt ZenStack v3
Les migrations de ZenStack v3
Confirmé : enveloppes autour de Prisma Migrate
doc ZenStack
Docker Engine dans WSL2 sans Docker Desktop
Confirmé : installation directe, démarrage par systemd
guide
Sources
Agents, contexte et outils
• Anthropic : harnais des agents de longue durée
• Synthèse du guide d'Anthropic sur l'ingénierie du contexte · autre synthèse
• Chroma : Context Rot
• SWE-agent : interfaces entre l'agent et l'ordinateur (arXiv) · résumé · analyse détaillée
• mini-swe-agent : code de l'agent par défaut · versions · trajectoires publiques
• LiteLLM : clés virtuelles et budgets
• Anthropic : mise en cache des consignes
• Anthropic : sorties structurées
• Beurer-Kellner et al. : patrons contre l'injection de consignes (arXiv)
Juges et tests
• fast-check : guide · fast-check : documentation
• Lam et al. : tests instables (citant Google)
• Horloge de Playwright
• StrykerJS et mutmut
Assembleur, évolution, traces
• ZenStack v3 : paquet du langage · générateur de ZModel · migrations
• ts-morph · ts-morph et Prettier
• Martin Fowler : Parallel Change
• Conventions OpenTelemetry pour l'IA générative (SigNoz) · statut des conventions (Lyzr)
Poste de travail
• Docker Engine dans WSL2 sans Docker Desktop
Visibilité et confidentialité
• Langfuse : documentation · licence et rachat par ClickHouse
• Claude Code : usage des données
• Anthropic : mise à jour des conditions grand public
• Voibe : conservation des données de l'API Claude
• SiLaw : Loi 25 et évaluation des facteurs relatifs à la vie privée · Fasken : hébergement hors du Québec


mais une petite question : quelle est la capacité de claude code ou d un agenti cli aussi performant de mettre en place ou developper ce system entier : pas besoin de tres long developpement .

Vérification du sens d'une formulation ambiguë
Réponse courte : Claude Code peut écrire l’essentiel du code de l’usine, et vite. Ce n’est pas ça qui limitera la vitesse.

Ce qu’il fait bien. Ton propre projet le montre : l’usine 2 (environ 6 800 lignes, avec ses preuves) a été écrite avec l’agent local en quelques semaines, et une app complète comme A0 en une heure. Le squelette qui marche est probablement une affaire de jours à deux semaines de sessions (estimation, pas mesure).

Ce qu’il ne peut pas faire à ta place :

Décider : quoi construire en premier, les seuils de réussite, ce qui compte comme critique.
Se juger lui-même : c’est la règle de l’usine, appliquée à l’usine. Les juges écrits par l’agent doivent être relus par toi, ligne par ligne ; c’est le seul code où une erreur passe en silence.
Remplacer l’expérience : mesurer la variance, la stabilité des juges ou le coût réel prend du temps calendaire, pas du temps de frappe.
Travailler longtemps sans toi : les limites de l’abonnement et la qualité qui baisse sur les longues sessions imposent des sessions courtes, une tâche à la fois.
Le vrai risque n’est pas qu’il soit trop lent, mais trop rapide. Un agent produit facilement beaucoup de code et ajoute de la complexité. L’usine 1 avait 23 000 lignes d’orchestration, et c’est ce code qui cassait. Les garde-fous sont déjà dans ta méthode : une fiche courte validée avant chaque mécanisme, la preuve écrite d’abord, un mécanisme à la fois.

En une phrase : ton rôle dans la construction de l’usine est exactement celui du miroir et des juges dans l’usine. Claude Code construit ; toi, tu fixes le contrat et tu vérifies. La vitesse dépendra surtout de ton temps de relecture et des expériences, pas de lui.