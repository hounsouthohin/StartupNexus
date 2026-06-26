"""
agents/page_planner.py
───────────────────────
Nœud LLM focalisé sur la PLANIFICATION DES PAGES.

Responsabilité unique : transformer les modèles (déjà connus) en pages, routes,
user_flows, design_system et labels UI.

Découplage délibéré :
- Les règles de structure modèle (userId, enums, relations) sont dans domain_interpreter.py.
- Les règles de routing (patterns page, segments dynamiques, page_links) sont ici.

Input attendu dans brief : models (non vide)
Output injecté dans brief : pages, routes, user_flows, design_system, ui_labels,
                             title_plurals, enum_value_labels, page_links
"""
from __future__ import annotations

import json
import logging
import os

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Prompt — règles pages uniquement
# ─────────────────────────────────────────────────────────────────────────────

_PAGE_STACK_INVARIANTS = """\
## RÈGLES STACK — PAGES (NON NÉGOCIABLES)

### Pages — pattern standard
- `/` : home publique (auth: false, page_type: "custom")
- `/{model-kebab}` : liste (auth: true, sauf si contenu public comme un blog)
- `/{model-kebab}/new` : création (auth: true TOUJOURS)
- `/{model-kebab}/[id]` : détail par id (auth selon visibilité)
- `/{model-kebab}/[slug]` : détail par slug si le modèle a `slug String @unique` (page_type: "detail-slug", auth: false)
- **RÈGLE LISTE+SLUG OBLIGATOIRE** : Si des visiteurs peuvent parcourir ET consulter via slug, générer OBLIGATOIREMENT les deux pages :
  `/{model-kebab}` (auth: false, page_type: "list") ET `/{model-kebab}/[slug]` (auth: false, page_type: "detail-slug").
- **INVARIANT CRITIQUE** : Si page_type="detail-slug" → le modèle DOIT avoir `slug String @unique` dans Prisma.
- Ne PAS générer `/[id]/edit` sauf si le brief le demande explicitement.

### Routes API
Les Server Actions gèrent le CRUD → `"routes": []` dans la grande majorité des cas.
Ajouter des routes seulement pour : webhooks, exports CSV, endpoints publics stateless.

### CATALOGUE DES MODULES (activés automatiquement via features[])
- `"status_flow"`   → badges statut + filtre. Si modèle avec enum de statuts workflow.
- `"search"`        → barre de recherche. Si brief mentionne recherche textuelle.
- `"slug_routing"`  → détail par URL slug. Si modèle a `slug String @unique` ET pages publiques.
- `"public_pages"`  → pages sans auth. Si certaines pages sont publiques.
- `"calendar_view"` → vue calendrier. Si brief mentionne réservations, créneaux.

### MÉTHODES DE SERVICE (contrat IMMUABLE — utiliser dans data_fetches)
- `xxxService.getAll(userId)` / `getById(userId, id)` / `create` / `update` / `delete`
- `xxxService.getAllWithRelations(userId)` — si modèle a @relation
- `xxxService.getPublished()` — UNIQUEMENT si modèle a un ENUM status (ex: DRAFT/PUBLISHED) — N'EXISTE PAS pour Boolean published
- `xxxService.getPublicAll()` — si modèle a Boolean published OU pour toute liste publique (JAMAIS getPublished pour un Boolean)
- `xxxService.getBySlug(slug)` — si modèle a `slug String @unique`
- `childService.getBy{Parent}Id(userId, parentId)` — si modèle enfant

### page_links — contrat de navigation (OBLIGATOIRE)
Pour CHAQUE page dans `pages`, liste les chemins `<Link href>` valides dans ce composant.
- Page **list** → [create, detail]
- Page **create** → [liste parent]
- Page **detail** → [liste parent, éventuellement create des enfants]\
"""

