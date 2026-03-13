## REGLES STACK — nextjs-clerk-prisma

### AUTHENTIFICATION
- Auth: Clerk uniquement. Interdits: bcrypt, NextAuth, JWT custom, Passport, authMiddleware.
- app/layout.tsx doit envelopper `<html>` avec `<ClerkProvider>`.
- middleware.ts (racine) doit importer `clerkMiddleware` depuis `@clerk/nextjs/server`.
- Dans middleware Clerk, la callback doit etre `async` et appeler `await auth.protect()`.
- En server component/route handler, `auth()` doit toujours etre `await`.
- Dans `app/api/**/route.ts`, si `authorId` utilise `userId`, ajouter `if (!userId) return 401` avant l'appel Prisma.
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

### FRONTIERE SERVER / CLIENT (CRITIQUE)
- Politique par defaut: pages `app/**/page.tsx` en Server Component (sans hooks React client).
- Si un hook React est necessaire (`useState`, `useEffect`, ...), extraire la logique dans un composant client dedie sous `app/components/**`.
- Tout composant client doit avoir `"use client";` en premiere directive.
- Les pages publiques `app/page.tsx` et `app/blog/[slug]/page.tsx` doivent rester server-first; ne pas y mettre de hooks client directement.

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
- Si `post.content` est utilise au rendu, la requete Prisma doit selectionner `content`.

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
