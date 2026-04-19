## RÈGLES STACK — nextjs-clerk-prisma

1. **FORCE-DYNAMIC (SERVER ONLY)** : `export const dynamic = 'force-dynamic';` PREMIÈRE LIGNE uniquement dans les **Server Components** (`app/**/page.tsx` sans hooks React) et les route handlers (`app/api/**/route.ts`). INTERDIT dans les Client Components.

2. **USE CLIENT (PRIORITÉ ABSOLUE)** : tout composant avec `useState`, `useEffect` ou tout hook React DOIT avoir `"use client"` en **ligne 1 absolue** — avant tout autre code. Un Client Component n'a JAMAIS `export const dynamic` (inutile : les Client Components sont toujours dynamiques).

3. **PRISMA SINGLETON** : `import prisma from '@/lib/prisma'` — JAMAIS `new PrismaClient()`.

4. **AUTH GUARD** : `const { userId } = await auth(); if (!userId) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });` AVANT tout accès Prisma. Après le guard, `userId` est `string` (non-nullable).

5. **AUTHORID SERVEUR** : `authorId`/`userId` vient de `auth()` UNIQUEMENT — JAMAIS du body/request.

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

18. **OWNERSHIP CHECK** : avant tout `prisma.model.update()` ou `prisma.model.delete()`, vérifier que l'enregistrement appartient à l'utilisateur :
    ```ts
    const record = await prisma.model.findUnique({ where: { id } });
    if (!record || record.userId !== userId) return NextResponse.json({ error: 'Forbidden' }, { status: 403 });
    ```
    JAMAIS faire un update/delete sans vérification préalable d'ownership.

19. **PAGES AVEC DONNÉES RÉELLES** : toute page listant des entités DOIT appeler `prisma.model.findMany({ where: { userId } })` et afficher les résultats dans le JSX. Un `<h1>` seul sans données est INTERDIT. Les pages doivent aussi inclure un état vide ("Aucun élément") si la liste est vide.

20. **AUTH REDIRECT PAGES** : dans les Server Components protégés, utiliser `redirect('/sign-in')` (depuis `next/navigation`) si `!userId` — JAMAIS retourner null ou un composant vide.

21. **LOADING STATES** : tout dossier de page avec fetch Prisma DOIT avoir un fichier `loading.tsx` adjacent avec un skeleton ou spinner. JAMAIS laisser une page sans état de chargement.

22. **DATA ACCESS LAYER** : tout accès Prisma depuis une page DOIT passer par `lib/services/<model>.service.ts`. Les pages n'importent JAMAIS prisma directement — elles importent le service correspondant. Les routes API peuvent importer prisma directement.

23. **PRISMA INDEXES** : tout champ utilisé dans un `where` fréquent (`userId`, `slug`, `email`) DOIT avoir `@@index([champ])` dans le schema Prisma.

24. **REDIRECT APRÈS MUTATION** : tout formulaire Client Component qui soumet un POST/PATCH DOIT appeler `router.push('/resource')` après succès via `useRouter()` de `next/navigation`.

25. **CREATEDDAT AUTO** : JAMAIS passer `createdAt: new Date()` dans un `prisma.model.create()` — le schema a `@default(now())`, c'est automatique.

26. **SERVICE DAL — PATTERN OBLIGATOIRE** : pour chaque modèle `ModelName`, créer `lib/services/modelName.service.ts` (camelCase) exportant un objet unique :
    ```ts
    export const modelNameService = {
      findMany: (userId: string) =>
        prisma.modelName.findMany({ where: { userId }, orderBy: { createdAt: 'desc' } }),
      findUnique: async (id: string, userId: string) => {
        const r = await prisma.modelName.findUnique({ where: { id } })
        if (!r || r.userId !== userId) return null
        return r
      },
      create: (data: CreateModelNameInput, userId: string) =>
        prisma.modelName.create({ data: { ...data, userId } }),
      update: async (id: string, data: UpdateModelNameInput, userId: string) => {
        const r = await prisma.modelName.findUnique({ where: { id } })
        if (!r || r.userId !== userId) throw new Error('Forbidden')
        return prisma.modelName.update({ where: { id }, data })
      },
      delete: async (id: string, userId: string) => {
        const r = await prisma.modelName.findUnique({ where: { id } })
        if (!r || r.userId !== userId) throw new Error('Forbidden')
        await prisma.modelName.delete({ where: { id } })
      },
    }
    ```
    - Si le modèle utilise `authorId` au lieu de `userId`, remplacer `userId` par `authorId` partout.
    - Si le modèle n'a pas de champ owner direct (ex: `Card` lié à `Board`), omettre les checks ownership et utiliser `boardId` ou l'id parent dans `findMany`.
    - Import dans les pages : `import { modelNameService } from '@/lib/services/modelName.service'`
    - JAMAIS exporter des fonctions nommées (`export function getAll`) — toujours l'objet service.