_PAGE_DEDUCTION_RULES = """\
## RÈGLES DE DÉDUCTION PAGES

### RÈGLE 5 — Page détail pour tout modèle parent avec enfants FK
Si un modèle PARENT a au moins un modèle ENFANT dont la FK pointe vers lui, une page détail PEUT être nécessaire.
**Sélection du segment — NON-NÉGOCIABLE, inconditionnelle :**
- Si le parent **N'A PAS** `slug String @unique` → `/{parent}/[id]` (page_type: "detail") OBLIGATOIRE.
- Si le parent **A** `slug String @unique` → **JAMAIS `[id]` pour ce parent**, sans exception, même si c'est un parent FK. RÈGLE 9 prime toujours sur RÈGLE 5. Si le brief demande une vue détail publique → `/{parent}/[slug]` (detail-slug). Sinon → ne rien ajouter, la liste + l'edit via `[slug]` suffisent.
Ex : `Project` (sans slug) a `Task` via `projectId` → `/projects/[id]` OBLIGATOIRE.
Ex : `Category` a `slug @unique` et `Article` via `categoryId` → JAMAIS `/dashboard/categories/[id]`. Zero page détail [id] pour Category.

### RÈGLE 6 — Tous les champs mentionnés dans le brief
Tout attribut nommé dans le brief DOIT être présent dans le modèle. Principe : inférer, jamais supprimer.

### RÈGLE 7 — Create implique edit (pattern CRUD universel)
Tout modèle avec une page `create` DOIT aussi avoir une page `edit` : `/{model-kebab}/[id]/edit` (auth: true, page_type: "edit").
Exception : si le modèle a `detail-slug` ([slug]), l'edit ne peut PAS être `/[id]/edit` (conflit routing).
Pattern correct dans ce cas : `/dashboard/{model-kebab}/[id]/edit`.

### RÈGLE 8 — Modèle mixte public/privé → liste privée obligatoire
Si un modèle a des pages publiques ET des pages d'admin privées, il DOIT avoir une liste privée (dashboard ou my-X auth=true).

### RÈGLE 9 — Un seul segment dynamique par route (JAMAIS [id] + [slug] ensemble)
- Modèle privé (pas de slug) → `[id]` uniquement.
- Modèle public SANS slug (ex: `isPublic Boolean`, `published Boolean`) → `[id]` UNIQUEMENT, jamais `[slug]`.
  ERREUR FATALE : générer à la fois `/{model}/[id]` et `/{model}/[slug]` → conflit de routing Next.js → build impossible.
  Si le modèle N'A PAS `slug String @unique`, utiliser UNIQUEMENT `[id]` pour toutes les pages de détail (auth: true ou false selon la page).
- Modèle avec `slug String @unique` → **INTERDICTION ABSOLUE de générer `/{model}/[id]`**, sous QUELQUE PRÉTEXTE QUE CE SOIT — y compris si RÈGLE 5 s'applique. Le slug remplace [id] partout pour ce modèle.
  Pattern obligatoire :
  - Détail public : `/{model}/[slug]` (page_type: "detail-slug", auth: false)
  - Édition privée : `/dashboard/{model}/[id]/edit` (page_type: "edit", auth: true) — JAMAIS `/{model}/[id]/edit`
  - Jamais `/{model}/[id]` — ce chemin est banni pour tout modèle avec `slug String @unique`.\
"""

