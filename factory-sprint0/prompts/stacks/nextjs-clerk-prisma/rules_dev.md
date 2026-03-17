## REGLES STACK — nextjs-clerk-prisma

### RÈGLE ABSOLUE — FORCE-DYNAMIC OBLIGATOIRE (VÉRIFIÉE AVANT BUILD — VIOLATION = BLOCAGE DÉFINITIF)

`export const dynamic = 'force-dynamic'` est OBLIGATOIRE dans CHAQUE fichier qui appelle Prisma au runtime.

OBLIGATOIRE dans TOUTE page `app/**/page.tsx` qui appelle prisma :
  ✅ Première ligne du fichier (avant les imports) : `export const dynamic = 'force-dynamic';`

OBLIGATOIRE dans TOUT handler `app/api/**/route.ts` qui appelle prisma :
  ✅ Première ligne du fichier (avant les imports) : `export const dynamic = 'force-dynamic';`

RAISON : Next.js `next build` tente de pré-rendre (prerender) les pages et routes API en mode statique.
Si Prisma est appelé pendant ce prerender, il échoue avec `PrismaClientKnownRequestError: Can't reach database server`
car aucune base de données n'existe dans l'environnement de build.
`force-dynamic` désactive le prerender statique et force le rendu à la demande (runtime uniquement).

INTERDIT — symptôme bloquant :
  ❌ Omettre `force-dynamic` dans une page ou route qui appelle prisma.findMany() / prisma.create() / etc.
  ❌ Ajouter `export const revalidate = 0` à la place — insuffisant pour les route handlers.
  ❌ Tenter de corriger l'erreur "Can't reach database server" en modifiant prisma/schema.prisma — ce n'est PAS un problème de schema.

Pattern complet d'un route handler correct :
```ts
export const dynamic = 'force-dynamic';
import { NextResponse } from 'next/server';
import { auth } from '@clerk/nextjs/server';
import prisma from '@/lib/prisma';

export async function GET() {
  const { userId } = await auth();
  if (!userId) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  const items = await prisma.model.findMany({ where: { authorId: userId } });
  return NextResponse.json(items);
}
```

Cette règle est vérifiée automatiquement. Toute violation bloque le build définitivement.

### RÈGLE ABSOLUE — APP ROUTER DATA FETCHING (VÉRIFIÉE AVANT BUILD — VIOLATION = BLOCAGE DÉFINITIF)

Dans TOUTES les pages `app/**/page.tsx` et composants server :

INTERDIT (APIs Pages Router — incompatibles avec `app/`) :
  ❌ export async function getServerSideProps(...)
  ❌ export async function getStaticProps(...)
  ❌ export async function getStaticPaths(...)

OBLIGATOIRE — Server Component App Router :
  ✅ export default async function Page() { const data = await prisma.model.findMany(); return <div>{data}</div>; }
  ✅ Pour ISR : export const revalidate = 60;
  ✅ Pour routes dynamiques : export async function generateStaticParams() { ... }

Toute page `app/**` DOIT être un async Server Component qui récupère les données directement.
Cette règle est vérifiée automatiquement. Toute violation bloque le build définitivement.

### RÈGLE ABSOLUE — PRISMA SINGLETON (VÉRIFIÉE AVANT BUILD — VIOLATION = BLOCAGE DÉFINITIF)

Dans TOUT fichier `app/api/**/route.ts` et tout fichier métier :

INTERDIT :
  ❌ import { PrismaClient } from '@prisma/client'
  ❌ const prisma = new PrismaClient()
  ❌ new PrismaClient({ ... })

OBLIGATOIRE — copier EXACTEMENT cette ligne en tête du fichier :
  ✅ import prisma from '@/lib/prisma'

Le singleton `lib/prisma.ts` gère la connexion. Ne jamais instancier PrismaClient directement.
Cette règle est vérifiée automatiquement. Toute violation bloque le build sans possibilité de run_build.

### RÈGLE ABSOLUE — GUARD AUTH DANS TOUT HANDLER API (GET, POST, PUT, PATCH, DELETE)

`if (!userId)` est OBLIGATOIRE dans CHAQUE handler qui utilise `userId`, sans exception.
Cela inclut les handlers GET qui filtrent par `authorId: userId` — même un GET expose des données privées si `userId` est null.

