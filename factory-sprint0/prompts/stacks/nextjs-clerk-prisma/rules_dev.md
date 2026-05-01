## RÈGLES STACK — nextjs-clerk-prisma (Option A — Server Actions, Avril 2026)

1. **FORCE-DYNAMIC (SERVER ONLY)** : `export const dynamic = 'force-dynamic';` PREMIÈRE LIGNE uniquement dans les **Server Components** (`app/**/page.tsx` sans hooks React) et les webhook handlers (`app/api/webhooks/**/route.ts`). INTERDIT dans les Client Components et les Server Actions.

2. **USE CLIENT (PRIORITÉ ABSOLUE)** : tout composant avec `useState`, `useEffect` ou tout hook React DOIT avoir `"use client"` en **ligne 1 absolue** — avant tout autre code. Un Client Component n'a JAMAIS `export const dynamic` (inutile : les Client Components sont toujours dynamiques).

3. **PRISMA SINGLETON** : `import prisma from '@/lib/prisma'` — JAMAIS `new PrismaClient()`.

4. **AUTH GUARD SERVER ACTIONS** : dans `app/**/actions.ts`, pattern obligatoire :
    ```ts
    const { userId } = await auth();
    if (!userId) throw new Error('Unauthorized');
    ```
    Après le guard, `userId` est `string` (non-nullable). JAMAIS `return NextResponse.json(...)` dans une Server Action — ce sont des fonctions, pas des handlers HTTP.

5. **AUTHORID SERVEUR** : `authorId`/`userId` vient de `auth()` UNIQUEMENT — JAMAIS du body/formulaire.

6. **TAILWIND ONLY** : INTERDIT `shadcn/ui`, `@radix-ui`, `@headlessui`, `@/components/ui/*`.

7. **TABLEAUX TYPÉS** : `const items: ModelType[] = await modelService.getAll(userId)` — JAMAIS `let items = []` (TypeScript infère `never[]`). Typer explicitement les tableaux.

8. **FICHIERS PROTÉGÉS** : JAMAIS `write_file` sur `prisma/schema.prisma`, `lib/prisma.ts`, `prisma.config.ts`, `lib/types.ts`, `lib/schemas.ts`, `lib/services/*` — pré-générés par le pipeline. Écrire UNIQUEMENT `app/**/actions.ts` et `app/**/page.tsx`.

9. **TYPES PARAMÈTRES** : type explicite sur chaque paramètre de callback React (`e: React.ChangeEvent<HTMLInputElement>`) et de destructuring (`{ id }: { id: string }`).

10. **PROPRIÉTÉS SCHEMA** : accéder uniquement aux champs déclarés dans `prisma/schema.prisma`.

11. **IMPORTS SERVER ACTIONS** : dans `app/**/actions.ts`, imports obligatoires :
    ```ts
    'use server'
    import { auth } from '@clerk/nextjs/server'
    import { revalidatePath } from 'next/cache'
    import { xxxService } from '@/lib/services/xxx.service'
    import { CreateXxxSchema, UpdateXxxSchema } from '@/lib/schemas'
    ```
    JAMAIS `NextResponse` dans les Server Actions.

12. **NOMS SPEC EXACTS** : noms de modèles, services et composants EXACTEMENT comme dans la spec — pas de traduction ni de synonyme.

13. **APP ROUTER ONLY** : JAMAIS `pages/` — tout dans `app/`.

14. **CHAMPS OBLIGATOIRES** : tout modèle Prisma DOIT avoir `id String @id @default(uuid())` et `createdAt DateTime @default(now())`.

15. **ENV.LOCAL REQUIS** : `.env.local` DOIT exister avec `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`, `CLERK_SECRET_KEY`, `DATABASE_URL`.

16. **PAS DE PASSWORDS** : INTERDIT tout champ `password`/`passwordHash`/`passwordDigest` dans schema — Clerk gère l'authentification.

17. **ZOD VALIDATION DANS SERVER ACTIONS** : toute Server Action de mutation DOIT valider les données avec le schéma Zod pré-généré :
    ```ts
    const parsed = CreateXxxSchema.safeParse(data)
    if (!parsed.success) throw new Error(parsed.error.message)
    await xxxService.create(userId, parsed.data)
    ```
    INTERDIT de passer `data` directement au service sans validation. Le champ `userId` vient toujours de `auth()`, jamais des données validées.

18. **OWNERSHIP VIA SERVICE** : le service DAL pré-généré inclut déjà la vérification d'ownership dans `getById`, `update` et `delete`. Ne PAS re-vérifier manuellement dans les Server Actions — appeler simplement le service.