_PAGE_FEW_SHOT = """\
## EXEMPLES — PAGES UNIQUEMENT (modèles déjà connus)

### Modèles donnés : Task (status TaskStatus), Comment (taskId FK → Task)
```json
{
  "pages": [
    {"path": "/", "auth": false, "page_type": "custom"},
    {"path": "/tasks", "auth": true, "model": "Task", "page_type": "list"},
    {"path": "/tasks/new", "auth": true, "model": "Task", "page_type": "create"},
    {"path": "/tasks/[id]", "auth": true, "model": "Task", "page_type": "detail"},
    {"path": "/tasks/[id]/edit", "auth": true, "model": "Task", "page_type": "edit"}
  ],
  "routes": [],
  "user_flows": [
    "Sur /tasks/new : l'utilisateur crée une tâche",
    "Sur /tasks : l'utilisateur consulte et filtre ses tâches",
    "Sur /tasks/[id] : l'utilisateur lit le détail et voit les commentaires"
  ],
  "ui_labels": {
    "Task": {"title": "Titre", "description": "Description", "status": "Statut"},
    "Comment": {"content": "Commentaire"}
  },
  "title_plurals": {"Task": "Tâches", "Comment": "Commentaires"},
  "enum_value_labels": {"TaskStatus": {"pending": "En attente", "in_progress": "En cours", "done": "Terminé"}},
  "page_links": {
    "/tasks": ["/tasks/new", "/tasks/[id]"],
    "/tasks/new": ["/tasks"],
    "/tasks/[id]": ["/tasks"]
  },
  "design_system": {
    "mood": "productif, épuré, SaaS interne",
    "animation_level": "standard",
    "density": "normal",
    "primary_color": "blue-700",
    "sidebar_bg": "slate-900",
    "brand_name": "Task Manager"
  }
}
```

### Modèles donnés : Post (authorId, published Boolean, slug String @unique)
```json
{
  "pages": [
    {"path": "/", "auth": false, "page_type": "custom"},
    {"path": "/posts", "auth": false, "model": "Post", "page_type": "list"},
    {"path": "/posts/[slug]", "auth": false, "model": "Post", "page_type": "detail-slug"},
    {"path": "/dashboard", "auth": true, "page_type": "custom"},
    {"path": "/dashboard/posts", "auth": true, "model": "Post", "page_type": "list"},
    {"path": "/dashboard/posts/new", "auth": true, "model": "Post", "page_type": "create"},
    {"path": "/dashboard/posts/[id]/edit", "auth": true, "model": "Post", "page_type": "edit"}
  ],
  "routes": [],
  "user_flows": [
    "Sur /posts : un visiteur parcourt les articles publiés",
    "Sur /posts/[slug] : un visiteur lit un article",
    "Sur /dashboard : l'auteur voit le nombre d'articles publiés vs total",
    "Sur /dashboard/posts : l'auteur liste ses articles publiés et brouillons",
    "Sur /dashboard/posts/new : l'auteur rédige un nouvel article"
  ],
  "ui_labels": {"Post": {"title": "Titre", "excerpt": "Extrait", "published": "Publié"}},
  "title_plurals": {"Post": "Articles"},
  "enum_value_labels": {},
  "page_links": {
    "/posts": ["/posts/[slug]"],
    "/posts/[slug]": ["/posts"],
    "/dashboard": ["/dashboard/posts"],
    "/dashboard/posts": ["/dashboard/posts/new", "/dashboard/posts/[id]/edit"],
    "/dashboard/posts/new": ["/dashboard/posts"],
    "/dashboard/posts/[id]/edit": ["/dashboard/posts"]
  },
  "design_system": {
    "mood": "éditorial, clair, lecture agréable",
    "animation_level": "standard",
    "density": "spacious",
    "primary_color": "indigo-600",
    "sidebar_bg": "white",
    "brand_name": "Mon Blog"
  }
}
```

### Modèles donnés : Category (slug String @unique, articles Article[]), Article (categoryId FK → Category, slug String @unique, published Boolean)
PATTERN GÉNÉRAL : tout modèle avec `slug String @unique` qui est aussi un parent FK → RÈGLE 9 prime toujours sur RÈGLE 5 → JAMAIS de `[id]` pour ce modèle, même s'il a des enfants FK. Valable pour Category, Tag, ProductFamily, Author, ou tout autre modèle slug+parent.
```json
{
  "pages": [
    {"path": "/", "auth": false, "page_type": "custom"},
    {"path": "/articles", "auth": false, "model": "Article", "page_type": "list"},
    {"path": "/articles/[slug]", "auth": false, "model": "Article", "page_type": "detail-slug"},
    {"path": "/dashboard", "auth": true, "model": null, "page_type": "custom"},
    {"path": "/dashboard/categories", "auth": true, "model": "Category", "page_type": "list"},
    {"path": "/dashboard/categories/new", "auth": true, "model": "Category", "page_type": "create"},
    {"path": "/dashboard/categories/[slug]/edit", "auth": true, "model": "Category", "page_type": "edit"},
    {"path": "/dashboard/articles", "auth": true, "model": "Article", "page_type": "list"},
    {"path": "/dashboard/articles/new", "auth": true, "model": "Article", "page_type": "create"},
    {"path": "/dashboard/articles/[id]/edit", "auth": true, "model": "Article", "page_type": "edit"}
  ],
  "routes": [],
  "user_flows": [
    "Sur /articles : un visiteur parcourt les articles publiés",
    "Sur /articles/[slug] : un visiteur lit un article",
    "Sur /dashboard/categories : l'utilisateur gère ses catégories",
    "Sur /dashboard/articles : l'utilisateur liste tous ses articles avec leur catégorie"
  ],
  "ui_labels": {
    "Category": {"name": "Nom", "slug": "Slug"},
    "Article": {"title": "Titre", "published": "Publié", "categoryId": "Catégorie"}
  },
  "title_plurals": {"Category": "Catégories", "Article": "Articles"},
  "enum_value_labels": {},
  "page_links": {
    "/articles": ["/articles/[slug]"],
    "/dashboard/categories": ["/dashboard/categories/new"],
    "/dashboard/articles": ["/dashboard/articles/new"]
  },
  "design_system": {
    "mood": "éditorial, propre",
    "animation_level": "standard",
    "density": "normal",
    "primary_color": "indigo-600",
    "sidebar_bg": "white",
    "brand_name": "Writer Pad"
  }
}
```\
"""

