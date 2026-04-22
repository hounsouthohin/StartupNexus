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
- Tout modele lie a un utilisateur doit utiliser `authorId` (String, lié au userId Clerk).
- Interdit: `password`, `password_hash`, `hashedPassword`.
- Interdit: MongoDB, MySQL, SQLite, Sequelize, TypeORM.

### EXTRACTION DES ENTITÉS — RÈGLE ABSOLUE
Le nom des modèles Prisma DOIT être extrait du brief. Deux cas :

**Brief avec modèle explicite** (ex: "Modele Prisma : Post {...}") → utiliser EXACTEMENT ce nom.
**Brief sans modèle explicite** → inférer depuis les mots-clés du domaine dans le brief :
  - "blog" / "publication" / "cms" → modèle `Post`
  - "todo" / "tâche" / "task" / "reminder" / "liste" → modèle `Task`
  - "todo app avec listes partagees" → `TodoList` (liste) + `Task` (item)
  - "produit" / "product" → modèle `Product`
  - "commande" / "order" → modèle `Order`
  - Si incertain : choisir le nom le plus court et le plus DIRECT depuis les mots du brief.

INTERDIT ABSOLU : générer un modèle nommé `Article`, `Book`, `Goal`, `Item`, `Workout` si le brief ne mentionne pas ce mot exactement.
INTERDIT ABSOLU : générer moins de 5 requirements — TOUT brief, même vague, DOIT produire :
  1. `Modèle Prisma: <Entité> avec authorId, createdAt`
  2. `Page liste: /<entités>` — affichage des items
  3. `Page détail: /<entités>/[id]` — détail d'un item
  4. `API Route: GET /api/<entités>` — liste filtrée par userId
  5. `API Route: POST /api/<entités>` — création avec authorId
INTERDIT : copier les noms d'entités depuis les standards RAG — ce sont des patrons techniques, pas des noms à réutiliser.

### UI
- Tailwind CSS uniquement.
- Interdit: Material UI, Chakra UI, Ant Design, Bootstrap.

### FORMAT DIAGRAMME MERMAID
- Produire un `flowchart LR`.
- Representer explicitement le flux pages -> auth -> API -> DB.
- Interdit: diagramme generique `graph TD` sans composants applicatifs.

### PAGES INTERACTIVES — MARQUAGE OBLIGATOIRE DANS pages_detail
Marquer avec `[INTERACTIVE]` uniquement les pages qui COMBINENT fetch de données serveur
ET boutons/handlers d'action (Modifier, Supprimer, Changer statut, Approuver, etc.).
Ces pages ont besoin d'un split Server Component (fetch) + Client Component (handlers).

```
"/tasks":     "Liste des tâches avec boutons Modifier et Supprimer [INTERACTIVE]"
"/tasks/[id]":"Détail avec bouton Terminer et formulaire commentaire inline [INTERACTIVE]"
"/tasks/new": "Formulaire de création (Client Component uniquement — pas de [INTERACTIVE])"
```

Règle de décision :
- Page avec données + boutons d'action → `[INTERACTIVE]` obligatoire
- Page formulaire pur (création/édition uniquement) → PAS de `[INTERACTIVE]`, déjà Client Component
- Page lecture seule (dashboard métriques, détail sans bouton) → PAS de `[INTERACTIVE]`

Ce marquage déclenche la génération d'un `page-client.tsx` séparé dans le DevAgent.

### MOTS INTERDITS DANS LA SPEC
- "React.js or Angular"
- "OAuth 2.0"
- "MongoDB"
- "Express.js"
- "Flask"
- "microservices"
