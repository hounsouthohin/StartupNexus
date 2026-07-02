Entrée : spec (ProjectSpec dict)
│
├─① ISOLATION : workdir FACTORY_WORKDIR/<project_name>/ (nettoyage résidus)
│
├─② TEMPLATES STATIQUES (dev_file_ops.py + stack JSON)
│    package.json, tsconfig.json, jest.config.js, .env.local, etc.
│    └─ GUARD BLOQUANT : si package.json absent → ABORT
│
├─③ schema.prisma ← ProjectSpec.to_prisma_schema_block() [déterministe]
│
├─④ ModelGenerationContext (dev_model_context.py)  ← SOURCE UNIQUE DE VÉRITÉ
│    build_all_contexts(spec_obj) → dict[ModelName → ctx]
│    Chaque ctx expose :
│      .editable_fields    → FieldInfo (type, input_type, is_optional…)
│      .display_fields     → [list of field names]
│      .relation_fields    → RelationInfo (is_array, FK…)
│      .fk_fields          → FKFieldInfo (field_name, related_model)
│      .has_slug / .has_status / .has_public_pages / .has_relations
│      .ui_labels / .enum_value_labels
│      .serialized_type    → "SerializedArticle"
│      .list_page_path     → "/dashboard/articles"
│
├─⑤ FONDATIONS (ordre strict — chaque étape dépend de la précédente)
│    ├─ dev_types_generator      → lib/types.ts          [déterministe]
│    ├─ dev_zod_generator        → lib/schemas.ts         [déterministe]
│    ├─ dev_service_generator    → lib/services/*.ts      [déterministe]
│    │    └─ service_modules/ (pluggable) :
│    │         crud.py           → getAll/getById/create/update/delete
│    │         relations.py      → getAllWithRelations/getByIdWithRelations
│    │         public.py         → getPublicAll/getPublicById
│    │         slug.py           → getBySlug/getBySlugWithRelations
│    │         status.py         → getPublished (ENUM only)
│    │         child.py          → getAllByParentId
│    │         public_relations  → getPublicByIdWithRelations
│    └─ dev_actions_generator   → app/**/actions.ts       [déterministe]
│
├─⑥ UI INFRASTRUCTURE
│    ├─ dev_design_system_generator → tailwind.config.js, globals.css
│    │    └─ _build_tailwind_config(ds) injecte fonts du preset
│    ├─ dev_layout_generator        → app/layout.tsx, TopNavShell, DashboardShell
│    ├─ dev_middleware_generator    → middleware.ts (routes publiques vs privées)
│    └─ dev_navigation_generator    → navigation helpers
│
├─⑦ PAGES + PAGE-CLIENTS (déterministes pour les pages model)
│    ├─ dev_pages_generator
│    │    ├─ generate_page_stubs()      → page.tsx (model pages)  [protégé]
│    │    ├─ generate_edit_page_stubs() → [id]/edit/page.tsx      [protégé]
│    │    ├─ generate_loading_files()   → loading.tsx
│    │    └─ generate_root_page_if_needed() → app/page.tsx
│    │
│    └─ dev_form_generator
│         Reçoit ctx → choisit template Jinja2 selon flags :
│         ├─ list    → list_client.tsx.j2 / list_client_card_grid.tsx.j2
│         │            / list_client_search.tsx.j2 / list_client_status.tsx.j2
│         ├─ public  → public_list_client.tsx.j2 / public_list_card_grid.tsx.j2
│         ├─ create  → create_client.tsx.j2
│         ├─ edit    → edit_client.tsx.j2
│         └─ detail  → detail_client.tsx.j2
│
├─⑧ PAGES SPÉCIALES
│    ├─ dev_hub_generator         → app/dashboard/page.tsx
│    └─ feature_modules/          → activation selon ctx.relation_fields
│         module_detail_with_children → parent+enfants page-client.tsx
│         module_search.py        → search module
│         module_status_flow.py   → workflow statuts
│
├─⑨ GUARDS PRÉ-BUILD (vérifications cohérence avant LLM)
│    ├─ <select> sans <option>
│    ├─ page.tsx importe page-client mais page-client absent
│    ├─ create sans edit (SPEC_WARNING)
│    └─ middleware wildcard dangereux
│
├─⑩ DESIGN BRIEF (dev_design_brief.py) ← 1 appel LLM
│    → DESIGN_BRIEF.json : brand_name, primary_color, density, animation_style
│       entities: { Article: { icon, badge_fields, list_card_layout } }
│
├─⑪ SHELL ENRICHER (dev_shell_enricher.py)
│    → injecte nav_icons Lucide dans TopNavShell + DashboardShell
│
├─⑫ PAGE ENRICHER (dev_page_enricher.py)
│    → enrichit page-client.tsx list+detail : icônes, animations, badges
│    → TSC guard : rollback si TypeScript échoue
│
├─⑬ PROTECTION (_protected set)
│    lib/*, **/actions.ts, enriched files → LLM ne peut pas écraser
│
└─⑭ LLM GRAPH (LangGraph — uniquement pour pages custom)
     ├─ planner_node  → file_plan (liste des fichiers à générer)
     ├─ executor_node → génère chaque fichier custom (home, dashboard custom)
     │    └─ tools : write_file / read_file / shell_exec / file_exists
     └─ build loop (max 3 tentatives npm run build)
