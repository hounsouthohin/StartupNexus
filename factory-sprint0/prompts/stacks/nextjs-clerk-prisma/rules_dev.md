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

### 8 — SCHEMA PRISMA : PRÉ-GÉNÉRÉ, NE PAS RÉÉCRIRE

`prisma/schema.prisma` est **pré-généré par le pipeline** avant que tu n'écrives le moindre fichier.
Il est déjà présent et CORRECT dans le dossier projet.

- **NE JAMAIS appeler** `write_file("prisma/schema.prisma", ...)` — ce fichier est protégé.
- **NE JAMAIS appeler** `write_file("prisma.config.ts", ...)` — idem.
- **NE JAMAIS appeler** `write_file("lib/prisma.ts", ...)` — idem.
- Si tu as besoin de connaître les modèles disponibles : lis le bloc SCHÉMA PRISMA dans ton contexte système.
- INTERDIT : réécrire ou « corriger » le schema — il fait autorité.

### 9 — HANDLERS TYPÉS (violation = TS7006 / TS7031)

Les callbacks d'événements React et les fonctions de destructuring DOIVENT avoir un type explicite.

```ts
// ✅ OBLIGATOIRE
onChange={(e: React.ChangeEvent<HTMLInputElement>) => setValue(e.target.value)}
onSubmit={(e: React.FormEvent<HTMLFormElement>) => { e.preventDefault(); handleSubmit(); }}

// ❌ INTERDIT — TS7006 : "Parameter 'e' implicitly has an 'any' type"
onChange={(e) => setValue(e.target.value)}
onSubmit={(e) => { e.preventDefault(); ... }}
```

Pour les destructurings en paramètre de fonction :
```ts
// ✅ OBLIGATOIRE
function Component({ id }: { id: string }) { ... }

// ❌ INTERDIT — TS7031 : "Binding element 'id' implicitly has 'any' type"
function Component({ id }) { ... }
```

### 10 — PROPRIÉTÉS PRISMA TYPÉES (violation = TS2339)

N'accéder qu'aux propriétés déclarées dans `prisma/schema.prisma`. Un champ absent du schema provoque TS2339.

```ts
// ✅ OBLIGATOIRE — propriétés issues du schema uniquement
const tasks = await prisma.task.findMany();
// task.title, task.completed sont valides SI déclarés dans le model Task

// ❌ INTERDIT si 'deadline' absent du schema Task
task.deadline

// Pattern sûr pour accès à une ressource unique
const item = await prisma.task.findUnique({ where: { id } });
if (!item) return NextResponse.json({ error: 'Not found' }, { status: 404 });
```

### 11 — IMPORTS ROUTE HANDLERS (violation = TS2552 / TS2305)

Dans tout fichier `app/api/**/route.ts`, les imports DOIVENT être présents en tête de fichier.

```ts
// ✅ OBLIGATOIRE — toujours présent en première ligne après dynamic
import { NextResponse } from 'next/server';
import { auth } from '@clerk/nextjs/server';
import prisma from '@/lib/prisma';

// ❌ INTERDIT — TS2552 : "Cannot find name 'NextResponse'. Did you mean 'Response'?"
// (oubli de l'import NextResponse)
```

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

### 12 — NOMS DE SPEC EXACTS (violation = routes/modèles introuvables)

Utilise EXACTEMENT les noms définis dans la spec — jamais de traduction ni de synonyme.

```
✅ Product, /api/products, ProductList
❌ Produit, /api/items, Products (pluriel non spécifié)
```

### 13 — APP ROUTER EXCLUSIF (violation = build crash / routes ignorées)

Tous les fichiers doivent être dans `app/` — jamais dans `pages/`.

```
✅ app/dashboard/page.tsx, app/api/products/route.ts
❌ pages/dashboard.tsx, pages/api/products.ts
```

### 14 — CHAMPS OBLIGATOIRES MODÈLE PRISMA (violation = TS2339 / migration échouée)

Chaque modèle Prisma DOIT avoir ces deux champs :

```prisma
id        String   @id @default(uuid())
createdAt DateTime @default(now())
```

### 15 — .ENV.LOCAL OBLIGATOIRE (violation = Clerk/Prisma non initialisés)

Le fichier `.env.local` DOIT exister à la racine du projet avec ce format exact :

```
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_placeholder
CLERK_SECRET_KEY=sk_test_placeholder
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
```

### 16 — CHAMPS INTERDITS SCHEMA PRISMA (violation = faille sécurité)

INTERDIT dans `prisma/schema.prisma` : tout champ `password`, `passwordHash`, `passwordDigest` ou dérivé.
Clerk gère l'authentification — aucun stockage de credential côté Prisma.
