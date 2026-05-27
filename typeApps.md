# Software Agent Factory — Carte de graduation des applications

## 1. Types d'applications cibles (stack nextjs-clerk-prisma)

| Code | Type | Exemples |
|---|---|---|
| A | CRUD SaaS simple | project-hub, contact-crm, leave-manager, invoice-tracker |
| B | Multi-tenant SaaS | Notion, Slack, Figma clone — workspaces/organisations |
| C | Marketplace / Platform | Etsy, Airbnb, Upwork clone — deux côtés |
| D | Blog / CMS | Medium clone, documentation, publishing workflow |
| E | E-commerce | Boutique, catalogue, panier, commandes |
| F | Social / Communauté | Feed, likes, follows, commentaires, notifications |
| G | Booking / Calendrier | Prise de RDV, disponibilités, créneaux |
| H | Dashboard / Analytics | Métriques, agrégations, séries temporelles |
| I | Workflow / Approbation | Processus RH, validation commandes, review content |
| J | Gestion de fichiers/documents | Uploads, versioning, permissions fichiers |

---

## 2. État actuel — Type A validé (Mai 2026)

### Ce que la factory sait faire aujourd'hui

- **3 modèles Prisma** avec relations parent-enfant (FK simple)
- **4 pages** : 2 listes + 2 formulaires de création, toutes protégées par Clerk
- **Services DAL** : getAll(userId), getById(userId, id), create(userId, data), update(userId, id, data), delete(userId, id)
- **Server Actions** : auth() + guard + service call + revalidatePath — générés par template (zéro variance LLM)
- **Sécurité** : double contrainte `where: { id, userId }` sur update/delete — vérifiée par le reviewer agent
- **Entités enfant** : userId obligatoire sur tous les modèles, même les enfants (fix Mai 2026)

### Validé sur

| Projet | Entités | Reviewer verdict |
|---|---|---|
| project-hub | Project, Task, Comment | COHERENT sec=100 après correction |
| contact-crm | Company, Contact, Interaction | COHERENT sec=100 après correction |
| leave-manager | Department, Employee, LeaveRequest | COHERENT sec=100 après correction |
| invoice-tracker | Client, Invoice, InvoiceItem | COHERENT sec=100 après correction (bug child entity fixé) |

### Limites résiduelles connues du Type A

- `tests_passed: false` — les tests Jest ne sont pas encore fonctionnels (non bloquant pour le build)
- `user_flows_covered: 2/5` — le Journey Validator ne couvre que les flows create/delete, pas les flows de lecture
- Reviewer corrige systématiquement ~3 IDOR au premier passage (services générés sans userId dans where) — acceptable car reviewer les corrige, mais idéalement à réduire à 0

---

## 3. Chemin de graduation recommandé

```
A (validé) → D (prochain test) → G → I → E → H → F → B → C → J
```

Chaque flèche = une ou deux limitations à corriger avant de passer au type suivant.

---

## 4. Carte détaillée par type

### Type D — Blog / CMS
**Nouveauté critique :** Routes à visibilité mixte — certaines pages sont publiques (auth=false), d'autres privées (auth=true)

Limitations à corriger :
| Limite | Description | Priorité |
|---|---|---|
| **L3** | Services sans filtre userId pour les modèles publics | 🔴 Bloquant |
| **L14** | Pas de getBySlug (URLs /posts/mon-titre) | 🟠 Important |
| **L11** | Many-to-many ignoré (Post ↔ Tag) | 🟠 Important |
| **L8** | Enums → string (DRAFT/PUBLISHED/ARCHIVED) | 🟡 Qualité |
| **L5** | Pas de tri par createdAt DESC | 🟡 UX |

Quand D est validé, la factory peut générer : blogs, portfolios, sites de documentation, wikis internes.

---

### Type G — Booking / Calendrier
**Nouveauté critique :** Logique métier sur les DateTime (créneaux, disponibilités, conflits)

Limitations à corriger :
| Limite | Description | Priorité |
|---|---|---|
| **L5** | Pas de tri par date | 🔴 Bloquant |
| **L6** | Pas de filtrage par statut/date | 🔴 Bloquant |
| **L8** | Enums (PENDING/CONFIRMED/CANCELLED) | 🟠 Important |

Quand G est validé, la factory peut générer : outils de prise de RDV, plannings, systèmes de réservation simple.

---

### Type I — Workflow / Approbation
**Nouveauté critique :** Transitions de statut multi-étapes avec règles métier

