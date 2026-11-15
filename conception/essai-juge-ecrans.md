# L'essai du juge d'écrans : un juge sans IA s'y retrouve-t-il dans des écrans faits par un agent ?

> **Taille** : moyen (essai jetable) · **Statut** : relu deux fois, corrigé ; **« go » d'Arthur le 14 nov** ·
> **Indépendant** des deux autres essais
> **Dates** : écrit le 14 nov 2026 · relu le 14 nov · corrigé le 14 nov · seconde lecture le 14 nov

## Avant : la conception

### 1. En mots simples
- **Ce que c'est.** Un **inspecteur d'écrans** automatique. On lui donne des « parcours », comme on donnerait une
  mission à un testeur humain : « le gérant confirme le devis ESSAI-7Q2 », « le membre de l'équipe ne doit pas pouvoir
  confirmer un devis ». Il ouvre l'app dans un navigateur, se connecte comme la bonne personne, cherche les boutons et
  les liens **par ce qui est écrit dessus**, comme le ferait un lecteur d'écran pour malvoyant. Il agit, puis vérifie
  ce que l'écran montre **et** ce que la base de données a enregistré. Il n'utilise aucune IA, pour ne jamais deviner.
- **Pourquoi on le fait.** Aujourd'hui, nos juges d'écrans ne savent vérifier que les écrans de notre propre squelette,
  dont ils connaissent la structure. Quand l'artisan IA construira des écrans, il faudra un inspecteur qui ne dépende
  pas de la façon dont ils sont faits. Sans lui, on ne pourrait pas dire si les écrans de l'artisan respectent les
  droits ni s'ils marchent.
- **Ce qu'on verra à la fin.** Sur trois apps déjà construites en octobre, on saura si l'inspecteur s'y retrouve. S'il
  échoue surtout parce qu'il « ne trouve pas » les boutons, on imposera d'abord à l'artisan des noms de boutons et de
  liens (un contrat d'accessibilité).

### 2. À quoi ça sert
C'est l'inspecteur qui jugera l'artisan dans la chaîne complète (le squelette de bout en bout), puis chaque capacité.

### 3. Ce qui existe déjà
- **Les trois apps d'octobre**, toutes pour le même brief (location de matériel pour événements) :
  - **l'app mixte** (`C:\Users\BAMBARA Arthur\poc-agents\B`) : son cœur et ses écrans de base viennent de notre usine ;
    l'artisan y a ajouté 4 écrans riches. Elle passe ses propres juges : 258/258 aux règles, 36/36 aux écrans ;
  - **l'app de l'agent** (`…\poc-agents\A`) : un agent du commerce l'a construite à partir de notre description et de
    notre matrice ; tous les écrans sont les siens ;
  - **l'app du brief seul** (`C:\Users\BAMBARA Arthur\poc-a0`) : l'agent n'avait que le brief ; elle a ses propres
    fiches et ses 5 rôles (`admin`, `commercial`, `logistique`, `monteur`, `comptable`).
  - Toutes ont une page `/connexion` où l'on choisit qui l'on est (personnes `<rôle>_1` et `<rôle>_2`), chacune faite à
    sa façon. Toutes sont en Next.js **16.4.0**, que la construction refuse désormais.
- **La matrice** de l'app mixte et de l'app de l'agent (`poc-agents\entrees\matrice.json`) :
  - 3 acteurs (visiteur, gérant, membre de l'équipe) et 12 fiches ;
  - **1 changement d'état** : le gérant fait passer un devis de « en attente » à « confirmé » ;
  - 15 droits de création.
- **Le format d'un parcours**, arrêté en novembre (`conception-technique.md` §5.6), complété par la relecture (voir le
  §4).

### 4. Comment on la construit
**Les parcours sont des données** (un fichier par app). Chacun dit :
1. **l'acteur**, et la personne précise : `gerant_1` ou `gerant_2`. Ça compte pour les droits du type « seulement les
   siennes » ;
2. **l'état de départ** : les fiches à préparer, chacune avec une **étiquette visible et unique**, posée exprès (par
   exemple `ESSAI-7Q2`), pour la retrouver à l'écran sans connaître l'app ;
3. **le chemin** : par les noms visibles (le lien du menu porte le nom de la fiche), jamais par une adresse propre à
   l'app ;
