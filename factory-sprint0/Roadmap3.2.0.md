# ROADMAP — SOFTWARE AGENT FACTORY
## Version 3.8 — Mise à jour 18 Juin 2026
## Historique : v2.0 (23 Fév) · v2.1 (03 Mars) · v2.2 (04 Mars) · v2.3 (28 Mars) · v3.0 (09 Mai) · v3.1 (15 Mai) · v3.2 (24 Mai) · v3.3 (05 Juin) · v3.4 (05 Juin — Consolidation) · v3.5 (05 Juin — Reséquençage Sprint 4.9) · v3.6 (06 Juin — FrontendActivity 3 couches) · v3.7 (06 Juin — FrontendAgent ReAct planifié) · v3.8 (18 Juin — FrontendAgent ANNULÉ ; design intégré dans pipeline déterministe ; Plan6 committé ; Sprint 4.9 reséquencé : 4.9A supprimé, 4.9C devient première priorité)

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

Chaque run améliore la factory : les erreurs détectées alimentent les standards Qdrant
via le Learner. L'usine apprend de chaque app qu'elle produit.

---

## PRINCIPES ARCHITECTURAUX (7)

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

## ÉTAT ACTUEL — 18 Juin 2026 (Niveau 1 stable, perfectionnement moteur en cours)

### Acquis confirmés

**Pipeline Temporal complet :**
`architect_activity → dev_test_activity → review_activity → correction_pass_activity → qa_activity → learner_activity`
*(github_activity en PAUSE volontaire — condition de réactivation : Sprint 5D)*

**Build stable :** Type A validé sur project-hub, task-manager, leave-manager, learn-hub, recipe-manager, expense-tracker, app-simple (7/7 BUILD_SUCCESS). Type D (personal-blog) : BUILD_SUCCESS. event-board (pages publiques/privées mixtes) : BUILD_SUCCESS validé.

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

## SPRINT 5 — Mode Replay + Type D Blog/CMS
## Deadline : Juillet–Août 2026 | STATUT : Planifié

**Condition GitHub agent :** Level A stable sur ≥10 runs consécutifs.

### 5A — Mode Replay
Comparer run N (échoué) vs run N-1 (réussi) : fichiers générés (diff), standards RAG (IDs Qdrant), décisions LLM.

### 5B — Standards Maintenance Agent
Pattern récurrent (N ≥ 3) → web search ALLOWLIST → LLM génère standard → Mode Replay valide → validation humaine → Qdrant.

### 5C — Compatibility Matrix dynamique
```json
{"next": "14.2.25", "clerk": "6.x", "prisma": "7.x"} → "validated"
```

### 5D — Expansion Type D : Blog / CMS
| Générateur | Contenu |
|-----------|---------|
| `dev_seo_generator.py` | `<meta>` tags, `og:image`, `sitemap.xml` |
| Template `rich_textarea.tsx.j2` | Textarea enrichi pour champ `content` |

Nouveaux standards Qdrant (~6) : SEO metadata, content field, category/tag, draft/publish lifecycle, slug routing, getPublished() pagination.

**Signal architect Type D :** "blog", "article", "post", "publication" → `has_slug: true` + `status` draft/published.

**Signal clôture :** `is_useful_app: true` sur personal-blog re-run post-générateurs.

---

## SPRINT 6 — Type G Booking + GitHub agent
## Deadline : Août–Septembre 2026 | STATUT : Planifié

**Condition d'entrée :** Type A ≥5 runs · Type D ≥2 runs · review_activity validé.

### 6A — Type G : Booking / Réservation
| Générateur | Contenu |
|-----------|---------|
| `dev_booking_generator.py` | Slot model, queries conflit, booking FSM |
| Template `calendar_picker.tsx.j2` | Date/time picker |

Standards Qdrant (~10) : conflit créneaux, état machine, timezone, politique annulation, disponibilités récurrentes.

