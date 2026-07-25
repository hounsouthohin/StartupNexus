# ROADMAP — SOFTWARE AGENT FACTORY
## Version 4.0 — Mise à jour 16 Juillet 2026
> **v4.0 = RELECTURE TERRAIN.** Les sessions de juillet ont invalidé plusieurs hypothèses
> fondatrices de la v3.9. **Lire la section RELECTURE TERRAIN en premier — elle a priorité
> sur tout le reste du document.** Ce qui suit elle est un plan écrit *avant d'avoir vu* ;
> ce qu'elle contient est vérifié dans le code réel et dans des runs.
>
> **En trois lignes :** la capacité de la factory = **l'ensemble de ses cases** (loi du
> contenant) · le modèle compilateur est assumé jusqu'au bout (architect = parseur, AST =
> unicité, générateurs = émetteur, executor LLM = assembleur inline) · **trois types et zéro
> livraison** → la Scène (4.9C) est promue avant toute nouvelle expansion.
>
## ~~Version 3.9~~ — 6 Juillet 2026
## Historique : v2.0 (23 Fév) · v2.1 (03 Mars) · v2.2 (04 Mars) · v2.3 (28 Mars) · v3.0 (09 Mai) · v3.1 (15 Mai) · v3.2 (24 Mai) · v3.3 (05 Juin) · v3.4 (05 Juin — Consolidation) · v3.5 (05 Juin — Reséquençage Sprint 4.9) · v3.6 (06 Juin — FrontendActivity 3 couches) · v3.7 (06 Juin — FrontendAgent ReAct planifié) · v3.8 (18 Juin — FrontendAgent ANNULÉ ; design intégré dans pipeline déterministe ; Plan6 committé ; Sprint 4.9 reséquencé) · **v3.9 (06 Juil — Priorité EXPANSION : sprints 5-10 reséquencés selon typeApps.md v2.0 (D→I→K→H→G→E→B), règle des 4 lots, D25-D28 réglées, 3/3 BUILD_SUCCESS writer-pad/freelance-tracker/sprint-board, 4.9C reste disponible en parallèle à la demande)**

---

## VISION

**Une startup agentique** : un seul opérateur humain recueille les briefs clients,
les valide et les soumet à la factory. La factory génère, teste et déploie l'application
complète — Next.js 14 + Clerk + Prisma — prête à être consommée par l'utilisateur final.
Aucun développeur. Aucune intervention manuelle entre la commande et le déploiement.

Le moteur repose sur un **modèle compilateur** :
```
Brief (langage naturel)
  → Architect LLM  →  ProjectSpec (IR formel)
  → Générateurs déterministes  →  Squelette garanti
  → Executor LLM (Level B)    →  Logique custom bornée
  → Build + Tests + Reviewer  →  Gate qualité
  → GitHub + Vercel + Neon    →  App déployée, URL livrée
```

La valeur différenciante : les **garanties déterministes** sur la couche données
(services, types, schémas, actions, formulaires, navigation) rendent la factory
structurellement plus fiable que tout outil de génération LLM pur.

~~Chaque run améliore la factory : les erreurs détectées alimentent les standards Qdrant
via le Learner. L'usine apprend de chaque app qu'elle produit.~~
→ **INVALIDÉ 16 Juil 2026** — voir RELECTURE TERRAIN ci-dessous. Le LLM dev n'écrit plus de
code sur les types couverts : des standards « comment bien coder » n'enseignent à personne.

---

## RELECTURE TERRAIN — 16 Juillet 2026 (v4.0)

> **Cette section a priorité sur tout ce qui la suit.** Elle est vérifiée dans le code réel
> et dans des runs, pas planifiée. Les sessions de juillet ont invalidé plusieurs hypothèses
> fondatrices de la v3.9. Une roadmap est un plan écrit avant d'avoir vu — le terrain gagne.

### 0. ÉTAT CONSOLIDÉ — 23 Juillet 2026 (point de référence stable)

> Snapshot validé ensemble. Ni idée neuve, ni ambition : juste où on est.

**Ce qui a été RETIRÉ :**
- *Principes* : PRINCIPE 3 (boucle RAG→Dev→Learner) mort · PRINCIPE 5 (reviewer auto-obsolète) mort ·
  PRINCIPE 6 (prouver utilisable avant type suivant) VIOLÉ.
- *Instruments* : Scorer 4.8D (composite de menteurs) · tests Jest 4.8B (testeraient nos compilateurs) ·
  mission Qdrant du Learner 4.8C (683 événements → 0 standard) · journey_validator (crashe).
- *Code* : LLM Page Enricher · `SERVICE_METHOD_REGISTRY` (dict) · les 3 miroirs de méthodes ·
  1 des 2 générateurs d'actions · `getPublished` (×6) · StatusModule.
- *Gelé* : RAG · *En pause* : github_activity · *Annulé avant nous* : FrontendAgent.

**Ce qui a été AJOUTÉ :** Type I (StatusFlowDeclaration/transitionTo/verrou) · Design Compiler ·
capteur quality_check réparé (C0/C1/C2) · source unique (MethodDecl/methods_for) · miroir Scène-A (unsupported[]).

**Ce que la startup EST maintenant :**
```
ARCHITECT (LLM) ─► DÉCLARATION (JSON=AST) ─► COMPILATEURS ─► EXECUTOR LLM ─► BUILD ─► REVIEW/QA
  comprend+avoue      l'unicité                traduisent      les bords      arbitre technique
```
- Intelligence aux bords, déterminisme au cœur · une seule source de vérité (méthodes) ·
  3 types qui composent (A+D+I) · avoue ses limites (unsupported[]).
- **Moitié GAUCHE (générer) marche (~95 s). Moitié DROITE (preview + deploy) N'EXISTE PAS.**

**Idéaux partagés (7) :** (1) loi du contenant · (2) la déclaration est le produit (corrige 1×→recompile
tout le parc) · (3) une seule marche perd de l'info (brief→déclaration) · (4) machine juge le technique,
humain juge le sens · (5) jamais éditer le code livré, remonter à la déclaration · (6) compile le récurrent,
LLM pour l'unique · (7) la Scène est le seul instrument qui ne peut pas mentir.

**Ouvert (décidé, pas fait) :** preview local (`preview_activity`) · édition de la déclaration (future,
prérequis : stocker le JSON par client) · Type K · Deploy · dettes infra (Temporal, Clerk, D31, amount Float).

---

### 1. LA LOI DU CONTENANT — découverte majeure

> **Toute intention client sans structure pour la porter s'évapore — quelle que soit
> l'intelligence du LLM.**

**Preuve** (run `notes-frais`, 16 Juil). Le brief disait noir sur blanc : *« on ne doit pas
pouvoir rembourser une note qui n'a pas été approuvée »*. L'architect a **parfaitement compris**
(5 états extraits dans le bon ordre depuis une prose qui ne les listait pas, `@default(draft)`,
`rejectionReason` déduit de « refusée avec un motif »). Mais **aucune structure ne pouvait
porter l'ordre ni les sauts interdits** → le savoir est tombé par terre. La phrase du client
est devenue… des couleurs de badge.

Résultat : `BUILD ✅` · `spec_coverage 1.0` · `requirements 6/6` · `quality_violations 0` ·
`review COHERENT 100/100` — sur une app qui laissait **créer une note de frais déjà
« Remboursée »**, jamais soumise ni approuvée.

**Correction** : créer la case (`StatusFlowDeclaration`) → l'architect l'a remplie
**parfaitement, du premier coup, sans un seul réglage de prompt**. Répété **3 fois** le même
jour (`transitions`, `locked_states`, `state_fields`). Il savait depuis le début.

**Conséquence — redéfinition de ce qu'est une expansion :**
```
Expansion d'un type  ≠  enseigner au LLM / ajouter des standards
Expansion d'un type  =  créer les CASES manquantes + les compilateurs qui les lisent
```
> **La capacité de la factory = exactement l'ensemble de ses cases.**
> Pas l'intelligence du LLM (il comprend déjà). Pas le nombre de générateurs (faciles une fois
> la déclaration là). Les types (A/D/I/K/H…) ne sont pas des catégories d'apps — ce sont des
> **paquets de cases**.

### 2. LE MODÈLE COMPILATEUR — assumé jusqu'au bout

La VISION nomme le « modèle compilateur » puis **planifie contre lui**. Assumé :

| Étage | Nature | Rôle réel |
|---|---|---|
| **Architect** | LLM | **le parseur** : français ambigu → déclarations. Seul endroit où l'intelligence est irremplaçable |
| **ProjectSpec / EnrichedSpec** | structure | **l'AST** — c'est lui qui porte l'unicité de chaque app |
| **Générateurs** | déterministe | **l'émetteur de code** : traduction fidèle, zéro créativité |
| **Dev executor LLM** | LLM | **l'assembleur inline** : la queue, la nouveauté, les webhooks, la correction |

**Ce que le modèle explique — et que la v3.9 ne voyait pas :**
- *La prose s'évapore* → l'AST n'a pas de nœud pour elle. Ce n'est pas un problème de prompt.
- *Le reviewer ment* → il inspecte la **sortie d'un compilateur**, correcte par construction.
  Il n'a rien de réel à trouver, alors il fabrique du réconfort (COHERENT 100/100).
- *Le dev executor a écrit **0 fichier*** sur notes-frais (`[executor] plan vide — tout
  pré-généré par templates`). **C'est sain** : un compilateur n'a pas besoin qu'on écrive à la
  main ce qu'il sait émettre. Il doit rester **petit** mais **jamais disparaître** — c'est lui
  qui fait que la factory *répond* à n'importe quel brief au lieu d'échouer.
- *Apps standardisées ?* **Non.** Un compilateur C émet des programmes infiniment différents
  avec le même back-end. **L'unicité vient de l'AST, jamais de l'émetteur.**

**Coût assumé :** chaque compilateur est du code que NOUS maintenons ; le LLM couvre la queue
gratuitement. Frontière = règle des 3 zones : **compiler le récurrent, laisser la queue au LLM.**

### 3. CE QUI MEURT (le terrain a retiré leur sujet)

| Élément | Pourquoi il meurt |
|---|---|
| **PRINCIPE 3** — boucle `RAG → Dev → Reviewer → Learner → RAG` | Le LLM dev n'écrit plus de code → des standards de codage n'enseignent à **personne**. La boucle n'a plus de maillon « Dev ». |
| **PRINCIPE 5** — le reviewer s'auto-rend inutile via les standards | Cassé aux deux bouts : il ne détecte rien de réel (100/100 sur une app absurde), et ses standards n'iraient nulle part. |
| **4.8C** — mission « le Learner enrichit Qdrant » | 683 événements, **0 standard approuvé**. Sans sujet. → **Reconverti**, voir §5. |
| **4.8D** — App Usefulness Scorer `build+flows+quality+spec` | flows = validator **crashé** · spec = **liste de fichiers** · quality = capteur **aveugle**. **Un composite de 4 menteurs est un menteur.** |
| **4.8B** — smoke tests Jest sur l'app livrée | Ils testeraient du code **déterministe** = notre bug, pas celui du LLM. On teste **le compilateur**, pas chaque programme. |
| **~8 standards Qdrant par type** (Lot 2) | Déjà bloqués par la roadmap elle-même (A/B RAG non fait) — et sans objet pour les types compilés. |

### 4. CE QUI EST CONFIRMÉ ET RENFORCÉ

- **PRINCIPE 4** (déterministe pour la forme / agentique pour le sens) → **c'est le moteur**.
  Le LLM décide la machine à états, le compilateur l'écrit.
- **PRINCIPE 7** (extension avant limitation) → type I ouvert **en une journée**.
- **PRINCIPE 8** (la Scène avant le déploiement) → **promu**, voir §6.
- **PRINCIPE 6** (complétion avant complexité) → **VIOLÉ** : *« le Level A doit être prouvé
  utilisable par un vrai utilisateur avant de passer au type suivant »*. **On n'a jamais fait
  tourner une seule app. Jamais cliqué un bouton. Zéro app livrée.** La décision du 6 Juil
  (« priorité EXPANSION avant la Scène ») contredit frontalement ce principe.