4. **l'action**, avec le nom exact du bouton, pris dans la Description ;
5. **le résultat visible** : par exemple le nouvel état affiché. La correspondance entre le code d'un état
   (`confirme`) et son libellé affiché (« Confirmé ») est donnée ;
6. **le résultat dans la base** : par exemple le champ `status` ;
7. **l'interdiction**, quand le parcours dit ce qu'une personne ne doit pas pouvoir faire.

D'où viennent les parcours :
- **calculés depuis la matrice**, pour l'app mixte et l'app de l'agent : environ 40 ;
- **3 à 5 écrits à la main** pour l'app mixte, à partir des phrases de son miroir. C'est un contrôle croisé : si le
  calcul se trompait, les parcours calculés et les règles se tromperaient ensemble ;
- **5 à 8 écrits à la main** pour l'app du brief seul, dont les rôles ne sont pas les nôtres. Ses résultats sont une
  indication seulement.

**L'inspecteur** : un programme Playwright, sans IA. Pour chaque parcours :
1. **remettre la base à zéro** : vider les tables (`TRUNCATE … RESTART IDENTITY CASCADE`), puis poser l'état de
   départ, avec des **identifiants de fiches fixes**, dans la même base, pendant que l'app tourne. C'est rapide, et
   l'app n'a pas à redémarrer. Chaque parcours a aussi un **navigateur neuf** : sinon, le navigateur pourrait montrer
   des données gardées d'avant la remise à zéro ;
2. **se connecter** : aller sur `/connexion`, puis activer l'élément dont le nom correspond **exactement** à
   l'identifiant de la personne (sinon `gerant_1` trouverait aussi `gerant_10`). La règle est la même pour les trois
   apps ;
3. **suivre le chemin et trouver l'action**, toujours avec le nom **exact** (`exact: true`) : sinon, « Confirmer »
   trouverait aussi « Confirmer la suppression » ;
4. **agir**, puis vérifier le résultat visible et le résultat dans la base ;
5. **pour une interdiction** :
   - vérifier que le bouton est absent pour la personne interdite ;
   - puis **rejouer la requête** enregistrée pendant le parcours de la personne permise, avec la session de la
     personne interdite : la base ne doit pas bouger. Dans Next.js, une action n'a pas d'adresse fixe ; c'est la
     seule façon générique de la tenter. La requête est rejouée **à l'identique**, en-tête `Origin` compris : Next.js
     refuse en silence une requête dont l'origine ne correspond pas, et un rejeu mal formé ressemblerait à une
     interdiction respectée ;
   - **ce rejeu est lui-même prouvé** (voir le §6) : la même requête, rejouée par la personne permise, doit réussir.
     Sans ce témoin, l'interdiction est dite « non jugée ».

**Le classement des échecs** : la page est **stable** quand le repère attendu du chemin est visible (par exemple le
titre de la liste). Ensuite seulement, l'inspecteur **compte** les éléments qui portent ce nom.

| Ce qu'il trouve | Classe | Ce que ça veut dire |
|---|---|---|
| aucun | **introuvable** | le nom attendu n'est pas à l'écran : le contrat d'accessibilité n'est pas respecté |
| plusieurs | **ambigu** | deux éléments portent le même nom |
| un seul, mais désactivé ou recouvert | **présent mais inutilisable** | pour la personne permise, c'est un défaut ; pour la personne interdite, c'est un bouton trompeur, pas une faille, sauf si la requête rejouée réussit |
| un seul ; l'action se fait, mais l'écran ou la base ne montre pas le bon résultat | **comportement faux** | un défaut de l'app |
| une action interdite réussit | **interdiction violée** | un défaut grave |
| la page ne charge pas, le navigateur plante | **environnement** | rejoué une fois, et la relance est inscrite |

À chaque échec, il garde une **trace** (le film de ce qu'il a fait) et une **capture d'écran**, pour qu'on puisse le
relire.

**La stabilité** :
- jamais d'attente fixe ;
- le fuseau horaire fixé, pour le navigateur **et** pour le serveur de l'app (l'horloge figée de Playwright ne fige que
  le navigateur) ;
- aucun parcours qui dépend de la date du jour dans cet essai.

**Les apps** : on travaille sur des **copies** montées en Next.js 16.4.6. Leurs juges d'origine sont rejoués sur les
copies avant l'essai, en témoins : 258/258 aux règles pour l'app mixte et l'app de l'agent, et 36/36 aux écrans pour
l'app mixte.