Pattern OBLIGATOIRE — GET handler liste (filtrée par utilisateur) :
```ts
export async function GET() {
  const { userId } = await auth();
  if (!userId) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  const items = await prisma.model.findMany({ where: { authorId: userId } });
  return NextResponse.json(items);
}
```

Pattern OBLIGATOIRE — POST/PUT/PATCH handler mutation :
```ts
export async function POST(request: Request) {
  const { userId } = await auth();
  if (!userId) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  const body = await request.json();
  const result = CreateSchema.safeParse(body);
  if (!result.success) return NextResponse.json({ error: result.error }, { status: 400 });
  const item = await prisma.model.create({ data: { ...result.data, authorId: userId } });
  return NextResponse.json(item);
}
```

INTERDIT :
  ❌ `const { userId } = await auth(); const items = await prisma.model.findMany({ where: { authorId: userId } });` — guard absent
  ❌ Utiliser `userId` dans `where:`, `data:`, ou n'importe quelle opération Prisma sans avoir d'abord vérifié `if (!userId)`

### RÈGLE ABSOLUE — authorId DANS LES MUTATIONS PRISMA

`authorId` dans `prisma.*.create()` ou `prisma.*.update()` doit TOUJOURS être `userId` (Clerk auth, déjà guardé).
INTERDIT : inclure `authorId` dans le Zod schema du body — c'est une donnée serveur, jamais client.

  ✅ `prisma.model.create({ data: { ...result.data, authorId: userId } })`
  ❌ `const CreateSchema = z.object({ ..., authorId: z.string().optional() })` — TypeScript error garantie
  ❌ `const { authorId } = await request.json()` — authorId NE vient JAMAIS du body

Après le guard `if (!userId) return 401`, TypeScript narrowe `userId` en `string` — utilisation directe sans cast.

### AUTHENTIFICATION
- Auth: Clerk uniquement. Interdits: bcrypt, NextAuth, JWT custom, Passport, authMiddleware.
- app/layout.tsx doit envelopper `<html>` avec `<ClerkProvider>`.
- middleware.ts (racine) doit importer `clerkMiddleware` depuis `@clerk/nextjs/server`.
- Dans middleware Clerk, la callback doit etre `async` et appeler `await auth.protect()`.
- En server component/route handler, `auth()` doit toujours etre `await`.
- Dans `app/api/**/route.ts`, si `authorId` utilise `userId`, ajouter `if (!userId) return 401` avant l'appel Prisma.
- IMPORT OBLIGATOIRE dans tout `app/api/**/route.ts` qui appelle `auth()` : `import { auth } from '@clerk/nextjs/server'` — sans cet import, TypeScript leve `Cannot find name 'auth'`.
- IMPORT OBLIGATOIRE dans tout route handler qui retourne une reponse JSON : `import { NextResponse } from 'next/server'`.
- RÈGLE ABSOLUE — guard `if (!userId)` dans TOUT handler API : voir section dédiée ci-dessus "GUARD AUTH DANS TOUT HANDLER API" — le pattern GET avec guard est OBLIGATOIRE, violation = blocage structurel définitif.
- En client component (`"use client"`), imports `@clerk/nextjs/server` interdits.
- `useAuth().user` interdit; utiliser `useUser()` pour l'objet user.
- `app/api/auth/route.ts` interdit.
- Si pages auth custom, utiliser les routes catch-all Clerk uniquement: `app/sign-in/[[...sign-in]]/page.tsx` et `app/sign-up/[[...sign-up]]/page.tsx`.
- Signature typée obligatoire pour `app/api/**/route.ts`: `request: Request` et `params` typé.

