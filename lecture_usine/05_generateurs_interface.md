# 05 — Générateurs d'interface (écrans, navigation, dashboard, design)

## Qui produit quoi
| Générateur | Produit | Technique |
|---|---|---|
| `dev_pages_generator` | `page.tsx` serveur de chaque page AVEC modèle (+ edit, loading, error, not-found, `/` racine) | Concaténation de chaînes. Liste : getAll / getAllWithRelations / getPublicAll ; admin → `getCurrentRole()` puis getAllAsAdmin ; création : fetch des options FK/M2M, garde initiateur (redirect) ; détail : getById/…AsAdmin/slug/public ; SEO generateMetadata sur detail-slug public. Pages SANS modèle → laissées au LLM. |
| `dev_form_generator` (+ 9 templates Jinja2) | `page-client.tsx` : list, create, edit, detail | Prépare un contexte → template (StrictUndefined). Renderer UNIQUE des listes (public → statut → recherche → card-grid → table). Détail : champs, badges, dates, montants, M2M, **boutons de transition + Modifier + Supprimer affichés à TOUS les acteurs connectés**. |
| `feature_modules/module_detail_with_children` | page-client détail parent + liste enfants + formulaire enfant inline | Registre de modules (`register()`, priorité), activé si relation 1-N + page détail privée. |
| `dev_layout_generator` | `layout.tsx` + DashboardShell (sidebar) ou TopNavShell | Templates chaînes avec placeholders `__X__`. S2 : nav filtrée par surface, **modèle binaire privilégié / « base » (2 acteurs max)**. Labels = title_plurals. |
| `dev_middleware_generator` | `middleware.ts` Clerk | Routes publiques exactes + `/` si pages publiques + `/api/oracle`. |
| `dev_hub_generator` | `app/dashboard/page.tsx` (+ home publique si liste filtrée) | Simple : 1 compteur par modèle (getAll dé-paginé) ; riche : KPI + listes filtrées compilés depuis `pages_detail['/dashboard']`. **Un seul dashboard pour tous les acteurs** ; `roles.dashboard` jamais lu. |
| `dev_seo_generator` | sitemap.ts, robots.ts | Si pages publiques. |
| `design_resolver` (core) | design_system | Mots-clés du brief → preset (design_presets.json) + override couleur. 0 LLM. |
| `dev_design_system_generator` | globals.css (variables HSL), tailwind.config, composants ui | Déterministe. |
| `dev_design_brief` | DESIGN_BRIEF.json | 1 appel LLM : icône Lucide, badge_fields (couleurs), highlight_fields, list_card_layout, nav_icons par entité. |
| `dev_design_compiler` | décorations pour templates | Vocabulaire fermé → classes Tailwind statiques (évite la purge JIT). |
| `dev_shell_enricher` | icônes dans la nav | TSC-guardé. |

## Constat « pas d'âme » dans le code
- **0** occurrence de rôle/initiateur/capacité dans les 9 templates → toute affordance (Modifier, Supprimer, Faire évoluer, Nouveau) est montrée sans savoir qui regarde ; c'est le serveur qui refuse après coup (affordance malhonnête).
- Dashboard unique, non différencié par acteur ; les indicateurs par acteur déclarés par l'architect (`roles.dashboard`) ne sont consommés par personne.
- Profil-singleton impossible à exprimer : chaque entité reçoit liste/création/détail/édition.
- Nav : 2 acteurs codés en dur ; entité dans aucune surface → visible par tous.
- Plusieurs générateurs recalculent les mêmes choses (fk_list par chaîne dans pages_generator alors que le contexte a fk_fields ; pluriel anglais réimplémenté ; détection titre/visibilité par listes de noms).

## Ce qui est solide
Renderer de liste unifié ; Design Compiler (vocabulaire fermé) ; templates Jinja2 StrictUndefined ; SEO ; KPI/listes filtrées compilés en expressions exactes (le patron « contrat → code exact » marche).