19. **PAGES AVEC DONNÉES RÉELLES** : toute page listant des entités DOIT appeler le service correspondant et afficher les résultats. Un `<h1>` seul sans données est INTERDIT. Les pages doivent inclure un état vide ("Aucun élément") si la liste est vide :
    ```ts
    const items = await xxxService.getAll(userId)
    ```

20. **AUTH REDIRECT PAGES** : dans les Server Components protégés, utiliser `redirect('/sign-in')` (depuis `next/navigation`) si `!userId` — JAMAIS retourner null ou un composant vide.

21. **LOADING STATES** : tout dossier de page avec fetch service DOIT avoir un fichier `loading.tsx` adjacent avec un skeleton ou spinner. JAMAIS laisser une page sans état de chargement.

22. **DATA ACCESS LAYER** : tout accès Prisma depuis une page ou Server Action DOIT passer par `lib/services/<model>.service.ts`. JAMAIS importer prisma directement dans `actions.ts` ou `page.tsx` — uniquement via le service. Exception : les webhook handlers (`app/api/webhooks/**`) peuvent importer prisma directement.

23. **PRISMA INDEXES** : tout champ utilisé dans un `where` fréquent (`userId`, `slug`, `email`) DOIT avoir `@@index([champ])` dans le schema Prisma.

24. **REVALIDATION APRÈS MUTATION** : toute Server Action de mutation DOIT appeler `revalidatePath('/resource')` après l'opération service pour invalider le cache Next.js. Les Client Components appellent les Server Actions directement (pas de `fetch` vers `/api`).

25. **CREATEDDAT AUTO** : JAMAIS passer `createdAt: new Date()` dans un `prisma.model.create()` — le schema a `@default(now())`, c'est automatique.

26. **SERVICE DAL — CONTRAT FIXE (pré-généré, NE PAS recréer)** : les services sont dans `lib/services/<model-name>.service.ts`, générés automatiquement. Méthodes disponibles — utiliser EXACTEMENT ces noms :

    ```ts
    // Import : import { modelNameService } from '@/lib/services/model-name.service'

    modelNameService.getAll(ownerId: string)           → Promise<ModelName[]>
    modelNameService.getById(ownerId: string, id: string) → Promise<ModelName | null>
    modelNameService.create(ownerId: string, data: CreateModelNameInput) → Promise<ModelName>
    modelNameService.update(id: string, data: UpdateModelNameInput) → Promise<ModelName>
    modelNameService.delete(ownerId: string, id: string) → Promise<void>
    ```

    - JAMAIS appeler `findMany`, `findUnique`, `getExpenses`, `getAllTasks` — ces méthodes n'existent pas
    - JAMAIS exporter des fonctions nommées (`export function getAll`) — toujours l'objet service
    - JAMAIS recréer le fichier service — il est pré-généré et protégé

27. **CREATEINPUT SANS CHAMP OWNER** : `CreateModelNameInput` dans `lib/types.ts` et `lib/schemas.ts` ne contient JAMAIS `userId`, `authorId` ou tout autre champ d'ownership — ces champs viennent de `auth()`. Un type d'entrée contenant `userId` est une faille de sécurité (TS2322 probable).
    ```ts
    // ✅ CORRECT
    export type CreateExpenseInput = { amount: number; category: string; description: string; date: string }
    // ❌ INTERDIT
    export type CreateExpenseInput = { amount: number; userId: string; ... }
    ```

28. **LOGGING STRUCTURÉ** : utiliser `import logger from '@/lib/logger'` dans les Server Actions et les webhooks. Chaque erreur serveur doit être loguée avec contexte :
    ```ts
    } catch (error) {
      logger.error({ error, userId, action: 'createModel' }, 'Erreur création')
      throw new Error('Internal server error')
    }
    ```

29. **GESTION ERREURS PRISMA** : utiliser `handlePrismaError` depuis `@/lib/prisma-errors` dans les blocs catch des Server Actions et webhooks :
    ```ts
    import { handlePrismaError } from '@/lib/prisma-errors'
    } catch (error) {
      const { message } = handlePrismaError(error)
      throw new Error(message)
    }
    ```
    `handlePrismaError` retourne `{ status: 409, message: 'Conflict' }` pour P2002, `{ status: 404, message: 'Not found' }` pour P2025.

30. **HEALTHCHECK + WEBHOOKS PROTÉGÉS** : ne pas créer `app/api/health/route.ts` ni `app/api/webhooks/clerk/route.ts` — ces fichiers sont pré-générés par le pipeline. Ne pas les réécrire avec `write_file`.
