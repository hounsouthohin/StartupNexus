## REGLES STACK — nextjs-clerk-prisma

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
  ✅ `const items = await prisma.model.findMany()` sans `select` — type complet infere automatiquement, aucun risque.
  ✅ `select` avec TOUS les champs du type local inclus dans le select.
  ❌ `let items: Model[] = await prisma.model.findMany({ select: { id: true, name: true } })` si `Model` a des champs supplementaires (ex: `authorId`) — erreur TypeScript.

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
