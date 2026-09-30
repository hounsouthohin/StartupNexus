# 06 — Le LLM executor (la « queue » : ce que le déterministe ne génère pas)

## Déroulé de `run_dev_agent` (dev_graph.py) après les générateurs
1. Garde pré-build : si un générateur cœur a planté OU un page.tsx importe un page-client absent → run annulé (le LLM n'improvise jamais un fichier cœur manquant).
2. Warnings qualité (create sans edit, wildcard middleware).
3. `_protected` = tous les fichiers de `template_written` + config ; `write_contract_file` (contrat machine pour le quality checker).
4. **pre_run_commands** (depuis la config JSON : npm install, prisma generate…), bloquantes ou non.
5. Service map (texte), **LevelAManifest + CONTRACTS.md**, carte des types Prisma réels (DMMF via Node).
6. **Design brief** (1 appel LLM) → shell enricher (icônes nav) → **régénération complète des page-clients avec décorations** (form_generator tourne donc 2 fois).
7. System prompt (`dev_prompts.build_system_prompt` : règles `rules_dev.md`, fichiers pré-écrits, service map, type map, design, standards Qdrant « mandatory RAG » selon 5 contextes de requêtes).
8. **Graphe LangGraph de l'executor** : `planner → executor ⇄ tools → progressive_validation → restore → extract_error → (executor | END)`.

## Les nœuds de l'executor
- **planner** (`agents/planner.py::make_deterministic_plan`) : liste ordonnée des fichiers à écrire, en SAUTANT tout ce qui est déjà dans `template_written`. En pratique pour les types couverts : pages custom (home, dashboard non compilé), webhooks. Plan vide = build direct.
- **executor** (gpt-4o-mini, temp 0, seed 42, outils) : pour le prochain fichier du plan non présent sur disque, injecte : contexte (context_hint + description pages_detail + appels service dé-paginés si agrégés + user_flows + contrat de page/navigation), règles de rôle (config), dépendances disque + standard RAG du rôle (`dev_context.build_role_context`), exemple ancré (dernier fichier du même rôle). Sur erreur de build : extrait les lignes TS, montre les 40 premières lignes du fichier fautif + ses dépendances.
- **tools** (`dev_tools.py`) : write_file (refuse les fichiers protégés, imports interdits), read_file, list_directory, shell_exec (bloque les commandes visant des fichiers protégés), file_exists, + web_search.
- **progressive_validation** : tsc désactivé (trop lent) ; seulement un regex « méthode de service absente du manifest » → warning.
- **restore** : réécrit tout fichier protégé que le LLM aurait supprimé.
- **extract_error** : succès/échec par le code de sortie de la commande de build (pas de mots-clés).
- **route_after_tools** : fin si succès ; **fin immédiate si l'erreur est dans un fichier protégé (GENERATOR_BUG)** ; sinon retour executor (max 3 builds, max 15 tours, recursion_limit 100).

## Lecture conception
- L'executor est devenu petit et bien encadré (plan déterministe, contrats, protection) ; sur les apps couvertes il écrit peu ou rien.
- Mais tout son outillage (RAG, exemples, règles, manifest, service map, type map, contrats) est lourd pour une petite part du code final.
- Quand le bug est dans le cœur déterministe, l'executor s'arrête (correct) mais `dev_test_activity` relance TOUT (régénération identique) → temps perdu.
- Restes d'anciennes époques : planner.py prévoit encore des services/actions écrits par le LLM (toujours sautés), commentaire « les services sont générés par le LLM » devenu faux.
