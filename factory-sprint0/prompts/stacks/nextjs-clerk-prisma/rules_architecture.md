# Règles Architecture — Stack nextjs-clerk-prisma

## Imports critique à vérifier

### Import Clerk : server vs client

Dans un fichier `app/api/**/*.ts` (route handler) :
- `from '@clerk/nextjs/server'` ✅ — correct
- `from '@clerk/nextjs'` ❌ — provoque une erreur de build (package client importé côté serveur)

Dans un fichier `app/**/*.tsx` avec `'use client'` :
- `from '@clerk/nextjs'` ✅ — correct (useAuth, useUser, useClerk)
- `from '@clerk/nextjs/server'` ❌ — interdit dans Client Component

### Import Prisma

Tout fichier qui accède à Prisma DOIT utiliser :
- `import prisma from '@/lib/prisma'` ✅ — singleton

Ces patterns sont architecturalement incorrects :
- `new PrismaClient()` ❌ — connexion directe non singleton
- `import { PrismaClient } from '@prisma/client'` ❌
- `import prisma from '../lib/prisma'` (chemin relatif) ❌

### Import composants UI

Cette stack utilise Tailwind CSS uniquement. Les imports suivants sont architecturalement incorrects :
- `from '@/components/ui/*'` ❌ — composants shadcn non générés
- `from 'shadcn/ui'` ❌
- `from '@radix-ui/*'` ❌

## Cohérence Prisma Schema

Pour un fichier `app/api/X/route.ts` utilisant `prisma.x.findMany()` :
- Le modèle `X` (capitalisé) DOIT exister dans `prisma/schema.prisma`
- Si le modèle n'existe pas → incohérence architecturale (confidence 0.9)

### Vérification obligatoire des noms de champs Prisma

Pour chaque opération `prisma.X.create({data: {...}})` ou `prisma.X.update({data: {...}})` dans le fichier reçu :

1. Extraire les noms de champs utilisés dans `data: { champ1, champ2, ... }`
2. Localiser le modèle correspondant dans `prisma_schema` (fourni en contexte)
3. Vérifier que **chaque champ utilisé existe bien** dans le modèle Prisma

Si un champ utilisé n'existe **pas** dans le modèle → `needs_fix`, confidence **0.95**

**Exemple de violation détectable :**
- Modèle `Product` dans schema : `name String`, `description String`, `price Float`
- Route utilise : `data: { title, content, price }` → `title` et `content` sont absents du modèle
- Fix : remplacer `title` par `name`, `content` par `description`

**Exemple conforme :**
- Modèle `Product` : `name String`, `price Float`, `stock Int`
- Route : `data: { name, price, stock, authorId }` → tous les champs existent → OK

## App Router Next.js — Conventions

**Directive 'use client'**
- Tout fichier `app/**/*.tsx` qui utilise `useState`, `useEffect`, `useRef`, `useCallback`, `useMemo`, `useReducer` DOIT avoir `'use client'` en PREMIÈRE ligne
- Exception : fichiers dans `app/components/` ou `app/hooks/` avec `'use client'`

**Fichiers templates — ne pas signaler**
Ces fichiers sont des templates de stack, toujours corrects :
- `middleware.ts`
- `app/layout.tsx`
- `lib/prisma.ts`
- `jest.config.js`, `jest.setup.js`
- `next.config.js`, `tsconfig.json`
- `.env.local`, `prisma.config.ts`

## Cohérence avec le plan Architect

Si un fichier `app/api/X/route.ts` est généré mais que la route `/api/X` n'est PAS dans `plan.api_routes` :
- Ce peut être un fichier parasite → signaler avec confidence 0.6-0.7

Si un fichier `app/X/page.tsx` est généré mais que la page `/X` n'est PAS dans `plan.pages` :
- Idem → signaler si confidence > 0.6

## Seuils spécifiques à cette stack

| Situation | Confidence |
|-----------|-----------|
| Clerk server importé dans un Client Component | 0.95 |
| Prisma direct instantiation (`new PrismaClient`) | 0.9 |
| Modèle Prisma référencé mais absent du schema | 0.9 |
| Import chemin relatif Prisma | 0.75 |
| Fichier hors plan (parasite) | 0.65 |
| Hook React sans 'use client' | 0.85 |
