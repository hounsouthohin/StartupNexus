## REGLES STACK — nextjs-clerk-prisma

- Authentification Clerk uniquement.
- Prisma + PostgreSQL pour la base de données.
- Next.js App Router obligatoire.
- Routes publiques: /sign-in et /sign-up.
- Middleware Clerk pour la protection des routes privées.
- Interdit: bcrypt, JWT custom, NextAuth, password/password_hash dans le schema.
