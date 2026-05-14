# Brief Contract — Software Agent Factory
## Stack : `nextjs-clerk-prisma` · v1.2 (Mai 2026)

Source de vérité pour soumettre un brief. Le format est interprété directement par la factory — aucune traduction manuelle.

---

## 1. Schéma JSON

```json
{
  "project_name": "string (kebab-case)",
  "family":       "string? — crm | finance | hr | blog | ecommerce",
  "tags":         ["string?"],
  "brief": {
    "description":   "string — 1-3 phrases : qui utilise l'app, que fait-elle ?",
    "architecture":  "string — ownership des modèles, relations, contraintes métier non-dérivables",
    "models":        ["string — Prisma DSL inline, une string par modèle"],
    "pages": [
      {
        "path":      "string — commence par /",
        "auth":      "boolean — true = Clerk, false = public",
        "page_type": "\"list\" | \"create\" | \"detail\" | \"custom\"",
        "model":     "string? — PascalCase, obligatoire si page_type=list ou detail"
      }
    ],
    "pages_detail": { "/chemin": "string — description fonctionnelle pour le LLM" },
    "routes":        [{ "method": "POST|DELETE|PUT|PATCH", "path": "string" }],
    "user_flows":    ["string — acteur → action → résultat"]
  }
}
```

---

## 2. Règles par champ

### `architecture`
Décrit les relations d'ownership et les contraintes métier non-dérivables.

