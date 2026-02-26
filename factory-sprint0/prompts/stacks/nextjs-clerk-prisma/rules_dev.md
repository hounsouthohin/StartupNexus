## REGLES STACK — nextjs-clerk-prisma

### AUTHENTIFICATION
- Clerk exclusif pour auth (INTERDIT: bcrypt, NextAuth, JWT custom, Passport)
- Implementer <ClerkProvider> dans app/layout.tsx
- Creer middleware.ts avec clerkMiddleware() et createRouteMatcher
- NE PAS generer app/api/auth/route.ts

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