### 6B — GitHub agent réactivation
Repo `factory-generated-apps` · branche par projet · PR avec run_report en description.

---

## SPRINT 7 — Type I Workflow/Approval + Level B Fondations
## Deadline : Septembre–Octobre 2026 | STATUT : Planifié

### 7A — Type I : Workflow / Approbation
`dev_fsm_generator.py` : FSM configurable, transitions légales uniquement.
Standards Qdrant (~8) : FSM pattern, notification triggers, audit trail, parallel approvals.

### 7B — Level B Fondations
```python
organizations: bool = False
roles: list[str] = []
```
`dev_membership_generator.py` → membership.service.ts + permissions.ts + orgId injection.

---

## SPRINT 8 — Level B Multi-tenant Complet + RBAC
## Deadline : Octobre 2026 | STATUT : Planifié

Stack `nextjs-clerk-orgs-prisma` complète · RBAC Guards dans templates · Dashboard Gouvernance (http://localhost:3001).

**Signal :** ≥1 run Notion/Slack clone avec `is_useful_app: true` · RBAC vérifié par reviewer.

---

## SPRINT 9 — Stripe + Type E/H + Stack Versioning
## Deadline : Novembre 2026 | STATUT : Planifié

`dev_billing_generator.py` (Stripe subscription + webhook) · `dev_cart_generator.py` · `dev_dashboard_generator.py` (aggregation queries + chart endpoints) · Stack versioning avec Compatibility Matrix.

---

## SPRINT 10 — Level C Marketplace + Stack 2 + Production Ready
## Deadline : Décembre 2026 | STATUT : Planifié

Stack `nextjs-marketplace-prisma` (two-actor BUYER/SELLER) · Stack 2 `vue-fastapi-sqlalchemy` · Playwright E2E sur URL Vercel · Démo 50 projets (80% `is_production_ready: true`).

---

## EXPANSION DÉTERMINISTE PAR TYPE D'APP

| Type | Nom | Generators manquants | Standards requis | Signal architect | Sprint |
|------|-----|---------------------|-----------------|-----------------|--------|
| **A** | CRUD SaaS | ✅ Complet | ✅ 116 actifs | — | ✅ 4.7 |
| **D** | Blog/CMS | `dev_seo_generator.py`, `rich_textarea.j2` | ~6 (SEO, content, draft/publish) | "blog", "article", "post" | 5 |
| **G** | Booking | `dev_booking_generator.py`, `calendar_picker.j2` | ~10 (slots, FSM, timezone) | "réservation", "créneau" | 6 |
| **I** | Workflow | `dev_fsm_generator.py`, `notification_model.j2` | ~8 (FSM, audit trail) | "approbation", "workflow" | 7 |
| **B** | Multi-tenant | `dev_membership_generator.py`, stack `nextjs-clerk-orgs` | ~12 (tenant isolation, RBAC) | "organisation", "workspace" | 7–8 |
| **H** | Dashboard | `dev_dashboard_generator.py` | ~6 (groupBy, chart endpoints) | "analytique", "dashboard" | 9 |
| **E** | E-commerce | `dev_billing_generator.py`, `dev_cart_generator.py` | ~15 (Stripe, checkout) | "boutique", "paiement" | 9 |
| **F** | Social | many-to-many, real-time module | ~10 (follows, feeds) | "réseau", "posts", "like" | 10+ |
| **C** | Marketplace | nécessite B + E | ~20 (escrow, listing lifecycle) | "acheteur", "vendeur" | 10 |
| **J** | File Mgmt | `dev_storage_generator.py` | ~8 (upload, permissions) | "fichier", "document", "upload" | 10+ |

**Règle d'expansion (PRINCIPE 7) :**
```
Nouveau type → identifier colonne vertébrale déterministe → encoder en générateur
→ écrire standards Qdrant → enseigner signaux à l'architect → LLM garde uniquement le custom
```

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
| Juillet 2026 | **D25-D28 (immédiat)** | Fixes templates : H1 statique, __esModule, checkbox, post-auth | 4 lignes de code, 0 LLM | ⏳ |
| Juillet 2026 | **D23-D24** | Private list cards + layout_hint LLM | variation structurelle par domaine | ⏳ |
| Juillet 2026 | **4.9C** | QA visuel (la scène) — Playwright host | `qa_score ≥ 0.8`, vidéos Windows | ⏳ |
| Juillet 2026 | **4.9D–E** | Correction agentique depuis QA + Production deploy (Vercel+Neon+Clerk) | URL Vercel livrée, DY3/7 résolus | ⏳ |
| Juil–Août 2026 | 5 | Mode Replay + Standards Web + Type D | `is_useful_app: true` personal-blog | ⏳ |
| Août–Sept 2026 | 6 | Type G Booking + GitHub réactivé | `is_useful_app: true` booking brief | ⏳ |
| Sept–Oct 2026 | 7 | Type I Workflow + Level B fondations | `is_useful_app: true` approval brief | ⏳ |
| Octobre 2026 | 8 | Level B complet + RBAC + Dashboard | Notion clone `is_useful_app: true` | ⏳ |
| Novembre 2026 | 9 | Stripe + Type E/H + Stack versioning | E-commerce `is_useful_app: true` | ⏳ |
| Décembre 2026 | 10 | Type C Marketplace + Stack 2 + Démo 50 | 50 projets déployés, 80% score≥70 | ⏳ |

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
| D9 | `reviewer_activity` score 100 sur apps défectueuses | 4.8A | ✅ résolu |
| D10 | `journey_validator` sous-compte les flows couverts | 4.7A (D1) | ⏳ |
| D11 | Progressive Validation absente du graphe | 4.9B (F1) | ⏳ |
| D12 | `quality_validator.py` : appel bloquant async + zombie file | 4.7D (F3/F4) | ⏳ |
| D13 | `getAllByUser` absent de `service_map_str` | 4.7E (G) | ⏳ |
| D14 | Feature modules via side-effect imports | 4.7E (F) | ⏳ |
| D15 | `SpecOutput` contrat zombie | Nettoyer 5 | ⏳ |
| D16 | `update`/`create` retournent `Promise<ModelName>` pas `SerializedXxx` | 4.7D (F9) | ⏳ |
| D17 | Decimal non sérialisé dans `_serialize` | 4.7D (F10) | ⏳ |
| D18 | Enum : union literals au lieu d'imports Prisma | 5 | ⏳ |
| D19 | `prebuild_pipeline.py` orchestrateur séparé de `dev_graph` | 4.9B | ⏳ |
| D20 | `module_search`/`status_flow` lisent heuristiques au lieu de `enriched_spec.features` | 4.9 (DY1) | ⏳ |
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
| DY1 | Module system mort : `should_activate()` lit heuristiques au lieu de `enriched_spec.features[]` | `module_search.py`, `module_status_flow.py` | 4.9 |
| DY2 | Fracture CROSS_ENTITY : `_gen_page_full()` deux fetches séparés au lieu de `getByIdWithRelations` — `module_detail_with_children` neutralisé | `dev_pages_generator.py`, `module_detail_with_children.py` | 4.9 |
| DY3 | `rules_dev.md` : 36 règles dont ~25 sur fichiers déterministes (services, actions) = bruit dans le contexte LLM | `prompts/rules_dev.md` | 4.9 |
| DY4 | `code_role_hints` JSON et `rules_dev.md` se chevauchent — une règle dans deux endroits | `config/stacks/*.json`, `prompts/rules_dev.md` | 4.9 |
| DY5 | Architect génère `pages_detail` pour toutes les pages y compris les déterministes (inutile) | `agents/architect.py` pages_detail_node | 4.9 |
| DY6 | Générateurs (backbone, toujours actifs) et modules (conditionnels) : deux systèmes non unifiés | `dev_graph.py`, `feature_modules/` | 5 |
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
