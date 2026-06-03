## RÈGLES STACK — nextjs-clerk-prisma (Option A — Server Actions)
## Portée : uniquement les fichiers que le LLM génère
## LLM génère : pages custom (page.tsx sans model), page-client.tsx [INTERACTIVE], webhooks route.ts
## Tout le reste est déterministe (protégé) : lib/types.ts, lib/schemas.ts, lib/services/*, app/**/actions.ts, page.tsx avec model, page-client.tsx CRUD

---

1. **FORCE-DYNAMIC (SERVER ONLY)** : `export const dynamic = 'force-dynamic'` PREMIÈRE LIGNE uniquement dans les Server Components (`app/**/page.tsx`). INTERDIT dans les Client Components.

2. **USE CLIENT (PRIORITÉ ABSOLUE)** : tout composant avec `useState`, `useEffect` ou tout hook React DOIT avoir `"use client"` en **ligne 1 absolue** — avant tout import.

3. **TAILWIND ONLY** : INTERDIT `shadcn/ui`, `@radix-ui`, `@headlessui`, `@/components/ui/*`.

4. **TABLEAUX TYPÉS** : `const items: SerializedModelType[] = await modelService.getAll(userId)` — JAMAIS `let items = []` (TypeScript infère `never[]`). Le service retourne `SerializedXxx` (dates = string), NE PAS annoter avec le type Prisma brut (TS2345 fatal).

5. **FICHIERS PROTÉGÉS** : JAMAIS `write_file` sur `prisma/schema.prisma`, `lib/prisma.ts`, `prisma.config.ts`, `lib/types.ts`, `lib/schemas.ts`, `lib/services/*`, `app/**/actions.ts`, `app/**/page-client.tsx` CRUD, `app/**/page.tsx` avec model, `middleware.ts`, `app/layout.tsx`.
Le LLM génère UNIQUEMENT : pages custom `app/**/page.tsx` (sans `model`), `app/**/page-client.tsx` [INTERACTIVE] custom, `app/api/webhooks/**/route.ts`.

6. **TYPES PARAMÈTRES** : type explicite sur chaque paramètre de callback React (`e: React.ChangeEvent<HTMLInputElement>`) et de destructuring (`{ id }: { id: string }`).

7. **NOMS SPEC EXACTS** : noms de modèles, services et composants EXACTEMENT comme dans CONTRACTS.md — pas de traduction ni de synonyme.

8. **APP ROUTER ONLY** : JAMAIS `pages/` — tout dans `app/`.

9. **PAGES AVEC DONNÉES RÉELLES** : toute page affichant des entités DOIT appeler le service correspondant et afficher les résultats. Un `<h1>` seul sans données est INTERDIT. Inclure un état vide si la liste est vide.

10. **AUTH REDIRECT PAGES** : dans les Server Components protégés, utiliser `redirect('/sign-in')` (depuis `next/navigation`) si `!userId` — JAMAIS retourner null.

11. **DATA ACCESS LAYER** : tout accès données depuis `page.tsx` DOIT passer par `lib/services/<model>.service.ts`. JAMAIS importer prisma directement dans page.tsx. Exception : webhook handlers.

12. **SERVICE DAL — LIRE CONTRACTS.md (pré-généré, NE PAS recréer)** : les services sont dans `lib/services/<model-name>.service.ts`. **Lire `CONTRACTS.md` à la racine du projet** pour la liste exacte des méthodes disponibles par modèle.

    Méthodes clés selon le contexte :
    ```ts
    // Import : import { modelNameService } from '@/lib/services/model-name.service'

    // Pages privées
    modelNameService.getAll(userId, page?)            → Promise<SerializedXxx[]>
    modelNameService.getById(userId, id)               → Promise<SerializedXxx>  (notFound() si absent)
    modelNameService.getAllWithRelations(userId, page?) → Promise<SerializedXxx[]>  (si relations)
    modelNameService.getByIdWithRelations(userId, id)  → Promise<SerializedXxx>   (si relations)

    // Pages publiques (sans auth)
    modelNameService.getPublicAll()                    → Promise<SerializedXxx[]>
    modelNameService.getPublicById(id)                 → Promise<SerializedXxx>
    modelNameService.getPublished()                    → Promise<SerializedXxx[]>  (si status enum)
    modelNameService.getBySlug(slug)                   → Promise<SerializedXxx>    (si champ slug)

    // Enfants d'un parent (CROSS_ENTITY)
    childService.getBy{Parent}Id(userId, parentId)     → Promise<SerializedChild[]>
    ```

    - JAMAIS appeler `prisma.*` directement depuis page.tsx
    - JAMAIS recréer un fichier service — il est pré-généré et protégé
    - **JAMAIS inventer une méthode absente de CONTRACTS.md** — `getActiveCount`, `getByStatus`, `countBy`, `sumField` et toute méthode non listée N'EXISTENT PAS → TS2339 fatal au build.
    - **Pour les agrégations** (compter les actifs, sommer les budgets, filtrer par statut) : utiliser `getAll(userId)` puis calculer en TypeScript. Ex : `const active = projects.filter(p => p.status === 'active')` / `const total = active.reduce((s, p) => s + (p.budget ?? 0), 0)`

13. **FICHIERS PRÉ-GÉNÉRÉS** : ne pas créer `app/api/health/route.ts`, `app/api/webhooks/clerk/route.ts`, `app/components/navigation.tsx`, `app/loading.tsx`, `app/error.tsx`, `app/not-found.tsx` — pré-générés par le pipeline.

14. **PAGE-CLIENT ÉTAT VIDE — PAGES LIST CUSTOM** : tout `page-client.tsx` de type list DOIT gérer `items.length === 0` :
    ```tsx
    if (items.length === 0) {
      return <p className="text-gray-500 text-center py-8">Aucun élément pour l'instant.</p>
    }
    ```

15. **PAGE-CLIENT BOUTON DELETE — ID DIRECT** : appeler `deleteX(item.id)` directement, JAMAIS `new FormData()`. Bouton `type="button"` :
    ```tsx
    <button type="button" onClick={() => deleteTask(item.id)}>Supprimer</button>
    ```

16. **PAGE-CLIENT USESTATE TYPÉ** : `useState` avec tableau DOIT avoir un type générique — `useState<SerializedXxx[]>([])`. Sans type, TypeScript infère `never[]` → TS2345 fatal.

17. **FORMULAIRES — USEACTIONSTATE OBLIGATOIRE (React 19)** : tout formulaire dans un `page-client.tsx` custom [INTERACTIVE] DOIT utiliser `useActionState` depuis `'react'` :
    ```tsx
    'use client'
    import { useActionState } from 'react'   // ← 'react', JAMAIS 'react-dom'

    const [error, formAction, isPending] = useActionState(
      async (_prev: unknown, formData: FormData) => {
        try { await createXxx(formData); return null }
        catch (e) { return (e as Error).message }
      },
      null,
    )
    ```
    `useFormState` de `'react-dom'` est **SUPPRIMÉ** depuis React 19 — TS2305 fatal.

18. **PARAMS DYNAMIQUES (Next.js 15)** : les pages dynamiques (`[id]`, `[slug]`) doivent typer `params` comme `Promise` :
    ```tsx
    export default async function Page({ params }: { params: Promise<{ id: string }> }) {
      const { id } = await params
      // ...
    }
    ```
    `params.id` SANS `await` → TS2339 fatal en Next.js 15.