Limitations à corriger :
| Limite | Description | Priorité |
|---|---|---|
| **L8** | Enums (PENDING/APPROVED/REJECTED) | 🔴 Bloquant |
| **L6** | Filtrage par statut | 🔴 Bloquant |

Note : leave-manager couvre déjà une grande partie de ce type — I est le plus proche de A après D.

Quand I est validé, la factory peut générer : workflows RH, processus de validation, systèmes d'approbation.

---

### Type E — E-commerce
**Nouveauté critique :** Catalogue public + transactions atomiques + montants Decimal

Limitations à corriger :
| Limite | Description | Priorité |
|---|---|---|
| **L3** | Catalogue produits public (pas de userId sur listing) | 🔴 Bloquant |
| **L10** | Decimal non sérialisé (prix, montants) | 🔴 Bloquant |
| **L15** | Create atomique (Order + OrderItems via $transaction) | 🔴 Bloquant |
| **L4** | Pas de pagination (catalogue de 1000+ produits) | 🟠 Important |
| **L14** | Pas de getBySlug (URLs produits) | 🟠 Important |
| **L9** | Soft delete ignoré (commandes annulées) | 🟡 Qualité |

Quand E est validé, la factory peut générer : boutiques en ligne simples, catalogues, systèmes de commande.

---

### Type H — Dashboard / Analytics
**Nouveauté critique :** Requêtes d'agrégation (count, sum, avg, groupBy)

Limitations à corriger :
| Limite | Description | Priorité |
|---|---|---|
| **L13** | Pas de méthodes d'agrégation Prisma | 🔴 Bloquant (type H entier) |
| **L4** | Pas de pagination | 🔴 Bloquant |
| **L12** | Json → unknown (metadata, event data) | 🟠 Important |

Quand H est validé, la factory peut générer : tableaux de bord de métriques, outils de reporting, analytics internes.

---

### Type F — Social / Communauté
**Nouveauté critique :** Relations many-to-many (follows, likes) et feed paginé

Limitations à corriger :
| Limite | Description | Priorité |
|---|---|---|
| **L11** | Many-to-many ignoré | 🔴 Bloquant |
| **L4** | Pagination (feed infini) | 🔴 Bloquant |
| **L5** | Tri chronologique inversé | 🔴 Bloquant |
| **L13** | Compteurs (likes, followers) | 🟠 Important |

Quand F est validé, la factory peut générer : fils d'actualité, systèmes de commentaires, communautés légères.

---

### Type B — Multi-tenant SaaS
**Nouveauté critique :** Ownership par organisation (workspaceId) plutôt que par userId individuel

Limitations à corriger :
| Limite | Description | Priorité |
|---|---|---|
| **L2** | Owner = userId hardcodé — ne supporte pas organizationId | 🔴 Bloquant (architecture complète) |
| **L7** | Relations à 1 niveau (workspace → channels → messages nécessite 2 niveaux) | 🔴 Bloquant |
| **L15** | Create atomique (workspace + member owner) | 🔴 Bloquant |

Note : B est le plus gros saut architectural — L2 implique de revoir le ProjectSpec, le générateur de services, et les Server Actions.

---

### Type C — Marketplace / Platform
**Nouveauté critique :** Deux types d'utilisateurs (vendeur/acheteur) avec ownership dual

Dépend de : D (routes publiques) + E (catalogue + commandes) + B (multi-ownership)
C'est la combinaison la plus complexe — à traiter en dernier.

---

### Type J — Gestion de fichiers / Documents
**Nouveauté critique :** Upload de fichiers vers un service externe (S3/Cloudflare R2), métadonnées, permissions

Limitations à corriger :
| Limite | Description | Priorité |
|---|---|---|
| **L12** | Json → unknown (métadonnées fichiers) | 🟠 Important |
| **L9** | Soft delete (versioning — fichier archivé, pas supprimé) | 🟠 Important |
| Intégration externe | Upload S3/R2 — hors scope générateur actuel | 🔴 Nouveau territoire |

Note : J nécessite une intégration externe que le générateur ne gère pas du tout aujourd'hui.

---

## 5. Tableau de synthèse — Limitations à corriger par phase

