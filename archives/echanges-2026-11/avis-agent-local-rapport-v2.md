# Le rapport de décisions v2 face à l'usine réelle, et comment nous pensons la coder — 12 novembre 2026

> **Pour qui** : une IA extérieure au projet (Claude en ligne, ou l'autre IA qui a audité les versions 1 et 2 du rapport).
> Arthur veut un regard neuf sur ce texte.
> **Qui écrit** : l'agent de code qui travaille avec Arthur sur son dépôt (Claude Code). J'ai lu le code et les essais ;
> toi, tu ne les as pas vus. Ce texte te les décrit.
> **Ce que c'est** : (1) le rapport v2 comparé à ce qui existe vraiment dans l'usine et à notre vision passée, avec assez
> de détails pour que tu juges toi-même ; (2) nos premières pistes sur **la manière de coder** l'usine, à critiquer.
> **Statuts** : **Prouvé** = un fichier du dépôt ou un essai mesuré ; **Avis** = mon jugement ; **À vérifier** = un fait
> que je cite de mémoire, sans l'avoir relu à la source.
> **Biais** : je suis un produit d'Anthropic, et j'ai construit l'usine avec Arthur. J'ai donc intérêt à ce que l'existant
> paraisse précieux. Méfie-toi de ce biais.

## Ce que nous attendons de toi

1. **Confronter ma lecture** : où je surestime l'existant, et où le rapport v2 avait raison de l'ignorer.
2. **Critiquer les pistes techniques du §4** : leurs failles, les outils établis qui font déjà la même chose, les
   précédents.
3. **Répondre aux questions du §5.**

Règles : réponds en français ; cite tes sources avec leurs liens ; sépare ce qui est prouvé de ton avis ; reste au niveau
des idées, de l'architecture et des choix d'outils, sans écrire de code ; ne parle pas de business ; sois franc, même si
cela contredit une décision déjà prise.

---

## 0. Le rapport v2 en bref (pour que ce texte se lise seul)

Le rapport v2 (Arthur, 12 novembre) rassemble une recherche de Claude en ligne et deux audits par une autre IA.
Ses décisions :

1. L'usine est un **outil**, pas un produit ; le business est mis de côté.
2. Elle grandit par **capacités admises**. Une capacité est un comportement (« notifier par e-mail le bon destinataire
   après un événement autorisé »). Elle a un contrat, une documentation donnée à l'agent, des juges (universels, de
   capacité, contextuels), des sabotages, les versions avec lesquelles elle a été prouvée, un périmètre, et un état
   (candidate, admise, devenue incompatible).
3. La valeur de l'usine : le contrat validé par le client (le miroir), les juges, le catalogue et l'orchestrateur. Le
   constructeur (agent, modèle, assembleur) est interchangeable.
4. Une preuve dit ses limites. Un juge est qualifié par les sabotages qu'il attrape **et** par les apps conformes qu'il
   accepte.
5. Pas de boucle d'agent maison : **mini-swe-agent** officiel d'abord, **OpenCode** en comparaison, avec le même modèle.
6. L'assembleur reste, sans être obligatoire : il ne garde que ce qu'il fait mieux que l'agent, et cela se mesure.
7. L'apprentissage autonome est un objectif de recherche. D'abord, ajouter une capacité à la main (l'e-mail).
8. La pile est conservée (Next.js, ZenStack, PostgreSQL, Tailwind, shadcn/ui), avec **Better Auth** pour les comptes.
9. Chaque construction laisse des traces dès maintenant.
10. Six étapes d'expériences : 0, qualifier un noyau de juges ; 1, comparer les moteurs ; 2, prouver le juge générique ;
    3, la capacité e-mail ; 4, la comparaison avec NocoBase ; 5, des juges écrits par des agents.

Il décrit aussi une chaîne en cinq étapes (questionner, planifier, construire, juger, livrer), quatre sortes d'échec de
juge (fonctionnel, navigation, contrat ambigu, environnement), des parcours d'écrans en sept éléments (acteur, état
initial, objet, action, résultat visible, résultat métier, interdiction) et 12 juges pour l'e-mail.

---

## 1. L'usine aujourd'hui, pièce par pièce

### 1.1 Vue d'ensemble

**Prouvé.** L'usine actuelle (dossier `usine/`, octobre 2026) fait le niveau 1, la gestion simple. Sa chaîne :

```
brief ─► comprendre (7 lecteurs IA + un critique) ─► Description typée ─► contrôle strict
      ─► calculateur (matrice des droits + doctrines) ─► miroir (phrases + questions) ─► porte (validation du client)
      ─► traducteurs (règles d'accès ZenStack, notice d'écran, données) ─► squelette Next.js fixe
      ─► installation figée, compilation ─► juge des règles ─► tests d'écran ─► rapport
```

- Commandes : `python -m usine comprendre <brief>`, puis `python -m usine fabriquer <description>`, puis
  `python -m usine demarrer <run>`.
- Fabrication : **3 min 27 s, 0 $** par app. Compréhension : environ 1 minute, de 0,20 à 0,34 $ par brief avec gpt-5.5,
  ou 0 $ par une session Claude Code isolée sur le forfait.
- Taille : environ **6 800 lignes** (4 350 en Python, 2 400 en TypeScript), plus le calculateur hérité (675 lignes).
  L'usine 1 avait environ 23 000 lignes pour la seule orchestration.

### 1.2 La Description typée : le contrat

**Prouvé** (`usine/description.py`). C'est un modèle pydantic qui refuse tout champ inconnu. Il contient cinq parties :

