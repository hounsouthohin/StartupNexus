## REGLES STACK — nextjs-clerk-prisma

### AUTHENTIFICATION
- Clerk exclusif pour auth (INTERDIT: bcrypt, NextAuth, JWT custom, Passport)
- Implementer <ClerkProvider> dans app/layout.tsx
- Creer middleware.ts avec clerkMiddleware() et createRouteMatcher
- NE PAS generer app/api/auth/route.ts
- Si des pages auth custom sont générées, utiliser OBLIGATOIREMENT les routes Catch-All Clerk:
  - `app/sign-in/[[...sign-in]]/page.tsx`
  - `app/sign-up/[[...sign-up]]/page.tsx`
  - INTERDIT: `app/sign-in/page.tsx` ou `app/sign-up/page.tsx` simples

### CLERK V6 — CHANGEMENTS CRITIQUES API (breaking changes vs v5)
- Dans `clerkMiddleware` : `auth` est un OBJET (pas une fonction) — utiliser `auth.protect()` (INTERDIT: `auth().protect()`)
- Callback `clerkMiddleware` OBLIGATOIREMENT `async` — utiliser `await auth.protect()`
- `createRouteMatcher` OBLIGATOIRE de `@clerk/nextjs/server` (INTERDIT: fonction custom `isPublicRoute` maison)
- Dans Server Components et API Routes : `auth()` retourne une Promise — TOUJOURS `await auth()` (INTERDIT: sans await)
- Dans Server Components et API Routes Next App Router : INTERDIT `auth(req)`/`auth(request)` — utiliser `await auth()` sans argument
- Hooks client (`useAuth`, `useUser`) : importer de `@clerk/nextjs` (INTERDIT: de `@clerk/nextjs/server`)
- API Route Handlers App Router (`app/api/**/route.ts`) DOIVENT typer les paramètres:
  `export async function PUT(request: Request, { params }: { params: { id: string } })`
  (INTERDIT: `export async function PUT(request, { params })` qui déclenche TS implicit any)
- INTERDIT: double annotation de `params` dans la signature (ex: `... { params }: { params: {...} }: { params: ... }`)
- INTERDIT: créer un wrapper custom `lib/auth.ts` pour encapsuler Clerk auth (userId/session). Utiliser directement `auth()` serveur, `useAuth()/useUser()` client, et `middleware.ts` officiel Clerk.

### UI / COMPOSANTS
- Tailwind CSS uniquement
- INTERDIT: shadcn/ui, @radix-ui, @headlessui, librairies de composants externes
- INTERDIT: import depuis @/components/ui/*
- TypeScript strict: les callbacks de tableaux (`map`, `filter`, etc.) doivent avoir des paramètres typés explicitement si le type n'est pas inféré (INTERDIT: `(post) => ...` non typé).
- App Router uniquement pour la navigation:
  - INTERDIT: `router.query` (pattern Pages Router) dans `app/**`.
  - INTERDIT: `getServerSideProps` dans `app/**` (Pages Router API non supportée).
  - INTERDIT: `react-router-dom` et `next/router` dans une app Next App Router.
  - CORRECT server page dynamique: `export default async function Page({ params }: { params: { slug: string } })`
  - CORRECT client component: `const params = useParams<{ slug: string }>()` depuis `next/navigation`.

### BASE DE DONNEES
- Prisma (schema.prisma) avec clerkId
- INTERDIT: champ password/password_hash
- Executer prisma_migrate apres ecriture schema.prisma
- Quand un requirement contient `Modèle Prisma: <Model> avec champs ...`, reproduire EXACTEMENT tous les champs et contraintes dans `prisma/schema.prisma` (ex: `slug @unique`, `content String`) — aucun champ requis ne doit être omis.
- TYPAGE PRISMA OBLIGATOIRE: ne jamais utiliser un alias de type non declare (`Post`, `User`, etc.) dans les pages/composants.
  - INTERDIT: `const post: Post | null = await prisma.post.findUnique(...)` sans declaration/import de `Post`.
  - CORRECT (server): laisser TypeScript inférer le type depuis `await prisma.post.findUnique(...)`, ou importer un type explicite depuis `@prisma/client`.
  - CORRECT (client): typer l'etat avec un type local declare dans le fichier, ou avec un type derive d'un schema (ex: `ReturnType<typeof PostSchema.parse>`).
- Prisma dans Next.js:
  - INTERDIT d'instancier `new PrismaClient()` dans `app/**`.
  - CORRECT: `import prisma from '@/lib/prisma'` (singleton).
  - Les annotations de type explicites doivent etre resolvables (type local, import type, ou inference).
  - Si le rendu utilise `post.content`, la requête Prisma DOIT inclure `content` dans les champs sélectionnés.
    - INTERDIT: `select: { id, title, slug, ... }` puis usage `post.content`
    - CORRECT: inclure `content: true` dans `select`, ou ne pas restreindre les champs (`findUnique` sans `select`)

### SCRIPTS package.json OBLIGATOIRES
- "build": "next build"
- "dev": "next dev"
- "start": "next start"
- "lint": "next lint"
- "test": "jest"

### SECURITE
- Validation Zod sur toutes les entrées utilisateur
- Pas de secrets en dur, utiliser .env.local

### VARIABLES D'ENVIRONNEMENT (.env.local) — OBLIGATOIRE
Créer .env.local à la RACINE du projet avec EXACTEMENT ces 3 variables :
```
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_placeholder
CLERK_SECRET_KEY=sk_test_placeholder
DATABASE_URL=postgresql://user:password@localhost:5432/todo-batch-alpha
```
- INTERDIT: NEXT_PUBLIC_CLERK_SECRET_KEY (expose le secret au bundle client)
- INTERDIT: DATABASE_URL avec préfixe NEXT_PUBLIC_
