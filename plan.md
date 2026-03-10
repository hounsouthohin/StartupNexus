# Plan de Stabilisation — Software Agent Factory
# Version v3 — validée à 100% (Codex + Claude Code, 08 Mars 2026)
# Auteur original : Codex | Amendements v2 : Claude Code | Amendements v3 : Codex (justifiés inline)

---

## Diagnostic système — Pourquoi on est là

Nous sommes arrivés à cette situation à cause d'un enchaînement systémique, pas d'un seul bug :

1. Le pipeline a été pensé d'abord "génération LLM", puis renforcé par couches successives de guards.
2. Ces guards ont amélioré la sécurité, mais ils sont surtout bloquants (négatifs), pas assez constructifs (guidage fort vers artefacts corrects).
3. La logique requirements a été dupliquée (`requirements_gate` vs `spec_coverage`) avec des règles différentes, créant des signaux incohérents.
4. L'orchestration finale n'a pas été entièrement déterminisée au départ (place laissée à des sorties textuelles LLM dans la boucle).
5. Plusieurs composants ont évolué séparément (dev agent, activity, contrats), provoquant des désalignements de schéma et de métriques.
6. Le cœur reste partiellement couplé à la stack Next.js, ce qui rend l'évolution multi-stack plus fragile et plus lente.
7. Résultat opérationnel : le système sait mieux détecter et bloquer les artefacts invalides, mais converge mal vers une solution complète avant `MAX_ITERATIONS`.
8. **[Amendement Claude Code v2]** Le contenu des fichiers dans le dict `files` n'est pas normalisé. Le LLM peut écrire des retours à la ligne sous forme de séquences littérales `\n` (deux chars) plutôt que de vrais caractères Unicode 0x0A. Les guards regex échouent silencieusement sur ce contenu.

**En bref** : on a construit une bonne "barrière de sécurité", mais pas encore une "chaîne de convergence déterministe" de bout en bout.

---

## Plan Béton (15 jours)

> **[Amendement Codex v3 — point 6]** Sprint A replanifié sur 8 jours (était 7). 1 buffer jour ajouté car T000 + T002 + T004 + T010 en parallèle = charge trop dense pour 7 jours sans marge. Un plan sans buffer n'est pas béton, c'est un plan optimiste.

1. **Freeze contrôlé (J1)**
   - Stopper les nouveaux features.
   - Travailler sur une branche `stabilization`.
   - Objectif unique : fiabilité pipeline.

2. **Baseline métriques (J1) — [Ajout Codex v3, point 2]**
   - Capturer les KPI initiaux sur 5 runs identiques AVANT tout changement.
   - Métriques : `build_attempted rate`, `build_success rate`, `avg_iterations`, `root_cause distribution`, `final_status coherence rate`.
   - **Pourquoi l'original ne l'avait pas** : Sans baseline, impossible de prouver que Sprint A a amélioré quoi que ce soit. Le harness T011 mesure l'état *après*, pas le delta. Une amélioration non mesurée ne peut pas être défendue.

3. **Source de vérité unique requirements (J2-J4)**
   - Extraire la logique de mapping requirements dans un module unique (`requirements_engine.py`).
   - `requirements_gate` et `spec_coverage` doivent appeler exactement ce module.
   - Fin des verdicts divergents.

4. **Machine d'états déterministe (J2-J5)**
   - Formaliser états : `GEN -> STRUCTURAL_GATES -> REQUIREMENTS_GATES -> BUILD -> TEST -> FINAL`.
   - `FINAL` calculé par code uniquement, jamais par prose LLM.
   - Si `build_attempted=false`, statut final doit être explicitement `NOT_BUILT_BY_GATE`.
   - **[Amendement Claude Code v2]** Budget token par phase formalisé comme contrainte de la machine (phase 1 : 6 000 tokens, phase 2 : 14 000 tokens).

