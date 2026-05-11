# Brief Contract — Software Agent Factory
## Stack : `nextjs-clerk-prisma` · Version du contrat : 1.1 (Mai 2026)

Ce document est le **contrat formel** qui définit comment structurer un brief pour que la factory puisse générer une application. Il est la source de vérité pour tout développeur qui veut soumettre une nouvelle app à la factory.

> Ce contrat évolue avec les capacités de la factory. Chaque section indique depuis quelle version un champ est supporté et quelles limitations s'appliquent aujourd'hui.

---

## 1. Structure complète (JSON)

```json
{
  "project_name": "string (kebab-case, unique)",
  "family":       "string (optionnel — catégorie métier : crm, finance, hr…)",
  "tags":         ["string"] ,
  "brief": {
    "description":   "string",
    "architecture":  "string",
    "models":        ["string (Prisma DSL inline)"],
    "pages": [
      {
        "path":  "string (commence par /)",
        "auth":  "boolean",
        "model": "string (PascalCase — NOM DU MODÈLE PRISMA, optionnel)"
      }
    ],
    "pages_detail": {
      "/chemin": "string (description détaillée de la page)"
    },
    "routes": [
      { "method": "POST|DELETE|PUT|PATCH", "path": "string" }
    ],
    "user_flows": ["string"]
  }
}
```

---

## 2. Référence des champs

### `project_name` · string · **Obligatoire**
Identifiant kebab-case unique du projet. Utilisé comme nom du dossier dans le volume Docker et comme ID de workflow Temporal.

```
✅  "invoice-tracker"
✅  "personal-blog"
❌  "InvoiceTracker"    ← PascalCase interdit
❌  "invoice tracker"   ← espaces interdits
```

---

### `family` · string · *Optionnel*
Catégorie métier de l'application. Utilisé pour regrouper les runs dans les rapports et pour le routing futur des standards RAG.

Valeurs actuellement reconnues : `project_management`, `crm`, `hr`, `finance`, `blog`, `ecommerce`

---

### `tags` · string[] · *Optionnel*
Étiquettes libres pour qualifier le brief. Utilisées pour filtrer les runs dans les rapports.

Exemples : `["multi_model", "relations", "public_pages", "status_field"]`

---

### `brief.description` · string · **Obligatoire**
Description humaine de l'application en 1 à 3 phrases. Doit répondre à : *qui utilise l'app, et quoi fait-elle ?*

```
✅  "Application SaaS de suivi de facturation. L'utilisateur gère ses clients et crée des factures."
❌  "App de factures"   ← trop vague
```

---

### `brief.architecture` · string · **Obligatoire**

Bloc de texte décrivant les règles d'ownership et les contraintes techniques. **C'est le texte le plus important du brief** — le LLM le lit en premier pour calibrer sa génération.

**Ce qui DOIT toujours être présent :**

| Élément | Exemple |
|---|---|
| Modèle d'auth | `"SaaS single-tenant — toutes les pages protégées par Clerk."` |
| Ownership de chaque modèle | `"Task est lié à Project via projectId (owner_field=userId)."` |
| Règle des mutations | `"Mutations via Server Actions (actions.ts) — jamais de routes API pour les mutations."` |

**Si des pages publiques existent (`auth: false`) :**

```
"RÈGLE CRITIQUE : les routes /blog et /blog/new sont publiques — leurs Server Components
NE DOIVENT PAS appeler auth() ni redirect('/sign-in').
postService.getPublished() filtre where: { status: 'published' } SANS userId."
```

**Si des entités enfant existent (modèle sans userId direct) :**

```
"InvoiceItem est lié à Invoice via invoiceId (owner_field=userId sur InvoiceItem).
Tous les modèles ont userId directement pour un ownership uniforme."
```

---

### `brief.models` · string[] · **Obligatoire**

Liste des modèles Prisma au format DSL inline (une string par modèle). Ces strings sont copiées verbatim dans `prisma/schema.prisma`.

**Règles de syntaxe Prisma (erreurs fréquentes à éviter) :**

| Règle | Correct | Faux |
|---|---|---|
| Defaults string | `@default("draft")` | `@default('draft')` ← guillemets simples = P1012 |
| Champ nullable | `String?` | `String \| null` ← syntaxe TypeScript, pas Prisma |
| Relation bidirectionnelle | champ `Invoice[]` + `@relation` côté FK | oublier un côté |
| Index userId | `@@index([userId])` sur chaque modèle | oublier → queries lentes |

