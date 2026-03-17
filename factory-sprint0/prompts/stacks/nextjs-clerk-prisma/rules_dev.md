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
