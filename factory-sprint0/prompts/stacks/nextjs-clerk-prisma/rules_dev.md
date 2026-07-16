## RÈGLES STACK — nextjs-clerk-prisma (Option A — Server Actions)
## Portée : uniquement les fichiers que le LLM génère
## LLM génère : pages custom (page.tsx sans model), page-client.tsx [INTERACTIVE], webhooks route.ts
## Tout le reste est déterministe (protégé) : lib/types.ts, lib/schemas.ts, lib/services/*, app/**/actions.ts, page.tsx avec model, page-client.tsx CRUD

---

> **[FATAL]** = TS error ou BUILD_FAILED garanti si violé | **[IMPORTANT]** = comportement erroné ou sécurité | **[BONNE PRATIQUE]** = qualité

---

1. **[IMPORTANT] FORCE-DYNAMIC (SERVER ONLY)** : `export const dynamic = 'force-dynamic'` PREMIÈRE LIGNE uniquement dans les Server Components (`app/**/page.tsx`). INTERDIT dans les Client Components.

2. **[FATAL] USE CLIENT (PRIORITÉ ABSOLUE)** : tout composant avec `useState`, `useEffect` ou tout hook React DOIT avoir `"use client"` en **ligne 1 absolue** — avant tout import.

3. **[IMPORTANT] COMPOSANTS UI** : utiliser UNIQUEMENT les composants shadcn/ui listés dans le bloc DESIGN SYSTEM du context (`Button`, `Input`, `Textarea`, `Label`, `Card`, `Badge`, `Table`, `Select`). INTERDIT : `@radix-ui` direct, `@headlessui`, tout composant non listé dans DESIGN SYSTEM.

4. **[FATAL] TABLEAUX TYPÉS** : `const items: SerializedModelType[] = await modelService.getAll(userId)` — JAMAIS `let items = []` (TypeScript infère `never[]`). Le service retourne `SerializedXxx` (dates = string), NE PAS annoter avec le type Prisma brut (TS2345 fatal).

5. **[FATAL] FICHIERS PROTÉGÉS** : JAMAIS `write_file` sur `prisma/schema.prisma`, `lib/prisma.ts`, `prisma.config.ts`, `lib/types.ts`, `lib/schemas.ts`, `lib/services/*`, `app/**/actions.ts`, `app/**/page-client.tsx` CRUD, `app/**/page.tsx` avec model, `middleware.ts`, `app/layout.tsx`.
Le LLM génère UNIQUEMENT : pages custom `app/**/page.tsx` (sans `model`), `app/**/page-client.tsx` [INTERACTIVE] custom, `app/api/webhooks/**/route.ts`.

6. **[FATAL] TYPES PARAMÈTRES** : type explicite sur chaque paramètre de callback React (`e: React.ChangeEvent<HTMLInputElement>`) et de destructuring (`{ id }: { id: string }`).

7. **[FATAL] NOMS SPEC EXACTS** : noms de modèles, services et composants EXACTEMENT comme dans CONTRACTS.md — pas de traduction ni de synonyme.

8. **[IMPORTANT] APP ROUTER ONLY** : JAMAIS `pages/` — tout dans `app/`.

9. **[IMPORTANT] PAGES AVEC DONNÉES RÉELLES** : toute page **déclarant des `data_fetches`** DOIT appeler le service correspondant et afficher les résultats (avec un état vide si la liste est vide). EXCEPTION : une page de présentation dont le contrat dit `data_fetches: []` (landing statique, hero) NE DOIT PAS fetcher — un `<h1>` + texte + lien sont légitimes. Ne jamais inventer un fetch absent du contrat.

10. **[IMPORTANT] AUTH REDIRECT PAGES** : dans les Server Components protégés, utiliser `redirect('/sign-in')` (depuis `next/navigation`) si `!userId` — JAMAIS retourner null.

11. **[IMPORTANT] DATA ACCESS LAYER** : tout accès données depuis `page.tsx` DOIT passer par `lib/services/<model>.service.ts`. JAMAIS importer prisma directement dans page.tsx. Exception : webhook handlers.