| Partie | Contenu |
|---|---|
| `app` | nom court et titre |
| `acces` | le format du calculateur : les acteurs (et comment on le devient), les fiches (nature, propriétaire, liens vers d'autres fiches, parent), les circuits d'états (avec qui fait chaque flèche), les exceptions de droits citées par le brief |
| `champs` | les informations de chaque fiche, en **11 types fermés** (texte, texte long, nombre, montant, date, date et heure, oui/non, e-mail, téléphone, adresse web, choix à codes stables). Chaque champ a une **origine** : cité par le brief (avec sa citation mot pour mot), nécessaire (il faut au moins un nom), ou proposé par l'IA **et accepté** par le client |
| `ecran` | le verbe de création (« Emprunter ») et le libellé du bouton de chaque étape |
| `depart` | le contenu initial des catalogues |

Un contrôle de cohérence vérifie les identifiants, les noms réservés (`id`, `ownerId`, `userId`, `status`…), les choix
et les données de départ.

**Refus franc et codé.** Ce que l'usine ne sait pas encore construire est refusé avec un code stable `[bloc:<id>]` :
la publication, la saisie pour autrui, le lien depuis un profil, « celles qui le désignent », l'invitation. Chacun de ces
refus est né d'un défaut réel trouvé par un juge. Un exemple : traduit tel quel, « le RH crée les comptes des employés »
laissait le RH se créer une fiche d'employé à lui-même (registre n° 53).

**Ce n'est pas de la prose** : c'est la seule source de tout ce qui suit.

### 1.3 Comprendre : les lecteurs et le critique

**Prouvé** (`usine/comprendre/`).

- **7 lecteurs IA**, une question chacun : acteurs, fiches, circuits, droits explicites, périmètre et hors stock, champs,
  libellés.
- Ils n'ont **aucun outil** (c'est voulu : moins de liberté, moins de dérive). Ils lisent le brief et répondent en JSON.
- Chaque réponse passe un contrôle strict : forme, identifiants connus, **citations recopiées mot pour mot** du brief.
  L'erreur précise est renvoyée au lecteur, avec 3 essais au plus. Un plafond de dépense est écrit dans le code.
- Un **critique** IA relit l'ensemble (`critique.py`).
- Mesures (grilles écrites avant de lancer l'IA) : 9 matrices justes sur 10 vrais briefs avec gpt-5.5 (étude E5) ;
  15 champs attendus trouvés sur 16 ; aucun type faux.
- Le lecteur 5 range le hors stock en catégories (paiement, notification, intégration, document, planning, calculs).
  C'est l'embryon de l'étape « planifier : capacités admises ou hors stock » du rapport v2.

### 1.4 Le calculateur de la matrice et les doctrines

**Prouvé** (`factory-sprint0/agents/capability_matrix.py`). La **matrice des droits** dit, pour chaque rôle et chaque
fiche :

- ce qu'il voit : rien, les siennes, toutes, ou au travers d'une autre fiche ;
- ce qu'il crée, ce qu'il modifie et dans quel état, quelles flèches du circuit il fait passer, ce qu'il supprime.

Elle n'est **jamais écrite, ni par l'IA ni par nous** : elle est **calculée** depuis la Description. Le calcul applique
les **doctrines** (USINE.md §4), des règles que personne n'a besoin de demander :

| Doctrine | En une ligne |
|---|---|
| Natures | profil, catalogue, registre, collection, enfant : chacune a ses droits par défaut, au moindre privilège |
| Rôles listés | « connecté » veut dire la liste des rôles déclarés, jamais « toute personne connectée » |
| Supprimer | jamais accordé par défaut, seulement si le brief le dit |
| Responsable | le responsable voit en lecture tous les registres ; le client peut le refuser |
| Clôture | on ne désigne que ce qu'on a le droit de voir, à la création comme à la modification |
| Cohérence | deux fiches liées du même rôle propriétaire appartiennent à la même personne |
| Propriétaire immuable | le propriétaire d'une fiche ne change jamais |
| Une étape ne change que l'état | pendant une transition, aucun autre champ ne bouge |
| Prudence | un accès que le brief limite n'est pas élargi |
| Visiteur | un droit sans compte, seulement sur une fiche déclarée publique |
| Ne pas croire un refus | ZenStack peut répondre « refusé » alors que l'écriture a eu lieu : on juge sur l'état de la base |
| Intégrité | on ne supprime pas une fiche que d'autres désignent (jamais de cascade, sauf les lignes d'un parent) |

Le calculateur est vérifié par un banc de 14 matrices attendues : 14 sur 14 sont conformes.

**Pourquoi c'est important pour la comparaison** : en construisant librement, l'agent A0 a ouvert l'annuaire du personnel
(avec les téléphones) à toute personne connectée. C'est exactement ce que la doctrine « rôles listés » empêche par
construction.

### 1.5 Le miroir et la porte

**Prouvé** (`usine/miroir/`).

- `contenu.py` écrit des phrases « qui peut faire quoi », **produites par programme depuis la matrice** : elles ne
  peuvent pas mentir. Il pose aussi des questions oui/non là où une erreur coûte cher (« Le professionnel verra tous les
  dossiers, pas seulement ceux qui le concernent : d'accord ? »). Cette question s'est déclenchée sur une vraie erreur
  de l'IA (étude E5).
- `reponses.py` : chaque réponse du client est une **opération typée** sur la Description (changer un libellé, accepter
  un champ proposé, répondre à une question de droits), jamais une nouvelle lecture du brief.
- `porte.py` : rien ne se fabrique sans `validation.json`, qui dit qui a validé, quand, et avec quelles empreintes de la
  Description validée. Une réponse ajoutée après la validation rouvre la porte. Les deux mécanismes ont leur preuve
  (`preuve_porte.py`, `preuve_reponses.py`).
- **Manques** : la page où le client répond n'existe pas, le miroir n'a jamais servi à un vrai client, et trois dettes
  de lisibilité ont été relevées quand Arthur a joué le client.

### 1.6 Traduire et assembler

**Prouvé.**

- Les traducteurs (`usine/traduire/`) :
  - `schema.py` écrit **par programme** les règles d'accès ZenStack depuis la matrice (11 patrons et 2 règles
    systématiques) ;
  - `ecran.py` écrit la notice d'écran ;
  - `depart.py` écrit les données de démonstration.
- Le squelette fixe (`usine/modele-app/`) :
  - Next.js 16.4.0, ZenStack 3.9.7, PostgreSQL ;
  - des pièces génériques qui lisent la notice : liste, création, choix d'un lien, lignes d'un parent, profil, bloc de
    décision ;
  - **affordance honnête** : un bouton n'apparaît que si le serveur accepterait l'action ;
  - une connexion simulée par cookie (`{id, role}`), et des actions toujours en formulaires POST.
- `sur-mesure/` : un dossier prévu pour le code propre à une app. **Aucun code ne le branche, ni ne le garde quand on
  refabrique.**
- `assembler.py` enchaîne 10 étapes journalisées : lire et contrôler, calculer la matrice, traduire, assembler, installer
  en versions figées, générer et créer la base, poser les données, construire, juger les règles, juger les écrans.
