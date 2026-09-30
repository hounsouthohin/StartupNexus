# 03 — Contexte & contrats de génération (la couche entre déclaration et générateurs)

## ModelGenerationContext (`dev_model_context.py`) — l'« AST par entité »
Calculé UNE fois par modèle (`build_all_contexts(spec, enriched_spec)`), lu par tous les générateurs.
- Identité : name, camel, kebab, owner (resolved_owner), serialized_type, spec_enums.
- Champs classés : `editable_fields` (FieldInfo : input_type, allowed_values, semantic_type…), `fk_fields`, `datetime_fields`, `decimal_fields`, `relation_fields`, `m2m_fields` (écarte les fausses M2M vers une entité à workflow), `display_fields` (≤4).
- Drapeaux : has_slug (+ slug_source auto), has_status, has_published_bool, has_relations, has_m2m, has_public_pages/list/detail, list_page_path, labels (ui_labels, title_plural/singular, enum_value_labels).
- Type I : `status_flow` VALIDÉ (champ réel, états dans l'enum, initial jamais verrouillé, state_fields réels) sinon None ; `create_excluded_fields` = champ d'état + TOUS les state_fields (y compris ceux de l'état initial → bug garage).
- Type K : `is_global` = « pas de champ owner » (le schéma tranche), `is_admin_scoped`, `gated_verbs`, `privileged_role`, `initiator` (S1).
- ABSENTS du contexte : surface, dashboard par acteur, nature d'entité, capacités par acteur.
- Heuristiques de filet : `_STRING_ENUM_DEFAULTS` (status/priority/type… → valeurs par défaut si l'architect a raté l'enum), `_TEXTAREA_NAMES`, résolution FK par suffixe de nom.

## Service modules (`service_modules/`)
- `ServiceMethodModule` (ABC) : `should_activate(ctx)`, `generate(ctx)` → lignes TS, `methods_for(ctx)` → [MethodDecl] (source unique des noms/signatures, remède « getPublished »).
- Registre ordonné : Crud, Child, Public, Relations, PublicRelations, Slug, Transition.
- `valid_methods_for_flags(...)` : reconstruit un contexte minimal (`_CtxStub`) pour que l'architect/spec_enricher (qui tournent AVANT les vrais contextes) valident les méthodes depuis la MÊME source. `build_factory_capabilities_string()` dérivé aussi.
- `base.py` : helpers TS partagés (select scalaires, maps DateTime→ISO / Decimal→Number racine et imbriqués, select imbriqué des relations = id + display_fields du lié, 1 seul niveau).

## Autres contrats
- `dev_service_spec.build_service_spec(ctx)` : inventaire des méthodes (dérivé de methods_for + required_queries) → consommé par manifest, planner, prompt.
- `level_a_manifest.py` : `LevelAManifest` (par modèle : service_var, import, méthodes) + `generate_contract_md` → **CONTRACTS.md** écrit dans le projet pour le LLM executor.
- `dev_page_contract.py` : pour chaque page AVEC modèle : service_method (selon page_type × auth × slug × relations), list/detail/back paths, slug_field, display_fields ordonnés, badge_fields, return_fields → injecté dans le brief de fichier du LLM executor. (Coexiste avec un autre « page contract » dans planner.py — deux notions homonymes.)
- `dev_naming.py` : « source unique » du nommage… mais camel/kebab sont réimplémentés dans model_context, manifest, spec_enricher.

## Lecture conception
Il existe déjà UN vrai patron de source unique qui marche (methods_for). Mais le contexte reste centré entité : les concepts d'acteur y sont des champs isolés (initiator, gated_verbs, privileged_role) et non une structure « acteur × entité × action ». C'est ici que la matrice des capacités se brancherait naturellement (au même niveau que build_all_contexts).