### 5. LA CARTE DES INSTRUMENTS — refaite

**Erreur de catégorie de la v3.9 :** on n'inspecte pas la sortie d'un compilateur.
**On teste le compilateur, une fois — pas chaque programme.**

| Ce qui peut réellement casser | Où le voir | État |
|---|---|---|
| Bug de compilateur | test **du compilateur**, une fois (pas par app) | ⚠️ `scripts/test_generators.py` existe mais **RIEN NE LE LANCE** (aucune CI ; dernière modif 20 juin vs `crud.py` 9 juil ; ignore `enriched_spec`). Prérequis = **avoir quelque chose qui lance les tests**, pas écrire des tests. |
| **L'architect déclare faux** | comparer la **déclaration** au brief (sémantique) | ❌ inexistant |
| **Une case manque** | 🔴 **rien ne le voit** — fait à la main le 16 Juil | ❌ → **nouvelle mission du Learner** |
| Le LLM executor code mal | le reviewer — son **seul** territoire légitime | ✅ existe (surdimensionné) |
| **Est-ce que ça marche pour un humain ?** | **la Scène (4.9C)** — seule vérité de bout en bout | ⏳ **PROMU** |

**Nouvelle mission du Learner :** ne plus corriger du code — **détecter les cases manquantes**.
Un learner capable de dire *« l'architect exprime X en prose et ça n'atterrit nulle part »*
ferait **s'étendre la factory toute seule**. C'est l'agentivité qui reste à conquérir. Aujourd'hui
ce détecteur, c'est l'humain — c'est *lui* qu'il faut faire entrer dans la boucle, pas la
correction de TS2339.

### 6. LE TROU STRATÉGIQUE : on fabrique des cases à l'aveugle

**Tous nos briefs sont écrits par nous. Aucun vrai brief client n'a jamais traversé la factory.**
Donc l'ordre `K → H → G → E` est une **supposition**, pas une observation.

C'est le vrai argument pour livrer : pas « tester la chaîne » — **apprendre quelles cases le
réel réclame.** La Scène (4.9C) n'est pas un confort : c'est **le seul instrument qui ne peut
pas mentir** (un robot qui clique « Approuver » et regarde ce qui se passe = vérité terrain),
et elle **remplace** 4.8B + 4.8D au lieu de les compléter.

### 7. VOIE RETRACÉE (remplace le séquencement v3.9)

```
1. FINIR le type I        — transitionTo + boutons détail + passe de cohérence + brief congés
2. LA SCÈNE (4.9C)        — PROMUE de « à la demande » à PROCHAINE (PRINCIPE 6 l'exige)
3. TRANCHER ENSUITE       — déployer (4.9E) ou reprendre l'expansion (K), informés par la Scène
```
Les types A + D + I couvrent déjà l'essentiel des apps métier réelles (CRUD, contenu public,
workflows d'approbation). Les victoires bon marché sont prises ; le type K est un vrai chantier.
**Trois types et zéro livraison** : la prochaine valeur est dans la sortie du tuyau, pas dans sa largeur.

### 8. MÉTHODE ACQUISE — run de référence avant toute expansion

Avant d'ouvrir un type : **1 seul run sur un brief non biaisé jamais vu** → lire **le code réel**
(jamais les métriques) → **le gap observé (pas supposé) définit le contrat**. Les instruments qui
affichent « 100/100 » sur du cassé disent du même coup **ce que le capteur doit apprendre**.
Validé sur notes-frais : mes 5 prédictions étaient justes, mais le run a révélé **ce que je
n'avais pas prédit** (la cause n'était pas « la prose se transmet mal » mais « aucune case
n'existe »). Sans ce run, on renforçait les prompts — un fix inutile sur un diagnostic faux.

### 9. MODÈLE OPÉRATIONNEL — intelligence aux bords, déterminisme au cœur (17 Juil 2026)

> **L'intelligence vit à EXACTEMENT deux endroits : l'ENTRÉE et la CROISSANCE.
> Le milieu est bête et rapide, exprès.**

```
ENTRÉE (intelligent)     : comprendre + déclarer + AVOUER ses limites      ← architect (LLM)
    │
MILIEU (bête et fiable)  : compiler · ~2 min · 0 erreur                    ← générateurs
    │
CROISSANCE (intelligent) : DRAFTER la case suivante depuis unsupported[]   ← proposé, humain-validé
```
Ce qui « apprend » n'apprend **jamais seul** : il **propose**, et l'humain + le build + la Scène
**valident**. Version forte ET sûre de l'« usine vivante ».

### 10. LA SCÈNE — décomposée (le robot n'est PAS la première marche)

Le besoin = « le client voit son app marcher ». Le robot Playwright est la partie **chère et
incertaine** (auth Clerk ~70 %). Or l'erreur naît **en haut** (brief→déclaration), pas en bas.
Donc on attaque à la source, en 3 temps par ordre de valeur/coût :

| # | Pièce | Ce que ça fait | Coût |
|---|---|---|---|
| **A** | **Miroir français** — la déclaration re-rendue en clair, montrée AVANT de construire (« votre app fera X, Y ; PAS Z [unsupported] ») | Tue la marche lossy à la source. Le client valide l'INTENTION en 30 s, avant qu'une ligne existe | 1 appel LLM · **le meilleur rapport valeur/effort de tout v4** |
| **B** | **Aperçu peuplé** — seed 2-3 données réalistes + `npm run dev` + l'HUMAIN clique (partage d'écran client) | « le client voit marcher » sans robot | seed + run |
| **C** | **Robot Playwright** — navigation automatisée, vidéo | **Régression** automatisée | Clerk (~70 %) → **plus tard**, après un spike ½ journée |

**A + B = ~80 % de la valeur à ~20 % du coût.** Le robot (C) est une optimisation de régression,
pas la première marche. `4.9C` du plan v3.9 = uniquement la marche C ; A et B sont nouveaux et prioritaires.

### 11. LA FRONTIÈRE DE L'EXECUTOR — économique, pas technique

