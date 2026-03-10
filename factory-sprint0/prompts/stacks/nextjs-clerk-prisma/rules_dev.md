## REGLES STACK — nextjs-clerk-prisma

### AUTHENTIFICATION
- Clerk exclusif pour auth (INTERDIT: bcrypt, NextAuth, JWT custom, Passport)
- Implementer <ClerkProvider> dans app/layout.tsx
- Creer middleware.ts avec clerkMiddleware() et createRouteMatcher
- NE PAS generer app/api/auth/route.ts

### CLERK V6 — CHANGEMENTS CRITIQUES API (breaking changes vs v5)
- Dans `clerkMiddleware` : `auth` est un OBJET (pas une fonction) — utiliser `auth.protect()` (INTERDIT: `auth().protect()`)
- Callback `clerkMiddleware` OBLIGATOIREMENT `async` — utiliser `await auth.protect()`
- `createRouteMatcher` OBLIGATOIRE de `@clerk/nextjs/server` (INTERDIT: fonction custom `isPublicRoute` maison)
- Dans Server Components et API Routes : `auth()` retourne une Promise — TOUJOURS `await auth()` (INTERDIT: sans await)
- Hooks client (`useAuth`, `useUser`) : importer de `@clerk/nextjs` (INTERDIT: de `@clerk/nextjs/server`)
- API Route Handlers App Router (`app/api/**/route.ts`) DOIVENT typer les paramètres:
  `export async function PUT(request: Request, { params }: { params: { id: string } })`
  (INTERDIT: `export async function PUT(request, { params })` qui déclenche TS implicit any)

### UI / COMPOSANTS
- Tailwind CSS uniquement
- INTERDIT: shadcn/ui, @radix-ui, @headlessui, librairies de composants externes
- INTERDIT: import depuis @/components/ui/*
- TypeScript strict: les callbacks de tableaux (`map`, `filter`, etc.) doivent avoir des paramètres typés explicitement si le type n'est pas inféré (INTERDIT: `(post) => ...` non typé).

### BASE DE DONNEES
- Prisma (schema.prisma) avec clerkId
- INTERDIT: champ password/password_hash
- Executer prisma_migrate apres ecriture schema.prisma
- Quand un requirement contient `Modèle Prisma: <Model> avec champs ...`, reproduire EXACTEMENT tous les champs et contraintes dans `prisma/schema.prisma` (ex: `slug @unique`, `content String`) — aucun champ requis ne doit être omis.

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