5. **Architecture multi-stack modulaire (J4-J7)**
   - Créer `StackAdapter` + `GuardRegistry`.
   - Déplacer les guards Next.js hors du cœur.
   - Garder dans le core seulement les guards globaux (séquence, contrats, limites).

6. **Guards constructifs (J4-J7)**
   - Pour chaque violation critique : fichier invalide détecté + fichier attendu + patch cible (template path).
   - Option : auto-write des fichiers standards via templates après 2 tentatives LLM échouées.
   - **[Amendement Claude Code v2]** Avancé en Sprint A : guider le LLM réduit les itérations perdues immédiatement.

7. **Robustesse LLM/infra (J6-J8)**
   - Gérer 429 : retry exponentiel + fallback model.
   - Timeout et retry policy explicites par étape.

8. **Harness de déterminisme bloquant (J7-J10)**
   - Lancer 20 runs sur mêmes briefs.
   - KPIs bloquants (voir définitions formelles section KPI ci-dessous).
   - CI échoue si seuils non atteints.

9. **Canary rollout (J9-J10) — [Ajout Codex v3, point 4]**
   - Activer les nouveaux gates/state machine sur 10% des runs avant déploiement global.
   - **Pourquoi l'original ne l'avait pas** : Un plan qui active directement 100% des nouveaux gates sans validation intermédiaire transforme une amélioration en risque de régression généralisée. Le canary rollout permet de vérifier que les nouveaux gates ne bloquent pas de nouveaux cas valides avant d'éteindre les anciens.

10. **Scoreboard exécutif (J9-J11)**
    - Dashboard quotidien : success rate, max_iterations rate, top root causes, temps moyen/run, drift par stack.

11. **Runbook opérationnel (J11-J12)**
    - Procédures incident : `429`, gate bloqué, contrat invalide, rollback, hotfix.
    - Procédure ajout de stack.

12. **Reprise progressive (J13-J15)**
    - Réactiver features seulement après 3 jours de stabilité KPI.
    - 1 changement structurel max/jour.
    - Postmortem court à chaque régression.

---

## Définitions formelles des KPIs — [Ajout Codex v3, point 3]

> **Pourquoi l'original ne les définissait pas** : Le KPI `build_attempted >= 95%` est manipulable si "gate légitime" n'est pas défini. Un gate qui bloque tout peut atteindre 95% en étant simplement désactivé. Sans définition formelle, la métrique ne prouve rien.

### `build_attempted rate`
- **Numérateur** : runs où `build_attempted = true`
- **Dénominateur** : tous les runs
- **Seuil** : >= 95%

### "Gate légitime" (exclusion du dénominateur autorisée)
Un gate est **légitime** (et peut exclure le run du calcul `build_attempted`) uniquement si :
1. Le requirement bloqué est **mappable** (Règle A/B/C du `requirements_engine`) ET
2. Le fichier attendu est **absent de `combined_files`** ET
3. Le gate a émis un message constructif (fichier attendu + template proposé) ET
4. Le run a atteint **au moins 3 itérations** (pas un blocage immédiat au premier tour).

Tout autre blocage est compté comme `build_attempted = false` et dégrade la métrique.

### `final_status coherence rate`
- **Définition** : % de runs où `final_status` correspond exactement aux events tools (`build_attempted`, `build_success`, `tests_passed`).
- **Seuil** : 100% (0 tolérance).

### `gate divergence rate`
- **Définition** : % de runs où `requirements_gate` et `spec_coverage` donnent des verdicts contradictoires sur les mêmes requirements.
- **Seuil** : 0%.

---

## Priorité immédiate (ordre exact dès maintenant)

1. **T000-B** Fix normalisation contenu ciblée (voir ticket, remplace T000 original).
2. **T000-BL** Baseline métriques sur 5 runs.
3. Unifier `requirements_gate` + `spec_coverage`.
4. Verrouiller machine d'états et final status tool-driven.
5. Mettre en place harness 20 runs avec seuils bloquants formels.
6. Ensuite seulement optimiser modèle/prompts.