**Champs obligatoires sur chaque modèle :**

```
id        String   @id @default(uuid())
userId    String                          ← OBLIGATOIRE sur TOUS les modèles (même les entités enfant)
createdAt DateTime @default(now())
@@index([userId])
```

> **Règle entités enfant (depuis Mai 2026)** : même un modèle lié à un parent (ex: `InvoiceItem` lié à `Invoice`) doit avoir `userId String` en direct. Sans ça, les actions de suppression reçoivent le Clerk userId à la place du parentId → crash Prisma P2025 silencieux.

---

### `brief.pages` · object[] · **Obligatoire**

Liste des pages de l'application. Chaque entrée a 3 champs :

| Champ | Type | Req. | Description |
|---|---|---|---|
| `path` | string | ✅ | Chemin URL commençant par `/`. Segments dynamiques : `[id]`. |
| `auth` | boolean | ✅ | `true` = page protégée par Clerk. `false` = page publique, aucun `auth()`. |
| `model` | string | ⚠️ | Nom PascalCase du modèle Prisma principal affiché sur cette page. |

**Quand `model` est obligatoire :**
- Page de **liste** (`/projects`, `/invoices`, `/dashboard`) → **obligatoire**
- Page de **détail** (`/projects/[id]`) → **obligatoire**
- Page de **création** (`/projects/new`) → *omis* (pas de données à afficher)

> **Règle de nommage** : si le chemin de la page ne contient pas le nom du modèle (ex: `/dashboard` au lieu de `/posts`), le champ `model` est **obligatoire** — sans lui, le générateur ne peut pas synchroniser les props entre `page.tsx` et `page-client.tsx`.

```json
"pages": [
  { "path": "/projects",      "auth": true,  "model": "Project"  },
  { "path": "/projects/new",  "auth": true                        },
  { "path": "/dashboard",     "auth": true,  "model": "Post"      },
  { "path": "/blog",          "auth": false, "model": "Post"      },
  { "path": "/blog/new",      "auth": false                       }
]
```

**Types de pages reconnus par le générateur :**

| Type | Critères de détection | Ce que le générateur produit |
|---|---|---|
| **Liste privée** | `auth: true` + `model` présent + path ne finit pas en `/new` ou `/[id]` | `page.tsx` avec `auth()` + `getAll(userId)` → `<XxxClient items={…} />` |
| **Liste publique** | `auth: false` + `model` présent + path ne finit pas en `/new` | `page.tsx` sans `auth()` + `getPublished()` → `<XxxClient items={…} />` |
| **Création** | path finit en `/new` | `page.tsx` minimal → `<XxxNewClient />` (sans données) |
| **Détail** | path contient `[id]` + `model` présent | `page.tsx` avec `getById(userId, params.id)` → `<XxxDetailClient item={…} />` |

---

### `brief.pages_detail` · object · **Obligatoire**

Dictionnaire `{ "/chemin": "description détaillée" }`. La description est lue par le LLM pour générer le JSX du `page-client.tsx`.

**Format recommandé (1 ligne par élément) :**

```
"Liste de toutes les factures.
Affiche : numéro, statut (badge : draft=gris, sent=bleu, paid=vert), date d'échéance.
Bouton 'Nouvelle facture' en haut → /invoices/new.
Bouton 'Supprimer' par ligne → Server Action deleteInvoice(id).
État vide : 'Aucune facture.'.
[INTERACTIVE]"
```

**Balises spéciales :**

| Balise | Signification | Effet générateur |
|---|---|---|
| `[INTERACTIVE]` | La page a des boutons ou un formulaire React | Génère un `page-client.tsx` ('use client') en plus de `page.tsx` |
| `PAGE PROTÉGÉE` | Rappel explicite que la page doit appeler `auth()` | Renforce l'instruction du prompt LLM |
| `PAGE PUBLIQUE` | Rappel explicite que la page NE DOIT PAS appeler `auth()` | Idem |

**Informations obligatoires dans chaque page_detail de liste :**
- Quels champs afficher
- Bouton d'ajout (→ quelle route)
- Action de suppression (→ quelle Server Action)
- Texte de l'état vide