*Écarté* :
- une IA pour trouver les éléments : ce juge doit être stable et ne jamais deviner ;
- les sélecteurs techniques (CSS, identifiants de test) : ils changent d'une app à l'autre, et ne disent pas si l'app
  est utilisable ;
- préparer l'état par l'écran : trop lent, et mélangé avec ce qu'on juge ;
- une base neuve par parcours : il faudrait redémarrer l'app à chaque fois ;
- une instance de l'app par base : trop lourd pour un essai.

### 5. Les pièges et leurs parades
- **Les noms choisis par l'agent** dans l'app de l'agent et l'app du brief seul ne sont pas ceux de notre Description :
  beaucoup d'« introuvable » sont attendus. C'est la mesure elle-même.
- **Chaque app a sa propre page de connexion** : une seule règle pour les trois. Si elle ne suffit pas, c'est un
  résultat de l'essai, pas un adaptateur à écrire.
- **Préparer l'état suppose de connaître les tables.** L'app mixte et l'app de l'agent suivent nos conventions de noms ;
  l'app du brief seul non. Parade : une préparation générique pour les deux premières, et une petite table de
  correspondance écrite à la main pour la troisième, comptée à part.
- **Confondre « absent » et « interdit »** : un parcours d'interdiction se joue toujours avec son **jumeau permis**, le
  même geste par une personne autorisée. Si le jumeau échoue, l'interdiction est dite « non jugée ».
- **Un inspecteur qui hésite** : chaque parcours est joué 3 fois ; une seule hésitation, et il est noté instable.
- **Les caches du serveur** : un écran d'agent peut garder des données en cache côté serveur et montrer d'anciennes
  données après la remise à zéro. Parade : avant l'essai, on relève si les apps utilisent des directives de cache ; si
  oui, ces échecs sont classés à part, sans être comptés comme des défauts de l'app.

### 6. Comment on prouve qu'elle marche (écrit avant)
**La démonstration** : l'inspecteur joue tous les parcours, sur les trois apps, 3 fois chacun.

| Mesure | Seuil (fixé maintenant) |
|---|---|
| **App mixte, sur les écrans de notre usine** : parcours joués jusqu'au bout, sans « introuvable » ni « ambigu » | **≥ 95 %** |
| **App mixte, sur les 4 écrans de l'artisan** | **mesuré**, donné à part |
| **App mixte** : verdicts | d'accord avec ses juges d'origine : aucun « comportement faux » ni « interdiction violée » |
| **App mixte** : les parcours écrits à la main | même verdict que les parcours calculés correspondants |
| **App de l'agent** | **mesuré**, sans seuil (pour savoir) |
| **App du brief seul** | **mesuré**, sans seuil (indication) |
| Stabilité, sur les 3 passages | **0 hésitation** |
| Durée | ≤ 2 min **par passage** et par app |

**Le témoin du rejeu, d'abord** : la requête du gérant qui confirme un devis, rejouée avec la session du **même**
gérant, sur une base remise à zéro, doit **réussir**. Sinon, aucune interdiction n'est jugée par rejeu.

**Ce que l'inspecteur doit attraper** : 6 sabotages sur une copie de l'app mixte ; chacun doit être signalé, dans la
bonne classe.
1. Le bouton « Confirmer » d'un devis est retiré pour le gérant → **introuvable**.
2. Le même bouton est montré au membre de l'équipe, et la règle du serveur est assouplie → **interdiction violée**.
3. Le bouton est montré au membre de l'équipe mais **désactivé**, et le serveur refuse → **présent mais
   inutilisable**, sans faille, puisque la requête rejouée échoue.
4. Deux boutons portent le même nom → **ambigu**.
5. Le bouton change l'écran, mais n'écrit pas dans la base → **comportement faux**.
6. Le bouton est **caché** au membre de l'équipe, mais la règle du serveur est assouplie → le rejeu doit réussir, et
   l'inspecteur doit dire **interdiction violée**. C'est ce sabotage qui prouve que le rejeu sait voir une faille.

**Le témoin** : l'app mixte intacte ; tous ses parcours passent.

**Le critère d'arrêt**, avec la décision écrite d'avance :
- moins de 95 % sur les écrans de notre usine, ou un sabotage non attrapé ou mal classé → l'inspecteur n'est pas prêt.
  On le corrige, jamais en assouplissant un parcours, puis on recommence une fois ; ensuite, on repense ;
