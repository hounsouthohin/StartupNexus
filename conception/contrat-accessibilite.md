# Le contrat d'accessibilité : les noms à l'écran

> **Taille** : critique (relevé par la relecture : c'est l'entrée de toute la chaîne et le contrat d'un juge) ·
> **Statut** : relu, corrections intégrées ; en attente du « go » d'Arthur
> **Dates** : écrit le 16 nov 2026 · relu le 16 nov (Claude en ligne et une IA d'un autre fournisseur) · validé le … ·
> fini le …

> **Règles d'écriture** (demandées par Arthur le 14 nov) :
> - des **noms**, jamais des codes seuls ;
> - des mots simples ; un terme technique vient après l'explication, entre parenthèses, et seulement s'il sert ;
> - pour chaque chose qu'on construit, **pourquoi** on la construit.

## Avant : la conception

### 1. En mots simples

- **Ce que c'est.** Une règle : **tout nom qu'un juge cherche à l'écran vient de la description, et la description est
  montrée au client** (dans le miroir). L'écran affiche ce nom, le juge cherche ce nom, et personne n'en invente un autre.
  En image, un immeuble : le plan signé dit « salle 204 », la plaque sur la porte dit « salle 204 », et le visiteur
  cherche « salle 204 ». Aujourd'hui, certaines plaques sont gravées par l'atelier selon sa propre règle, sans figurer
  sur le plan, et le visiteur doit deviner.
- **Pourquoi on le fait.** L'essai du juge d'écrans l'a montré : l'inspecteur tient, mais il ne retrouve un bouton que
  si son nom est connu d'avance.
  - Sur nos propres écrans, **aucun parcours autorisé n'a réussi sans repli** (connexion, nom de création, ouverture
    d'une fiche par sa ligne, début d'un libellé, majuscules).
  - Sur l'app de l'agent, des parcours ont échoué faute de noms ou de règles écrits dans la description.
  - Sans contrat, chaque nouvelle app ajouterait un repli à l'inspecteur. C'est la rigidité qui s'empile.
- **Ce n'est pas une liste de mots imposés.** Les mots changent avec chaque client : « Produits » chez l'un,
  « Instruments » chez l'autre. Seule la **correspondance** est fixe : l'écran dit ce que le client a vu au miroir. Et
  les noms gardent leur souplesse : le lecteur des libellés (une IA) les propose, le client les corrige au miroir, la
  description les fige.
- **Ce qu'on verra à la fin.**
  - Le miroir montre, pour chaque fiche, les noms qui apparaîtront à l'écran : le menu, le bouton de création, les
    boutons d'étape, et ce qui permet de reconnaître la fiche.
  - L'app affiche exactement ces noms.
  - L'inspecteur parcourt les trois exemples de l'usine **sans aucun repli**.

### 2. À quoi ça sert

Le contrat est la langue commune de trois parties :
- **la description**, validée par le client ;
- **ceux qui construisent les écrans** : le traducteur de l'usine, et plus tard l'artisan (Claude Code dans l'atelier) ;
- **ceux qui les jugent** : l'inspecteur d'écrans.

Il vient avant la chaîne complète, parce que le juge de cette chaîne jugera les écrans de l'artisan. Sans nom commun,
il dirait « introuvable » pour des raisons de vocabulaire, pas de qualité.

### 3. Ce qui existe déjà

| Nom à l'écran | D'où il vient aujourd'hui | Montré au miroir ? | Le problème |
|---|---|---|---|
| Lien du menu (« Produits ») | le nom pluriel de la fiche, dans la description, avec une majuscule ajoutée à l'affichage | oui (sans la majuscule) | pas imposé à l'agent : l'app du brief seul ne nomme pas « Produits » |
| Champ d'un formulaire | le libellé du champ, dans la description | oui | le nom lu par la machine ajoute « (facultatif) » et, pour une liste de choix, la valeur choisie : l'inspecteur devait comparer le début |
| Bouton du formulaire de création | une règle de grammaire dans [ecran.py:50-51](../usine/traduire/ecran.py#L50-L51) : « Nouveau / Nouvel / Nouvelle » + nom | **non** | hors de la description ; faux devant un h aspiré (« Nouvel hangar ») |
| Bouton de création en un clic (« Emprunter » sur un livre) | le « verbe de création » proposé par le lecteur des libellés | **non** | jamais validé. Il ne sert que si la fiche n'a aucun champ obligatoire et un seul lien ; sinon il est calculé pour rien |
| Boutons d'étape (« Confirmer ») | proposés par le lecteur des libellés | **non** | jamais validés |
| Ce qui ouvre une fiche dans une liste | le premier morceau de la ligne : les fiches liées d'abord, puis les champs ([vues.tsx:36-47](../usine/modele-app/components/vues.tsx#L36-L47)) ; pour l'affichage et le tri, la règle « premier champ texte » ([modele.py:80](../usine/traduire/modele.py#L80)) | **non** | un devis s'ouvre par le nom de son client. Un mouvement de stock n'a aucun champ texte |
| Connexion simulée | l'accueil du squelette : « personne 1 », « personne 2 » ([page.tsx:20](../usine/modele-app/app/(app)/page.tsx#L20)) | — | l'identifiant `gerant_1` n'apparaît pas |
| Règle métier ajoutée par l'artisan | nulle part | — | l'agent a filtré de lui-même les devis « confirmés » |

**Ce qu'on réutilise :**
- le lecteur des libellés, le septième lecteur ;
- la question du miroir qui existe déjà : « Votre brief ne disait pas comment reconnaître certaines fiches ; nous
  avons choisi : … » (réponse : oui, ou un autre nom) ;
- **la porte du miroir** ([porte.py](../usine/miroir/porte.py)). Elle enregistre déjà l'empreinte de la description
  validée et la vérifie avant de fabriquer ;
- les tests d'écran de l'usine, qui lisent déjà les noms dans la notice produite par l'usine : ils suivront tout
  seuls ;
- l'inspecteur de l'essai, comme instrument de preuve.

### 4. Comment on la construit

**Les dix règles du contrat.** Ce sont les six de l'essai, revues après vérification du code, plus les ajouts de la
relecture. Les règles 3, 7 et 9 sont des **conventions du squelette** de l'usine, imposées aussi à l'artisan. Ce ne
sont pas des exigences de la norme d'accessibilité.

| # | Règle | Source du nom |
|---|---|---|
| 1 | **Connexion d'essai** : chaque bouton de connexion simulée contient l'identifiant de la personne, en mot entier (« personne 1 · gerant_1 ») | les personnes d'essai (rôle + numéro) |
| 2 | **Menu** : le lien porte le nom pluriel de la fiche | la description |
| 3 | **Repère de page** : une page de liste a pour titre principal le nom pluriel de la fiche ; une page de fiche, le titre de cette fiche. L'inspecteur attend ce repère avant de compter quoi que ce soit | la description |
| 4 | **Bouton de création** : son nom est celui que la description donne à la fiche | **nouveau** : `creation`, pour chaque fiche principale |
| 5 | **Boutons d'étape et de création en un clic** : leur nom est celui de la description | la description (existe déjà) ; **désormais montré au miroir** |
| 6 | **Ce qui reconnaît une fiche** : chaque fiche principale déclare son titre. Dans une liste, c'est le premier morceau de la ligne et **le lien qui ouvre la fiche, dont le nom est exactement le titre**, sans préfixe ni suffixe. Partout ailleurs (listes de choix, fiche liée, tri), c'est ce qui la montre | **nouveau** : `titre` = un champ de type texte court de la fiche (jamais un texte long), **ou** la fiche qu'elle désigne (un emprunt se reconnaît à son livre) |
| 7 | **Libellé des états** : un état s'affiche avec le libellé de la description, et rien d'autre | la description |
| 8 | **Champs** : le nom d'un champ, tel que la machine le lit, est exactement son libellé. L'étiquette est reliée au champ (par `for` et `id`) ; « (facultatif) » et les aides sont une indication à part (`aria-describedby`), hors du nom | la description |
| 9 | **Un nom, une action** : dans le contexte d'une action, pour un rôle et un état donnés, deux éléments ne portent pas le même nom. Ce contexte, c'est la ligne, la fenêtre ouverte, ou la page pour les actions de page (création, étapes, création en un clic). Deux « Modifier » sur deux lignes différentes sont permis | — |
| 10 | **Pas de règle cachée** : l'artisan n'ajoute aucune règle (filtre, condition) que la description ne contient pas. S'il en voit une dans le brief, il la signale, et elle passe par le miroir. **C'est une obligation de l'artisan.** Les parcours en attrapent certaines manifestations, comme un filtre qui exclut une fiche d'essai, mais ils ne prouvent pas qu'il n'en reste aucune | — |

**Deux conventions s'appliquent à tous les noms :**
- **Le nom lu par la machine correspond au texte affiché.** Un élément trouvé par son nom est aussi vérifié par son
  texte visible (la règle « Label in Name » du W3C). Sans ça, un écran pourrait annoncer un nom au juge et en montrer un
  autre au client.
- **La forme exacte est fixée dans la description.** Les espaces sont normalisés à l'écriture de la description ; la
  comparaison est exacte, majuscules comprises, comme celle de Playwright avec `exact: true`. Une seule mise en forme
  est permise, écrite ici : **la majuscule initiale d'un nom affiché seul** (menu, titre de page). La description garde
  « produits » pour ses phrases, et l'écran affiche « Produits ».

Une « fiche principale » est une fiche qui a sa propre page : ni un profil, ni une ligne d'une autre fiche.

**Les morceaux, et pourquoi chacun :**

1. **La description** ([description.py](../usine/description.py)). Elle porte maintenant un **numéro de format** (2). Une
   ancienne description est refusée avec ce message : « format 1, attendu 2 ». Les libellés d'écran de chaque fiche
   reçoivent `creation` et `titre`. Les noms sont normalisés (espaces). Les contrôles refusent, sans jamais deviner :
   - une fiche principale sans l'un ou l'autre ;
   - un `titre` qui n'est ni un champ texte court de la fiche, ni une fiche qu'elle désigne ;
   - deux actions de même nom **sur une même page de l'usine**. L'usine sait ce qu'elle met sur chaque page :
     - la création ;
     - les étapes ;
     - les créations en un clic des fiches qui désignent celle-ci ;
     - les ajouts de lignes ;
     - les gestes réservés (Créer, Modifier, Supprimer, Enregistrer).

   *Pourquoi* : la description est la seule source validée. Un nom absent est refusé franchement, au lieu d'être
   deviné plus loin par une règle que personne n'a vue. Pour les écrans de l'artisan, que l'usine ne connaît pas
   d'avance, c'est l'inspecteur qui garantit l'unicité, en répondant « ambigu ».
2. **Le lecteur des libellés** ([lecteurs.py:335](../usine/comprendre/lecteurs.py#L335)). Il reçoit une consigne de
   plus : `creation` = le nom du bouton qui ouvre le formulaire de création, pour chaque fiche principale
   (« Planifier un événement », « Nouvelle facture »). Ses contrôles vérifient que le nom n'est pas vide et qu'il est
   distinct.

   *Pourquoi* : c'est l'articulation souple. L'IA propose un nom naturel, le client le corrige au miroir, la
   description le fige.
3. **La complétion, avant le miroir et seulement là** (l'étape « assembler la description » de
   [comprendre](../usine/comprendre/__init__.py#L239)).
   - Si le lecteur ne donne pas de nom de création, l'ancienne règle de grammaire le fabrique, mais il est désormais
     **visible** au miroir.
   - `titre` par défaut, dans cet ordre :
     - le premier champ texte court ;
     - sinon, la première fiche désignée (l'emprunt et son livre, le mouvement de stock et son produit) ;
     - sinon, un champ « Libellé » obligatoire, marqué « nécessaire ».
   - **Règle : un champ ajouté de cette façon n'existe que s'il est montré et validé au miroir avant la fabrication.**
     Il n'est jamais ajouté au moment de traduire. En effet, il change les données et les formulaires.

   *Pourquoi* : la règle de clôture existe déjà pour une fiche sans aucun nom ; on l'étend. Et l'emprunt de la
   médiathèque se crée en un clic, sans formulaire : un champ obligatoire de plus casserait ce clic. Le reconnaître à
   son livre ne casse rien. L'assembleur, lui, ne complète jamais une description en silence.
4. **Le miroir** ([contenu.py](../usine/miroir/contenu.py)). Chaque fiche affiche une ligne « À l'écran » : menu
   « Événements » · bouton « Planifier un événement » · reconnue par son « nom » · étapes « Confirmer » · en un clic
   « Emprunter ».
   - En rendez-vous, le client corrige, et Arthur modifie la description. Les réponses automatiques du miroir pour ces
     noms attendent le miroir complet, celui du premier vrai client.
   - **Un contrôle par programme** compare les noms que l'inspecteur cherchera, tirés de ses parcours, au **texte du
     miroir tel qu'il s'affiche**, et non la description à elle-même. Un nom absent du miroir arrête tout, et le contrôle
     le nomme.

   *Pourquoi* : un nom que le client n'a jamais vu n'est pas validé, quel que soit son auteur.
5. **L'empreinte de la description.** Le juge refuse de juger si l'empreinte de la description qu'il lit ne concorde pas
   avec celle que **la porte** a enregistrée à la validation. Ni l'app ni le juge ne fournissent cette référence. La
   porte la calcule déjà, sur le fichier tel quel ; c'est plus strict qu'une forme recalculée, puisque le moindre
   changement fait refuser. Le mode d'essai de l'usine (les trois exemples) écrit lui aussi son empreinte, marquée
   « essai — non validée par un client ».

   *Pourquoi* : pendant l'essai du juge d'écrans, l'inspecteur a lu par erreur la description d'une autre app, ce qui a
   produit une fausse alarme. Avec l'empreinte, cette erreur arrête le juge au lieu de fausser son verdict.
6. **Le traducteur d'écrans** ([ecran.py](../usine/traduire/ecran.py), [modele.py](../usine/traduire/modele.py)). Il
   lit `creation` et `titre` dans la description. La règle de grammaire quitte le traducteur, et la règle « premier
   champ texte » est remplacée partout par le `titre` déclaré : affichage d'une fiche liée, tri.

   *Pourquoi* : un concept, une seule source.
7. **Le squelette** (`usine/modele-app`).
   - Les boutons de connexion portent l'identifiant.
   - Chaque page a son repère (le titre principal).
   - Dans une liste, le titre vient en premier, et son lien porte exactement le titre.
   - Les étiquettes sont reliées à leur champ ; « (facultatif) » est une indication à part.

   *Pourquoi* : nos propres écrans doivent respecter le contrat sans exception. On le corrige à la source, au lieu
   d'apprendre à l'inspecteur à deviner.
8. **Les trois exemples** (`usine/exemples/*.json`) : format 2, `creation` et `titre` ajoutés à la main.
9. **La notice de l'artisan** (`usine/modele-app/CONTRAT-ECRANS.md`, nouvelle). Elle donne les dix règles en une page,
   pour Claude Code quand il construit des écrans, avec ce rappel : ce sont les juges qui vérifient.

   *Pourquoi* : les consignes expliquent, et ici c'est le juge qui impose.
10. **L'inspecteur de l'essai** (`essais/juge-ecrans/`, jetable). C'est l'instrument de la preuve. Il ne reçoit que ce
    que cette preuve exige :
    - il lit `creation` et `titre` dans la description et vérifie son empreinte ;
    - il compare exactement, majuscules comprises ;
    - il trouve d'abord **exactement une** ligne, par l'étiquette unique des données d'essai (sinon « ambigu »), puis le
      lien du titre dans cette ligne. Si deux fiches portent le même titre (deux emprunts du même livre), il reconnaît
      la ligne par une seconde valeur visible : la personne, la date ;
    - il vérifie que le texte affiché correspond au nom ;
    - il cherche d'abord dans une fenêtre de confirmation ouverte, et vérifie qu'elle correspond à l'action attendue ;
    - il joue **sans aucun repli** (le mode « sans repli » existe depuis le rejeu du 16 nov).

**Les choix écartés :**
- **Des marques invisibles pour les tests** (`data-testid`). Le juge vérifierait un nom que personne ne voit, pas ce
  que voit le client. Le contrat sert aussi les lecteurs d'écran des personnes malvoyantes : c'est de la vraie
  accessibilité.
- **Recopier la règle de grammaire dans le juge.** Le juge partagerait la logique du constructeur : si la règle est
  fausse, les deux se trompent ensemble. La seule mise en forme partagée est la majuscule initiale, écrite dans le
  contrat.
- **Un nom par défaut calculé au moment de traduire.** C'est exactement la situation d'aujourd'hui, une règle que
  personne n'a vue. Notre règle : refuser, jamais deviner.
- **Promettre des titres uniques**, en limitant les données (un seul emprunt par livre, par exemple). On ne restreint
  jamais les données pour faciliter un test : c'est l'inspecteur qui reconnaît la ligne autrement.
- **L'IA « cartographe »**, qui trouverait les noms sur l'écran. Plus tard, à l'étape des juges, pour les écrans
  d'agent qui s'écartent. Pas pour nos propres écrans, qui n'ont aucune excuse.

**Les outils établis :**
- Playwright cherche les éléments par leur rôle et leur nom, comme un lecteur d'écran ;
- le navigateur calcule ce nom selon la norme du W3C sur l'accessibilité (le « nom accessible ») ;
- Pydantic fait les contrôles de la description ;
- SHA-256 calcule les empreintes, comme la porte le fait déjà.

### 5. Les pièges et leurs parades

- **Casser ce qui marche.** La description est l'entrée de toute la chaîne. Parade : refabriquer les trois exemples,
  et tous les juges existants doivent donner les mêmes résultats qu'à la montée de Next.js (voir le §6).
- **Les anciennes descriptions seront refusées** : les fabrications d'octobre et de novembre, et les apps des essais.
  C'est accepté, et le refus le dit franchement (« format 1, attendu 2 »). Les fonctions de mise à niveau sont prévues
  à l'étape de l'évolution.
- **Le lecteur propose de mauvais noms** : trop longs, bizarres, ou identiques à une étape. Les contrôles attrapent les
  doublons et les gestes réservés. Arthur lit le tableau des noms proposés pour les 10 briefs d'apprentissage.
- **La nouvelle consigne déplace les autres réponses du lecteur** (le titre de l'app, les boutons d'étape). Parade :
  comparer avant et après sur les mêmes 10 briefs.
- **Le champ « Libellé » ajouté gêne le client.** Il ne vient qu'en dernier recours (ni champ texte, ni fiche
  désignée), et seulement s'il est validé au miroir.
- **Un `aria-label` qui ment.** Le juge vérifie que le texte affiché correspond au nom (convention « le nom correspond
  au texte »).
- **L'identifiant visible sur le bouton de connexion.** Ce sont des personnes d'essai, sans compte réel ni donnée
  réelle. La vraie connexion aura son propre contrat.
- **Le juge et le traducteur lisent la même description.** C'est la règle (« un juge tire ses attentes de la source
  validée »), pas une logique partagée. Le juge ne lit jamais la notice, qui est le fichier du constructeur. Et
  l'empreinte prouve que c'est bien la description validée.
- **La règle 10 ne se prouve pas complètement.** C'est écrit comme tel : une obligation de l'artisan, dont les parcours
  attrapent certaines manifestations.
- **Le coût** : 10 appels au lecteur des libellés, sur l'abonnement, à petit volume (permis : `USINE.md` §2.4).

### 6. Comment on prouve qu'elle marche (écrit AVANT le code)

**Les démonstrations**
1. Les trois exemples (la médiathèque, les types, l'union sportive) sont refabriqués. L'inspecteur, **en mode sans
   repli**, joue tous les parcours calculés depuis leur matrice : 100 % joués jusqu'au bout, 0 « introuvable »,
   0 « ambigu », sur 3 passes, 0 hésitation. Chaque résultat porte ses empreintes.
2. Le miroir des trois exemples et des 10 briefs d'apprentissage : **tout nom cherché par l'inspecteur figure dans le
   texte affiché du miroir** (100 %).
3. Le lecteur des libellés, sur les 10 briefs :
   - 100 % des fiches principales reçoivent un nom de création ;
   - aucun doublon, aucun geste réservé ;
   - les boutons d'étape couvrent les mêmes états qu'avant.

**Ce qu'elle doit refuser (les sabotages)**

| Sabotage | Qui doit l'attraper | Réponse attendue |
|---|---|---|
| 1. Une fiche principale sans `titre` | les contrôles de la description | refusée, avec le nom de la fiche |
| 2. Un `titre` qui désigne un nombre, une date ou un texte long | les contrôles de la description | refusée |
| 3. Un nom de création égal à un bouton d'étape de la même page (« Confirmer ») | les contrôles de la description | refusée |
| 4. Une description de format 1 | les contrôles de la description | refusée : « format 1, attendu 2 » |
| 5. Un nom retiré du bloc « À l'écran » du miroir | le contrôle de couverture | échec, qui nomme ce nom |
| 6. La description modifiée après sa validation | le juge | refuse de juger (empreinte) |
| 7. Les boutons de connexion sans identifiant | l'inspecteur | « introuvable » à la connexion |
| 8. Le lien du menu renommé | l'inspecteur | « introuvable » |
| 9. Le repère d'une page renommé | l'inspecteur | « introuvable » |
| 10. Le bouton de création renommé à l'écran (« Ajouter ») | l'inspecteur | « introuvable » |
| 11. Un bouton d'étape renommé | l'inspecteur | « introuvable » |
| 12. Le lien de la ligne placé sur un autre champ que le titre | l'inspecteur | « introuvable » à l'ouverture de la fiche |
| 13. Un mot ajouté au nom d'un champ | l'inspecteur | « introuvable » sur ce champ |
| 14. Un `aria-label` différent du texte affiché | l'inspecteur | « comportement faux » (le nom ne correspond pas au texte) |
| 15. Un filtre caché sur une liste. Les données de départ contiennent une fiche que ce filtre exclut à tort, sinon le sabotage ne prouve rien | l'inspecteur | « comportement faux » |

**Les témoins (ce qui doit rester vrai)**
- L'assembleur sur les trois exemples, avec les mêmes chiffres qu'à la montée de Next.js :
  - la médiathèque : 120/120 et 11 écrans ;
  - les types : 267/267 et 17 ;
  - l'union sportive : 212/212 et 28.
- Les sabotages d'écran : 8/8.
- Les règles : 35/41 avec effet.
- La preuve du contrôle des failles : 3/3.
- Un témoin proche pour le sabotage 14 : un `aria-label` qui **reprend** le texte affiché ne doit pas être signalé.

**Les seuils**, fixés maintenant :
- 100 % pour la première démonstration (ce sont nos propres écrans : aucune excuse) ;
- 100 % pour la couverture du miroir ;
- 100 % / 0 / 0 pour le lecteur ;
- les 15 sabotages, chacun attrapé par la bonne pièce ;
- tous les témoins identiques ;
- Arthur ne corrige pas plus d'un nom proposé sur cinq.

**Le critère d'arrêt**
- Un témoin change : on s'arrête et on comprend.
- Arthur corrige plus d'un nom sur cinq : la proposition du lecteur est mise de côté. La règle fixe reste, désormais
  visible au miroir, et on réessaiera plus tard.
- L'inspecteur a encore besoin d'un repli sur nos propres écrans : le contrat est incomplet. On le complète avant la
  chaîne complète.

### 7. Le périmètre

**Ce qui est touché :**
- la description (format 2) ;
- le lecteur des libellés et l'étape « assembler la description » ;
- le miroir et son contrôle de couverture ;
- la porte, dont le mode d'essai écrit lui aussi son empreinte ;
- le traducteur d'écrans ;
- le squelette : l'accueil, les repères, les listes, les formulaires ;
- les trois exemples ;
- la notice de l'artisan, nouvelle ;
- l'inspecteur de l'essai.

**Ce qui ne l'est pas :**
- les droits, la matrice, le calculateur ;
- les juges de l'usine (règles, sonde) ;
- les six premiers lecteurs ;
- la vraie connexion ;
- le titre des lignes d'une fiche : elles s'affichent dans la page de leur parent, ce sera plus tard ;
- les parcours des écrans riches, qui relèvent de la recette des capacités ;
- la vitesse de l'inspecteur ;
- l'IA cartographe.

**La taille** : une journée et demie à deux jours, une quinzaine de fichiers.

**Le risque** : élevé, parce que la description est l'entrée de toute la chaîne. D'où les témoins, et la relecture
après.

### 8. Questions pour le relecteur

Les six questions posées le 16 nov ont reçu leur réponse : voir la section Relecture.

## Relecture

- **Relecteurs** : Claude en ligne, et une IA d'un autre fournisseur (16 nov 2026). La synthèse est archivée dans
  `archives/echanges-2026-11/relecture-contrat-et-juge-ecrans-2026-11-16.md`.
- **Verdict** : **OK avec corrections**, unanime. L'architecture ne change pas.
- **Réponse point par point** (tous les points sont acceptés et intégrés plus haut) :

| Point de la relecture | Réponse | Ce qui change |
|---|---|---|
| 1. Trois règles de plus : le repère de page, le libellé des états, le lien de titre exact | accepté | règles 3, 6 et 7 |
| 2. L'unicité dans le contexte d'une action | accepté, avec une précision : la description ne peut le contrôler que pour les pages de l'usine ; pour l'artisan, c'est l'inspecteur (« ambigu ») | règle 9, morceau 1 |
| 3. Le titre n'est pas promis unique ; une ligne d'abord, puis son lien ; une seconde valeur visible ; pas de texte long | accepté | règle 6, morceau 10, choix écartés |
| 4. Le champ « Libellé » validé au miroir avant la fabrication, jamais ajouté en traduisant | accepté, écrit comme une règle | morceau 3 |
| 5. Étiquettes reliées par `for` et `id`, « (facultatif) » hors du nom | accepté | règle 8, morceau 7 |
| 6. Le nom lu par la machine correspond au texte affiché | accepté | convention, sabotage 14 et son témoin proche |
| 7. La couverture du miroir, prouvée par sabotage, contre le texte affiché | accepté | morceau 4, sabotage 5 |
| 8. L'empreinte de la description, comparée à la référence de la porte | accepté. **Elle existe déjà** : la porte la calcule sur le fichier tel quel, ce qui est plus strict qu'une forme recalculée. Le mode d'essai l'écrira aussi | morceau 5, sabotage 6 |
| 9. Les sabotages manquants (menu, étape, repère, filtre caché avec la bonne donnée) | accepté | sabotages 8, 9, 11 et 15 |
| 10. La règle 7 (devenue 10) est une obligation, pas une chose prouvée | accepté : j'en disais trop | règle 10, pièges |
| 11. Un numéro de format | accepté | morceau 1, sabotage 4 |
| 12. La normalisation des noms, selon la comparaison réelle de Playwright | accepté. La comparaison est exacte, majuscules comprises. Une seule mise en forme est écrite dans le contrat : la majuscule initiale d'un nom affiché seul. Le rejeu de l'essai a montré que le menu de notre squelette en dépend | convention « forme exacte » |
| 13. Les fenêtres de confirmation | accepté | morceau 10 |
| Criticité élevée | accepté : taille **critique**, relecture aussi après | en-tête, §7 |

- **Décision d'Arthur** : …

## Après : le compte rendu

*(à écrire après le développement ; il passera en relecture extérieure)*

## Petit lexique

- **Nom accessible** : ce qui est écrit sur un bouton, un lien ou un champ, tel qu'un lecteur d'écran le lit à voix
  haute. C'est aussi ce que cherche l'inspecteur.
- **Description** : le fichier qui dit tout de l'app (qui fait quoi, les fiches, leurs champs, leurs noms à l'écran),
  validée par le client au miroir.
- **Miroir** : la page qui montre au client, en français, ce que l'app fera, avant qu'on construise.
- **Porte** : le contrôle qui empêche de fabriquer une description que le client n'a pas validée, ou qui a changé
  depuis.
- **Empreinte** : un code calculé sur le contenu d'un fichier. Si un seul caractère change, l'empreinte change.
- **Notice** : le fichier que l'usine produit pour les écrans, à partir de la description. C'est le fichier du
  constructeur, jamais lu par un juge.
- **Fiche principale** : une fiche qui a sa propre page (ni un profil, ni une ligne d'une autre fiche).
- **Repli** : un second moyen de trouver un élément quand le premier échoue. Il est noté sur le parcours et compté à
  part ; le contrat sert à ne plus en avoir besoin.