**Informations obligatoires dans chaque page_detail de formulaire :**
- Chaque champ : type HTML (`input text`, `input email`, `textarea`, `select`), required/optionnel
- Server Action appelée au submit + paramètres
- Redirect après submit

---

### `brief.routes` · object[] · *Optionnel depuis Sprint 4*

> **Note importante** : les routes listées ici servent uniquement à **documenter les Server Actions** existantes. Depuis Sprint 4, les mutations (create/delete) sont générées via `dev_actions_generator.py` (déterministe) — il ne faut PAS créer de vraies routes API pour les mutations CRUD.

```json
"routes": [
  { "method": "POST",   "path": "/api/invoices" },
  { "method": "DELETE", "path": "/api/invoices/[id]" }
]
```

**Cas où de vraies routes API sont nécessaires :**
- Webhooks externes (ex: Stripe, GitHub)
- Endpoints appelés par des services tiers (format : `POST /api/webhooks/stripe`)

---

### `brief.user_flows` · string[] · **Obligatoire**

Liste des flux utilisateurs principaux. Utilisés par le **Journey Validator** pour calculer le score `user_flows_coverage`. Chaque flow doit être une phrase complète décrivant : *acteur → action → résultat*.

**Format :**
```
"L'utilisateur [action] : [chemin de départ] → [mécanisme] → [résultat/redirect]"
```

**Exemples :**
```json
"user_flows": [
  "L'utilisateur crée une facture : /invoices/new → Server Action createInvoice() → redirect /invoices",
  "L'utilisateur supprime un client : bouton Supprimer → Server Action deleteClient(id)",
  "Un visiteur lit les articles publiés : /blog → postService.getPublished() sans auth"
]
```

**Règle :** prévoir au minimum un flow par action principale (create, delete, list public si applicable).

---

## 3. Exemple complet — invoice-tracker v1.1

```json
{
  "project_name": "invoice-tracker",
  "family": "finance",
  "tags": ["multi_model", "relations", "status_field"],
  "brief": {
    "description": "Application SaaS de suivi de facturation. L'utilisateur gère ses clients et crée des factures.",
    "architecture": "SaaS single-tenant — toutes les pages protégées par Clerk. Invoice est lié à Client via clientId (owner_field=userId sur Invoice). InvoiceItem est lié à Invoice via invoiceId (owner_field=userId sur InvoiceItem). Tous les modèles ont userId directement pour un ownership uniforme. Mutations via Server Actions (actions.ts) — jamais de routes API pour les mutations.",
    "models": [
      "Client { id String @id @default(uuid()), name String, email String, phone String?, address String?, invoices Invoice[], userId String, createdAt DateTime @default(now()), @@index([userId]) }",
      "Invoice { id String @id @default(uuid()), number String, status String @default(\"draft\"), dueDate DateTime, clientId String, client Client @relation(fields: [clientId], references: [id]), userId String, createdAt DateTime @default(now()), @@index([userId]), @@index([clientId]) }",
      "InvoiceItem { id String @id @default(uuid()), description String, quantity Int @default(1), unitPrice Float, invoiceId String, userId String, createdAt DateTime @default(now()), @@index([invoiceId]), @@index([userId]) }"
    ],
    "pages": [
      { "path": "/clients",      "auth": true,  "model": "Client"  },
      { "path": "/clients/new",  "auth": true                       },
      { "path": "/invoices",     "auth": true,  "model": "Invoice"  },
      { "path": "/invoices/new", "auth": true                       }
    ],
    "pages_detail": {
      "/clients":      "Liste de tous les clients. Affiche : nom, email (lien mailto:), téléphone (ou '-'), date d'ajout. Bouton 'Nouveau client' en haut → /clients/new. Bouton 'Supprimer' par ligne → Server Action deleteClient(id). État vide : 'Aucun client. Ajoutez votre premier client !'. [INTERACTIVE]",
      "/clients/new":  "Formulaire de création de client. Champs : nom (input text, required), email (input email, required), téléphone (input tel, optionnel), adresse (textarea, optionnel). Bouton 'Ajouter le client'. Submit → Server Action createClient({ name, email, phone, address }) → redirect /clients. [INTERACTIVE]",
      "/invoices":     "Liste de toutes les factures. Affiche : numéro, statut (badge : draft=gris, sent=bleu, paid=vert), date d'échéance, date de création. Bouton 'Nouvelle facture' en haut → /invoices/new. Bouton 'Supprimer' par ligne → Server Action deleteInvoice(id). État vide : 'Aucune facture.'. [INTERACTIVE]",
      "/invoices/new": "Formulaire de création de facture. Champs : numéro (input text, required, placeholder 'FAC-001'), clientId (input text, required, placeholder 'ID du client'), date d'échéance (input date, required). Bouton 'Créer la facture'. Submit → Server Action createInvoice({ number, clientId, dueDate }) → redirect /invoices. [INTERACTIVE]"
    },
    "routes": [
      { "method": "POST",   "path": "/api/clients" },
      { "method": "DELETE", "path": "/api/clients/[id]" },
      { "method": "POST",   "path": "/api/invoices" },
      { "method": "DELETE", "path": "/api/invoices/[id]" }
    ],
    "user_flows": [
      "L'utilisateur ajoute un client : /clients/new → Server Action createClient() → redirect /clients",
      "L'utilisateur crée une facture : /invoices/new → Server Action createInvoice() → redirect /invoices",
      "L'utilisateur supprime un client : bouton Supprimer → Server Action deleteClient(id)"
    ]
  }
}
```

