# Le contrat des noms à l'écran

> **Renommé le 19 nov 2026** (décision d'Arthur, sur une remarque de Codex) : il s'appelait « contrat
> d'accessibilité ». Ce nom promettait une conformité générale d'accessibilité qu'il ne vérifie pas. Le contrat fixe les
> noms, les repères et les états de chargement dont les juges ont besoin.

> **Taille** : critique (c'est l'entrée de toute la chaîne et le contrat d'un juge)
> **Statut** : **version 3**, le 19 nov. Elle répond aux trois garanties demandées par Codex sur la version 2. **À
> valider par Codex**, puis « go » d'Arthur.
> **Dates** : écrit le 16 nov · relu le 16 nov (Claude en ligne et une IA d'un autre fournisseur) · « oui » d'Arthur au
> principe le 19 nov · vérifié par Codex le 19 nov (« à revoir ») · version 2 le 19 nov · revérifiée (« à revoir » sur
> trois garanties) · version 3 le 19 nov · fini le …
> **Auteur** : Claude Code · **Vérificateur** : Codex

> **Règles d'écriture** : des noms, pas des codes ; des mots simples ; toujours le pourquoi. Les affirmations de fait
> portent leur étiquette : [lu], [rapporté] ou [rejoué].

## Avant : la conception

### 1. En mots simples

- **Ce que c'est.** Une règle : **tout nom qu'un juge cherche à l'écran vient de la description, et la description est
  montrée au client**, dans le miroir. L'écran affiche ce nom, le juge cherche ce nom, personne n'en invente un autre. Le
  contrat ajoute une chose qui n'est pas un nom : **chaque zone de l'écran dit à la machine si elle charge, si elle est
  prête, ou si elle a échoué**. Sans ce signal, un juge peut prendre une page qui charge, ou qui a planté, pour une page
  sans l'élément, et croire à tort qu'une interdiction est respectée.

  En image, un immeuble : le plan signé dit « salle 204 », la plaque sur la porte dit « salle 204 », et le visiteur
  cherche « salle 204 ». Et une lumière au-dessus de la porte dit si la salle est ouverte ou en travaux.
- **Pourquoi on le fait.** L'essai du juge d'écrans l'a montré : **sans noms imposés, l'inspecteur ne joue aucun
  parcours autorisé**, même sur nos propres écrans (0 sur 51 sans repli [rapporté : `conception/essai-juge-ecrans.md`
  §11]). Sans contrat, chaque nouvelle app ajouterait un repli. Le rejeu du 17 nov a montré en plus qu'un juge qui
  devine le moment où la page est prête se trompe sur une machine lente.
- **Ce n'est pas une liste de mots imposés.** Les mots changent avec chaque client ; seule la **correspondance** est
  fixe. Les noms gardent leur souplesse : le lecteur des libellés (une IA) les propose, le client les corrige au miroir,
  la description les fige.
- **Ce qu'on verra à la fin.**
  - Le miroir montre, pour chaque fiche, les noms qui apparaîtront à l'écran.
  - L'app affiche exactement ces noms, et chaque zone dit son état.
  - L'inspecteur, **sans aucun repli**, joue tout l'inventaire des parcours écrit d'avance sur les trois exemples de
    l'usine, sans aucun parcours « non jugé ».

### 2. À quoi ça sert

Le contrat est la langue commune de trois parties :
- **la description**, validée par le client ;
- **ceux qui construisent les écrans** : le traducteur de l'usine, et plus tard l'artisan ;
- **ceux qui les jugent** : l'inspecteur d'écrans.

Il vient avant la chaîne complète : le juge de cette chaîne jugera les écrans de l'artisan.

### 3. Ce qui existe déjà [lu]

| Ce que l'écran montre | D'où ça vient aujourd'hui | Le problème |
|---|---|---|
| Lien du menu | le nom pluriel de la description, avec une majuscule ajoutée à l'affichage | pas imposé à l'agent |
| Champ d'un formulaire | son libellé, placé dans l'étiquette, avec le champ ou la liste de choix **dedans** (`components/vues.tsx`, `pieces.tsx:104-117`) | le nom lu par la machine ajoute « (facultatif) », ou la valeur choisie |
| Bouton du formulaire de création | une règle de grammaire (`usine/traduire/ecran.py:50-51`) | hors de la description et du miroir ; faux devant un h aspiré |
| Boutons d'étape, création en un clic | proposés par le lecteur des libellés | jamais montrés au miroir |
| Ce qui ouvre une fiche dans une liste | le premier morceau non vide de la ligne (`components/vues.tsx:36-47`) ; « premier champ texte » pour l'affichage et le tri (`usine/traduire/modele.py:80`) | un devis s'ouvre par le nom de son client ; un champ vide fait disparaître le morceau |
| **Le chargement** | « Chargement… » en texte, sans aucun signal pour la machine (`pieces.tsx:55`) ; **une erreur de chargement s'affiche comme une liste vide** (`data ?? []`, `pieces.tsx:76` et `:108`) | une page qui charge ou qui a planté ressemble à une page sans l'élément |
| Connexion simulée | « personne 1 », « personne 2 » (`app/(app)/page.tsx:20`) | l'identifiant `gerant_1` n'apparaît pas |
| Confirmations | des boutons de confirmation sur place (« Confirmer la suppression »), pas des fenêtres (`pieces.tsx:144`, `:179-185`) | — |
| Règle métier ajoutée par l'artisan | nulle part | l'agent a filtré de lui-même les devis « confirmés » |

**Ce qu'on réutilise :**
- le lecteur des libellés ;
- la question du miroir « nous avons choisi : … » ;
- **la porte**, qui enregistre déjà l'empreinte de la description validée et la vérifie avant de fabriquer
  (`usine/miroir/porte.py:52-98`) ;
- l'inspecteur de l'essai, comme instrument de preuve.

**Les tests d'écran existants ne suivront pas tout seuls** [lu].
- Ils lisent certains noms dans la notice (`e2e/noyau.ts:73`).
- Ils dépendent aussi de l'ordre des lignes : `ouvrirPlusRecente` clique la première ligne (`e2e/noyau.ts:48-52`).
- Ils dépendent encore de noms fixes : « Ajouter : … » (`e2e/noyau.ts:102`), « Créer », « Enregistrer ».

Ce sont des **témoins**. Chaque test qui doit changer à cause du contrat sera listé et justifié, jamais modifié en
silence.

### 4. Comment on la construit

**Les onze règles du contrat.** Les règles 3, 7, 9 et 11 sont des **conventions du squelette** de l'usine, imposées
aussi à l'artisan. Ce ne sont pas des exigences de la norme d'accessibilité.

| # | Règle | Source |
|---|---|---|
| 1 | **Connexion d'essai** : chaque bouton de connexion simulée contient l'identifiant de la personne, en mot entier (« personne 1 · gerant_1 ») | les personnes d'essai |
| 2 | **Menu** : le lien porte le nom pluriel de la fiche | la description |
| 3 | **Repère de page** : une page de liste a pour titre principal le nom pluriel ; une page de fiche, **sa sorte et son titre** (« Mouvement de stock : ESSAI-Produit »). Sans la sorte, la page d'un mouvement et celle de son produit se confondaient (la fausse alarme du rejeu du 17 nov) | la description |
| 4 | **Bouton de création** : son nom est celui que la description donne à la fiche | **nouveau** : `creation` |
| 5 | **Boutons d'étape et de création en un clic** : leur nom vient de la description | existe ; **désormais montré au miroir** |
| 6 | **Le titre d'une fiche.** Dans une liste, c'est le premier morceau de la ligne et **le lien qui ouvre cette fiche-là**. Son nom est exactement le titre, sans préfixe ni suffixe. Il n'est **pas promis unique** : le juge reconnaît d'abord la ligne. Les règles du titre sont détaillées plus bas | **nouveau** : `titre` |
| 7 | **Libellé des états** : un état s'affiche avec le libellé de la description, et rien d'autre | la description |
| 8 | **Champs** : le nom d'un champ, tel que la machine le lit, est exactement son libellé. L'étiquette est **reliée** au champ (`for` et `id`), listes de choix comprises, avec des identifiants uniques même si plusieurs formulaires sont ouverts. « (facultatif) » et les aides passent dans la description accessible (`aria-describedby`) | la description |
| 9 | **Un nom, une action** : dans le contexte d'une action, pour un rôle et un état donnés, deux éléments ne portent pas le même nom. Ce contexte est la ligne, ou la page pour les actions de page | — |
| 10 | **Pas de règle cachée** : l'artisan n'ajoute aucune règle que la description ne contient pas ; s'il en voit une, il la signale. C'est une **obligation** de l'artisan : les parcours en attrapent certaines manifestations, mais ne prouvent pas qu'il n'en reste aucune | — |
| 11 | **L'état de chaque zone de données** (une liste, une fiche, une liste de choix) : elle porte `data-etat` = `chargement`, `pret` ou `erreur`, et `aria-busy="true"` pendant le chargement. **Une erreur s'affiche comme une erreur, jamais comme une liste vide.** Une liste vide est « pret », avec son message. Le juge ne conclut à l'absence d'un élément que dans la **bonne** zone, de la **bonne** page (le repère), à l'état **pret**. Une erreur, un état manquant ou une attente dépassée (10 secondes) donne **« non jugé »**, jamais « interdiction respectée » | — |

**Les règles du titre (règle 6).**
- **Le titre est l'un ou l'autre** :
  - **(a)** un champ texte court **obligatoire** de la fiche. Un texte long ne compte pas ;
  - **(b)** une fiche désignée par un lien **obligatoire**, dont le titre est lui-même de la sorte (a). On ne va pas plus
    loin qu'**un niveau**.
- **(b) n'est permis que si chaque rôle qui voit la fiche voit TOUTES les fiches de la sorte désignée** : la portée
  « toutes » dans la matrice. *(Version 3 : c'est la remarque de Codex.)* Voir les deux sortes ne suffit pas. Un rôle
  peut voir l'emprunt de Paul tout en ne voyant que **ses propres** fiches liées. Si un seul de ces rôles ne voit les
  fiches désignées que par « les siennes », « les publiées » ou « au travers d'une autre fiche », (b) est **refusé** :
  le titre est alors (a), ou le champ « Libellé » validé au miroir. **Aucun droit n'est élargi** pour faire passer un
  titre, et aucun titre n'est inventé.
- **Un titre est non vide.** *(Version 3 : remarque de Codex, vérifiée dans le code.)* « Obligatoire » ne garantit pas
  « non vide » aujourd'hui. Le formulaire retire les espaces, puis **transmet** une chaîne vide
  (`components/vues.tsx:89-92`) [lu]. Aucun contrôle côté serveur n'impose « non vide ». **Que cette chaîne vide soit
  vraiment enregistrée en base reste à confirmer** : c'est la première mesure du morceau 12. D'où deux choses :
  - **le serveur refuse un texte obligatoire vide ou fait seulement d'espaces** (morceau 12). C'est une correction
    pour **tous** les textes obligatoires, inscrite au registre (n° 63) ;
  - **une fiche dont le titre est vide**, par exemple une donnée ancienne, est « **non jugé** » pour le juge, jamais
    « absente ».
- **Le tri ne fait pas partie du contrat.** Les fiches à circuit restent triées par date, la plus récente d'abord, comme
  aujourd'hui (les tests en dépendent). Les autres sont triées par leur titre (a), ou par date de création pour (b).

**Deux conventions s'appliquent à tous les noms :**
- **Le nom lu par la machine correspond au texte affiché.** C'est la règle « Label in Name » du W3C. Un `aria-label` ne
  peut pas dire autre chose que ce que voit le client.
- **La forme exacte est fixée dans la description.** Les espaces sont normalisés ; la comparaison est exacte, majuscules
  comprises (Playwright avec `exact: true`). Une seule mise en forme est permise : **la majuscule initiale d'un nom
  affiché seul** (le menu, le titre d'une page).

**Les morceaux, et pourquoi chacun :**

1. **La description** (`usine/description.py`). Elle porte un **numéro de format** : `format: 2`. Une description sans
   numéro est de format 1, et elle est refusée avec ce message : « format 1 (sans numéro), attendu 2 ». Elle gagne
   `creation` et `titre` pour chaque fiche principale. Les noms sont normalisés. Les contrôles refusent, sans jamais
   deviner :
   - un `creation` ou un `titre` absent ;
   - un titre (a) facultatif, long, numérique ou daté ;
   - un titre (b) dont le lien est facultatif, ou dont les fiches désignées ne sont pas toutes visibles (portée
     « toutes ») pour **chaque** rôle qui voit la fiche ;
   - deux actions de même nom sur une même page de l'usine.

   *Pourquoi* : la description est la seule source validée. Un nom absent est refusé franchement.
2. **Le lecteur des libellés** (`usine/comprendre/lecteurs.py`). Il reçoit une consigne de plus : `creation`, pour
   chaque fiche principale. Ses contrôles vérifient que ce nom n'est pas vide et qu'il est distinct.
   - **La méthode de mesure** : sur les 10 briefs d'apprentissage, on garde les réponses d'**avant** le changement (même
     brief, même lecteur), puis on lance la nouvelle consigne.
   - **Le dénominateur** : tous les noms de création proposés pour des fiches principales.
   - Arthur lit le tableau et compte les noms qu'il corrige ; les noms refusés par les contrôles sont comptés à part.
   - Le coût observé est rapporté : le nombre d'appels.
3. **La complétion, avant le miroir et seulement là** (l'étape « assembler la description »).
   - Le nom de création manquant est fabriqué par l'ancienne règle de grammaire, mais **visible** au miroir.
   - Le titre par défaut est, dans l'ordre :
     - le premier champ texte court obligatoire ;
     - sinon, le premier lien obligatoire qui respecte la règle (b) ;
     - sinon, un champ « Libellé » obligatoire, marqué « nécessaire ».
   - **Un champ ajouté n'existe que s'il est validé au miroir** (la question « nous avons choisi : … »), avant la
     fabrication.
   - **Toute correction faite à la main dans la description repasse par le miroir.** La porte annule déjà la validation
     quand la description change.
4. **Le miroir** (`usine/miroir/contenu.py`).
   - Chaque fiche a son bloc « À l'écran » : le menu, le bouton de création, le titre, les étapes, la création en un
     clic.
   - **Le contrôle de couverture** prend les noms que l'inspecteur cherchera, dans son inventaire (fiche, action, nom).
     Il vérifie que chacun figure **dans le bloc de sa fiche, à la ligne de son action**, dans **la vue présentée au
     client**, et non n'importe où dans le texte.
   - Un nom absent arrête tout, et le contrôle le nomme.
5. **La porte et les empreintes** (`usine/miroir/porte.py`).
   - À la validation, la porte enregistre déjà l'empreinte de la description. Elle enregistre désormais **aussi celle
     de la vue du miroir présentée au client**.
   - *(Version 3, remarque de Codex.)* **La vue empreintée doit être celle qui découle de la description validée.**
     Au moment de valider, la porte **régénère** la vue depuis la description qu'elle valide, et la compare à la vue
     présentée. Si elles diffèrent (une vue tirée d'une autre version, par exemple), la validation est refusée.
   - Une modification de l'une ou de l'autre après la validation est refusée.
   - Le juge refuse de juger si l'empreinte de la description ne concorde pas.
   - **Le mode d'essai** (les trois exemples) écrit une validation marquée `essai : vrai` et « essai — non validée par
     un client ». Le juge l'accepte seulement en mode d'essai, et ses résultats portent cette mention : jamais
     confondus avec un accord de client.
6. **Le traducteur d'écrans** (`usine/traduire/ecran.py`, `modele.py`). Il lit `creation` et `titre` dans la
   description. La règle de grammaire en sort. Le tri suit la règle 6, sans changement pour les fiches à circuit.
7. **Le squelette** (`usine/modele-app`).
   - Les boutons de connexion portent l'identifiant.
   - Chaque page a son repère.
   - Dans une liste, le titre vient en premier, et son lien ouvre **cette** fiche.
   - Les étiquettes sont reliées, listes de choix comprises, avec des identifiants uniques.
   - **Les zones de données portent leur état** ; une erreur s'affiche comme telle (`isError` de React Query).
   - Les confirmations restent des boutons sur place. On les teste ainsi ; les vraies fenêtres attendront qu'elles
     existent.
8. **Les trois exemples** (`usine/exemples/*.json`) : format 2, `creation` et `titre` ajoutés à la main.
   - **L'union sportive doit être adaptée** *(trouvé par Claude Code le 19 nov en préparant la couverture [lu])*.
     Aucune de ses fiches n'a de champ texte obligatoire : tous ses « nom » sont facultatifs. La règle du titre la
     refuserait. L'adaptation prévue : son champ « nom », celui qui sert à reconnaître la fiche, devient obligatoire. C'est
     un changement **déclaré** de l'exemple. Son témoin (212/212 et 28) sera recompté, et tout écart sera justifié
     ligne à ligne, jamais accepté en silence.
   - La médiathèque et les types ont déjà un titre possible (le titre d'un livre, le nom d'un article…). L'emprunt se
     reconnaît à son livre (b), si la règle de visibilité « toutes » est vérifiée.
   - **Un petit exemple d'essai dédié** (`usine/exemples/textes-obligatoires.json`, nouveau) : une seule fiche avec les
     cinq types de texte, chacun une fois obligatoire et une fois facultatif. Il sert uniquement aux preuves du
     morceau 12. *Pourquoi* : aucun exemple actuel n'a d'adresse web obligatoire, ni tous les types à la fois.
9. **La notice de l'artisan** (`usine/modele-app/CONTRAT-ECRANS.md`, nouvelle) : les onze règles en une page.
10. **L'inspecteur de l'essai** (`essais/juge-ecrans/`, jetable), l'instrument de la preuve. Il ne reçoit que ce que
    la preuve exige :
    - il lit `creation` et `titre`, et vérifie l'empreinte ;
    - il compare exactement ;
    - il reconnaît d'abord **une seule** ligne par l'étiquette d'essai, sinon « ambigu », puis le lien du titre dans
      cette ligne ;
    - il vérifie que le lien et l'adresse désignent **la bonne fiche**, avec le repère « sorte : titre » ;
    - il vérifie que le nom correspond au texte affiché ;
    - il n'attend que des zones « pret » pour conclure à une absence ;
    - *(version 3, remarque de Codex)* **une interdiction de voir n'est jugée que si toute la chaîne est prouvée.** La
      fiche d'essai connue existe en base, et le jumeau autorisé, dans la même passe, a retrouvé **cette même fiche**
      (le même identifiant), à cette adresse, sur la bonne page. La zone de la personne interdite est « pret » à la
      même adresse. Sinon, « non jugé ». Une liste vide et prête, seule, ne prouve rien ;
    - il joue **sans repli**.
11. **Les tests d'écran existants** : on inventorie ceux que le contrat touche, et ils restent des témoins.
12. **Un texte obligatoire n'est jamais vide** *(version 3, précisé après la vérification de Codex ; correction de
    classe, registre n° 63)*. Ce n'est pas une règle métier cachée : c'est le sens de « obligatoire », déjà montré au
    miroir. Ce morceau **touche le cœur** (le schéma) : les témoins des règles doivent rester identiques.
    - **Les champs couverts** : **tous** les champs obligatoires de type texte court, texte long, e-mail, téléphone et
      adresse web, c'est-à-dire tous ceux qui sont des textes dans le schéma (`usine/description.py:25`). Ne sont pas
      couverts : les listes de choix (une valeur fixe, jamais vide), les nombres, les montants, les dates, les oui/non.
    - **Le moyen** : les outils de ZenStack prévus pour ça, retirer les espaces et imposer une longueur minimale. Ils sont
      déclarés dans sa bibliothèque [lu par Codex], mais **leur comportement dans notre app n'est pas encore vérifié**.
      S'ils ne font pas exactement ce qu'il faut, on s'arrête et on rend compte, sans bricoler.
    - **Les écritures couvertes** : toutes celles qui passent par le client protégé de l'app, c'est-à-dire les
      formulaires, les actions et les appels directs à l'API de l'app.
    - **Les écritures non couvertes**, dites franchement : un accès direct à la base (SQL brut, outils de l'usine,
      migrations). Les données de départ doivent donc respecter la règle : un témoin compte, après leur chargement, les
      textes obligatoires vides en base. Il doit en trouver zéro.
    - **La première mesure, avant toute correction : prouver le défaut.** Un essai direct (une création, puis une
      modification, avec des espaces seuls) sur le squelette actuel dit si le texte vide est **vraiment enregistré**.
      Aujourd'hui, ce défaut est **lu**, pas rejoué. S'il ne se reproduit pas, le n° 63 du registre est reclassé, et ce
      morceau se réduit à ce qui reste vrai.

**Les choix écartés :**
- **Des marques invisibles pour les noms** (`data-testid`) : le juge vérifierait un nom que personne ne voit. *Pour
  l'état de chargement*, un attribut est accepté (`data-etat`), car ce n'est pas un nom : il double l'état visible et
  `aria-busy`.
- **Recopier la règle de grammaire dans le juge.**
- **Un nom par défaut calculé au moment de traduire.**
- **Promettre des titres uniques** en limitant les données.
- **Un titre sur plus d'un niveau de fiches liées**, ou qui traverse une fiche interdite.
- **L'IA « cartographe »** : plus tard, à l'étape des juges, pour les écrans d'agent qui s'écartent.

### 5. Les pièges et leurs parades

- **Une page qui charge ou qui a planté passe pour une page sans l'élément.** Parade : la règle 11. Le juge exige « pret »
  dans la bonne zone ; sinon « non jugé ».
- **Un titre vide, ou qui révèle une donnée interdite.** Parade : un titre obligatoire, un seul niveau, et la règle de
  visibilité (b).
- **Un contrôle du miroir qui réussit parce que le mot apparaît ailleurs.** Parade : le contrôle se fait dans le bloc de la
  fiche, à la ligne de l'action, dans la vue présentée.
- **Une preuve qui réussit faute de cas.** Parade : l'inventaire est écrit et vérifié avant de mesurer (§6).
- **Casser ce qui marche.** Parade : les témoins (§6), et la liste des tests d'écran touchés.
- **Les anciennes descriptions** sont refusées franchement (« format 1 »). Les fonctions de mise à niveau viendront avec
  l'évolution.
- **Le lecteur propose de mauvais noms.** Parade : les contrôles, et la lecture d'Arthur, avec la méthode du morceau 2.
- **Un `aria-label` qui ment.** Parade : la convention « le nom correspond au texte ».
- **Le juge et le traducteur lisent la même description.** C'est la règle, et l'empreinte prouve qu'il s'agit de la
  description validée.
- **Le coût** : 10 lectures de libellés sur l'abonnement, à petit volume.

### 6. Comment on prouve qu'elle marche (écrit AVANT le code)

**D'abord, l'inventaire** (avant toute mesure). Pour chaque exemple (la médiathèque, les types, l'union sportive), la
liste des parcours attendus, par rôle, fiche et action, avec ses permis, ses interdits et leurs jumeaux. Elle est
calculée depuis la matrice, puis **publiée avec son nombre**. On vérifie qu'elle n'est pas vide, et qu'elle couvre
chaque règle qui se voit à l'écran (1 à 9 et 11). **Un parcours non joué, ou une interdiction sans jumeau, est « non
jugé », jamais réussi.**

**Les démonstrations :**
1. **En mode sans repli**, sur les trois exemples refabriqués, l'inspecteur joue tout l'inventaire, aux 3 passes :
   - réussis = tous les parcours de l'inventaire ;
   - 0 échec, 0 « non jugé », 0 repli, 0 hésitation ;
   - toutes les mesures portent les empreintes d'une même version ;
   - une passe sur un navigateur **ralenti trois fois** donne les mêmes verdicts. Elle prouve ce ralentissement-là,
     pas l'indépendance à tous les délais.
2. **La couverture du miroir** : chaque nom de l'inventaire figure dans le bloc de sa fiche, à la ligne de son action,
   dans la vue présentée, pour les 3 exemples et les 10 briefs d'apprentissage (100 %).
3. **Le lecteur des libellés**, sur les 10 briefs :
   - 100 % des fiches principales reçoivent un nom de création ;
   - aucun doublon, aucun geste réservé ;
   - Arthur corrige au plus un nom sur cinq, avec la méthode du morceau 2.

**Ce qu'elle doit refuser (les sabotages)** : chacun est attrapé par la bonne pièce, **à chacune des 3 passes**.

| Pièce qui doit l'attraper | Sabotages | Réponse attendue |
|---|---|---|
| **Les contrôles de la description** | 1. pas de `titre` · 2. un titre numérique, daté ou long · 3. un titre facultatif · 4. un titre (b) alors qu'un rôle voit les deux sortes, mais seulement **ses propres** fiches désignées · 5. un nom de création égal à une étape de la même page · 6. une description de format 1 | refusée, avec la raison et la fiche |
| **Le miroir et la porte** | 7. un nom absent du bloc de sa fiche mais présent ailleurs · 8. deux actions au même texte **dans le même contexte** (deux noms identiques sur deux lignes différentes sont permis) · 9. la description modifiée après la validation · 10. la vue du miroir modifiée après la validation · 10 bis. une vue présentée qui découle d'une autre version de la description | le contrôle échoue en nommant le nom ; la porte refuse |
| **Le serveur** (morceau 12) | 24. sur **un petit exemple d'essai dédié** (une fiche qui a les cinq types de texte, chacun une fois obligatoire et une fois facultatif), par des **appels directs** hors du formulaire, **en création et en modification** : chaque champ obligatoire, vide puis fait d'espaces. Cela fait 5 types × 2 écritures × 2 valeurs = **20 cas**. En plus, le titre vide sur un exemple réel (les types) | chacun des 20 cas est refusé, et **la base ne change pas** (mêmes lignes, mêmes valeurs) |
| **L'inspecteur** | 11. la connexion sans identifiant · 12. le menu renommé · 13. le repère renommé · 14. le bouton de création renommé · 15. un bouton d'étape renommé · 16. le lien de la ligne sur un autre champ · 17. un mot ajouté au nom d'un champ · 18. un `aria-label` différent du texte · 19. un filtre caché (les données de départ contiennent une fiche qu'il exclut à tort) · 20. une zone sans `data-etat` · 21. une erreur de chargement · 22. une zone toujours « chargement » · 23. un lien de titre qui mène à la fiche désignée au lieu de la fiche (le cas du mouvement de stock) · 25. la fiche d'essai retirée, ou rendue invisible à son jumeau autorisé | 11 à 17 : « introuvable » · 18, 19 et 23 : « comportement faux » · 20 à 22 et 25 : « non jugé », **jamais** « interdiction respectée » |

**Les témoins (ce qui doit rester vrai, ou passer)** :
- **L'assembleur sur les trois exemples**, comme à la montée de Next.js [rapporté : `conception/montee-nextjs.md`] :
  - la médiathèque : règles 120/120, écrans **11 passés et 1 sauté** ;
  - les types : 267/267 et 17 ;
  - l'union sportive : 212/212 et 28, **recomptés après l'adaptation déclarée** (morceau 8), chaque écart étant
    justifié.

  Plus : les sabotages d'écran 8/8, les règles 35/41 avec effet, et la preuve du contrôle des failles 3/3.
- **Les tests d'écran touchés** par le contrat, listés : verts, ou changés avec une justification écrite.
- **Les témoins proches** :
  - *(version 3)* une fiche d'essai qui existe, que la personne autorisée voit, et qui est absente pour la personne
    interdite, dans une zone prête, à la même adresse. C'est **le seul** cas où le juge conclut « interdiction
    respectée » ;
  - une liste qui contient la fiche attendue ;
  - sur l'exemple dédié, des valeurs normales acceptées pour les cinq types, en création et en modification ; **les
    cinq champs facultatifs laissés vides, acceptés** (la correction ne doit pas refuser ce qui est permis) ;
  - après le chargement des données de départ, aucun texte obligatoire vide en base ;
  - une fiche (b) dont les fiches désignées sont visibles à tous ses rôles (« toutes ») : acceptée ;
  - une vue du miroir qui découle de la description validée : acceptée ;
  - deux fiches au même titre, reconnues par une seconde valeur visible ;
  - un `aria-label` identique au texte ;
  - un produit autorisé et un mouvement interdit, au même titre : le juge doit conclure sur **le mouvement** ;
  - une ancienne description refusée, avec le bon message, et une nouvelle acceptée ;
  - une validation d'essai, étiquetée comme telle.

**Le critère d'arrêt :**
- un témoin change : on s'arrête et on comprend ;
- l'inventaire est vide ou incomplet : on ne mesure pas ;
- Arthur corrige plus d'un nom sur cinq : on garde la règle fixe, visible au miroir ;
- l'inspecteur a encore besoin d'un repli, ou laisse un « non jugé », sur nos propres écrans : le contrat est
  incomplet, et on le complète avant la chaîne complète ;
- une correction en cours de route impose de rejouer tout l'ensemble concerné.

**Ce qui ne sera pas prouvé, même si tout passe :**
- l'accessibilité générale ;
- l'absence de toute règle cachée ;
- les classes « présent mais inutilisable », « session interdite reconnue » et « rejeu d'une modification », qui sont
  pour le vrai juge ;
- les écrans riches ;
- les vraies fenêtres de dialogue ;
- l'indépendance à tous les délais.

### 7. Le périmètre

**Ce qui est touché :**
- la description (format 2) ;
- le lecteur des libellés et la complétion ;
- le miroir et son contrôle ;
- la porte (l'empreinte de la vue et sa régénération, la validation d'essai) ;
- le traducteur des écrans ;
- **le traducteur du schéma** : le refus serveur d'un texte obligatoire vide (morceau 12). **Il touche le cœur**, d'où
  les témoins des règles ;
- le squelette : l'accueil, les repères, les listes, les fiches, les formulaires, les états de chargement ;
- les trois exemples (l'union sportive adaptée, de façon déclarée) et un exemple d'essai dédié ;
- la notice de l'artisan ;
- l'inspecteur de l'essai ;
- les tests d'écran touchés, listés.

**Ce qui ne l'est pas** :
- les droits, la matrice, le calculateur ;
- les juges des règles et la sonde ;
- les six premiers lecteurs ;
- la vraie connexion ;
- le titre des lignes d'une fiche ;
- les écrans riches et les fenêtres de dialogue ;
- l'IA cartographe.

**La taille.** La première estimation (une journée et demie à deux jours) n'a pas été vérifiée, et la version 2 ajoute
du travail. Nouvelle estimation : **deux à trois jours, une vingtaine de fichiers**, à confirmer par la revérification.
**On n'allège pas les preuves pour tenir le délai.** Si la taille est dépassée, on s'arrête et on rend compte.

**Le risque** : élevé. Il y a donc les témoins, et la vérification après.

## Relecture

### Première relecture (16 nov) : Claude en ligne et une autre IA

Verdict « OK avec corrections » ; les 13 points ont été acceptés et intégrés. Synthèse archivée :
`archives/echanges-2026-11/relecture-contrat-et-juge-ecrans-2026-11-16.md`.

### Vérification par Codex (19 nov) : « à revoir »

Le fil : [`dialogue/2026-11-19-verification-contrat-noms-ecran.md`](../dialogue/2026-11-19-verification-contrat-noms-ecran.md).
Tous ses constats sur le code ont été vérifiés par Claude Code, et sont exacts [lu].

| Point de Codex | Réponse | Où, dans la version 2 |
|---|---|---|
| **Bloquant 1** : un chargement ou une erreur peut passer pour une absence | accepté | règle 11 (un signal positif « pret », l'erreur distincte de la liste vide, une attente bornée, « non jugé ») ; morceau 7 ; sabotages 20 à 22 ; témoins proches |
| **Bloquant 2** : un titre vide ou inaccessible ; le tri par fiche liée | accepté | les règles du titre (obligatoire, un niveau, la visibilité (b)) ; le tri sorti du contrat ; sabotages 2 à 4 et 23 ; témoins proches |
| **Bloquant 3** : la couverture du miroir, au bon endroit | accepté | morceau 4 (le bloc de la fiche, la ligne de l'action, la vue présentée) ; morceau 5 (l'empreinte de la vue) ; sabotages 7 à 10 |
| **Bloquant 4** : une preuve qui réussit faute de cas | accepté | §6 : l'inventaire d'abord, et le « non jugé » jamais compté comme réussi |
| **Bloquant 5** : la chaîne des versions et des réponses | accepté | morceaux 1, 3 et 5 : le format, le champ ajouté validé au miroir, les corrections à la main, la validation d'essai étiquetée |
| La fausse alarme du mouvement de stock | accepté | règle 3 (sorte et titre) ; sabotage 23 ; témoin proche |
| Les tests existants ne suivront pas tout seuls ; « 11 passés et 1 sauté » | accepté ; mon « 11 écrans » était inexact | §3 ; témoins ; morceau 11 |
| Les étiquettes et les fenêtres | accepté | règle 8 ; morceau 7 (les confirmations sur place, les fenêtres plus tard) |
| La méthode du lecteur ; le ralenti ne prouve que trois fois | accepté | morceau 2 ; §6 |
| La taille et l'estimation | accepté | §7 (réestimée, à confirmer) |

### Revérification par Codex de la version 2 (19 nov) : « à revoir » sur trois garanties

Les trois constats sont exacts. J'ai vérifié le deuxième dans le code [lu] : `vues.tsx:89-92`.

| Point de Codex | Réponse | Où, dans la version 3 |
|---|---|---|
| **Bloquant** : le bon rôle ne garantit pas la bonne fiche liée (« les siennes ») | accepté | les règles du titre : (b) seulement si chaque rôle voit **toutes** les fiches désignées, sinon refus, sans élargir de droit ; contrôles (morceau 1) ; sabotage 4 précisé ; témoin |
| **Bloquant** : « obligatoire » ne veut pas dire « non vide » | accepté. C'est **un défaut probable** de l'usine pour tous les textes obligatoires (registre n° 63 : transmis vide [lu] ; l'enregistrement est à confirmer par la première mesure) | les règles du titre ; morceau 12 (le serveur refuse un texte vide ou fait d'espaces) ; un titre vide donne « non jugé » ; sabotage 24 ; témoins |
| **Bloquant** : une liste vide et prête ne prouve pas une interdiction | accepté | morceau 10 (la chaîne complète : la fiche connue, le jumeau qui retrouve la même fiche, la même adresse, une zone prête) ; sabotage 25 ; le témoin du §6 réécrit |
| La vue empreintée doit être celle de la description validée | accepté | morceau 5 (la porte régénère et compare) ; sabotage 10 bis |
| Deux actions au même texte : dans le même contexte seulement | accepté | sabotage 8 précisé |
| *(Vérification de la version 3)* Prouver la portée annoncée du morceau 12, pas seulement le titre | accepté | morceau 12 (les champs couverts, le moyen, les écritures couvertes et non couvertes) ; sabotage 24 étendu (création et modification, plusieurs champs, base inchangée) ; témoins (valeurs normales, champ facultatif vide, données de départ) |
| *(Vérification de la version 3)* Le défaut est lu, pas rejoué | accepté | morceau 12 : prouver d'abord le défaut par un essai direct ; registre n° 63 reformulé |
| *(Vérification des précisions)* Le passage sur le titre et la relecture disaient encore « enregistre » | accepté | les règles du titre et ce tableau disent « transmis [lu], enregistrement à confirmer » |
| *(Vérification des précisions)* Cinq types annoncés, trois essayés « s'ils existent » | accepté | un exemple d'essai dédié, avec les cinq types : 20 cas de refus et 5 témoins facultatifs (sabotage 24, témoins, morceau 8) |
| *(Trouvé par Claude Code en préparant la couverture)* L'union sportive n'a aucun texte obligatoire | déclaré avant le code | morceau 8 : son « nom » devient obligatoire, et son témoin est recompté et justifié |

- **Décision d'Arthur** : « oui » au principe (19 nov). Le « go » au code attend la validation de Codex.

## Après : le compte rendu

*(Le compte rendu complet s'écrira à la fin du développement, et Codex le vérifiera. En attendant, voici les mesures,
au fur et à mesure.)*

### Le journal du développement

**19 nov, les témoins « avant »** [rejoué]. Les trois exemples ont été fabriqués sur le code d'aujourd'hui, avant tout
changement :
- les types : règles 267/267, écrans 17 passés ;
- la médiathèque : règles 120/120, écrans 11 passés et 1 sauté ;
- l'union sportive : règles 212/212, écrans 28 passés.

Cela confirme les chiffres de la montée de Next.js. Les journaux sont dans
`C:\Users\BAMBARA Arthur\essais\contrat-noms\avant-*.log`, et les apps dans `runs/20261119-21*`.

**19 nov, la première mesure : le défaut n° 63 est confirmé** [rejoué].
- **L'essai** : par le client protégé de l'app (celui des écrans), hors du formulaire, une valeur vide puis faite
  d'espaces dans chaque champ texte obligatoire, en création et en modification.
- **Le résultat** : sur les types et la médiathèque, **34 écritures sur 34 ont été enregistrées**, et aucune n'a été
  refusée. Cela vaut pour le texte court, le texte long, le téléphone et l'e-mail.
- **La rigueur de la mesure** : chaque cas a eu son témoin (une écriture valide d'abord), et l'écriture est jugée sur
  l'état de la base.
- **Ce qui n'a pas été jugé** : 3 cas, des fiches qu'aucun rôle ne crée (le profil des types, le livre et le membre de
  la médiathèque, pour la création seulement).
- **Les fichiers** : l'essai `essais/contrat-noms/essai-obligatoire.mts`, les résultats `defaut-63-*.json`.
- **En passant** : un e-mail fait seulement d'espaces est accepté aussi. Le format des e-mails n'est donc pas contrôlé
  côté serveur ; c'est hors du contrat, et noté pour plus tard.

Le morceau 12 est donc justifié. Il reste à couvrir l'adresse web, avec l'exemple dédié.

**20 nov, l'inventaire des parcours, écrit avant toute mesure.** Il est calculé par
`C:\Users\BAMBARA Arthur\essais\contrat-noms\inventaire.py`, depuis la matrice et la description de chaque exemple
fabriqué le 19 nov, jamais depuis les écrans. Le détail est dans `inventaire.md` et `inventaire-<exemple>.json`.

| Exemple | Parcours | Voir (permis / interdits) | Créer | Étapes | En un clic |
|---|---|---|---|---|---|
| La médiathèque | **23** | 6 / 2 | 1 / 2 | 3 / 6 | 1 / 2 |
| Les types | **28** | 8 / 5 | 3 / 6 | 2 / 4 | — |
| L'union sportive | **40** | 8 / 6 | 7 / 7 | 6 / 6 | — |
| **Total** | **91** | | | | |

- **Chaque règle visible du contrat** (1 à 9, et 11) est exercée par au moins un parcours, dans chacun des trois
  exemples.
- **Chaque interdit a son jumeau permis**, qui devra retrouver la même fiche d'essai.
- **Une nouveauté par rapport à l'essai du juge d'écrans** : quand un rôle ne voit que « les siennes », l'inventaire
  vérifie aussi qu'il **ne voit pas celle d'un autre** du même rôle. L'emprunt d'un autre adhérent, par exemple, doit
  rester invisible. L'ancien inventaire comptait seulement « il voit ».
- **Non couvert, et déclaré** : ce que le gérant des types voit des adresses **au travers** d'une commande. C'est
  affiché dans une autre page, donc hors de ces parcours ; la page des adresses, elle, lui reste interdite, et c'est
  jugé.
- **Hors du contrat** : les profils (le membre de la médiathèque, le profil des types) et les lignes (les lignes de
  commande).
- **Les limites déclarées** :
  - où apparaît un bouton de création en un clic suit la règle d'affichage de l'usine, une logique partagée avec le
    constructeur ;
  - modifier et supprimer ne sont pas dans l'inventaire : ce ne sont pas des règles du contrat, et les tests d'écran de
    l'usine les jugent (ce sont des témoins).
- **Les empreintes de l'inventaire**, prises avant toute mesure :
  - `inventaire-mediatheque.json` : `5c17d8286d9bf429…` ;
  - `inventaire-types.json` : `8b5170e4afde041b…` ;
  - `inventaire-union-sportive.json` : `14da47307beb2ca2…` ;
  - `inventaire.py` : `e4e167120d466613…`.
- **Une condition pour la mesure** : les matrices doivent garder leurs empreintes, puisque le contrat ne touche aucun
  droit :
  - la médiathèque : `c8c547fb266a…` ;
  - les types : `5d27e151634c…` ;
  - l'union sportive : `95aa8255d325…`.

  Elles sont déjà identiques entre le 13 et le 19 nov pour la médiathèque, preuve qu'elles sont stables.

**20 nov, l'inventaire en version 2, après la vérification de Codex, toujours avant toute mesure.** Codex a recompté les
91 parcours et les 46 jumeaux [rejoué sur les fichiers], et il a trouvé deux trous, qui étaient réels :
- **la création d'un livre** (la médiathèque) avait disparu sans être signalée, puisque personne ne crée de livre et
  donc qu'aucun jumeau n'existe. Elle a maintenant **3 parcours « absence »**, pour les trois personnes qui voient les
  livres : le bouton de création doit être absent. C'est un contrôle d'affichage, **compté à part**. Le refus du serveur
  est déclaré **non couvert**, faute de jumeau ;
- **l'adresse et le gérant** (les types) : le gérant lit à bon droit une adresse liée à une commande. L'interdit est donc
  écrit avec sa **condition** : la fiche d'essai n'est désignée par aucune commande.

En plus :
- **chaque fiche d'essai a un identifiant fixe**, partagé par un interdit et son jumeau, et vérifié par le programme :
  aucun interdit ne porte sur une autre fiche que son jumeau ;
- chaque interdit écrit sa **preuve** : le rejeu, sur la même fiche, ne change rien ; le bouton est absent si la page
  est accessible, sinon « page inaccessible » est noté.

**Total : 94 parcours** (la médiathèque 26, les types 28, l'union sportive 40). **Empreintes de la version 2** :
`inventaire-mediatheque.json` `4d74bddd17ddf30d…`, `inventaire-types.json` `645e1afc28dec1a5…`,
`inventaire-union-sportive.json` `c0ba0f6fbc96c07e…`, `inventaire.py` `825c23a1a926d6a1…`. Les empreintes de la version
1 sont remplacées, et les matrices sont inchangées.

**20 nov, la répartition à deux** (décision d'Arthur). Claude Code construit le côté usine ; **Codex construit le juge**
(l'inspecteur sans repli, sa maquette conforme, les sabotages côté écran) et devient responsable de l'inventaire. Chacun
vérifie l'autre. L'interface entre les deux côtés a été proposée par Claude Code et **confirmée par Codex**, avec ses
précisions (fil [Codex, auteur du juge du contrat](../dialogue/2026-11-20-juge-du-contrat-par-codex.md)).

**20 nov, la description de format 2 : faite et prouvée** (morceaux 1 et 3).
- **Ce qui a été fait** :
  - `usine/description.py` : le numéro de format, `creation` et `titre`, la normalisation des noms, les contrôles du
    contrat (le titre (a) ou (b) avec la portée « toutes », un nom par action, les gestes réservés) ;
  - `usine/comprendre/completion.py` (nouveau) : la complétion avant le miroir, et `charger_lecture`, qui complète une
    lecture d'avant le format 2 au chargement, elle et jamais une description validée ;
  - `usine/comprendre/__init__.py`, `usine/miroir/contenu.py`, `usine/miroir/preuve_reponses.py`, `usine/repetition.py`,
    `usine/outils/photo.py` : branchés sur la complétion ;
  - les trois exemples en format 2, l'union sportive adaptée de façon déclarée.
- **La preuve** [rejoué] : `python -m usine.preuve_description` donne **21 sur 21**. Il y a 12 sabotages (le titre absent,
  numérique, daté, long, facultatif ; un titre tiré d'une fiche que le gérant ne voit pas en entier ; le format 1…),
  chacun refusé avec la bonne raison et la bonne fiche, et 9 témoins (les trois exemples ; la complétion qui retrouve les
  choix faits à la main ; le « Libellé » ; jamais un titre tiré d'une fiche invisible).
- **Une régression, trouvée et corrigée.** La preuve des réponses du miroir, qui rejoue les 67 anciennes lectures,
  plantait, parce que le format 2 refusait ces lectures. Le remède : une lecture non validée est complétée au
  chargement. Après la correction : **0 défaut**, comme avant. Il y a deux écarts, **expliqués au cas près** :
  - **+20 questions « nom »** : 22 « Libellé » ajoutés, moins 2 fiches retirées par la variante du miroir ;
  - **−1 proposition** : la « Dépense » de la location événementielle avait déjà une proposition « Libellé ».

  Aucune autre question n'a changé sur les 67 lectures (comparaison lecture par lecture, avant et après).
- **Les témoins de l'usine** [rejoué], refabriqués le 20 nov :
  - les types : **identiques** (règles 267/267, écrans 17 passés) ;
  - la médiathèque : **identique** (règles 120/120, écrans 11 passés et 1 sauté) ;
  - l'union sportive : écrans **identiques** (28 passés), mais règles **185/185 au lieu de 212/212**.
- **L'écart de l'union sportive, expliqué.** Les 27 vérifications en moins concernent uniquement l'administrateur, sur
  les quatre fiches à circuit. Le juge des règles rejoue chaque étape avec les champs facultatifs vides puis remplis, et
  essaie de les vider pendant l'étape. Le seul champ de ces fiches, le « nom », est devenu obligatoire : ces
  combinaisons n'existent plus. **Aucune garantie n'est retirée sur un champ qui existe.** C'est la conséquence de
  l'adaptation déclarée (morceau 8).
- **La carte des blocs et le banc de la matrice** : inchangés.

**20 nov, le traducteur et le squelette : faits** (morceaux 6 et 7).
- **Ce qui a été fait** :
  - le traducteur (`usine/traduire/ecran.py`) lit `creation` et `titre` dans la description. Pour chaque lien, le champ
    montré dans la liste de choix est le titre de la fiche désignée. Le tri suit la règle 6 : les fiches à circuit
    restent « les plus récentes d'abord » ; un titre tiré d'un champ trie par ce champ ; un titre tiré d'une fiche
    désignée trie par ordre de création ;
  - le squelette (`usine/modele-app`) :
    - les boutons de connexion portent l'identifiant : `personne 1 · adherent_1` ;
    - chaque zone de données porte son état : chargement, erreur (affichée comme telle, jamais comme une liste vide) ou
      prêt ;
    - dans une liste, le titre vient en premier, et c'est lui le lien vers **cette** fiche ;
    - la page d'une fiche a pour titre « Sorte : titre », par exemple « Emprunt : Germinal » ;
    - chaque étiquette est reliée à son champ, listes de choix comprises, avec des identifiants uniques. « (facultatif) »
      est relié au champ comme une aide.
- **Les témoins de l'usine** [rejoué], refabriqués après le changement :
  - la médiathèque : **identique** (règles 120/120, écrans 11 passés et 1 sauté) ;
  - les types : **identiques** (règles 267/267, écrans 17 passés) ;
  - l'union sportive : règles 185/185, comme après la description. Pour les écrans, **un blocage non expliqué**, une
    fois :
    - au premier lancement, le test « administrateur : menu et boutons de création » n'a pas pu ouvrir la page des
      adhésions dans le temps imparti, puis la suite est restée bloquée environ 9 minutes et demie ;
    - relancée sur la même app : **28 passés** ;
    - refabriquée à neuf : **28 passés**.

    La cause n'est pas trouvée. Le blocage est noté et reste à surveiller ; il n'est pas compté comme réussi.
  - les matrices des trois apps gardent leurs empreintes (`c8c547fb266a…`, `5d27e151634c…`, `95aa8255d325…`).
- **Un contrôle de l'auteur, qui n'est pas une preuve** [rejoué, à la main] : sur la médiathèque, l'adhérent emprunte
  « Germinal » en un clic. La ligne de l'emprunt commence par « Germinal », son lien ouvre cet emprunt, la page a pour
  titre « Emprunt : Germinal », et le champ « Ouvrage » se trouve par son étiquette. Seul le juge de Codex dira si les
  onze règles sont tenues.
- **Une trouvaille, en faisant ce contrôle** [rejoué]. Next.js 16, avec le réglage `cacheComponents` du squelette, garde
  la page qu'on vient de quitter **dans la page, cachée** (`display: none`). Sa zone y reste, marquée « prêt ».
  - Un lecteur d'écran ne la voit pas, et Playwright non plus quand on cherche par rôle.
  - Mais un sélecteur CSS simple la trouve : un juge pourrait conclure sur la zone d'une autre page.
  - **La parade proposée à Codex** : seules les zones **visibles** comptent. Ce n'est pas un défaut de l'usine, c'est
    le fonctionnement voulu de Next.js.

**20 nov, la porte : la validation désigne la description exacte** (morceau 5, première partie).
- **Ce qui a été fait** (`usine/miroir/porte.py`, `usine/assembler.py`) :
  - le dossier de chaque fabrication reçoit un `validation.json` qui désigne `01-description.json`, le fichier que
    lisent le traducteur et le juge, avec l'empreinte de ses octets (SHA-256) ;
  - **un essai** est marqué `"essai": true` et « essai — non validée par un client » ;
  - **une app de client** doit être, à l'octet près, la description que le client a validée ; sinon la porte se ferme ;
  - la description n'est plus écrite qu'à un seul endroit (`ecrire_description`), pour la validation comme pour la
    fabrication : mêmes octets, même empreinte.
- **La preuve** [rejoué] : `python -m usine.miroir.preuve_porte <dossier>` donne **0 échec**, sur deux lectures copiées.
  Les anciens contrôles passent toujours, et trois nouveaux s'y ajoutent :
  - la description validée, relue et réécrite comme le fait la fabrication, garde ses octets : acceptée ;
  - un caractère modifié dans la description fabriquée : refusée « à l'octet près » ;
  - un essai est bien marqué comme tel, avec l'empreinte du fichier.
- **Les fabrications** [rejoué] :
  - les trois exemples refabriqués, **témoins identiques** (120/120 et 11 + 1 sauté ; 267/267 et 17 ; 185/185 et 28),
    matrices inchangées. Chaque `validation.json` porte l'empreinte exacte de son `01-description.json` ;
  - **une vraie fabrication « validée par un client »**, sur une copie de lecture (les dossiers de maintenance) : 170/170
    et 38 écrans passés. L'empreinte du fichier fabriqué est **identique** à celle que le client a validée.
- **Reste de ce morceau** : l'empreinte de la vue du miroir présentée au client, et sa régénération au moment de
  valider. Ils viendront avec le miroir (morceau 4), dont ils dépendent.

**20 nov, un texte obligatoire n'est jamais vide : fait et prouvé par l'auteur** (morceau 12, et l'exemple dédié du
morceau 8). À vérifier par Codex.
- **Ce qui a été vérifié avant de coder** [lu, ZenStack 3.9.7 dans le squelette] :
  - `@trim` et `@length` existent dans sa bibliothèque ;
  - son client valide chaque écriture avec ces règles, droits ou pas (`@zenstackhq/orm`, validation des entrées active
    par défaut) ;
  - **il les applique dans l'ordre écrit** (`@zenstackhq/zod`). L'ordre compte : `@trim @length(1)` retire les espaces
    puis exige un caractère ; dans l'autre ordre, « ␣␣␣ » passerait la longueur, puis serait enregistré vide.
- **Ce qui a été fait** :
  - `usine/traduire/schema.py` : chaque champ **obligatoire** qui est un texte dans la base reçoit `@trim @length(1)`.
    C'est la classe entière : texte court, texte long, e-mail, téléphone, adresse web. Les champs facultatifs ne sont
    pas touchés. Sur les exemples, la règle tombe sur 5 champs (l'exemple dédié), 8 (les types), 4 (la médiathèque) et
    7 (l'union sportive), exactement les obligatoires de texte ;
  - `usine/exemples/textes-obligatoires.json` (nouveau) : une fiche « contact » avec les cinq sortes de texte, chacune
    une fois obligatoire et une fois facultative.
- **La preuve** : `C:\Users\BAMBARA Arthur\essais\contrat-noms\preuve-textes-obligatoires.mts` (empreinte
  `bf4e5056841b9f31…`), **le même script avant et après**. Un refus ne compte que si l'appel échoue **et** que la table
  entière est identique (toutes les lignes, toutes les valeurs). Il ne compte « pour la bonne raison » que si l'entrée est
  refusée comme invalide **en nommant le champ** : un refus des droits ne compte pas.

  | Mesure [rejoué] | Avant la correction | Après |
  |---|---|---|
  | **Les 20 cas** (5 sortes × création, modification × vide, espaces) | **0 refusé sur 20** : tous enregistrés | **20 refusés sur 20**, tous pour la bonne raison |
  | En plus, non prévu d'avance : `updateMany`, `upsert`, `createMany` | 0 refusé sur 30 | **30 refusés sur 30**, pour la bonne raison |
  | Témoins : valeurs normales acceptées, facultatifs vides acceptés (`null`, ce qu'envoie le formulaire, et `''`), aucun texte obligatoire vide après les données de départ | 33 sur 33 | **33 sur 33** |
  | Témoins de l'usine sur l'exemple dédié | règles 13/13, écrans 6 | **identiques** |

  - La forme `{ set: … }` **n'existe pas** dans ZenStack 3.9.7 : elle est refusée même avec une valeur normale. Ses 10
    cas sont « non jugeables », comptés à part.
  - **Le titre vide sur un exemple réel** (les types) : 30 refusés sur 32, tous pour la bonne raison. Les 2 non
    jugeables sont la création d'un profil, qu'aucun rôle ne fait.
- **L'essai du 19 nov, rejoué tel quel** [rejoué] : sur les mêmes cas, **les 34 écritures enregistrées le 19 nov sont
  refusées, les 34** (30 sur les types, 4 sur la médiathèque). Les 3 non jugeables restent les mêmes.
- **Les témoins de l'usine** [rejoué], refabriqués après la correction : la médiathèque (120/120, 11 + 1 sauté), les
  types (267/267, 17), l'union sportive (185/185, 28) sont **identiques**, et les matrices inchangées.
- **Un changement de comportement, déclaré** : « ␣␣Valeur␣␣ » est désormais enregistré « Valeur », pour les champs
  obligatoires seulement. Avant, il l'était avec ses espaces.
- **Non couvert, comme prévu** : un accès direct à la base (SQL brut, migrations). Le client « brut » du testeur, lui, est
  un client ZenStack : il applique aussi la règle, et les données de départ la respectent.
- **Deux observations, hors du morceau** :
  - la grande zone de texte (`texte_long`) du formulaire n'a pas l'attribut `required` : le navigateur laisse partir une
    présentation obligatoire vide. Le serveur la refuse désormais, et le formulaire affiche « Refusé : » suivi d'un
    message technique de ZenStack. C'est à proposer, pas fait ;
  - **un incident de mesure** : sur la fabrication de l'exemple dédié, la compilation a pris 2 422 s au lieu d'environ
    50 s. Le processeur était à 100 % et il ne restait que 2,4 Go de mémoire libre ; les autres apps se sont ensuite
    compilées en temps normal. La cause n'est pas établie (peut-être le travail de Codex en même temps). Le résultat
    n'en dépend pas, seulement le temps.
- **Une erreur de ma part, rattrapée** : mon premier script de mesure enchaînée passait un chemin faux aux preuves (une
  fonction PowerShell renvoie aussi ce qu'elle affiche). Les preuves n'avaient pas tourné ; elles ont été rejouées à la
  main sur les mêmes apps. Les chiffres ci-dessus viennent de ces rejeux.

**20 nov, les témoins lourds, sur la médiathèque finale** (`runs/20261120-114415-mediatheque`, après le traducteur, le
squelette, la porte et le refus des textes vides) [rejoué] :
- **le contrôle des failles** (`python -m usine.preuve_audit`) : 3 sur 3, comme le 13 nov ;
- **les règles cassées exprès** (`usine/preuve_regles.mts`) : 35 attrapées sur 57, 22 survivantes. **Les 57 mutants sont
  identiques à ceux du 13 nov**, dans le même ordre et avec le même verdict (comparaison des deux `preuve-regles.json`).
  C'est attendu : la correction touche les champs, pas les règles d'accès ;
- **les sabotages d'écran** (`python -m usine.preuve_ecrans`) : 8 sur 8 attrapés, et l'app intacte passe. Ils ont pris
  443 s, contre 69 minutes le 13 nov ; la raison n'est pas cherchée.

Tous les témoins écrits d'avance au §6 sont donc identiques sur cette version.

## Petit lexique

- **Nom accessible** : ce qui est écrit sur un bouton, un lien ou un champ, tel qu'un lecteur d'écran le lit.
- **Description** : le fichier qui dit tout de l'app, validé par le client au miroir.
- **Miroir** : la page qui montre au client, en français, ce que l'app fera.
- **Porte** : le contrôle qui empêche de fabriquer une description non validée, ou modifiée depuis.
- **Empreinte** : un code calculé sur le contenu d'un fichier ; si un seul caractère change, elle change.
- **Inventaire** : la liste des parcours attendus, écrite avant de mesurer.
- **Non jugé** : le juge ne peut pas conclure. Ce n'est jamais une réussite.
- **Fiche principale** : une fiche qui a sa propre page.
- **Repli** : un second moyen de trouver un élément. Le contrat sert à ne plus en avoir besoin.