| Phase | Type | Limitations clés | Apps débloquées |
|---|---|---|---|
| Phase 1 ✅ | A | L1, L16 (fixes faits), child entity userId | project-hub, CRM, HR, billing |
| Phase 2 | **D** | **L3, L14, L11, L8, L5** | blogs, CMS, portfolios, wikis |
| Phase 3 | G + I | L5, L6, L8 | booking, RH, approval workflows |
| Phase 4 | E | L3, L10, L15, L4, L14 | e-commerce, boutiques |
| Phase 5 | H | L13, L4, L12 | dashboards, analytics |
| Phase 6 | F | L11, L4, L5, L13 | social, communautés |
| Phase 7 | B | L2, L7, L15 | multi-tenant SaaS |
| Phase 8 | C | D + E + B | marketplaces |
| Phase 9 | J | L9, L12 + intégration externe | gestion de fichiers |

---

## 6. Audit des limites déterministes (détail technique)

### L1 — Omit<PrismaType, K> ne fonctionne pas avec Prisma 7
Fichier : `dev_types_generator.py` ligne 208

Impact : `SerializedXxx = { createdAt: string }` seulement — id, content, tous les autres champs manquants

Apps bloquées : TOUS — bloque le BUILD dès qu'un modèle a un champ DateTime

Fix : Générer un type explicite en énumérant tous les champs scalaires ✅ **Corrigé Sprint 2**

---

### L2 — Owner = toujours userId, un seul propriétaire par modèle
Fichier : `dev_service_generator.py` ligne 67 — `_resolve_owner(model)` retourne userId par défaut

Ce que ça produit :
```typescript
getAll: async (userId: string) => prisma.project.findMany({ where: { userId } })
```
Problème : en Multi-tenant, le modèle appartient à un `organizationId` ou `workspaceId`, pas à `userId`. En Marketplace, un Product appartient à un `sellerId`, pas un userId générique. En Social, un Post peut avoir `authorId` + `communityId`.

Apps bloquées : B (multi-tenant), C (marketplace), G (booking team-based)

Fix : ProjectSpec doit exposer `owner_type: "user" | "organization" | "public"` + `owner_field: string` — le générateur lit ces champs

---

### L3 — Aucun modèle public (sans owner)
Fichier : `dev_service_generator.py` ligne 103 — `where: { userId }` toujours injecté

Problème : Un catalogue de produits, un article de blog publié, une fiche vendeur — ces modèles se lisent sans authentification. Actuellement le service force un userId qui n'existe pas → résultats vides ou erreur runtime.

Apps bloquées : C (listings publics), D (articles publiés), E (catalogue produits)

Fix : Détecter quand `resolved_owner()` retourne null (modèle public) → générer `getAll(): Promise<SerializedXxx[]>` sans where

---

### L4 — getAll sans pagination
Fichier : `dev_service_generator.py` ligne 104

Ce que ça produit :
```typescript
const items = await prisma.project.findMany({ where: { userId } })  // ALL records
```
Problème : 1 000 produits e-commerce ? 50 000 articles de blog ? La requête charge tout en mémoire, le serveur s'effondre.

Apps bloquées : D, E, F, H, I — toute app au-delà de ~100 enregistrements

Fix : Ajouter `take?` et `skip?` optionnels + retourner `{ data: SerializedXxx[], total: number }`

---

### L5 — getAll sans tri
Fichier : `dev_service_generator.py` ligne 104 — aucun `orderBy`

Problème : Un feed social non trié par `createdAt DESC` est inutilisable. Un catalogue produits sans `orderBy: { price: 'asc' }` est incohérent.

Apps bloquées : D (articles par date), E (produits par prix), F (feed chronologique), G (créneaux triés)

Fix : Détecter les champs `createdAt`/`updatedAt` → `orderBy: { createdAt: 'desc' }` par défaut ; rendre configurable dans ProjectSpec

---

### L6 — getAll sans filtrage ni recherche
Fichier : `dev_service_generator.py` ligne 104

Problème : Impossible de faire `getByStatus('PENDING')`, `searchByName('claude')`, `getByCategory('tech')` — le service ne génère aucune méthode de filtrage.