---

## 4. Exemple complet — personal-blog (Type D, pages mixtes)

```json
{
  "project_name": "personal-blog",
  "family": "blog",
  "tags": ["public_pages", "status_field", "mixed_auth"],
  "brief": {
    "description": "Blog personnel SaaS. L'auteur gère ses articles depuis son tableau de bord privé. Les visiteurs lisent les articles publiés sans compte.",
    "architecture": "SaaS single-tenant — tableau de bord protégé par Clerk, lectures publiques sans auth. Post est lié à Category via categoryId (owner_field=userId sur Post). Un Post a un champ status String @default(\"draft\") — seuls les posts avec status='published' sont visibles publiquement. RÈGLE CRITIQUE : les routes /blog et /blog/new sont publiques — NE PAS appeler auth(). postService.getPublished() filtre where: { status: 'published' } SANS userId. postService.getAll(userId) filtre where: { userId }. Mutations via Server Actions (actions.ts).",
    "models": [
      "Category { id String @id @default(uuid()), name String, userId String, createdAt DateTime @default(now()), @@index([userId]) }",
      "Post { id String @id @default(uuid()), title String, excerpt String?, status String @default(\"draft\"), categoryId String, userId String, createdAt DateTime @default(now()), @@index([userId]), @@index([categoryId]), @@index([status]) }",
      "Comment { id String @id @default(uuid()), content String, postId String, authorId String, createdAt DateTime @default(now()), @@index([postId]) }"
    ],
    "pages": [
      { "path": "/blog",           "auth": false, "model": "Post"     },
      { "path": "/blog/new",       "auth": false                      },
      { "path": "/dashboard",      "auth": true,  "model": "Post"     },
      { "path": "/categories",     "auth": true,  "model": "Category" },
      { "path": "/categories/new", "auth": true                       }
    ],
    "pages_detail": {
      "/blog":           "PAGE PUBLIQUE — aucun auth() requis. Liste des posts avec status='published'. Affiche : titre, extrait (ou '-'), date. Lien 'Écrire un article' → /blog/new. État vide : 'Aucun article publié pour l'instant.'. [INTERACTIVE]",
      "/blog/new":       "PAGE PUBLIQUE — aucun auth() requis. Formulaire de création d'article. Champs : titre (input text, required), extrait (textarea, optionnel), categoryId (input text, required). Bouton 'Publier'. Submit → Server Action createPost({ title, excerpt, categoryId }) → redirect /dashboard. [INTERACTIVE]",
      "/dashboard":      "PAGE PROTÉGÉE. Liste de TOUS les articles de l'auteur (drafts + published). Affiche : titre, statut (badge : draft=gris, published=vert), date. Bouton 'Supprimer' → Server Action deletePost(id). État vide : 'Aucun article.'. [INTERACTIVE]",
      "/categories":     "PAGE PROTÉGÉE. Liste des catégories de l'auteur. Affiche : nom, date. Bouton 'Nouvelle catégorie' → /categories/new. Bouton 'Supprimer' → Server Action deleteCategory(id). État vide : 'Aucune catégorie.'. [INTERACTIVE]",
      "/categories/new": "PAGE PROTÉGÉE. Formulaire de création de catégorie. Champ : nom (input text, required). Bouton 'Créer'. Submit → Server Action createCategory({ name }) → redirect /categories. [INTERACTIVE]"
    },
    "routes": [
      { "method": "POST",   "path": "/api/posts" },
      { "method": "DELETE", "path": "/api/posts/[id]" }
    ],
    "user_flows": [
      "Un visiteur lit les articles publiés : /blog → postService.getPublished() sans auth",
      "L'auteur écrit un article : /blog/new → Server Action createPost() → redirect /dashboard",
      "L'auteur gère ses articles : /dashboard → postService.getAll(userId) avec auth",
      "L'auteur supprime un article : bouton Supprimer → Server Action deletePost(id)"
    ]
  }
}
```