- La reprise existe déjà : `--reprendre` ne repaie que les lectures refusées, `--rejouer` refabrique sans rien payer.
- Stabilité : 10 apps identiques sur deux passages (13 octobre).

### 1.7 Le catalogue des blocs

**Prouvé** (`usine/blocs/__init__.py`).

- Un **bloc** est un mot du vocabulaire de la Description : une nature, une action, une portée, un acteur, un lien, une
  garantie ou un type de champ.
- Ses **4 parties sont livrées ensemble** :
  - construire : le traducteur ;
  - écran : la pièce ;
  - juger : le module du juge ;
  - prouver : l'app où le bloc a été fabriqué, et où ses juges ont été prouvés par sabotage.

  Un bloc pas encore construit est remplacé par un **refus**, qui dit où l'usine le refuse.
- Il y a **38 blocs** : 32 construits, 6 refusés franchement.
- Un **contrôle d'architecture** lit le vocabulaire **dans le code** (les types pydantic). Il vérifie que chaque mot a
  son bloc, et que chaque partie déclarée existe vraiment (un fichier et un repère dans ce fichier). Un mot sans bloc
  empêche de fabriquer.
- `python -m usine carte` dessine une carte des blocs, avec les scores lus dans les rapports de preuve.
- **Écart avec une « capacité admise »** : un bloc n'a ni version, ni état « incompatible », ni documentation pour un
  agent, ni contrat de comportement séparé (son contrat, c'est le vocabulaire de la Description). Et ses parties sont
  des pièces écrites par nous, pas un travail confié à un agent.

### 1.8 Les juges et leurs preuves

| Juge | Ce qu'il juge | Comment | Preuve |
|---|---|---|---|
| Contrôles stricts | la forme de chaque réponse de l'IA | pydantic | étude E5 |
| Banc des matrices | le calculateur | 14 matrices attendues | 14 sur 14 |
| **Juge des règles** (`verification/noyau.mts` et `blocs/*.mts`, livré dans chaque app) | chaque case de la matrice, pour chaque rôle, plus l'**intrus** (connecté sans rôle) et le visiteur | il essaie vraiment chaque action par le client ZenStack et **juge sur l'état de la base**, pas sur la réponse | **par sabotage** : v1.0, 205 erreurs sur 214 (95,8 %) ; v1.2, 85 à 86 % des erreurs qui ont un effet. Les manquées forment une famille connue et bénigne (relire ou modifier ses propres fiches après avoir perdu son rôle). Il exige 6 conventions de noms (`cas.mts`) |
| **Tests d'écran** (`e2e/`, Playwright) | menu, création, modification, suppression, circuit et profil, rôle par rôle | attentes **tirées de la matrice** ; éléments repérés par leur rôle et par les libellés de la Description (`getByRole('button', { name: libelle })`) | **par sabotage** : sabotages tirés de la matrice, 8 sur 8, puis 6 sur 6 sur 3 apps ; **témoin** vert. Ils ne savent juger que notre squelette |
| Compilation et types | la cohérence du code | `next build` | — |
| **Sonde** (preuve de concept, `poc-agents\outils\sonde\sonde.mts`, 88 lignes) | ce que la base permet **réellement** à chaque personne, fiche par fiche : lire (combien sur combien), modifier une fiche visible ou cachée, créer, supprimer | elle ne lit que le schéma généré, ni nos noms ni notre squelette ; elle signale aussi « ÉCRIT MALGRÉ LE REFUS » | comparée seulement à une matrice connue (48 cases sur 48) ; **pas prouvée par sabotage** |

**Principes des juges, déjà écrits** (USINE.md §2 et §7) :

- **Un juge tire ses attentes de la source** (la matrice), jamais du fichier qu'il juge. Le jour où les tests d'écran
  lisaient les droits produits par l'usine, ils n'attrapaient qu'un sabotage sur quatre. En lisant la matrice, quatre
  sur quatre.
- **Deux façons de se tromper** : la fausse alarme (visible) et l'aveuglement (invisible, donc dangereux). Le sabotage
  traite l'aveuglement ; le **témoin** (l'app intacte, que le juge doit dire conforme) traite la fausse alarme.
- **Trois filets** : une erreur de l'IA est attrapée par les contrôles et le miroir ; une erreur de l'usine, par les
  juges ; une erreur d'un juge, par les sabotages et les apps nouvelles.

### 1.9 La méthode : corpus, examen caché, registre

**Prouvé.**

- **Corpus** : 33 vrais briefs pris sur Codeur.com. La règle de choix et les réponses attendues ont été écrites **avant**
  tout lancement. `python -m usine.mesures.corpus` mesure le périmètre, les blocs manquants, le hors stock et le coût.
- **Lot d'examen caché** : 10 briefs dont on n'a gardé que les liens (7 octobre), jamais ouverts, et écartés du corpus
  par un programme qui compare les numéros. Il est prévu pour l'examen final du niveau 1.
- **Registre de 59 corrections** (USINE.md §7). Chaque correction est classée (défaut de l'usine, défaut de l'IA, ou mon
  erreur), avec qui l'a trouvée et si elle est générale. Règle : une correction qui cite un métier ou un brief est
  refusée ; aucun juge n'est assoupli ; chaque défaut corrigé est verrouillé par un juge. La **convergence** (défauts
  nouveaux par app nouvelle) est suivie.
- **Avant, pendant, après** : l'accord d'Arthur avant chaque étape ; les défauts corrigés et inscrits pendant ; trois
  indicateurs après, avec un critère d'arrêt fixé d'avance.

### 1.10 La preuve de concept et ses outils (20 au 22 octobre)