_PAGE_FORMAT = """\
## FORMAT DE SORTIE — JSON uniquement

```json
{
  "pages": [{"path": "/...", "auth": bool, "model": "Name|null", "page_type": "list|create|detail|detail-slug|edit|custom"}, ...],
  "routes": [],
  "user_flows": ["Sur /path : description", ...],
  "ui_labels": {"ModelName": {"fieldName": "Label lisible", ...}, ...},
  "title_plurals": {"ModelName": "Libellé pluriel", ...},
  "enum_value_labels": {"EnumName": {"val_raw": "Label affiché", ...}, ...},
  "page_links": {"/path": ["/linked-path", ...], ...},
  "design_system": {
    "mood": "...", "animation_level": "none|standard|enhanced",
    "density": "compact|normal|spacious",
    "primary_color": "couleur-shade (ex: blue-700)",
    "sidebar_bg": "white|slate-900|...",
    "brand_name": "Nom app"
  }
}
```

Retourne UNIQUEMENT le JSON. Aucune explication, aucun markdown.\
"""

_PAGE_SYSTEM_PROMPT = "\n\n".join([
    (
        "Tu es un architecte d'interface expert Next.js 14 + Clerk V6.\n"
        "Tu reçois un brief et les modèles Prisma déjà extraits.\n"
        "Ta mission UNIQUE : planifier les pages, routes, labels et design_system.\n"
        "Ne régénère PAS les modèles — ils sont déjà fournis en input."
    ),
    _PAGE_STACK_INVARIANTS,
    _PAGE_DEDUCTION_RULES,
    _PAGE_FEW_SHOT,
    _PAGE_FORMAT,
])


# ─────────────────────────────────────────────────────────────────────────────
# Node
# ─────────────────────────────────────────────────────────────────────────────

async def page_planner_node(state: dict) -> dict:
    """
    Planifie les pages, routes et labels depuis les modèles du brief.

    Skip si brief contient déjà des pages.
    Requiert : brief.models non vide (rempli par domain_interpreter_node).
    Fail-safe : erreur LLM → ApplicationError.
    """
    from temporalio.exceptions import ApplicationError

    brief = state.get("brief", {})

    if brief.get("pages"):
        logger.info("[page_planner] pages déjà présentes → skip")
        return {}

    models = brief.get("models", [])
    if not models:
        raise ApplicationError(
            "page_planner: models absent — domain_interpreter doit s'exécuter en premier.",
            non_retryable=True,
        )

    description = brief.get("description", "").strip()

    from agents.llm_provider import get_chat_llm
    from langchain_core.messages import SystemMessage, HumanMessage as _HM
    from agents.stack_config import get_llm_models as _get_llm_models

    _arch_model = _get_llm_models().get("architect_base", "gpt-4o-mini")
    llm = get_chat_llm(
        model=_arch_model,
        temperature=0.0,
        api_key=os.getenv("ARCHITECT_API_KEY", os.getenv("OPENAI_API_KEY")),
    ).bind(response_format={"type": "json_object"})

    context = {
        "description": description,
        "models": models,
        "enums": brief.get("enums", {}),
    }

    try:
        response = await llm.ainvoke([
            SystemMessage(content=_PAGE_SYSTEM_PROMPT),
            _HM(content=json.dumps(context, ensure_ascii=False)),
        ])
        result: dict = json.loads(response.content)
    except json.JSONDecodeError as e:
        raise ApplicationError(f"page_planner: réponse non-JSON — {e}", non_retryable=False)
    except Exception as e:
        raise ApplicationError(f"page_planner: erreur LLM — {e}", non_retryable=False)

    if not result.get("pages"):
        raise ApplicationError(
            "page_planner: aucune page générée — brief trop vague ?",
            non_retryable=False,
        )

    logger.info(
        "[page_planner] ✓ %d page(s), design=%s",
        len(result.get("pages", [])),
        result.get("design_system", {}).get("primary_color", "?"),
    )

    # Fusion dans le brief (sans écraser ce qui était déjà présent)
    updated_brief = {
        **brief,
        "pages": result.get("pages", []),
        "routes": result.get("routes", []),
        "user_flows": result.get("user_flows", []),
        "design_system": result.get("design_system", {}),
        "ui_labels": result.get("ui_labels", {}),
        "title_plurals": result.get("title_plurals", {}),
        "enum_value_labels": result.get("enum_value_labels", {}),
        "page_links": result.get("page_links", {}),
    }
    return {"brief": updated_brief}
