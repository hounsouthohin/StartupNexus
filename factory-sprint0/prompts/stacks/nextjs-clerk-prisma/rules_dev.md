## REGLES STACK — nextjs-clerk-prisma

### 1 — FORCE-DYNAMIC (violation = build crash Prisma)

`export const dynamic = 'force-dynamic';` DOIT être la **première ligne** (avant les imports) de tout fichier qui appelle Prisma :
- `app/**/page.tsx` appelant prisma
- `app/api/**/route.ts` appelant prisma

```ts
export const dynamic = 'force-dynamic';
import { NextResponse } from 'next/server';
import { auth } from '@clerk/nextjs/server';
import prisma from '@/lib/prisma';
```

### 2 — PRISMA SINGLETON (violation = instances multiples / build error)

```ts
// ✅ OBLIGATOIRE
import prisma from '@/lib/prisma'

// ❌ INTERDIT
import { PrismaClient } from '@prisma/client'
const prisma = new PrismaClient()
```

### 3 — AUTH GUARD + TYPE NARROWING (violation = erreur TypeScript compilation)

`auth()` retourne `{ userId: string | null }`. Prisma attend `String` (non-nullable). TypeScript **refuse** de compiler `where: { authorId: userId }` si le guard est absent.

Pattern OBLIGATOIRE dans TOUT handler (GET, POST, PUT, PATCH, DELETE) :

```ts
const { userId } = await auth();
if (!userId) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
// Après ce guard : userId est string (plus string | null)
```

### 4 — AUTHORID CÔTÉ SERVEUR UNIQUEMENT (violation = TypeScript error)

```ts
// ✅ OBLIGATOIRE
prisma.model.create({ data: { ...body, authorId: userId } })

// ❌ INTERDIT — authorId ne vient JAMAIS du body
const CreateSchema = z.object({ authorId: z.string() })
```

### 5 — SERVER / CLIENT BOUNDARY (violation = runtime crash)

Tout composant avec `useState`, `useEffect` ou hook React DOIT avoir `"use client"` en première ligne.
Les pages `app/**/page.tsx` sont Server Components par défaut — pas de hooks React directs.

### 6 — TAILWIND UNIQUEMENT (violation = dépendance manquante)

Écrire les styles directement avec des classes Tailwind CSS.
INTERDIT : `shadcn/ui`, `@radix-ui`, `@headlessui`, `@/components/ui/*`.

### 7 — TYPESCRIPT STRICT — TABLEAUX (violation = `never[]` compilation error)

```ts
// ✅ PATTERN RECOMMANDÉ
const items = await prisma.model.findMany().catch(() => []);

// ❌ INTERDIT — TypeScript infère never[]
let items = [];
try { items = await prisma.model.findMany(); } catch { items = []; }
```

### 8 — SCHEMA PRISMA : ÉCRITURE UNIQUE OBLIGATOIRE

`prisma/schema.prisma` DOIT être écrit **une seule fois**, avec **tous les modèles métier** du brief en un seul `write_file`.

- Écrire TOUS les modèles dans un seul appel `write_file("prisma/schema.prisma", ...)`.
- Après cela : **NE PLUS RÉÉCRIRE** `prisma/schema.prisma`, même si un superviseur signale une correction.
- Si correction demandée : appliquer **une seule fois**, puis passer aux pages et routes API.
- INTERDIT : réécrire le schema à chaque itération ou combiner son écriture avec d'autres fichiers.

## Concepts Stack Obligatoires

Le code généré doit respecter explicitement ces concepts techniques de stack, même sans appel RAG:

- Versions exactes et cohérentes de `next`, `@clerk/nextjs`, `prisma`, `jest`, `ts-jest` et packages requis.
- Clerk V6: `ClerkProvider` dans `app/layout.tsx`, `clerkMiddleware` côté serveur, et logique auth conforme App Router.
- Prisma 7: séparation `schema.prisma` / `prisma.config.ts`, modèles métier complets, sans patterns obsolètes.
- `auth()` asynchrone partout côté serveur (server components et route handlers), sans dérive `auth().userId`, `useAuth`/`useUser` mal placés.
- Singleton Prisma obligatoire via `@/lib/prisma`, interdiction d'instanciation directe `new PrismaClient()`.
- Pages server component avec accès Prisma typé et patterns robustes (`findMany`, tableaux typés, gestion d'erreur propre, pas de hooks client).
- Guard `userId` nul avant toute opération Prisma liée à `authorId`/`ownerId` (`401` avant DB).
- Prisma 7: `datasource.url` interdit dans `schema.prisma` (éviter les erreurs P1012), structure canonique `generator`/`datasource`.
- TypeScript strict: aucun tableau non typé (`let arr = []`), aucun fallback `any`, types explicites sur données Prisma.
