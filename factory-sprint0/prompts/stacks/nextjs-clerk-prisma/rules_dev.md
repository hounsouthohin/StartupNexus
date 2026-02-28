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

### UI / COMPOSANTS
- Tailwind CSS uniquement
- INTERDIT: shadcn/ui, @radix-ui, @headlessui, librairies de composants externes
- INTERDIT: import depuis @/components/ui/*

### BASE DE DONNEES
- Prisma (schema.prisma) avec clerkId
- INTERDIT: champ password/password_hash
- Executer prisma_migrate apres ecriture schema.prisma

### SCRIPTS package.json OBLIGATOIRES
- "build": "next build"
- "dev": "next dev"
- "start": "next start"
- "lint": "next lint"
- "test": "jest"

### SECURITE
- Validation Zod sur toutes les entrées utilisateur
- Pas de secrets en dur, utiliser .env.local