---

## 5. Ce que la factory supporte et ne supporte pas (Mai 2026)

### Supporté ✅
| Feature | Notes |
|---|---|
| 3 modèles Prisma avec relations 1-N | max 3 modèles validé sur 4 apps |
| Toutes les pages `auth: true` (Type A) | projet-hub, contact-crm, leave-manager, invoice-tracker |
| Pages publiques `auth: false` + `getPublished()` | Type D — disponible depuis v1.1 |
| Entités enfant avec `userId` direct | Fix Mai 2026 — obligatoire sur tous les modèles |
| Server Actions CRUD déterministes | create/delete via `dev_actions_generator.py` |
| Reviewer de sécurité (IDOR) + correction pass | COHERENT sec=100 sur Type A |
| Champ `status String @default("draft")` | génère `getPublished()` sur le service |

### Non supporté ❌ (limitations actives)
| Feature | Limitation | Priorité |
|---|---|---|
| Pagination (`take`/`skip` exposés) | `take: 20` fixe hardcodé | L4 — Phase 4 |
| Enums Prisma (`Status`, `Role`) | mappés en `string` | L8 — Phase 3 |
| Relations 2 niveaux imbriqués | `include` 1 seul niveau | L7 — Phase 5 |
| `getBySlug(slug)` | `getById(userId, id)` uniquement | L14 — Phase 2 |
| Many-to-many | ignoré par le générateur | L11 — Phase 3 |
| Soft delete (`deletedAt`) | `delete` hard uniquement | L9 — Phase 5 |
| Champ `Decimal` sérialisé | retourné comme objet Prisma brut | L10 — Phase 4 |
| Multi-tenant (organizationId) | `owner_field` = `userId` hardcodé | L2 — Phase 7 |
| Transactions atomiques | create séparé pour chaque modèle | L15 — Phase 4 |

---

## 6. Checklist avant de soumettre un brief

```
[ ] project_name en kebab-case, unique
[ ] description : ≥ 1 phrase métier claire
[ ] architecture : mentionne ownership + règle mutations + règles auth si pages mixtes
[ ] models : TOUS ont userId String + createdAt DateTime @default(now()) + @@index([userId])
[ ] models : @default("...") avec guillemets DOUBLES
[ ] pages : chaque page de liste a un champ "model" (surtout si le chemin est ambigu)
[ ] pages : pages /new n'ont PAS de champ "model"
[ ] pages_detail : chaque page a son entrée, [INTERACTIVE] si formulaire ou boutons
[ ] pages_detail : chaque formulaire liste ses champs + Server Action + redirect
[ ] pages_detail : pages publiques précisent explicitement "PAGE PUBLIQUE — aucun auth()"
[ ] user_flows : ≥ 1 flow par action principale (create, delete, list public)
```

---

## 7. Changelog

| Version | Date | Changements |
|---|---|---|
| 1.0 | Mars 2026 | Structure initiale : description, architecture, models, pages (path+auth), pages_detail, routes, user_flows |
| 1.1 | Mai 2026 | + champ `pages[].model` (obligatoire pour pages liste/détail) · + support `auth: false` (pages publiques) · + règle entités enfant (userId sur tous les modèles) · + checklist |
