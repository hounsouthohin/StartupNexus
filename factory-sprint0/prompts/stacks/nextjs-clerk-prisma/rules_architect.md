## REGLES STACK — nextjs-clerk-prisma

### CONTEXTE OBLIGATOIRE
Tu generes des specifications techniques pour une application web Next.js App Router qui sera implementee par un DevAgent.
Tu ne generes jamais de specs pour des logiciels de CAO, de construction, ni pour un "agent architecte metier".

### TYPE D'APPLICATION
- Framework: Next.js App Router (repertoire `app/`).
- Auth: Clerk uniquement (version selon stack_config).
- Base de donnees: Prisma + PostgreSQL (versions selon stack_config).
- UI: Tailwind CSS.
- Langage: TypeScript.

### SECTIONS OBLIGATOIRES DANS LA SPEC
La spec DOIT contenir ces sections dans cet ordre:
1. `## Vue d'ensemble`
2. `## Stack technique`
3. `## Structure des pages`
4. `## Schéma Prisma`
5. `## Authentification Clerk`
6. `## API Routes`
7. `## Composants Tailwind`

### AUTHENTIFICATION (CRITIQUE)
- `ClerkProvider` obligatoire dans `app/layout.tsx`.
- `middleware.ts` obligatoire avec `clerkMiddleware()` et `createRouteMatcher`.
- Routes publiques: `/sign-in`, `/sign-up`.
- Interdit: OAuth custom, JWT custom, bcrypt, NextAuth, passport, sessions custom.
- Ne pas mentionner `app/api/auth/route.ts`.

### BASE DE DONNEES
- Utiliser Prisma avec PostgreSQL.
- Tout modele lie a un utilisateur doit utiliser `clerkId`.
- Interdit: `password`, `password_hash`, `hashedPassword`.
- Interdit: MongoDB, MySQL, SQLite, Sequelize, TypeORM.

### UI
- Tailwind CSS uniquement.
- Interdit: Material UI, Chakra UI, Ant Design, Bootstrap.

### FORMAT DIAGRAMME MERMAID
- Produire un `flowchart LR`.
- Representer explicitement le flux pages -> auth -> API -> DB.
- Interdit: diagramme generique `graph TD` sans composants applicatifs.

### MOTS INTERDITS DANS LA SPEC
- "React.js or Angular"
- "OAuth 2.0"
- "MongoDB"
- "Express.js"
- "Flask"
- "microservices"
