# Factory Audit — StartupNexus Software Agent Factory

> Document vivant — mis à jour à chaque ajout de concept majeur.
> Dernière mise à jour : 22 Juin 2026

---

## TABLE DES MATIÈRES

1. [Philosophie et promesse de valeur](#1-philosophie-et-promesse-de-valeur)
2. [Architecture du pipeline](#2-architecture-du-pipeline)
3. [Couche déterministe (Level A)](#3-couche-déterministe-level-a)
4. [Couche LLM — Architect Graph](#4-couche-llm--architect-graph)
5. [Couche LLM — Dev Test Agent](#5-couche-llm--dev-test-agent)
6. [Mécanisme de contrat et d'injection de contexte](#6-mécanisme-de-contrat-et-dinjection-de-contexte)
7. [Design System déterministe](#7-design-system-déterministe)
8. [Feature Modules](#8-feature-modules)
9. [Observabilité et apprentissage](#9-observabilité-et-apprentissage)
10. [Bugs actifs identifiés (22 Jun 2026)](#10-bugs-actifs-identifiés-22-jun-2026)
11. [Analyse de la non-conformité LLM — causes et solutions](#11-analyse-de-la-non-conformité-llm--causes-et-solutions)
12. [Roadmap et prochaines étapes](#12-roadmap-et-prochaines-étapes)

---

## 1. Philosophie et promesse de valeur

La factory génère des applications Next.js 14 complètes (Clerk V5 + Prisma 7) à partir d'un brief textuel, en **une seule exécution**, sans intervention humaine dans la boucle.

**Principe fondateur** : "Level A = 100% déterministe." Tout ce qui peut être calculé à partir du schéma Prisma est généré par du code Python déterministe. Le LLM n'intervient que là où la décision ne peut pas être calculée : l'interprétation du domaine métier et la génération de pages custom (sans modèle direct).

**Stack cible** : Next.js 14, App Router, Clerk V5, Prisma 7, shadcn/ui, Tailwind CSS, TypeScript strict.

**Stack ID** : `nextjs-clerk-prisma` — sert de clé pour charger la configuration depuis `config/stacks/nextjs-clerk-prisma.json`.

---

## 2. Architecture du pipeline

### 2.1 Pipeline Temporal
```
TodoPilotWorkflow
  → architect_activity   (graph LLM → sortie : EnrichedSpec)
  → dev_test_activity    (générateurs déterministes + LLM executor + build)
  → qa_activity          (vérifications post-build)
  → github_activity      (push optionnel)
  → learner_activity     (shadow mode — apprentissage des erreurs)
```

### 2.2 Modules clés
| Fichier | Rôle |
|---------|------|
| `workflows/todo_pilot_workflow.py` | Workflow principal Temporal |
| `agents/shared_tools.py` | Tous les `@tools` + façade `context` + `observability` |
| `agents/context.py` | `ContextVar` async-safe : `run_id`, `stack_id` |
| `agents/observability.py` | Logger, RAG usage events, learner events |
| `agents/stack_config.py` | Loader JSON stack, `get_root_file()` multi-stack |
| `config/stacks/nextjs-clerk-prisma.json` | Stack-as-Config (fichiers requis, validation, env, etc.) |
| `agents/architect.py` | Graph architect (nœuds décrits §4) |
| `agents/stacks/nextjs_clerk_prisma/dev_graph.py` | Orchestrateur niveau-A + LLM executor |

### 2.3 Variables d'environnement critiques
- `FACTORY_WORKDIR` — chemin du répertoire de génération à l'intérieur du container Docker (`/app/generated-projects`). Toutes les écritures sur disque passent par `_get_workdir()` dans `shared_tools.py`.
- Named volume Docker : `generated-projects`.

---

## 3. Couche déterministe (Level A)

### 3.1 Principe
Level A produit tous les fichiers qui peuvent être calculés de façon déterministe à partir du schéma Prisma et de la spec enrichie. Le LLM ne peut **jamais** écraser ces fichiers.

### 3.2 Générateurs et leurs outputs

| Générateur | Output principal |
|-----------|-----------------|
| `dev_types_generator.py` | `lib/types.ts` — `SerializedXxx` interfaces (champs scalaires uniquement, dates → string) |
| `dev_zod_generator.py` | `lib/schemas.ts` — schémas Zod pour chaque modèle |
| `dev_service_generator.py` | `lib/services/*.ts` — service layer (7 méthodes garanties + conditionnelles) |
| `dev_actions_generator.py` | `app/**/actions.ts` — Server Actions (create/update/delete) par liste page |
| `dev_pages_generator.py` | `app/**/page.tsx` et `app/**/page-client.tsx` — pages CRUD déterministes |
| `dev_form_generator.py` | `page-client.tsx` pour list/create/edit (formulaires shadcn/ui) |
| `dev_hub_generator.py` | `app/dashboard/page.tsx` — hub de navigation |
| `dev_layout_generator.py` | `app/layout.tsx`, sidebar/topnav selon design preset |
| `dev_design_system_generator.py` | `app/globals.css` — CSS variables HSL mappées depuis design preset |

### 3.3 Méthodes service garanties

Le module `service_modules/` compose chaque service. Voici les méthodes générées selon les conditions :

| Méthode | Condition d'activation |
|---------|----------------------|
| `getAll(userId)` | Toujours |
| `getById(userId, id)` | Toujours |
| `create(userId, data)` | Toujours |
| `update(userId, id, data)` | Toujours |
| `delete(userId, id)` | Toujours |
| `getPublicById(id)` | Si `has_public_pages` |
| `getPublicAll(page, pageSize)` | Si `has_public_pages` (Boolean `published`/`isPublic` OU enum `status`) |
| `getBySlug(slug)` | Si `slug @unique` sur le modèle |
| `getBySlugOwned(userId, slug)` | Si `slug @unique` + authentification |
| `getAllWithRelations(userId)` | Si `@relation` 1-N |
| `getByIdWithRelations(userId, id)` | Si `@relation` 1-N |
| `getBySlugWithRelations(slug)` | Si `slug @unique` + `@relation` |

**IMPORTANT** : `getPublished()` **n'existe pas**. Ce nom n'est jamais généré. La méthode pour les pages publiques est toujours `getPublicAll()` — que le modèle ait un Boolean `published` ou un enum `status`. Voir `service_modules/public.py` pour la logique exacte du filtre WHERE.

### 3.4 CONTRACTS.md
Avant chaque run LLM executor, `dev_graph.py` génère `CONTRACTS.md` depuis `_level_a_manifest`. Ce fichier liste toutes les signatures de méthodes réellement disponibles pour ce projet spécifique.

**Périmètre actuel d'injection** : `dev_context.py` injecte CONTRACTS.md uniquement pour les pages **custom** (type `custom`, sans model résolu par segment d'URL). Pour les pages CRUD standards, il injecte le contenu brut du fichier `.service.ts` concerné.

### 3.5 Fichiers déterministes protégés
Ces fichiers ne peuvent JAMAIS être écrits par le LLM :
- `middleware.ts` (template fixe)
- `jest.config.js`, `jest.setup.js` (templates fixes)
- `tsconfig.json` (template fixe)
- `package.json`, `.env.local` (templates fixes avec substitution)
- Tous les outputs des générateurs §3.2

---

## 4. Couche LLM — Architect Graph

### 4.1 Nœuds du graph (Plan6)

```
domain_interpreter → page_planner → semantic_annotator → pages_detail → spec_enricher → planner
```

Pour les briefs **structurés** (models + pages déjà fournis), le pipeline saute directement à `semantic_annotator`.

### 4.2 domain_interpreter_node (LLM)
- **Rôle** : interprète le brief libre, extrait les entités métier, crée le schéma Prisma.
- **Invariants injectés** : tous les modèles ont `userId String`, pas de modèle `User`, exception `authorId String` pour les CMS.
- **Output** : `models[]` avec champs Prisma.

### 4.3 page_planner_node (LLM)
- **Rôle** : propose la structure de pages depuis les modèles.
- **Prompt** : `agents/page_planner.py` — contient `_PAGE_STACK_INVARIANTS` avec RÈGLE 9 (interdiction de générer `[id]` et `[slug]` en parallèle).
- **Important** : ce nœud génère aussi un `design_system`, mais il sera **totalement écrasé** par `spec_enricher_node` (design_resolver déterministe). Le design_system du page_planner est donc sans effet.
- **Skip** : ignoré pour les briefs structurés.

### 4.4 semantic_annotator_node (LLM)
- **Rôle** : annote chaque page avec `page_type` (list, create, detail, edit, detail-slug, custom), `model`, `auth_required`, et les features à activer.
- **Activation des features** : `module_status_flow`, `module_detail_with_children`, `module_search` — détectés ici.

### 4.5 pages_detail_node (LLM)
- **Rôle** : pour chaque page de type `custom` (sans modèle direct), génère `description` et `data_fetches`.
- **Portée** : UNIQUEMENT les pages custom. Les pages CRUD (list/create/detail/edit) sont 100% déterministes et ne passent pas ici.
- **Bug actif** : le prompt ligne 421 liste `getPublicAll()` ET `getPublished()` comme options valides pour les pages publiques sans distinction. Le LLM choisit `getPublished()` par biais de pré-entraînement (pattern courant dans les repos Rails/Django).

### 4.6 spec_enricher_node (déterministe)
- **Rôle** :
  1. Valide et overrides les `data_fetches` LLM si incorrects.
  2. Injecte le `design_system` depuis `design_resolver.py` (écrase complètement tout ce que le LLM a proposé).
- **Bug actif** : `_VALID_SERVICE_METHODS` inclut `"getPublished"` à la ligne 34, ce qui fait passer `getPublished()` comme valid. Le spec_enricher ne l'override pas. Or cette méthode n'existe JAMAIS dans les services générés (§3.3). Résultat : le dev LLM reçoit `data_fetches: [{service: "articleService", method: "getPublished", ...}]` et génère du code qui appelle une méthode inexistante → `TS2339`.

### 4.7 planner_node (déterministe)
- **Rôle** : construit le manifest final — liste ordonnée des fichiers à générer, avec phase, générateur, et métadonnées.
- **RÈGLE 5** : auto-ajoute une page `[parent_list]/[id]` pour tout modèle parent (avec enfants FK). Ne vérifie pas si une route `[slug]` existe déjà sur le même segment.
- **Bug actif** : pour `Article` (parent de `Resource`), RÈGLE 5 ajoute `/articles/[id]`. Or `/articles/[slug]` est déjà déclaré → conflit Next.js `'id' !== 'slug'` → BUILD_FAILED.
- **Invariant detail-slug** (lignes 628-648) : corrige les pages `detail-slug` pour les modèles sans `slug @unique` → les transforme en `detail`. Mais ne supprime pas la route `[id]` ajoutée par RÈGLE 5 en aval.

---

## 5. Couche LLM — Dev Test Agent

### 5.1 Portée du LLM executor
Le LLM dev ne génère QUE :
- `app/**/page.tsx` pour les pages **custom** (sans modèle, ni list/create/detail/edit)
- `app/**/page-client.tsx` [INTERACTIVE] pour les pages custom
- `app/api/webhooks/**/route.ts`

Tout le reste est Level A déterministe.

### 5.2 Contexte injecté dans le dev LLM
Depuis `dev_context.py` :
- **D1** : Service file `.service.ts` (si page avec modèle résolu) OU CONTRACTS.md (si page custom, §3.4)
- **D2** : Contenu de `page-client.tsx` sibling (si présent — pour que `page.tsx` passe les bonnes props)
- **D3** : `page_detail_hint` depuis `dev_prompts.py` (description précise du contenu attendu)
- **Rules** : `rules_dev.md` (21 règles + exemples)
- **Capabilities** : `factory_capabilities.md` (méthodes garanties, composants shadcn/ui)

### 5.3 Observation sur l'injection CONTRACTS.md
Le chemin d'injection dans `dev_context.py` (lignes 387-394) :
```python
elif service_map_str:
    _contracts_path = os.path.join(workdir, "CONTRACTS.md")
    _contracts_content = _read_file_safe(_contracts_path, 2000)
    if _contracts_content:
        dep = f"\nCONTRACTS.md ..."
    else:
        dep = f"\n{service_map_str}"
```
CONTRACTS.md est injecté **seulement** quand `service_map_str` est défini ET que le service spécifique au segment d'URL n'a PAS été trouvé. Pour une page `/articles/[slug]`, le service `articleService` EST résolu par segment → le LLM reçoit le fichier `.service.ts` brut, PAS CONTRACTS.md. Donc pour les pages CRUD publiques, le dev LLM reçoit directement le service généré (qui contient `getPublicAll`, pas `getPublished`). Le problème vient de l'architect qui met le mauvais `data_fetches` dans la spec, que le dev suit.

### 5.4 Rules_dev.md
21 règles injectées en tête du prompt système. Points critiques :
- **Règle 12** : "JAMAIS inventer une méthode absente de CONTRACTS.md"
- **Règle 20** : "PAGES PUBLIQUES — INTERDIT AUTH()"
- **Règle 48** : "JAMAIS utiliser `getPublished()` si le modèle a `isPublic/published Boolean` → utiliser `getPublicAll()`"

**Observation** : Rule 48 est correcte mais arrive trop tard dans un prompt de 21 règles. Le LLM a déjà reçu la spec de l'architect qui dit `getPublished()`. L'instruction contradictoire entre la spec architect et rules_dev.md crée un conflit d'objectifs — le LLM suit la spec (source de données contextuelles) plutôt que la règle (instruction générale).

---

## 6. Mécanisme de contrat et d'injection de contexte

### 6.1 Flux de connaissance pour le LLM

```
design_resolver.py (déterministe) ──→ design_system dans EnrichedSpec
service_modules/ (déterministe)   ──→ CONTRACTS.md sur disque
pages_detail_node (LLM)           ──→ data_fetches dans EnrichedSpec (souvent faux)
spec_enricher (déterministe)      ──→ overrides data_fetches si méthode invalide
                                      (mais valide incorrectement getPublished)
dev_context.py                    ──→ injecte [service.ts OU CONTRACTS.md] + hints + rules
dev LLM executor                  ──→ génère page.tsx / page-client.tsx
```

### 6.2 Pourquoi le dev LLM "suit l'architect" plutôt que les règles

Quand le spec architect contient `data_fetches: [{method: "getPublished"}]`, ce datum est injecté dans le contexte du dev LLM via `page_detail_hint`. C'est une **donnée contextualisée** (haute attention) vs une **règle générale** (basse attention, lost-in-the-middle). Le LLM accorde plus de poids aux données du contexte immédiat qu'aux règles déclarées en tête de prompt.

**Solution structurelle** : corriger la source (spec_enricher doit rejeter `getPublished` comme invalide et calculer le bon data_fetch). Ne pas rajouter de règle dev supplémentaire.

### 6.3 factory_capabilities.md
Fichier `prompts/stacks/nextjs-clerk-prisma/factory_capabilities.md` :
- Liste les 7 méthodes service garanties
- Liste les composants shadcn/ui disponibles : Button, Input, Textarea, Label, Card, Badge, Table, Select, Empty, StatCard
- Note : "L'architect ne doit JAMAIS décrire la configuration des couleurs"

### 6.4 rules_architect.md (ARCHIVÉ)
**Inutilisé depuis Option-A** (26 Apr 2026). L'architect est désormais déterministe sauf pour les nœuds LLM du graph. Ce fichier est un zombie — ses règles sont obsolètes.

---

## 7. Design System déterministe

### 7.1 Flux du design system

```
spec_enricher_node
  └→ design_resolver.resolve_preset(brief.description)
       └→ score les mots du brief contre _DOMAIN_KEYWORDS
            └→ preset gagnant → charge design_presets.json[preset]
                 └→ EnrichedSpec.design_system
                      └→ dev_design_system_generator.py
                           └→ app/globals.css (CSS variables HSL)
                      └→ dev_layout_generator.py
                           └→ app/layout.tsx (sidebar OU topnav)
```

**Point clé** : Le design_system est **100% déterministe**. Ni le page_planner, ni le dev LLM ne peuvent influencer les couleurs ou le layout. Tout provient de `design_presets.json`.

### 7.2 Presets actuels

| Preset | Domaines déclencheurs | Couleur primaire | Layout | List style |
|--------|----------------------|-----------------|--------|-----------|
| `saas_dashboard` | tracker, gestion, clients, projet, tâche, sprint | `blue-700` | sidebar | table |
| `editorial` | blog, article, post, rédaction, publication | `amber-600` | topnav | card-grid |
| `marketplace` | achat, vente, marché, produit, commande | `emerald-600` | topnav | card-grid |
| `minimal` | (fallback) | `slate-700` | topnav | list |

### 7.3 Bug actif — Color override ignoré
Les mots-clés de couleur explicites dans le brief ("orange vif", "violet", "rouge") ne sont pas considérés par `design_resolver.py`. Le matching est purement basé sur les mots du domaine. Sprint-board brief "orange vif" → match `saas_dashboard` → `blue-700`.

**Fix envisagé** : Ajouter un extracteur de couleur explicite dans `design_resolver.py` — si le brief mentionne une couleur nommée ou un hex, l'utiliser comme `primary_color` override sur le preset de domaine.

### 7.4 Tokens design dans les générateurs
Les générateurs Jinja2 reçoivent les tokens via la fonction `_design_tokens(design_system)` dans `dev_form_generator.py` :
```python
{
    "primary": "primary",            # → bg-primary, text-primary (CSS var)
    "primary_hover": "primary/85",   # → hover:bg-primary/85
    "primary_light": "primary/10",   # → bg-primary/10
    "primary_ring": "primary",       # → focus:ring-primary
    "card_cls": "bg-card ...",       # → classes Tailwind pour card elevation
    "p_cls": "p-6",                  # → padding selon density
    "transition_cls": "...",
    "list_style": "table" | "card-grid" | ...,
}
```
Les feature modules (`module_status_flow`, `module_detail_with_children`) n'ont pas accès au `design_system` de l'EnrichedSpec lors de l'exécution de `run_feature_modules()`. Ils utilisent des valeurs hardcodées par défaut (`primary="primary"`, `p_cls="p-6"`, etc.).

---

## 8. Feature Modules

Les feature modules sont des générateurs déterministes activés conditionnellement via `enriched_spec.features[]`.

### 8.1 module_status_flow (priority=10)
- **Activation** : modèle avec enum `status` ET page list déclarée.
- **Produit** : `page-client.tsx` de la page list avec filtrage par statut (tabs ou select).
- **Template** : `list_client_status.tsx.j2`.
- **Variables requises** : `status_values`, `status_labels`, `has_search`, `p_cls`, `primary`, `primary_hover`, `primary_light`, `primary_ring`.

### 8.2 module_detail_with_children (priority=100)
- **Activation** : modèle parent avec au moins une relation 1-N (`is_array=True`).
- **Produit** : `app/{detail_path}/page-client.tsx` — affiche le parent + liste des enfants + formulaire inline de création.
- **Template** : `detail_with_children_client.tsx.j2`.
- **Avantage** : évite les hallucinations LLM sur les pages CROSS_ENTITY (enfants FK).
- **Variables requises** : `p_cls`, `card_cls`, `primary`, `primary_hover`, `primary_light`, `primary_ring`.

### 8.3 module_search
- **Activation** : `has_search=True` dans la spec.
- **Produit** : enrichit la page list avec un champ de recherche côté client.

### 8.4 run_feature_modules()
Appelé dans `dev_graph.py`. Itère sur les modules enregistrés (via `register()`), appelle `should_activate()` et `generate()`. Le `design_system` de l'EnrichedSpec **n'est pas transmis** aux feature modules — limitation actuelle.

---

## 9. Observabilité et apprentissage

### 9.1 learner_agent (shadow mode)
- **Fichier** : `agents/learner.py`.
- **Rôle** : observe les runs, extrait les anti-patterns depuis `last_build_error`.
- **P006** : normalise l'erreur de build via `_normalize_build_error()` et propose une suggestion Qdrant ZONE_14.

### 9.2 approve_suggestion.py
- Workflow interactif y/n/q → upsert Qdrant ZONE_14 si approuvé.
- Gate décisionnel : `_check_gate()` — si >15 suggestions avec taux >70%, génère `sprint5_gate.json`.

### 9.3 RAG Qdrant
- Collection : `factory_standards`, localhost:6333.
- 116 standards actifs post-Option-A (26 Avr 2026).
- Zones ZONE_1-14 + ZONE_17B→30 + ZONE_HARD_RULES.
- Format post-Option-A : `RULE: / WHY: / GOOD: / BAD:`.
- `_build_architect_rag_filter()` : filtre toujours sur `metadata.status=active`.

---

## 10. Bugs actifs identifiés (22 Jun 2026)

### Bug 1 — `planner_node` RÈGLE 5 : conflit slug/id
**Fichier** : `agents/architect.py`, lignes 675-716.
**Symptôme** : `Error: You cannot use different slug names for the same dynamic path ('id' !== 'slug')` → BUILD_FAILED pour writer-pad.
**Cause** : RÈGLE 5 ajoute `/articles/[id]` automatiquement pour tout modèle parent. Ne vérifie pas si `/articles/[slug]` existe déjà.
**Fix** : dans RÈGLE 5, avant d'ajouter `[parent_list]/[id]`, vérifier si une page `detail-slug` existe déjà sur le même segment de base. Si oui, ne pas ajouter la page `[id]`.

### Bug 2 — `spec_enricher._VALID_SERVICE_METHODS` : `getPublished` accepté
**Fichier** : `agents/spec_enricher.py`, ligne 34.
**Symptôme** : `TS2339 Property 'getPublished' does not exist` → BUILD_FAILED pour writer-pad et tout projet avec `published Boolean`.
**Cause** : `_VALID_SERVICE_METHODS` contient `"getPublished"` alors que cette méthode n'est jamais générée par `service_modules/public.py`. `getPublicAll()` est toujours le vrai nom.
**Fix** : retirer `"getPublished"` de `_VALID_SERVICE_METHODS`. Quand la méthode n'est pas reconnue, `spec_enricher` calculera le bon data_fetch (`getPublicAll()` pour toute page publique).

### Bug 3 — `pages_detail_node` prompt : ambiguïté `getPublished` vs `getPublicAll`
**Fichier** : `agents/architect.py`, ligne 421.
**Symptôme** : LLM architect génère `getPublished()` pour des modèles avec `published Boolean`.
**Cause** : le prompt liste les deux méthodes comme équivalentes pour les pages publiques. Le LLM choisit `getPublished()` par biais de pré-entraînement.
**Fix** : retirer `getPublished()` du prompt. Seul `getPublicAll()` doit apparaître. `getPublished()` n'existe pas dans la factory.

### Bug 4 — `design_resolver.py` : couleur explicite brief ignorée
**Fichier** : `agents/core/design_resolver.py`.
**Symptôme** : sprint-board demande "orange vif" → reçoit `blue-700` (preset saas_dashboard).
**Cause** : le resolver ne lit pas les couleurs explicites dans le brief, uniquement les mots de domaine.
**Fix** : ajouter un pre-pass qui extrait couleurs nommées/hex du brief et les injecte comme `primary_color` override sur le preset sélectionné.

---

## 11. Analyse de la non-conformité LLM — causes et solutions

### 11.1 Les 4 causes racines

#### Cause 1 — Biais de pré-entraînement
Le LLM a été entraîné sur des millions de repos qui utilisent `getPublished()`, `getPosts()`, `getArticles()`. Quand il voit un modèle `Article` avec un champ `published`, il associe automatiquement ce pattern à `getPublished()` — c'est la convention la plus répandue dans son corpus d'entraînement. Une règle dans le prompt lui dit autre chose, mais son prior de pré-entraînement est fort.

**Solution dans notre contexte** : rendre le biais inopérant en le rendant non-exécutable. Si `getPublished()` est supprimé du `_VALID_SERVICE_METHODS` + du prompt architect, la spec produit `getPublicAll()` → le dev LLM reçoit ce data_fetch + lit le `.service.ts` généré qui contient `getPublicAll()` → il n'a aucune raison de dévier.

#### Cause 2 — Attention loss / Lost-in-the-middle
Les LLMs ont un biais attentionnel : ils lisent bien le début et la fin du prompt, moins bien le milieu. `rules_dev.md` avec 21 règles numérotées → les règles 10-18 sont statistiquement moins bien suivies. Les specs de l'architect (données contextuelles) arrivent juste avant la tâche → forte attention.

**Solution dans notre contexte** :
- **Diviser pour mieux régner** : chaque nœud du graph ne reçoit que les règles pertinentes à sa tâche. `pages_detail_node` ne devrait avoir que 3-5 règles, pas 21.
- **Structured outputs** : forcer le schema JSON de sortie — si le schema n'a pas de champ `color` dans `data_fetches`, le LLM ne peut pas halluciner une méthode inexistante (la structure du JSON l'empêche physiquement).
- **Règle critique en premier** : placer les règles de type "JAMAIS `getPublished()`" AVANT les exemples, pas après 15 autres règles.

#### Cause 3 — Conflit d'objectifs
Le dev LLM reçoit :
- Une spec architect (données) qui dit `data_fetches: [{method: "getPublished"}]`
- Une règle (instruction) qui dit "JAMAIS getPublished()"

Il y a contradiction. Le LLM résout le conflit en favorisant les données contextuelles (la spec) sur les règles générales. C'est rationnel de son point de vue : la spec est spécifique à CE projet, la règle est générale. Il pense que la règle ne s'applique peut-être pas ici.

**Solution dans notre contexte** : éliminer la contradiction à la source. Si `spec_enricher` garantit que `getPublished` ne peut jamais apparaître dans la spec (Bug 2 fix), le dev LLM ne reçoit plus de signal contradictoire. Plus besoin de la règle 48.

#### Cause 4 — Absence de mémoire de travail réelle
Le LLM executor est appelé une fois par fichier. Il ne "sait" pas qu'il vient de générer `/articles/page.tsx` quand il génère `/articles/[slug]/page.tsx`. Chaque appel est indépendant — il ne peut pas raisonner sur la cohérence inter-fichiers.

**Solution dans notre contexte** :
- Level A déterministe élimine ce problème pour les fichiers CRUD.
- Pour les fichiers custom : le `page-client.tsx` sibling est injecté dans le contexte quand `page.tsx` est généré (D2 dans `dev_context.py`) — c'est déjà implémenté.
- Pour les conflits de routes : `planner_node` déterministe doit valider la cohérence avant le run LLM (Bug 1 fix).

### 11.2 Solutions adaptées à la factory

#### Solution A — Structured Outputs (priorité haute)
Utiliser l'API OpenAI avec `response_format={type: "json_schema", json_schema: {...}}` pour les nœuds LLM de l'architect.

**Application factory** :
- `pages_detail_node` : schema JSON strict pour `pages_detail`. Champ `method` dans `data_fetches` → enum : `["getAll", "getById", "getPublicAll", "getPublicById", "getBySlug", "getAllWithRelations", "getByIdWithRelations"]`. `getPublished` est physiquement absent de l'enum → impossible à halluciner.
- `semantic_annotator_node` : schema strict pour `page_type` → enum des valeurs valides.

**Avantage** : élimine structurellement les hallucinations de méthode. Le LLM choisit parmi les options valides, pas dans son imagination.

**Prérequis** : tous les nœuds LLM doivent migrer vers l'API chat completions avec structured outputs (actuellement LangChain). La migration est possible via le paramètre `response_format` de LangChain ChatOpenAI.

#### Solution B — Few-Shot Examples ciblés (priorité haute)
Les LLMs suivent mieux des exemples concrets que des règles abstraites. Remplacer les règles textuelles par des paires input→output.

**Application factory** — `pages_detail_node`, injecter 3 exemples :

**Exemple 1 — Modèle avec published Boolean (le cas qui déconne)**
```json
// Brief : "Les articles ont un champ published Boolean"
// Page : /articles (public, auth=false)
// CORRECT :
{"path": "/articles", "data_fetches": [{"service": "articleService", "method": "getPublicAll", "args": []}]}
// INTERDIT :
{"data_fetches": [{"method": "getPublished"}]}  // ← n'existe pas
```

**Exemple 2 — Page dashboard (auth=true)**
```json
// Page : /dashboard (auth=true)
// CORRECT :
{"path": "/dashboard", "data_fetches": [{"service": "projectService", "method": "getAll", "args": ["userId"]}]}
// INTERDIT :
{"data_fetches": [{"method": "getPublicAll"}]}  // ← public sur page privée
```

**Exemple 3 — Home page sans données**
```json
// Page : / (landing page statique)
// CORRECT :
{"path": "/", "data_fetches": []}
```

**Pourquoi ça marche** : in-context learning. Le LLM extrapole un pattern depuis les exemples plutôt que d'appliquer une règle abstraite. Plus robuste contre le biais de pré-entraînement.

#### Solution C — Chain of Thought forcé (priorité moyenne)
Avant de produire le JSON final, forcer le LLM à raisonner sur chaque décision.

**Application factory** — ajouter dans `pages_detail_node` :
```
Pour chaque page, avant de choisir la méthode data_fetches :
1. Ce modèle a-t-il un champ slug @unique ? → utiliser getBySlug
2. Cette page est-elle publique (auth=false) ? → utiliser getPublicAll (JAMAIS getPublished)
3. Cette page est-elle privée (auth=true) ? → utiliser getAll(userId)
Justifie ton choix en une phrase, puis donne le JSON.
```

**Avantage** : le LLM externalise son raisonnement. Les erreurs apparaissent dans le CoT et peuvent être détectées avant le JSON final. On peut même valider le CoT programmatiquement.

#### Solution D — Diviser pour mieux régner (priorité haute, déjà partiellement fait)
Le graph Plan6 est la bonne direction : chaque nœud a une responsabilité unique et un prompt court.

**Axes d'amélioration** :
- `pages_detail_node` actuel : 1 gros prompt → devrait recevoir UNE page à la fois, pas toutes les pages dans un seul appel. Cela réduit le contexte, améliore la cohérence, permet de relancer individuellement en cas d'erreur.
- `rules_dev.md` 21 règles → segmenter par phase d'exécution. L'executor reçoit seulement les règles pertinentes au type de page qu'il génère actuellement.
- Prompt monolithique → fichiers de règles par domaine : `rules_auth.md`, `rules_services.md`, `rules_public.md`. Injectés conditionnellement selon le contexte de la page.

#### Solution E — Validation déterministe post-LLM (déjà partiellement fait)
`spec_enricher_node` est la bonne approche : corriger les sorties LLM de façon déterministe avant qu'elles ne propagent dans le pipeline.

**À étendre** :
- Retirer `getPublished` de `_VALID_SERVICE_METHODS` (Bug 2 fix).
- Ajouter validation : si `method == "getPublished"` ET le modèle n'a pas de champ enum `status` → remplacer par `getPublicAll`.
- Ajouter validation : si `auth_required=false` dans la page spec ET `method` contient `userId` → remplacer par la méthode publique équivalente.

### 11.3 Matrice priorisation
| Solution | Impact | Complexité | Priorité |
|----------|--------|------------|----------|
| Fix spec_enricher (Bug 2) | Élimine `getPublished` erreurs | Faible | **P0 immédiat** |
| Fix planner_node (Bug 1) | Élimine conflit slug/id | Faible | **P0 immédiat** |
| Fix prompt pages_detail_node (Bug 3) | Réduit hallucinations | Faible | **P0 immédiat** |
| Few-Shot examples (Solution B) | Réduit toutes les hallucinations | Moyen | **P1** |
| Structured Outputs (Solution A) | Élimine structurellement | Moyen-fort | **P1** |
| Diviser pages_detail en 1 appel/page (Solution D) | Réduit attention loss | Fort | **P2** |
| Chain of Thought (Solution C) | Auditabilité + précision | Moyen | **P2** |
| Color override brief (Bug 4) | UX design | Faible | **P3** |

---

## 12. Roadmap et prochaines étapes

### Sprint actuel (22 Jun 2026)
- [x] Level A déterministe complet (7 générateurs + feature modules)
- [x] Plan6 architect graph décomposé
- [x] Bugs générateurs fixés : `status_values`, `p_cls/card_cls`, design tokens modules
- [ ] **P0** : Fix Bug 1 (planner_node RÈGLE 5 slug conflict)
- [ ] **P0** : Fix Bug 2 (spec_enricher `getPublished` invalide)
- [ ] **P0** : Fix Bug 3 (pages_detail_node prompt ambigu)

### Prochaines phases (roadmap `project_architectural_roadmap.md`)
1. **Phase-Aware System Prompt** : l'executor reçoit des règles différentes selon la phase (Level A vs custom)
2. **Plan-and-Execute** : architect produit un plan de fichiers avant l'exécution — le dev LLM suit le plan
3. **Structured Outputs** par nœud LLM
4. **Few-Shot examples** dans `pages_detail_node`
5. **Contract Generator dans le planner** : contrats de fichiers déterministes pour guider le LLM sur `actions.ts`

### Références mémoire croisées
- Architecture paliers → `project_evolution_levels.md`
- Décision Level A déterministe → `project_deterministic_level_a.md`
- Roadmap architecturale → `project_architectural_roadmap.md`
- Design gap analysis → `project_design_gap_analysis.md`
- Frontend agent anatomy → `project_frontend_agent_anatomy.md`
- shadcn/ui intégration → `project_shadcn_integration.md`
- Session Plan6 → `project_plan6_session.md`
