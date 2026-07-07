# CARTE DE LA MACHINE — Software Agent Factory
> Document opérateur : 5 minutes de lecture pour savoir ce qui existe, qui décide de quoi,
> et ce qui a changé. Mis à jour à CHAQUE session. (Détails → Roadmap3.2.0.md, typeApps.md)
> Dernière mise à jour : **6 Juillet 2026** (post-unification DY6 + chantiers ②③④⑤)

---

## VUE D'ENSEMBLE — le pipeline complet

```
Brief client (langage naturel)
  → ARCHITECT (5 nœuds LLM + 1 déterministe)     : comprend → ProjectSpec (contrat)
  → DEV_GRAPH (14 étapes, détail ci-dessous)      : génère l'app → BUILD
  → REVIEWER (2 couches : Python + LLM)           : audite sécurité + conformité brief
  → CORRECTION_PASS (si findings actionnables)    : corrige les pages custom + re-review
  → QA (Jest) → LEARNER (suggestions standards)   : boucle d'apprentissage
```

## FRONTIÈRE INTELLIGENCE / DÉTERMINISME (PRINCIPE 4)

| L'IA décide (10 points) | Le déterminisme garantit |
|---|---|
| domain_interpreter : brief → modèles Prisma | Schema Prisma final (inverses injectées, M2M complété) |
| page_planner : pages, labels FR, design mood | Types, Zod, services, actions (zéro variance) |
| semantic_annotator : sens des champs, features | Pages + formulaires CRUD (templates Jinja2) |
| pages_detail : contrat des pages custom + **kpis[]** | **Expressions KPI compilées en TS exact** (nouveau) |
| design_brief : icônes, badges, layouts par entité | Design system (7 presets, CSS vars, shadcn) |
| page_enricher : embellit (TSC-guardé, rollback) | SEO : sitemap, robots, generateMetadata |
| dev executor : pages custom (home, dashboard) | Fichiers protégés (template_written) |
| reviewer L2 : conformité brief, ghost success | reviewer L1 : IDOR, CROSS_USER, AUTH, **PII public** |
| correction_pass : re-génère pages custom fautives | Trigger correction : findings actionnables (verdict-indépendant) |
| qa : tests Jest | Guards architect (cartographiés → project_guards_map) |

---

## DEV_GRAPH — les 14 étapes