**Ce qui doit y être :**
- Relations entre modèles (`Post lié à Category via categoryId`)
- Owner_field non standard (`owner_field=authorId` sur Comment)
- Règles métier spéciales (ex : seul l'auteur peut modifier)

**Ce qui est inutile — déjà géré automatiquement :**
| Instruction redondante | Géré par |
|---|---|
| `NE PAS appeler auth()` sur les pages publiques | `pages[].auth: false` → déterministe |
| `getPublished()` vs `getAll()` | champ `status` détecté → déterministe |
| `Mutations via Server Actions` | invariant de stack |
| `Les pages /x sont protégées` | `pages[].auth: true` → déterministe |

### `models`
Champs obligatoires sur **chaque** modèle, y compris les entités enfant :
```
id        String   @id @default(uuid())
userId    String
createdAt DateTime @default(now())
@@index([userId])
```
Pièges fréquents : `@default("draft")` (guillemets **doubles**), `String?` (pas `String | null`).

### `pages`
- `page_type = "list"` ou `"detail"` → `model` obligatoire
- `page_type = "create"` → `model` omis (la factory le déduit du chemin parent)
- `auth: false` → la factory omet `auth()` automatiquement dans `page.tsx`

### `pages_detail`
Description lue par le LLM pour la logique UI. Format recommandé :
```
"Liste des factures. Affiche : numéro, statut, date d'échéance.
Bouton 'Nouvelle facture' → /invoices/new.
Bouton 'Supprimer' → Server Action deleteInvoice(id).
État vide : 'Aucune facture.'. [INTERACTIVE]"
```
`[INTERACTIVE]` = la page a des boutons ou un formulaire React.
Formulaires : préciser chaque champ (type HTML, required) + Server Action + redirect.

### `routes`
Optionnel. Documente les Server Actions. Ne pas créer de routes API pour les mutations CRUD — elles sont générées automatiquement.

### `user_flows`
Flux utilisateur pour le Journey Validator (score `user_flows_coverage`).
Format : `"acteur → action → résultat"`. Prévoir ≥ 1 flow par action principale.

---

## 3. Exemple complet — personal-blog (auth mixte)

```json
{
  "project_name": "personal-blog",
  "family": "blog",
  "tags": ["public_pages", "mixed_auth"],
  "brief": {
    "description": "Blog personnel. L'auteur gère ses articles depuis son tableau de bord privé. Les visiteurs lisent les articles publiés sans compte.",
    "architecture": "SaaS single-tenant. Post lié à Category via categoryId. Comment lié à Post via postId (owner_field=authorId). Tableau de bord privé (auth), lectures publiques sur /blog sans compte.",
    "models": [
      "Category { id String @id @default(uuid()), name String, userId String, createdAt DateTime @default(now()), @@index([userId]) }",
      "Post { id String @id @default(uuid()), title String, excerpt String?, status String @default(\"draft\"), categoryId String, userId String, createdAt DateTime @default(now()), @@index([userId]), @@index([categoryId]), @@index([status]) }",
      "Comment { id String @id @default(uuid()), content String, postId String, authorId String, createdAt DateTime @default(now()), @@index([postId]) }"
    ],
    "pages": [
      { "path": "/blog",           "auth": false, "page_type": "list",   "model": "Post"     },
      { "path": "/blog/new",       "auth": false, "page_type": "create"                      },
      { "path": "/dashboard",      "auth": true,  "page_type": "list",   "model": "Post"     },
      { "path": "/categories",     "auth": true,  "page_type": "list",   "model": "Category" },
      { "path": "/categories/new", "auth": true,  "page_type": "create"                      }
    ],
    "pages_detail": {
      "/blog":           "Liste des posts publiés. Affiche : titre, extrait, date. Lien 'Écrire' → /blog/new. État vide : 'Aucun article publié.'. [INTERACTIVE]",
      "/blog/new":       "Formulaire de création. Champs : titre (text, required), extrait (textarea, optionnel), categoryId (text, required). Submit → createPost({ title, excerpt, categoryId }) → redirect /dashboard. [INTERACTIVE]",
      "/dashboard":      "Liste de TOUS les articles de l'auteur (drafts + published). Affiche : titre, statut (badge : draft=gris, published=vert), date. Bouton 'Supprimer' → deletePost(id). État vide : 'Aucun article.'. [INTERACTIVE]",
      "/categories":     "Liste des catégories. Affiche : nom, date. Bouton 'Nouvelle catégorie' → /categories/new. Bouton 'Supprimer' → deleteCategory(id). État vide : 'Aucune catégorie.'. [INTERACTIVE]",
      "/categories/new": "Formulaire de création. Champ : nom (text, required). Submit → createCategory({ name }) → redirect /categories. [INTERACTIVE]"
    },
    "routes": [
      { "method": "POST",   "path": "/api/posts" },
      { "method": "DELETE", "path": "/api/posts/[id]" }
    ],
    "user_flows": [
      "Un visiteur lit les articles publiés : /blog → postService.getPublished() sans auth",
      "L'auteur écrit un article : /blog/new → createPost() → redirect /dashboard",
      "L'auteur gère ses articles : /dashboard → postService.getAll(userId) avec auth",
      "L'auteur supprime un article : bouton Supprimer → deletePost(id)",
      "L'auteur crée une catégorie : /categories/new → createCategory() → redirect /categories"
    ]
  }
}
```

---

## 4. Ce que la factory supporte (Mai 2026)

### Supporté ✅
| Feature | Notes |
|---|---|
| 3 modèles Prisma avec relations 1-N | max 3 modèles validé |
| Toutes les pages `auth: true` (Type A) | projet-hub, contact-crm, leave-manager |
| Pages publiques `auth: false` + `getPublished()` | Type D — auth mixte |
| Entités enfant avec `userId` direct | obligatoire sur tous les modèles |
| Server Actions CRUD déterministes | `create`/`delete` via générateur Python |
| Reviewer IDOR + correction pass | COHERENT sec=100 |
| `page-client.tsx` déterministes (list + create) | stubs UI réels, lockés |

### Non supporté ❌
| Feature | Priorité |
|---|---|
| Pagination exposée (`take`/`skip`) | Phase 4 |
| Enums Prisma (`Status`, `Role`) | Phase 3 |
| Relations 2 niveaux imbriqués | Phase 5 |
| Many-to-many | Phase 3 |
| Soft delete (`deletedAt`) | Phase 5 |
| Multi-tenant (`organizationId`) | Phase 7 |

---

## 5. Checklist avant de soumettre

```
[ ] project_name en kebab-case
[ ] description : ≥ 1 phrase métier claire
[ ] architecture : ownership + relations uniquement (pas les règles stack invariantes)
[ ] models : tous ont userId + createdAt + @@index([userId])
[ ] models : @default("...") avec guillemets DOUBLES
[ ] pages : page_type explicite sur chaque page
[ ] pages : page_type=list/detail → model obligatoire
[ ] pages_detail : entrée pour chaque page + [INTERACTIVE] si boutons/formulaire
[ ] pages_detail : formulaires décrivent champs + Server Action + redirect
[ ] user_flows : ≥ 1 flow par action principale
```

---

## 6. Changelog

| Version | Date | Changements |
|---|---|---|
| 1.0 | Mars 2026 | Structure initiale |
| 1.1 | Mai 2026 | + `pages[].model`, `auth: false`, règle entités enfant |
| 1.2 | Mai 2026 | + `page_type` obligatoire · document raccourci · `architecture` simplifiée (stack invariants retirés) |
