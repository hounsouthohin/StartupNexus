# Generator Contract — Software Agent Factory
## Stack : `nextjs-clerk-prisma` · Version : 1.0 (Mai 2026)

Ce document est le **contrat formel de la couche déterministe** de la factory. Il définit les règles d'architecture que tout développeur doit respecter quand il ajoute, modifie ou corrige un générateur.

> Ce document complète `BRIEF_CONTRACT.md` (contrat d'entrée) et décrit l'intérieur de la machine de génération.

---

## 1. Principe fondateur

**Toute question sur la structure du brief a une réponse unique : une méthode sur `AppSpec`.**

Les générateurs sont des **renderers passifs**. Ils ne raisonnent pas sur la structure du brief — ils appellent des méthodes sur `AppSpec` et produisent du texte. Toute intelligence structurelle (quel service appeler, quelle route de redirect, quelles pages sont publiques, quel modèle associer à quelle page) appartient à `AppSpec`, pas aux générateurs.

Cette règle garantit que :
- Ajouter un nouveau type de brief ne demande qu'une nouvelle méthode sur `AppSpec`
- Les générateurs ne grossissent pas en conditions spéciales au fil des app types
- La logique est testable en isolation sur `AppSpec`, sans dépendance aux fichiers générés

---

## 2. Architecture en 3 couches

```
┌─────────────────────────────────────────────────────────────┐
│  AppSpec  (agents/project_spec.py)                          │
│  Source de vérité. Méthodes de lookup et de dérivation.     │
│  Aucun générateur ne dérive lui-même de l'info du brief.    │
└────────────────────────────┬────────────────────────────────┘
                             │ toutes les méthodes get_X()
┌────────────────────────────▼────────────────────────────────┐
│  dev_naming.py  (agents/stacks/nextjs_clerk_prisma/)        │
│  Fonctions de nommage pures, partagées par tous les         │
│  générateurs. Jamais dupliquées dans un fichier générateur. │
└────────────────────────────┬────────────────────────────────┘
                             │ reçoivent (spec, workdir)
┌────────────────────────────▼────────────────────────────────┐
│  Generators  (agents/stacks/nextjs_clerk_prisma/)           │
│  dev_*_generator.py — renderers passifs.                    │
│  Appellent spec.get_X() et dev_naming.xxx().                │
│  Retournent dict[str, str] (path → contenu).                │
└─────────────────────────────────────────────────────────────┘
                             │ orchestré par
┌────────────────────────────▼────────────────────────────────┐
│  dev_graph.py  (agents/stacks/nextjs_clerk_prisma/)         │
│  Appelle les générateurs dans l'ordre.                      │
│  Gère template_written (fichiers lockés).                   │
│  Passe le même spec à tous les générateurs.                 │
└─────────────────────────────────────────────────────────────┘
```

### Règle de séparation — que va où

| Ce qui appartient à **AppSpec** | Ce qui appartient aux **générateurs** |
|---|---|
| "Quelles pages listent le modèle Post ?" | "Comment écrire l'import TypeScript de ce service ?" |
| "Quelles routes sont publiques ?" | "Comment formater le createRouteMatcher ?" |
| "Quel service appeler pour une page publique ?" | "Comment structurer le return JSX d'une page ?" |
| "Quel est le path de redirect après une mutation ?" | "Comment écrire la ligne redirect() ?" |
| "Ce modèle a-t-il un champ status ?" | "Comment nommer la méthode getPublished ?" |

---

## 3. AppSpec — méthodes de lookup requises

Ces méthodes **doivent exister** sur `AppSpec` (`agents/project_spec.py`). Elles remplacent tout calcul structurel local dans les générateurs.

```python
class AppSpec(BaseModel):
    # --- champs existants (project_name, models, pages, ...) ---

    def get_model_by_name(self, name: str) -> "AppModel | None":
        """Lookup PascalCase → AppModel. Retourne None si absent."""
        return next((m for m in self.models if m.name == name), None)

    def get_list_page_for_model(self, model_name: str) -> "str | None":
        """Path de la page liste principale pour ce modèle (page_type='list').
        Ex: 'Post' → '/dashboard', 'Category' → '/categories'.
        Retourne None si aucune page liste ne référence ce modèle."""
        return next(
            (p.path for p in self.pages if p.model == model_name and p.page_type == "list"),
            None,
        )

    def get_public_pages(self) -> "list[AppPage]":
        """Toutes les pages avec auth_required=False, dans l'ordre du brief."""
        return [p for p in self.pages if not p.auth_required]

    def get_private_pages(self) -> "list[AppPage]":
        """Toutes les pages avec auth_required=True."""
        return [p for p in self.pages if p.auth_required]

    def get_pages_for_model(self, model_name: str) -> "list[AppPage]":
        """Toutes les pages qui référencent ce modèle via page.model."""
        return [p for p in self.pages if p.model == model_name]

    def model_has_status_field(self, model_name: str) -> bool:
        """True si le modèle a un champ nommé 'status'."""
        model = self.get_model_by_name(model_name)
        if not model:
            return False
        return any("status" in field for field in (model.fields or []))
```

> **Règle :** si un générateur a besoin d'une information structurelle non couverte par ces méthodes, la réponse est d'ajouter une méthode sur `AppSpec`, pas de calculer dans le générateur.

---

## 4. page_type — champ explicite sur AppPage

Le type de page est **déclaré explicitement** dans le brief et propagé sur `AppPage`. Il ne doit jamais être deviné par heuristique sur le chemin URL.

```python
from typing import Literal

class AppPage(BaseModel):
    path: str
    auth_required: bool = True
    model: str | None = None
    page_type: Literal["list", "create", "detail", "custom"] = "custom"
```

### Sémantique des valeurs

| Valeur | Quand l'utiliser | `model` obligatoire | Ce que le générateur produit |
|---|---|---|---|
| `"list"` | Page affichant une collection d'items | ✅ oui | `page.tsx` avec `getAll(userId)` ou `getPublished()` + stub client avec `items: SerializedXxx[]` |
| `"create"` | Formulaire de création (path finit en `/new` ou `/create`) | ❌ non | `page.tsx` minimal + stub client sans props |
| `"detail"` | Vue d'un item unique (path contient `[id]`) | ✅ oui | `page.tsx` avec `getById(userId, id)` + stub client avec `item: SerializedXxx` |
| `"custom"` | Dashboard de stats, page d'accueil, page sans modèle dominant | selon le cas | stub minimal, LLM complète |

### Règle de validation croisée

Un `AppSpec` invalide si :
- `page_type == "list"` ET `model` est absent → **erreur blueprint**
- `page_type == "detail"` ET `model` est absent → **erreur blueprint**
- `page_type == "list"` ET `path` contient `[id]` → **incohérence**

Ces validations sont dans `AppSpec.model_validator()`, pas dans les générateurs.

---

## 5. Catalogue des générateurs

Tout générateur doit être déclaré dans ce tableau **avant** d'être intégré dans `dev_graph.py`.

| Fichier | Produit | Locké (`template_written`) | Signature |
|---|---|---|---|
| `dev_schema_generator.py` | `prisma/schema.prisma` | ✅ oui | `generate_schema(spec, workdir) -> dict` |
| `dev_service_generator.py` | `lib/services/*.service.ts` | ✅ oui | `generate_services(spec, workdir) -> dict` |
| `dev_actions_generator.py` | `app/*/actions.ts` | ✅ oui | `generate_actions(spec, workdir) -> dict` |
| `dev_pages_generator.py` | `app/*/page.tsx` | ✅ oui (pages avec model) | `generate_page_stubs(spec, workdir) -> dict` |
| `dev_pages_generator.py` | `app/*/page-client.tsx` (stub) | ❌ non — LLM complète JSX | `generate_page_client_stubs(spec, workdir)` |
| `dev_middleware_generator.py` | `middleware.ts` | ✅ oui | `generate_middleware(spec, workdir) -> dict` |

**Signature obligatoire pour tout nouveau générateur :**
```python
def generate_xxx(spec: AppSpec, workdir: str) -> dict[str, str]:
    """Retourne {chemin_relatif: contenu}. Ne write pas sur disque directement."""
```

**Pattern d'intégration dans `dev_graph.py` :**
```python
files = generate_xxx(spec_obj, project_workdir)
_write_generated_files(files, project_workdir)
template_written.update(files)   # lock — LLM ne peut pas écraser
```

---

## 6. Protocole template_written

`template_written` est un `dict[str, str]` géré par `dev_graph.py`. Tout fichier présent dans ce dict **ne peut pas être écrasé par le LLM** pendant la phase de génération.

### Ce qui DOIT être locké

- Tous les fichiers produits par un générateur déterministe (`page.tsx`, `*.service.ts`, `actions.ts`, `middleware.ts`, `schema.prisma`)
- Tout fichier dont le contenu est entièrement calculable depuis `AppSpec` sans intervention LLM

### Ce qui NE DOIT PAS être locké

- `page-client.tsx` — le JSX body est complété par le LLM
- `layout.tsx` — structure globale laissée au LLM
- `lib/types.ts`, `lib/schemas.ts` — le LLM dérive les types Zod

### Règle

> Un fichier est locké si et seulement si le corriger à la main (après génération) serait toujours nécessaire sans le lock. Si le LLM peut le compléter correctement de façon autonome, il ne doit pas être locké.

---

## 7. dev_naming.py — fonctions de nommage partagées

Toutes les transformations de nommage sont dans `dev_naming.py`. **Aucun générateur n'implémente ses propres fonctions de nommage.** Si une transformation manque, on l'ajoute ici.

```python
# agents/stacks/nextjs_clerk_prisma/dev_naming.py

def pascal_to_camel(name: str) -> str:
    """Post → post, BlogPost → blogPost"""

def pascal_to_plural_camel(name: str) -> str:
    """Post → posts, Category → categories (gère les irréguliers courants)"""

def pascal_to_kebab(name: str) -> str:
    """BlogPost → blog-post"""

def pascal_to_service_var(name: str) -> str:
    """Post → postService, Category → categoryService"""

def pascal_to_client_component(name: str) -> str:
    """Post → PostClient, Category → CategoriesClient"""

def path_to_component_name(path: str) -> str:
    """/dashboard → DashboardPage, /blog/new → BlogNewPage"""

def model_to_serialized_type(name: str) -> str:
    """Post → SerializedPost"""
```

---

## 8. Règles pour ajouter un nouveau générateur

Ordre strict à respecter :

1. **Identifier les méthodes AppSpec nécessaires** — les ajouter à `project_spec.py` si elles n'existent pas
2. **Identifier les fonctions de nommage nécessaires** — les ajouter à `dev_naming.py` si elles n'existent pas
3. **Écrire le générateur** — signature `(spec: AppSpec, workdir: str) -> dict[str, str]`, sans logique de lookup interne
4. **Valider sur AppSpec** — si une règle métier doit être vérifiée (ex: model obligatoire pour une list page), elle va dans `AppSpec.model_validator()`, pas dans le générateur
5. **Déclarer dans ce catalogue** (section 5)
6. **Intégrer dans `dev_graph.py`** via le pattern `template_written.update(generate_xxx(spec, workdir))`
7. **Documenter la limitation** dans `BRIEF_CONTRACT.md` section "Ce que la factory ne supporte pas" si le cas n'est pas encore couvert

---

## 9. Failles architecturales connues (à corriger)

| ID | Description | Fichier actuel | Correction cible |
|---|---|---|---|
| F1 | `page_type` deviné par heuristique string au lieu d'être déclaré | `dev_pages_generator.py` | Champ `page_type` sur `AppPage` + validation `AppSpec` |
| F2 | `redirect('/posts')` hardcodé — ignore le path réel de la page liste | `dev_actions_generator.py` | `spec.get_list_page_for_model(model_name)` |
| F3 | `middleware.ts` template fixe — ne déclare pas les routes `auth: false` | `middleware.ts` (template) | `dev_middleware_generator.py` → `spec.get_public_pages()` |
| F4 | Fonctions de nommage réimplémentées localement dans chaque générateur | `dev_pages_generator.py`, autres | Centraliser dans `dev_naming.py` |
| F5 | Certains générateurs reçoivent des dicts bruts, pas `AppSpec` | `dev_actions_generator.py` | Uniformiser la signature |
| F6 | Aucune validation que `page.model` correspond à un modèle réel | Aucun | `AppSpec.model_validator()` |

---

## 10. Changelog

| Version | Date | Changements |
|---|---|---|
| 1.0 | Mai 2026 | Document initial — principe fondateur, 3 couches, méthodes AppSpec, `page_type`, catalogue générateurs, protocole `template_written`, `dev_naming.py`, règles d'ajout, failles F1-F6 |
