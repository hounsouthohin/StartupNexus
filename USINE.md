# USINE — documentation centrale

> **Document de référence unique du projet.** En cas de contradiction avec un autre fichier,
> **ce document fait foi**. Réécrit le 7 octobre 2026 pour la nouvelle conception (« usine
> d'assemblage »), à partir des six études menées du 5 au 7 octobre. L'ancienne version (trajectoire
> du 30 septembre : phases 0 à 6, générateurs de code) est conservée intacte dans
> [`archives/USINE_trajectoire_avant_assemblage_2026-10-07.md`](archives/USINE_trajectoire_avant_assemblage_2026-10-07.md).
>
> **Comment lire les statuts** : ✔ **prouvé** (par une étude, citée) · ✔ **validé** (décision de
> l'utilisateur) · ◐ **partiel** · ○ **à faire** · *proposé* (en discussion, n'engage pas).
> Seuls les statuts ✔ et le journal (§9) engagent.

---

## 1. Ce qu'on construit

Une **usine d'assemblage de logiciels de gestion** pour de petites structures (cabinet, atelier,
association, PME). À partir du brief d'un client, elle livre vite une application sûre, testée et peu
chère. ✔ validé (5 oct)

**Le principe en une ligne : l'IA comprend, un programme assemble.**

```
brief ──► COMPRENDRE ──► MIROIR ──────► TRADUIRE ───────► PIÈCES ──────► TESTS PAR RÔLE ──► app
          (IA)           (le client     (programme :      (programme :   (programme :         + sur-mesure
                          valide)        matrice → règles)  écrans)        serveur + écrans)    (humain)
```

- **La valeur est l'assembleur**, pas l'IA : à partir d'une matrice validée, il produit une app
  sûre et testée, presque sans coût. L'IA est un **accélérateur** : elle retire le temps humain de la
  compréhension (≈ 0,20 $ et une minute par brief) et rend l'usine utilisable sans rendez-vous.
- **Plan A** (cible) : l'IA écrit la description de l'app, le client la valide dans le miroir.
  **Plan B** (repli, et possible offre « concierge » pour les premiers clients) : la description est
  remplie avec le client, l'IA ne fait que proposer. Tout ce qui suit est identique. ✔ validé (7 oct)
- **Ce que l'IA ne fait jamais** : écrire le code de l'app (l'échec de l'ancienne usine) et décider
  de la sécurité (règles fixées par programme).
- **Objectif** : un produit commercialisable (pas un portfolio). Écart de marché observé dans les
  vrais briefs : budgets annoncés de 500 à 10 000 €, devis reçus en moyenne de 16 600 à 24 300 €.

### Les niveaux (des livrables testables en vrai)

| Niveau | Ce que l'app sait faire | Statut |
|---|---|---|
| **1 — Gérer** | des fiches, des rôles (1 à 3+), chacun ne voit et ne fait que ce qu'il doit ; des demandes à états | **en cours** (§6) |
| 2 — Prévenir | e-mails sur changement d'état, rappels | ○ |
| 3 — Montrer | calendrier, planning, graphiques | ○ |
| 4 — Relier | « ses » clients, « son » agence, partage fiche par fiche | ○ |
| 5 — Encaisser / connecter | paiement, liens avec d'autres logiciels | ○ |

L'ordre 2 → 5 est provisoire : il sera fixé par la demande réelle (les besoins « hors stock » que la
compréhension relève sur chaque brief). **On ne passe au niveau suivant que lorsque le précédent est
fini et testé en vrai.** ✔ validé (5 oct)

Hors périmètre : places de marché avec paiements au cœur, réseaux sociaux et messageries,
applications mobiles natives, design original.

---

## 2. Principes (acquis, confirmés par les essais)

