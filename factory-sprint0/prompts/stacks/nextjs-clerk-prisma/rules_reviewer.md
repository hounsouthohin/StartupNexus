## RÈGLES STACK — nextjs-clerk-prisma

### CONTEXTE DE STACK
- Next.js 14 App Router (Server Components, Server Actions)
- Authentification : Clerk V6 — `auth()` dans les Server Components et Server Actions, `currentUser()` si besoin de l'objet user complet
- ORM : Prisma 7 — `prisma.model.method()` avec `where` clause
- Pas de Route Handlers pour les mutations (sauf webhooks Stripe) — les mutations passent exclusivement par des Server Actions (`"use server"`)

---

### IDOR — RÈGLE CRITIQUE

Une opération Prisma `update()` ou `delete()` sur un enregistrement appartenant à un utilisateur DOIT inclure `userId` dans le `where` :

```typescript
// ❌ IDOR — l'id seul ne garantit pas que l'enregistrement appartient à l'user
await prisma.project.update({ where: { id }, data: { ... } })

// ✅ CORRECT — double contrainte id + userId
await prisma.project.update({ where: { id, userId }, data: { ... } })
```

Si tu vois `where: { id }` sans `userId` sur une entité appartenant à un utilisateur → finding CRITICAL de type IDOR.

---

### SERVER ACTIONS — RÈGLE CRITIQUE

Toute Server Action qui effectue une mutation DOIT :
1. Appeler `auth()` et extraire `userId`
2. Vérifier que `userId` n'est pas null (redirection ou throw)
3. Transmettre `userId` au service comme argument explicite

```typescript
// ❌ MANQUANT — userId non transmis au service
export async function updateProject(id: string, data: UpdateProjectInput) {
  return projectService.update(id, data)
}

// ✅ CORRECT
export async function updateProject(id: string, data: UpdateProjectInput) {
  const { userId } = await auth()
  if (!userId) redirect("/sign-in")
  return projectService.update(id, userId, data)
}
```

---

### DONNÉES CROSS-USER — RÈGLE CRITIQUE

Toute requête `findMany()` ou `findFirst()` sur des enregistrements appartenant à un utilisateur DOIT filtrer par `userId` :

```typescript
// ❌ EXPOSITION CROSS-USER — retourne les enregistrements de tous les users
await prisma.project.findMany({ include: { tasks: true } })

// ✅ CORRECT
await prisma.project.findMany({ where: { userId }, include: { tasks: true } })
```

---

### GHOST SUCCESS — CONFORMITÉ

Compare les entités du brief avec le schéma Prisma et les services générés. Si le brief demande `Invoice` et que le code génère `Project`, c'est un Ghost Success → finding CRITICAL de type GHOST_SUCCESS.

Vérifie aussi que les noms de champs correspondent au brief (ex: brief dit `dueDate`, code génère `deadline` → WARNING).

---

### PAGE STUB — CONFORMITÉ

Une page est considérée comme un stub si :
- Elle ne fait aucun appel à un service ou une action
- Elle retourne du JSX statique hardcodé sans données réelles
- Elle contient des commentaires `// TODO` ou affiche des données placeholder

→ finding WARNING de type PAGE_STUB si la page est dans le user_flow principal, CRITICAL si c'est la page principale du brief.

---

### COHÉRENCE DE CHAÎNE — RÈGLE ABSOLUE

**Tout `targeted_fix` qui modifie la signature d'une fonction de service DOIT être accompagné des fixes correspondants dans tous les fichiers appelants visibles dans le contexte analysé.**

Cas concret : un fix IDOR qui ajoute `userId` comme paramètre à `service.update()` casse immédiatement les Server Actions qui appellent ce service avec l'ancienne signature. Le fix est incomplet et cause un BUILD_FAILED.

#### Exemple complet — fix IDOR avec propagation obligatoire

```typescript
// ── targeted_fix 1 : le service (DAL) ────────────────────────────────────────
// fichier : lib/services/project.service.ts
// current_code :
update: async (id: string, data: UpdateProjectInput): Promise<Project> => {
  return prisma.project.update({ where: { id }, data })
}
// fix_code :
update: async (userId: string, id: string, data: UpdateProjectInput): Promise<Project> => {
  return prisma.project.update({ where: { id, userId }, data })
}

// ── targeted_fix 2 : l'action appelante (OBLIGATOIRE) ────────────────────────
// fichier : app/projects/actions.ts
// current_code :
export async function updateProject(id: string, data: UpdateProjectInput) {
  return projectService.update(id, data)
}
// fix_code :
export async function updateProject(id: string, data: UpdateProjectInput) {
  const { userId } = await auth()
  if (!userId) redirect("/sign-in")
  return projectService.update(userId, id, data)
}
```

**Règle de vérification** : avant de finaliser `targeted_fixes`, parcours tous les fichiers actions (`app/**/actions.ts`) visibles dans le contexte. Pour chaque service corrigé, vérifie que l'action correspondante est aussi dans `targeted_fixes` avec le bon nombre d'arguments.

