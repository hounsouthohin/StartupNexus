# L'essai du juge d'écrans : un juge sans IA s'y retrouve-t-il dans des écrans faits par un agent ?

> **Taille** : moyen (essai jetable) · **Statut** : **faisable, pas encore admis** (réécrit le 17 nov après la relecture
> et un rejeu sur une seule version) ; le contrat des noms à l'écran devient prioritaire ; **à clore par Arthur** après un
> dernier coup d'œil des relecteurs sur les faits nouveaux · **Indépendant** des deux autres essais
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
  liens (un contrat des noms à l'écran).

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
| aucun | **introuvable** | le nom attendu n'est pas à l'écran : le contrat des noms à l'écran n'est pas respecté |
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

**Où il tourne (révisé le 16 nov, d'après l'essai de la boîte)** : chaque app essayée tourne **dans un atelier**, avec
sa base et Chromium, sans réseau. L'inspecteur y joue ses parcours, et la base de l'usine n'est plus touchée. C'est la
règle « les juges tournent toujours dans un atelier neuf », appliquée dès l'essai. Il faut pour cela un étage de moule
par app : ses bibliothèques, ses tables, ses données de démonstration.

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

## Après : le compte rendu (16 nov 2026 ; réécrit le 17 nov, après la relecture et le rejeu)

> **Ce compte rendu remplace celui du 16 nov.** Celui-là annonçait « 51/51 ✔ ». C'était trop beau : aucun parcours
> autorisé ne réussissait sans contournement, et une partie des résultats venait d'une version d'avant ma dernière
> correction. Les deux relecteurs l'ont relevé ([relecture archivée](../archives/echanges-2026-11/relecture-contrat-et-juge-ecrans-2026-11-16.md)).
> Le rejeu sur une seule version a ensuite trouvé **trois défauts de délai** dans l'inspecteur, et une fausse alarme.
> Les anciens résultats sont gardés dans `essais/juge-ecrans/avant-rejeu/` (16 nov) et `rejeu-1-du-17-nov/` (rejeu
> interrompu par les défauts) ; l'ancien texte est dans l'historique git.

### 9. Ce qui a été fait
Dans `C:\Users\BAMBARA Arthur\essais\juge-ecrans\` :
- `apps/` : les copies des trois apps, en Next.js 16.4.6, sans aucun `.env` ;
- `Dockerfile.app` : un étage de moule par app (ses bibliothèques, ses tables, ses données) ;
- `generer_parcours.py` : 51 parcours calculés depuis la matrice, pour l'app mixte et l'app de l'agent. Chaque fichier
  de parcours porte le chemin et l'empreinte de la description qu'il a lue ;
- `parcours_a_la_main.py` : 4 parcours tirés du miroir pour l'app mixte, 8 pour l'app du brief seul ;
- `inspecteur/inspecteur.mjs` : l'inspecteur. Depuis le 17 nov, il a :
  - un mode **sans repli** ;
  - une **note sur chaque parcours pour chaque tolérance** utilisée ;
  - les **empreintes** dans chaque résultat ;
  - un mode **ralenti** ;
- `juge.py` : le pilote, qui sort l'atelier, construit l'app, lance l'inspecteur et rapatrie ses verdicts ;
- `saboter.py` : les 6 sabotages, joués 3 fois chacun ;
- `rejouer_tout.py` : tout le rejeu en une commande ; `bilan.py` : le bilan (`bilan.json`) ;
- `resultats-*.json`, `preuves/` (une capture et un « film » par échec), `journal-rejeu/`.

### 10. Les écarts avec la conception

- **Il n'y avait pas deux replis, mais six tolérances.** Je n'en avais déclaré que deux ; elles sont désormais toutes
  notées par la machine, parcours par parcours :
  1. **la connexion** : le bouton « personne 1 » sur la ligne du rôle, faute d'identifiant ;
  2. **le menu** : son nom reconnu sans tenir compte des majuscules (« Événements » pour « événements »), ou au singulier ;
  3. **le bouton de création** : le nom générique « Nouveau … » quand le nom proposé est absent, ou quand la description
     n'en donne aucun (ce second cas n'était même pas noté le 16 nov) ;
  4. **les champs** : reconnus par le **début** de leur libellé ;
  5. **l'ouverture d'une fiche par sa ligne**, quand son lien ne porte pas l'étiquette ;
  6. **une fiche sans texte** (le mouvement de stock), reconnue par l'étiquette de la fiche qu'elle désigne.
- **Le sabotage n° 3** : notre squelette ne sait pas afficher un bouton désactivé. On a donc montré le bouton **actif**,
  avec un serveur qui refuse. C'est un scénario de **remplacement** : la classe « présent mais inutilisable » n'est pas
  prouvée.
- **Trois erreurs, corrigées pendant le premier essai** :
  - les modifications par PUT et PATCH n'étaient pas enregistrées ;
  - les champs texte qui ont une valeur par défaut étaient écrasés ;
  - l'inspecteur lisait la description des entrées, et non celle de l'app mixte (une fausse alarme).
- **Trois défauts de délai, trouvés par le rejeu du 17 nov, et corrigés.** Les deux premiers pouvaient donner un faux
  « interdiction respectée » :
  1. **l'adresse notée avant la fin d'un changement de page.** Un lien de ces apps change de page sans recharger le
     navigateur ; sur une machine lente, l'inspecteur notait encore l'ancienne adresse. Le 16 nov, le sabotage n° 3
     n'a été « attrapé » que par chance. Au premier rejeu, le membre était contrôlé sur la liste au lieu de la fiche,
     et le sabotage a été manqué. Parade : attendre que l'adresse change vraiment ;
  2. **une absence conclue sur une page encore « Chargement… »**, 250 ms après l'apparition du cadre. Le 16 nov,
     l'interdiction de voir les devis a été constatée sur la fiche ; sur la liste, encore en chargement, elle avait été
     comptée « absente ». Parade : attendre que la page ne fasse plus aucune requête. Si elle ne se stabilise pas,
     le parcours n'est **pas jugé**. Le vrai remède est un signal de chargement imposé par le contrat ;
  3. **une remise à zéro de la base sans limite d'attente.** Une passe a duré 704 s, et l'app du brief seul s'est
     arrêtée sur un blocage mutuel (« deadlock »). Parade établie : une attente bornée, puis un nouvel essai.

  **Preuve que l'inspecteur ne dépend plus du délai** : une passe sur un navigateur ralenti trois fois (outil de
  Chromium) donne exactement les mêmes verdicts.
- **L'empreinte des « données de départ » ne prouve rien.** PostgreSQL ajoute à chaque export une clé de sécurité tirée
  au hasard (les lignes `\restrict`, une protection récente de ses outils), si bien que l'empreinte change à chaque
  fois. Les données sont pourtant les mêmes : elles sont figées dans l'image, dont l'empreinte est identique d'un
  passage à l'autre. Pour le vrai juge : une clé fixe (`--restrict-key`).
- **Où il tourne** : dans un atelier, et non sur le PC.

### 11. Les résultats des preuves (une seule version, contre les seuils écrits d'avance)

**La version jugée** (toutes les mesures ci-dessous, sabotages compris) :
- l'inspecteur `1afd3ef7…`, Chromium 156.0.8078.4, Playwright 1.64.0 ;
- l'app mixte : la description `de1c821b…`, l'app `bcbf1601…`, l'image `84c88e36…` ;
- l'app de l'agent : la description `e86bad44…`, l'app `b3bbe9b2…`, l'image `23d3f7e2…` ;
- l'app du brief seul : pas de description, l'app `5bbdab54…`, l'image `09e82ad1…`.

**La règle d'écriture** (17 nov) : le chiffre en tête est la mesure stricte ; ✔ seulement si le seuil est atteint
sans aucun contournement.

| Mesure | Seuil | **Sans aucun repli** | Avec replis | Verdict |
|---|---|---|---|---|
| App mixte (nos écrans) : parcours joués jusqu'au bout | ≥ 95 % | **0 / 51** (34 « introuvable » dès la connexion, 17 « non jugé ») | 51 / 51, aux 3 passes | ✗ |
| App mixte : verdicts d'accord avec ses juges d'origine | d'accord | non mesurable | d'accord : aucun « comportement faux », aucune « interdiction violée » | ✗ (seulement avec replis) |
| App mixte : les 4 parcours écrits à la main | même verdict que les calculés | non joué | 4 / 4 | ✗ (seulement avec replis) |
| App mixte : les 4 écrans riches de l'artisan | mesuré à part | non mesuré | non mesuré | — |
| App de l'agent | mesuré | **0 juste** (23 « introuvable » dès le menu, à cause de la majuscule ; 28 « non jugé ») | 38 justes sur 44 jugés ; 7 « non jugé » à part (détail plus bas) | mesuré |
| App du brief seul | mesuré | **0 juste** (4 « introuvable » au menu ; 4 « non jugé ») | 6 justes sur 7 jugés ; 1 « non jugé » | mesuré |
| Témoin du rejeu | doit réussir | — | 9 / 9 sur l'app mixte (avec la connexion de repli) ; **6 / 6 sur l'app de l'agent, sans repli de connexion** | ✔ pour l'app de l'agent ; ✗ pour l'app mixte |
| Sabotages (sur l'app mixte) | 6 / 6, dans la bonne classe | non mesurable (la connexion échoue) | **5 sabotages prévus et 1 de remplacement**, chacun attrapé aux 3 passes, et aussi au ralenti | ✗ au sens strict (avec replis) |
| Stabilité | 0 hésitation | 0 sur 3 passes | 0 sur 3 passes, pour les trois apps | ✔ |
| Indépendance au délai (ajoutée le 17 nov) | mêmes verdicts au ralenti × 3 | — | app mixte : 0 différence ; app de l'agent : 0 différence ; sabotages : 6 / 6 | ✔ |
| Durée par passage | ≤ 2 min par app | — | app mixte **172 à 175 s** ; app de l'agent **125 à 127 s** ; app du brief seul 24 s | ✗ pour les deux grandes apps |

La durée a augmenté depuis le 16 nov (150 s et 105 s) : attendre les vrais changements de page et la fin des
chargements coûte du temps. C'est le prix de verdicts justes.

**Combien de parcours dépendent de chaque repli** (les replis se chevauchent : ce ne sont pas des sommes ; un parcours
interdit compte aussi les replis de son jumeau, qui a trouvé l'adresse et la requête) :

| Repli | App mixte (51) | App de l'agent (51) | App du brief seul (8) |
|---|---|---|---|
| connexion par « personne N » | 51 | 0 | 0 |
| menu sans tenir compte des majuscules | 51 | 51 | 6 |
| création : nom générique | 24 | 6 | 0 |
| champ reconnu par le début de son libellé | 21 | 18 | 0 |
| fiche ouverte par sa ligne | 18 | 0 | 0 |
| fiche sans texte, reconnue par la fiche désignée | 3 | 3 | 0 |

**Les échecs de l'app de l'agent, par catégorie** (sur 44 parcours jugés) :
- **2 « introuvable » : un trou du contrat.** Ce sont les boutons de création des clients et des produits : la
  description ne donne aucun nom.
- **1 « comportement faux » : une règle non validée.** L'agent ne propose que les devis « confirmés » à la création d'un
  contrat. C'est vérifié : la fiche d'essai était « en attente » et visible du gérant, et l'écran ne la proposait pas.
  C'est un vrai écart avec la description ; il aurait dû passer par le miroir.
- **2 « comportement faux », reclassés « affichage non conforme au contrat » : un trou du contrat dans cet essai.**
  Les vidéos étaient bien en base (aucun écart à la préparation), mais la liste affiche « Vidéo test : nom du
  produit », et le contrat ne disait pas quel champ sert de titre. Une fois le contrat écrit, ce sera un vrai défaut.
- **1 « interdiction violée » : une fausse alarme de l'inspecteur, nouvelle au rejeu.**
  - Le mouvement de stock n'a aucun texte, donc l'inspecteur le reconnaît par son produit (un repli).
  - Dans l'app de l'agent, le lien de sa ligne mène à la **page du produit**, pas à celle du mouvement.
  - Le membre, qui a le droit de voir les produits, y voit donc « ESSAI-Produit ».
  - Le 16 nov, ce parcours était « ok » uniquement parce que l'adresse notée était fausse.
  - Deux leçons : la page d'une fiche doit dire **de quelle sorte de fiche** il s'agit, et un repli de reconnaissance ne
    doit **jamais** servir à juger une interdiction.
- **7 « non jugé »** : leur jumeau autorisé a échoué. Ils ne comptent ni comme des réussites, ni comme des échecs.

**Les sabotages, un par un** (3 passes à vitesse normale, 3 passes au ralenti ; même résultat à chaque fois) :

| Sabotage | Attendu | Obtenu |
|---|---|---|
| 1. « Confirmer » retiré pour le gérant | introuvable | ✓ introuvable |
| 2. Montré au membre, et le serveur autorise | interdiction violée | ✓ violée : le rejeu confirme le devis, et le devis est visible |
| 3. *(remplacement)* Montré au membre, mais le serveur refuse | bouton trompeur, pas une faille | ✓ « bouton présent, mais le serveur refuse » |
| 4. Deux boutons du même nom | ambigu | ✓ ambigu |
| 5. Le bouton n'écrit rien en base | comportement faux | ✓ comportement faux |
| 6. **Caché** au membre, mais le serveur autorise | interdiction violée | ✓ violée : seul le rejeu pouvait la voir |

Pour rejouer : `python rejouer_tout.py` (environ 50 minutes, ordinateur allumé), puis lire `bilan.json`.

### 11 bis. Ce qui n'est pas prouvé

- **L'inspecteur n'est pas admis.** Sans repli, il ne joue aucun parcours autorisé, sur aucune des trois apps. Il est
  seulement montré **faisable** : il sait jouer des parcours et distinguer les classes de défauts, **une fois les
  éléments trouvés**.
- **La classe « présent mais inutilisable »** (un bouton désactivé ou recouvert) n'a jamais été provoquée.
- **Que la session interdite soit bien reconnue par le serveur** avant le rejeu : rien ne le vérifie (aucune page ne
  montre qui est connecté).
- **Le rejeu d'une modification** (PUT, PATCH) : aucun témoin. Seules des créations et une confirmation ont été prouvées.
- **Les écrans riches** (calendrier, stock, profit, rapports) : aucun parcours.
- **La parade contre les blocages de la remise à zéro** n'a pas eu à servir pendant ce rejeu (aucun nouvel essai
  nécessaire) : elle n'est pas prouvée.
- **Les données d'essai** sont posées en SQL brut, sans passer par les règles de l'app.
- **Un seul navigateur** (Chromium), une seule machine.
- **Les parcours écrits à la main** n'ont pas été joués sans repli.

### 12. Comment ça marche, et comment c'est fait (en mots simples)
- **Les missions sont des données.** Un petit programme Python lit la matrice des droits, et écrit pour chaque rôle et
  chaque fiche : « le gérant voit les devis », « le membre ne les voit pas », « le gérant confirme un devis ». Il en
  sort 51 missions. Chaque interdiction est accompagnée de son jumeau autorisé.
- **L'inspecteur est un robot de navigateur.** Il utilise **Playwright**, qui pilote un vrai Chromium comme le ferait une
  personne. Pour chaque mission :
  1. il remet la base à zéro, avec des fiches d'essai aux identifiants fixes, nommées « ESSAI-… » ;
  2. il ouvre un navigateur neuf et se connecte ;
  3. il cherche les liens et les boutons **par ce qui est écrit dessus**, sans rien savoir du code ;
  4. il agit, **attend que la page ait vraiment changé et fini de charger**, puis vérifie deux fois : ce que l'écran
     montre, et ce que la base de données a enregistré.
- **Le rejeu.** Quand le gérant clique sur « Confirmer », l'inspecteur enregistre la requête envoyée au serveur. Pour le
  membre de l'équipe, il renvoie cette même requête avec la session du membre : la base ne doit pas bouger. Avant de
  croire ce test, il le prouve : renvoyée par le gérant lui-même, la requête doit réussir.
- **Chaque tolérance est notée**, et le **mode sans repli** les refuse toutes : c'est la mesure stricte.
- **Chaque résultat porte ses empreintes** (un code calculé sur le contenu, qui change si un seul caractère change) :
  on sait exactement quel inspecteur a jugé quelle app, avec quelle description.
- **Le mode ralenti** demande à Chromium de travailler trois fois plus lentement. Si les verdicts changent, c'est que
  l'inspecteur dépend du hasard des délais.
- **Tout se passe dans un atelier** : l'app, sa base, le navigateur et l'inspecteur, sans réseau.

### 13. Ce qu'Arthur peut voir lui-même
- `bilan.json` : tous les chiffres ci-dessus, app par app, avec les empreintes.
- `preuves/` : pour chaque échec, une capture d'écran (`.png`) et le film du parcours (`.zip`). Ce dernier s'ouvre sur
  https://trace.playwright.dev en y déposant le fichier ; il reste sur ton PC.
- `resultats-sabotages.json` et `resultats-sabotages-ralenti.json` : les six sabotages, attendu et obtenu, passe par
  passe.

### 14. Ce que ça change pour la suite
- **La conclusion**, dans les mots demandés par la relecture : *l'essai montre qu'un inspecteur sans IA peut jouer ces
  parcours, et certaines interdictions, sur des apps construites différemment, à condition que les noms d'interface
  soient définis d'avance. Les adaptations nécessaires confirment la priorité du contrat des noms à l'écran.
  L'inspecteur n'est pas encore admis : il le sera dans le vrai juge, avec ses propres preuves.*
- **Le contrat des noms à l'écran passe en priorité.** Le rejeu lui ajoute :
  - une règle : la page dit quand elle a fini de charger ;
  - une précision : la page d'une fiche dit de quelle sorte de fiche il s'agit.
  - Son [dossier](contrat-noms-ecran.md) est à jour.
- **Pour le vrai juge** (inscrit dans `USINE.md`, étape des juges) :
  - ne dépendre d'aucun délai, preuve par une passe ralentie ;
  - ne jamais juger une interdiction à l'aide d'un repli ;
  - une clé fixe pour l'empreinte des données ;
  - plus les sept points de la relecture.
- **La vitesse** : 175 s et 127 s par passage, au-delà des 120 s. La parade pour le vrai juge : plusieurs navigateurs en
  parallèle, chacun avec **sa propre base**.
- **Les deux défauts de l'usine** au registre (`USINE.md` §7, n° 61 avec son diagnostic corrigé, et n° 62) se
  corrigent avec le contrat.
- **L'inconnue n° 4** est fermée ainsi : faisable, pas encore admis.
- **Relecture extérieure** : ce compte rendu est la correction que la relecture demandait. Mais il contient des faits
  nouveaux que les relecteurs n'ont pas vus (les trois défauts de délai, la fausse alarme, la clé de PostgreSQL). Je
  recommande qu'ils relisent au moins les §10, §11 et §11 bis avant qu'Arthur clôture l'essai.

## Petit lexique
- **Parcours** : une mission décrite comme une donnée (qui, quoi, où, ce qu'on doit voir, ce qui est interdit).
- **Nom accessible** : ce qui est écrit sur un bouton ou un lien, tel qu'un lecteur d'écran le lit.
- **Playwright** : l'outil qui pilote un vrai navigateur, comme un humain, mais automatiquement.
- **Jumeau permis** : le même geste, fait par une personne qui a le droit ; il prouve que le geste existe.
- **Contrat des noms à l'écran** : des noms de boutons et de liens imposés à l'artisan, pour que l'inspecteur les trouve.