1. **Loi du contenant.** Une intention du brief sans structure typée pour la porter s'évapore, même
   si l'IA l'a comprise. Étendre l'usine = ajouter du vocabulaire à la matrice, pas enseigner à l'IA.
   *(Confirmé en E5 : sans la nature « registre », l'IA ne pouvait pas exprimer « dossiers confidentiels ».)*
2. **Intelligence aux bords, programme au cœur.** L'IA comprend ; tout le reste est calculé.
3. **Une seule source par concept.** La matrice est calculée une fois ; règles serveur, droits
   d'écran, menus, tests et miroir en dérivent.
4. **L'app est des acteurs qui déroulent un processus sur des fiches.** L'unité de conception est
   l'acteur, pas l'écran.
5. **Affordance honnête.** Un bouton n'apparaît que si le serveur accepterait l'action.
6. **Clôture vs désir.** L'usine complète ce qui est impliqué par nécessité (clôture) ; ce qui n'est
   pas demandé remonte au client par le miroir. Dans le doute : désir.
7. **La description est le produit.** On corrige la description ou le traducteur, jamais le code livré.
8. **Des juges qui ne mentent pas** (§7). Un outil de mesure n'est cru qu'une fois prouvé (E4). Un
   juge tire ses attentes de la **source** (la matrice), jamais du fichier qu'il juge : sinon le fichier
   et le juge se trompent ensemble *(N1.0 : tests d'écran 1/4 → 4/4 erreurs attrapées)*.
9. **Moindre privilège.** Personne ne reçoit un droit qui n'est pas nécessaire à son rôle ou cité par
   le brief. Une exception oubliée donne un manque visible, jamais une fuite invisible.
10. **Des blocs complets.** ✔ validé (8 oct) Chaque mot de vocabulaire (nature, action, type de
   champ…) est un **bloc** : construire, écran, juger, prouver, livrés ensemble. Un programme le vérifie
   (`python -m usine carte`) : un mot sans son bloc empêche de fabriquer ; un mot pas encore construit
   est **refusé franchement**, jamais traité à moitié. Étendre l'usine = ajouter des blocs, sans
   toucher à ceux qui existent.
11. **Corriger une classe, jamais un cas.** ✔ validé (9 oct) Une correction qui cite un métier ou un
   brief est refusée ; **on n'assouplit jamais un juge pour faire passer une app** ; chaque défaut
   corrigé est verrouillé par un juge. Chaque correction est inscrite au registre (§7), et la
   convergence (défauts nouveaux par app nouvelle) doit décroître. *(Leçon de l'ancienne usine : ses
   générateurs étaient réajustés brief par brief, et la même panne revenait sous une autre forme.)*
12. **Avant, pendant, après.** ✔ validé (10 oct) **Avant**, accord de l'utilisateur (quoi, pourquoi,
   comment on saura que ça marche) : chaque étape, et même en cours d'étape toute règle de droits ou de
   sécurité, toute doctrine, tout ce qui change ce que le client verra. **Pendant**, les défauts trouvés
   par les juges sont corrigés sans attendre et inscrits au registre. **Après**, chaque compte rendu
   donne trois indicateurs vérifiables : convergence, couverture des vrais briefs, essais à la main.
   **Critère d'arrêt fixé d'avance** : si après N1.3 la couverture ne monte pas nettement, ou si les mêmes
   familles de défauts reviennent, on s'arrête et on repense.

### Circulation de l'information — 7 règles ✔ validé (30 sept)

Les étapes ne se parlent pas : chacune lit une fiche de forme fixe et en produit une autre.
1. **Un fait = un seul auteur.** 2. **Entre machines, des données, jamais du texte.**
3. **Contrôle strict à chaque frontière** : une réponse invalide est refusée et l'erreur précise est
renvoyée (N essais), jamais « devinée ». 4. **Fiches figées** : aucune étape ne corrige une fiche amont
en silence. 5. **L'IA reçoit le minimum, sous forme de données.** 6. **Les ordres d'exécution viennent
du plan, pas de l'IA.** 7. **Traçabilité** : chaque fichier sait de quelle case il vient.

Limite assumée : le contrôle bloque une fiche **mal formée**, pas une fiche **fausse** — d'où le
miroir validé par le client (§3.2) et les contrôles croisés entre lecteurs IA (E5).

---

## 3. La chaîne, maillon par maillon

### 3.1 Comprendre — l'IA écrit la description de l'app  ✔ prouvé · ◐ à compléter

**Comment** (`poc/comprehension/comprendre.py`) : 5 **lecteurs IA**, une question chacun, réponses en
JSON contrôlées par programme (forme stricte, identifiants connus, **citations recopiées mot pour
mot**), erreur renvoyée au lecteur (2 essais de plus). ✔ validé (8 oct) : on les appelle **lecteurs**,
pas « agents » — ils n'ont aucun outil et n'agissent sur rien ; ils lisent le brief et répondent à
une question, et c'est voulu (moins de liberté = moins de dérive).

| Lecteur | Question | Contrôles par programme |
|---|---|---|
| 1. Acteurs | qui se connecte, comment on le devient | un responsable ; pas d'inscription libre pour du personnel |
| 2. Fiches | quelles fiches, quelle nature, à qui | chaque non-utilisateur devient une fiche ; un registre a un responsable |
| 3. Circuits | quels états, qui fait chaque étape | ≥ 2 états et une flèche ; l'initiateur d'un registre le tient |
| 4. Droits explicites | ce que le brief dit (supprimer, tout voir…) | visiteur seulement sur une fiche publique ; un acteur rendu aveugle → droits revus |
| 5. Périmètre | dans / hors ; ce qui est hors stock | citations |

**Preuves** ([`etudes/05`](etudes/05-comprehension.md)) : 10 vrais briefs (lot d'apprentissage),
grille de référence écrite avant de lancer l'IA. gpt-4o-mini 3/10 ; gpt-5.4-mini 6/10 et instable ;
**gpt-5.5 9/10**, puis les 3 cas fragiles corrigés en v3. **Modèle retenu : gpt-5.5** ✔ validé.
Coût réel : 0,195 $ par brief.

**N1.1 (8 oct, en cours)** : les lecteurs sont dans l'usine (`usine/comprendre/`, commande
`python -m usine comprendre <brief> --nom <nom>`), les 5 premiers **inchangés**, plus deux nouveaux :

| Lecteur | Question | Contrôles par programme |
|---|---|---|
| 6. Champs | les informations de chaque fiche, leur type (11 types), obligatoires, valeurs d'un choix | cité par le brief (mot pour mot) ou « nécessaire » (un nom, si le brief ne cite rien) ; le reste → propositions pour le miroir ; jamais un lien, l'état ou une date automatique |
| 7. Libellés | titre de l'app, verbe de création, bouton de chaque étape | un bouton par état d'arrivée |

**Plafond de dépense dans le code** : chaque lancement s'arrête de lui-même au-delà de son plafond
(0,20 $ par défaut). Mesure du lecteur 6 seul contre une grille écrite d'avance
(`usine/mesures/`) : sur gpt-5.4-mini, médiathèque 8/8 et union sportive 3/3 sans invention, mais
autocars et formation faibles, et réponses instables d'un passage à l'autre. gpt-5.4-mini range aussi
les emprunts de la médiathèque en registre (lecteurs 1-5) : **il ne suffit pas**. Coût mesuré d'une
compréhension complète en gpt-5.5 : ≈ 0,33 $ par brief (lecteur 6 ≈ 0,11 $).

✔ **Prouvé (8 oct) : du texte du brief à l'app vérifiée, sans aucun fichier écrit à la main** —
médiathèque, gpt-5.5 : champs 8/8 justes et 0 inventé (genre en choix avec ses 4 valeurs), libellés
justes, un 3ᵉ rôle « gestionnaire » (l'auteur du brief) qui tient le catalogue ; app fabriquée :
132/132 règles, 7/7 tests d'écran. Coût : 0,46 $ (dont 0,14 $ pour redemander le lecteur 4 après un
défaut trouvé : il citait les états par leur libellé, et rien ne le refusait — le calculateur et le
contrôle du lecteur 4 refusent désormais tout état absent du circuit ; reprise `--reprendre` pour ne
repayer que ce qui est refusé).
**Vu, pour le miroir (N1.2)** : le gestionnaire ne voit pas les emprunts et le miroir ne le demande
pas (la doctrine « le responsable voit tout » ne couvre que les registres).

✔ **Lecteur 6 mesuré sur gpt-5.5** (3 briefs, grille écrite d'avance) : **15/16 informations
attendues trouvées (94 %)**, 0 type faux, 0 lien ou état pris pour un champ ; 1 « inventé » qui cite
le brief (« renouvellement automatique ou manuel » lu comme un choix) ; 1 manqué (« reste dû ou
avoir » fusionnés en un seul montant). gpt-5.4-mini : 0 à 1 sur 5 pour les autocars → **gpt-5.5
retenu pour tous les lecteurs**. Coût réel du lecteur 6 : 0,13 $ par brief ; compréhension complète
≈ 0,34 $ par brief (critère : < 1 $ par app).

**Pas prouvé / à faire** : stabilité de gpt-5.5 (un seul passage) ; la généralisation se mesurera à
l'examen (briefs jamais vus).

### 3.2 Le miroir — le client valide avant toute construction  ◐

**Existe** (`agents/capability_matrix.py` : `explain`, `questions`) : des phrases « qui peut faire
quoi » **produites par programme depuis la matrice** (elles ne peuvent pas mentir) et des questions
oui/non ciblées là où une erreur coûte (un acteur qui voit les données d'un autre, ce que voit un
visiteur, un registre vu en entier : « Le professionnel verra tous les dossiers, pas seulement ceux
qui le concernent — d'accord ? »). La question s'est déclenchée sur une vraie erreur de l'IA (E5).

**À faire** (○, niveau 1) : la **porte** (rien ne se construit avant validation), l'interface où le
client répond (chaque réponse modifie la description de façon déterministe), et le premier essai
avec de vrais clients. Le miroir est la protection n°1 contre une description fausse.

### 3.3 Traduire — matrice → règles d'accès  ✔ prouvé · ◐ traducteur v0 (N1.0) · ○ à généraliser (N1.3)

**Calculateur** (`agents/capability_matrix.py`, phase 3) : natures → préréglages au moindre privilège,
exceptions citées, clôture, pages / menus / tableaux de bord dérivés, miroir. Banc de 14 matrices
(12 de nos briefs + 2 vrais), toutes conformes à l'attendu.

**Traduction en règles ZenStack** ([`etudes/03`](etudes/03-regles-cas-durs.md)) : **11 patrons**
couvrent tous les cas essayés (profil, catalogue, registre, collection, saisie pour autrui, circuit —
une règle par flèche —, modification par état, enfant via `check(parent)`, « au travers de »,
suppression, tables de choix) + **2 règles systématiques** : clôture à la création
(`check(lien, 'read')`) et cohérence des propriétaires. Sur 5 cas (dont 2 vrais briefs) :
traduction mécanique, aucun cas impossible.

**Fait (N1.1)** : 11 types de champs (montant, choix ajoutés) ; données de démonstration fabriquées
par programme quand la description n'en donne pas ; 2 défauts trouvés par l'app d'essai des types
(`usine/exemples/types.json`) et corrigés à la source : « rien d'autre ne bouge » échouait sur un champ
facultatif vide (en SQL, vide = vide n'est pas vrai) ; la date de création pouvait être modifiée.
**Fait (N1.0)** : traducteur v0 (`usine/traduire/`) — description + matrice → schéma et règles,
notice, droits d'écran, données de départ. Sur la médiathèque, il redonne le schéma écrit à la main en
E6 (16 règles). **À faire** (○, N1.3) : le généraliser à tous les patrons et doctrines du §4 (enfants,
saisie pour autrui, modification par état…). Les pièges connus qu'il doit compenser sont au §4.

### 3.4 Les pièces d'écran  ✔ prouvé (plomberie) · ◐ squelette v0 (N1.0) · ○ catalogue à construire

**Décision** ([`etudes/06`](etudes/06-ecrans.md)) : **nos propres pièces**, sur les fonctions que
ZenStack génère depuis le schéma (`@zenstackhq/tanstack-query`). Refine écarté. ✔
**Architecture des pièces** : une **notice typée** (fiches, champs, libellés — chaque nom de champ
vérifié contre le schéma), un **affichage** partagé, une **plomberie** mince. Pièces génériques
essayées : liste de fiches, fiche + bloc de décision, mon profil (tests par rôle 3/3).
**Squelette v0** (`usine/modele-app/`, N1.0) : ces pièces + coquille, menu par rôle, bouton d'action
sur une ligne (« Emprunter »), connexion simulée. Règle apprise : une action qui change l'état est un
**formulaire** (POST), jamais un lien — Next précharge les liens visibles, et précharger un lien de
connexion revenait à se connecter (trouvé par les tests d'écran : 42 pages sur 50 au mauvais rôle).

**Catalogue du niveau 1** ([`etudes/01`](etudes/01-pieces-niveau-1.md)) — ○ à construire :
coquille + menu par rôle ✔ (essayé) · liste de fiches (◐ : pagination, filtres, tri à écrire) ·
fiche détail + bloc de décision ✔ · formulaire (○ : 12 types de champs) · mon profil ✔ ·
enfants dans le parent ○ · tableau de bord par rôle ○ · pages publiques ✔ · équipe (invitation avec
rôle) ○ · messages clairs (« interdit » / « introuvable » / saisie invalide) ○.

### 3.5 Les tests par rôle  ✔ prouvé · ✔ livrés dans chaque app (N1.0) · ◐ données de test à généraliser

- **Côté serveur** : `poc/regles/run.ts`, testeur générique qui lit la matrice et essaie chaque case
  (voir, voir par identifiant forcé, créer, créer au nom d'un autre, chaque flèche du circuit,
  changer le propriétaire, supprimer, intrus connecté sans rôle, changement de rôle…), en jugeant sur
  l'**état de la base**. **Prouvé par mutation** ([`etudes/04`](etudes/04-testeur-prouve.md)) :
  95,8 % des erreurs à effet attrapées ; **figé en version 1.0**.
  **v1.3 (N1.1b)** : même contenu, nouvelle structure — un **noyau** (personnes d'essai, jugement sur
  la base, rapport) et **un module par bloc** (`verification/blocs/` : voir, créer, modifier, circuit,
  supprimer, types de champs). Prouvé sans effet sur ce qui est vérifié : sur 3 apps, la liste
  complète des vérifications, leur ordre et leurs verdicts sont identiques à la v1.2.
  **v1.2 (N1.1, figée)** : il essaie aussi les dates, montants et choix (sautés en silence avant), les
  champs facultatifs vides puis remplis, et la date de création sous une modification ordinaire.
  Re-prouvée par mutation sur 2 apps : médiathèque 35/41 erreurs à effet (85 %), app des types 37/43
  (86 %) ; les manquées sont toutes la famille bénigne connue (ci-dessous).
  **v1.1 (N1.0)** : livré dans chaque app (`verification/`), il lit la description et la matrice de
  l'app ; la partie qui juge est inchangée, les données de test sont construites depuis la description
  (`cas.mts`). **Re-prouvé sur l'app fabriquée** (`usine/preuve_regles.mts`) : 33/49 erreurs attrapées ;
  des 16 survivantes, 10 sont sans effet (règles en double) et 6 sont bénignes mais non testées (relire
  ou modifier **ses propres** fiches après avoir perdu son rôle) → 33/39 erreurs à effet (84,6 %). Un
  vrai trou trouvé et corrigé en route : aucune fiche « reliée à rien » dans les données.
- **Côté écrans** ✔ prouvé (N1.0) : `e2e/roles.spec.ts`, livré dans chaque app — pour chaque rôle,
  menu, boutons de création, circuit, profil ; **attentes tirées de la matrice**. Prouvé par mutation
  (`usine/preuve_ecrans.py`) : 4/4 erreurs attrapées, témoin vert 3 fois (l'ancienne version, qui lisait
  les droits produits : 1/4). Il a trouvé dès son premier jour un vrai défaut du squelette (§3.4).
  **(N1.1b)** les sabotages sont maintenant **tirés de la matrice de chaque app** (donner un droit,
  retirer ou ajouter une étape, retirer « voir », retirer une entrée du menu, une pièce fixe cassée) :
  6/6 attrapés sur 3 apps, témoin vert — la preuve vaut pour n'importe quelle app.

**À faire** (○) : données de test pour tous les patrons (N1.4) ; le testeur essaie aussi le
changement de rôle **en lecture** et **sur les profils** (referme les 6 bénignes ; v1.2 re-prouvée) ;
tests d'écran des formulaires de création et de modification (N1.5).

---

## 4. Doctrines (règles que le traducteur applique toujours)

| Doctrine | Contenu | Origine |
|---|---|---|
| Natures | **profil** (une par acteur) · **catalogue** (référentiel visible de tous les connectés) · **registre** (fiches tenues par l'équipe, visibles de ceux qui le tiennent) · **collection** (éléments d'un acteur) · **enfant** (lignes d'un parent). Circuit permis sur collection et registre | phase 3 ; registre ajouté le 7 oct (E5) ✔ |
| Supprimer | jamais accordé par défaut ; seulement si le brief le dit | 1er oct ✔ |
| Responsable | le responsable de l'app voit en lecture tous les registres ; le client peut le refuser | 7 oct ✔ validé |
| Rôles listés | « connecté » se traduit par la **liste des rôles déclarés**, jamais « toute personne connectée » (un inconnu peut se créer un compte) | E4 ✔ |
| Clôture | on ne pointe que ce qu'on a le droit de voir — à la création **et à la modification** ; et on ne re-désigne qu'une fiche qu'on voit **directement** (pas seulement au travers d'autres fiches : elle deviendrait visible grâce au lien même qu'on pose) | E2 ; étendue N1.2 ✔ |
| Cohérence | deux fiches liées du même rôle propriétaire appartiennent à la même personne | E2 ✔ |
| Propriétaire immuable | le propriétaire d'une fiche ne change jamais | E2 ✔ |
| Une étape ne change que l'état | les autres champs restent identiques pendant une transition | E2, E4 ✔ |
| Prudence | un accès que le brief **limite** n'est pas élargi ; le partage fin est signalé hors stock | E5 ✔ |
| Visiteur | un droit sans compte seulement sur une fiche déclarée publique | E5 ✔ |
| Pas de confiance dans le refus de relecture | ZenStack peut répondre « refusé » alors que l'écriture a eu lieu : chaque interdiction est une règle explicite | E4 ✔ |
| Listes de valeurs | une liste **fixe** énumérée par le brief (« roman, essai, bande dessinée ») → un champ **choix** (la changer = refabriquer) ; une liste que le client **fait vivre** (catégories, tarifs, « 478 / 754 ») → un **catalogue** (des données) | E2 ; précisée N1.1 ✔ |
| Intégrité | on ne supprime pas une fiche que d'autres fiches désignent (restriction en base, jamais de suppression en cascade) ; l'écran grise le bouton et dit pourquoi | N1.2 ✔ |

**Pièges techniques connus** : bug ZenStack 3.9.7 (comparer un état à sa valeur d'avant → erreur
SQL ; contournement : nommer l'état) ; Prisma interdit qu'une IA remette une base à zéro (chaque
version de schéma d'essai a sa base neuve) ; Next.js 16.4 exige que la lecture de session soit derrière
un `<Suspense>`.

**Trous de vocabulaire restants** (○) : un **enfant** avec circuit d'états ; plusieurs rôles qui créent
« pour leur compte » ; l'administrateur qui **modifie** tout (la doctrine ne lui donne que la lecture) ;
« ses » clients / « son » agence (niveau 4). **Refusés franchement** par l'usine en attendant leur bloc
(N1.3) : fiches enfants, publication, liens multiples, saisie pour autrui.

---

## 5. Outils et dépendances

| Outil | Rôle | Statut | Porte de sortie |
|---|---|---|---|
| Next.js (16.x) | cadre de l'app | ✔ fixé | — |
| PostgreSQL | base de données | ✔ | — |
| **ZenStack v3** | règles d'accès (dans le schéma), données, et plomberie des écrans | ✔ retenu (PoC, E2, E4, E6) | CASL ou règles dans la base (Postgres RLS) ; appels directs à l'API RPC |
| TanStack Query | cache des données à l'écran | ✔ (E6) | — |
| Clerk | comptes, connexion, rôles | ✔ niveau 1, isolé à un seul endroit ; **à réévaluer avant le premier client** (RGPD : données aux États-Unis ; prix par utilisateur) | Better Auth (bibliothèque, utilisateurs dans notre base) |
| gpt-5.5 (OpenAI) | comprendre le brief | ✔ validé (E5) | Gemini Pro, Claude (le banc permet de comparer) |
| Playwright | tests par rôle dans un vrai navigateur | ✔ | — |
| ~~Refine~~ | — | ✘ écarté (E6) | — |

**Politique de dépendances** ✔ validé (7 oct) : (1) notre valeur ne vit jamais chez eux — la matrice
est à nous, les outils sont des cibles de traduction ; (2) bibliothèque plutôt que service, licence
libre ; (3) peu de dépendances, chacune avec une raison écrite et une porte de sortie ; (4) un seul
endroit du code touche chaque outil ; (5) versions figées, tests par rôle à chaque montée de version ;
(6) acheter le difficile et le générique, construire notre cœur.

**IA payante pour les vrais clients** : les offres gratuites peuvent utiliser les données envoyées ;
elles ne servent qu'aux essais sur des briefs publics.

---

## 6. Plan du niveau 1 — « Gérer »

**Le livrable** : à partir d'un brief de gestion, l'usine produit une app qui tourne, sûre, testée,
avec un miroir validé, sans écrire de code à la main pour cette app.

| Étape | Contenu | Statut |
|---|---|---|
| Essais E1-E6 | pièces, PoC, règles, testeur, compréhension, écrans | ✔ faits (études 01 à 06) |
| **N1.0 Squelette qui marche** | une commande transforme la médiathèque (description écrite à la main, champs compris) en app qui tourne et se vérifie seule, en passant par tous les maillons dans leur version minimale ; chaque N1.x suivante élargit un maillon d'une chaîne qui marche déjà | ✔ **fait** (7 oct) : `python -m usine fabriquer usine/exemples/mediatheque.json` → app en ~4 min, 10 étapes, 0 $ d'IA ; 104/104 règles, 6/6 tests d'écran ; juges re-prouvés par mutation |
| N1.1 Description complète | ajouter à la compréhension les **champs** des fiches (12 types, obligatoires, tables de choix) ; combler les trous de vocabulaire utiles au niveau 1 | ✔ **fait** (8 oct) : lecteurs 6-7 (champs 15/16 sur gpt-5.5), 11 types, testeur v1.2 re-prouvé ; **médiathèque du texte à l'app sans rien écrire à la main** (132/132, 7/7) ; 4 défauts trouvés et corrigés à la source ; 0,81 $ |
| **N1.1b Architecture en blocs** | chaque mot de vocabulaire = un bloc complet (construire, écran, juger, prouver) ; testeur en noyau + modules ; sabotages tirés de la matrice ; carte visuelle des blocs | ✔ **fait** (8 oct) : 32 blocs (23 complets, 6 partiels expliqués, 3 refusés franchement) ; contrôle d'architecture prouvé et branché sur `fabriquer` ; testeur v1.3 identique à la v1.2 sur 3 apps ; sabotages d'écran générés 6/6 sur 3 apps ; `python -m usine carte` ; 0 $ |
| **Répétition générale** (✔ validé, 8 oct) | les briefs du lot d'apprentissage passent dans toute la chaîne (descriptions déjà payées à l'étude 05 : 0 $ ; avec les champs : ≈ 0,15 $ par brief, sur accord) ; la liste de ce qui bloque fixe le contenu de N1.2 à N1.5. **Règle : on ne passe l'examen que quand la répétition le réussit (≥ 6/7)** — les briefs d'examen ne servent qu'une fois, et l'examen coûtera ≈ 3,40 $ (prévoir une recharge) | ◐ **temps 1 fait** (9 oct, 0 $, `python -m usine.repetition`) : 3/3 hors périmètre reconnus ; **7/7 briefs du périmètre fabriqués et jugés** (règles 100 % conformes, écrans verts) — dont 2 sans leur fiche enfant et 1 sans 3 exceptions v2 ; **mais 13 fiches sur 39 seulement se créent à l'écran, et aucune ne se modifie (hors profil)** : sûres, pas encore utilisables. 3 défauts trouvés et corrigés (registre n° 14-16). ✔ **Temps 2 fait (9-10 oct, chaîne réelle gpt-5.5, ≈ 6,3 $)** : 10 briefs d'apprentissage + 9 du corpus 2 (arrêt au 10e sur 33 : crédit épuisé) ; **périmètre juste 19/19 ; 15/16 apps fabriquées et jugées par les juges actuels** (8 complètes, 7 variantes), la 16e (boutons homonymes) attend une nouvelle lecture ; 15 corrections (n° 29-43) ; mesure : fiches enfants 6/16, profil relié 3/16, « celles qui le désignent » 2/16 ; hors stock : calculs 11/16, documents 10/16, planning 9/16. Apps remises à l'utilisateur pour essai à la main (`usine/ESSAIS.md`) ; tableau de bord « Usine d'assemblage » |
| **N1.2 Formulaires** (✔ ordre validé le 9 oct, d'après la répétition) | chaque droit a son geste à l'écran : créer (formulaire + choix des fiches liées visibles), modifier (selon l'état), supprimer (avec confirmation) ; clôture et cohérence aussi à la modification | ✔ **fait** (9 oct, 0 $) : **39/39 fiches créables à l'écran** dans les 7 apps de la répétition (contre 13), modification et vraie suppression jouées ; intégrité (« on ne supprime pas une fiche désignée ») ; testeur v1.4 ; 2 trous de sécurité trouvés et fermés avant tout client ; sabotages d'écran 8/8, 8/8, 6/6 |
| N1.3 Traducteur complet (✔ fiche validée le 10 oct : les 3 blocs manquants mesurés sur les vrais briefs) | **fiches enfants**, profil relié à une fiche, « celles qui le désignent » ; préalable : tests d'écran découpés en noyau + un module par bloc ; critère : 16/16 apps complètes ; signal d'alarme : fichiers existants touchés par bloc. Puis publication, saisie pour autrui | ◐ **préalable fait** (tests d'écran en modules, verdicts identiques, sabotages 8/8) ; **bloc « enfant » construit** (traducteurs, cascade seule exception, pièce « Lignes », juge `enfant.mts` v1.5, juge d'écran ; app d'essai des types : 267/267, 16/16, sabotages des règles 27/27 à effet) → formation, portes, bâtiment deviennent complets (11/16 à confirmer par refabrication) ; restent : profil relié, « celles qui le désignent » |
| N1.4 Miroir v1 | porte de validation ; interface de réponse aux questions ; corrections déterministes ; la question « le responsable voit-il les collections ? » | ○ |
| N1.5 Connexion et équipe | Clerk, invitations par rôle ; données de test du testeur (changement de rôle en lecture, sur les profils) | ○ |
| N1.6 Assembleur | brief → app, de bout en bout ; tests par rôle (serveur + écrans) produits automatiquement ; **démonstration visuelle** : page de suivi de la fabrication + le robot d'écran joué dans un navigateur visible et filmé (« l'app vérifie elle-même que l'adhérent ne peut pas accepter son emprunt ») | ○ |
| N1.7 Examen | les 10 briefs cachés (`harness/briefs_reels/examen/`), textes originaux recueillis ce jour-là ; puis 3 premiers vrais utilisateurs | ○ |

**Organisation du code** ✔ validé (7 oct) : un dossier neuf **`usine/`** à la racine (comprendre,
matrice, miroir, traduire, modele-app, assembler, verifier) ; chaque fabrication laisse ses fiches dans
`runs/<n°>/` ; une simple commande (`usine fabriquer …`), **sans Temporal au départ** (il viendra
quand le miroir devra attendre un client pendant des jours) ; l'ancienne usine reste intacte jusqu'à
la réussite de l'examen, puis elle est retirée.

**Ce qui est produit vs ce qui est fixe** : une app = le **squelette fixe** (pièces, plomberie,
affichage — écrits et testés une fois, versionnés) + des **fichiers de données produits** par les
traducteurs (schéma et règles, notice, droits d'écran, données de départ, tests) + un dossier
**`sur-mesure/`** (le code propre à un client, écrit à la main, jamais touché par l'usine).

**Voir l'usine travailler** : chaque étape écrit un événement (résultat, durée, coût) → journal de
fabrication dans le terminal dès N1.0 ; page de suivi visuelle (aussi démonstration client) en N1.6.

**Critères de fin du niveau 1** ✔ validés (7 oct) : sur les 7 briefs d'examen dans le
périmètre, au moins 6 apps assemblées qui compilent et passent tous leurs tests par rôle, **zéro
accès forcé accepté** ; les 3 hors périmètre reconnus ; coût d'IA < 1 $ par app ; et l'avis de 3
utilisateurs réels.

**Méthode** ✔ validé : une fiche avant chaque étape (but, ce que tu verras, fichiers touchés, coût,
taille, risque) ; travail sans interruption jusqu'au compte rendu ; compte rendu d'une page (fait /
prouvé / fait à la main / risques / suite) ; un outil est figé et prouvé avant qu'on se fie à ses
mesures ; essais d'un concept sur la vraie IA avant de le construire.

**Budget IA** ✔ révisé (9 oct, par l'utilisateur) : **le coût n'est pas un frein à l'apprentissage
ni à l'expansion** (corpus de briefs, mesures, nouvelles capacités) ; le coût réel est rapporté dans
chaque compte rendu ; un plafond technique de 2 $ par lancement protège seulement contre une boucle qui
s'emballerait ; le solde qui fait foi est celui du tableau de bord de l'utilisateur. Les preuves
complètes par sabotage ne se font qu'en fin d'étape. *(Remplace la règle du 7 oct : rien au-delà de
0,20 $ sans accord.)*

**En continu** : les besoins « hors stock » relevés sur chaque brief sont comptés pour fixer l'ordre
des niveaux 2 à 5 (`scripts/non_couverts.py`, à brancher sur la nouvelle compréhension).

---

## 7. Les juges

| Juge | Ce qu'il juge | Statut |
|---|---|---|
| Contrôles stricts aux frontières | la forme de chaque réponse de l'IA | ✔ (E5) |
| Banc des matrices | le calculateur contre 14 matrices attendues | ✔ 14/14 |
| Testeur par rôle (serveur) | les règles d'accès, case par case, sur l'état de la base | ✔ prouvé par mutation (E4) ; livré dans chaque app ; v1.2 re-prouvée (N1.1 : 85-86 % des erreurs à effet) |
| Compilateur (TypeScript) | la cohérence notice / schéma / code | ✔ (E6) |
| Tests Playwright par rôle | ce que chaque rôle voit et peut faire à l'écran | ✔ livrés dans chaque app, attentes tirées de la matrice ; créer / modifier / supprimer / circuits / profil (N1.2) ; (10 oct) une création permise mais impossible **échoue** (n° 39), le circuit est **parcouru** état après état (n° 42), **un profil par rôle**, lecture seule si non modifiable ; sabotages tirés de la matrice : 8/8, 8/8, 6/6 sur 3 apps, puis **8/8 sur une app à 3 profils et circuit à 3 états** (clôtures) |
| Contrôle d'architecture | chaque mot de vocabulaire a son bloc complet | ✔ (N1.1b) ; vu échouer sur fautes simulées |
| Miroir validé | l'intention du client | ◐ (phrases et questions ; porte à construire) |
| Grille de référence | la compréhension de l'IA (écrite avant de lancer l'IA) | ✔ (E5, N1.1) |
| Répétition générale | toute la chaîne sur le lot d'apprentissage | ✔ temps 1 (9 oct) ; ✔ temps 2 en chaîne réelle (9-10 oct) : 7 apprentissage + 9 corpus 2 ; `python -m usine.mesures.corpus` mesure périmètre, blocs manquants, hors stock, coût |
| Examen sur briefs cachés | la généralisation | ○ (N1.7) |

**Un juge** est un programme qui vérifie une app produite, seul, et rend un verdict (conforme / pas
conforme) contre la matrice. Il peut se tromper de deux façons : **fausse alarme** (visible : on
enquête) ou **aveuglement** (invisible : dangereux) — d'où la **preuve par sabotage** (on casse l'app
exprès ; le juge doit le voir) et le **témoin** (l'app intacte ; le juge doit dire conforme). Trois
sortes d'erreurs, trois filets : erreur de l'IA → contrôles + miroir ; erreur de l'usine → juges ;
erreur d'un juge → sabotages + apps nouvelles.

### Registre des corrections ✔ validé (9 oct)

Chaque correction, sa nature, qui l'a trouvée, si elle est générale, et le sens du juge. Règle 11 :
aucune correction propre à un brief, aucun juge assoupli.

| # | Date | Correction | Nature | Trouvée par | Générale ? | Juge |
|---|---|---|---|---|---|---|
| 1 | 7 oct | connexion simulée en liens (préchargés) → formulaires | défaut de l'usine (squelette) | tests d'écran | oui | — |
| 2 | 7 oct | tests d'écran : attentes tirées de la matrice, pas du fichier jugé | **mon erreur** (aveuglement) | relecture | oui | plus strict |
| 3 | 7 oct | données d'essai : une fiche reliée à rien | trou du juge | sabotage | oui | plus strict |
| 4 | 7 oct | caractère invisible (BOM) dans un réglage | erreur d'outillage | construction | oui | — |
| 5 | 8 oct | « rien d'autre ne bouge » échouait sur un champ facultatif vide | défaut de l'usine (traducteur) | app d'essai des types | oui | — |
| 6 | 8 oct | la date de création pouvait être modifiée | défaut de l'usine (traducteur) | juge étendu | oui | — |
| 7 | 8 oct | dates décalées (serveur à l'heure locale, base en UTC) | défaut de l'usine (squelette) | juge étendu | oui | — |
| 8 | 8 oct | dates mal affichées et mal ressaisies | défaut de l'usine (squelette) | relecture des écrans | oui | — |
| 9 | 8 oct | dates, montants, choix ; champs facultatifs vides ; date de création en modification | trous du juge | relecture, sabotage | oui | plus strict |
| 10 | 8 oct | test du circuit : ordre des rôles | **mon erreur** (fausse alarme) | app nouvelle | oui | plus juste |
| 11 | 8 oct | états cités par leur libellé, acceptés sans contrôle | trou des contrôles (calculateur, lecteur 4) | premier essai bout à bout | oui | plus strict |
| 12 | 8 oct | matrice de référence « coworking » encodait l'inexprimable | erreur du banc | contrôle n° 11 | oui | plus strict |
| 13 | 8 oct | publication à moitié construite → refusée franchement | défaut de l'usine | inventaire des blocs | oui | — |
| 14 | 9 oct | une liste n'affichait que le premier bouton de création | défaut de l'usine (pièce) | répétition | oui | — |
| 15 | 9 oct | citation sur plusieurs lignes : le schéma cassait | défaut de l'usine (traducteur) | répétition | oui | — |
| 16 | 9 oct | circuits des registres jamais essayés à l'écran | trou du juge | répétition (tests « sautés ») | oui | plus strict |
| 17 | 9 oct | test d'écran : comptait les boutons de la page précédente, gardée cachée par Next | **mon erreur** (fausse alarme) | répétition | oui | plus juste |
| 18 | 9 oct | générateur de sabotages : proposait des sabotages sans effet visible (« créer » au visiteur qui ne voit pas la liste) | **mon erreur** (preuve trop faible) | répétition | oui | plus strict |
| 19 | 9 oct | la clôture et la cohérence des propriétaires ne s'appliquaient qu'à la création, pas à la modification d'un lien | défaut de l'usine (traducteur ; trou de sécurité latent) | conception des formulaires | oui | plus strict (testeur v1.4) |
| 20 | 9 oct | la suppression permise seulement dans certains états n'était pas essayée état par état | trou du juge | app d'essai des types | oui | plus strict |
| 21 | 9 oct | données d'essai : une collection désignée par une autre n'avait aucune fiche reliée à rien | trou du juge (famille du n° 3) | sabotage | oui | plus strict |
| 22 | 9 oct | test « modifier » : une même valeur écrite dans des fiches liées s'affichait trois fois | **mon erreur** (fausse alarme) | répétition (union) | oui | plus juste |
| 23 | 9 oct | qui ne voit une fiche qu'au travers d'autres pouvait re-désigner un lien vers une fiche cachée (la vérification tournait en rond) | défaut de l'usine (traducteur ; **trou de sécurité**) | testeur v1.4 | oui | plus strict |
| 24 | 9 oct | « Supprimer » proposé sur une fiche que d'autres désignent, puis refus technique incompréhensible | défaut de l'usine (pièce ; affordance malhonnête) | tests d'écran (union) | oui | plus strict (intégrité jugée) |
| 25 | 9 oct | doctrine « tables de choix » contredisait les champs « choix » de N1.1 | incohérence de la documentation | relecture | oui | — |
| 26 | 9 oct | l'intégrité ne reposait que sur la contrainte de la base (refus par erreur technique) → règle explicite « on ne supprime pas une fiche désignée » | défaut de l'usine (traducteur ; doctrine E4 non appliquée) | testeur v1.4 (refus compté comme erreur) | oui | — |
| 27 | 9 oct | test « supprimer » : cherchait le lien par le nom, alors que le lien d'une ligne était l'état ; et la liste ouvrait une fiche en cliquant sur « actif » | **mon erreur** (fausse alarme) + défaut d'ergonomie (pièce) | répétition (union) | oui | plus juste |
| 28 | 9 oct | test « supprimer » : comptait les lignes avant la fin du chargement de la liste | **mon erreur** (fausse alarme) | répétition (union) | oui | plus juste |
| 29 | 9 oct | un profil qui désigne une autre fiche (« l'agence du chef de projet ») était accepté sans être construit : le profil, créé tout seul à la première connexion, ne peut pas remplir ce lien → l'app aurait planté → refusé franchement (bloc « lien depuis un profil », N1.3) | défaut de l'usine (contrôle de la description, famille du n° 13) | testeur (10 refus comptés comme erreurs : livraison bloquée) | oui | — |
| 30 | 9 oct | chaque app gardait ses dépendances (620 Mo, identiques pour toutes) : disque plein après ~55 fabrications (39 Go) → retirées à la livraison, réinstallées à la demande par `demarrer` | défaut de l'usine (assemblage) | répétition temps 2 (disque plein) | oui | — |
| 31 | 9 oct | sur une fiche à circuit, « une étape ne change que l'état » comparait un champ **choix** à sa valeur d'avant : erreur SQL de ZenStack (même bogue que l'état) → écrit valeur par valeur | défaut de l'usine (traducteur) | testeur (erreur, livraison bloquée — union sportive) | oui | — |
| 32 | 9 oct | l'app d'essai des types ne mettait que 3 types sur 11 (tous facultatifs) sur sa fiche à circuit : la règle du n° 31 n'avait jamais été essayée → la commande porte les 11 types, obligatoires et facultatifs, et un code de choix identique à un état (217/217) | trou du juge (famille du n° 9) | n° 31 | oui | plus strict |
| 33 | 9 oct | l'accueil et l'en-tête affichaient l'identifiant du rôle (« responsable_des_commandes ») au lieu de son libellé → libellés produits par le traducteur (squelette mis à jour après la répétition en cours) | défaut de l'usine (traducteur + pièce) | essai de lancement avant remise à l'utilisateur | oui | — |
| 34 | 9 oct | une fiche qui ne désigne rien pouvait n'avoir aucun champ pour la reconnaître (« chauffeur » : amplitudes, couleur — les listes et les choix de lien l'auraient affiché par sa couleur) : la consigne interdisait le champ « nécessaire » dès que le brief citait une information → le premier champ fait reconnaître la fiche ; « nécessaire » permis (en premier) quand rien de cité ne la fait reconnaître ; 1 réponse sur 10 redemandée | défaut de l'usine (consigne + contrôle du lecteur 6) | relecture du miroir avant remise à l'utilisateur | oui | — |
| 35 | 9 oct | qui crée une fiche devait choisir une fiche qu'il ne voyait qu'au travers des fiches existantes (le 1er « bon d'intervention » impossible : aucun collaborateur à choisir) ; le calculateur le savait mais n'émettait qu'une **alerte**, que rien n'arrêtait → il voit toutes les fiches à désigner… **sauf** si elles appartiennent à des personnes de son propre rôle (le client qui choisit SON site) : alors refus (« celles qui le désignent », N1.3), jamais d'ouverture à tous. Banc : 1 attendu corrigé (il encodait la création impossible, famille du n° 12) | défaut de l'usine (calculateur) + erreur du banc | tests d'écran (création impossible, portes) ; **la fuite entre clients de ma 1re version** trouvée par la mesure d'impact avant toute fabrication | oui | — |
| 36 | 9 oct | « les siennes » accepté sur une fiche sans propriétaire (« le client voit ses équipements ») : aucune règle écrite, l'acteur ne voyait rien en silence, et le testeur plantait → refusé franchement (bloc « celles qui le désignent », N1.3) | défaut de l'usine (contrôle de la description) | testeur (plantage, 2 briefs) | oui | — |
| 37 | 9 oct | une fiche sans texte court s'affichait par son identifiant technique dans les choix de lien (« cmv1qsz… ») → le meilleur champ existant sert de titre | défaut de l'usine (traducteur) | capture de l'échec d'écran (portes) | oui | — |
| 38 | 10 oct | **un seul profil par app** : le traducteur ne gardait que le dernier ; dans une app où chaque rôle a son profil, les autres rôles n'avaient ni profil créé à la connexion ni « Mon profil » (qui montrait celui d'un autre rôle), et tout ce qui désigne leur profil (« l'équipe et ses membres ») était impossible à créer → un profil par rôle ; « Mon profil » cherche le SIEN ; les autres rôles qui voient ces profils les ont en liste | défaut de l'usine (traducteur + squelette) | tests d'écran (création impossible, clôtures) | oui | — |
| 39 | 10 oct | test d'écran « création » : **sauté** quand il n'y avait rien à choisir — le saut cachait le n° 38 ; et le constat se faisait avant la fin du chargement des listes → une création permise mais impossible **échoue** ; on attend le chargement | trou du juge | n° 38 | oui | plus strict |
| 40 | 10 oct | test du profil : cherchait le champ « Nom » par un libellé approché (deux champs le contenaient) | **mon erreur** (fausse alarme) | répétition (client simulé) | oui | plus juste |
| 41 | 10 oct | « Mon profil » proposait « Enregistrer » à un rôle qui n'a pas le droit de modifier son profil (« seuls les administrateurs modifient ») : refus technique → lecture seule (affordance honnête) ; le test du profil suit la matrice | défaut de l'usine (pièce) + **mon erreur** (test qui supposait le droit) | tests d'écran (dépannage) | oui | plus juste |
| 42 | 10 oct | test d'écran « circuit » : seule la 1re étape était essayée — une étape plus loin (« orange → vert ») pouvait disparaître sans être vue (sabotage survivant, clôtures) → le test parcourt le circuit état après état ; preuve : 8/8 | trou du juge | preuve par sabotage | oui | plus strict |
| 43 | 10 oct | deux boutons **homonymes** sur une fiche : « Supprimer » (passer à l'état « supprimé ») à côté de « Supprimer » (effacer la fiche) → le lecteur 7 n'a plus le droit de reprendre un geste de l'application ni de donner deux fois le même nom (consigne + contrôle) ; le test d'écran le vérifie explicitement. L'app concernée (support-interventions) attend une nouvelle lecture (≈ 0,03 $, après recharge) | défaut de l'usine (consigne + contrôle du lecteur 7) + trou du juge | tests d'écran plus stricts (support-interventions) | oui | plus strict |

| 44 | 10 oct | un formulaire envoyé pendant qu'une liste de choix chargeait partait avec un **lien vide**, refusé par la base avec un message incompréhensible (« An error occurred… ») — un utilisateur pressé l'aurait vécu. Je l'avais classé « échec passager » le matin (dépannage) ; il est revenu sur le **témoin** d'une preuve par sabotage (clôtures) → le formulaire attend (« Patientez ») et n'envoie jamais un lien absent ; le test « modifier » ralentit exprès les listes et clique aussitôt ; le serveur journalise désormais ses refus | défaut de l'usine (pièce) + trou du juge + **mon erreur** (classé passager) | témoin de la preuve par sabotage | oui | plus strict |

| 45 | 10 oct | juge du bloc neuf « enfant », **avant toute livraison** : sa preuve par sabotage a trouvé 3 trous (retirer la ligne de la commande d'un autre ; date de création d'une ligne ; changer l'article d'une ligne vers un article visible) → comblés, 27/27 sabotages à effet attrapés ; le juge d'écran ne regardait le parent que dans son état de départ → joué aussi quand le circuit l'a fait avancer ; la section des lignes s'affichait même sans le droit de les voir → conditionnée | trou du juge (bloc neuf) + défaut de l'usine (pièce) | preuve par sabotage du bloc | oui | plus strict |

| 46 | 12 oct | droits des LIGNES décidés à **deux endroits** : le calculateur ne faisait pas hériter les droits du parent dès qu'une exception visait la ligne (même pour « voir » seulement), et le traducteur recalculait les droits depuis le parent sans lire la matrice → la matrice refusait le retrait que les règles permettaient (bâtiment, clôtures) → une exception ne remplace que l'action qu'elle nomme ; traducteur, pièce « Lignes » et juge d'écran lisent tous la case de la ligne (règle 1 : un fait, un seul auteur) ; vérifié à sec sur les 14 sortes de lignes des 7 apps : 0 écart. **Même famille que le n° 35** (« une décision à deux endroits ») — recherche à la racine prévue (plan de convergence, étape 3) | défaut de l'usine (calculateur + traducteur ; **mon erreur de conception** du bloc) | testeur (2 vrais briefs) | oui | — |

| 47 | 12 oct | une app livrée ne démarrait pas (« tsx introuvable », Next.js incomplet) : la suppression des dépendances en fin de fabrication s'était arrêtée à mi-chemin (fichier encore ouvert, Windows), et `demarrer` prenait un dossier qui EXISTE pour une installation complète → une marque « installation complète » est posée après chaque installation réussie et retirée en premier avant toute suppression ; sans elle, `demarrer` réinstalle (2 tentatives de suppression) | défaut de l'usine (assemblage, n° 30) | **premier essai à la main de l'utilisateur** | oui | — |

| 48 | 13 oct | **famille « une décision à deux endroits » traitée à la racine** (plan de convergence, étape 3) : (A) le lien de propriété (ownerId → userId) décidé par 3 morceaux de code aux conditions légèrement différentes — défaut **latent**, qui aurait cassé avec la saisie pour autrui → une seule définition (`lien_proprietaire`, matrice `owner_links`), lue par l'usine et le testeur ; (B) les droits des lignes calculés deux fois dans le calculateur → une seule section ; (C) « une ligne s'ajoute quand elle se modifie » recodé à 4 endroits → la matrice porte `create_while` ; (D) « choisir parmi les siens » recalculé par l'outil de répétition → lu dans la matrice (`own_choice_links`) ; (E) refus de blocs reconnus à des morceaux de phrase → codes stables `[bloc:<id>]`. **Preuve** : banc 14/14 ; photo avant/après de tout ce que l'usine produit pour 19 apps : règles, écrans, droits, données **identiques** ; seuls les textes d'explication de 3 matrices changent (plus justes : ils citent maintenant l'exception qui fait gérer les lignes) | défaut de l'usine (latent) + structure | recensement « qui décide quoi » | oui | — |

| 49 | 13 oct | boîte aux lettres : questions numérotées 0001, 0002… pour chaque lecture → une réponse en retard d'un essai arrêté (un agent finissait après le nettoyage) aurait été prise pour la réponse à la nouvelle question du même numéro (évité à la main de justesse) → chaque lecture a ses numéros (« <date>-0001 ») et range les anciennes questions dans `boite/archives/` ; et (signalé par la session isolée elle-même) les agents lancés avaient tous les outils alors que les demandes contiennent des briefs venus d'internet → agent `lecteur` limité à lire et écrire, réglages du dossier non modifiables | défaut de l'usine (boîte aux lettres, neuve) | premier essai réel ; la session isolée | oui | — |

| 50 | 13 oct | circuit d'états posé sur un **catalogue** (qui ne change pas d'état) : l'assemblage le laissait tomber **en silence**, mais le lecteur des droits recevait quand même ses états et pouvait les citer → matrice refusée (union sportive, lecture Claude). Encore la famille « une décision à deux endroits » → une seule définition (`circuit_admis`), et le contrôle du lecteur 3 refuse ce circuit (l'IA corrige elle-même) ; rejoué sur les 28 lectures existantes : seule celle-ci est concernée | défaut de l'usine (contrôle + assemblage de la compréhension) | mesure de la session Claude (lot 2) | oui | plus strict |

| 51 | 13 oct | lignes qui désignent d'autres lignes (portes, lecture Claude : la ligne de checklist d'un bon désigne un point de checklist, lui-même ligne d'un type d'intervention) : (a) le juge d'écran essayait les lignes dans le désordre, puis retirait la ligne qu'il venait d'ajouter → plus rien à choisir → il suit l'ordre de création et laisse une ligne quand d'autres en dépendent ; (b) le formulaire laissait cliquer « Ajouter » sans rien à choisir (refus incompréhensible) → il bloque avec « il faut d'abord créer … » ; (c) une ligne qui « désigne » aussi son parent (bâtiment, mesures-terrain : erreur propre à Claude, jamais vue chez gpt) faisait planter la génération (champ en double) → refusée par le contrôle du lecteur 2 et par la description. Portes : 52/52 écrans | trou du juge + défaut de l'usine (pièce, contrôle) | mesure de la session Claude (lot 3) | oui | plus strict |

| 52 | 13 oct | « voir les siennes » accordé à un acteur qui ne possède PAS ces fiches (« l'enseignant voit les siennes » parmi les notes des étudiants) : accepté en silence, règle qui ne lui montrait rien (le juge l'a vu : 449/450) → refusé franchement comme le n° 36 (bloc « celles qui le désignent ») ; rejoué sur toutes les lectures : seule celle-ci concernée ; plateforme éducative en variante : 448/448, 36 écrans | défaut de l'usine (contrôle de la description, famille du n° 36) | testeur (corpus, lot C1) | oui | — |

| 53 | 14 oct | « créer le compte d'une autre personne » (le RH crée les comptes des employés) : un droit de création sur un PROFIL donné à un autre rôle était traduit en règle absurde (le RH pouvait se créer une fiche d'employé à lui-même — le juge l'a vu : 616/618) → refusé franchement, nouveau bloc « Invitation » (prévu avec la connexion et l'équipe, N1.5) ; seule cette lecture concernée | défaut de l'usine (contrôle de la description) | testeur (corpus, lot C2) | oui | — |

| 54 | 15 oct | fiche du menu qui désigne une LIGNE (dossiers-maintenance : l'intervention désigne un matériel installé, ligne d'un dossier client) : le bloc « créer » passait avant le bloc « enfants » → rien à choisir, l'app était bonne (une relecture qui met le matériel au menu passe) → le bloc « créer » ajoute, à sa place dans l'ordre de création et par la page du parent, toute ligne que d'autres fiches désignent (geste « ajouter une ligne » mis en commun au noyau) ; trou révélé au passage : le bloc « enfants » comptait les lignes avant leur chargement (0 au lieu de 1, invisible tant qu'aucune ligne n'existait d'avance) → il attend la section. Maintenance 38/38 écrans (1 échec avant), non-régression bâtiment 24/24, portes 53/53 | trou du juge | testeur (corpus, lot C2) | oui | plus strict |

| 55 | 15 oct | l'état d'une fiche cherché dans N'IMPORTE QUEL champ (garage : l'état « à effectuer » trouvé aussi dans « Réparations à effectuer », champ rempli par le juge → arrêt ; à l'inverse, un état faux pouvait passer si un autre champ contenait le bon libellé) → le bloc « circuit » lit le champ « État » seul, texte exact (geste commun `champEtat` au noyau, déjà celui de `etatAffiche`). Garage 19/19 écrans (1 échec avant), non-régression portes 53/53, maintenance 38/38 | trou du juge | testeur (corpus, lot C4a) | oui | plus strict |

| 56 | 16 oct | un rôle qui MODIFIE, supprime ou fait avancer des fiches qu'il ne VOIT pas (flotte-assurance, variante : l'administrateur « gère » contrats et véhicules, mais son « voir les siennes » erroné a été retiré) : accepté par le calculateur → l'app refusait ses gestes sur les véhicules (82/85) et écrivait ses créations en lui répondant « refusé » (5 écritures malgré le refus) → clôture « on voit ce qu'on modifie » (les siennes s'il en est propriétaire, sinon toutes ; voir donne moins que modifier ; créer sans voir reste permis = dépôt), avant l'héritage des lignes. Rejoué sur 113 descriptions : 11 cases changent, toutes dans 3 variantes (flotte, congés-attestations ×2), aucune vraie lecture ; banc des matrices 10/10 sans écart ; flotte refabriquée 85/85, 0 écriture malgré refus, 11/11 écrans | défaut de l'usine (calculateur ; famille des droits incohérents, n° 36, 52) | testeur (corpus, lot C4b) | oui | — |

| 57 | 16 oct | le bloc « enfants » marquait ses lignes d'essai de la MÊME façon à ses deux passages (parent au départ / avancé) : quand le rôle ajoute mais ne retire pas (l'agent ajoute des photos à son intervention ; une pièce à un dossier), la ligne du 1er passage reste → au 2e, deux lignes portent « la » marque → arrêt (nettoyage, suivi-dossiers ; vu en rejouant tout le corpus avec les juges n° 54-55, confirmé sur base neuve) → la marque porte le passage. Rejeu du corpus : 31/31 apps vertes (nettoyage 29/29, suivi-dossiers 9/9 ; non-régression maintenance 35/35, portes 53/53) | trou du juge | rejeu du corpus avec les juges actuels | oui | plus strict |

| 58 | 18 oct | les VARIANTES proposées au client « à la place » d'une demande refusée (réutilisées par le miroir N1.4a depuis l'outil de répétition) pouvaient DONNER des droits refusés par le brief : retirer « saisie pour autrui » faisait saisir le propriétaire lui-même (l'étudiant créait ses notes et diplômes, l'employé modifiait ses soldes de congés) ; trouvé par le critique (essai A) → **règle validée par l'utilisateur : une variante ne fait que RETIRER** (pour autrui → la fiche est retirée ; « voir les siennes » refusé → le droit est retiré et dit en clair « ⚠ … ne verra pas … » ; publication → la fiche est retirée) + contrôle par programme `elargissements` (matrice de la variante ⊆ matrice de la lecture, case par case) : une variante qui élargirait n'est ni proposée ni fabriquée (2 cas sur 17 : un responsable « voir les siens » → « voir tous »). Phrases de retrait écrites pour le client. Plateforme éducative refabriquée : 282/282 règles, 24 écrans, l'étudiant sans accès aux notes ni aux diplômes ; couverture du miroir 73/73 | **mon erreur de conception** (N1.4a) + défaut de l'usine (variante) | critique IA (essai A) | oui | plus strict |

| 59 | 18 oct | miroir (N1.4a) : (a) une case « crée sans voir » (dépôt) donnait « … affichés dans les  qu'il consulte » (phrase vide) → « crée des … sans les voir ensuite (dépôt) » ; (b) les raisons de refus étaient montrées brutes au client (codes, messages techniques) → le client lit les retraits en phrases, les raisons brutes vont au volet concepteur | **mon erreur** | lecture des miroirs (essai A) | oui | — |

**Fragilité relevée, à corriger** : chaque fabrication télécharge le moteur de base de données (Prisma) depuis internet ; une coupure (12 oct, ~19 h) arrête l'usine à l'étape « créer les tables ». À mettre en cache local.

**Bilan au 14 oct** : 53 corrections — 33 défauts de l'usine (dont 2 trous de sécurité, n° 19 et 23),
9 trous des juges, 8 erreurs de ma part, 1 erreur du banc, 1 d'outillage, 1 incohérence de documentation
(classées par leur nature principale, comme sur le tableau de bord) ; **0 propre à un brief, 0 juge assoupli**.

**Règles qui se masquent** : quand deux protections se recouvrent (ex. « ne pointer qu'une adresse qu'on
voit » et « seulement du même propriétaire »), retirer l'une ne change rien et le sabotage « survit ».
On les prouve alors **ensemble** (sabotage de groupe : les retirer toutes à la fois) — fait à la main
le 9 oct sur l'app d'essai des types : 2 groupes sur 2 attrapés. À intégrer à l'outil de preuve (○).

**Convergence** (défauts nouveaux de l'usine ou des juges, par app nouvelle) :

| Moment | Apps nouvelles | Défauts nouveaux | Par app |
|---|---|---|---|
| N1.0 | 1 (médiathèque) | 4 | 4 |
| N1.1 | 2 (types, médiathèque par l'IA) | 8 | 4 |
| Répétition, temps 1 | 7 (6 domaines jamais vus) | 5 (n° 14-18) | 0,7 |
| N1.2 formulaires (**parties neuves** : créer, modifier, supprimer à l'écran) | 0 app nouvelle ; 9 apps rejouées | 7 (n° 19-24, 26), dont 2 trous de sécurité trouvés **avant** tout client | — |
| Répétition temps 2 (chaîne réelle : champs, libellés ; corpus 2 commencé) | 16 (7 apprentissage + 9 corpus) | 14 (n° 29-39, 42-44) | 0,88 |
| Étape 6 : corpus complet lu par la session Claude (Opus), 13-16 oct | 32 (33 briefs, 1 hors) | 6 (n° 52-57 : 3 usine, 3 juge) | 0,19 |

Le temps 2 (champs) et les formulaires toucheront des parties neuves : de nouveaux défauts y sont
attendus ; ils doivent rester généraux, puis décroître.

---

## 8. Questions ouvertes

- ~~Où vit le nouveau code~~ → tranché le 7 oct : `usine/` (§6). Le calculateur
  (`agents/capability_matrix.py`) est utilisé en place et ne déménagera qu'au retrait de l'ancienne usine.
- ~~**Positionnement commercial**~~ → tranché le 16 oct : phase 1 **accompagnée** (le client vient, présentiel ou
  visio ; miroir lu à deux), puis validation à distance, puis libre-service = SaaS (but final). Reste ouvert : le prix.
- **Place de l'IA générative** (discussion du 17 oct — hypothèses ; **place A prouvée et adoptée le 18 oct**, B et C à essayer). Règle proposée : l'IA va
  là où son erreur est **visible et corrigeable avant de nuire** ; le code prouvé garde ce qui ne doit jamais casser
  (droits, porte, verdict des juges, argent). Quatre places candidates : (A) critique de la compréhension ;
  (B) design propre à chaque app dans un cadre de thème vérifié ; (C) extensions sur mesure (documents, calculs,
  notifications) écrites par des agents dans des emplacements isolés, avec leurs tests, relues par le concepteur ;
  (D) utilisateur simulé qui signale ce qui coince. Argument fort : le hors stock mesuré (documents 21/32, calculs 18,
  notifications 14…) ne sera jamais couvert à la main seulement. Argument contre : l'ancienne usine (agents qui
  écrivaient le code) n'a jamais compilé un vrai brief. **À trancher par trois essais à critères écrits d'avance** :
  A sur les 33 lectures du corpus (repère le paramédical sans noyer de fausses alertes) ; B sur 5 apps (jugé par
  l'utilisateur) ; C avec un rapport PDF sur 3 briefs sans retouche. Ordre proposé : A, puis N1.4b-c, puis B et C.
- **Diversité des apps** (17 oct, hypothèse) : les axes d'intention (§1) forment une grammaire — peu de pièces,
  beaucoup d'apps ; la cible = toute app de **données, de rôles et d'étapes**, quel que soit le secteur, avec un
  visage propre ; hors cible : les apps dont la valeur est un algorithme ou une interaction uniques (le terrain de
  Lovable, Bolt). Fait qui la rend possible : les droits sont vérifiés à l'accès aux données (règles ZenStack), du
  code produit par l'IA sur les bords ne peut donc pas faire fuir de données.
- **Sécurité au-delà des droits** : les juges prouvent les droits (la 1ʳᵉ famille de failles OWASP), pas la
  connexion (N1.5), les injections et le XSS (protégés par construction, non vérifiés), les failles des
  bibliothèques, les en-têtes, les abus, les sauvegardes. Proposé : un examen de sécurité avant les premiers
  clients (N1.7) — `npm audit`, scan OWASP ZAP de chaque app, en-têtes.
- **Bibliothèques partagées entre apps** : chaque app copie les mêmes 0,6 Go figés et les installe en ~3,5 min ;
  les installer une fois et les partager (fiche à faire).
- **Livraison** : hébergement par client, évolution de sa base de données sans perte (migrations),
  sauvegardes.
- **Clerk** : réévaluation avant le premier client (RGPD, prix) ; sortie possible : Better Auth.
- **Partage fiche par fiche** (cabinet médical) : demandé tôt par les vrais briefs ; niveau 4 ou avant ?
- **Variance de gpt-5.5** : mesurée à l'examen.
- ~~Critères de fin du niveau 1~~ → validés le 7 oct (§6).
- **Originalité visuelle** : hors périmètre actuel (30 sept) — **rouverte le 17 oct** (place B ci-dessus). Leçon à
  garder : en juin, l'agent frontend dérivait ; l'IA ne choisirait que DANS un cadre de thème vérifié.

---

## 9. Journal des décisions

| Date | Décision | Pourquoi |
|---|---|---|
| Juin 2026 | Agent frontend annulé ; design déterministe | l'agent dérivait, le compilateur non |
| 16 juil 2026 | Modèle compilateur assumé ; loi du contenant | run notes-frais : l'IA comprenait, aucune case ne portait l'intention |
| 17 juil 2026 | Source unique des méthodes (`methods_for`) | `getPublished` vivait dans 4 copies divergentes |
| 26 juil 2026 | Rôles = accès privilégié dans le même espace, pas du multi-tenant | simplicité, invariant conservé |
| 1 août 2026 | Anatomie d'une app bien formée = la cible | les apps compilaient mais étaient « sans âme » |
| Août 2026 | Axes d'intention plutôt que types d'apps | les types sont infinis et se mélangent ; les axes sont peu nombreux |
| 30 sept 2026 | **Matrice des capacités** = cœur de l'usine ; pages dérivées ; l'IA ne planifie plus les écrans | lecture du code : ordre et unité de génération sont les causes de la lourdeur et du manque d'âme |
| 30 sept 2026 | Ce document devient la référence unique | 170+ fichiers dispersés et contradictoires |
| 30 sept 2026 | Pas de nouveau « type » ni de correctif isolé avant la phase 5 | éviter d'empiler sur un cœur qui ne s'auto-vérifie pas |
| 30 sept 2026 | Conserver chaque déclaration ; le harnais rejoue des déclarations enregistrées | la déclaration est le produit, et elle était effacée à chaque run |
| 30 sept 2026 | **7 règles de circulation de l'information** (§2) | l'information fuit aux frontières (dictionnaires libres, prose, corrections silencieuses, copies) |
| 30 sept 2026 | Originalité visuelle hors périmètre actuel | le cœur (comportement, âme) passe d'abord |
| 30 sept 2026 | Phase 1 terminée : déclaration conservée, séquence des générateurs extraite (`dev_core`), harnais sur 9 étalons | filet de sécurité avant de toucher au cœur |
| 30 sept 2026 | Phase 2 : RAG, revue L2, QA Jest, recherche web, retry tsc et code vestigial retirés ; config 47 → 18 clés | signal nul ou négatif pour un coût réel ; run 41 % plus rapide, sortie des générateurs identique |
| 1er oct 2026 | Compter les « non couverts » dès maintenant ; test de l'IA en fin de phase 3 ; vrais briefs tout de suite + phase 5 bis « premiers vrais utilisateurs » | le plan mesurait trop tard, figeait un format sans savoir si l'IA peut le remplir, et ne parlait jamais de vrais utilisateurs |
| 1er oct 2026 | Supprimer n'est accordé par défaut à personne ; un enfant n'est public que déclaré public ; seul qui modifie le parent gère ses enfants | le banc a montré des fuites et des droits trop larges avec les règles précédentes |
| 5 oct 2026 | **Nouvelle conception : usine d'assemblage.** 4 petits agents de compréhension → contrôle strict + matrice → miroir validé par le client → assembleur programmé posant des pièces testées → tests par rôle → sur-mesure humain. Périmètre : logiciels de gestion de petites structures, par niveaux (1 Gérer, 2 Prévenir, 3 Montrer, 4 Relier, 5 Encaisser/connecter ; ordre 2-5 provisoire) | 0 vrai brief sur 5 compilait ; la génération de code-texte multipliait les pannes et les garde-fous |
| 5 oct 2026 | Méthode : définir avant d'implémenter ; finir un niveau (livrable testable en vrai) avant le suivant ; fiche validée avant chaque étape ; documentation progressive et critiquée | l'utilisateur ne pouvait plus suivre ni juger ce qui était construit |
| 5 oct 2026 | Preuve de concept médiathèque (ZenStack + Refine + Clerk) réussie : 35/35 règles serveur, 11/11 HTTP, 3/3 tests par rôle ([`etudes/02`](etudes/02-preuve-de-concept.md)) | vérifier que les pièces tiennent avant de bâtir dessus |
| 7 oct 2026 | ZenStack v3 retenu (remplace Prisma à l'exécution) ; Clerk gardé et isolé pour le niveau 1 ; politique de dépendances (§5) | la traduction matrice → règles est mécanique ; Clerk est notre dépendance la plus risquée (service) |
| 7 oct 2026 | Essai 2 ([`etudes/03`](etudes/03-regles-cas-durs.md)) : 5 cas dont 2 vrais briefs, 479/479 vérifications dérivées de la matrice ; traduction matrice → règles mécanique (11 patrons) + 2 règles systématiques (clôture à la création, cohérence des propriétaires) ; 4 trous de vocabulaire à combler avant le niveau 1 | savoir si l'assembleur est faisable avant de le construire |
| 7 oct 2026 | E4 ([`etudes/04`](etudes/04-testeur-prouve.md)) : testeur prouvé par mutation (205/214 erreurs à effet attrapées, 95,8 %) puis **figé v1.0** ; ZenStack peut répondre « refusé » alors que l'écriture a eu lieu → le traducteur n'en dépend jamais ; « connecté » se traduit par la liste des rôles, jamais `auth() != null` | ne pas se fier à des chiffres produits par un outil non prouvé |
| 7 oct 2026 | Feuille de route après les essais : E4 testeur prouvé → E5 compréhension (10 briefs d'apprentissage ; ≥ 7/10 matrices justes = automatiser, < 5/10 = configurateur assisté) → E6 écrans → niveau 1 → examen sur briefs inédits. Remplace les phases 4-6 | traiter le risque n°1 (comprendre le brief) avant les maillons faciles |
| 7 oct 2026 | E5 partie 1 ([`etudes/05`](etudes/05-comprehension.md)) : agents de compréhension sur 10 vrais briefs, grille écrite d'avance ; gpt-4o-mini 3/10, gpt-5.4-mini 6/10, gpt-5.5 4/6 (crédits OpenAI épuisés) → zone intermédiaire ; 5 causes génériques (dont la nature « registre » manquante, seule cause de fuite) ; pas de cul-de-sac | mesurer le risque n°1 avant de construire |
| 7 oct 2026 | **Nature « registre » ajoutée au calculateur** (`agents/capability_matrix.py`, première modification de l'usine depuis la nouvelle conception) : fiches tenues par l'équipe, visibles de ceux qui les tiennent seulement ; circuit d'états permis sur un registre. Banc 14/14 (le SAV réel passe de 4 écarts à 0) | seule cause de fuite en E5 (dossiers médicaux visibles de tous) ; comble aussi le trou « fiche d'équipe » de l'E2 |
| 7 oct 2026 | Essais IA : l'offre gratuite de Gemini est insuffisante (Pro : 0 appel/jour ; Flash : 20/jour/modèle) ; versions payantes obligatoires pour les vrais clients (sinon les données peuvent servir à Google) | une mesure demande 60 à 80 appels |
| 7 oct 2026 | E5 bis : gpt-5.5 + corrections v2 = **9/10** (1 passage) ; gpt-5.4-mini 6/10 et instable ; coût réel 0,195 $/brief (gpt-5.5) et 0,014 $/brief (mini) | seuil « automatiser » atteint mais stabilité non mesurée |
| 7 oct 2026 | E5 fin (v3) : prudence sur les accès restreints, droits du visiteur limités aux fiches publiques, question du miroir sur les registres vus en entier (calculateur) ; gpt-5.5 juste sur les 3 cas fragiles ; **gpt-5.5 retenu pour la compréhension** ; compréhension close jusqu'au niveau 1 | dernier défaut grave (confidentialité) corrigé ; le chemin critique est l'assembleur |
| 7 oct 2026 | Plan A / plan B : l'IA est un accélérateur (elle retire le temps humain de la compréhension) ; la valeur est l'assembleur ; le plan B « concierge » peut servir les premiers clients | analyse demandée par l'utilisateur : « quel est l'apport de l'IA ? » |
| 7 oct 2026 | E6 ([`etudes/06`](etudes/06-ecrans.md)) : **Refine écarté, nos pièces sur les fonctions générées par ZenStack retenues** — mêmes tests par rôle (3/3 chacun), 27 % de plomberie en moins, pas d'adaptateur, typage déduit de la requête (attrape les oublis). Architecture des pièces : notice typée / affichage partagé / plomberie | même résultat avec moins de code et de dépendances, et plus de sécurité de type |
| 7 oct 2026 | **Doctrine** (validée par l'utilisateur) : le responsable de l'app (bootstrap) voit en lecture tous les registres de l'équipe ; le client peut le refuser dans le miroir. Banc 14/14 | dans une petite structure, le patron répond de tout ; sans ça, l'IA pouvait le priver de ses propres chantiers |
| 7 oct 2026 | Pas de nouveau passage des 7 briefs déjà justes : les crédits sont gardés pour l'examen sur briefs inédits | peu d'information à apprendre sur des briefs connus |
| 7 oct 2026 | **Règle de budget IA** : le coût estimé figure dans chaque fiche ; aucun lancement au-delà de 0,20 $ sans accord ; itérations sur le modèle économique et sur 2-3 briefs ; le modèle cher seulement pour les mesures finales ; dépenses étalées dans le temps | l'utilisateur a vu un tiers de sa recharge partir en un jour |
| 7 oct 2026 | Lot d'apprentissage = les 10 briefs choisis par l'utilisateur (textes originaux) ; lot d'examen = 10 autres briefs (liens seulement, `harness/briefs_reels/examen/`), non ouverts jusqu'à l'examen | un examen sur des textes jamais vus |
| 7 oct 2026 | Briefs réels en deux lots : un lot connu pour apprendre, un lot **caché** jusqu'à l'examen final du niveau 1, avec quelques briefs hors périmètre exprès | éviter d'ajuster l'usine aux briefs qu'on connaît (surapprentissage) ; vérifier que le miroir sait dire « je ne sais pas faire » |
| 7 oct 2026 | Niveau 1 : dossier neuf `usine/`, commande simple sans Temporal au départ, **N1.0 « squelette qui marche » en premier**, critères de fin validés ; une app = squelette fixe + fichiers de données produits + `sur-mesure/` ; journal de fabrication visible | éviter l'intégration tardive ; séparer le besoin de voir l'usine travailler (valable) de l'outil Temporal (fait pour la robustesse) |
| 7 oct 2026 | **USINE.md réécrit pour la nouvelle conception** (chaîne, doctrines, outils, plan du niveau 1) ; l'ancienne trajectoire archivée intacte | le document décrivait encore l'ancienne usine |
| 7 oct 2026 | **N1.0 fait** : `python -m usine fabriquer <description>` produit en ~4 min une app qui tourne et se vérifie seule (104/104 règles, 6/6 écrans), 0 $ d'IA ; chaque app embarque ses juges, qui lisent sa propre matrice | intégrer tous les maillons dès le début, en version minimale, plutôt qu'à la fin |
| 7 oct 2026 | **Un juge tire ses attentes de la source** (la matrice), jamais du fichier qu'il juge ; les données de test contiennent au moins une fiche reliée à rien | tests d'écran 1/4 → 4/4 erreurs attrapées ; trou des données trouvé par mutation |
| 7 oct 2026 | **Squelette : une action qui change l'état est un formulaire (POST), jamais un lien** | Next précharge les liens visibles : la connexion simulée en lien mettait 42 pages sur 50 au mauvais rôle (trouvé par les tests d'écran ; aucune donnée exposée, le serveur jugeait chaque requête sur son cookie) |
| 8 oct 2026 | Fiche N1.1 validée ; « agents de compréhension » renommés **lecteurs IA** ; démonstration visuelle du robot d'écran ajoutée à N1.6 | les lecteurs n'ont ni outil ni action : le mot « agent » trompait ; le robot qui clique seul est une démonstration client parlante |
| 8 oct 2026 | **Plafond de dépense inscrit dans le code** de chaque lancement d'IA (0,20 $ par défaut) | la règle de budget ne doit pas dépendre de la vigilance de l'assistant |
| 8 oct 2026 | Une **app d'essai de tous les types** (`usine/exemples/types.json`) est fabriquée et vérifiée comme une vraie app | elle a trouvé 3 défauts que la médiathèque cachait (champ facultatif vide, date de création modifiable, fuseau horaire) |
| 8 oct 2026 | Chaque app fabriquée tourne en **UTC** (`TZ=UTC`) ; une date pure s'affiche en UTC, une date et heure à l'heure de la personne | serveur à l'heure locale + base en UTC : une date relue se décalait de 4 h et bloquait toute modification |
| 8 oct 2026 | **Testeur v1.2 figé** (tous les types, champs facultatifs vides et remplis, date de création), re-prouvé par mutation sur 2 apps (85-86 %) | le juge doit couvrir chaque type qu'on ajoute, sinon il est aveugle là précisément |
| 8 oct 2026 | Pas de réglage des lecteurs sur gpt-5.4-mini au-delà de 2 essais | ses réponses changent d'un passage à l'autre : régler la consigne sur lui, c'est poursuivre son bruit |
| 8 oct 2026 | **Premier « brief → app » sans rien écrire à la main** (médiathèque, gpt-5.5, 0,46 $) : 132/132 règles, 7/7 écrans | la chaîne entière tient ; elle a aussi révélé un défaut que rien ne refusait (états cités par leur libellé) |
| 8 oct 2026 | Lecteur 6 sur gpt-5.5 : 15/16 informations attendues, 0 type faux ; **gpt-5.5 pour tous les lecteurs** ; N1.1 terminée (0,81 $ au total) | gpt-5.4-mini trop instable (autocars 0-1/5) |
| 8 oct 2026 | **Architecture en blocs validée** (avant N1.3) : aucun mot de vocabulaire n'entre dans l'usine sans son bloc complet — construire, écran, juger, prouver | le testeur grossissait de l'intérieur à chaque type ajouté : discipline saine, structure qui ne passerait pas aux niveaux 2-5 |
| 8 oct 2026 | **N1.1b fait : l'usine est rangée en blocs** (catalogue de 32 blocs, contrôle d'architecture qui lit le vocabulaire dans le code et empêche de fabriquer s'il manque un bloc, carte visuelle) ; la publication est désormais refusée franchement (trouvé par l'inventaire : la règle citait un champ jamais créé) | une architecture qu'on peut étendre sans fragiliser ce qui existe, et qu'on peut voir |
| 8 oct 2026 | **Répétition générale avant l'examen** : l'examen n'a lieu que si le lot d'apprentissage passe toute la chaîne (≥ 6/7) | les briefs d'examen ne servent qu'une fois ; l'examen coûte ≈ 3,40 $ |
| 8 oct 2026 | Le calculateur refuse tout état absent du circuit ; la matrice de référence « coworking » corrigée (elle encodait une étape sur un enfant sans circuit, inexprimable) ; banc 14/14 | règle 3 : refuser, jamais deviner — l'ancien calculateur acceptait en silence |
| 9 oct 2026 | **Répétition, temps 1** : 7/7 briefs du périmètre fabriqués et jugés, 3/3 hors périmètre reconnus ; registre prouvé (union sportive : 188/188, sabotages à effet 70/70) ; **constat principal : les apps sont sûres mais pas utilisables (13/39 fiches créables à l'écran, modification seulement du profil)** ; hors stock le plus fréquent : planning, documents, automatisation (5/7 briefs chacun), calculs (4/7) | mesurer sur des briefs réels avant de choisir la suite |
| 9 oct 2026 | Solde réel des crédits IA : celui du tableau de bord de l'utilisateur (6,29 au 9 oct) ; mes calculs surestimaient | prix relevés sur des sites tiers |
| 9 oct 2026 | **Règle 11 : corriger une classe, jamais un cas** ; registre des corrections et suivi de la convergence (§7) | l'utilisateur craignait le retour du réajustement brief par brief de l'ancienne usine |
| 9 oct 2026 | **N1.2 faite : les apps deviennent utilisables** (39/39 fiches créables à l'écran, modifier, supprimer avec intégrité) ; doctrines « clôture à la modification » et « intégrité » ; 10 corrections (n° 19-28), dont 2 trous de sécurité | la répétition avait montré des apps sûres mais inutilisables |
| 9 oct 2026 | **Budget révisé par l'utilisateur** : le coût n'est pas un frein à l'apprentissage ; preuves complètes seulement en fin d'étape | trop de temps passé en vérifications, pas assez en expansion |
| 9 oct 2026 | Méthode : la **couverture** se mesure sur un large corpus de briefs (répétitions, jugement visuel de l'utilisateur) ; la **valeur** (utilité, envie de payer) seulement par quelques vraies personnes, comme boussole ; l'ordre des niveaux se décide sur les fréquences mesurées | discussion de méthode avec l'utilisateur |
| 9 oct 2026 | **L'utilisateur essaie chaque app à la main** et rend des retours d'utilisateur (au lieu de captures d'écran) : guide `usine/ESSAIS.md`, liste `a-tester.md` par répétition, deux personnes par rôle sur l'accueil (pour vérifier la séparation), `demarrer --depart` | un vrai usage dit plus qu'une image |
| 12 oct 2026 | **Pause et plan de convergence** (l'utilisateur constate qu'on ne converge pas) : gel des nouveaux blocs ; finir la correction en cours ; **test de stabilité** (16 apps + 3 exemples refabriqués deux fois sans changer le code : 0 défaut nouveau attendu) ; recherche à la racine de la famille « une décision à deux endroits » (n° 35, enfants) ; essais à la main par l'utilisateur ; puis seulement le corpus | les défauts par app ne baissaient plus : on ajoutait du neuf pendant qu'on mesurait l'ancien |
| 12 oct 2026 | **Les lectures de développement passent à une session Claude (Opus 5.5) isolée** au lieu de gpt-5.5 (crédit épuisé) : dossier vide hors du projet, « boîte aux lettres » (l'usine écrit exactement ce que gpt recevait, mêmes contrôles), lectures étiquetées ; **d'abord mesurée sur les 19 briefs déjà lus par gpt** (0 $) ; le miroir (N1.4) reste ce qui rend la compréhension juste dans le produit ; le produit aura une IA par API (fournisseur à choisir sur mesure) ; chaque réglage touchant l'IA dira au registre s'il « serait encore juste avec une IA parfaite » | l'usine ne dépend d'aucune IA ; seule compte une IA forte, mesurée |
| 19 oct 2026 | **N1.4b fait : les réponses par clics** (`usine/miroir/reponses.py`, `python -m usine.miroir repondre <lecture> id=valeur …`) : chaque réponse = une opération écrite d'avance (garder un champ proposé, renommer, « non » à une question de droit, visiteur, « il doit voir TOUS les … », accepter la proposition) ; description à jour = lecture + `reponses.json` (la lecture ne change jamais) ; effet vérifié sur ce qui sera construit, sinon rien n'est appliqué et la raison est dite ; « ce qui a changé » ; règle validée : une réponse EXPLICITE du client peut donner un droit (notée qui/quand). Les questions sont essayées d'avance : une question sans vrai choix devient un fait expliqué (69 « registre vu en entier » sur 119 n'avaient pas de « non » possible). Les fonctions des questions du calculateur deviennent structurées (`questions_detail`), le client simulé passe par le même ajout de champ. **Preuve** (`python -m usine.miroir.preuve_reponses`) : 67 lectures, 1 700+ réponses rejouées une à une — jamais en silence, effet voulu et rien d'autre (seuls les droits de l'acteur visé changent), miroir toujours complet, « garder tout » = client simulé 67/67 ; 0 défaut. La preuve a attrapé 5 défauts de mon code avant usage (dont « non » au visiteur qui retirait aussi la vue d'autres rôles) | contenu juste et réponses sûres avant la porte (N1.4c) et la page (N1.4d) |
| 18 oct 2026 | **Place A ADOPTÉE : le critique IA** — vérification indépendante des 10 signalements tirés au hasard (une nouvelle conversation claude.ai, consignes neutres, fichier `runs/essai-critique/a-juger-par-claude.md`) : **9/10 justes** (exigé 7) ; le seul désaccord (n° 10, clôtures : « exagéré, seul le planning manque ») était classé juste par moi → mon classement 63/64 était indulgent, justesse estimée ≈ 90 %. Limite : le juge est aussi un Claude (second avis, pas une vérification humaine). Suite : le critique entre dans la compréhension, ses signalements au volet concepteur du miroir ; d'abord corriger les variantes proposées au client | les 4 critères écrits d'avance sont tenus |
| 18 oct 2026 | **Essai A (critique IA de la compréhension), résultats** — session Claude isolée (Opus, 0 $), 32 lectures du corpus, critères écrits d'avance : (1) paramédical signalé « cœur non construit », bloquant : **oui** ; (2) briefs limite : **3/3** ; (4) bruit : **2,3 signalements par brief** (≤ 3) ; (3) justesse des 64 bloquants ou importants : **63/64 selon mon classement** (1 faux : « utilisable par un novice », non actionnable), 4 affirmations graves vérifiées dans les miroirs, **10 à vérifier par l'utilisateur** (n° 1, 9, 10, 16, 41, 42, 46, 48, 60, 64 de `runs/essai-critique/a-classer.md`). **Découverte majeure** : la plupart des contradictions graves viennent des VARIANTES que le miroir propose « à la place » (N1.4a) — retirer « saisie pour autrui » fait saisir le propriétaire lui-même (l'étudiant crée ses notes et diplômes, l'employé ses soldes de congés), retirer « voir les siennes » rend la direction aveugle : une variante peut DONNER des droits que le brief refuse → à corriger avant de montrer le miroir à un client. Défauts du miroir vus au passage : raisons de refus montrées brutes (codes, messages techniques), « affichées dans les  qu'il consulte » (libellé vide) | adoption de la place A en attente de la vérification de l'utilisateur |
| 17 oct 2026 | **Disque libéré ; partie Docker de l'ancienne factory retirée** (accord de l'utilisateur) : disque à 11,8 Go libres → tri de `runs/` (27 apps périmées supprimées ; bibliothèques des 42 apps gardées retirées, réinstallables), cache npm vidé (+38 Go) ; Docker : cache de construction, images inutilisées, conteneurs et volumes de l'ancienne factory (worker, Temporal, n8n, Qdrant, Ollama, Elasticsearch, apps générées 18,7 Go) retirés — reste `temporal-postgresql` (bases de l'usine). Sauvegardes : `archives/docker-ancienne-factory/` (n8n, Qdrant, journal). Le code de `factory-sprint0/` reste : l'usine y lit encore le calculateur | 11,8 Go libres bloquaient le travail ; l'ancienne factory n'est plus utilisée |
| 16 oct 2026 | **Corpus clos (étape 6)** : 33/33 briefs lus par la session Claude (Opus ; essai Sonnet rejeté : 3 besoins hors stock, 1 droit, ~30 % des propositions perdus) ; périmètre juste 32/33 (paramédical lu « dans », attendu hors) ; 27/32 apps fabriquées et jugées au moment des lots, les 5 échecs corrigés depuis (n° 51-56) ; rejeu des écrans avec les juges actuels : 31/31 vertes ; 6 défauts nouveaux (n° 52-57), 0,19 par app ; blocs manquants mesurés : saisie pour autrui 8/32, « celles qui le désignent » 4, invitations 4, lien de profil 2 ; 45 % des champs « nécessaires » | la convergence décroît ; la compréhension et le hors stock remontent au miroir |
| 16 oct 2026 | **Modèle accompagné (phase 1)**, validé par l'utilisateur : le client vient (présentiel ou visio) chez le concepteur ; le brief = SES mots (l'aide du concepteur passe par des compléments tracés) ; le client tient la souris sur le miroir, le concepteur explique ; volet « concepteur » ; journal des interventions humaines par app (doit décroître → critère des phases 2 puis 3, le libre-service). But final inchangé : SaaS commercialisable | apprendre au contact des clients sans masquer les faiblesses de l'usine ; N1.4 devient une page locale, sans comptes |
| 16 oct 2026 | **N1.4a fait : miroir calculé** (`usine/miroir/`) : phrases par rôle regroupées (droits simples identiques → une phrase ; états, circuits, affichage indirect → la leur), circuits en phrases, champs avec leur origine (cité / choisi par nous / proposé à cocher) et leurs liens, questions de droits une par une et noms regroupés en UNE, hors stock en vos mots, refus + variante proposée (logique partagée avec la répétition : `usine/variante.py`), volet concepteur (pourquoi, citations, codes) ; `miroir.json` + `miroir.md`. **Couverture prouvée par programme sur 73 lectures** (chaque case active avec exactement ses droits, chaque champ, proposition, besoin hors stock, refus). Paramédical : le cœur du besoin apparaît en entier dans « pas encore dans notre stock ». Non fait (pas de lien sûr) : signaler sur une fiche le besoin hors stock qui la concerne | contenu juste avant les réponses (N1.4b), la porte (c), la page (d) |
| 13 oct 2026 | **Plan de convergence, étapes 1 à 4 faites** : stabilité prouvée (mêmes verdicts au chiffre près sur deux passages, puis après l'étape 3 : 15/16 apps + 3 exemples ; support-interventions = échec connu, relecture IA en attente) ; étape 3 (n° 48) sans aucun changement des règles produites (photo avant/après) ; essai à la main de l'utilisateur (n° 47 trouvé). Incidents d'environnement, pas de l'usine : Docker arrêté après redémarrage, coupure internet, mise en veille du PC (le script de test l'empêche désormais tant qu'il tourne). Nettoyage de `runs/` (accord de l'utilisateur) : 218 anciennes apps et 173 bases supprimées, 19 → 40 Go libres ; gardés : compréhensions, résumés, dernière app de chaque brief | prouver la convergence par un chiffre |
| 13 oct 2026 | **Session Claude qualifiée** : l'utilisateur a lu les miroirs côte à côte (critère 5) et décide de continuer avec elle ; le corpus (étape 6) sera lu par la session isolée, par lots, en tenant compte des limites du forfait | les 5 critères écrits d'avance sont remplis |
| 13 oct 2026 | **Mesure de la session Claude isolée sur les 19 briefs connus (étape 5), face aux critères écrits d'avance** : périmètre juste **18/19** (exigé ≥ 18 ; l'erreur : transport-mobile, cas limite, lu « dans » contre la grille « hors ») ; apps jugées bonnes **15/16** (exigé ≥ 15, score de gpt ; la 16e, portes, passe 52/52 après correction du juge n° 51) ; rôles identiques 14/16 ; fiches : souvent mêmes notions sous d'autres noms (comparaison des noms trop grossière : à confirmer par la lecture des miroirs) ; **variation nulle** sur 3 briefs relus (même périmètre, mêmes rôles, mêmes fiches) ; propositions de champs bien plus nombreuses que gpt ; 0 $, mais une limite du forfait atteinte une fois. Défauts de l'usine trouvés pendant la mesure : n° 49, 50, 51 ; une erreur propre à Claude (une ligne qui désigne aussi son parent) désormais attrapée par un contrôle. Reste le critère 5 : lecture de 2-3 miroirs côte à côte par l'utilisateur | prouver avant de confier le corpus |
| 13 oct 2026 | **Boîte aux lettres construite** (étape 5) : modèle `boite` (`usine/comprendre/ia.py` : ClientBoite imite le client OpenAI ; questions dans `C:\Users\BAMBARA Arthur\lecteur-isole\boite\demandes`, réponses dans `…\reponses`, signal `FIN` en fin de lot) ; dossier isolé avec consignes (`DEMARRAGE.md`), script d'attente, réglages qui interdisent de lire le Bureau et internet ; lectures nommées `…-claude-comprendre` ; le lot d'examen est refusé avant lecture ; essai sans session (répondeur automatique) : refus → nouvelle question avec l'erreur → acceptée | remplacer gpt pour le développement |
| 12 oct 2026 | **Garde-fous de la session Claude isolée** (validés) : (1) chaque question est lue par un agent NEUF, sans mémoire des briefs précédents (comme un appel à gpt) ; (2) message de départ qui interdit de lire hors du dossier, et vérification qu'aucune mémoire globale n'apporte d'information sur le projet ; (3) 3 briefs lus deux fois pour mesurer la variation normale ; (4) critères écrits AVANT : périmètre ≥ 18/19, apps jugées bonnes ≥ 15/16 (gpt), mêmes rôles et fiches principales sur la grande majorité, avis de l'utilisateur sur 2-3 miroirs côte à côte ; (5) la boîte aux lettres refuse tout brief du lot d'examen (dans le code) ; (6) lots de 3 à 5 briefs, reprise sans perte si le forfait s'épuise. **Règle de classement** : une app fausse est d'abord classée — défaut de construction (on corrige l'usine) ou erreur de compréhension (« à rattraper par le miroir », avec la question que le miroir aurait dû poser ; la consigne ne change que si la règle serait encore juste avec une IA parfaite) | penser à tout avant de commencer |
| 10 oct 2026 | **Signal d'alarme N1.3, premier bloc** : « enfant » a d'abord touché 3 modules du juge appartenant à d'autres blocs (supprimer, menu, circuit) pour leur apprendre à ignorer les lignes → restructuré aussitôt : la notion de ligne vit dans les deux NOYAUX du juge (règles : `foreignKeys` ne compte que les désignations ; écrans : `fiches` / `toutes` / `fichesDeLaMatrice`) ; verdicts identiques avant/après (262/262, 16/16). Reste touché : circuit (les boutons d'une ligne de tableau ne comptent pas comme homonymes — règle générale) | appliquer la règle fixée dans la fiche |
| 10 oct 2026 | **Fiche N1.3 validée** (les 3 blocs de vocabulaire manquants : fiches enfants, profil relié, « celles qui le désignent » ; préalable : découper les tests d'écran en modules ; critère : 16/16 apps complètes ; signal d'alarme : fichiers existants touchés par bloc). **Doctrines tranchées par l'utilisateur** : (1) supprimer un parent supprime ses lignes enfants — seule exception à « jamais de cascade » ; (2) les lignes ne se modifient que lorsque le parent est lui-même modifiable dans son état | recommandations acceptées |
| 10 oct 2026 | **Répétition temps 2 terminée** (crédit épuisé au brief 10 du corpus) : 15/16 apps jugées par les juges actuels, 19/19 périmètres justes, 15 corrections (n° 29-43) dont 1 fuite entre clients évitée avant fabrication (n° 35) ; mesure des besoins réels (fiches enfants 6/16 ; calculs 11/16, documents 10/16, planning 9/16) ; règle 12 « avant, pendant, après » ; tableau de bord en ligne | décider la suite sur des fréquences mesurées |
| 9 oct 2026 | **Client simulé** pour les apps d'essai : elles prennent les champs proposés par l'IA (origine « proposition », facultatifs), comme si le client les acceptait au miroir (N1.4) ; étiqueté dans `a-tester.md` ; la mesure de compréhension reste faite sans | les vrais briefs décrivent surtout le hors stock : sans les propositions, les fiches n'ont qu'un « Intitulé » et l'essai à la main ne dirait rien |
| 9 oct 2026 | **Corpus 2** : 33 vrais briefs Codeur.com (`usine/corpus/`), règle de choix et périmètre attendu écrits **avant** tout lancement ; lot d'examen écarté par un programme qui compare les numéros (2 candidates écartées). Transparence : le moteur de recherche avait affiché le titre et une phrase de résumé de ces 2 briefs avant le filtre — rien d'autre n'a été lu ; l'usine ne sera pas réglée sur ces thèmes à partir de ces résumés | élargir la mesure de couverture (décision du 9 oct) |

---

## 10. Carte des documents

| Fichier | Statut |
|---|---|
| [`etudes/01`](etudes/01-pieces-niveau-1.md) à [`etudes/06`](etudes/06-ecrans.md) | **Valides** : les preuves de ce document (pièces, PoC, règles, testeur, compréhension, écrans) |
| `usine/` | **La nouvelle usine** (niveau 1) : `comprendre/` (les 7 lecteurs IA, `python -m usine comprendre …`), `description.py` (forme stricte), `matrice.py` (le calculateur, en place), `traduire/` (traducteurs), `modele-app/` (squelette fixe + juges livrés : `verification/noyau.mts` + `verification/blocs/`), `assembler.py` (`python -m usine fabriquer …`), `blocs/` (**catalogue des blocs**, contrôle d'architecture, carte : `python -m usine carte`), `preuve_regles.mts` et `preuve_ecrans.py` (preuves des juges par sabotage), `mesures/` (grilles écrites d'avance), `exemples/`, `repetition.py` (`python -m usine.repetition --chaine-reelle [--corpus usine/corpus]`), `corpus/` (**corpus 2**, 33 vrais briefs + règle de choix + périmètre attendu), `ESSAIS.md` (**guide d'essai à la main** et fiche de retour), `outils/` (**outils de travail** : lots de la session Claude isolée, refabrication, comparaisons, photo avant/après, nettoyage — voir `outils/LISEZMOI.md`) |
| `runs/` | **Jetable** (hors git) : une fabrication par dossier, avec ses fiches, son journal et ses traces |
| [`archives/USINE_trajectoire_avant_assemblage_2026-10-07.md`](archives/USINE_trajectoire_avant_assemblage_2026-10-07.md) | **Historique** : l'ancienne version de ce document (phases 0-6, 9 axes, dimensions, ancienne usine) |
| `anatomie_app.md` | **Valide** comme portrait d'une app bien formée (natures, affordance honnête, tableau de bord par acteur) |
| `contrat_correction.md` | **Partiellement valide** : ses invariants deviennent des tests par rôle |
| `lecture_usine/` | **Historique** : le détail du code de l'ancienne usine |
| `poc/` (`mediatheque` supprimé, `regles`, `comprehension`, `ecrans`) | **Jetable** : les essais ; leurs conclusions sont dans `etudes/` |
| `factory-sprint0/harness/matrices/` | **Valide** : le banc des matrices (14) |
| `factory-sprint0/harness/briefs_reels/` | **Valide** : 5 premiers vrais briefs, lot d'**apprentissage** (10), lot d'**examen** (10, à ne pas ouvrir) |
| `factory-sprint0/` (pipeline, générateurs, executor) | **Ancienne usine**, à retirer progressivement (§8) ; seul `agents/capability_matrix.py` est au cœur de la nouvelle |
| `Roadmap3.2.0.md`, `architecture.md`, `typeApps.md`, `DETECTEUR_amont_carte_cases.md`, `RECHERCHE_*.md`, `factory_audit.md`, `remodularisation_plan.md`, `session.md` | **Historique** (à archiver lors du nettoyage des vieilles docs) |
| `sorties.md`, `logit.md`, `rapports.md`, `result.md` | Brouillons / journaux machine |

---

## 11. Petit lexique

- **Brief** : la demande du client, en langage courant.
- **Description de l'app (déclaration)** : ce que l'IA a compris, sous forme de données (acteurs,
  fiches, circuits, droits) ; c'est le produit.
- **Acteur** : un type de personne qui se connecte (adhérent, bibliothécaire). **Visiteur** : sans
  compte. **Responsable** : l'acteur qui porte l'app (le patron, l'administrateur). **Intrus** :
  quelqu'un de connecté sans rôle déclaré.
- **Fiche** : une chose enregistrée (un emprunt, un dossier) ; sa **nature** (profil, catalogue,
  registre, collection, enfant) fixe ses droits par défaut.
- **Registre** : fiches tenues par l'équipe, visibles de ceux qui le tiennent seulement.
- **Circuit** : les états d'une fiche et qui fait passer de l'un à l'autre.
- **Matrice des capacités** : pour chaque acteur et chaque fiche, ce qu'il peut voir et faire.
- **Préréglage / exception** : les droits par défaut d'une nature / un écart cité par le brief.
- **Clôture vs désir** : ce qui est impliqué par nécessité / ce qui n'est pas demandé (remonte au miroir).
- **Miroir** : ce que l'app fera, en phrases, plus des questions ciblées ; le client le valide.
- **Hors stock / hors périmètre** : un besoin que l'usine ne sait pas encore faire / un projet qui
  n'est pas un logiciel de gestion.
- **Traducteur** : le programme qui transforme la matrice en règles d'accès.
- **Pièce** : un morceau d'écran générique (liste, fiche, formulaire…). **Notice** : la description
  typée des fiches que lisent les pièces. **Plomberie** : le code qui relie l'écran aux données.
- **Assembleur** : le programme qui pose les pièces et les règles pour produire l'app.
- **Testeur** : le programme qui essaie chaque case de la matrice contre la base. **Test par
  mutation** : on abîme exprès les règles (ou les écrans) pour vérifier que le juge le voit ; une
  erreur « survivante » est soit sans effet, soit un trou du juge. **Témoin** : la même mesure sur
  l'app intacte, qui doit passer.
- **Squelette** : la partie fixe de chaque app (pièces, plomberie, juges), écrite et testée une fois ;
  l'usine n'y ajoute que des fichiers de données.
- **Lot d'apprentissage / d'examen** : briefs qu'on étudie / briefs gardés cachés jusqu'au test final.
- **Plan A / plan B** : l'IA écrit la description / on la remplit avec le client.
- **Fiche d'étape** : le court document validé avant chaque étape (but, démo, fichiers, coût, risque).
