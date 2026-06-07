# CAPACITÉS DÉTERMINISTES DE LA FACTORY

Ce fichier décrit ce que la factory sait construire automatiquement.
Il est injecté dans `pages_detail_node` (architect.py → `_FACTORY_CAPABILITIES`) pour que
le LLM génère des descriptions de pages parfaitement alignées avec les générateurs existants.

**Règle de maintenance** : toute modification d'un générateur doit être répercutée ici
ET dans `_FACTORY_CAPABILITIES` dans `architect.py`.

---

## Générateurs automatiques — ne pas décrire dans pages_detail, déjà géré

| page_type      | Ce qui est généré automatiquement                                              |
|----------------|--------------------------------------------------------------------------------|
| `"list"`       | table tous champs visibles + boutons Nouveau / Modifier / Supprimer            |
| `"create"`     | formulaire tous champs éditables + submit                                      |
| `"detail"`     | carte tous champs + boutons Modifier / Supprimer                               |
| `"detail-slug"`| lecture seule, accès via `params.slug` (pas de boutons d'action)              |
| `"custom"`     | shell vide — le LLM DOIT décrire précisément le contenu dans `pages_detail`   |

## Services auto-générés par modèle (7 méthodes garanties)

```
getAll(userId)              — liste de l'utilisateur
getById(userId, id)         — par id pour l'utilisateur
getPublicById(id)           — sans auth
getPublicAll()              — liste publique
create(userId, data)        — création
update(id, data)            — mise à jour
delete(userId, id)          — suppression
getBySlug(slug)             — disponible si le modèle a un champ `slug String @unique`
getAllWithRelations(userId)  — disponible si le modèle a des @relation Prisma
```

## Convention paramètres dynamiques — INVARIANT TypeScript

| Segment URL | Paramètre TypeScript | Interdit                              |
|-------------|----------------------|---------------------------------------|
| `[id]`      | `params.id`          | params.taskId, params.postId, etc.    |
| `[slug]`    | `params.slug`        | params.name, params.identifier, etc.  |

## [CROSS_ENTITY] — données secondaires non auto-gérées

La factory ne génère PAS automatiquement les fetches depuis plusieurs modèles sur une même page.

Si une page doit afficher des données d'un modèle SECONDAIRE (pas le modèle principal de la page),
le LLM doit ajouter le tag `[CROSS_ENTITY: NomDuModèle]` dans la description de cette page.

Ce tag est lu par `build_page_contracts()` dans `planner.py` pour générer le fetch secondaire approprié
dans le `context_hint` de `page.tsx`.

**Exemple** : `/projects/[id]` qui doit aussi afficher ses tâches →
```
"Détail d'un projet. Affiche : title, description, status.
Affiche aussi la liste des tâches liées : title, dueDate, status.
[CROSS_ENTITY: Task] [INTERACTIVE]"
```

Sans ce tag, la factory génère uniquement le fetch du modèle principal (Project).

## Design System auto-généré (ne pas décrire dans pages_detail)

Les fichiers suivants sont générés automatiquement par `dev_design_system_generator` :

| Fichier | Contenu |
|---------|---------|
| `app/globals.css` | CSS variables HSL depuis `design_system.primary_color` — `--primary`, `--foreground`, `--radius`… |
| `tailwind.config.js` | Format shadcn — `bg-primary` = `hsl(var(--primary))`, `text-foreground`, `bg-muted`… |
| `components/ui/button.tsx` | Composant shadcn officiel |
| `components/ui/input.tsx` | Composant shadcn officiel |
| `components/ui/card.tsx` | Composant shadcn officiel |
| `components/ui/table.tsx` | Composant shadcn officiel |
| `components/ui/badge.tsx` | Composant shadcn officiel |
| `components/ui/label.tsx` | Composant shadcn officiel |
| `components/ui/textarea.tsx` | Composant shadcn officiel |
| `components/ui/select.tsx` | Composant shadcn officiel |
| `components/Empty.tsx` | État vide sémantique (custom) |
| `components/StatCard.tsx` | Carte métrique (custom) |
| `app/components/layout/DashboardShell.tsx` | Sidebar avec `sidebar_bg` du brief |
| `app/layout.tsx` | ClerkProvider + DashboardShell |

**L'architect ne doit JAMAIS décrire** :
- La configuration des couleurs (gérée par `design_system.primary_color`)
- L'import ou l'usage de Button/Card/Table (le LLM en est informé via le prompt)
- La création de globals.css ou tailwind.config.js
- La sidebar ou le layout principal

## Ce que le LLM n'a PAS besoin de décrire

- Les formulaires CRUD standard (list/create/detail/detail-slug) — auto-générés
- Les imports Clerk, `auth()`, `redirect('/sign-in')` — injectés automatiquement
- La signature TypeScript de base des composants — générée par le planner
- Les imports service standard pour le modèle principal — dans le context_hint automatique
- Le design system, les couleurs, les composants shadcn — générés et injectés via le prompt