Deux « imprévisibles » :
- **Imprévisible qui SE RÉPÈTE** → deviendra une case (« workflow » l'était avant `StatusFlowDeclaration`).
- **Unique IRRÉDUCTIBLE** → jamais une case (un compilateur pour une population de **un** = gâchis).

> Compile ce qui revient · laisse au LLM ce qui est unique. **L'executor ne se vide jamais**
> (queue unique permanente) **et ne grossit jamais** (chaque motif récurrent est absorbé).
> `unsupported[]` compté = le signal qui dit de quel côté est chaque chose.

### 12. `unsupported[]` — 3 niveaux d'exploitation (Niveau 1 = cible, PLUS TARD)

- **N0 (aujourd'hui)** : humain lit, humain écrit la case. Sûr, lent.
- **N1 (cible)** : le LLM **drafte** la case (schéma + générateur + test, calqué sur le patron
  existant) → **humain relit/merge**. Il fait les 80 % fastidieux, l'humain juge les 20 % qui
  comptent (bonne abstraction ? compose ?). L'usine s'étend elle-même, **à qualité brouillon,
  rien ne ship sans review + build + Scène.**
- **N2 (INTERDIT)** : LLM écrit ET livre des compilateurs sans review. **Rayon de destruction :
  un bug de compilateur touche les 50 clients.** Jamais.

⚠ N1 est **plus tardif** : le construire avec 0 `unsupported[]` réel en stock = outil sans
matière. D'abord accumuler les vrais `unsupported[]`, le patron émergera.

### 13. RETOUCHE CLIENT & MAINTENANCE — la règle non négociable

> **On ne modifie JAMAIS le code livré à la main. On modifie la DÉCLARATION et on recompile.**

Le code livré est une **sortie jetable** ; la déclaration (« le négatif ») est ce qu'on garde
et versionne **par client**. Trois cas de retouche :

| Demande client | Action | Coût |
|---|---|---|
| Changement dans une case existante (« ajoute un champ », « le manager peut annuler ») | éditer la déclaration → recompiler → redéployer | ~2 min |
| Changement exigeant une case absente (« des SMS ») | nouvel `unsupported[]` (fréquent→case, unique→LLM) | selon N0/N1 |
| Visuel / libellé | design brief ou libellé dans la déclaration → recompiler | ~2 min |

Éditer le TS livré **casse le négatif** (la recompilation l'écrase). ⚠ Contrainte de design à
tenir : **la régénération ne doit pas écraser le travail custom légitime de l'executor** (les
bords) — préservation des pages LLM à travers les recompilations.

**Propriété tueuse business** : corrige le compilateur **une fois** → **réémets tout le parc**.
Ex. `formatCurrency` (17 Juil) : avec les déclarations stockées, les 50 apps reçoivent le fix.
Aucune agence (qui vend du code figé) ne peut faire ça.

### 14. DÉFINITION FINALE (remplace « startup agentique »)

> **Une usine de compilation pilotée par le langage : une seule tête intelligente à l'entrée
> qui comprend le brief ET connaît ses propres limites, un cœur déterministe qui compile sans
> erreur, un LLM résiduel pour la queue unique, et deux yeux honnêtes — le miroir français en
> amont, l'aperçu peuplé en aval. Elle grandit case par case, sous contrôle humain.**

« Agentique » était un **moyen** (pari 2024-25), pas le but ; le terrain a montré qu'un agent
qui écrit du code dérive, un compilateur non. On ne rejette pas les agents — on les remonte à
l'étage où ils sont irremplaçables (comprendre un humain, avouer une limite), pas là où il faut
zéro erreur. Ni « vivante » (rien n'apprend seul, c'est voulu) : **auto-analytique** (connaît ses
limites) et **évolutive** (par cases validées).

**Ce qui nous a permis d'y arriver — 4 faits, pas des idées :** executor = 0 fichier · 100/100
sur une app absurde · `getPublished` dans 6 endroits · l'architect juste 4×/4 du premier coup.

### 15. LE DESIGN — axe transversal, même modèle (ajouté 17 Juil — était omis de la carte)

Le design n'est **pas un type** (pas dans la séquence D→I→K→H) : c'est un **axe transversal** —
toutes les apps en ont, comme toutes ont de l'auth.

**Il suit EXACTEMENT le modèle compilateur :**
```
brief → DESIGN BRIEF (preset, couleurs, layout, badges)  ← déclaration / AST
           ↓  DESIGN COMPILER (vocabulaire FERMÉ → classes Tailwind statiques)
        l'apparence
```
Existant et déterministe : `design_resolver` (7 presets) · `dev_design_system_generator`
(CSS vars, shadcn) · **`dev_design_compiler`** (badges/icônes/highlights/formatCurrency,
construit 16 Juil). **Preuve de la loi du contenant** : le *LLM Page Enricher* (design en roue
libre) **dérivait** (badges cassés, colonnes fantômes) → **tué et remplacé** par le compilateur.

- **`unsupported` du design** : le vocabulaire est fermé → « timeline animée », « plan de salle »
  = hors vocabulaire. Même concept que `unsupported[]`, autre axe.
- **Lien Scène** : « le client voit son app » = il voit le **design**. Jugé pour de vrai en Scène-B.

**Limite ASSUMÉE (D23)** : couleurs/fonts/density varient par domaine, mais la **structure**
(sidebar fixe, tables) est **identique** d'une app à l'autre. Le **FrontendAgent** (variété
structurelle riche : shadcn, graphiques, animations) a été **annulé** (coût LLM + dérive).

**Décision v4.1 — ne PAS deviner** : « la structure identique coûte-t-elle des ventes ? » n'a
qu'un juge honnête = **la Scène**. Aucun investissement design lourd (FrontendAgent ressuscité,
etc.) **avant** qu'un vrai client ait vu une app. Le signal décide, pas nous. Design actuel =
**correct et cohérent**, limite connue, réévaluée après Scène-B.

---

## PRINCIPES ARCHITECTURAUX (7)
> ⚠️ Lire d'abord RELECTURE TERRAIN §3-§4 : **PRINCIPE 3 et PRINCIPE 5 sont morts** (16 Juil 2026).
> **PRINCIPE 6 est violé.** Les PRINCIPES 4, 7, 8 sont confirmés et renforcés.
> **Nouveau — PRINCIPE 9 (loi du contenant)** : toute intention sans structure pour la porter
> s'évapore. Une expansion crée des **cases**, elle n'enseigne pas au LLM.

**PRINCIPE 1 — Le code exécute, la configuration décide**
Toute règle stack-spécifique vit dans `config/stacks/*.json`.
Le code Python est un exécuteur générique.
Ajouter une stack = créer un JSON + un StackAdapter. Zéro Python core modifié.

**PRINCIPE 2 — Standards prescriptifs, pas descriptifs**
Chaque standard Qdrant dit : RULE:/WHY:/GOOD:/BAD:
Un standard sans exemple négatif est incomplet.
Les standards sont la source de connaissance — le code est l'exécuteur.

**PRINCIPE 3 — La boucle d'apprentissage doit être fermée**
RAG → Dev → Build → Reviewer → Learner → RAG
Chaque maillon est implémenté avant de passer au suivant.
Les fixes gardes-fous masquent l'apprentissage → corriger à la source.

**PRINCIPE 4 — Déterministe pour la forme, Agentique pour le sens**
Les compilateurs (tsc, prisma, next build) sont les arbitres de compilabilité.
Les agents LLM sont les arbitres de sémantique (IDOR, conformité brief, cohérence).
Les deux niveaux coexistent — le déterministe ne disparaît pas, il se concentre.

**PRINCIPE 5 — L'agent reviewer s'auto-rend inutile**
Chaque pattern détecté par le reviewer devient un standard Qdrant (via Learner).
Le Dev apprend → le reviewer corrige moins → les standards s'enrichissent.
Un reviewer qui ne détecte plus rien = succès, pas inutilité.

**PRINCIPE 6 — Complétion avant complexité**
Un niveau doit être fonctionnellement complet avant d'introduire le niveau suivant.
Le Level A (CRUD SaaS simple) doit être prouvé utilisable par un vrai utilisateur
avant de passer au type suivant.
Construire du multi-tenant sur des formulaires cassés = construire sur du sable.

**PRINCIPE 7 — Extension avant limitation**
Quand la factory ne sait pas générer un type d'app, la réponse est d'étendre la couche
déterministe (nouveaux générateurs, nouveaux standards, nouveaux templates),
pas de signaler l'échec au client.
Tout type d'application complexe a une colonne vertébrale déterministe identifiable.

**PRINCIPE 8 — La Scène avant le Déploiement**
Une app n'est pas livrée avant d'avoir été montrée au client dans un état fonctionnel et visuel satisfaisant.
Le déploiement Vercel est la conséquence d'une validation, pas une étape de pipeline automatique.
Ordre non négociable : Frontend viable → QA visuel → Validation client → Deploy.
Un build_success sans frontend décent ni validation visuelle n'est pas un livrable client.

---

## ÉTAT ACTUEL — 6 Juillet 2026 (Niveau 1 stable — PHASE EXPANSION ENGAGÉE)

### Acquis confirmés

**Pipeline Temporal complet :**
`architect_activity → dev_test_activity → review_activity → correction_pass_activity → qa_activity → learner_activity`
*(github_activity en PAUSE volontaire — condition de réactivation : Sprint 9C)*

**Build stable :** Type A validé sur project-hub, task-manager, leave-manager, learn-hub, recipe-manager, expense-tracker, app-simple (7/7 BUILD_SUCCESS). Type D (personal-blog) : BUILD_SUCCESS. event-board (pages publiques/privées mixtes) : BUILD_SUCCESS validé.

**Runs Juillet 2026 (3/3 BUILD_SUCCESS) :** writer-pad (Type D : slug, public/privé, dual-nav), freelance-tracker (FK chain 3 niveaux), sprint-board (3 enums multi-enum). Fixes qualité appliqués : enum labels dans badges/colonnes, nav labels localisés (title_plurals), boolean exclu des pages publiques, D25-D28 réglées.

**Référence expansion : typeApps.md v2.0 (6 Juil 2026)** — états L1-L16 vérifiés dans le code, chemin D→I→K→H→G→E→B, règle des 4 lots.

**Plan6 committé (10 Juin 2026) :**
- **A1** — `dev_actions_generator.py` : `return { error }` → `throw new Error()` dans catch (erreurs formulaires visibles)
- **A2** — templates list : `handleDelete` vérifie `result?.error` avant mise à jour state
- **A3** — `dev_layout_generator.py` : `PUBLIC_PATHS` calculé depuis spec, DashboardShell ne wrappe plus les pages publiques
- **A4** — `public_list_client.tsx.j2` (nouveau) : pages publiques avec template dédié sans boutons dashboard
- **A5** — `dev_service_generator.py` : `getPublicById` filtre `{vis_field}: true` (fix IDOR)
- **A6** — `project_spec.py` : `url = env("DATABASE_URL")` dans bloc datasource Prisma
- **Bloc B** — typeApps.md : Type K (RBAC) ajouté, chemin graduation `A→D→K→G→I→E→H→F→B→C→J`
- **Bloc C** — `service_modules/` : refacto (crud, child, status, public, relations, public_relations, slug)
- **Bloc D** — architect décomposé : `domain_interpreter` + `page_planner` + `spec_enricher`

**Design system intégré (Juin 2026) — REMPLACE Sprint 4.9A FrontendAgent :**
- `design_resolver.py` : 7 presets domaine (editorial/saas/marketplace/wellness/finance/education/community) → couleurs HSL + fonts + density
- `dev_design_system_generator.py` : `globals.css` (CSS vars `--primary` HSL) + `tailwind.config.js` shadcn + composants `components/ui/*.tsx`
- `dev_layout_generator.py` : DashboardShell avec sidebar light/dark selon preset, connecté à dev_graph
- `dev_navigation_generator.py` : navigation.tsx généré ET monté dans layout (fix bug navigation morte)
- `dev_form_generator.py` : tokens sémantiques `bg-primary` / `hover:bg-primary/85` dans toutes les templates
- **design_block** injecté dans prompt LLM dev : brand_name, mood, density, sidebar_bg, composants disponibles
- Résultat : couleurs, fonts et density varient par domaine. Structure (sidebar fixe gauche, tables) identique → **limitation connue, voir dette D23**

**Reviewer opérationnel :** Architecture deux couches. Layer 1 Python déterministe (IDOR/CROSS_USER/AUTH). Layer 2 LLM sémantique (conformité brief, ghost success, page stubs). Résultat : apps correctes → COHERENT 100/100.

**correction_pass réécrit (4.8A') :** Déclenché sur `findings` actionnables (WRONG_AUTH/MISSING_AUTH/BRIEF_CONFORMITY). Rebuild sans `npm install`.

**Architecture modules :**
- `agents/core/` : pipeline_types, error_parser, requirements_engine, spec_coverage, journey_validator, quality_validator
- `agents/stacks/` : StackAdapter pattern
- Level A complet : services, actions, types, schémas, middleware, form generator (Jinja2), pages, design system

**RAG actif :** 116 standards Qdrant, format RULE:/WHY:/GOOD:/BAD:

**Guide briefs :** `factory-sprint0/docs/brief_guide.md` — 4 règles fondamentales.

**Guide briefs :** `factory-sprint0/docs/brief_guide.md` — 4 règles fondamentales pour rédiger des briefs exploitables par la factory.

---

## SPRINTS COMPLÉTÉS — RÉSUMÉ

| Sprint | Période | Livrables clés |
|--------|---------|----------------|
| 0–3 | Fév–Mars 2026 | Pipeline end-to-end, Stack-as-Config, RAG, Learner shadow mode |
| 4 | Mars–Avr 2026 | Requirements déterministes, contracts v2, Blueprint Validator, spec_coverage |
| 4.5 | Avr 2026 | user_flows[], Journey Validator, seuil is_useful_app |
| Pré-4.6 | Mars 2026 | Refacto Architecture Simplifiée (supervisors LLM inline supprimés) |
| 4.6 | ❌ Abandonné | LLM inline : angles morts partagés → Reviewer post-build |
| T2–T5 | Mai 2026 | agents/core/ extraits, StackAdapter, Docker npm_cache, forbidden_keywords |

---

## SPRINT 4.7 — Complétion Fonctionnelle Level A
## Deadline : Mai–Juin 2026 | STATUT : ✅ COMPLÉTÉ

| Fix | Fichier cible | Impact |
|-----|--------------|--------|
| A1 | `templates/env.local.template` | DIRECT_DATABASE_URL + 4 vars Clerk redirect |
| A2 | `templates/prisma_config.ts` | DIRECT_DATABASE_URL pour migrations Neon/PgBouncer |
| A3 | `templates/env.example.template` + JSON config | .env.example dans chaque projet livré |
| B1 | `dev_navigation_generator.py` + layout template | Navigation depuis spec.pages[] |
| C1 | `dev_service_generator.py` | Supprimer `as unknown as Model[]` + `as any` |
| D1 | `agents/core/journey_validator.py` | Détecter actions.ts par contenu modèle |

**4.7B — Form Generator déterministe (Jinja2) :** `dev_form_generator.py` génère `page-client.tsx` pour chaque modèle (String→input, Int/Float→number, DateTime→datetime-local, Boolean→checkbox, FK→select).

**4.7C — dev_pages_generator :** pages list / detail / edit complètes.

**4.7D — Failles techniques :** F1 (Progressive Validation), F3/F4 (quality_validator async), F5 (getAllByUser), F8 (pagination), F9 (types retour), F10 (Decimal).

**4.7E — Innovations :** Feature Module Registry déclaratif + LevelAManifest + CONTRACT.md généré.

### Signal clôture Sprint 4.7 ✅
- `npm install && npm run dev` sans intervention
- Utilisateur peut CRUD sans taper un UUID
- Navigation présente dans le header
- `is_useful_app: true` sur ≥3 runs consécutifs Type A

---

## SPRINT 4.8 — Boucle Qualité Complète
## Deadline : Juin 2026 | STATUT : EN COURS (4.8A ✅ · 4.8A' ✅)

### 4.8A — Reviewer deux couches ✅ COMPLÉTÉ (05 Juin 2026)

**Layer 1 — Python déterministe** (`reviewer.py/_run_deterministic_checks`) :
- IDOR : `update/delete` sans owner dans `where`
- CROSS_USER : `findMany` sans filtre owner
- AUTH_GUARD : pages privées sans `auth()` / pages publiques avec auth bloquant
- `targeted_fixes` générés depuis Layer 1 (WRONG_AUTH/MISSING_AUTH) pour affichage/reporting

**Layer 2 — LLM sémantique** (gpt-4o, services exclus du contexte) :
- Ghost success, page stubs, brief conformity
- Résultat : recipe-manager BRIEF_CONFORMITY trouvé — apps correctes → COHERENT 100/100

**Format ReviewReport :**
```json
{
  "verdict": "COHERENT|DEGRADED|INCOHERENT",
  "security_score": 100,
  "coherence_score": 80,
  "findings": [{"type": "BRIEF_CONFORMITY", "severity": "WARNING", "file": "app/page.tsx"}],
  "targeted_fixes": [{"file": "...", "type": "WRONG_AUTH", "fix": "..."}]
}
```

---

### 4.8A' — correction_pass ✅ COMPLÉTÉ (05 Juin 2026)

**Portée** : uniquement les **pages custom LLM-générées** (jamais les fichiers protégés).

| Finding | Action |
|---|---|
| `WRONG_AUTH` sur page publique | Supprimer `auth()+redirect` (déterministe) |
| `MISSING_AUTH` sur page privée | Ajouter `auth()+redirect` (déterministe) |
| `BRIEF_CONFORMITY` (page custom) | Re-soumettre la page au LLM avec le finding comme contrainte |

**Changements implémentés :**
- `correction_pass_activity.py` : lit `findings` (pas `targeted_fixes`), Level 1 déterministe + Level 2 LLM, rebuild sans `npm install`
- `todo_pilot_workflow.py` : trigger sur findings actionnables, passe `findings` + `brief` + `spec`
- `reviewer.py` : génère `targeted_fixes` depuis Layer 1 WRONG_AUTH/MISSING_AUTH

**Signal de déclenchement :** ≥1 finding CRITICAL/WARNING de type `WRONG_AUTH`, `MISSING_AUTH` ou `BRIEF_CONFORMITY` sur une page non-protégée.

---

### 4.8B — QA Agent — Couche 1 Jest ✅

**Architecture — deux couches :**

**Couche 1 — Smoke tests Jest** ✅ IMPLÉMENTÉ
- `gpt-4o` génère des tests Zod + services via `json_object`
- Exécutés en <1 min, signal rapide
- Fichiers : `agents/qa.py` + `qa_activity.py`

**Couche 2 — QA visuel E2E** → DÉPLACÉ EN SPRINT 4.9C
*(Raison : l'app doit avoir un frontend viable et une identité visuelle avant d'être présentée.
BrowserUse/noVNC abandonnés — problèmes Docker. Architecture correcte : Playwright sur host.
Voir Sprint 4.9C.)*

**Output actuel :**
```json
{
  "tests_passed": true/false,
  "tests_summary": "...",
  "semgrep": {"ran": true, "findings_count": 0}
}
```

**Boucle d'apprentissage (cible 4.9C) :**
```
QA visuel : flow_2 FAIL (formulaire ne soumet pas)
  → Learner : propose standard "useActionState doit retourner errors"
    → Opérateur approuve → Qdrant enrichi
      → Dev LLM applique au prochain run
        → QA : flow_2 PASS ✅
```

**Ordre pipeline :** `dev_test → review → correction_pass → QA → Learner`

**Signal cible 4.8B :** `tests_passed: true` sur ≥1 run (Jest smoke tests)

---

### 4.8C — Learner — Vision révisée ⏳

**Output 1 — FactoryRunReport** (écrit dans `logs/run_reports/` à chaque run) :
```
FactoryRunReport — event-board — 2026-06-05
══════════════════════════════════════════
BUILD        : ✅ SUCCESS (1 correction — Link import)
REVIEW       : COHERENT | sec=100 | coh=100 | 0 findings
CORRECTIONS  : 0 (correction_pass SKIPPED — aucun finding CRITICAL)
TESTS        : ✗ 0 tests générés

PATTERNS DÉTECTÉS :
  ⚠ Link import oublié dans pages custom (× 3 runs)
  → Suggestion standard — DÉCISION REQUISE

RAG UTILISÉ  : Z08, Z24, Z26
DURÉE        : 3min 20s
```

**Output 2 — StandardSuggestions** (`learner_suggestions.json`) :
- Basées sur patterns détectés (N ≥ 2 occurrences)
- Validation humaine via `approve_suggestion.py` avant upsert Qdrant
- **Le développeur reste dans la boucle** — aucun standard n'entre dans Qdrant sans approbation

**Learner deux couches (vision) :**
- Standards dev LLM : patterns de code mauvais → Qdrant
- Standards architect : patterns spec mauvais → `_DEDUCTION_RULES`

---

### 4.8D — Innovations ⏳

**A. Type Safety Chain Validator :** valide `SerializedXxx → service → actions → page-client` avant build.

**B. App Usefulness Scorer :**
```
score = build_success(40%) + user_flows_coverage(30%) + quality_violations(20%) + spec_coverage(10%)
→ is_production_ready: bool + score/100
```

**H. Learner-Driven Standard Evolution :** violations quality_validator → Learner → standards Qdrant.

---

### Signal clôture Sprint 4.8

- ✅ `review_activity` : findings réels détectés (recipe-manager BRIEF_CONFORMITY)
- ✅ `correction_pass` : réécrit, déclenche sur findings actionnables (4.8A')
- ✅ `FactoryRunReport` produit à chaque run — `logs/run_reports/<projet>_<date>.md` (4.8C)
- ✅ `learner_suggestions.json` mis à jour à chaque run (4.8C)
- ✅ BrowserUse/noVNC retirés — QA visuel déplacé en 4.9C (architecture correcte)
- ⏳ `correction_pass` : validé sur cas réel avec WRONG_AUTH détecté + corrigé
- ⏳ `tests_passed: true` sur ≥1 run — Jest smoke tests (4.8B)
- ⏳ ≥1 StandardSuggestion approuvée + upsert Qdrant (4.8C)

---

## SPRINT 4.9 — La Scène + Correction + Deploy
## Deadline : Juillet 2026 | STATUT : Planifié (4.9A + 4.9B ANNULÉS — remplacés)

**Vision (PRINCIPE 8) :** Le client assiste à la démonstration de son application avant tout déploiement.
La factory doit produire une app fonctionnelle et visuellement présentable, la faire naviguer par Playwright,
corriger agentiquement ce qui cloche, et seulement ensuite déployer sur Vercel.

**Ordre non négociable :**
```
~~A — FrontendAgent~~  →  ~~B — Brief visuel~~  →  C — QA visuel (la scène)  →  D — Correction agentique  →  E — Deploy
```

**4.9A annulé :** FrontendAgent LLM ReAct (v3.7) → remplacé par design déterministe intégré dans dev_graph (Juin 2026). Raison : coût LLM supplémentaire non justifié, contexte frais préservé, design variante via presets domain. Voir "Design system intégré" dans Acquis.

**4.9B annulé :** L'agent lit le ProjectSpec directement → remplacé par `design_resolver.py` qui infère automatiquement le domaine depuis le brief (0 LLM, 0 coût).

---

### ~~4.9A — FrontendAgent : agent LLM autonome avec outils~~ ❌ ANNULÉ

**Décision architecturale finale (Juin 2026 — v3.8) :**
Le FrontendAgent ReAct a été annulé. Le design est intégré directement dans le pipeline déterministe :
`design_resolver` → `dev_design_system_generator` → `dev_layout_generator` → `dev_form_generator`.
Résultat : 7 presets de domaine avec couleurs/fonts/density distincts, 0 LLM supplémentaire.
**Limitation intentionnelle acceptée :** la structure des pages (sidebar fixe, tables pour listes privées)
reste identique entre apps. Voir dette D23 pour l'amélioration prévue (private list cards).

**Contrat fondamental :**
- Accès lecture : tous les fichiers (brief, ProjectSpec, code généré)
- Accès écriture : **couche présentation uniquement**
  - `app/**/page-client.tsx` — pages client réécrites avec les composants choisis
  - `app/layout.tsx` — navigation, sidebar, header global
  - `app/globals.css` — tokens visuels (couleurs, typo, animations base)
  - `app/components/` — composants UI créés ici (pas de limite fixe)
  - `tailwind.config.js` + `postcss.config.js` — config CSS
  - `package.json` — uniquement devDependencies (ajout shadcn, framer-motion, recharts…)
- **Jamais modifiés** : `lib/services/`, `app/**/actions.ts`, `prisma/`, `middleware.ts`, `lib/prisma.ts`

**Architecture FrontendAgent (LLM ReAct loop) :**

```
BUILD_SUCCESS + correction_pass OK
    │
    ▼
FrontendActivity (Temporal wrapper — après correction_pass, avant QA)
    │
    ├── SNAPSHOT : sauvegarde page-client.tsx existants (rollback target)
    │
    ├── AGENT LOOP (max_iterations = 8)
    │   │
    │   ├── Contexte injecté au démarrage :
    │   │     brief (texte naturel)
    │   │     ProjectSpec { models, pages, routes, user_flows }
    │   │     liste des page-client.tsx existants
    │   │     librairies disponibles : shadcn/ui · Tailwind · Lucide React
    │   │                              Framer Motion · Recharts · Tremor
    │   │
    │   ├── Tool : read_file(path)         — lire n'importe quel fichier du projet
    │   ├── Tool : write_file(path, content) — écrire dans la couche présentation
    │   ├── Tool : npm_add(packages[])     — ajouter des devDependencies + npm install
    │   ├── Tool : tsc_check(path)         — valider un fichier TypeScript isolément
    │   ├── Tool : build_check()           — npm run build complet
    │   └── Tool : finish(summary)         — signaler la fin du travail
    │
    │   Comportement attendu du LLM :
    │   1. Lit le brief → identifie le domaine (CRM ? dashboard ? blog ?)
    │   2. Lit les pages existantes → comprend la structure actuelle
    │   3. Planifie : quels composants shadcn/ui installer, quelles animations,
    │                 quel layout (sidebar ? topnav ? cards ?), quels graphiques
    │   4. npm_add si nécessaire (framer-motion, recharts, @radix-ui/…)
    │   5. Réécrit page par page avec les composants choisis
    │   6. tsc_check après chaque fichier modifié
    │   7. build_check → si SUCCESS : finish / si FAIL : corrige et réitère
    │
    └── ROLLBACK si build_check toujours FAIL après max_iterations
        → restauration snapshot page-client.tsx
        → suppression tailwind.config.js / postcss.config.js / app/components/ui/
        → log FRONTEND_DEGRADED dans FactoryRunReport
        → pipeline continue sans régression (app fonctionnelle garantie)
```

**Ce que le LLM sait faire nativement (pas besoin de lui enseigner) :**

| Besoin visuel | Librairie | Comment le LLM l'utilise |
|---|---|---|
| Composants UI complets | **shadcn/ui** | Connaît chaque composant, props, CLI `npx shadcn@latest add` |
| Icônes | **Lucide React** (npm) | Connaît 1500+ icônes, importe directement |
| Animations | **Framer Motion** | Écrit variants, transitions, AnimatePresence |
| Graphiques | **Recharts** ou **Tremor** | Connaît BarChart, LineChart, AreaChart complets |
| Transitions CSS | **Tailwind animate** | Classes animate-*, custom keyframes dans globals.css |
| Illustrations/SVG | **SVG inline** | Génère SVG directement dans JSX (pas besoin d'API externe) |
| Images produit | `next/image` + placeholder | Génère le slot, contenu = responsabilité client |

**Pourquoi pas DALL-E ni génération d'images :**
Les images "de fond" d'une app SaaS sont du contenu client (avatars, photos produit, illustrations).
Ce que le frontend produit c'est de la structure : `<Image src={user.avatar} />` — pas l'image elle-même.
Pour les illustrations d'état vide, le LLM écrit des SVG directement. Pas d'API image nécessaire.

**Starter kit (fourni avant l'agent loop, non imposé) :**
Le design system généré en v3.6 (Button, Card, Table, Badge, Empty, StatCard + tailwind.config.js)
reste présent comme **point de départ optionnel**. L'agent peut l'utiliser, l'enrichir, ou l'ignorer
s'il choisit shadcn/ui à la place. Ce n'est plus une contrainte, c'est une ressource.

**Signal clôture 4.9A :**
- `FrontendActivity` Temporal active avec agent ReAct loop (≥2 tools utilisés)
- L'agent choisit au moins 1 librairie externe selon le domaine (shadcn/ui, framer-motion ou recharts)
- `build_check()` SUCCESS après réécriture ≥1 page-client.tsx
- Rollback activé : build dégradé → version pré-frontend préservée

---

### ~~4.9B — ProjectSpec → FrontendAgent~~ ❌ ANNULÉ

**Décision (v3.8) :** Remplacé par `design_resolver.py` — infère automatiquement le domaine
(editorial/saas/marketplace/wellness/finance/education/community) depuis le brief, sans LLM.
La déduction "ce brief = blog editorial = amber, Playfair Display, spacious" est déterministe.

**Ce que le FrontendAgent reçoit en contexte de démarrage :**
```json
{
  "brief": "Outil de gestion de projets pour équipes, avec tableau de bord et KPIs",
  "project_spec": {
    "models": ["Project", "Task", "User"],
    "pages":  ["/projects", "/projects/[id]", "/dashboard"],
    "user_flows": ["Créer un projet", "Assigner une tâche", "Voir le tableau de bord"]
  },
  "existing_files": ["app/projects/page-client.tsx", "app/dashboard/page-client.tsx", ...]
}
```

**Ce que l'agent en déduit seul (sans aide) :**
- "tableau de bord + KPIs" → installer recharts, créer StatCard + BarChart
- "gestion de projets" → layout avec sidebar de navigation latérale
- "équipes" → composants d'avatar, badge statut membre
- `/projects/[id]` → page détail avec onglets (Overview / Tasks / Members)

**layout_type + theme_tone : optionnels mais acceptés**
Si l'architect les fournit dans ProjectSpec (v3.6 déjà prévu), l'agent les utilise comme hints.
Si absents, l'agent les infère. Dans les deux cas, l'agent décide en dernier ressort.

**Signal :** l'agent produit un frontend différencié selon le domaine (CRM ≠ blog ≠ dashboard)
sans instructions visuelles explicites — seulement depuis le brief + les pages.

---

### 4.9C — QA Visuel — La Scène *(couche 2 QA)* ← PROCHAINE PRIORITÉ

**Vision :** le client assiste à la navigation de son app par un agent Playwright.
Il voit ses données apparaître, ses formulaires fonctionner, ses flows s'exécuter.
Pas de streaming Docker complexe — le navigateur tourne sur le host, visible sur l'écran de l'opérateur.

**Architecture :**
```
BUILD_SUCCESS
  → factory-worker : npm run dev (port 3000, mappé 3000:3000 dans docker-compose)
  → healthcheck : attendre localhost:3000 ready
  → Playwright Python (sur HOST Windows) :
      Pour chaque user_flow[] :
        ├── navigate + interact
        ├── screenshot à chaque étape clé
        └── video .webm enregistrée (via playwright.record_video)
  → Artefacts dans logs/qa/<projet>/ (volume bind-mounté)
  → qa_score = flows_passed / flows_total
```

**Pourquoi sur le host, pas dans Docker :**
Docker est aveugle — pas d'écran. noVNC/Xvfb : complexe, fragile, retiré en Sprint 4.8.
Le navigateur sur Windows est visible directement. L'opérateur et le client regardent ensemble.
Les vidéos sont dans `./logs/qa/` accessibles depuis Windows immédiatement.

**Infrastructure requise :**
- `docker-compose.yml` : ajouter `3000:3000` au factory-worker
- `scripts/qa_visual.py` : script Playwright Python sur host (hors container)
- `scripts/start_app.py` : script qui démarre `npm run dev` dans le container via docker exec

**Output :**
```json
{
  "qa_score": 0.75,
  "flows_passed": 3,
  "flows_total": 4,
  "flow_results": [
    {"flow": "Utilisateur crée une recette", "status": "PASS", "video": "flow_1.webm"},
    {"flow": "Utilisateur modifie une recette", "status": "FAIL",
     "error": "Formulaire vide après navigation", "screenshot": "flow_2_fail.png"}
  ]
}
```

**Signal cible :** `qa_score ≥ 0.8` sur ≥1 run, vidéos consultables depuis Windows

---

### 4.9D — Boucle correction agentique depuis QA visuel

**Problème :** les bugs visuels détectés par le QA ne déclenchent pas de correction aujourd'hui.
`correction_pass` est câblé sur les findings du reviewer (WRONG_AUTH, BRIEF_CONFORMITY) — pas sur les flows QA ratés.

**Solution :** étendre `correction_pass` pour recevoir les `flow_results` en entrée :

| Finding QA | Action correction |
|---|---|
| Flow FAIL + erreur formulaire | LLM re-génère la page-client avec le flow comme contrainte |
| Flow FAIL + données absentes | LLM vérifie les appels service dans page.tsx |
| Flow FAIL + navigation cassée | LLM corrige les `<Link href>` selon `page_links` du spec |

**Ordre pipeline complet :**
```
dev_test → review → correction_pass (reviewer) → FrontendActivity → QA visuel → correction_pass (QA) → Learner
```

**Signal :** au moins 1 flow_fail → déclenche correction → flow passe au run suivant

---

### 4.9E — Production Deploy + DY fixes

*(Seulement après validation visuelle client — PRINCIPE 8)*

**Deploy pipeline :**
```
Client valide la démo → deploy_activity :
  1. Neon API → créer DB client → DATABASE_URL
  2. Clerk API → enregistrer domaine app dans Allowed Redirect URLs
  3. vercel --prod --token=$VERCEL_TOKEN → URL de production
  4. Injecter vars d'env dans projet Vercel via API
```

**Fichiers générés par `dev_production_generator.py` :**

| Fichier | Contenu |
|---------|---------|
| `vercel.json` | `{"framework": "nextjs"}` |
| `.env.production.local` | DATABASE_URL Neon + vars Clerk prod |
| `migrate.sh` | `npx prisma migrate deploy` |
| `app/error.tsx` | Error boundary global |
| Prisma `@@index` | FK + champs filtrés fréquemment |

**DY fixes (qualité du contexte LLM) :**
- DY3 : `rules_dev.md` réduit à ≤12 règles LLM uniquement (retirer règles sur fichiers déterministes)
- DY7 : retirer queries RAG "service" et "actions" du JSON config
- DY1 : modules via `enriched_spec.features[]` (remplace heuristiques)
- Progressive Validation : `tsc --noEmit` après chaque `write_file()` LLM

**Technologies sprint 4.9 :**
Playwright Python (host) · Tailwind theme tokens · VisualSpec architect · Neon API · Clerk API deploy · Langfuse (observabilité) · Track 2 Phase-Aware

---

### Signal clôture Sprint 4.9

- ✅ `FrontendAgent` ReAct loop : ≥2 tools utilisés (au moins read_file + write_file + build_check)
- ✅ Agent choisit ≥1 librairie externe selon le domaine (shadcn/ui, recharts, framer-motion ou autre)
- ✅ Frontend différencié selon le brief : un dashboard ≠ un blog ≠ un CRM visuellement
- ✅ build_check SUCCESS après réécriture ≥1 page-client.tsx
- ✅ Rollback activé : build dégradé → version pré-frontend préservée, pipeline continue
- ✅ `qa_score ≥ 0.8` sur ≥1 run — vidéos consultables depuis Windows
- ✅ ≥1 flow_fail → correction agentique → flow passe
- ✅ App déployée sur Vercel via `deploy_activity` sans intervention manuelle
- ✅ DY3 + DY7 résolus : `rules_dev.md` ≤ 12 règles, queries RAG mortes retirées

---

## SPRINT 5 — Type D-complet : Blog/CMS
## Deadline : Juillet 2026 | STATUT : ✅ **COMPLÉTÉ (16 Juil 2026)**

**Validé sur 3 briefs non biaisés** : `abo` (privé), `atelier` (public + card-grid + M2M),
`club-running` (statut + FK + enfants) — BUILD_SUCCESS + 0 violation qualité, **vérifiés par
lecture du code généré**, pas par métriques.

**Livré au-delà du plan (16 Juil) :**
- **Design Compiler déterministe** (`dev_design_compiler.py`) — remplace le *LLM Page Enricher*,
  supprimé : il réécrivait les fichiers entiers et **dérivait** (badges cassés, colonnes
  fantômes). Runs ~2× plus rapides (~113s vs ~230s).
- **Capteur qualité réparé** — `quality_check.mjs` était **aveugle à tous les .tsx** (option
  `filePath` manquante → JSX parsé comme .ts → erreur avalée par un `catch{continue}`).
  **Il n'avait donc JAMAIS analysé une seule page.** + checks C1/C2 + `C0-unparseable`.
- **`getPublished` déprécié dans 6 sources écrites à la main** (service_modules, status.py,
  page_planner, dev_system_prompt, dev_service_spec/CONTRACTS.md, **prompt annotateur**) —
  méthode fantôme que l'architect croyait exister → TS2339. Voir D34 : le mécanisme qui l'a
  laissée dériver est **toujours là**.
- **`formatCurrency` ajouté aux 5 templates de liste** — le détail affichait « 42,50 € », la
  liste « 42.5 ». Corrige **toutes** les apps avec de l'argent.

**Règle des 4 lots (typeApps.md v2.0 §3.5)** : chaque expansion livre Squelette + Connaissance + Design + Garde-fous, puis une passe de cohérence (rules_dev / CONTEXT_QUERIES / capabilities string / standards).

### Lot 1 — Squelette
| Livrable | Contenu |
|-----------|---------|
| `dev_seo_generator.py` | `generateMetadata()` par page publique, `og:image`, `sitemap.xml`, `robots.txt` |
| M2M dans service_modules | Détection `Tag[]` sans @relation → include dans getAllWithRelations + connect dans create |
| Template `rich_textarea.tsx.j2` | Textarea enrichi pour champ `content` long |

### Lot 2 — Connaissance
~6 standards Qdrant : SEO metadata, draft/publish lifecycle, M2M tags, content field. Architect : déjà à jour (editorial, slug_routing, public_pages connus).

### Lot 3 — Design : rien (preset editorial + layout hero existants)
### Lot 4 — Garde-fous : rien de nouveau (checks publics existants)

**Brief de validation :** blog avec tags M2M, SEO, draft/publié, contenu long.
**Signal clôture :** BUILD_SUCCESS + sitemap.xml présent + tags fonctionnels + `is_useful_app: true`.

*(Reportés en flux secondaire : 5A Mode Replay · 5B Standards Maintenance Agent · 5C Compatibility Matrix — non bloquants pour l'expansion.)*

---

## SPRINT 6 — Type I : Workflow / Approbation
## Deadline : ~~Août~~ → **EN COURS (16 Juil — en avance)** | STATUT : ~90 % — cœur acquis et vérifié

**Brief de référence utilisé** : `notes-frais` (non biaisé — voir §8). Le brief congés du plan
reste à passer en validation finale.

### ✅ ACQUIS — vérifié par lecture du code généré (build + tsc OK)
| Pièce | Détail |
|---|---|
| **La case** — `StatusFlowDeclaration` (`semantic_spec.py`) | `field` · `initial` · `transitions` · `locked_states` · `state_fields`. Clé par **MODÈLE** (pas par champ : `field_annotations` est indexé globalement → 2 modèles à `status` auraient collisionné). Composabilité assurée dès le design |
| **`EnrichedSpec.status_flows`** + prompt annotateur | L'architect remplit **parfaitement, du premier coup**, sans réglage |
| **Validation déterministe** (`dev_model_context.py`) | Rejette une déclaration invalide (champ fantôme, état hors enum) → dégrade en CRUD simple plutôt que compiler du faux. **Jamais l'état initial dans `locked_states`** (figerait toute entité dès sa création) |
| **État initial forcé** | `status` hors de `CreateSchema` **et** du formulaire **et** écrasé serveur (`data: {...data, userId, status: 'draft'}`) — triple verrou |
| **Garde serveur de transition** (`crud.py update`) | Liste blanche `allowedTransitions` → `throw` sinon. **Ferme la porte dérobée** que `transitionTo` seul laissait ouverte |
| **Verrou d'édition** (`locked_states`) | Champs métier figés, **le statut continue d'avancer** (`_k !== 'status'`) — sinon le workflow se figerait à la 1ʳᵉ étape |
| **UI** | Select restreint aux transitions permises + option vide supprimée + état terminal figé « gratuitement » (liste vide = verrou) + champs désactivés + bandeau |

### ⏳ RESTE À FAIRE
| Livrable | Contenu |
|-----------|---------|
| `transitionTo(userId, id, newStatus, data?)` + `if_transitions` au REGISTRY | **L'intention** : porte les boutons ET les `state_fields` (« refusée AVEC UN MOTIF » = charge utile d'une transition, pas un champ parmi d'autres). Entrée REGISTRY → auto-propagation architect. **La garde dans `update` RESTE** (défense en profondeur) |
| Template détail | **Boutons de transition** ; `status` retiré du formulaire d'édition — *modifier ≠ faire avancer*, deux intentions, deux interfaces |
| **Passe de cohérence** *(obligatoire — règle des 4 lots)* | Vérifier qu'aucune instruction ancienne ne contredit les transitions (piège type ligne 872 : « rules_dev règle 12 vs AggregationModule ») |
| Brief congés | Validation finale (le brief du plan) |

### ❌ ABANDONNÉS (voir RELECTURE TERRAIN §3)
- ~~`project_spec.status_transitions`~~ → la déclaration vit dans `EnrichedSpec` : c'est
  l'annotateur qui la produit (le Lot 2 du plan le disait déjà lui-même).
- ~~Check reviewer L1 « update direct du status hors transitionTo »~~ → **rendu inutile** :
  la garde est *dans* `update`, il n'y a plus de contournement à surveiller. Fermer la porte
  plutôt que poster un gardien (`feedback_fix_at_source`).
- ~~~8 standards Qdrant~~ → sans sujet (§3).

### Lot 2 — Connaissance
- semantic_annotator : annoter les transitions légales (extension status-enum existant)
- domain_interpreter : few-shot congés (soumis → approuvé/rejeté)
- ~8 standards Qdrant (FSM pattern, anti-update-direct, audit trail)
- CONTEXT_QUERY `workflow-pages` dans dev_prompts.py

### Lot 3 — Design : rien (conventions badges pending/approved/rejected déjà dans design_brief)
### Lot 4 — Garde-fous
- Check reviewer Layer 1 : « update direct du champ status hors transitionTo »
- Entrée `if_transitions` dans SERVICE_METHOD_REGISTRY (propagation auto architect + enricher)

**Brief de validation :** demandes de congé — employé soumet, manager approuve/rejette.
**Signal clôture :** transition illégale refusée par le service + boutons UI corrects + `is_useful_app: true`.

---

## SPRINT 7 — Type K : Multi-Role / RBAC
## Deadline : Septembre 2026 | STATUT : Planifié

**Le vrai chantier Lot 2 de la série** : le concept « rôle » est absent des 8 niveaux du pipeline. Clerk `publicMetadata.role` — pas de modèle Prisma Role. L'invariant single-tenant n'est PAS violé (admin = lecteur privilégié, pas second propriétaire).

### Lot 1 — Squelette
| Livrable | Contenu |
|-----------|---------|
| `dev_rbac_generator.py` | Guards rôle dans Server Actions + `getAllAsAdmin()` |
| Middleware template | Routes /admin/* vs routes user |
| `dev_layout_generator.py` | Nav conditionnelle par rôle |
| `project_spec.py` | Champ `roles: list[str]` |

### Lot 2 — Connaissance *(dominant)*
- Few-shots admin/portail dans domain_interpreter ET page_planner (pattern /admin/*)
- Standards LK1-LK4 · règle rules_dev « page admin vérifie le rôle » · CONTEXT_QUERY `admin-pages`
- brief_guide.md : nuancer « un seul acteur » → un seul propriétaire de données, plusieurs niveaux de lecture

### Lot 3 — Design : nav_icons admin dans design_brief
### Lot 4 — Garde-fous **(OBLIGATOIRE avant le 1er run)**
- Check reviewer : « page /admin sans vérification de rôle » — faille sécurité silencieuse sinon

**Brief de validation :** SaaS admin+user — admin voit tout, user voit ses données.
**Signal clôture :** reviewer 0 finding rôle + nav différenciée + `is_useful_app: true`.

---

## SPRINT 8 — Type H : Dashboard / Analytics *(le plus agentique)*
## Deadline : Octobre 2026 | STATUT : Planifié

### Lot 1 — Squelette
| Livrable | Contenu |
|-----------|---------|
| `service_modules/aggregation.py` | count/sum/avg/groupBy selon annotation `analytics` |
| StatCard enrichi + pagination getAll | L4 + composant métrique |

### Lot 2 — Connaissance
- ⚠ **RÉÉCRIRE rules_dev.md règle 12** (« agrégations = getAll + calcul TS ») — contradiction directe avec AggregationModule sinon (piège cohérence identifié 6 Juil)
- Annotation `kpis` dans semantic_annotator · standards charts/recharts · CONTEXT_QUERY `analytics-pages`

### Lot 3 — Design : archétype chart_type par entité dans design_brief + recharts au package template
### Lot 4 — Garde-fous : entrée `if_analytics` registre + check N+1 dashboards

**Brief de validation :** dashboard commercial — CA du mois, taux de conversion, chart d'évolution.
**Signal clôture :** agrégations exécutées en DB (pas getAll+filter) + recharts rendu + `is_useful_app: true`.

---

## SPRINT 9 — Type G Booking + Type E E-commerce (début)
## Deadline : Novembre 2026 | STATUT : Planifié

### 9A — Type G : Booking *(réutilise la FSM du Sprint 6)*
`dev_booking_generator.py` (conflits de créneaux, disponibilités) · `calendar_picker.tsx.j2` + module CalendarView (le signal `calendar_view` existe dans le catalogue features — aucun module ne l'implémente aujourd'hui) · standards timezone/annulation (~10).

### 9B — Type E fondations : L10 Decimal (`_serialize` + toNumber) · L15 $transaction (`createWithItems`)

### 9C — GitHub agent réactivation (condition : Level A stable ≥10 runs)

---

## SPRINT 10 — Type E complet (Stripe) + Type F Social + Level B préparation
## Deadline : Décembre 2026 | STATUT : Planifié

`dev_billing_generator.py` (Stripe + webhooks) · `dev_cart_generator.py` · Type F (feed, M2M hérité de D, compteurs hérités de H) · Préparation B : plan de casse de l'invariant single-tenant (touche domain_interpreter + ProjectSpec + tous les service_modules + reviewer — batterie de non-régression A→H obligatoire).

*(Type B complet, C Marketplace, J Fichiers, Stack 2 : 2027 — après validation des 8 types fondamentaux.)*

---

## EXPANSION DÉTERMINISTE PAR TYPE D'APP

| Type | Nom | Generators manquants | Standards requis | Signal architect | Sprint |
|------|-----|---------------------|-----------------|-----------------|--------|
| **A** | CRUD SaaS | ✅ Complet | ✅ 116 actifs | — | ✅ 4.7 |
| **D** | Blog/CMS *(80% fait)* | `dev_seo_generator.py`, M2M service, `rich_textarea.j2` | ~6 (SEO, draft/publish, M2M) | ✅ déjà connus (editorial/slug/public) | 5 |
| **I** | Workflow | `service_modules/transition.py` (FSM) | ~8 (FSM, anti-update-direct, audit) | status-enum ordre workflow ✅ + transitions à annoter | 6 |
| **K** | RBAC | `dev_rbac_generator.py`, middleware rôles, nav conditionnelle | ~4 (LK1-LK4) + règle rules_dev | "admin", "manager", "portail" — few-shots À CRÉER | 7 |
| **H** | Dashboard | `service_modules/aggregation.py`, StatCard, pagination | ~6 (groupBy, recharts) + **réécrire règle 12** | annotation `kpis` à créer | 8 |
| **G** | Booking | `dev_booking_generator.py`, CalendarView (signal existe, module absent) | ~10 (slots, timezone) | "réservation", "créneau" — catalogue ✅ | 9 |
| **E** | E-commerce | Decimal + $transaction + `dev_billing/cart_generator.py` | ~15 (Stripe, checkout) | "boutique", "paiement" | 9–10 |
| **F** | Social | hérite M2M (D) + compteurs (H) + feed paginé | ~10 (follows, feeds) | "réseau", "posts", "like" | 10 |
| **B** | Multi-tenant ⚠ | casse invariant single-tenant (domain_interpreter) | ~12 (tenant isolation) | "organisation", "workspace" | 2027 |
| **C** | Marketplace | nécessite D + E + B | ~20 (escrow, listing lifecycle) | "acheteur", "vendeur" | 2027 |
| **J** | File Mgmt | `dev_storage_generator.py` + intégration S3/R2 | ~8 (upload, permissions) | "fichier", "document", "upload" | 2027 |

**Règle d'expansion v3.9 (PRINCIPE 7 + règle des 4 lots — typeApps.md v2.0 §3.5) :**
```
Nouveau type → LOT 1 Squelette (modules + templates + ProjectSpec + flags contexte)
             → LOT 2 Connaissance (few-shots architect + annotator + standards + CONTEXT_QUERY
                                   + MISE À JOUR rules_dev — jamais juste ajout)
             → LOT 3 Design (archétypes design_brief + presets)
             → LOT 4 Garde-fous (check reviewer L1 + SERVICE_METHOD_REGISTRY)
             → PASSE DE COHÉRENCE (aucune instruction ancienne ne contredit la nouvelle capacité)
             → RUN DE VALIDATION (brief de test typeApps.md §7) avant le type suivant
```
Mécanisme d'auto-propagation : toute méthode ajoutée au SERVICE_METHOD_REGISTRY est
automatiquement connue de l'architect (capabilities string) et validée par le spec_enricher.

---

## DÉPLOIEMENT — Architecture Standard

```
App générée → github_activity → factory-generated-apps (branche par projet)
           → Vercel (auto-deploy, zero-config Next.js)
           → Neon PostgreSQL (serverless, connection pooling Prisma natif)
           → Clerk (auth)
```

**Pourquoi Neon :** serverless PostgreSQL avec connection pooling natif Prisma. Vercel + Prisma sans pooler = saturation connexions en serverless. PlanetScale a supprimé son free tier.

**Ce que `dev_production_generator.py` génère (Sprint 4.9) :**
`vercel.json` · `.env.production.local` · `migrate.sh` · `lib/logger.ts` · `app/error.tsx` · `app/[route]/error.tsx` · `schema.prisma` enrichi (@@index FK)

---

## INNOVATIONS ARCHITECTURALES — Catalogue A→H

| # | Nom | Sprint | Description |
|---|-----|--------|-------------|
| A | Type Safety Chain Validator | 4.8D | Valide SerializedXxx → service → actions → page-client avant build |
| B | App Usefulness Scorer | 4.8D | Score composite : build(40%) + flows(30%) + quality(20%) + spec(10%) |
| C | Progressive Validation | 4.9B | `tsc --noEmit --isolatedModules` après chaque write_file() LLM |
| D | Smart Context Injection | 4.9B | Standards pertinents uniquement selon le rôle du fichier |
| E | Semantic Reviewer | 4.8A ✅ | Deux couches : déterministe + LLM sémantique |
| F | Feature Module Registry | 4.7E ✅ | Registre JSON déclaratif → fin des side-effect imports |
| G | LevelAManifest + CONTRACT.md | 4.7E ✅ | Toutes méthodes service exposées → LLM ne devine plus |
| H | Learner-Driven Standards | 4.8D | Violations quality_validator → Learner → standards Qdrant |

---

## JALONS v3.5

| Date cible | Sprint | Livrable clé | Signal mesurable | Statut |
|------------|--------|-------------|-----------------|--------|
| Mars 2026 | 0–3 | Pipeline end-to-end | build_success reproductible | ✅ |
| Avril 2026 | 4 | Gate décisionnel + contracts v2 | spec_coverage + requirements | ✅ |
| Avril 2026 | 4.5 | Journey Validator | user_flows_covered 100% Type A | ✅ |
| Mai 2026 | T2–T5 | agents/core/ + StackAdapter + Docker | Refacto sans régression | ✅ |
| Mai–Juin 2026 | **4.7** | Form Generator + Pages complètes + F/G innovations | `is_useful_app: true` ≥3 runs A | ✅ |
| Juin 2026 | **4.8A** | Reviewer deux couches | findings réels, security=100 | ✅ |
| Juin 2026 | **4.8A'** | correction_pass redesign | trigger sur findings, rebuild sans npm install | ✅ |
| Juin 2026 | **4.8C** | FactoryRunReport + learner_suggestions.json | rapport lisible après chaque run | ✅ |
| Juin 2026 | **4.8B** | QA Jest smoke tests | `tests_passed: true` ≥1 run | ⏳ |
| ~~Juillet 2026~~ | ~~**4.9A**~~ | ~~FrontendAgent ReAct~~ | ~~agent utilise ≥1 lib externe~~ | ❌ ANNULÉ |
| ~~Juillet 2026~~ | ~~**4.9B**~~ | ~~FrontendAgent ProjectSpec~~ | ~~frontend différencié par domaine~~ | ❌ ANNULÉ |
| Juin 2026 | **Design système intégré** | 7 presets domaine + CSS vars + shadcn dans pipeline | apps avec couleurs/fonts/density par domaine | ✅ |
| Juin 2026 | **Plan6 A1-A6** | Fixes déterministes : delete, navigation, IDOR, datasource | validation en cours sur nouveaux runs | ✅ commité / ⏳ validé |
| ~~Juillet 2026~~ | **D25-D28 (immédiat)** | Fixes templates : H1 statique, __esModule, checkbox, post-auth | 4 fixes indépendants | ✅ 06 Juil 2026 |
| Juillet 2026 | **D23-D24** | Private list cards + layout_hint LLM | variation structurelle par domaine | ⏳ |
| À la demande | **4.9C–E** | QA visuel (la scène) + correction QA + Deploy — **en parallèle de l'expansion, non bloquant** | `qa_score ≥ 0.8`, URL Vercel | ⏳ |
| Juillet 2026 | **5** | Type D-complet (SEO + M2M + rich textarea) | validé sur abo/atelier/club — **lecture du code**, pas métriques | ✅ **16 Juil** |
| ~~Août~~ **Juil 2026** | **6** | Type I Workflow | garde de transition + verrou d'édition **lus dans le code** (build+tsc OK) | 🔵 **~90 % — en avance** |
| **Juil 2026** | **Scène-A** | **Miroir français** : déclaration re-rendue en clair + unsupported[], montrée AVANT de construire | client valide l'intention en 30 s | ⏳ **PROCHAIN — meilleur ratio** |
| **Juil–Août 2026** | **Scène-B** | **Aperçu peuplé** : seed + `npm run dev` + humain clique | « le client voit marcher » sans robot | ⏳ |
| **Août+ 2026** | **Scène-C** (ex-4.9C) | **Robot Playwright** (régression) — après spike ½ j sur l'auth Clerk | vidéo navigable, régression auto | ⏳ après A+B |
| ~~Septembre~~ | **7** | Type K RBAC | — | ⏸️ **après la Scène** (voir §7 : on fabrique des cases **à l'aveugle**, aucun brief client réel) |
| Septembre 2026 | **7** | Type K RBAC (guards rôle + nav conditionnelle) | reviewer 0 finding rôle | ⏳ |
| Octobre 2026 | **8** | Type H Dashboard (AggregationModule + recharts) | agrégations en DB + charts rendus | ⏳ |
| Novembre 2026 | **9** | Type G Booking + Type E fondations (Decimal, $transaction) | `is_useful_app: true` booking brief | ⏳ |
| Décembre 2026 | **10** | Type E complet (Stripe) + Type F + préparation B | e-commerce `is_useful_app: true` | ⏳ |
| 2027 | 11+ | Type B multi-tenant + C Marketplace + J + Stack 2 + Démo 50 | 50 projets déployés, 80% score≥70 | ⏳ |

---

## DETTE TECHNIQUE CONNUE

| # | Description | Sprint cible | Statut |
|---|-------------|-------------|--------|
| D1 | `(data as any)` dans les services | 4.7A (C1) | ✅ |
| D2 | IDOR sur update (userId absent du where) | 4.8A | ✅ reviewer détecte |
| D3 | `updatedAt` manquant sur certains modèles | 5 | ⏳ |
| D4 | Pagination hardcodée `take:20` dans `getPublished` | 4.7D (F8) | ⏳ |
| D5 | User model orphelin (no FK vers entités) | Design decision 7 | ⏳ |
| D6 | GitHub agent désactivé | Réactivation conditionnelle 6 | ⏳ |
| D7 | `test_sprint1_validation.py` legacy | Archiver 5 | ⏳ |
| D8 | `learner_agent_contract.json` zombie | Supprimer 5 | ⏳ |
| D9 | `reviewer_activity` score 100 sur apps défectueuses | 4.8A | 🔴 **NON RÉSOLU — réfuté 16 Juil** : COHERENT 100/100 + 0 finding sur `notes-frais`, app qui laissait créer une note déjà « Remboursée » et violait les 2 règles explicites du brief. Le marquage ✅ était faux. Cause structurelle : le reviewer inspecte la sortie d'un compilateur (correcte par construction) → il n'a rien de réel à trouver. Voir RELECTURE TERRAIN §5 |
| D10 | `journey_validator` sous-compte les flows couverts | 4.7A (D1) | 🔴 **PIRE : il CRASHE** — `[dev_graph] journey_validator échoué : name '_path_of' is not defined` (16 Juil). L'erreur est avalée en WARNING **et la métrique affiche quand même `user_flows_coverage: 1.0` (3/3)**. Un instrument mort qui applaudit |
| **D29** | `requirements` = **liste de fichiers** (`"Page: /x"`, `"Modèle Prisma: X"`), aucune règle métier → « 6/6 met » ne prouve que l'existence de 6 fichiers. `spec_coverage 1.0` idem | Voir §5 | 🔴 16 Juil |
| **D30** | `rejectionReason` saisissable à la **création** — champ appartenant à une **transition** (« refusée AVEC UN MOTIF »), pas à la création. Case `state_fields` créée, **branchement à finir sur `transitionTo`** | Type I | ⏳ 16 Juil |
| **D31** | KPI déclarables **seulement sur pages custom** (`pages_detail`) → « le total en attente de remboursement » demandé par le client **s'évapore** sur une page `list` déterministe. Même maladie « pas de contenant » | Type H | 🔴 16 Juil |
| **D32** | `amount Float` pour de l'argent (architect) → bugs d'arrondi classiques. Devrait être `Decimal` (L10/D17 connexes) | 9B | ⏳ 16 Juil |
| **D33** | `SERVICE_METHOD_REGISTRY` sur-liste `getBySlugWithRelations` sous `if_slug` seul, alors que `slug.py:64` ne l'écrit que si **slug ET relations** → mensonge latent (TS2339 possible sur modèle slug-sans-relations) | — | ⏳ 16 Juil (latent, non déclenché) |
| **D34** | `dev_service_spec.py` est un **miroir hand-maintained** du générateur (son propre docstring l'avoue : « si une méthode est ajoutée dans le générateur, l'ajouter ici **aussi** ») → alimente CONTRACTS.md. C'est ce mécanisme qui a produit le fantôme `getPublished` dans **6 endroits écrits à la main**. Remède : faire **dériver** le spec du registre + garde d'égalité | — | ⏳ 16 Juil |
| **D35** | `scripts/test_generators.py` : **rien ne le lance** (aucune CI, aucun appel dans le dépôt). Dernière modif **20 juin** vs `crud.py` **9 juil** → déjà dérivé. Ignore `enriched_spec` → tout ce que la couche sémantique pilote (`status_flows`, `currency`, `textarea`) n'est testé par **personne**. **Prérequis : avoir quelque chose qui lance les tests — pas en écrire davantage** | Voir §5 | 🔴 16 Juil |
| D11 | Progressive Validation absente du graphe | 4.9B (F1) | ⏳ |
| D12 | `quality_validator.py` : appel bloquant async + zombie file | 4.7D (F3/F4) | ⏳ |
| D13 | `getAllByUser` absent de `service_map_str` | 4.7E (G) | ⏳ |
| D14 | Feature modules via side-effect imports | 4.7E (F) | ⏳ |
| D15 | `SpecOutput` contrat zombie | Nettoyer 5 | ⏳ |
| D16 | `update`/`create` retournent `Promise<ModelName>` pas `SerializedXxx` | 4.7D (F9) | ⏳ |
| D17 | Decimal non sérialisé dans `_serialize` | 4.7D (F10) | ⏳ |
| D18 | Enum : union literals au lieu d'imports Prisma | 5 | ⏳ |
| D19 | `prebuild_pipeline.py` orchestrateur séparé de `dev_graph` | 4.9B | ⏳ |
| D20 | `module_search`/`status_flow` lisent heuristiques au lieu de `enriched_spec.features` | 4.9 (DY1) | ✅ 06 Juil (modules supprimés — unification DY6) |
| D21 | `rules_dev.md` : ~25 règles sur fichiers déterministes = bruit LLM | 4.9 (DY3) | ⏳ |
| D22 | `role_rag_queries` "service" et "actions" actifs mais inutiles (déterministes) | 4.9 (DY7) | ⏳ |
| D23 | `list_style: "cards"` dans presets mais aucun template list cards privé → toujours table | `dev_form_generator.py` + `list_client_card_grid.tsx.j2` | 4.9 |
| D24 | `design_block` LLM sans `layout_hint` → pages custom sans guidance structurelle | `dev_prompts.py` | 4.9 |
| D25 | `<h1>Post</h1>` hardcodé dans template détail au lieu de `{{ title_detail }}` | `detail_client.tsx.j2` | Immédiat |
| D26 | `__esModule: true` manquant dans mock Prisma `prompts/base/qa.md` → 2 tests ❌ par run | `prompts/base/qa.md` | Immédiat |
| D27 | Checkbox boolean affiché brut ("true"/"false") au lieu de badge visuel dans liste | `list_client.tsx.j2` | Immédiat |
| D28 | Post-auth redirect vers `/blog` au lieu de `/dashboard` dans template `.env.local` | template `.env.local` | Immédiat |

---

## DYSFONCTIONNEMENTS CONNUS — Référence technique

| # | Dysfonctionnement | Fichiers concernés | Sprint |
|---|---|---|---|
| ~~DY1~~ | ~~Module system mort : heuristiques au lieu de features[]~~ **✅ RÉSOLU 06 Juil 2026 par l'unification DY6** — la feature `search` est consommée par le form generator depuis `enriched_spec.has_feature()` ; `status` reste structurel (ctx.has_status, déterministe) | `dev_form_generator.py` | ✅ |
| DY2 | Fracture CROSS_ENTITY : `_gen_page_full()` deux fetches séparés au lieu de `getByIdWithRelations` — `module_detail_with_children` neutralisé | `dev_pages_generator.py`, `module_detail_with_children.py` | 4.9 |
| DY3 | `rules_dev.md` : 36 règles dont ~25 sur fichiers déterministes (services, actions) = bruit dans le contexte LLM | `prompts/rules_dev.md` | 4.9 |
| DY4 | `code_role_hints` JSON et `rules_dev.md` se chevauchent — une règle dans deux endroits | `config/stacks/*.json`, `prompts/rules_dev.md` | 4.9 |
| DY5 | Architect génère `pages_detail` pour toutes les pages y compris les déterministes (inutile) | `agents/architect.py` pages_detail_node | 4.9 |
| ~~DY6~~ | ~~Générateurs et modules : deux systèmes non unifiés~~ **✅ RÉSOLU 06 Juil 2026** — les listes ont UN renderer unique (`_gen_list_client`, arbre public→status→search→card-grid) ; `module_status_flow` + `module_search` SUPPRIMÉS (leur double-rendu divergent causait la mort silencieuse : TypeError design_system + template search jamais valide + card_cls). `list_client_search.tsx.j2` fusionné dans `list_client.tsx.j2` (bloc has_search). Le registre feature_modules reste pour les vrais modules (detail_with_children, futur calendar_view) | `dev_form_generator.py` | ✅ |
| DY7 | `role_rag_queries` "service" et "actions" actifs mais services/actions sont déterministes → requêtes Qdrant inutiles | `config/stacks/nextjs-clerk-prisma.json` | 4.9 |

---

## DÉCISIONS ARCHITECTURALES (log permanent)

| Date | Décision | Raison |
|------|----------|--------|
| Fév 2026 | Stack-as-Config JSON | PRINCIPE 1 — zéro logique stack en Python |
| Mars 2026 | Guards regex → WARN | TypeScript/Prisma sont arbitres |
| Mars 2026 | Sprint 4.6 abandonné | LLM inline supervisors : angles morts partagés |
| Mars 2026 | requirements[] déterministe | Élimine ghost success |
| Avril 2026 | StackAdapter pattern | Multi-stack sans toucher au moteur |
| Avril 2026 | agents/core/ extraction | Stack-agnostique réutilisable |
| Mai 2026 | Reviewer post-build | Scope clos, modèle différent, advisory |
| Mai 2026 | GitHub agent mis en PAUSE | Éviter création de dizaines de repos pendant la phase test |
| Mai 2026 | Reséquençage : complétion Level A avant Level B | PRINCIPE 6 — Type D révèle formulaires non fonctionnels |
| Mai 2026 | Form Generator déterministe (Pilier 1) | Les formulaires sont de la donnée structurée |
| Mai 2026 | Extension avant limitation (PRINCIPE 7) | Tout type d'app a une colonne vertébrale déterministe |
| Mai 2026 | Déploiement standard : Vercel + Neon PostgreSQL | Connection pooling natif Prisma, zero-config Next.js |
| Mai 2026 | Sprint 4.9 : Production Readiness Layer | Gap entre build_success et app production-ready |
| Mai 2026 | Vision affirmée : agentic startup opérée par un humain unique | Opérateur recueille briefs, factory génère + déploie |
| **Juin 2026** | **correction_pass déclenché sur `findings` (pas `targeted_fixes`)** | **`targeted_fixes` toujours vide → SKIPPED_NO_FIXES systématique** |
| **Juin 2026** | **Guide de rédaction des briefs (`brief_guide.md`)** | **Briefs libres → GENERATION_ERROR — 4 règles fondamentales obligatoires** |
| **Juin 2026** | **reviewer génère `targeted_fixes` depuis Layer 1 WRONG_AUTH/MISSING_AUTH** | **LLM ne peut pas produire ces fixes fiablement — Layer 1 déterministe** |
| **Juin 2026** | **BrowserUse/noVNC retirés — QA visuel sur host Playwright** | **Docker aveugle → Playwright sur Windows, browser visible en direct** |
| **Juin 2026** | **PRINCIPE 8 — La Scène avant le Déploiement** | **Deploy = conséquence d'une validation client, pas étape automatique** |
| **Juin 2026** | **Sprint 4.9 reséquencé : Frontend → QA visuel → Deploy** | **Build_success sans frontend décent n'est pas un livrable client** |
| **Juin 2026** | **VisualSpec inline rejeté — FrontendActivity post-traitement adopté** | **Le frontend ≠ couche CSS : animations, graphiques, images, layouts — trop vaste pour une injection dans le pipeline de génération. Post-traitement sur app fonctionnelle = approche correcte.** |
| **Juin 2026** | **FrontendActivity à 3 couches (v3.6) → pivot FrontendAgent ReAct (v3.7)** | **Pipeline déterministe trop limitatif : 6 composants fixes, palette imposée, aucun graphique/animation. Les LLMs connaissent shadcn/ui, Framer Motion, Recharts mieux que tout pipeline statique. Un agent ReAct avec outils produit un résultat indifférenciable d'un développeur frontend senior.** |
| **Juin 2026** | **FrontendAgent lit brief + ProjectSpec directement (Option 2)** | **Planifié en v3.7 puis ANNULÉ — remplacé par design_resolver déterministe.** |
| **Juin 2026** | **Pas de DALL-E ni génération d'images dans FrontendAgent** | **Décision conservée : images = contenu client. Illustrations = SVG inline. Icônes = Lucide React.** |
| **Juin 2026** | **FrontendAgent ReAct (4.9A v3.7) ANNULÉ — design intégré dans pipeline déterministe** | **Raison : coût LLM non justifié, contexte dev préservé, design_resolver + CSS vars suffisants pour variation par domaine. Limitation acceptée : structure identique (sidebar, tables).** |
| **10 Juin 2026** | **Plan6 — Refactorisation majeure (Blocs A–D)** | **6 bug fixes déterministes (A1-A6), Type K RBAC dans typeApps, service_modules/ assembler, architect décomposé (domain_interpreter + page_planner + spec_enricher).** |
| **Juin 2026** | **Design system intégré dans dev_graph (Sprint 4.9A replacement)** | **design_resolver (7 presets) → dev_design_system_generator (CSS vars + shadcn) → dev_layout_generator (DashboardShell) → dev_form_generator (tokens sémantiques). Limitation D23 : pas de variant cards pour listes privées.** |
| **06 Juil 2026** | **Priorité EXPANSION avant la Scène (4.9C) — sprints 5-10 reséquencés D→I→K→H→G→E→B** | **Lecture complète 8-niveaux : L3/L5/L6/L8/L14 déjà résolues dans le code (typeApps.md v1.0 obsolète). Type I quasi débloqué (semantic_annotator extrait déjà l'ordre workflow). Type K = concept rôle absent partout (chantier Lot 2). 4.9C reste disponible à la demande, non bloquant.** |
| **06 Juil 2026** | **Règle des 4 lots pour toute expansion (typeApps.md v2.0 §3.5)** | **Squelette + Connaissance + Design + Garde-fous, jamais l'un sans les autres + passe de cohérence. Piège identifié : rules_dev règle 12 (« agrégations = getAll + calcul TS ») contredirait l'AggregationModule du Type H si non réécrite — toute expansion inclut la mise à jour des instructions existantes, pas seulement l'ajout.** |

---

## GUIDE DE RÉDACTION DES BRIEFS

Référence complète : `factory-sprint0/docs/brief_guide.md`

**4 règles fondamentales (structurelles) :**
1. **Entités nommées** avec champs clés explicites (pas "je gère mes données")
2. **Relations parent → enfant** dans ce sens avec FK nommée (`categoryId`, `userId`)
3. **Auth explicite** page par page : *"sans connexion"* → `auth_required: false` / *"après connexion"* → `auth_required: true`
4. **Un seul acteur** par app (deux acteurs sans ownership clair = données cross-user)

**5e règle — Ton visuel (optionnel, une phrase) :**
Si absent : le moteur déduit depuis le type d'app (layout_type + theme_tone par défaut = professional).
Si présent : une seule indication suffit — le moteur fait le reste.
```
"outil de gestion sobre et efficace"   → professional, layout data
"app créative et dynamique"            → colorful, layout app
"blog / recettes / articles"           → warm, layout content
"tableau de bord analytique"           → professional, layout dashboard + KPIs auto
"galerie / portfolio / vitrine"        → minimal, layout showcase
```

**Signaux d'alerte :** deux acteurs sans propriété claire · route publique non nommée · entité sans champs · fonctionnalité temps-réel mentionnée · logique conditionnelle complexe (premium, rôles multiples).

---

## TECHNOLOGIES PAR SPRINT

| Technologie | Problème résolu | Sprint | Effort | Priorité |
|---|---|---|---|---|
| **Structured outputs gpt-4o** (`json_schema`) | QA JSON malformé | 4.8B | 1h | 🔴 Maintenant |
| **Semgrep** (déjà dans repo) | Sécurité statique pipeline | 4.8B | 30min | 🔴 Maintenant |
| **FrontendAgent (LLM ReAct loop + tools)** | Apps fonctionnelles visuellement ternes — agent autonome lit brief+spec, choisit ses libs, réécrit les pages | 4.9A | 4j | 🔴 Sprint 4.9A |
| **shadcn/ui** | Composants React production-ready, LLM les connaît parfaitement, CLI `npx shadcn@latest add` | 4.9A | 30min | 🔴 Sprint 4.9A |
| **Framer Motion** | Animations React — variants, transitions, AnimatePresence — LLM code directement | 4.9A (si agent le choisit) | npm add | 🔴 Sprint 4.9A |
| **Recharts / Tremor** | Graphiques React — BarChart, LineChart, AreaChart — pour briefs dashboard/analytics | 4.9A (si agent le choisit) | npm add | 🔴 Sprint 4.9A |
| **Lucide React** | 1500+ icônes SVG npm, zero config, LLM connaît tous les noms | 4.9A | npm add | 🔴 Sprint 4.9A |
| **Tailwind CSS + postcss** | Base CSS — déjà ajouté au package.json template en v3.6 | 4.9A ✅ skeleton | 2h | 🔴 Sprint 4.9A |
| **Playwright Python (host Windows)** | QA visuel E2E — browser visible, vidéos — hors Docker | 4.9C | 2j | 🔴 Sprint 4.9C |
| **Neon API + Clerk API + Vercel CLI** | Provisioning infra client automatisé (DB, domaine, deploy) | 4.9E | 2j | 🟠 Sprint 4.9E |
| **Langfuse** | Observabilité : quels standards RAG sur quels runs | 4.9 | 1j | 🟠 Sprint 4.9 |
| **Mesure de l'apport RAG (A/B)** | ⚠ PROUVÉ 9 Juil : les standards Qdrant sont bien INJECTÉS (logs mandatory-rag, 4/contexte) mais leur IMPACT causal est NON MESURÉ — les mêmes leçons sont enseignées en triple (stubs déterministes + rules_dev + contrats de page), donc le RAG est « une voix dans un chœur ». Faire un A/B : même brief avec/sans standards → diff du code généré. Décider ensuite : garder minimal (niche zone 3 = code vraiment imprévisible), étendre, ou retirer. NE PAS étendre le RAG aveuglément avant cette mesure. | 5 | 1j | 🟡 Sprint 5 |
| **Track 2 Phase-Aware** | System prompt dev LLM surchargé → ~1500 tokens statiques | 4.9 | 3j | 🟠 Sprint 4.9 |
| **Few-shot examples → JSON externe** | Prompt architect surchargé (~4000 → ~1500 tokens) | 4.9 | 4h | 🟠 Sprint 4.9 |
| **fast-check** | Property-based testing : "getAll(userId) ne retourne jamais données cross-user" | 5 | 1j | 🟡 Sprint 5 |
| **LLM-as-Judge (ragas/promptfoo)** | Qualité fonctionnelle non mesurée par Jest | 5 | 2j | 🟡 Sprint 5 |
| **DSPy (Stanford)** | Optimisation automatique des prompts architect | 5-6 | 1 sem | 🟡 Sprint 5+ |
| **Chromatic + Storybook** | Régression visuelle des templates Jinja2 entre versions | 5 | 2j | 🟡 Sprint 5 |
| **Style Dictionary + shadcn** | UI design system client (Figma tokens → Tailwind) | 8+ | Élevé | 🟢 Long terme |
| **Knowledge Graph (Neo4j)** | Standards structurés post-Qdrant : modéliser les relations entre règles | 6+ | Élevé | 🟢 Long terme |
| **RLAIF** | Auto-amélioration prompts depuis `is_useful_app` + `reviewer_score` | 8+ | Très élevé | 🟢 Long terme |

**Règle :** ne pas chercher un service externe pour remplacer le Learner ou le QA agent — trop spécifiques à l'architecture factory pour être délégués à des outils génériques.
