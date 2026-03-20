# Règles Conformité — Stack nextjs-clerk-prisma (Per-File v2)

Ces règles s'appliquent lors de la supervision inline d'UN fichier à la fois.

## Mapping fichier → requirements

### Route Handler `app/api/X/route.ts`

Concerne les requirements "API Route: METHOD /api/X".

Un handler est conforme si :
1. Le fichier contient `export async function METHOD(` (structure)
2. Le handler accède à Prisma pour lire/écrire des données réelles (sémantique)
3. Le handler retourne une réponse avec les données pertinentes

**Non conforme sémantiquement :**
- Handler qui retourne uniquement `NextResponse.json({})` ou `NextResponse.json({ message: 'ok' })`
- Handler qui ne fait aucun accès Prisma pour une route de données
- Handler GET qui retourne des données hardcodées (ex: `posts: []`) sans lire la base

### Page `app/X/page.tsx`

Concerne les requirements "Page: /X" ou "Page: /X/[param]".

Une page est conforme si :
1. Elle contient `export default function` ou `export default async function` (structure)
2. Elle affiche des données pertinentes au brief (sémantique)
3. Pour une page de liste → elle récupère les données depuis la base (prisma ou API route)
4. Pour une page de détail → elle récupère la ressource par ID

**Non conforme sémantiquement :**
- Page qui ne rend rien de pertinent (juste un titre H1)
- Page de dashboard sans données
- Page de liste qui affiche un tableau/liste vide sans accès Prisma

### Modèle Prisma `prisma/schema.prisma`

Concerne les requirements "Modèle Prisma: X" et les features nécessitant un modèle.

Un modèle est conforme si :
1. Le bloc `model X { ... }` existe (structure)
2. Il contient les champs demandés par le brief (sémantique)
3. Les types des champs sont cohérents avec l'usage (ex: `String`, `DateTime`, `Boolean`)

**Champs attendus par défaut (stack Clerk/Prisma) :**
- `id String @id @default(cuid())`
- `authorId String` pour les ressources par utilisateur (pas de FK vers User)
- `createdAt DateTime @default(now())`
- `updatedAt DateTime @updatedAt`

### Fichier utilitaire `lib/X.ts`

Concerne les requirements de features transversales (ex: "Envoi d'email", "Calcul de score").

Conforme si le fichier exporte les fonctions décrites dans les requirements.

## Ce qui N'EST PAS à vérifier ici

- Fichiers templates (middleware.ts, app/layout.tsx, lib/prisma.ts, jest.config.js, etc.) → hors scope
- Routes Clerk (`/api/webhooks/**`) → hors scope
- Qualité du code TypeScript (types précis, etc.) → rôle du build

## Calibration des seuils pour cette stack

| Situation | Verdict | Confidence |
|-----------|---------|-----------|
| Handler API retourne `{}` sans Prisma | needs_fix | 0.85 |
| Page vide sans données alors que brief demande une liste | needs_fix | 0.80 |
| Modèle Prisma sans champ `authorId` pour ressource utilisateur | needs_fix | 0.75 |
| Handler GET sans filtre `authorId` (données privées) | needs_fix | 0.70 |
| Page avec données hardcodées au lieu de Prisma | needs_fix | 0.70 |
| Modèle Prisma incomplet mais partiellement présent | needs_fix | 0.60 |
| Fichier partiellement conforme (>50% implémenté) | ok | — |

## Cas particuliers

- `middleware.ts` : fichier template, toujours conforme → `skipped`
- `app/layout.tsx` : fichier template, toujours conforme → `skipped`
- `app/globals.css` : non pertinent pour la conformité → `skipped`
- Routes Clerk : `middleware.ts` gère l'auth → ne pas chercher `/api/auth/**`