Apps bloquées : C (filtrer par catégorie), D (filtrer par tag/status), E (filtrer par prix), F (filtrer par type de post), I (filtrer par statut d'approbation)

Fix : Détecter les champs `status`, `category`, `type` dans le schéma → générer `getByStatus(userId, status)` ou une méthode générique `findMany(userId, where?)`

---

### L7 — Relations à un seul niveau (include: { relation: true })
Fichier : `dev_service_generator.py` ligne 115-122

Ce que ça produit :
```typescript
prisma.project.findMany({ include: { tasks: true } })  // ← tasks sans leurs comments
```
Problème : Pour afficher Project → Tasks → Comments, un seul niveau ne suffit pas. Pour Order → OrderItems → Product, il faut `include: { items: { include: { product: true } } }`.

Apps bloquées : B (workspace → channels → messages), C (order → items → products), D (article → sections → blocks), E idem

Fix : ProjectSpec expose `include_depth: number` ou des relations imbriquées explicites → le générateur construit le bloc include en récursif

---

### L8 — Enums Prisma mappés en string
Fichier : `dev_types_generator.py` ligne 63 — `_PRISMA_TO_TS.get(base, "string" if base[0].isupper()...)`

Ce que ça produit pour Status enum :
```typescript
// Devrait être :  status: Status  (depuis @prisma/client)
// Est généré :    status: string  ← TypeScript ne valide plus les valeurs
```
Problème : `status: "APPROVD"` (faute de frappe) passe TypeScript. L'enum est la protection contre ça.

Apps bloquées : I (PENDING/APPROVED/REJECTED), E (PENDING/PAID/SHIPPED/DELIVERED), D (DRAFT/PUBLISHED/ARCHIVED), F (PUBLIC/PRIVATE/FOLLOWERS_ONLY)

Fix : Détecter les Enums depuis ProjectSpec → `import type { Status } from '@prisma/client'` → `status: Status` dans les types

---

### L9 — Soft delete (deletedAt) non géré
Fichier : `dev_types_generator.py` ligne 40 — `"deletedat"` dans `_AUTO_FIELDS` (exclu des inputs) mais `dev_service_generator.py` n'ajoute jamais `where: { deletedAt: null }`

Ce que ça produit :
```typescript
getAll: async (userId) => prisma.contact.findMany({ where: { userId } })
// retourne AUSSI les contacts supprimés
```
Apps bloquées : C (contacts CRM supprimés), D (articles archivés), E (commandes annulées), F (posts supprimés), J (documents supprimés)

Fix : Détecter `deletedAt DateTime?` dans le schéma → ajouter automatiquement `deletedAt: null` au where

---

### L10 — Decimal non sérialisé (comme DateTime)
Fichier : `dev_types_generator.py` ligne 31 — `"Decimal": "number"` + `dev_service_generator.py` — `_serialize` ne touche pas les Decimal

Problème : Prisma retourne `Decimal` (objet Prisma custom), pas un `number` JavaScript. `.toNumber()` est nécessaire. Sans sérialisation, `JSON.stringify` échoue en production et le Client Component plante.

Apps bloquées : E (prix produits), H (métriques financières), tout SaaS avec montants exacts

Fix : Decimal dans `_PRISMA_TO_TS` → `number` dans le type ET `_serialize` ajoute `field: item.field.toNumber()` comme pour DateTime

---

### L11 — Relations many-to-many non supportées
Fichier : `dev_service_generator.py` ligne 47 — `_relation_fields` détecte uniquement `@relation` explicite

Problème : Les relations implicites many-to-many (Post ↔ Tag via table pivot auto-générée par Prisma) n'ont pas de `@relation` dans les champs — le générateur les ignore complètement.

Apps bloquées : D (articles ↔ tags/catégories), C (produits ↔ tags), F (users ↔ groups), E (produits ↔ promotions)

Fix : Détecter les champs de type tableau (`Tag[]`, `Category[]`) sans `@relation` → les inclure dans `getAllWithRelations`

---

### L12 — Champs Json inutilisables
Fichier : `dev_types_generator.py` ligne 34 — `"Json": "unknown"`

Problème : `content: unknown` force des casts partout. Le LLM ne sait pas comment typer/utiliser ce champ → improvise → erreurs TypeScript.

Apps bloquées : D (rich text en JSON), H (event metadata), J (document content), tout app avec config flexible

Fix : Accepter un champ optionnel `json_type` dans ProjectSpec (`json_type: "Record<string, unknown>"` ou une interface nommée) → le générateur l'utilise

---

### L13 — Pas de méthodes d'agrégation (count, sum, avg)
Fichier : `dev_service_generator.py` — aucun `prisma.model.aggregate()` généré

Problème : Un dashboard avec "42 projets actifs", "€12,500 de CA ce mois" ou "85 nouveaux utilisateurs" nécessite des agrégations. Le LLM les improvise dans les Server Components → erreurs, requêtes N+1.

Apps bloquées : H (ENTIÈREMENT), E (totaux commandes), F (compteurs likes/follows), I (taux d'approbation)

Fix : Détecter les modèles marqués `analytics: true` dans ProjectSpec → générer `count(userId)`, `aggregate(userId, field)`

---

### L14 — getById uniquement par id, pas par slug
Fichier : `dev_service_generator.py` ligne 108 — `where: { id, userId }` seulement

Problème : Un blog, un portfolio, un e-commerce veulent des URLs `/articles/mon-titre-article` — slug unique, SEO-friendly. Aucune méthode générée pour ça.

Apps bloquées : D (blog), E (produits), C (profils vendeurs)

Fix : Détecter les champs nommés `slug` avec `@unique` → générer `getBySlug(slug: string): Promise<SerializedXxx | null>`

---

### L15 — create atomique (multi-modèles) non généré
Fichier : `dev_service_generator.py` ligne 126 — un seul `prisma.model.create()`

Problème : Créer une Order avec ses OrderItems doit être atomique (`$transaction`). Créer un Workspace avec son WorkspaceMember (rôle owner) est toujours couplé. Le générateur ne gère qu'un modèle à la fois.

Apps bloquées : E (commandes + items), B (workspace + member owner), G (booking + confirmation)

Fix : ProjectSpec expose des `transactions: [{ trigger: "createOrder", models: ["Order", "OrderItem"] }]` → générateur crée une méthode `createWithItems(userId, data, items)` avec `$transaction`

---

### L16 — Actions 100% LLM (le plus critique après L1)
Fichier : aucun — les `app/*/actions.ts` sont entièrement générés par le LLM

✅ **Corrigé Sprint 4** — les actions CRUD sont désormais générées par `dev_actions_generator.py` (template déterministe). Le LLM ne génère que les actions métier complexes.

---

## 7. Priorités par niveau d'évolution

| # | Limite | Apps débloquées | Priorité |
|---|---|---|---|
| L1 | Bug Omit<PrismaType> | TOUS | ✅ Corrigé |
| L16 | Actions 100% LLM | TOUS | ✅ Corrigé |
| **L3** | **Pas de modèle public** | **C, D, E** | **🔴 Phase 2 — Blog/CMS** |
| **L14** | **Pas de getBySlug** | **C, D, E** | **🔴 Phase 2 — Blog/CMS** |
| L10 | Decimal non sérialisé | E, H | 🟠 Phase 4 — E-commerce |
| L8 | Enums → string | D, E, I | 🟠 Phase 2-3 |
| L4 | Pas de pagination | D, E, F, H | 🟠 Phase 4 |
| L9 | Soft delete ignoré | C, D, E, F | 🟡 Phase 4-5 |
| L5 | Pas de tri | D, E, F, G | 🟡 Phase 2-3 |
| L2 | Owner = userId hardcodé | B, C, G | 🟡 Phase 7 |
| L7 | Relations 1 niveau | B, C, D, E | 🟡 Phase 4-5 |
| L11 | Many-to-many ignoré | C, D, F | 🟡 Phase 2-3 |
| L6 | Pas de filtrage | C, D, E, F, I | 🟡 Phase 3-4 |
| L13 | Pas d'agrégations | H entier | 🟡 Phase 5 |
| L12 | Json → unknown | D, H, J | 🟢 Phase 5-6 |
| L15 | Create atomique | B, E, G | 🟢 Phase 4-7 |

---

## 8. Prochain test — Type D : Blog/CMS (L1+)

**Objectif :** Tester la factory sur des pages à visibilité mixte — public vs privé dans la même app.

**Ce qui est nouveau par rapport au Type A :**
- Pages publiques : pas d'appel `auth()` bloquant, service sans filtre userId
- Pages privées : pattern habituel avec auth() + redirect
- Champ `status` (draft/published) utilisé pour filtrer la visibilité publique

**Brief :**

```json
{
  "project_name": "personal-blog",
  "brief": {
    "description": "Blog personnel SaaS. L'auteur gère ses articles et catégories depuis son tableau de bord privé. Les visiteurs peuvent lire les articles publiés sans compte.",
    "architecture": "SaaS single-tenant — tableau de bord protégé par Clerk, lectures publiques sans auth. Post est lié à Category via categoryId (owner_field=userId sur Post). Un Post a un champ status String: 'draft' par défaut, 'published' quand publié — seuls les posts published sont visibles sur /blog. Comment est lié à Post via postId (owner_field=authorId). RÈGLE CRITIQUE : les routes /blog et /blog/new sont publiques — leurs Server Components NE DOIVENT PAS appeler auth() ni redirect('/sign-in'). Les routes /dashboard et /categories sont protégées — elles appellent auth() + redirect. postService.getPublished() filtre where: { status: 'published' } SANS userId. postService.getAll(userId) filtre where: { userId }. Mutations via Server Actions (actions.ts) — jamais de routes API pour les mutations.",
    "models": [
      "Category { id String @id @default(uuid()), name String, userId String, createdAt DateTime @default(now()), @@index([userId]) }",
      "Post { id String @id @default(uuid()), title String, excerpt String?, status String @default('draft'), categoryId String, userId String, createdAt DateTime @default(now()), @@index([userId]), @@index([categoryId]), @@index([status]) }",
      "Comment { id String @id @default(uuid()), content String, postId String, authorId String, createdAt DateTime @default(now()), @@index([postId]) }"
    ],
    "pages": [
      { "path": "/blog",           "auth": false },
      { "path": "/blog/new",       "auth": false },
      { "path": "/dashboard",      "auth": true  },
      { "path": "/categories",     "auth": true  },
      { "path": "/categories/new", "auth": true  }
    ],
    "pages_detail": {
      "/blog": "PAGE PUBLIQUE — aucun auth() requis. Liste des posts avec status='published'. Affiche : titre, extrait (ou '-'), date de création. Lien 'Écrire un article' → /blog/new. État vide : 'Aucun article publié pour l\\'instant.'. [INTERACTIVE]",
      "/blog/new": "PAGE PUBLIQUE — aucun auth() requis. Formulaire de création d'article. Champs : titre (input text, required), extrait (textarea, optionnel), categoryId (input text, required, placeholder 'ID de la catégorie'). Bouton 'Publier'. Submit → Server Action createPost({ title, excerpt, categoryId }) → redirect /dashboard. [INTERACTIVE]",
      "/dashboard": "PAGE PROTÉGÉE — auth() + redirect('/sign-in') obligatoires. Liste de TOUS les articles de l'auteur connecté (drafts + published). Affiche : titre, statut (badge : draft=gris, published=vert), date de création. Bouton 'Supprimer' par ligne → Server Action deletePost(id). État vide : 'Aucun article. Créez votre premier article sur /blog/new.'. [INTERACTIVE]",
      "/categories": "PAGE PROTÉGÉE — auth() + redirect('/sign-in') obligatoires. Liste des catégories de l'auteur. Affiche : nom, date de création. Bouton 'Nouvelle catégorie' → /categories/new. Bouton 'Supprimer' par ligne → Server Action deleteCategory(id). État vide : 'Aucune catégorie.'. [INTERACTIVE]",
      "/categories/new": "PAGE PROTÉGÉE — auth() + redirect('/sign-in') obligatoires. Formulaire de création de catégorie. Champ : nom (input text, required). Bouton 'Créer la catégorie'. Submit → Server Action createCategory({ name }) → redirect /categories. [INTERACTIVE]"
    },
    "routes": [
      { "method": "POST",   "path": "/api/posts" },
      { "method": "DELETE", "path": "/api/posts/[id]" },
      { "method": "POST",   "path": "/api/categories" },
      { "method": "DELETE", "path": "/api/categories/[id]" }
    ],
    "user_flows": [
      "Un visiteur lit les articles publiés : /blog → postService.getPublished() sans auth",
      "L'auteur écrit un article : /blog/new → Server Action createPost() → redirect /dashboard",
      "L'auteur gère ses articles : /dashboard → postService.getAll(userId) avec auth",
      "L'auteur supprime un article : bouton Supprimer → Server Action deletePost(id)",
      "L'auteur crée une catégorie : /categories/new → Server Action createCategory() → redirect /categories"
    ]
  }
}
```

**Commande de test :**

```bash
python -m scripts.run_batch --briefs scripts/test_blog_only.json --review-mode
```

**Ce qu'on observe :**
- Le dev LLM génère-t-il `/blog` sans `auth()` bloquant ?
- `postService` a-t-il une méthode `getPublished()` sans filtre userId ?
- Le reviewer détecte-t-il les pages publiques qui ne doivent PAS être marquées MISSING_AUTH ?
- La re-review donne-t-elle COHERENT ?
