# 02 — Architect (brief → déclaration)

## Graphe LangGraph (`architect.py::create_architect_agent`)
Entrée routée selon ce que le brief contient déjà (models ? pages ?). Chaque nœud est idempotent (skip si déjà rempli).
```
domain_interpreter (LLM) → page_planner (LLM) → semantic_annotator (LLM) → pages_detail (LLM)
   → spec_enricher (déterministe) → planner_node (déterministe) → mirror (LLM) → END
```
5 appels LLM (gpt-4o-mini, temperature 0, `response_format=json_object`), 2 étapes déterministes. L'état circule dans `state["brief"]` (dict enrichi au fil des nœuds).

## Rôle de chaque nœud
- **domain_interpreter** : brief → `models` (une STRING Prisma par modèle : `"Name { champ Type attrs, ... }"`) + `enums`. Prompt en 3 blocs séparés : STACK_INVARIANTS (userId partout par défaut, pas de modèle User, exception catalogue global, rôles ≠ modèle), DEDUCTION_RULES (préservation des champs, enum vs Boolean, lookup+FK, valeurs finies→enum, M2M), FEW_SHOT (tâches, blog, blog+tags, facturation).
- **page_planner** : models → `pages` (path, auth, model, page_type ∈ list/create/detail/detail-slug/edit/custom), `routes`, `user_flows` (prose), `ui_labels`, `title_plurals/singulars`, `enum_value_labels`, `page_links`, `design_system` (écrasé plus tard). Règles de routage très détaillées (RÈGLE 5/7/8/9, conflits [id]/[slug]). **Les pages sont décidées par ENTITÉ, avant que les acteurs soient connus.**
- **semantic_annotator** : `field_annotations` (textarea, status-enum, currency, date/datetime, url, email), `required_queries`, `features`, `status_flows` (initial, transitions liste blanche, locked_states, state_fields), `roles` (roles, privileged_role, admin_scoped_views, role_gated_actions, global_entities, initiator, surface, dashboard), `ux_hints`. Validé par Pydantic `EnrichedSpec` (raw conservé si échec).
- **pages_detail** : UNIQUEMENT pages custom (sans modèle) → contrats `{description, data_fetches, interactive, kpis, filtered_lists}`. Reçoit la liste des méthodes valides par modèle (dérivée des service_modules) + corrige inline les méthodes inventées.
- **spec_enricher** (déterministe) : corrige conflits de segments [id]/[slug], valide/remplace les data_fetches (regex sur les strings de modèles), **écrase design_system** par `design_resolver.resolve_preset(description)` (mots-clés → preset).
- **planner_node** (déterministe) : parse les strings de modèles → `PrismaModel` (`_parse_model_str`, découpe par virgules/profondeur de parenthèses), construit `ProjectSpec` + garde-fous (detail-slug sans slug → detail ; force auth=false si pages_detail dit « public » ; RÈGLE 5 auto-ajout des pages détail parents ; page `/` ajoutée). Attache `enriched_spec` et `design_system` au dict. Produit `requirements` = « Modèle X / Page Y ».
- **mirror** : résumé (modèles, champs, pages, workflows, rôles, KPI, user_flows) → `summary_fr` + `unsupported[]`.

## Techniques
LangGraph StateGraph ; prompts hardcodés (NO RAG pour l'architect, décision assumée) ; Pydantic comme validateur a posteriori ; beaucoup de regex/heuristiques de chaînes (strings de modèles, signaux « public », détection de modèle par chemin).

## Points notables (pour la conception)
- **Ordre problématique** : les écrans (page_planner) sont figés avant les acteurs (semantic_annotator). L'âme arrive après la structure → les générateurs doivent réconcilier.
- La représentation intermédiaire des modèles est une STRING Prisma reparsée plusieurs fois (planner, spec_enricher, pages_detail) par des regex différentes.
- Plusieurs garde-fous « symptomatiques » compensent la variance du page_planner (routing, auth, RÈGLE 5).
- Le design_system du page_planner est produit pour rien (écrasé).
- `user_flows` reste de la prose non compilée (utilisée par journey_validator/mirror seulement).
- Pas de notion de « nature » d'entité (profil / catalogue / collection) : seulement `global_entities` + schéma sans userId.
