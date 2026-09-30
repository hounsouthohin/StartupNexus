# 08 — Learner, rapports, observabilité

## Learner (`agents/learner.py`, 643 l.)
- Lit `logs/shadow/learner_shadow_log.json` (tous les événements de tous les runs depuis le début, ~200 runs / 900+ événements) et génère des `StandardSuggestion` par règles fixes :
  - P001 taux de succès, P002 violations sémantiques, P003 fichiers insuffisants, P004 max itérations, P005 progrès, P006 erreurs de build récurrentes normalisées, P007 spec_coverage bas, P008 superviseurs ;
  - BP001-003 : « superviseurs », « batchs », « must_fix » → **concepts d'architectures supprimées** (superviseurs LLM inline abandonnés en mars).
- Importe `scripts.sprint5_gate` qui n'existe pas (warning à chaque run).
- Résultat observé : 6 suggestions par run, en grande partie des erreurs de build de VIEUX projets (writer-pad ×10, coworking-hub…), recopiées dans chaque FactoryRunReport → bruit.
- La mission redéfinie le 16 juillet (« détecter les cases manquantes » à partir des non-mappés / `unsupported[]`) **n'est pas implémentée** : le miroir produit `unsupported[]`, personne ne l'agrège.
- `scripts/approve_suggestion.py` (validation humaine → Qdrant) : mentionné en mémoire, absent du dossier scripts actuel.

## Rapports
- `utils/run_report.py` : `run_report_<id>.json` (métriques) + FactoryRunReport `.md` (miroir « ce que l'app fait », non couvert, build, review, tests, semgrep, patterns du learner, durée).
- `logs/metrics/guard_rule_events.jsonl`, `rag_usage.jsonl`, `sorties.md` (JSONL de chaque activité via run_batch).
- `agents/observability.py` : logger d'événements learner/RAG.

## Lecture conception
- La boucle d'« apprentissage » est morte deux fois : la version standards Qdrant (PRINCIPE 3, déclaré mort le 16 juillet) et la version « détecter les cases manquantes » (jamais construite). Ce qui tourne est un résidu qui pollue le rapport.
- La matière première utile existe déjà : `unsupported[]` du miroir à chaque run. Un agrégateur simple (fréquence des demandes non couvertes par axe) serait le vrai learner de la doctrine.
