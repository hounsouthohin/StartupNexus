# Audit Source-First (2026-03-11)

## Scope
- `agents/dev.py` (guards/fixs hardcodés)
- `config/stacks/nextjs-clerk-prisma.json`
- `prompts/stacks/nextjs-clerk-prisma/rules_dev.md`
- `scripts/pending_prescriptive_standards.json`
- `sorties.md` (dernier run observé)
- `plan.md` + `Roadmap3.0.1.md`

## Constat Exécution (preuve)
- Run observé: `build_attempted=true`, `build_success=false`, erreur dominante:
  - `Type error: Cannot find name 'Post'` sur `app/blog/[slug]/page.tsx`.
- Donc: on n'est plus principalement en blocage gate, mais en erreurs TypeScript/implémentation.

## Inventaire Guards/Fix dans dev.py (état actuel)

### Guards hardcodés (pré-build)
1. `blueprint` (`dev.py` ~442-452): bloque si fichiers obligatoires manquants.
   - Rôle: structure minimale projet.
   - Décision: **garder** (guard global core, conforme plan T008/T009).

2. `use_state_typed` (`dev.py` ~453-473): warn sur `useState([])` non typé.
   - Erreur ciblée: `never[]` / `Property ... does not exist on type never`.
   - Décision: **garder en warn** (qualité TS, non bloquant).

3. `app_router_convention` (`dev.py` ~474-557): migration auto de `app/foo.tsx` -> `app/foo/page.tsx`.
   - Erreur ciblée: structure route App Router invalide.
   - Décision: **garder temporairement** (auto-fix structurel, pas métier).

4. `app_router_api_naming` (`dev.py` ~558-590): warn si route API n'est pas `route.ts`.
   - Erreur ciblée: mauvais nom de fichier API App Router.
   - Décision: **garder en warn** (guidage).

5. `forbidden_paths` (`dev.py` ~591-610): bloque `pages/`.
   - Erreur ciblée: conflit App Router/Pages Router.
   - Décision: **garder** (structural).

6. `forbidden_imports` (`dev.py` ~611-629): warn selon tokens stack.
   - Erreur ciblée: imports incompatibles stack.
   - Décision: **garder**, piloté par config.

7. `auth_wrapping_route` (`dev.py` ~630-686): warn + auto-correction après répétition.
   - Erreur ciblée: pattern Clerk wrapper invalide en App Router.
   - Décision: **garder temporairement**, à déprécier après stabilisation source.

8. `content_guards` config-driven (`dev.py` ~688-791): moteur générique (bien aligné multi-stack).
   - Décision: **garder** (cible architecture modulaire).

## Écarts “source-first” détectés
- Plusieurs “sanitizers sémantiques” dans `shared_tools.py` réécrivaient le code juste avant build:
  - `router.query` rewrite
  - `react-router-dom` rewrite
  - `post.content` select injection
  - alias type `Post/User` rewrite
- Risque: masquent la vraie qualité de génération et biaisent les KPIs (Roadmap principe 3: éviter patches silencieux).

## Actions appliquées (ce commit)
1. `config/stacks/nextjs-clerk-prisma.json`
   - Désactivé les réécritures sémantiques automatiques:
     - `normalize_app_router_query_usage: false`
     - `normalize_react_router_dom_usage: false`
     - `normalize_post_content_select: false`
     - `normalize_unknown_state_type_aliases: false`
   - Ajouté un content guard `undeclared_prisma_type_alias` (mode warn) pour détecter `Post/User` non déclarés.

2. `prompts/stacks/nextjs-clerk-prisma/rules_dev.md`
   - Renforcé règles source:
     - Interdiction `router.query` en App Router.
     - Interdiction `react-router-dom` / `next/router`.
     - Règles explicites de typage Prisma (pas d'alias fantôme).
     - Rappel singleton Prisma `@/lib/prisma`.

3. `scripts/pending_prescriptive_standards.json`
   - Ajout de standards prescriptifs:
     - `router.query` interdit en App Router.
     - `react-router-dom` / `next/router` interdits.
     - `useAuth().user` interdit, utiliser `useUser()`.
     - `auth().userId` sans `await` interdit.

## Alignement plan.md / Roadmap3.0.1
- Conforme `plan.md`:
  - Sprint D insiste sur qualité de génération + guards sémantiques + mesures non biaisées.
- Conforme `Roadmap3.0.1` principes:
  - “Le code exécute, la configuration décide”.
  - “Standards prescriptifs”.
  - “Patches silencieux visibles/réduits”.

## Décision sur suppression des fix temporaires
- **À garder maintenant**: guards structurels (`blueprint`, `forbidden_paths`) + engine `content_guards`.
- **À réduire progressivement**: auto-corrections sémantiques hardcodées (déjà désactivées via policy pour le lot principal).
- **Critère de retrait complet**: 10 runs avec stabilité `build_attempted` + amélioration `build_success` sans dépendre de rewrites sémantiques.

## Références officielles (utilisées pour corrélation)
- Next.js App Router:
  - `use client`: https://nextjs.org/docs/app/api-reference/directives/use-client
  - `useParams` (App Router): https://nextjs.org/docs/app/api-reference/functions/use-params
  - `useRouter` depuis `next/navigation`: https://nextjs.org/docs/app/api-reference/functions/use-router
- Clerk:
  - `auth()` (server): https://clerk.com/docs/references/nextjs/auth
  - `useAuth()` (client): https://clerk.com/docs/react/reference/hooks/use-auth
  - `useUser()` (client): https://clerk.com/docs/react/reference/hooks/use-user
- Prisma:
  - Next.js + Prisma guide: https://www.prisma.io/docs/guides/nextjs
  - Prisma Client reference: https://www.prisma.io/docs/orm/reference/prisma-client-reference