- l'inspecteur tient sur nos écrans, mais les écrans des agents échouent surtout en « introuvable » → le **contrat
  d'accessibilité** passe avant la chaîne complète : des noms imposés à l'artisan, et vérifiés par un contrôle
  automatique avant l'inspecteur ;
- une hésitation → le parcours est corrigé ou retiré avant toute autre mesure.

### 7. Le périmètre
- **Touché** :
  - un dossier d'essai jetable, `C:\Users\BAMBARA Arthur\essais\juge-ecrans\` (l'inspecteur, les parcours, les
    mesures) ;
  - des copies des trois apps, montées en 16.4.6, et des bases jetables.
- **Pas touché** : les apps d'origine et leurs bases, le dépôt `StartupNexus` (sauf ce dossier), les juges de l'usine.
- **Taille max** : 2 jours. **Risque** : faible.

## Relecture

**Relecteur** : Claude en ligne, le 14 nov 2026 · **Verdict** : OK AVEC CORRECTIONS (aucun point bloquant)
(texte complet : `archives/echanges-2026-11/relecture-des-trois-essais-2026-11-14.md`)

| Point du relecteur | Réponse |
|---|---|
| « Tenter par l'adresse directe » ne marche pas pour une action Next.js | **Accepté** : on rejoue la requête du jumeau permis avec la session interdite. L'adresse directe reste pour voir une fiche |
| La recherche par nom est partielle par défaut | **Accepté** : `exact: true` partout |
| L'erreur de Playwright ne suffit pas pour classer | **Accepté** : on compte les éléments une fois la page stable ; nouvelle classe « présent mais inutilisable » ; « environnement » réservé aux pannes de chargement et de navigateur |
| La base neuve par parcours, avec l'app qui tourne | **Accepté** : remise à zéro des données dans la même base |
| Il manque de quoi trouver l'objet | **Accepté** : étiquette visible et unique, chemin par les noms, personne précise, correspondance des états |
| L'horloge figée ne fige que le navigateur | **Accepté** : fuseau fixé aussi pour le serveur, pas de parcours qui dépende de la date |
| Suggestion : des parcours écrits à la main, en contrôle croisé | **Accepté** : 3 à 5 pour l'app mixte |
| Suggestion : le bouton visible mais désactivé | **Accepté** : sabotage n° 3 et classe « présent mais inutilisable » |
| Suggestion : séparer les taux selon l'origine des écrans | **Accepté**, et le seuil monte à 95 % sur nos propres écrans |
| Suggestion : « ≤ 2 min » par passage | **Accepté** |
| Suggestion : trace et capture à chaque échec | **Accepté** |

**Seconde lecture** (Claude en ligne, le 14 nov) · **Verdict** : OK AVEC CORRECTIONS, après un nouveau point bloquant.

| Point du relecteur | Réponse |
|---|---|
| **BLOQUANT** : le rejeu de la requête n'est jamais prouvé ; un rejeu mal formé ressemblerait à une interdiction respectée | **Accepté** : témoin du rejeu (même personne permise → réussit), sabotage n° 6 (bouton caché + serveur assoupli → interdiction violée), en-tête `Origin` gardé, identifiants de fiches fixes |
| « Une fois la page stable » doit être défini | **Accepté** : quand le repère attendu du chemin est visible |
| Un navigateur neuf par parcours | **Accepté** |
| Les caches du serveur après la remise à zéro | **Accepté** : relevés avant l'essai, classés à part |
| La règle de connexion « contient l'identifiant » | **Accepté** : correspondance exacte |
| Suggestion : `TRUNCATE … RESTART IDENTITY CASCADE` | **Accepté** |

**Décision d'Arthur** : « go », le 14 nov (« si tu juges bon, on peut commencer »).

## Petit lexique
- **Parcours** : une mission décrite comme une donnée (qui, quoi, où, ce qu'on doit voir, ce qui est interdit).
- **Nom accessible** : ce qui est écrit sur un bouton ou un lien, tel qu'un lecteur d'écran le lit.
- **Playwright** : l'outil qui pilote un vrai navigateur, comme un humain, mais automatiquement.
- **Jumeau permis** : le même geste, fait par une personne qui a le droit ; il prouve que le geste existe.
- **Contrat d'accessibilité** : des noms de boutons et de liens imposés à l'artisan, pour que l'inspecteur les trouve.
