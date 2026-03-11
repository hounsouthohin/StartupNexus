# Audit Checklist (Source-First)

## Regle de preuve

Chaque conclusion doit etre appuyee par:

- une citation de doc officielle (Next.js, Clerk, Prisma)
- un fichier du pack (chemin exact)
- un niveau de severite: `P0`, `P1`, `P2`

## Axes a verifier

1. Cohérence stack config
- `config/stacks/nextjs-clerk-prisma.json` est coherent avec `schemas/stack_config.schema.json`
- aucune contradiction entre `prompt_rules`, `content_guards`, `prebuild_policies`, `import_remaps`

2. Cohérence templates
- templates aligns avec conventions officielles App Router / Clerk / Prisma
- `lib/prisma.ts` conforme singleton Prisma recommande
- `prisma.config.ts` et `prisma/schema.prisma` compatibles Prisma 7

3. Cohérence prompts
- prompts n'imposent pas de pattern obsolete (`next/router`, `react-router-dom`, etc.)
- prompts stack et prompts base n'entrent pas en conflit

4. Cohérence standards
- standards couvrent les erreurs dominantes observees en run
- standards ne recommandent pas de pattern contraire a la doc officielle

5. Cohérence guards/fixers
- seuls les guards P0 bloquants restent en `block`
- les autres sont `warn` ou supprimes
- les fixers prebuild sont generiques (famille d'erreurs), pas ultra-specifiques

6. Contrats et workflow
- contracts d'entree/sortie restent valides
- workflow continue d'exposer les metriques cle (`build_attempted`, `build_success`, `blocking_guard_id`)

## Sortie attendue de l'auditeur externe

- section `P0 Must Fix` (max 10 items)
- section `P1 Important`
- section `P2 Nice-to-have`
- section `Keep As Is` (elements conformes a conserver)
- section `Deprecated/Remove` (dette technique a retirer)