---

## Backlog Exécutable — Tickets avec Definition of Done

---

### T000-B — Fix Normalisation Contenu Ciblée

> **[Remplacement de T000 original — Amendement Codex v3, point 1]**
> L'original (T000) proposait un `replace("\\n", "\n")` global sur tout le contenu de fichier.
> **Pourquoi remplacé** : Un replace global corrompt les chaînes JSON légitimes qui contiennent `\n` comme donnée (ex : un champ de spec, un message d'erreur JSON stocké dans un fichier). La normalisation doit être ciblée par type de fichier et vérifiée par heuristique avant application.

- **Priority**: P0
- **Estimate**: 0.5j *(était 0.25j dans T000 — ajout tests heuristique)*
- **Owner**: Backend Eng
- **Depends on**: none
- **Description**:
  - Créer `normalize_file_content(path: str, content: str) -> str` dans `requirements_engine.py`.
  - Logique : si `path` se termine par `.prisma`, `.ts`, `.tsx`, `.js`, `.py`, `.md` ET si le contenu ne contient aucun vrai `\n` (char 0x0A) ET si le ratio `\\n` / longueur > 0.01 → remplacer `\\n` par `\n` et `\\t` par `\t`.
  - Appliquer cette fonction dans `_requirements_gate()` et `compute_spec_coverage()` avant tout regex.
  - Ne jamais normaliser les fichiers `.json` (risque corruption légitime).
- **DoD**: Run avec `prisma/schema.prisma` double-encodé → Rule A passe. Fichier `.json` avec `\\n` légitimes → non modifié. Tests unitaires sur 5 cas-limites.

---

### T000-BL — Baseline Métriques

> **[Ticket ajouté — Amendement Codex v3, point 2]**
> **Pourquoi absent de l'original** : Sans baseline, impossible de mesurer le gain de Sprint A. Le plan calculait les seuils sans point de départ connu.

- **Priority**: P0
- **Estimate**: 0.25j
- **Owner**: QA/Backend
- **Depends on**: none (doit tourner AVANT tout changement de code)
- **Description**: Lancer 5 runs identiques (brief : personal-blog) sur l'état actuel du code. Capturer et stocker : `build_attempted rate`, `build_success rate`, `avg_iterations`, distribution `root_cause_category`, `final_status coherence rate`.
- **DoD**: Fichier `baseline_kpis.json` en dépôt avec les 5 runs + métriques agrégées. Ce fichier devient la référence pour T011.

---

### T001 — Freeze Stabilisation

- **Priority**: P0
- **Estimate**: 0.5j
- **Owner**: CTO/Lead Eng
- **Depends on**: none
- **Description**: Geler les nouvelles features sur branche `stabilization`, policy "stability-first".
- **DoD**: Guide de merge publié. Seuls tickets P0/P1 de stabilité autorisés.

---

### T002 — Requirements Engine Unifié

> **[Amendement Claude Code v2]** Estimate 1.5j → 3j. Couplage profond dans 3 fichiers + tests intégration nécessaires.

- **Priority**: P0
- **Estimate**: 3j
- **Owner**: Backend Eng
- **Depends on**: T001
- **Description**: Créer `requirements_engine.py` — source unique de mapping/validation. `requirements_gate` dans `dev.py` et `compute_spec_coverage` dans `dev_test_agent.py` appellent ce module. Intègre `normalize_file_content` de T000-B.
- **DoD**: Plus de logique dupliquée. Mêmes inputs → mêmes verdicts. Suite de tests sur 10 requirements types.

---

### T003 — Alignement `spec_coverage`

> **[Amendement Claude Code v2]** Estimate 1j → 1.5j. Re-test d'intégration obligatoire après T002.

- **Priority**: P0
- **Estimate**: 1.5j
- **Owner**: Backend Eng
- **Depends on**: T002
- **Description**: Remplacer matching permissif `any(expected in fp ...)` par exact-match aligné sur `requirements_engine.py`.
- **DoD**: 0 divergence `requirements_gate` vs `spec_coverage` sur suite de tests.

---

### T004 — State Machine Déterministe

> **[Amendement Claude Code v2]** Budget token ajouté comme livrable de la state machine.

- **Priority**: P0
- **Estimate**: 2j
- **Owner**: Backend Eng
- **Depends on**: T001
- **Description**: Implémenter transitions `GEN -> STRUCT_GATES -> REQ_GATES -> BUILD -> TEST -> FINAL`. Final status calculé sans texte LLM. Budget token par phase en config (phase 1 : 6 000, phase 2 : 14 000).
- **DoD**: Transition logs explicites + final status calculé par état + budget token en config.

---

### T005 — Final Status Tool-Driven

- **Priority**: P0
- **Estimate**: 1j
- **Owner**: Backend Eng
- **Depends on**: T004
- **Description**: Standardiser message final par état (`NOT_BUILT_BY_GATE`, `BUILD_SUCCESS`, `BUILD_FAILED`, `MAX_ITER_REACHED`). Impossible d'avoir message "build fix" si `build_attempted=false`.
- **DoD**: `final_message` toujours issu d'un template code, jamais texte LLM quand `build_attempted=false`.

---

### T006 — Contrats Erreur/Sortie

- **Priority**: P0
- **Estimate**: 1j
- **Owner**: Backend Eng
- **Depends on**: T001
- **Description**: Aligner `output_schema`, `error_schema` et payload runtime dans tous les contrats JSON.
- **DoD**: 0 `ValidationError` de schéma sur chemins succès et échec.

---

### T007 — Retry/Backoff 429 + Fallback

- **Priority**: P1
- **Estimate**: 1j
- **Owner**: Platform Eng
- **Depends on**: T001
- **Description**: Retry exponentiel + fallback model. Run ne casse plus immédiatement sur 429 transitoire.
- **DoD**: Simulation 429 → retry transparent, run continue.

---

### T008 — Guard Registry Multi-Stack

- **Priority**: P1
- **Estimate**: 2j
- **Owner**: Backend Eng
- **Depends on**: T004
- **Description**: Séparer guards globaux et guards stack-spécifiques. Registre `stack_id -> guard list`. `dev.py` non couplé Next.
- **DoD**: Guards Next.js isolés, core sans règles Next hardcodées.

---

### T009 — Stack Adapter Interface

- **Priority**: P1
- **Estimate**: 2j
- **Owner**: Backend Eng
- **Depends on**: T008
- **Description**: Interface standard (`paths`, `commands`, `artifacts`, `conventions`). Stack Next migrée sur adapter. Ajout d'une 2e stack sans modifier core.
- **DoD**: Protocole "nouvelle stack en <1 jour" validé.

---

### T010 — Guards Constructifs (Templates)

> **[Amendement Claude Code v2]** P1 → P0, Sprint C → Sprint A. Guider le LLM = convergence immédiate, avant multi-stack.

- **Priority**: P0
- **Estimate**: 1.5j
- **Owner**: Fullstack Eng
- **Depends on**: T004
- **Description**: Pour chaque violation critique : invalide → attendu → template cible. Auto-write après 2 tentatives LLM échouées.
- **DoD**: Chaque violation P0 renvoie "invalid → expected → template". Itérations perdues sur violations connues ≤ 1.

---

### T011 — Determinism Harness 20 Runs

- **Priority**: P0
- **Estimate**: 1.5j
- **Owner**: QA/Backend
- **Depends on**: T003, T005, T006
- **Description**: Script batch 20 runs + assertions bloquantes en CI. KPIs définis formellement (section KPI ci-dessus).
- **DoD** (seuils formels) :
  - `build_attempted >= 95%` (avec définition "gate légitime" appliquée),
  - `final_status coherence rate = 100%`,
  - `gate divergence rate = 0%`,
  - Delta vs baseline T000-BL positif sur chaque métrique.

---

### T012 — KPI Dashboard

- **Priority**: P1
- **Estimate**: 1j
- **Owner**: Data/Backend
- **Depends on**: T011
- **Description**: Reporting quotidien : success rate, max_iterations, root causes, temps moyen/run, drift par stack.
- **DoD**: Dashboard auto généré par run + agrégat quotidien.

---

### T013 — Regression Test Pack

> **[Amendement Claude Code v2]** Estimate 1.5j → 2j, cas normalisation ajoutés.
> **[Amendement Codex v3, point 5]** Ajout cas explicites : `final_status` quand `build_attempted=false` + mismatch contrats.
> **Pourquoi l'original ne couvrait pas ces cas** : Les tests de régression ciblaient les guards et transitions mais pas la cohérence du statut final dans les chemins d'échec. Or, c'est précisément là que les bugs de `final_message` LLM se glissent (quand `build_attempted=false` mais LLM écrit quand même un message de build).

- **Priority**: P0
- **Estimate**: 2.5j *(était 2j — ajout cas Codex v3)*
- **Owner**: QA Eng
- **Depends on**: T003, T005, T006
- **Description**: Tests non-régression guards, contrats, transitions état. **Inclure** :
  - Cas `prisma/schema.prisma` double-encodé → gate passe après T000-B.
  - Cas `build_attempted=false` → `final_status` = `NOT_BUILT_BY_GATE` (jamais texte LLM).
  - Cas payload erreur avec champ inattendu → `ValidationError` levée, jamais silencieuse.
  - Cas `requirements_gate` bloque + `spec_coverage` valide → divergence détectée.
- **DoD**: Suite passe en CI et bloque merge en cas d'échec.

---

### T014-CR — Canary Rollout

> **[Ticket ajouté — Amendement Codex v3, point 4]**
> **Pourquoi absent de l'original** : Le plan original activait les nouveaux gates/state machine directement à 100%. Si un nouveau gate bloque un cas valide non anticipé, toute la production est affectée. Un canary rollout à 10% permet de valider le comportement sur une minorité de runs avant exposition totale.

- **Priority**: P1
- **Estimate**: 0.5j
- **Owner**: Platform Eng
- **Depends on**: T004, T010, T011
- **Description**: Implémenter flag `CANARY_MODE=true/false` dans la config. En mode canary : 10% des runs utilisent le nouveau pipeline (nouvelle state machine + guards constructifs), 90% utilisent l'ancien. Comparer les métriques des deux populations pendant 48h avant bascule totale.
- **DoD**: Flag opérationnel. Rapport comparatif 10%/90% avant activation globale. Critères de bascule documentés (delta `build_attempted >= +5%`, 0 nouvelle catégorie de régression).

---

### T015 — Runbook Incident

- **Priority**: P1
- **Estimate**: 0.5j
- **Owner**: CTO/Platform
- **Depends on**: T007, T011
- **Description**: Procédures : 429, loop gates, contrat invalide, rollback, hotfix. Simulation incident effectuée.
- **DoD**: Runbook publié + simulation validée.

---

### T016 — Reprise Progressive

- **Priority**: P0
- **Estimate**: 0.5j
- **Owner**: CTO
- **Depends on**: T011, T012, T013, T014-CR
- **Description**: Reprendre features seulement après stabilité mesurée.
- **DoD**: 3 jours consécutifs KPI verts + canary bascule complète avant reprise produit.

---

### T-QA1 — Enrichissement RAG : patterns corrects App Router + Clerk V6 + Prisma 7

> **[Ticket Sprint D — ajouté Claude Code v3]**
> **Pourquoi nécessaire** : Le LLM génère depuis son training + le RAG. Les 53 standards actuels couvrent la gouvernance (sécurité, structure) mais pas les patterns d'implémentation corrects. Résultat : le LLM génère `useRouter().query` (Pages Router) en App Router, `useAuth()` côté serveur (Clerk V5), `await await auth.protect()` (double await). Ces bugs persistent indépendamment de la fiabilité du pipeline.

- **Priority**: P0 (Sprint D)
- **Estimate**: 2j
- **Owner**: Backend Eng / RAG Eng
- **Depends on**: T016 (pipeline stable avant d'optimiser le contenu)
- **Description**: Ajouter dans Qdrant (ZONE_15+) 10-15 standards d'implémentation corrects :
  - Pattern `auth()` server-side Clerk V6 dans une route API (`export async function GET`)
  - Pattern `auth()` dans un server component (pas de hook, pas de `useAuth`)
  - Pattern async server component pour une page App Router (props `params`, `searchParams`)
  - Pattern slug generation côté serveur (`slugify(title)` dans une server action)
  - Pattern Prisma 7 query dans un server component (pas de PrismaClient singleton côté client)
  - Pattern `useAuth()` et `useUser()` : usage **exclusivement** dans un client component (`'use client'`)
- **DoD**: 10+ standards ZONE_15 actifs dans Qdrant. Run de validation : LLM génère `auth()` server-side sur 3 runs consécutifs sans régression.

---

### T-QA2 — Semantic Guards sur contenu : patterns interdits + alternatives

> **[Ticket Sprint D — ajouté Claude Code v3]**
> **Pourquoi nécessaire** : Les guards actuels vérifient les **noms de fichiers** et la **présence de fichiers**. Aucun guard ne lit le **contenu** pour détecter des patterns d'implémentation incorrects. Le bug `useRouter().query` dans App Router passe tous les guards actuels car le fichier s'appelle bien `app/blog/[slug]/page.tsx`.

- **Priority**: P0 (Sprint D)
- **Estimate**: 2j
- **Owner**: Backend Eng
- **Depends on**: T010 *(T-QA1 recommandé mais non bloquant)*
- **Description**: Étendre `_prebuild_gates()` avec une couche "semantic content guards". Pour chaque fichier `.tsx`/`.ts` généré, vérifier :

  | Pattern interdit | Contexte | Alternative à proposer |
  |-----------------|----------|------------------------|
  | `useRouter().query` | `app/**/*.tsx` | Utiliser `props.params` ou `props.searchParams` |
  | `useAuth()` ou `useUser()` sans `'use client'` | `app/**/*.tsx` server component | Ajouter `'use client'` ou remplacer par `auth()` |
  | `await await` | tout fichier | Supprimer le premier `await` |
  | `import { useAuth } from '@clerk/nextjs'` | fichier sans `'use client'` | Remplacer par `import { auth } from '@clerk/nextjs/server'` |
  | `router.reload()` | `app/**/*.tsx` | `router.refresh()` en App Router |
  | `useEffect`/`useState` sans `'use client'` | `app/**/*.tsx` | Ajouter `'use client'` en ligne 1 ou convertir en server component sans hooks |

  Chaque violation renvoie : pattern détecté + ligne approximative + correction cible (constructif, aligné T010).
  Ajouter un compteur `semantic_guard_false_positive` (cas où le guard bloque un code buildable) pour pilotage qualité.

- **DoD**: Guard détecte les 6 patterns sur code synthétique. Run de validation : 0 violation sémantique non détectée sur **10 runs** consécutifs. `semantic_guard_false_positive_rate <= 5%`.

---

### T-QA3 — Template injection : squelettes server component et route handler

> **[Ticket Sprint D — ajouté Claude Code v3]**
> **Pourquoi nécessaire** : Certains patterns sont tellement récurrents et tellement mal générés que confier leur structure au LLM est une source de régression permanente. On a déjà appliqué ce principe pour `middleware.ts` et `jest.setup.js` (templated_files). Il faut l'étendre aux squelettes d'implémentation.

- **Priority**: P1 (Sprint D)
- **Estimate**: 1.5j
- **Owner**: Fullstack Eng
- **Depends on**: T009, T-QA2
- **Description**: Ajouter dans `nextjs-clerk-prisma.json` des `partial_templates` :
  - `_templates/server-page.tsx.tpl` : squelette async server component avec `params` props typés
  - `_templates/api-route.ts.tpl` : squelette `export async function PUT/GET/POST` avec `auth()` et `NextResponse`
  - `_templates/slug-util.ts.tpl` : fonction `generateSlug(title: string): string` prête à l'emploi

  Le LLM reçoit ces squelettes en contexte et doit **compléter la logique métier**, pas réécrire la structure. Si le LLM génère une structure différente du squelette → guard sémantique T-QA2 bloque et propose le template.

- **DoD**: 3 partial templates fonctionnels. Run de validation : LLM complète la logique sans réécrire la structure. 0 `useRouter().query` et 0 `useAuth()` server-side sur 5 runs.

---

### T-QA4 — Few-shot examples dans le prompt dev

> **[Ticket Sprint D — ajouté Claude Code v3]**
> **Pourquoi nécessaire** : Le system prompt actuel de `dev.py` décrit les règles en texte. Les LLM apprennent mieux par l'exemple que par la règle. Un seul exemple complet et correct d'un server component App Router + Clerk V6 ancre le LLM sur le bon pattern dès l'itération 1, avant même que les guards n'interviennent.

- **Priority**: P1 (Sprint D)
- **Estimate**: 1j
- **Owner**: Backend Eng / Prompt Eng
- **Depends on**: T-QA1, T-QA3
- **Description**: Ajouter dans le system prompt de `dev.py` (section dédiée "EXEMPLES CORRECTS") :
  - 1 exemple complet d'une page server component avec `auth()` Clerk V6
  - 1 exemple complet d'une route API `PUT` avec `auth()` + Prisma query
  - 1 exemple de `generateSlug()` côté serveur

  Format : commentaire `// ✅ CORRECT` sur chaque pattern clé. Les exemples doivent être extraits des templates T-QA3 pour cohérence.

- **DoD**: Prompt mis à jour. Run de validation : taux de génération correcte `auth()` server-side >= 80% sur 10 runs (vs baseline T000-BL).

---

### Amendement Sprint D — Qualité de mesure (retour exécution)

> **[Ajout Codex v4 — Mars 2026]**
> **Pourquoi** : Les runs récents montrent un pattern dominant (`client_directive`: hooks React sans `'use client'`) et des pertes d'observabilité quand les payloads de logs sont trop volumineux.  
> Un Sprint D robuste doit mesurer sur des runs exploitables, pas sur des données partielles.

- Les validations critiques Sprint D se font sur **10 runs minimum** (3 runs = signal trop faible).
- Les runs marqués `infra` ou `données partielles` sont exclus des KPI code et comptés séparément.
- Ajouter un KPI qualité guard : `semantic_guard_false_positive_rate` (cible <= 5%).
- Tant que `client_directive` reste root cause dominante, priorité absolue à T-QA2 avant extension à 20 runs.

---

## Attentes par sprint

| Sprint | Métrique principale | Attente réaliste |
|--------|--------------------|--------------------|
| **A** | `build_attempted` | 0% → ~70% |
| **A** | `final_status coherence` | ~60% → 100% |
| **A** | `gate divergence` | élevé → 0% |
| **A** | `avg_iterations` | 14 → 8-10 |
| **B** | `build_attempted` | ~70% → >= 95% (validé harness) |
| **B** | `build_success` | inconnu → mesuré (pas encore ciblé) |
| **C** | ajout nouvelle stack | impossible → < 1 jour |
| **D** | `build_success` | baseline → **objectif >= 60%** |
| **D** | violations sémantiques | non détectées → 0 sur patterns connus |
| **D** | `avg_iterations` | 8-10 → **5-7** (LLM ancré dès iter 1) |
| **D** | `semantic_guard_false_positive_rate` | non mesuré → **<= 5%** |

> **Note** : `build_success >= 60%` après Sprint D est l'objectif. Ce n'est pas 100% — certains briefs complexes nécessiteront toujours plusieurs runs. L'objectif est la convergence fiable, pas la perfection absolue.

---

## Sprint Plan (complet)

**Sprint A — Stabilisation dure (J1-J8)**
`T000-B, T000-BL, T001, T002, T003, T004, T005, T006, T010, T013`

> Buffer J8 ajouté (Codex v3). T000-BL en J1 avant tout changement de code. T010 avancé en Sprint A car guards constructifs = levier de convergence immédiat.

**Sprint B — Résilience + Mesure (J8-J11)**
`T007, T011, T012, T014-CR`

> T014-CR (canary) inclus : dépend de T004+T010 (Sprint A), précède T016.

**Sprint C — Scalabilité Multi-Stack (J11-J15)**
`T008, T009, T015, T016`

**Sprint D — Qualité génération (J15-J21)**
`T-QA1, T-QA2, T-QA3, T-QA4`

> Sprint D ne démarre qu'après T016 (pipeline stable + canary validé). Optimiser le contenu sur un pipeline instable mélange les signaux.
> **Run d'observation obligatoire** entre Sprint A→B, B→C, C→D pour mesurer le delta KPI.

---

## Tableau des amendements (résumé complet)

| Ticket | Auteur | Changement | Raison |
|--------|--------|-----------|--------|
| T000-B | Claude Code v2 + Codex v3 | Normalisation ciblée par type de fichier | Replace global risque de corrompre JSON légitimes |
| T000-BL | Codex v3 | Baseline métriques avant Sprint A | Sans baseline, impossible de prouver le gain |
| T002 | Claude Code v2 | Estimate 1.5j → 3j | Couplage profond dans 3 fichiers |
| T003 | Claude Code v2 | Estimate 1j → 1.5j | Re-test intégration obligatoire après T002 |
| T004 | Claude Code v2 | Budget token ajouté comme livrable | Sans formalisation, dérive contextuelle revient |
| T010 | Claude Code v2 | P1 → P0, Sprint C → Sprint A | Guards constructifs = convergence immédiate |
| T013 | Codex v3 | Estimate 2j → 2.5j, cas final_status + contrats | Bugs `final_message` dans chemins d'échec |
| T014-CR | Codex v3 | Canary rollout 10% ajouté | Éviter régression généralisée sur activation 100% |
| KPIs | Codex v3 | Définition formelle "gate légitime" | KPI manipulable sans définition |
| Sprint A | Codex v3 | J7 → J8 (buffer) | Plan sans buffer n'est pas béton |
| T-QA1 | Claude Code v3 | Enrichissement RAG patterns corrects | LLM génère depuis training sans exemples RAG corrects |
| T-QA2 | Claude Code v3 | Semantic guards sur contenu fichiers | Guards actuels vérifient noms, pas contenu |
| T-QA3 | Claude Code v3 | Template injection squelettes | Structure incorrecte = source de régression permanente |
| T-QA4 | Claude Code v3 | Few-shot examples dans prompt dev | LLM apprend par exemple, pas par règle seule |
| Sprint D | Claude Code v3 | Sprint entier ajouté — qualité génération | Pipeline fiable ≠ contenu correct : deux problèmes distincts |
| Sprint D (amendement qualité) | Codex v4 | DoD durcis (10 runs), ajout pattern `useEffect/useState` sans `'use client'`, KPI `semantic_guard_false_positive_rate` | Les runs réels montrent `client_directive` dominant et nécessité d'éviter les faux positifs guard |
