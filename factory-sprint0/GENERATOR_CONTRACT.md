# Generator Contract — Software Agent Factory
## Stack : `nextjs-clerk-prisma` · v1.1 (Mai 2026)

Contrat de la couche déterministe. Pour les développeurs qui ajoutent ou modifient un générateur.

> Complète `BRIEF_CONTRACT.md` (contrat d'entrée). Décrit l'intérieur de la machine.

---

## 1. Principe

**Toute question sur la structure du brief = une méthode sur `AppSpec`.**

Les générateurs sont des **renderers passifs** : ils appellent `AppSpec.get_X()` et produisent du texte. Toute logique structurelle (quel service appeler, quelles pages sont publiques, quel modèle associer) appartient à `AppSpec`, pas aux générateurs. Cela garantit que les générateurs ne grossissent pas en conditions spéciales au fil des app types.

---

## 2. Architecture en 3 couches

```
AppSpec  (agents/project_spec.py)
  └─ Source de vérité. Méthodes get_X(). Validation dans model_validator().
     Aucun générateur ne dérive lui-même de l'info du brief.

dev_naming.py  (agents/stacks/nextjs_clerk_prisma/)
  └─ Fonctions de nommage pures, partagées. Jamais dupliquées dans un générateur.

Generators  (agents/stacks/nextjs_clerk_prisma/dev_*_generator.py)
  └─ Renderers passifs. Reçoivent (spec, workdir). Retournent dict[str, str].
     N'écrivent pas sur disque directement.

dev_graph.py
  └─ Orchestre les générateurs dans l'ordre. Gère template_written (fichiers lockés).
```

| Ce qui appartient à **AppSpec** | Ce qui appartient aux **générateurs** |
|---|---|
| Quelles pages listent le modèle X ? | Comment écrire l'import TypeScript ? |
| Quelles routes sont publiques ? | Comment formater le JSX d'une page ? |
| Quel service appeler pour une page publique ? | Comment structurer un formulaire ? |
| Ce modèle a-t-il un champ `status` ? | Comment nommer la méthode `getPublished` ? |

---

## 3. AppSpec — méthodes clés

| Méthode | Retourne |
|---|---|
| `get_model_by_name(name)` | `AppModel \| None` |
| `get_list_page_for_model(model_name)` | `str \| None` — path de la page liste principale |
| `get_public_pages()` | `list[AppPage]` — pages `auth_required=False` |
| `get_private_pages()` | `list[AppPage]` — pages `auth_required=True` |
| `get_pages_for_model(model_name)` | `list[AppPage]` — pages référençant ce modèle |
| `model_has_status_field(model_name)` | `bool` |

> Si un générateur a besoin d'une info structurelle non couverte → ajouter la méthode sur `AppSpec`, pas calculer dans le générateur.

---

## 4. page_type — déclaré dans le brief, jamais deviné

```python
class AppPage(BaseModel):
    path: str
    auth_required: bool = True
    model: str | None = None
    page_type: Literal["list", "create", "detail", "custom"] = "custom"
```

| Valeur | `model` | Ce que le générateur produit |
|---|---|---|
| `"list"` | obligatoire | `page.tsx` déterministe (`getAll`/`getPublished`) + `page-client.tsx` list UI |
| `"create"` | omis | `page.tsx` déterministe (import client) + `page-client.tsx` form |
| `"detail"` | obligatoire | `page.tsx` déterministe (`getById`) + stub client |
| `"custom"` | optionnel | stubs minimaux, LLM complète |

Validations dans `AppSpec.model_validator()` :
- `page_type="list"` ou `"detail"` sans `model` → erreur blueprint
- `page_type="list"` avec `[id]` dans le path → incohérence

---

## 5. Catalogue des générateurs

| Fichier | Produit | Locké (`template_written`) |
|---|---|---|
| `dev_schema_generator.py` | `prisma/schema.prisma` | ✅ |
| `dev_service_generator.py` | `lib/services/*.service.ts` | ✅ |
| `dev_actions_generator.py` | `app/*/actions.ts` | ✅ |
| `dev_pages_generator.py` | `app/*/page.tsx` (avec model) | ✅ |
| `dev_pages_generator.py` | `app/*/page-client.tsx` (list + create) | ✅ |
| `dev_middleware_generator.py` | `middleware.ts` | ✅ |
| `dev_design_system_generator.py` | `app/globals.css`, `tailwind.config.js`, `postcss.config.js` | ✅ |
| `dev_design_system_generator.py` | `components/ui/*.tsx` (shadcn officiel, copié depuis `assets/shadcn/`) | ✅ |
| `dev_design_system_generator.py` | `lib/utils.ts` (shadcn util), `components/Empty.tsx`, `components/StatCard.tsx` | ✅ |
| `dev_layout_generator.py` | `app/components/layout/DashboardShell.tsx`, `app/layout.tsx` | ✅ |
| `dev_navigation_generator.py` | `components/navigation.tsx` (liens sidebar depuis spec.pages) | ✅ |

**Signature obligatoire pour tout nouveau générateur :**
```python
def generate_xxx(spec: AppSpec, workdir: str) -> dict[str, str]:
    """Retourne {chemin_relatif: contenu}. Ne write pas sur disque."""
```

### Cas spécial — générateurs design (pas de AppSpec)

Les générateurs de design (`dev_design_system_generator`, `dev_layout_generator`) reçoivent
`project_workdir: str` et `design_system: dict | None` plutôt que `spec: AppSpec`. Raison :
le design_system est un sous-dict plat sans logique AppSpec. Signature tolérée :
```python
def generate_design_system(project_workdir: str, design_system: dict | None = None) -> dict[str, str]:
```

### Shadcn assets — prérequis

Les composants `components/ui/*.tsx` sont copiés depuis `factory-sprint0/assets/shadcn/`.
Ce répertoire doit être peuplé une seule fois en exécutant :
```powershell
cd factory-sprint0
powershell -ExecutionPolicy Bypass -File scripts\prebuild_shadcn.ps1
```
Puis commiter les fichiers générés. Si `assets/shadcn/` est absent → warning non-bloquant, composants shadcn absents du projet (les autres fichiers design sont générés normalement).

**Pattern d'intégration dans `dev_graph.py` :**
```python
files = generate_xxx(spec_obj, project_workdir)
_write_generated_files(files, project_workdir)
template_written.update(files)   # lock — LLM ne peut pas écraser
```

---

## 6. Protocole template_written

`template_written` : `dict[str, str]` géré par `dev_graph.py`. Tout fichier présent **ne peut pas être écrasé par le LLM**.

**Locké :** tout fichier entièrement calculable depuis `AppSpec` sans intervention LLM (schema, services, actions, `page.tsx` avec model, `page-client.tsx` list/create, middleware).

**Non locké :** `layout.tsx`, `lib/types.ts`, `lib/schemas.ts` — le LLM y apporte de la valeur réelle (types Zod dérivés, mise en page globale).

> Règle : un fichier est locké si et seulement si le laisser au LLM produirait systématiquement des résultats incorrects ou sous-optimaux.

---

## 7. dev_naming.py — fonctions partagées

Toutes les transformations de nommage sont ici. **Aucun générateur n'implémente ses propres fonctions de nommage.**

```python
pascal_to_camel(name)           # Post → post
pascal_to_plural_camel(name)    # Post → posts, Category → categories
pascal_to_kebab(name)           # BlogPost → blog-post
pascal_to_service_var(name)     # Post → postService
path_to_client_component(path)  # /dashboard → DashboardPageClient
path_to_page_component(path)    # /dashboard → DashboardPage
model_to_serialized_type(name)  # Post → SerializedPost
```

---

## 8. Ajouter un nouveau générateur — checklist

1. Identifier les méthodes `AppSpec` nécessaires → les ajouter à `project_spec.py` si absentes
2. Identifier les fonctions de nommage → les ajouter à `dev_naming.py` si absentes
3. Écrire le générateur avec la signature standard `(spec, workdir) -> dict[str, str]`
4. Placer les validations métier dans `AppSpec.model_validator()`, pas dans le générateur
5. Déclarer dans le catalogue (section 5)
6. Intégrer dans `dev_graph.py` via `template_written.update(...)`
7. Documenter les limitations dans `BRIEF_CONTRACT.md` section "Non supporté"

---

## 9. Changelog

| Version | Date | Changements |
|---|---|---|
| 1.0 | Mai 2026 | Document initial |
| 1.1 | Mai 2026 | `page-client.tsx` list/create lockés dans `template_written` · page_type déclaré (F1 fixée) · document raccourci |
| 1.2 | Juin 2026 | Ajout générateurs design au catalogue (dev_design_system_generator, dev_layout_generator, dev_navigation_generator) · tokens CSS variables · shadcn/ui prebuild script |