```
Entrée : spec (ProjectSpec dict)
│
├─① ISOLATION : workdir FACTORY_WORKDIR/<project_name>/ (nettoyage résidus)
│
├─② TEMPLATES STATIQUES (dev_file_ops.py + stack JSON)
│    package.json, tsconfig.json, jest.config.js, .env.local, etc.
│    └─ GUARD BLOQUANT : si package.json absent → ABORT
│
├─③ schema.prisma ← ProjectSpec.to_prisma_schema_block() [déterministe]
│    └─ Guards P1012 : inverses 1-N + inverses M2M injectées si manquantes
│
├─④ ModelGenerationContext (dev_model_context.py)  ← SOURCE UNIQUE DE VÉRITÉ
│    build_all_contexts(spec_obj) → dict[ModelName → ctx]
│    Chaque ctx expose :
│      .editable_fields / .display_fields / .relation_fields / .fk_fields
│      .m2m_fields         → relations many-to-many implicites (tags…)      [Sprint 5]
│      .datetime_fields / .decimal_fields  → sérialisation toISOString/Number [Sprint 5]
│      .has_slug / .has_status / .has_m2m / .has_public_pages / .has_relations
│      .ui_labels / .enum_value_labels / .serialized_type / .list_page_path
│
├─⑤ FONDATIONS (ordre strict — chaque étape dépend de la précédente)
│    ├─ dev_types_generator      → lib/types.ts          [déterministe]
│    │    └─ M2M : CreateXxxInput & { tagIds?: string[] }
│    ├─ dev_zod_generator        → lib/schemas.ts        [déterministe]
│    ├─ dev_service_generator    → lib/services/*.ts     [déterministe]
│    │    └─ service_modules/ (pluggable, registre auto-propagé vers l'architect) :
│    │         crud.py           → getAll/getById/create/update/delete
│    │         │                    M2M : connect (create) / set (update)
│    │         relations.py      → getAllWithRelations/getByIdWithRelations
│    │         public.py         → getPublicAll/getPublicById
│    │         slug.py           → getBySlug/getBySlugOwned (+relations si M2M)
│    │         status.py         → getPublished (ENUM only)
│    │         child.py          → getBy{Parent}Id
│    │         public_relations  → getPublicByIdWithRelations
│    └─ dev_actions_generator    → app/**/actions.ts     [déterministe]
│         └─ M2M : formData.getAll('tagIds') avant le parse Zod
│
├─⑥ UI INFRASTRUCTURE
│    ├─ dev_design_system_generator → tailwind.config.js, globals.css, components/ui/*
│    ├─ dev_layout_generator        → app/layout.tsx, TopNavShell, DashboardShell
│    │    └─ nav labels localisés via title_plurals
│    ├─ dev_middleware_generator    → middleware.ts (routes publiques vs privées)
│    └─ dev_navigation_generator    → navigation helpers
│
├─⑦ PAGES + PAGE-CLIENTS (déterministes pour les pages model)
│    ├─ dev_pages_generator
│    │    ├─ generate_page_stubs()      → page.tsx (model pages)  [protégé]
│    │    │    └─ detail-slug PUBLIC : generateMetadata (SEO) injecté
│    │    ├─ generate_edit_page_stubs() → [id|slug]/edit/page.tsx [protégé]
│    │    │    └─ M2M : fetch options + getByIdWithRelations (préselection)
│    │    ├─ generate_loading_files()   → loading.tsx
│    │    └─ generate_root_page_if_needed() → app/page.tsx
│    │
│    └─ dev_form_generator — _gen_list_client = RENDERER UNIQUE des listes (DY6 ✅)
│         Arbre : public → status (filtre, prime sur l'esthétique) → search → card-grid → table
│         ├─ list    → list_client.tsx.j2 (bloc recherche intégré via has_search)
│         │            / list_client_status.tsx.j2 / list_client_card_grid.tsx.j2
│         ├─ public  → public_list_client.tsx.j2 / public_list_card_grid.tsx.j2
│         ├─ create  → create_client.tsx.j2   (M2M : groupe de checkboxes tagIds)
│         ├─ edit    → edit_client.tsx.j2     (M2M : préselection defaultChecked)
│         └─ detail  → detail_client.tsx.j2   (M2M : badges tags · enums labellisés)
│         ⚠ SUPPRIMÉS (6 Juil) : module_search.py, module_status_flow.py,
│           list_client_search.tsx.j2 — double rendu divergent = mort silencieuse.
│
├─⑧ PAGES SPÉCIALES
│    ├─ dev_hub_generator         → app/dashboard/page.tsx
│    ├─ dev_seo_generator         → app/sitemap.ts + app/robots.ts   [Sprint 5, protégés]
│    └─ feature_modules/          → registre (le dispatcher LÈVE sur signature incompatible)
│         module_detail_with_children → parent+enfants — UNIQUEMENT page détail PRIVÉE (PII ✅)
│
├─⑨ GUARDS PRÉ-BUILD (cartographie complète → mémoire project_guards_map)
│    ├─ <select> sans <option> · page-client absent · create sans edit · middleware wildcard
│
├─⑩ DESIGN BRIEF (dev_design_brief.py) ← 1 appel LLM
│    → DESIGN_BRIEF.json : icônes Lucide, badge_fields, list_card_layout par entité
│
├─⑪ SHELL ENRICHER  → nav_icons Lucide dans les shells (TSC-guardé)
├─⑫ PAGE ENRICHER   → enrichit les page-clients (TSC guard + rollback)
│
├─⑬ PROTECTION (_protected set) : lib/*, actions.ts, sitemap/robots, enrichis
│
└─⑭ LLM GRAPH (LangGraph — uniquement pages custom : home, dashboard)
     ├─ planner_node  → file_plan (context_hint par fichier)
     ├─ executor_node → par fichier : brief + data_fetches + contrats navigation
     │    └─ KPIS : contrat kpis[] compilé en expressions TS EXACTES (fin du count-vs-sum)
     └─ build loop (max 3 tentatives npm run build) + restore_protected
```

## ÉTAT & PROCHAINE ÉTAPE
- **Type A validé** (10+ apps) · **Type D à ~95 %** (M2M+SEO faits, run 3 de validation à faire)
- Expansion actée : D → **I (workflow)** → K (RBAC) → H (dashboard) — règle des 4 lots (typeApps §3.5)
- Dette surveillée : dev_graph.py 1 360 lignes (découpage prévu avant Type K)

---

## JOURNAL DE BORD (5 lignes max par session — le plus récent en haut)

**7 Juil 2026** — RUN 3 : 3/3 BUILD_SUCCESS (1 tentative), 3× COHERENT 100/100, **8/8 validations confirmées sur fichiers réels** (search, KPI somme exacte via contrat, datetime-local, badges tags, SEO desc, PII zéro sur public + participants au privé, Decimal, badges statut). **TYPE D DÉCLARÉ VALIDÉ.** atelier-recettes extraite pour test manuel. → Prochain : expansion Type I (workflow/FSM).

**6 Juil 2026 (soir)** — Unification DY6 : renderer unique des listes, 2 modules + 1 template SUPPRIMÉS (-423 lignes). Contrat KPI structuré (architect → TS exact). correction_pass réveillée (trigger verdict-indépendant). P1 : datetime annotator, SEO desc, badges M2M détail, check PII reviewer. Net : la machine a PERDU du code et gagné 4 garanties. → **Prochain : run 3 de validation.**

**6 Juil 2026 (jour)** — Sprint 5 Type D-complet : M2M bout-en-bout (9 fichiers), dev_seo_generator, ZONE_32 (5 standards), RÈGLE 5 architect. 2 runs de test sur briefs non biaisés : 5/6 builds, 3 bugs systémiques découverts et corrigés à la source (modules morts ×2 couches, fuite PII, Decimal L10).