### UI / COMPOSANTS
- UI: Tailwind CSS uniquement.
- Librairies UI externes interdites: shadcn/ui, @radix-ui, @headlessui.
- Imports `@/components/ui/*` interdits.
- Navigation App Router uniquement: `router.query`, `getServerSideProps`, `next/router`, `react-router-dom` interdits sous `app/**`.
- Callbacks `map/filter/reduce` doivent etre typées si l'inference TypeScript est absente.
- En TypeScript strict, `useState([])` sans type generique est interdit; typer explicitement les tableaux (`useState<PostSummary[]>([])`).
- RÈGLE TYPESCRIPT STRICT — `let` sans type : Interdit de declarer `let x;` ou `let x = []` sans type explicite puis assigner dans try/catch. TypeScript strict infere `any` ou `never[]` et refuse a la compilation.
  ❌ `let tasks; try { tasks = await prisma.task.findMany(); } catch { tasks = []; }`
  ❌ `let tasks = []; try { tasks = await prisma.task.findMany(); } catch { tasks = []; }` — `[]` infere `never[]`
  ✅ PATTERN RECOMMANDÉ (evite tout try/catch) : `const tasks = await prisma.task.findMany({ ... }).catch(() => []);`
  ✅ PATTERN ALTERNATIF : `import type { Task } from '@prisma/client'; let tasks: Task[] = []; try { tasks = await prisma.task.findMany(); } catch { tasks = []; }`

### FRONTIERE SERVER / CLIENT (CRITIQUE)
- Politique par defaut: pages `app/**/page.tsx` en Server Component (sans hooks React client).
- Si un hook React est necessaire (`useState`, `useEffect`, ...), extraire la logique dans un composant client dedie sous `app/components/**`.
- Tout composant client doit avoir `"use client";` en premiere directive.
- Toutes les pages `app/**/page.tsx` doivent rester server-first par defaut; si des hooks React sont necessaires, extraire la logique dans un composant client dedie sous `app/components/**`.

### BASE DE DONNEES
- Le schema Prisma autorise est `prisma/schema.prisma`; `prisma.config.ts` reste template stack.
- Prisma 7: `schema.prisma` DOIT toujours contenir `datasource db { provider = "postgresql" }`.
- Prisma 7: `datasource db` dans `schema.prisma` ne doit pas declarer `url = env(...)`.
- `generator client` doit utiliser `provider = "prisma-client-js"`.
- `lib/prisma.ts` doit utiliser `PrismaPg` (`@prisma/adapter-pg`) avec `new PrismaClient({ adapter })`.
- Dans `app/api/**/route.*`, interdits: import direct `@prisma/client` et `new PrismaClient()`; utiliser `import prisma from '@/lib/prisma'`.
- Champs `password` et `password_hash` interdits avec Clerk.
- Si un requirement impose des champs/contraintes Prisma (ex: `slug @unique`, `content`), ils sont obligatoires a l'identique.
- Les types utilises dans pages/composants doivent etre resolvables (inference, type local, ou import type explicite).
- Si un champ d'un modele Prisma est utilise au rendu (ex: `item.description`, `post.content`), la requete Prisma doit explicitement le selectionner via `select: { champ: true }`.
- TYPES PRISMA + SELECT : Si `select` partiel est utilise, NE PAS declarer un type local avec plus de champs que le select — TypeScript error garantie (champ manquant). Deux options valides :
  ✅ RECOMMANDÉ : `const items = await prisma.model.findMany()` SANS select — type complet infere automatiquement, zero risque TypeScript.
  ✅ `select` avec TOUS les champs du type local inclus dans le select (y compris `authorId` si le type le declare).
  ❌ `let items: Book[] = []; items = await prisma.book.findMany({ select: { id, title } })` si `Book` declare `authorId` — TypeScript refuse, `authorId` manquant dans le select.
  RÈGLE PRATIQUE : eviter `select` dans les pages de listing. N'utiliser `select` que si le type local ne contient QUE les champs selectionnés.

### SCRIPTS package.json OBLIGATOIRES
- build: `next build`
- dev: `next dev`
- start: `next start`
- lint: `next lint`
- test: `jest`

### SECURITE
- Toutes les entrees utilisateur doivent etre validees avec Zod.
- Secrets en dur interdits.

### VARIABLES D'ENVIRONNEMENT (.env.local) — OBLIGATOIRE
- `.env.local` doit contenir: `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`, `CLERK_SECRET_KEY`, `DATABASE_URL`.
- `NEXT_PUBLIC_CLERK_SECRET_KEY` interdit.
- `DATABASE_URL` prefixe `NEXT_PUBLIC_` interdit.
