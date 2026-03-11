# Audit Philosophie & Cohérence (2026-03-11)

## Référentiel
- `Roadmap3.0.1.md` — Principes:
  - Principe 1: le code exécute, la configuration décide.
  - Principe 2: standards prescriptifs.
  - Principe 3: boucle RAG -> Agent -> Erreur -> Learner -> RAG.
- `plan.md` — guards globaux au core, stack-specific hors core.
- `ETAPES.md` — pas de guards ajoutés "au hasard", preuve exigée.

## Verdict global
- **Direction conforme**: architecture majoritairement config-driven, standards prescriptifs actifs, drift check OK.
- **Non-conformités restantes**: hardcoding résiduel dans `dev.py`/`shared_tools.py`, prompt base architect encore partiellement stack-orienté.

## Guards essentiels gardés (P0) et pourquoi
Source principale: `config/stacks/nextjs-clerk-prisma.json` + moteur `content_guards` dans `agents/dev.py`.

- `blueprint` (core, block): empêche build sans fichiers obligatoires.
- `forbidden_paths` (core, block): empêche mélange App Router / Pages Router.
- `use_client` (content_guard, block): bloque hooks React sans directive client.
- `prisma_schema_datasource_url` (content_guard, block): cohérence Prisma 7 stack.
- `prisma_generator_provider` (content_guard, block): évite provider Prisma incompatible.
- `prisma_direct_instantiation` (content_guard, block): interdit `new PrismaClient()` côté app.
- `clerk_server_in_client` (content_guard, block): interdit import Clerk server en client.

## Guards/réécritures mis OFF et pourquoi
Source: `prebuild_policies` dans `config/stacks/nextjs-clerk-prisma.json`.

- `normalize_app_router_query_usage: false`
- `normalize_react_router_dom_usage: false`
- `normalize_post_content_select: false`
- `normalize_unknown_state_type_aliases: false`

Raison:
- Ces fixs masquaient la qualité réelle de génération.
- On privilégie correction à la source (stack rules + prompts + standards), pas patch silencieux.

## Éléments hardcodés non alignés (à migrer)

### Dans `agents/dev.py`
- **Mise à jour P1 appliquée**:
  - `use_state_typed` migré vers `content_guards`.
  - `auth_wrapping_route` migré vers `content_guards`.
  - `app_router_convention` et `app_router_api_naming` migrés vers `path_guards` déclaratifs.
- Reste hardcodé au core: `blueprint`, `forbidden_paths` (invariants structurels).

### Dans `agents/shared_tools.py`
- Plusieurs fonctions de correction stack-spécifiques vivent en Python.
- Même si pilotées par `prebuild_policies`, la logique reste couplée à la stack.
- Cible philosophie: `SanitizerRegistry` modulaire (nom de sanitizer déclaré en JSON).

### Dans `prompts/base/architect.md`
- Exemple d'output historiquement orienté stack unique.
- Action P0 appliquée: `"stack": "<stack_id_from_context>"` et mention explicite "example shape".

## Incohérences / dettes détectées

1. `create_full_standards_v1.py` contient encore beaucoup de texte legacy; gouvernance de version requise.
2. `pending_prescriptive_standards.json` peut accumuler des entrées proches (risque de bruit sémantique).
3. `qa.py`/`dev_test_agent.py` utilisent `_DEFAULT_STACK_ID` en fallback (acceptable en secours, mais limite le vrai multi-stack strict).

## Techniques perfectibles
- `trigger_contains` (substring) pour semantic guards:
  - robuste/simple, mais pas précis sur cas limites.
  - amélioration future: parser AST TS pour règles critiques.
- remaps textuels globaux:
  - risque de contexte mal ciblé.
  - amélioration: remap context-aware par scope/fichier.

## Prompts et philosophie
- `prompts/stacks/**`: globalement alignés (règles prescriptives, contextuelles, stack-driven).
- `prompts/base/**`: mieux alignés après P0, mais encore à généraliser pour neutralité multi-stack complète.

## Vérification cohérence config-runtime
- Script exécuté: `scripts/validate_config_consumption.py`
- Résultat: **OK — aucun drift déclaré** (champs stack consommés).

## Plan conseillé (suite)
1. P1: migrer progressivement les guards hardcodés non-core vers config/sanitizers nommés.
2. P1: nettoyer standards legacy et introduire versioning/obsolescence explicite.
3. P2: AST guards pour patterns Clerk/Next.js à forte criticité.