**Prouvé** (`C:\Users\BAMBARA Arthur\poc-agents\` et `poc-a0\`).

- **Le contrat technique d'A0** (`poc-a0\contrat-technique.md`), donné à l'agent avec le brief seul :
  - la pile imposée en versions exactes ;
  - les règles d'accès obligatoirement dans le schéma ZenStack ;
  - une session `{ id, role }`, et des personnes d'essai `<rôle>_1` et `<rôle>_2` ;
  - le périmètre convenu avec le client, et les pièges du poste.

  C'est déjà une « documentation injectée » et une convention qui rend l'app jugeable. Next.js 16 ajoute lui-même un
  `AGENTS.md` qui renvoie à sa documentation locale.
- **Outils** :
  - `juger.ps1` : il vérifie par empreintes que le juge est intact, et part d'une base neuve à chaque passage ;
  - `sonder.ps1` et `ecrans_b.ps1` ;
  - `audit_session.py` : durée, jetons, appels d'outils, et fichiers lus hors du dossier ;
  - des scripts de préparation.
- **Résultats** (Sonnet 5.5 dans Claude Code, sessions interactives) :

| Essai | Résultat |
|---|---|
| A1 (avec notre Description) | 41 min, environ 8 $, 253 cas sur 258 |
| A2 (avec en plus le rapport du juge) | 258 sur 258, en une correction |
| B (4 écrans hors stock sur l'app de l'usine) | 20 min, cœur intact |
| Évolution | 52 lignes migrées sur 52 par une session neuve |
| A0 (brief seul) | 1 h 02, environ 7,50 $, app plus riche que celle de l'usine, une faille (l'annuaire ouvert à tout connecté) |

### 1.11 Ce qui manque

- Un juge d'écrans pour une app écrite par un agent.
- La preuve par sabotage de la sonde.
- La construction sans humain : le mode non interactif a été refusé par l'outil de sécurité de ma session.
- La variance, jamais mesurée.
- Un code qui garde `sur-mesure/` quand on refabrique.
- Les migrations : chaque fabrication part d'une base neuve.
- Les vrais comptes, l'hébergement, les sauvegardes, la sécurité au-delà des droits, l'isolement de l'agent.

---

## 2. Notre vision passée, ce qu'elle disait

### 2.1 Trois usines en huit mois

- **Usine 1 (mars à septembre)** : une IA « architecte », une vingtaine de générateurs fixes et un exécuteur IA fait
  maison. Le 28 septembre, deux briefs inédits ont donné 0 compilation sur 2, « alors que l'IA avait correctement
  compris ». Les causes relevées dans le code :
  - un mauvais ordre (écrans planifiés avant les acteurs) et une mauvaise unité (« fiche × type de page ») ;
  - des concepts recopiés à plusieurs endroits ;
  - des modèles transportés en texte et relus par des expressions régulières ;
  - des garde-fous qui traitaient le symptôme ;
  - des juges faibles : la compilation était le seul juge fiable.
- **Usine 2 (octobre)** : « l'IA comprend, un programme assemble ». C'est le §1.
- **Après la preuve de concept (22 octobre au 11 novembre)** : une usine hybride avec l'inspecteur au centre (§2.3).

### 2.2 Les principes acquis (USINE.md §2)

1. **Loi du contenant** : une intention sans structure typée pour la porter s'évapore, même si l'IA l'a comprise.
2. **Intelligence aux bords, programme au cœur.**
3. **Une seule source par concept** : la matrice est calculée une fois ; règles, écrans, menus, tests et miroir en
   dérivent.
4. **L'app est faite d'acteurs qui déroulent un processus sur des fiches** : l'unité, c'est l'acteur, pas l'écran.
5. **Affordance honnête** : un bouton n'apparaît que si le serveur accepterait l'action.
6. **Clôture contre désir** : l'usine complète ce qui est nécessaire ; ce qui n'est pas demandé remonte au client.
7. **La description est le produit** : on corrige la description ou le traducteur, jamais le code livré.
8. **Des juges qui ne mentent pas** : un juge n'est cru qu'une fois prouvé, et il lit la source.
9. **Moindre privilège** : une exception oubliée donne un manque visible, jamais une fuite invisible.
10. **Des blocs complets.**
11. **Corriger une classe, jamais un cas.**
12. **Avant, pendant, après.**

S'y ajoutent **7 règles de circulation** :

- un fait n'a qu'un auteur ;
- entre machines, on échange des données, jamais du texte ;
- un contrôle strict à chaque frontière, avec l'erreur renvoyée, jamais devinée ;
- les fiches sont figées ;
- l'IA reçoit le minimum ;
- les ordres viennent du plan, pas de l'IA ;
- chaque fichier sait de quelle case il vient.

### 2.3 Les positions d'octobre et novembre (USINE.md §0.10, marquées hypothèses)

- **La règle des trois zones (19 octobre).**
  - Le **cœur** (données, droits, porte, juges, argent) est écrit une fois, relu et prouvé, et jamais généré pour une
    app.
  - Les **déclarations** (formules, règles, indicateurs, raccordements) sont contrôlées et compilées par l'usine.
  - Les **bords** (design, page sur mesure, PDF, intégration) peuvent être écrits par l'IA, dans un emplacement isolé,
    avec un contrat typé et des tests, et n'accèdent aux données que par le client ZenStack.
- **Le vrai argument de l'assemblage (19 octobre).** Ce n'est pas « l'IA ne sait pas coder » (en 2026, elle sait), mais :
  - la preuve se fait une fois ;
  - une même description donne la même app ;
  - une correction de classe vaut pour toutes les apps ;
  - et surtout, **l'entretien d'une flotte** : une faille corrigée ou une montée de version, c'est un changement du
    squelette, pas N bases de code qui divergent.
- **Le contrat de l'app livrée (19 octobre)** : une liste de qualités, chacune avec son juge. Les droits sont faits ;
  la connexion, la sécurité au-delà des droits, le déploiement, les mises à jour sans perte, les sauvegardes, le RGPD et
  l'accessibilité restent à faire. Chaque qualité se construit une fois dans le squelette, et toutes les apps en
  héritent.
- **Les petits langages (§0.4).** Les formules, règles et indicateurs s'écrivent dans un petit langage limité, que
  l'usine traduit en code et teste par des exemples. L'usine 1 l'avait réussi pour les indicateurs.
- **L'agent opérateur (19 et 20 octobre).** Un agent conduit l'usine par ses commandes prouvées, exposées en outils MCP.
  Il n'écrit jamais de fichier directement. Conduire et construire sont deux modes séparés, pour que le même agent ne
  soit pas tenté de « réparer » un juge.
- **Le cycle de vie (20 octobre)**, à décider avant la première app livrée :
  - les noms internes sont gelés, et renommer ne change que le libellé ;
  - la description est versionnée ;
  - une évolution se fait par des opérations typées, chacune portant sa migration de données ;
  - on répète sur une copie de la base, avec sauvegarde et retour arrière ;
  - la flotte se met à jour en refabriquant depuis les descriptions ;
  - les demandes du client sont triées : défaut, évolution, ou question d'usage.
- **L'hybride B (21 octobre et 11 novembre).** Le cœur est assemblé quand il entre dans le vocabulaire ; l'agent fait
  la périphérie ; un inspecteur indépendant juge ce que l'agent écrit. Ce que l'assembleur garantit et que l'agent ne
  garantit pas (transmis le 11 novembre dans `reponse-usine3.md`) :

| Garantie | Assembleur | Agent |
|---|---|---|
| Droits conformes à la matrice et aux doctrines | par construction (31 apps sur 31) | après coup, par le juge (A1 : 253 sur 258 ; faille latente d'A0) |
| Conventions de noms, donc tous les juges s'appliquent | toujours | seulement si l'agent les respecte |
| Écrans cohérents avec les droits | prouvé (36 tests d'écran) | non vérifié |
| Même description, même app | prouvé | non mesuré |
| Une correction vaut pour toute la flotte | par refabrication | une session d'agent par app |
| Coût | 0 $, 3 min 27 s | environ 8 $, 41 à 62 min |
| Ce que l'agent fait mieux | — | écrans plus riches, hors stock, migrations, meilleure modélisation du métier |

- **La politique de dépendances (7 octobre).**
  - Notre valeur ne vit jamais chez un fournisseur.
  - Une bibliothèque plutôt qu'un service, sous licence libre.
  - Peu de dépendances, chacune avec une raison écrite et une porte de sortie.
  - Un seul endroit du code touche chaque outil.
  - Les versions sont figées, avec tests à chaque montée.
  - On achète le difficile et le générique, on construit notre cœur.

  Better Auth figurait déjà comme porte de sortie de Clerk (USINE.md §5).

---

## 3. Le rapport v2 face à l'existant

### 3.1 Ce qui existait déjà

| Idée du rapport v2 | Ce qui existe déjà | Ce que le rapport ajoute vraiment |
|---|---|---|
| Capacité admise | Le bloc et ses 4 parties ; le contrôle d'architecture ; le refus franc (§1.7) | des versions, un état « incompatible », la documentation pour l'agent, un contrat de comportement |
| Une partie non admise ne se livre pas | le refus codé dans la Description ; le hors stock dit dans le miroir | la prévisualisation expérimentale |
| Juges testés contre les faux positifs | le témoin (§1.8) | un corpus d'apps conformes **d'autres origines** |
| Corpus fermé (5 sur 33) | le lot d'examen caché (§1.9) | rien : les 33 ont déjà servi aux 59 corrections, aucun n'est « fermé » |
| Celui qui construit ne touche pas ses juges | le juge intact vérifié par empreintes ; aucun juge assoupli ; deux modes séparés | « ni choisir les cas de validation finale, ni effacer ses échecs » |
| La bonne réponse vient du contrat | le juge qui lit la source (§1.8) | les oracles par propriétés (tests métamorphiques) |
| Parcours ciblés par rôle et libellé | les tests d'écran le font déjà, avec les libellés de la Description | le format en 7 éléments, la validation par le client |
| Documentation dans `AGENTS.md` | le contrat technique d'A0 ; l'`AGENTS.md` de Next.js | l'injection par capacité |
| Personnes d'essai par rôle (critère de Better Auth) | `<rôle>_1`, `<rôle>_2` et la session `{id, role}` imposés à A0 | les vrais comptes |
| Traces | `journal.jsonl` et `99-rapport.json` à chaque fabrication ; `audit_session.py` ; un tableau de bord | une table PostgreSQL ; le coût **par app admise** |
| Deux corrections au plus | l'hybride du 11 novembre | l'arrêt anticipé si l'erreur se répète |
| Un analyste qui questionne | les lecteurs, le critique, les questions du miroir | un agent qui pose des questions ouvertes |

**Avis.** C'est normal : le rapport a été écrit à partir de nos résumés, sans le code. Deux conséquences :

- on part de plus loin qu'il ne le croit ;
- il faut éviter de reconstruire sous un nouveau nom ce qui existe. Le catalogue des capacités doit **faire évoluer**
  `usine/blocs/`, pas s'ajouter à côté. Sinon on aurait deux catalogues, donc une décision à deux endroits, classe de
  défaut déjà rencontrée (registre n° 35).

### 3.2 Ce qui est vraiment nouveau, et meilleur

1. **Le constructeur n'est plus forcément l'assembleur.** Un bloc, c'est une pièce écrite par nous. Une capacité, c'est
   un comportement plus une documentation pour un agent. Le catalogue peut grandir sans qu'on écrive chaque pièce à la
   main. C'est le vrai saut, et c'est aussi un changement de doctrine (§3.3, point 1).
2. **Les versions et l'état « devenue incompatible ».** Nos dépendances sont figées, sans aucune manière de monter de
   version.
3. **Les faux positifs testés sur des apps conformes variées.** Notre témoin est la même app intacte ; les apps d'agent
   ne se ressemblent jamais.
4. **Quatre sortes d'échec.** Aujourd'hui, un test d'écran qui échoue est toujours un défaut. C'est juste sur notre
   squelette, mais pas sur une interface qu'on n'a pas écrite.
5. **Des parcours d'écrans validés dans le miroir.** C'est la réponse à notre manque n° 1, et elle respecte « le juge lit
   la source ».
6. **Un niveau « couvert » par un catalogue fini.** Ça corrige notre critère « toutes les apps du niveau », qui ne peut
   jamais se vérifier. Il faut garder aussi le critère par corpus (seuil de compréhension, majorité d'apps sans défaut,
   convergence).
7. **Les oracles par propriétés** pour les calculs. Ils complètent les petits langages.
8. **« Apprendre à vérifier avant d'apprendre à construire ».** C'est plus modeste que nos cinq étapes d'apprentissage,
   mais cohérent avec la preuve : l'agent sait construire, il rate des droits.
9. **Des outils tranchés** : un moteur d'agent ouvert, Better Auth, un bac à sable Docker (nous n'avions aucun
   isolement), Mailpit. Mon biais est à dire : faire de Claude Code une simple référence me paraît juste.
10. **Tout ce qui touche l'e-mail** : rien n'existe chez nous.

### 3.3 Ce que le rapport a perdu en route

1. **Un changement de doctrine passé en silence.** Avec « ce qui fabrique est flexible » et un assembleur facultatif,
   l'agent peut écrire les droits, et seuls les juges les contrôlent après coup. C'est l'inverse de la règle des trois
   zones et du principe « la sécurité est fixée par programme ». Ce n'est pas forcément faux, mais ça repose sur un seul
   brief (A0 et A2). Ça doit être une décision prise consciemment.
2. **L'entretien de la flotte et la reproductibilité.** Le rapport veut mesurer « ce que l'assembleur fait mieux », mais
   sur une seule construction, l'agent gagnera toujours. Il faut mesurer aussi la variance, et une montée de version
   sur plusieurs apps.
3. **Le cycle de vie** (noms gelés, versions, opérations typées, migration par opération) se réduit à une ligne. Ce sont
   pourtant les décisions qu'on ne rattrape plus après la première app livrée.
4. **La cohabitation de l'assembleur et de l'agent.** L'assembleur pose, l'agent complète : à chaque évolution, la
   refabrication effacerait le travail de l'agent. C'est la question d'architecture n° 1 d'une usine hybride, et le
   rapport ne la pose pas (piste au §4, point 5).
5. **La matrice calculée par les doctrines** n'apparaît pas dans « ce qui fait la valeur ». Il faut la ranger du côté
   fixe et prouvé : si l'agent écrit lui-même la matrice, les doctrines sautent.
6. **L'agent opérateur par MCP** est remplacé par un orchestrateur en Python. **Avis** : c'est mieux, parce que c'est
   plus prévisible, mais c'est un abandon à acter.

Les points 1, 2 et 5 avaient été transmis le 11 novembre (`reponse-usine3.md`) et ne figurent pas dans le rapport v2.

### 3.4 Les trous du plan d'expériences

1. **L'étape 1 ne peut pas être mesurée par les juges de l'étape 0.** L'étape 0 qualifie le juge des règles, qui exige
   6 conventions de noms. A0, construit à partir du brief seul, n'en avait aucune : c'est la sonde qui l'a jugé. Or la
   sonde n'est qualifiée qu'à l'étape 2. **Avis** : faire entrer la sonde dans le noyau de l'étape 0, puisque c'est le
   seul juge qui ne dépend pas de nos noms.
2. **L'étape 0 est une construction, pas seulement une qualification.** Le moteur de parcours n'existe pas, et le rapport
   ne dit pas comment il fonctionne : un moteur fixe, ou un navigateur IA (§4, point 7).
3. **La règle de l'étape 0 risque de faire échouer notre propre juge.** « Tous les sabotages critiques attrapés » : le
   juge des règles en attrape 85 %. Les manquées (relire ou modifier ses propres fiches après avoir perdu son rôle)
   sont-elles critiques ? Il faut le décider avant de lancer l'étape, sinon on assouplit après coup.
4. **Le corpus fermé** doit être le lot d'examen caché, pas 5 des 33.
5. **Le coût** : environ 65 $ par l'API pour l'étape 1, et nous n'avons plus de crédit API (l'IA passe aujourd'hui par
   le forfait Claude).

---

## 4. Comment nous pensons coder l'usine (pistes, à critiquer)

> Tout ce chapitre est **Avis** : des pistes, pas des décisions, et aucune n'est encore mesurée. Le but est que tu les
> critiques avant que nous écrivions la moindre ligne.

### 4.0 Le principe : l'usine se construit comme elle construit

On impose aux apps un contrat typé, une source unique, des juges prouvés et des états calculés. L'usine elle-même doit
suivre les mêmes règles. Chaque étape lit des fichiers figés et en écrit d'autres. Chaque pièce de l'usine a sa propre
preuve, comme aujourd'hui `preuve_regles.mts`, `preuve_ecrans.py` et `preuve_porte.py`. Ce qui décide est du programme ;
ce qui varie (l'agent, le modèle) est enfermé et jugé.

### 4.1 Les pistes

**1. L'usine comme un système de construction à empreintes.**

- *Idée* : chaque étape est une fonction de ses entrées. Ses entrées sont figées et ont une empreinte ; une étape ne se
  rejoue que si ses entrées changent.
- *Gains* : la reprise après une interruption est gratuite, comme la reproductibilité. On ne repaie jamais une étape
  déjà faite. La chaîne des empreintes devient elle-même la trace.
- *Déjà là* : `journal.etape`, `--reprendre`, `--rejouer`, les empreintes de `validation.json` et de `juger.ps1`.
- *Outils* : le faire nous-mêmes (une empreinte est un calcul exact, pas une heuristique), ou une bibliothèque de flux
  durables sur PostgreSQL (DBOS Transact, *à évaluer*). Pas Temporal : trop lourd pour un orchestrateur mince, et déjà
  quitté avec l'usine 1.
- *Risque* : les étapes IA ne donnent pas deux fois la même réponse. On fige donc leur sortie à la première exécution,
  comme on le fait déjà pour les lectures payées.

**2. L'état d'une capacité se calcule, il ne se déclare pas.**

- *Idée* : « admise » est le résultat d'un calcul sur le dossier de preuve et les versions en vigueur. Si une version
  change, la capacité redevient « à requalifier » d'elle-même, et les apps qui l'utilisent sont listées.
- *Déjà là* : `carte.py` lit les scores dans les rapports de preuve ; le contrôle d'architecture vérifie que chaque partie
  existe.
- *Risque* : requalifier coûte des constructions d'agent. On commencerait par rejouer les juges sur le banc (point 9),
  sans rien reconstruire.

**3. Une image figée par version de la pile.**

- *Idée* : une image Docker contient Node, les dépendances installées en versions exactes, et Playwright avec ses
  navigateurs. Toutes les constructions et tous les juges partent de la même image, et son empreinte (le *digest*) est
  la version contre laquelle une capacité est prouvée.
- *Gains* : une installation en 0 s au lieu de 87 s ; une seule copie des 620 Mo de dépendances au lieu d'une par app
  (le disque s'était rempli en octobre) ; une preuve rattachée à quelque chose d'exact.
- *Risque* : sur ce poste, Docker Desktop s'arrête à chaque redémarrage.

**4. Trois conteneurs, trois rôles, et git comme seul passage.**

- *Idée* :
  - le constructeur travaille dans son conteneur, sur un dépôt git, sans les juges, et rend un commit ;
  - l'orchestrateur applique ce commit dans un conteneur neuf, issu de la même image ;
  - les juges y tournent, apportés par une image séparée ;
  - l'agent ne reçoit que le rapport (verdicts, parcours ratés), jamais le code des juges.
- *Gains* : ce qui est jugé est exactement ce qui sera livré, sans processus ni état laissé par l'agent. La règle
  « celui qui construit ne touche pas ses juges » devient physique.
- *Déjà là* : `juger.ps1` (empreintes, base neuve).
- *Outils* : Docker et git. mini-swe-agent sait travailler dans un conteneur (*à vérifier en détail*).
- *Risque* : le réseau du conteneur (npm, API du modèle) doit passer par une liste blanche.

**5. Deux branches git pour faire vivre ensemble l'assembleur et l'agent.**

- *Idée* :
  - la branche `coeur` ne contient que ce que l'assembleur produit ;
  - la branche `app` contient `coeur` plus les commits de l'agent ;
  - une refabrication est un nouveau commit sur `coeur`, suivi d'une fusion à trois voies dans `app` ;
  - sans conflit, les juges tranchent ; en cas de conflit ou de compilation cassée, l'agent reçoit une tâche
    d'adaptation, avec le diff du cœur.
- *Garde-fous* : un **manifeste de propriété** refuse mécaniquement tout commit de l'agent qui touche un fichier du
  cœur ; l'assembleur n'écrit jamais dans `sur-mesure/`. Le code de l'agent ne touche le cœur que par des **points
  d'extension typés** (pages en plus, panneaux dans une fiche, entrées de menu) et par le client ZenStack.
- *Déjà là* : lors de l'évolution de B, le typage a signalé le seul endroit cassé du sur-mesure.
- *Précédents* (*à vérifier*) : JHipster régénère son code dans une branche dédiée, puis la fusionne ; le patron
  « Generation Gap » sépare le code généré du code écrit à la main.
- *Ce que ça résout* : le §3.3, point 4.

**6. Les parcours d'écrans, surtout calculés.**

- *Idée* : la plupart des parcours d'une app de gestion se déduisent de la matrice :
  - pour chaque flèche d'un circuit et chaque rôle autorisé, « R fait passer F de l'état A à l'état B » ;
  - pour chaque rôle non autorisé, l'interdiction.

  C'est ce que font déjà nos tests d'écran. Seuls les parcours hors matrice (écrans sur mesure, capacités nouvelles)
  sont écrits par l'analyste et validés dans le miroir. Le format en 7 éléments devient un type de la Description.
- *Gains* : le client a moins à valider, et il n'y a toujours qu'une source.
- *À mesurer sur notre corpus* : quelle part des parcours est calculable.

**7. Un contrat d'accessibilité : la convention qui rend l'app jugeable la rend aussi accessible.**

- *Idée* : on impose à l'agent que chaque action d'un parcours soit un élément accessible (bouton, lien, champ) dont le
  nom est le libellé de la Description, et que chaque fiche affichée porte son nom accessible. Le moteur de parcours
  (Playwright, sans IA) cible les éléments par rôle et par nom ; axe-core vérifie l'accessibilité.
- *Conséquences* :
  - aucune IA n'est nécessaire pour naviguer, donc aucune IA ne sert d'oracle ;
  - les quatre sortes d'échec deviennent en partie mécaniques :
    - un élément introuvable veut dire que la convention n'est pas respectée : c'est un défaut réel, mais d'une autre
      famille que la logique métier ;
    - deux éléments trouvés déclenchent l'erreur du mode strict de Playwright : c'est une ambiguïté ;
    - un délai réseau ou une panne de navigateur relève de l'environnement ;
    - une action faite avec une base fausse est un échec fonctionnel ;
  - le **résultat métier** se vérifie dans la base (par la sonde ou une requête), pas à l'écran.
- *Divergence avec le v2* : avec un moteur sans IA, « échec de navigation » perd en partie son sens. Il devient
  « convention non respectée ».
- *Risque* : imposer les libellés appauvrirait-il les écrans ? Probablement peu, puisque les libellés sont validés par
  le client et qu'A0 était riche sans gabarit.

**8. Des sabotages placés à la frontière observable.** Trois familles :

- **Droits** : modifier les règles du schéma ZenStack en passant par son arbre syntaxique (le parseur officiel du
  langage, *à vérifier*), jamais par des expressions régulières. Cela marche quel que soit le constructeur, puisque le
  contrat technique impose les règles dans le schéma.
- **Pannes** : injecter des pannes entre l'app et ses services. Par exemple :
  - un proxy de pannes comme Toxiproxy ;
  - l'arrêt du processus entre l'approbation et l'envoi ;
  - deux requêtes simultanées ;
  - les erreurs SMTP que Mailpit sait simuler (*à vérifier*).
- **Logique et écrans** : un agent saboteur isolé, à qui on demande un défaut d'une famille précise. Un sabotage n'est
  retenu que si une sonde ciblée montre que le comportement a vraiment changé. Sinon il est classé « sans effet », comme
  les mutants équivalents du test par mutation.

*Déjà là* : les sabotages tirés de la matrice (écrans) et 49 mutants classés (règles). *Problème ouvert* : prouver qu'un
sabotage est valide sans tourner en rond.

**9. Le banc de qualification des juges est un tableau calculé.**

- *Idée* : les lignes sont des apps conformes d'origines variées (assemblées, ou construites par un agent puis revues).
  Les colonnes sont les sabotages. Chaque case donne le verdict attendu : accepter ou refuser. Le banc se rejoue à
  chaque version d'un juge, et le dossier de preuve en sort.
- *Déjà là* : `preuve_regles.mts`, `preuve_ecrans.py`, le témoin.
- *Manque* : des apps conformes construites par des agents. Aujourd'hui, il n'y a qu'A2.

**10. La variance comme détecteur de trous du contrat.**

- *Idée* : deux constructions du même contrat passent toutes deux les juges, mais se comportent différemment sur une
  même sonde (tableau des droits, parcours). Cela montre un endroit que le contrat ne fixe pas : une question à ajouter
  au miroir. C'est le principe du test différentiel, employé pour les compilateurs (Csmith, *à vérifier*).
- *Déjà là* : la sonde donne un tableau comparable d'une app à l'autre. A0 a vu un lien entre devis et événement que
  notre lecture avait raté.
- *Coût* : deux constructions. Hypothèse.

**11. L'`AGENTS.md` est généré, jamais écrit à la main pour une app.**

- *Idée* : il est assemblé à partir du contrat (Description, parcours), des fragments de chaque capacité, des
  conventions (noms, accessibilité, points d'extension) et des doctrines en mots simples.
- *Limite assumée* : les doctrines existent alors deux fois, dans le code du calculateur et dans le texte pour l'agent.
  Le texte n'est qu'une aide ; ce sont les juges qui font foi.
- *Déjà là* : le contrat technique et les consignes d'A0.

**12. Des traces sans effort.**

- *Idée* : une construction donne une ligne dans PostgreSQL et un dossier.
  - La ligne contient les empreintes des entrées, l'image, le modèle, le moteur, le coût **réel** lu dans les réponses
    de l'API, et les verdicts.
  - Le dossier contient la trajectoire de l'agent, le diff et les rapports.
- *Déjà là* : `journal.jsonl`, `99-rapport.json`, `audit_session.py`, le tableau de bord.

### 4.2 Ce que nous ne ferions pas

- Une boucle d'agent maison, ou une compression de contexte maison avant que l'expérience en montre le besoin.
- Un agent qui navigue pour juger.
- Des expressions régulières sur du code.
- Un deuxième catalogue à côté des blocs.
- Un moteur de flux lourd.
- Un juge que le constructeur peut lire ou modifier.

### 4.3 Notre façon de travailler

- **Reprendre avant de réécrire** :

| Existant | Devient |
|---|---|
| `usine/blocs/` (catalogue, contrôle, carte) | le catalogue des capacités |
| `e2e/blocs/` (tests d'écran par rôle et libellé) | le moteur de parcours |
| `sonde.mts` | le juge générique, versé dans `usine/` puis prouvé |
| `juger.ps1` | l'étape « juger » de l'orchestrateur |
| `journal.py`, `--reprendre`, `--rejouer` | l'orchestrateur à empreintes |
| `contrat-technique.md` d'A0 | l'`AGENTS.md` généré |
| `audit_session.py` | les traces |
| les outils de photo avant/après d'octobre | le juge « aucune fiche perdue » des migrations |

- **Une tranche verticale à la fois** : une capacité de bout en bout (contrat, phrase du miroir, juges, sabotages,
  documentation, construction, preuve) plutôt qu'une couche après l'autre. C'est ce qui a marché pour le niveau 1.
- **Vérifier avant de construire, pour nous aussi** : la preuve d'une pièce de l'usine s'écrit avec elle, ou avant.
- **Deux langages, une frontière de données.** Python pour l'orchestrateur, la compréhension et le catalogue.
  TypeScript pour les juges qui vivent près de l'app, parce qu'ils utilisent le client ZenStack et Playwright. Entre les
  deux, uniquement des fichiers JSON à forme fixe.
- **Qui écrit le code de l'usine** : Arthur et moi. À l'exécution, l'usine ne dépend d'aucun agent en ligne de commande
  précis. La règle des deux modes vaut pour nous aussi : la même étape ne modifie pas à la fois un juge et ce qu'il juge.
- **Une fiche courte avant tout code** (but, démonstration, ce qui est touché, taille, risque), validée par Arthur, et
  chaque correction au registre.

---

## 5. Les questions que nous te posons

1. **La comparaison** : ai-je mal décrit l'existant ? Le rapport v2 a-t-il ignoré certaines choses à raison ? Après avoir
   lu les §1 et §2, changerais-tu une décision du v2 ?
2. **La règle des trois zones** : faut-il laisser l'agent écrire les règles d'accès (les juges contrôlant après coup), ou
   les garder écrites par programme depuis la matrice, l'agent ne faisant que le reste ? Que dit l'état de l'art
   (*policy as code*, développement guidé par les spécifications) ?
3. **La cohabitation par deux branches git** (§4, point 5) : quels précédents et quels pièges ? JHipster, Generation Gap,
   d'autres ?
4. **Le contrat d'accessibilité** (§4, point 7) : existe-t-il des précédents d'une convention d'accessibilité utilisée
   pour rendre une interface testable automatiquement ? Quelles limites ?
5. **La validité des sabotages** (§4, point 8) : comment l'état de l'art prouve-t-il qu'une mutation ou une panne injectée
   est « valide », sans raisonnement circulaire (le problème des mutants équivalents) ?
6. **L'orchestrateur** (§4, point 1) : pour un orchestrateur mince et durable, en Python et sur PostgreSQL, faut-il le
   faire nous-mêmes, prendre DBOS, procrastinate, ou autre chose ? Nos critères : peu de dépendances, reprise, traces.
7. **Le trou de l'étape 1** (§3.4, point 1) : mettre la sonde dans le noyau de l'étape 0, ou donner les conventions de
   noms à l'agent dès l'étape 1 ?
8. **Le test différentiel** (§4, point 10) : existe-t-il des travaux qui comparent deux générations d'un même programme
   pour trouver les trous d'une spécification ?

---

## 6. Fichiers cités

**Dans le dépôt `StartupNexus`** :
- `USINE.md` : document de référence (§0.10 pour la vision d'octobre et novembre, §2 principes, §4 doctrines, §5 outils,
  §7 juges et registre) ;
- `usine/description.py`, `usine/comprendre/`, `usine/miroir/`, `usine/traduire/`, `usine/blocs/`, `usine/assembler.py` ;
- `usine/modele-app/verification/` (juge des règles) et `usine/modele-app/e2e/` (tests d'écran) ;
- `usine/preuve_regles.mts`, `usine/preuve_ecrans.py` ;
- `factory-sprint0/agents/capability_matrix.py` (calculateur) ;
- `reponse-agent-local.md` (inventaire du 10 novembre), `reponse-usine3.md` (avis du 11 novembre),
  `etalage-usine.md` (intentions et niveaux), `usine-a-apps-rapport-decisions-v2.md` (le rapport commenté ici).

**Hors du dépôt** : `C:\Users\BAMBARA Arthur\poc-agents\` (essais A1, A2, B, évolutions ; outils dans `outils\`, sonde
dans `outils\sonde\`) et `C:\Users\BAMBARA Arthur\poc-a0\` (essai A0, `contrat-technique.md`).
