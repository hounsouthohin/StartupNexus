# 10 — Synthèse de la lecture (30 Sept 2026)

## Ce qu'est réellement l'usine
Un compilateur piloté par LLM : 5 appels LLM comprennent le brief (architect) → une déclaration (ProjectSpec + EnrichedSpec) → un contexte par entité → ~20 générateurs déterministes (≈ 9 000 lignes spécifiques Next.js/Clerk/Prisma) écrivent presque tout → un petit LLM executor écrit les pages sur mesure restantes → build → revue/QA/preview. Orchestré par Temporal. ≈ 23 000 lignes au total.

## Les 6 causes structurelles de « lourd et sans âme »
1. **Mauvais ordre** : l'architect décide les écrans (page_planner) AVANT les acteurs (semantic_annotator). L'âme est greffée après la structure.
2. **Mauvaise unité** : tout est généré « par entité × type de page ». Les notions d'acteur sont des drapeaux isolés, réinterprétés dans 9 fichiers ; templates, dashboard et formulaires n'en lisent aucun ; nav codée pour 2 acteurs.
3. **Concepts recopiés** : owner/global, visibilité, nommage, FK, pluriels réimplémentés à plusieurs endroits → divergences (bugs des runs du 28 sept).
4. **Représentation fragile** : les modèles circulent en chaînes Prisma reparsées par des regex différentes (planner, spec_enricher, pages_detail).
5. **Garde-fous symptomatiques** : règles de routage (RÈGLES 5/7/8/9) + corrections aval (spec_enricher, planner, ProjectSpec) existent parce qu'un LLM planifie les pages entité par entité.
6. **Code vestigial** (estimation ≥ 2 500 lignes) : prebuild_pipeline, page_composer, navigation_generator, flask_api cassé, moitié du learner (superviseurs/batchs), planification de services dans planner.py, QA Jest gpt-4o testant du déterministe, sections de config non lues, page-clients générés deux fois, retry tsc qui régénère tout.

## Ce qui est solide (à garder)
Pipeline Temporal ; protection des fichiers + garde pré-build ; patron source unique `methods_for` ; workflow (StatusFlow + transitionTo + verrous) ; KPI/listes filtrées compilés ; Design Compiler (vocabulaire fermé) ; miroir (summary_fr + unsupported) ; preview automatique ; seed.

## Où se branche la matrice des capacités
Au niveau de `build_all_contexts` : un objet acteur × entité × action calculé une fois, dont DÉRIVENT les pages (fin du page_planner LLM et de ses garde-fous), la nav (N acteurs), les dashboards par acteur, les clauses where, les gardes serveur, les boutons des templates, le seed et les oracles.