12. **[FATAL] SERVICE DAL — LIRE CONTRACTS.md (pré-généré, NE PAS recréer)** : les services sont dans `lib/services/<model-name>.service.ts`. **Lire `CONTRACTS.md` à la racine du projet** pour la liste exacte des méthodes disponibles par modèle. CONTRACTS.md est la source de vérité — pas cette liste.

    Méthodes clés selon le contexte :
    ```ts
    // Import : import { modelNameService } from '@/lib/services/model-name.service'

    // Pages privées
    modelNameService.getAll(userId, page?)            → Promise<SerializedXxx[]>
    modelNameService.getById(userId, id)               → Promise<SerializedXxx>  (notFound() si absent)
    modelNameService.getAllWithRelations(userId, page?) → Promise<SerializedXxx[]>  (si relations)
    modelNameService.getByIdWithRelations(userId, id)  → Promise<SerializedXxx>   (si relations)

    // Pages publiques (sans auth)
    modelNameService.getPublicAll()   → liste publique (si modèle a `isPublic Boolean`, `published Boolean`, ou enum de statut)
    modelNameService.getPublicById(id)                 → Promise<SerializedXxx>
    modelNameService.getBySlug(slug)                   → Promise<SerializedXxx>    (si champ slug @unique)
    ```

    - JAMAIS appeler `prisma.*` directement depuis page.tsx
    - JAMAIS recréer un fichier service — il est pré-généré et protégé
    - **JAMAIS inventer une méthode absente de CONTRACTS.md** — `getPublished`, `getActiveCount`, `getByStatus`, `countBy` et toute méthode non listée dans CONTRACTS.md N'EXISTENT PAS → TS2339 fatal au build.
    - `getBy{Parent}Id(userId, parentId)` EXISTE uniquement pour les modèles ayant une FK (ex: `getByProjectId` pour Task avec `projectId`). Vérifier CONTRACTS.md — absent = n'existe pas pour ce modèle.
    - **Pour les agrégations** (compter les actifs, sommer les budgets, filtrer par statut) : utiliser `getAll(userId)` puis calculer en TypeScript. Ex : `const active = projects.filter(p => p.status === 'active')` / `const total = active.reduce((s, p) => s + (p.budget ?? 0), 0)`
    - **Pour les données d'enfants liés** : utiliser `getAllWithRelations(userId)` ou `getByIdWithRelations(userId, id)` sur le modèle parent — les enfants sont inclus dans la réponse.

13. **[IMPORTANT] FICHIERS PRÉ-GÉNÉRÉS** : ne pas créer `app/api/health/route.ts`, `app/api/webhooks/clerk/route.ts`, `app/components/navigation.tsx`, `app/loading.tsx`, `app/error.tsx`, `app/not-found.tsx`, `app/sitemap.ts`, `app/robots.ts` — pré-générés par le pipeline. Le `generateMetadata()` des pages détail publiques ([slug]) est aussi pré-généré dans leur page.tsx.

14. **[BONNE PRATIQUE] PAGE-CLIENT ÉTAT VIDE — PAGES LIST CUSTOM** : tout `page-client.tsx` de type list DOIT gérer `items.length === 0` :
    ```tsx
    if (items.length === 0) {
      return <p className="text-gray-500 text-center py-8">Aucun élément pour l'instant.</p>
    }
    ```

15. **[IMPORTANT] PAGE-CLIENT BOUTON DELETE — ID DIRECT** : appeler `deleteX(item.id)` directement, JAMAIS `new FormData()`. Bouton `type="button"` :
    ```tsx
    <button type="button" onClick={() => deleteTask(item.id)}>Supprimer</button>
    ```

16. **[FATAL] PAGE-CLIENT USESTATE TYPÉ** : `useState` avec tableau DOIT avoir un type générique — `useState<SerializedXxx[]>([])`. Sans type, TypeScript infère `never[]` → TS2345 fatal.

17. **[FATAL] FORMULAIRES — USEACTIONSTATE OBLIGATOIRE (React 19)** : tout formulaire dans un `page-client.tsx` custom [INTERACTIVE] DOIT utiliser `useActionState` depuis `'react'` :
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

18. **[FATAL] PARAMS DYNAMIQUES (Next.js 15)** : les pages dynamiques (`[id]`, `[slug]`) doivent typer `params` comme `Promise` :
    ```tsx
    export default async function Page({ params }: { params: Promise<{ id: string }> }) {
      const { id } = await params
      // ...
    }
    ```
    `params.id` SANS `await` → TS2339 fatal en Next.js 15.

19. **[FATAL] IMPORT LINK OBLIGATOIRE** : tout fichier utilisant `<Link href="...">` DOIT importer `Link` explicitement :
    ```tsx
    import Link from 'next/link'
    ```
    Oublier cet import → `Cannot find name 'Link'` → BUILD FAILED fatal.

20. **[FATAL] PAGES PUBLIQUES — INTERDIT AUTH()** : toute page dont la spec indique `auth_required: false` (home `/`, listing public, page blog publique) ne DOIT **JAMAIS** contenir `auth()`, `currentUser()` ni `redirect('/sign-in')`.
    Méthode pour pages publiques : `getPublicAll()` uniquement.
    La règle 10 (auth redirect) s'applique UNIQUEMENT aux pages `auth_required: true`.

    CORRECT :
    ```tsx
    // page publique — aucun import Clerk
    export default async function HomePage() {
      const posts = await postService.getPublicAll()
      return <main>...</main>
    }
    ```
    INTERDIT :
    ```tsx
    const { userId } = await auth()
    if (!userId) redirect('/sign-in')  // jamais sur une page publique
    ```

21. **[FATAL] RELATIONS OPTIONNELLES — OPTIONAL CHAINING** : si `SerializedXxx` déclare une relation comme optionnelle (`category?: SerializedCategory`), toujours utiliser l'optional chaining pour accéder aux champs imbriqués :
    ```tsx
    item.category?.name   // CORRECT — évite TS18048
    item.category.name    // INTERDIT si category est nullable → TS18048 fatal
    ```
    Pour garantir que la relation est chargée, utiliser `getAllWithRelations(userId)` à la place de `getAll(userId)`.
