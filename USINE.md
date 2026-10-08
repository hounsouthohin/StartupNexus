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

### Circulation de l'information — 7 règles ✔ validé (30 sept)

Les étapes ne se parlent pas : chacune lit une fiche de forme fixe et en produit une autre.
1. **Un fait = un seul auteur.** 2. **Entre machines, des données, jamais du texte.**
3. **Contrôle strict à chaque frontière** : une réponse invalide est refusée et l'erreur précise est
renvoyée (N essais), jamais « devinée ». 4. **Fiches figées** : aucune étape ne corrige une fiche amont
en silence. 5. **L'IA reçoit le minimum, sous forme de données.** 6. **Les ordres d'exécution viennent
du plan, pas des agents.** 7. **Traçabilité** : chaque fichier sait de quelle case il vient.

Limite assumée : le contrôle bloque une fiche **mal formée**, pas une fiche **fausse** — d'où le
miroir validé par le client (§3.2) et les contrôles croisés entre agents (E5).

---

## 3. La chaîne, maillon par maillon

### 3.1 Comprendre — l'IA écrit la description de l'app  ✔ prouvé · ◐ à compléter

**Comment** (`poc/comprehension/comprendre.py`) : 5 agents, une question chacun, réponses en JSON
contrôlées par programme (forme stricte, identifiants connus, **citations recopiées mot pour mot**),
erreur renvoyée à l'agent (2 essais de plus) :

| Agent | Question | Contrôles par programme |
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

**Pas prouvé / à faire** : stabilité de gpt-5.5 (un seul passage) ; **les champs des fiches** (nom,
type, obligatoire) ne sont pas encore extraits — indispensables aux formulaires (○, niveau 1).

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
| Clôture | on ne pointe que ce qu'on a le droit de voir (`check(lien, 'read')` à la création) | E2 ✔ |
| Cohérence | deux fiches liées du même rôle propriétaire appartiennent à la même personne | E2 ✔ |
| Propriétaire immuable | le propriétaire d'une fiche ne change jamais | E2 ✔ |
| Une étape ne change que l'état | les autres champs restent identiques pendant une transition | E2, E4 ✔ |
| Prudence | un accès que le brief **limite** n'est pas élargi ; le partage fin est signalé hors stock | E5 ✔ |
| Visiteur | un droit sans compte seulement sur une fiche déclarée publique | E5 ✔ |
| Pas de confiance dans le refus de relecture | ZenStack peut répondre « refusé » alors que l'écriture a eu lieu : chaque interdiction est une règle explicite | E4 ✔ |
| Tables de choix | une liste de valeurs (« 478 / 754 ») est une table de données, pas une énumération dans le code | E2 ✔ |

**Pièges techniques connus** : bug ZenStack 3.9.7 (comparer un état à sa valeur d'avant → erreur
SQL ; contournement : nommer l'état) ; Prisma interdit qu'une IA remette une base à zéro (chaque
version de schéma d'essai a sa base neuve) ; Next.js 16.4 exige que la lecture de session soit derrière
un `<Suspense>`.

**Trous de vocabulaire restants** (○) : un **enfant** avec circuit d'états ; plusieurs rôles qui créent
« pour leur compte » ; l'administrateur qui **modifie** tout (la doctrine ne lui donne que la lecture) ;
« ses » clients / « son » agence (niveau 4).

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
| N1.1 Description complète | ajouter à la compréhension les **champs** des fiches (12 types, obligatoires, tables de choix) ; combler les trous de vocabulaire utiles au niveau 1 | ○ |
| N1.2 Miroir v1 | porte de validation ; interface de réponse aux questions ; corrections déterministes | ○ |
| N1.3 Traducteur | matrice → schéma ZenStack (patrons + doctrines), vérifié par le testeur figé | ○ |
| N1.4 Données de test | générateur de données (≥ 2 par sorte…) et des adaptateurs du testeur | ○ |
| N1.5 Catalogue de pièces | notice générée depuis la matrice ; pièces du §3.4 ; connexion Clerk + équipe | ○ |
| N1.6 Assembleur | brief → app, de bout en bout ; tests par rôle (serveur + écrans) produits automatiquement | ○ |
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

**Budget IA** ✔ validé (7 oct) : coût estimé dans chaque fiche ; aucun lancement au-delà de 0,20 $
sans accord ; itérations sur le modèle économique et sur 2-3 briefs ; le modèle cher pour les mesures
finales ; dépenses étalées dans le temps.

**En continu** : les besoins « hors stock » relevés sur chaque brief sont comptés pour fixer l'ordre
des niveaux 2 à 5 (`scripts/non_couverts.py`, à brancher sur la nouvelle compréhension).

---

## 7. Les juges

| Juge | Ce qu'il juge | Statut |
|---|---|---|
| Contrôles stricts aux frontières | la forme de chaque réponse de l'IA | ✔ (E5) |
| Banc des matrices | le calculateur contre 14 matrices attendues | ✔ 14/14 |
| Testeur par rôle (serveur) | les règles d'accès, case par case, sur l'état de la base | ✔ prouvé par mutation (E4) ; v1.1 livré dans chaque app, re-prouvé (N1.0 : 33/39 à effet) |
| Compilateur (TypeScript) | la cohérence notice / schéma / code | ✔ (E6) |
| Tests Playwright par rôle | ce que chaque rôle voit et peut faire à l'écran | ✔ livrés dans chaque app, attentes tirées de la matrice, prouvés par mutation 4/4 (N1.0) |
| Miroir validé | l'intention du client | ◐ (phrases et questions ; porte à construire) |
| Grille de référence | la compréhension de l'IA (écrite avant de lancer l'IA) | ✔ (E5) |
| Examen sur briefs cachés | la généralisation | ○ (N1.7) |

---

## 8. Questions ouvertes

- ~~Où vit le nouveau code~~ → tranché le 7 oct : `usine/` (§6). Le calculateur
  (`agents/capability_matrix.py`) est utilisé en place et ne déménagera qu'au retrait de l'ancienne usine.
- **Positionnement commercial** : produit (plan A) ou service « concierge » (plan B) pour les premiers
  clients ; prix.
- **Livraison** : hébergement par client, évolution de sa base de données sans perte (migrations),
  sauvegardes.
- **Clerk** : réévaluation avant le premier client (RGPD, prix) ; sortie possible : Better Auth.
- **Partage fiche par fiche** (cabinet médical) : demandé tôt par les vrais briefs ; niveau 4 ou avant ?
- **Variance de gpt-5.5** : mesurée à l'examen.
- ~~Critères de fin du niveau 1~~ → validés le 7 oct (§6).
- **Originalité visuelle** : hors périmètre actuel (30 sept).

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

---

## 10. Carte des documents

| Fichier | Statut |
|---|---|
| [`etudes/01`](etudes/01-pieces-niveau-1.md) à [`etudes/06`](etudes/06-ecrans.md) | **Valides** : les preuves de ce document (pièces, PoC, règles, testeur, compréhension, écrans) |
| `usine/` | **La nouvelle usine** (niveau 1) : `description.py` (forme stricte), `matrice.py` (le calculateur, en place), `traduire/` (traducteurs), `modele-app/` (squelette fixe + juges livrés), `assembler.py` (`python -m usine fabriquer …`), `preuve_regles.mts` et `preuve_ecrans.py` (preuves des juges par mutation), `exemples/` |
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
