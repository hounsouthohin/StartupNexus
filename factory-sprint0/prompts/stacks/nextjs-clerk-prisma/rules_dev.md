## RÈGLES STACK — nextjs-clerk-prisma

1. **FORCE-DYNAMIC** : `export const dynamic = 'force-dynamic';` PREMIÈRE LIGNE (avant les imports) dans tout fichier appelant Prisma (`app/**/page.tsx`, `app/api/**/route.ts`).

2. **PRISMA SINGLETON** : `import prisma from '@/lib/prisma'` — JAMAIS `new PrismaClient()`.

3. **AUTH GUARD** : `const { userId } = await auth(); if (!userId) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });` AVANT tout accès Prisma. Après le guard, `userId` est `string` (non-nullable).

4. **AUTHORID SERVEUR** : `authorId`/`userId` vient de `auth()` UNIQUEMENT — JAMAIS du body/request.

5. **USE CLIENT** : tout composant avec `useState`, `useEffect` ou hook React DOIT avoir `"use client"` en première ligne.

6. **TAILWIND ONLY** : INTERDIT `shadcn/ui`, `@radix-ui`, `@headlessui`, `@/components/ui/*`.

7. **TABLEAUX TYPÉS** : `const items: ModelType[] = await prisma.model.findMany().catch(() => []);` — JAMAIS `let items = []` (TypeScript infère `never[]`).

8. **FICHIERS PROTÉGÉS** : JAMAIS `write_file` sur `prisma/schema.prisma`, `lib/prisma.ts`, `prisma.config.ts` — pré-générés par le pipeline.

9. **TYPES PARAMÈTRES** : type explicite sur chaque paramètre de callback React (`e: React.ChangeEvent<HTMLInputElement>`) et de destructuring (`{ id }: { id: string }`).

10. **PROPRIÉTÉS SCHEMA** : accéder uniquement aux champs déclarés dans `prisma/schema.prisma`.

11. **IMPORTS ROUTES** : `import { NextResponse } from 'next/server'`, `import { auth } from '@clerk/nextjs/server'`, `import prisma from '@/lib/prisma'` OBLIGATOIRES en tête de tout route handler.

12. **NOMS SPEC EXACTS** : noms de modèles, routes et composants EXACTEMENT comme dans la spec — pas de traduction ni de synonyme.

13. **APP ROUTER ONLY** : JAMAIS `pages/` — tout dans `app/`.

14. **CHAMPS OBLIGATOIRES** : tout modèle Prisma DOIT avoir `id String @id @default(uuid())` et `createdAt DateTime @default(now())`.

15. **ENV.LOCAL REQUIS** : `.env.local` DOIT exister avec `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`, `CLERK_SECRET_KEY`, `DATABASE_URL`.

16. **PAS DE PASSWORDS** : INTERDIT tout champ `password`/`passwordHash`/`passwordDigest` dans schema — Clerk gère l'authentification.

17. **ZOD VALIDATION** : tout handler POST/PUT/PATCH DOIT valider le body avec `z.object({...}).safeParse(body)` avant tout accès Prisma. INTERDIT de passer `body` directement à `prisma.model.create/update()`. Le champ `authorId` vient toujours de `auth()`, jamais de `result.data`.
