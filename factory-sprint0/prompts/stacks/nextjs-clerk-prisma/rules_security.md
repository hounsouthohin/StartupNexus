# Règles Sécurité — Stack nextjs-clerk-prisma

## Pattern d'auth Clerk v6 (OBLIGATOIRE)

Dans cette stack, l'auth check se fait via Clerk v6 :

```typescript
// Pattern valide — App Router (Server Component / Route Handler)
import { auth } from '@clerk/nextjs/server';
const { userId } = await auth();
if (!userId) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
```

Patterns INVALIDES à signaler (severity HIGH) :
- Handler utilise `prisma.X.findMany()` ou `prisma.X.create()` etc. SANS appel à `auth()` ou `getAuth()` avant.
- Handler expose `userId` dans la réponse JSON (ne doit jamais être retourné au client).

## Filtrage authorId (OBLIGATOIRE pour GET /liste)

```typescript
// Pattern valide
const posts = await prisma.post.findMany({
  where: { authorId: userId }
});

// Pattern invalide (severity MEDIUM) — expose TOUTES les données
const posts = await prisma.post.findMany();
```

## Vérification propriété par ID (OBLIGATOIRE pour GET/PUT/DELETE /[id])

```typescript
// Pattern valide
const post = await prisma.post.findUnique({ where: { id } });
if (!post || post.authorId !== userId) {
  return NextResponse.json({ error: 'Forbidden' }, { status: 403 });
}
```

Un handler GET/PUT/DELETE par ID qui ne vérifie pas `authorId === userId` → severity MEDIUM.

## Routes Clerk à NE PAS auditer

Ne pas signaler de problèmes sur :
- `app/api/webhooks/**` — webhooks Clerk, auth différente (secret Clerk)
- `middleware.ts` — géré par Clerk directement

## Contexte multi-utilisateur

Cette stack gère du contenu par utilisateur (SaaS). Toute exposition de données sans filtre userId est potentiellement une faille IDOR (Insecure Direct Object Reference). Sois particulièrement attentif aux routes GET sans `where: { authorId: userId }`.

## Severité résumée

| Situation | Severity |
|-----------|----------|
| Prisma sans auth() | high |
| GET liste sans where authorId | medium |
| GET/PUT/DELETE [id] sans vérif authorId | medium |
| POST sans validation body | low |
| userId exposé dans réponse | medium |