Si l'action n'est pas visible dans le contexte fourni, indique-le dans le `reason` du fix service : `"Action appelante non visible dans le contexte — fix service seul, vérification manuelle requise."` et downgrade le verdict à DEGRADED plutôt qu'INCOHERENT.

---

---

### NEXT.JS 14 — ANTI-PATTERNS CODE

**LINK/A ANTI-PATTERN**
En Next.js 14 App Router, `Link` génère automatiquement son propre `<a>`. Imbriquer un `<a>` dans un `<Link>` crée du HTML invalide et des erreurs d'hydration.

```tsx
// ❌ ANTI-PATTERN — double <a> dans le DOM, hydration error
<Link href="/path">
  <a className="text-blue-500">texte</a>
</Link>

// ✅ CORRECT — Next.js 14 App Router
<Link href="/path" className="text-blue-500">texte</Link>
```

Si tu vois `<Link>` avec un enfant `<a>` → finding WARNING de type LINK_A_ANTIPATTERN.

---

### CONFORMITÉ CRUD — PAGE EDIT MANQUANTE

Pour chaque modèle visible dans les fichiers, vérifier la cohérence create/edit :
- Si une action `createXxx` est visible dans `actions.ts` → une page `/xxx/[id]/edit` (ou `/dashboard/xxx/[id]/edit`) devrait exister.
- Si aucun chemin d'édition n'est détectable dans les fichiers fournis → finding WARNING de type MISSING_EDIT.

Exemple : `createRecipe` dans `actions.ts` visible mais aucun fichier d'édition fourni → MISSING_EDIT WARNING.

**Important** : downgrade à INFO si le brief ne mentionne pas explicitement de gestion (app en lecture seule, catalogue public sans modification).

---

### MIDDLEWARE — CONTRAT AUTH (nouveau check prioritaire)

Le fichier `middleware.ts` définit quelles routes sont publiques via `createRouteMatcher`.

**RÈGLE CRITIQUE** : les patterns dans `createRouteMatcher` doivent être des chemins EXACTS ou des paramètres typés (`:id`), jamais des wildcards `(.*)` sur des routes qui ont des sous-chemins auth=true.

```typescript
// ❌ MIDDLEWARE_WILDCARD — /recipes/new devient public alors que auth=true
createRouteMatcher(['/recipes(.*)'])

// ✅ CORRECT — seuls les chemins déclarés publics
createRouteMatcher(['/recipes', '/recipes/:id'])
```

Si tu vois `'/path(.*)'` dans `createRouteMatcher` pour un path autre que `/sign-in` ou `/sign-up` → finding CRITICAL de type MIDDLEWARE_WILDCARD.

---

### PAGE STUB — CHECK RENFORCÉ

Une page LLM custom est un stub si elle :
- Affiche du JSX statique sans aucun appel à un service
- Contient `// TODO` ou des données hardcodées (noms, ids, montants fixes)
- N'a aucun `await xxxService.getXxx(userId)` visible

→ finding CRITICAL PAGE_STUB si la page est dans le user_flow principal.
→ finding WARNING PAGE_STUB si la page est secondaire.

**IMPORTANT** : les pages avec `export const dynamic = 'force-dynamic'` ET un appel service dans le corps sont CORRECTES — ne pas les marquer comme stub.

---

### AUTH CONTRACT — PAGES MIXTES PUBLIC/PRIVÉ

Pour les apps avec des pages publiques ET privées :

**Pages publiques** (auth_required=false dans le spec) :
- Ne doivent PAS appeler `auth()` avec redirect — elles servent les visiteurs non connectés
- Doivent appeler `xxxService.getPublicAll()` ou `getPublicById()` — sans userId

**Pages privées** (auth_required=true dans le spec) :
- DOIVENT appeler `const { userId } = await auth()` + `if (!userId) redirect('/sign-in')`

Si une page déclarée publique appelle `auth()` avec redirect → finding MISSING_PUBLIC_ACCESS (WARNING).
Si une page déclarée privée n'appelle pas `auth()` → finding MISSING_AUTH (CRITICAL).

---

### SCORES — CALIBRATION

**security_score** :
- Part de 100
- -30 par finding IDOR, CROSS_USER_EXPOSURE ou MIDDLEWARE_WILDCARD de type CRITICAL
- -15 par finding MISSING_AUTH de type CRITICAL
- -10 par finding MIDDLEWARE_WILDCARD de type WARNING
- -5 par finding WARNING de sécurité

**coherence_score** :
- Part de 100
- -40 par finding GHOST_SUCCESS de type CRITICAL
- -20 par finding PAGE_STUB de type CRITICAL
- -15 par finding MISSING_PUBLIC_ACCESS de type CRITICAL
- -10 par finding PAGE_STUB de type WARNING
- -10 par finding MISSING_EDIT de type WARNING
- -5 par finding LINK_A_ANTIPATTERN de type WARNING
- -5 par écart de nommage mineur (WARNING)
