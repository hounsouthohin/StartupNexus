# 07 — Contrôle qualité (les « juges »)

| Instrument | Où | Ce qu'il juge vraiment | Coût | Verdict |
|---|---|---|---|---|
| `next build` + `tsc` | dev_graph + dev_test_activity | Compilabilité | temps | **Seul juge fiable** du pipeline |
| `prisma validate` | dev_test_activity | Schéma valide | faible | Fiable |
| Garde pré-build (générateur planté, page-client absent) | dev_graph | Cohérence des fichiers cœur | 0 | Fiable, bien placé |
| `requirements_engine` / `spec_coverage` | core | Existence de fichiers « Modèle X → schema », « Page /y → page.tsx » | 0 | Mesure la forme, pas le sens (17/17 sur app cassée) |
| `journey_validator` | core | Le chemin cité dans chaque user_flow (prose) existe en fichier (regex + LLM optionnel) | 0 | Idem, forme |
| `quality_validator` + `quality_checker/quality_check.mjs` | dev_graph fin de run | AST (@typescript-eslint) : Z21 pagination, Z24 N+1, Z25 select, Z26 transaction + règles C* comparant le code au contrat de page (KPI tronqué, fetch interdit) | faible | Utile, non bloquant |
| Reviewer L1 (`reviewer.py`) | review_activity | Auth manquante/abusive sur page.tsx, PII sur page publique | 0 | Fiable mais étroit (pages seulement) |
| Reviewer L2 | review_activity | Conformité brief par gpt-4o sur ≤14 fichiers + standards Qdrant | $ | Prouvé menteur (COHERENT 100/100 sur apps absurdes) |
| correction_pass | activité | Corrige auth par regex / réécrit une page custom par LLM | $ | Ne touche que les pages LLM |
| QA Jest (`agents/qa.py`) | qa_activity | gpt-4o écrit des tests des schemas/services **déterministes** | $$ (gpt-4o) | Déclaré « mort » par la roadmap (tester nos générateurs, pas l'app) mais toujours exécuté ; échoue en routine (mocks Prisma) |
| Semgrep | qa_activity | Règles critiques de sécurité | faible | Signal secondaire |
| Oracle (`dev_oracle_generator`) | route dans l'app | Transitions interdites refusées (seul invariant couvert) | 0 | Bonne idée, jamais appelée |

## Lecture conception
- Il y a BEAUCOUP d'instruments, mais un seul juge fiable du produit (le build) et un seul capteur sémantique honnête potentiel (l'oracle) qui n'est pas branché.
- Les juges du SENS (reviewer L2, journey, spec_coverage) sont soit menteurs soit formels. Le vrai juge du sens prévu par la doctrine (la Scène + l'humain, ou des oracles dérivés de la déclaration) est le moins outillé.
- Plusieurs instruments coûtent des appels LLM à chaque run pour un signal nul ou négatif (QA Jest gpt-4o, reviewer L2 gpt-4o).
- Une matrice des capacités donnerait une liste finie d'invariants vérifiables mécaniquement (une assertion par case) → l'oracle deviendrait complet et remplacerait plusieurs juges faibles.
